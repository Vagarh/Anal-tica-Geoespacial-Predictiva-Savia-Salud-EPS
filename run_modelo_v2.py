"""Script de entrenamiento modelo XGBoost v2 — Savia Salud EPS.

Ejecutar desde la raíz del proyecto:
    python run_modelo_v2.py

Correcciones vs v1:
- sample_weight explícito por clase (XGBoost multiclase ignora scale_pos_weight)
- Umbral óptimo por curva Precision-Recall (F-beta=2)
- min_child_weight=3, max_delta_step=1
"""

import json
import logging
import sys
import warnings
from pathlib import Path
from datetime import date

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR  = Path("d:/Users/jcardonr/Documents/Savia")
PROC_DIR  = BASE_DIR / "Data" / "processed"
FIG_DIR   = BASE_DIR / "reports" / "figures"
MODEL_DIR = BASE_DIR / "models" / "artifacts"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BASE_DIR))

from src.data.geo_features import (
    build_geo_features,
    compute_glosa_rate_by_municipio,
    compute_hhi_dx_by_municipio,
    get_geo_feature_names,
)

TODAY        = date.today().strftime("%Y%m%d")
RANDOM_STATE = 42
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({"figure.dpi": 120, "figure.figsize": (12, 5)})

# ── 1. Cargar datos ───────────────────────────────────────────────────────────
fase0_files = sorted(PROC_DIR.glob("*_geo_eda_fase0.parquet"))
if not fase0_files:
    raise FileNotFoundError("No se encontró archivo de Fase 0.")

df_base = pd.read_parquet(fase0_files[-1])
df_base["fecha_radicacion"] = pd.to_datetime(df_base["fecha_radicacion"])
logger.info("Dataset Fase 0: %d filas · %d cols", len(df_base), len(df_base.columns))

sedes_files = sorted((BASE_DIR / "Data" / "raw").glob("*_cnt_prestador_sedes.parquet"))
df_sedes = pd.read_parquet(sedes_files[-1])
logger.info("Sedes IPS: %d registros", len(df_sedes))

vc = df_base["target"].value_counts().sort_index()
for cls, label in [(0, "Auditada"), (1, "Glosada"), (2, "Devuelta")]:
    n = vc.get(cls, 0)
    logger.info("Clase %d (%s): %d  (%.2f%%)", cls, label, n, n / len(df_base) * 100)

# ── 2. División temporal ──────────────────────────────────────────────────────
df_sorted = df_base.sort_values("fecha_radicacion").reset_index(drop=True)
n       = len(df_sorted)
n_train = int(n * 0.60)
n_val   = int(n * 0.20)

df_train = df_sorted.iloc[:n_train].copy()
df_val   = df_sorted.iloc[n_train : n_train + n_val].copy()
df_test  = df_sorted.iloc[n_train + n_val :].copy()

for name, split in [("Train", df_train), ("Val", df_val), ("Test", df_test)]:
    logger.info("%s: %d filas  Glosa=%.2f%%", name, len(split), (split["target"] == 1).mean() * 100)

# ── 3. Tasas históricas SOLO en train (anti-leakage) ──────────────────────────
glosa_rates  = compute_glosa_rate_by_municipio(df_train)
hhi_dict     = compute_hhi_dx_by_municipio(df_train)
global_glosa = (df_train["target"] == 1).mean()
global_hhi   = df_train.groupby(
    df_train["municipio_residencia"].str.strip().str.upper()
)["codigo_dx"].apply(lambda s: float((s.value_counts(normalize=True) ** 2).sum())).mean()

# ── 4. Features geoespaciales ─────────────────────────────────────────────────
build_kwargs = dict(
    df_sedes=df_sedes,
    glosa_rates=glosa_rates,
    hhi_dict=hhi_dict,
    global_glosa_rate=global_glosa,
    global_hhi=global_hhi,
)

df_train_geo = build_geo_features(df_train, **build_kwargs)
df_val_geo   = build_geo_features(df_val,   **build_kwargs)
df_test_geo  = build_geo_features(df_test,  **build_kwargs)

geo_feats = [f for f in get_geo_feature_names() if f != "nivel1_en_municipio"]

geo_path = PROC_DIR / f"{TODAY}_geo_features.parquet"
pd.concat([df_train_geo, df_val_geo, df_test_geo]).to_parquet(geo_path, index=False)
logger.info("Dataset features geo guardado: %s", geo_path)

# ── 5. Encoding + pesos de clase ─────────────────────────────────────────────
from sklearn.preprocessing import LabelEncoder

feats_socio           = ["nivel_sisben", "edad"]
feats_categoricas_raw = ["zona_afiliado", "regimen", "grupo_poblacional", "genero"]
all_feats = list(geo_feats) + [f for f in feats_socio if f in df_train_geo.columns]

le_dict = {}
for col in feats_categoricas_raw:
    if col in df_train_geo.columns:
        le = LabelEncoder()
        all_vals = pd.concat([df_train_geo[col], df_val_geo[col], df_test_geo[col]]).fillna("DESCONOCIDO")
        le.fit(all_vals)
        for split in [df_train_geo, df_val_geo, df_test_geo]:
            split[col + "_enc"] = le.transform(split[col].fillna("DESCONOCIDO"))
        le_dict[col] = le
        all_feats.append(col + "_enc")

logger.info("Features totales (%d): %s", len(all_feats), all_feats)

# Submuestreo estratificado
SAMPLE_SIZE = 1_500_000
if len(df_train_geo) > SAMPLE_SIZE:
    frac = SAMPLE_SIZE / len(df_train_geo)
    df_train_sample = (
        df_train_geo
        .groupby("target", group_keys=False)
        .apply(lambda x: x.sample(frac=frac, random_state=RANDOM_STATE))
        .reset_index(drop=True)
    )
    logger.info("Train submuestreado: %d → %d", len(df_train_geo), len(df_train_sample))
else:
    df_train_sample = df_train_geo.reset_index(drop=True)

X_train = df_train_sample[all_feats].apply(pd.to_numeric, errors="coerce")
y_train = df_train_sample["target"].astype(int)
X_val   = df_val_geo[all_feats].apply(pd.to_numeric, errors="coerce")
y_val   = df_val_geo["target"].astype(int)
X_test  = df_test_geo[all_feats].apply(pd.to_numeric, errors="coerce")
y_test  = df_test_geo["target"].astype(int)

# Pesos: inverso de frecuencia + boost x2 en Glosada
class_counts  = y_train.value_counts().sort_index()
n_total       = len(y_train)
n_clases      = len(class_counts)
class_weights = {cls: n_total / (n_clases * cnt) for cls, cnt in class_counts.items()}
GLOSADA_BOOST = 2.0
class_weights[1] = class_weights[1] * GLOSADA_BOOST
sample_weights = y_train.map(class_weights).values

for cls, label in [(0, "Auditada"), (1, "Glosada"), (2, "Devuelta")]:
    logger.info("Peso clase %d (%s): %.4f", cls, label, class_weights[cls])

# ── 6. Entrenamiento ──────────────────────────────────────────────────────────
import xgboost as xgb

logger.info("Entrenando XGBoost v2 con sample_weight...")
model = xgb.XGBClassifier(
    objective="multi:softprob",
    num_class=3,
    n_estimators=500,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=3,
    max_delta_step=1,
    reg_alpha=0.1,
    reg_lambda=1.0,
    random_state=RANDOM_STATE,
    eval_metric="mlogloss",
    early_stopping_rounds=40,
    n_jobs=-1,
    verbosity=1,
    tree_method="hist",
)

model.fit(
    X_train, y_train,
    sample_weight=sample_weights,
    eval_set=[(X_val, y_val)],
    verbose=50,
)
logger.info("Entrenamiento completo · Mejor iteración: %d", model.best_iteration)

# ── 7. Umbral óptimo ──────────────────────────────────────────────────────────
from sklearn.metrics import precision_recall_curve, f1_score, roc_auc_score

y_proba_val      = model.predict_proba(X_val)
prob_glosada_val = y_proba_val[:, 1]

precisions, recalls, thresholds = precision_recall_curve(
    (y_val == 1).astype(int), prob_glosada_val
)

BETA = 2.0
fbeta_scores = (
    (1 + BETA**2) * precisions[:-1] * recalls[:-1]
    / (BETA**2 * precisions[:-1] + recalls[:-1] + 1e-9)
)
best_idx      = fbeta_scores.argmax()
UMBRAL_OPTIMO = float(thresholds[best_idx])

logger.info("Umbral óptimo (F-beta=%.0f): %.4f", BETA, UMBRAL_OPTIMO)
logger.info("  Precision Glosada @ umbral: %.4f", precisions[best_idx])
logger.info("  Recall    Glosada @ umbral: %.4f", recalls[best_idx])

# Gráfica curva Precision-Recall
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].plot(recalls[:-1], precisions[:-1], color="#3498db", linewidth=2)
axes[0].scatter(recalls[best_idx], precisions[best_idx], color="#e74c3c", s=120, zorder=5,
                label=f"Umbral óptimo ({UMBRAL_OPTIMO:.3f})")
axes[0].set_xlabel("Recall Glosada")
axes[0].set_ylabel("Precision Glosada")
axes[0].set_title("Curva Precision-Recall — Clase Glosada (Val)")
axes[0].legend()

axes[1].plot(thresholds, recalls[:-1],  label="Recall",           color="#e74c3c")
axes[1].plot(thresholds, precisions[:-1], label="Precision",      color="#3498db")
axes[1].plot(thresholds, fbeta_scores,  label=f"F{BETA:.0f}-score", color="#f39c12", linestyle="--")
axes[1].axvline(UMBRAL_OPTIMO, color="#2c3e50", linestyle=":", label=f"Umbral={UMBRAL_OPTIMO:.3f}")
axes[1].set_xlabel("Umbral de probabilidad")
axes[1].set_title("Precision / Recall / F-beta vs Umbral")
axes[1].legend()

plt.tight_layout()
plt.savefig(FIG_DIR / "02_precision_recall_umbral.png", bbox_inches="tight")
logger.info("Gráfica guardada: 02_precision_recall_umbral.png")

# ── 8. Evaluación ─────────────────────────────────────────────────────────────
from sklearn.metrics import classification_report, confusion_matrix


def predecir_con_umbral(proba: np.ndarray, umbral_glosada: float) -> np.ndarray:
    """Aplica umbral personalizado para clase Glosada sobre probabilidades multiclase."""
    predicciones = np.argmax(proba, axis=1)
    predicciones[proba[:, 1] >= umbral_glosada] = 1
    return predicciones


def evaluar_modelo(model, X, y, nombre, umbral_glosada=0.5):
    """Evalúa el modelo con umbral ajustado y retorna métricas del proyecto."""
    y_proba = model.predict_proba(X)
    y_pred  = predecir_con_umbral(y_proba, umbral_glosada)

    f1  = f1_score(y, y_pred, average="macro", zero_division=0)
    auc = roc_auc_score(y, y_proba, multi_class="ovr", average="macro")
    recall_glosada    = float((y_pred[y == 1] == 1).mean()) if (y == 1).any() else 0.0
    precision_glosada = float((y[y_pred == 1] == 1).mean()) if (y_pred == 1).any() else 0.0

    print(f"\n{'='*65}")
    print(f"MÉTRICAS — {nombre}  (umbral Glosada={umbral_glosada:.4f})")
    print(f"{'='*65}")
    print(f"  F1-macro:                    {f1:.4f}")
    print(f"  AUC-ROC (OvR macro):         {auc:.4f}")
    print(f"  Recall    Glosada (clase 1): {recall_glosada:.4f}  <- metrica primaria")
    print(f"  Precision Glosada (clase 1): {precision_glosada:.4f}")
    print()
    print(classification_report(y, y_pred, target_names=["Auditada", "Glosada", "Devuelta"], zero_division=0))

    return {
        "split": nombre,
        "umbral_glosada": umbral_glosada,
        "f1_macro": float(f1),
        "auc_roc": float(auc),
        "recall_glosada": recall_glosada,
        "precision_glosada": precision_glosada,
    }


metricas_val  = evaluar_modelo(model, X_val,  y_val,  "Validacion", UMBRAL_OPTIMO)
metricas_test = evaluar_modelo(model, X_test, y_test, "Test",       UMBRAL_OPTIMO)

# Matriz de confusión
y_proba_test = model.predict_proba(X_test)
y_pred_test  = predecir_con_umbral(y_proba_test, UMBRAL_OPTIMO)
cm = confusion_matrix(y_test, y_pred_test, normalize="true")
clases = ["Auditada (0)", "Glosada (1)", "Devuelta (2)"]

fig, ax = plt.subplots(figsize=(7, 5))
sns.heatmap(cm, annot=True, fmt=".2f", cmap="Blues",
            xticklabels=clases, yticklabels=clases, ax=ax)
ax.set_ylabel("Real")
ax.set_xlabel("Predicho")
ax.set_title(f"Matriz de Confusion Normalizada — Test (umbral={UMBRAL_OPTIMO:.3f})")
plt.tight_layout()
plt.savefig(FIG_DIR / "02_confusion_matrix_test_v2.png", bbox_inches="tight")
logger.info("Gráfica guardada: 02_confusion_matrix_test_v2.png")

# Comparación v1 vs v2
y_pred_argmax = np.argmax(y_proba_test, axis=1)
recall_v1 = float((y_pred_argmax[y_test == 1] == 1).mean()) if (y_test == 1).any() else 0.0
recall_v2 = float((y_pred_test[y_test == 1] == 1).mean()) if (y_test == 1).any() else 0.0
print(f"\n{'='*50}")
print("COMPARACION v1 (baseline) vs v2 (corregido)")
print(f"{'='*50}")
print(f"  Recall Glosada v1 (argmax):  {recall_v1:.4f}")
print(f"  Recall Glosada v2 (umbral):  {recall_v2:.4f}")
print(f"  AUC-ROC v1:                  0.6214")
print(f"  AUC-ROC v2:                  {metricas_test['auc_roc']:.4f}")
print(f"  Baseline AUC >= 0.75: {'CUMPLIDO' if metricas_test['auc_roc'] >= 0.75 else 'PENDIENTE'}")

# ── 9. Importancia de features ────────────────────────────────────────────────
try:
    import shap
    X_shap    = X_val.fillna(0).sample(min(5000, len(X_val)), random_state=RANDOM_STATE)
    explainer = shap.TreeExplainer(model)
    shap_raw  = explainer.shap_values(X_shap)

    # shap_raw puede ser list[ndarray(n,p)] (una por clase) o ndarray(n,p,c)
    if isinstance(shap_raw, list):
        # lista de arrays (n_muestras, n_features) — una por clase
        importancia_shap = pd.DataFrame(
            np.mean([np.abs(sv) for sv in shap_raw], axis=0), columns=all_feats
        ).mean().sort_values(ascending=False)
    elif shap_raw.ndim == 3:
        # array (n_muestras, n_features, n_clases)
        importancia_shap = pd.Series(
            np.abs(shap_raw).mean(axis=(0, 2)), index=all_feats
        ).sort_values(ascending=False)
    else:
        # array (n_muestras, n_features) — fallback
        importancia_shap = pd.Series(
            np.abs(shap_raw).mean(axis=0), index=all_feats
        ).sort_values(ascending=False)

    top_feats   = importancia_shap.head(15)
    colors_shap = ["#e74c3c" if f in geo_feats else "#3498db" for f in top_feats.index[::-1]]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.barh(top_feats.index[::-1], top_feats.values[::-1], color=colors_shap)
    ax.set_xlabel("Importancia SHAP media |valor|")
    ax.set_title("Top 15 features por importancia SHAP — v2")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "02_shap_geo_features_v2.png", bbox_inches="tight")
    logger.info("SHAP guardado: 02_shap_geo_features_v2.png")
    print("\nTop 15 features SHAP:")
    print(top_feats.round(4).to_string())
except (ImportError, Exception) as e:
    logger.warning("SHAP no disponible (%s) — usando importancia nativa XGBoost", e)
    importancia = pd.Series(model.feature_importances_, index=all_feats).sort_values(ascending=False)
    print(importancia.head(15).round(4))

# ── 10. Guardar artefactos v2 ─────────────────────────────────────────────────
model_path = MODEL_DIR / f"{TODAY}_geo_xgboost_v2.json"
model.save_model(str(model_path))
logger.info("Modelo v2 guardado: %s", model_path)

metadata = {
    "version": "v2",
    "fecha": TODAY,
    "modelo": "XGBoost geo_v2",
    "descripcion": "Correccion desbalance: sample_weight explicito + umbral optimo F-beta=2",
    "features": all_feats,
    "features_geo": geo_feats,
    "umbral_glosada": UMBRAL_OPTIMO,
    "glosada_boost": GLOSADA_BOOST,
    "pesos_clase": {str(k): float(v) for k, v in class_weights.items()},
    "n_train_sample": len(X_train),
    "n_val": len(X_val),
    "n_test": len(X_test),
    "metricas_val": metricas_val,
    "metricas_test": metricas_test,
    "global_glosa_rate": float(global_glosa),
    "random_state": RANDOM_STATE,
    "correcciones_vs_v1": [
        "scale_pos_weight eliminado (ignorado en multiclase XGBoost)",
        "sample_weight explicito: inverso de frecuencia con boost x2 en Glosada",
        "umbral ajustado por curva Precision-Recall (F-beta=2)",
        "min_child_weight reducido de 10 a 3",
        "max_delta_step=1 para estabilizar gradientes en clases raras",
    ],
}

meta_path = MODEL_DIR / f"{TODAY}_geo_xgboost_v2_metadata.json"
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)
logger.info("Metadata v2 guardada: %s", meta_path)

rates_path = PROC_DIR / f"{TODAY}_glosa_rates_municipio.json"
with open(rates_path, "w", encoding="utf-8") as f:
    json.dump(glosa_rates, f, indent=2, ensure_ascii=False)

print(f"\n{'='*65}")
print("ARTEFACTOS GUARDADOS — v2")
print(f"{'='*65}")
print(f"  Modelo:   {model_path}")
print(f"  Metadata: {meta_path}")
print(f"  Dataset:  {geo_path}")
print()
print("RESUMEN FINAL — Test:")
print(f"  AUC-ROC:          {metricas_test['auc_roc']:.4f}  (>= 0.75: {'SI' if metricas_test['auc_roc'] >= 0.75 else 'NO'})")
print(f"  F1-macro:         {metricas_test['f1_macro']:.4f}")
print(f"  Recall  Glosada:  {metricas_test['recall_glosada']:.4f}  <- metrica primaria")
print(f"  Precision Glosada:{metricas_test['precision_glosada']:.4f}")
print(f"  Umbral Glosada:   {UMBRAL_OPTIMO:.4f}")
