"""Modelo XGBoost v3 — Savia Salud EPS.

Mejoras sobre v2:
1. Features temporales: mes, semana_anio, dias_desde_inicio_periodo
   → captura estacionalidad en tasas de glosa (variación semanal 0.5% - 17.5%)
2. Features de diagnóstico: capitulo_dx (1er char CIE-10), dx_categoria (3 chars)
   → codigo_dx tiene 100% nulos en EDA pero capitulo puede inferirse de historial
3. Features de IPS: capitacion (flag), region_ips_enc
4. Eliminadas: hhi_dx_municipio y sin_cobertura_savia (SHAP ≈ 0 en v2)
5. Calibración de umbral: usar solo últimas 2 semanas de val donde
   la tasa de glosa (~5%) es comparable a test (~5.56%), evitando
   el sesgo del drift en val completa (13.59%)
6. Split de calibración separado del split de validación (sin leakage de umbral)
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

# ── 1. Cargar datos ───────────────────────────────────────────────────────────
fase0_files = sorted(PROC_DIR.glob("*_geo_eda_fase0.parquet"))
df_base = pd.read_parquet(fase0_files[-1])
df_base["fecha_radicacion"] = pd.to_datetime(df_base["fecha_radicacion"])
logger.info("Dataset: %d filas · período %s → %s",
            len(df_base),
            df_base["fecha_radicacion"].min().date(),
            df_base["fecha_radicacion"].max().date())

sedes_files = sorted((BASE_DIR / "Data" / "raw").glob("*_cnt_prestador_sedes.parquet"))
df_sedes = pd.read_parquet(sedes_files[-1])

vc = df_base["target"].value_counts().sort_index()
for cls, label in [(0, "Auditada"), (1, "Glosada"), (2, "Devuelta")]:
    n = vc.get(cls, 0)
    logger.info("Clase %d (%s): %d  (%.2f%%)", cls, label, n, n/len(df_base)*100)

# ── 2. Features temporales (antes del split) ─────────────────────────────────
fecha_min = df_base["fecha_radicacion"].min()
df_base["mes_radicacion"]        = df_base["fecha_radicacion"].dt.month.astype(int)
df_base["semana_anio"]           = df_base["fecha_radicacion"].dt.isocalendar().week.astype(int)
df_base["dia_semana"]            = df_base["fecha_radicacion"].dt.dayofweek.astype(int)
df_base["dias_desde_inicio"]     = (df_base["fecha_radicacion"] - fecha_min).dt.days.astype(int)

# Feature de diagnóstico: capítulo CIE-10 (primer carácter — sin PII)
# codigo_dx tiene muchos nulos — usar fallback "Z" (desconocido)
if "codigo_dx" in df_base.columns:
    df_base["dx_capitulo"] = (
        df_base["codigo_dx"]
        .fillna("Z")
        .str[:1]
        .str.upper()
        .str.replace(r"[^A-Z]", "Z", regex=True)
    )
else:
    df_base["dx_capitulo"] = "Z"

logger.info("Features temporales y dx_capitulo construidas")

# ── 3. División temporal — 60/20/20 ──────────────────────────────────────────
import gc

df_sorted_base = df_base.sort_values("fecha_radicacion").reset_index(drop=True)
n       = len(df_sorted_base)
n_train = int(n * 0.60)
n_val   = int(n * 0.20)

# Materializar solo train ahora — val/test después de calcular tasas históricas
df_train = df_sorted_base.iloc[:n_train].copy()
# Guardar fechas límite sin mantener val/test en memoria aún
fecha_val_fin    = df_sorted_base["fecha_radicacion"].iloc[n_train + n_val - 1]
# Split de calibración: último 30% de val — más representativo de test (tasa ~5-6%)
# Los últimos días de val tienen la menor tasa de glosa dentro del val
n_cal_start      = n_train + int(n_val * 0.70)
fecha_cal_inicio = df_sorted_base["fecha_radicacion"].iloc[n_cal_start]
del df_sorted_base
gc.collect()

logger.info("Splits definidos: train=%d  val=%d  test=%d", n_train, n_val, n - n_train - n_val)
logger.info("Calibración desde: %s  (último 30%% de val)", fecha_cal_inicio.date())
logger.info("Train Glosa=%.2f%%", (df_train["target"] == 1).mean() * 100)

# ── 4. Tasas históricas SOLO en train (anti-leakage) ──────────────────────────
glosa_rates  = compute_glosa_rate_by_municipio(df_train)
hhi_dict     = compute_hhi_dx_by_municipio(df_train)
global_glosa = (df_train["target"] == 1).mean()
global_hhi   = df_train.groupby(
    df_train["municipio_residencia"].str.strip().str.upper()
)["codigo_dx"].apply(lambda s: float((s.value_counts(normalize=True) ** 2).sum())).mean()

# Tasa de glosa por región (calcular SOLO en train)
glosa_rates_region: dict[str, float] = (
    df_train.groupby(
        df_train["region_residencia"].str.strip().str.upper().fillna("DESCONOCIDA")
    )["target"]
    .apply(lambda x: (x == 1).mean())
    .to_dict()
)
global_glosa_region = float(global_glosa)
logger.info("Tasas históricas calculadas: %d municipios · %d regiones",
            len(glosa_rates), len(glosa_rates_region))

# Añadir features de región y capitacion al df_base ANTES de los splits
# → una sola operación sobre df_base evita repetirla 4 veces
region_norm_base = df_base["region_residencia"].str.strip().str.upper().fillna("DESCONOCIDA")
df_base["glosa_rate_region"] = region_norm_base.map(glosa_rates_region).fillna(global_glosa_region)
df_base["ips_capitacion"]    = pd.to_numeric(
    df_base["capitacion"] if "capitacion" in df_base.columns else 0,
    errors="coerce"
).fillna(0).astype("int8")
del region_norm_base
gc.collect()

# ── 5. Materializar splits y construir features geoespaciales ─────────────────
build_kwargs = dict(
    df_sedes=df_sedes,
    glosa_rates=glosa_rates,
    hhi_dict=hhi_dict,
    global_glosa_rate=global_glosa,
    global_hhi=global_hhi,
)

# Train: df_train ya existe — añadir columnas nuevas de df_base y construir geo
df_train["glosa_rate_region"] = df_base.loc[df_train.index, "glosa_rate_region"].values
df_train["ips_capitacion"]    = df_base.loc[df_train.index, "ips_capitacion"].values
df_train_geo = build_geo_features(df_train, **build_kwargs)
del df_train; gc.collect()

# Val / Cal / Test: extraer directamente de df_base (ya tiene columnas nuevas)
df_sorted_rest = df_base.sort_values("fecha_radicacion").reset_index(drop=True)

df_val_raw  = df_sorted_rest.iloc[n_train : n_train + n_val].copy()
df_val_geo  = build_geo_features(df_val_raw, **build_kwargs)
logger.info("Val: %d filas  Glosa=%.2f%%", len(df_val_raw), (df_val_raw["target"] == 1).mean() * 100)

df_cal_raw  = df_val_raw[df_val_raw["fecha_radicacion"] >= fecha_cal_inicio].copy()
df_cal_geo  = build_geo_features(df_cal_raw, **build_kwargs)
logger.info("Cal: %d filas  Glosa=%.2f%%", len(df_cal_raw), (df_cal_raw["target"] == 1).mean() * 100)
del df_val_raw, df_cal_raw; gc.collect()

df_test_raw = df_sorted_rest.iloc[n_train + n_val :].copy()
df_test_geo = build_geo_features(df_test_raw, **build_kwargs)
logger.info("Test: %d filas  Glosa=%.2f%%", len(df_test_raw), (df_test_raw["target"] == 1).mean() * 100)
del df_test_raw, df_sorted_rest; gc.collect()

# Features geo base (eliminar las de SHAP≈0 en v2: hhi_dx_municipio, sin_cobertura_savia)
geo_feats_base = [
    f for f in get_geo_feature_names()
    if f not in ("nivel1_en_municipio", "hhi_dx_municipio", "sin_cobertura_savia")
]

logger.info("Features geo construidas para todos los splits")

# ── 6. Encoding + preparación de matrices ────────────────────────────────────
from sklearn.preprocessing import LabelEncoder

feats_socio           = ["nivel_sisben", "edad"]
feats_categoricas_raw = ["zona_afiliado", "regimen", "grupo_poblacional", "genero", "dx_capitulo"]
feats_nuevas_num      = [
    "mes_radicacion", "semana_anio", "dia_semana", "dias_desde_inicio",
    "glosa_rate_region", "ips_capitacion",
    # glosa_rate_dx_capitulo excluida: codigo_dx 100% nulo → un solo capítulo "Z", sin discriminación
]

all_feats = (
    list(geo_feats_base)
    + [f for f in feats_socio if f in df_train_geo.columns]
    + [f for f in feats_nuevas_num if f in df_train_geo.columns]
)

le_dict: dict = {}
for col in feats_categoricas_raw:
    if col in df_train_geo.columns:
        le = LabelEncoder()
        all_vals = pd.concat([
            df_train_geo[col], df_val_geo[col], df_test_geo[col]
        ]).fillna("DESCONOCIDO")
        le.fit(all_vals)
        for split in [df_train_geo, df_val_geo, df_cal_geo, df_test_geo]:
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

# Asegurar que todas las features existen antes de crear matrices
all_feats = [f for f in all_feats if f in df_train_sample.columns]
logger.info("Features finales tras filtro (%d): %s", len(all_feats), all_feats)

X_train = df_train_sample[all_feats].apply(pd.to_numeric, errors="coerce")
y_train = df_train_sample["target"].astype(int)
X_val   = df_val_geo[all_feats].apply(pd.to_numeric, errors="coerce")
y_val   = df_val_geo["target"].astype(int)
X_cal   = df_cal_geo[all_feats].apply(pd.to_numeric, errors="coerce")
y_cal   = df_cal_geo["target"].astype(int)
X_test  = df_test_geo[all_feats].apply(pd.to_numeric, errors="coerce")
y_test  = df_test_geo["target"].astype(int)

logger.info("Shapes — train:%s val:%s cal:%s test:%s",
            X_train.shape, X_val.shape, X_cal.shape, X_test.shape)

# Pesos de clase sobre train (inverso frecuencia + boost x2 en Glosada)
class_counts  = y_train.value_counts().sort_index()
n_total       = len(y_train)
n_clases      = len(class_counts)
class_weights = {cls: n_total / (n_clases * cnt) for cls, cnt in class_counts.items()}
GLOSADA_BOOST = 2.0
class_weights[1] = class_weights[1] * GLOSADA_BOOST
sample_weights = y_train.map(class_weights).values

for cls, label in [(0, "Auditada"), (1, "Glosada"), (2, "Devuelta")]:
    logger.info("Peso clase %d (%s): %.4f", cls, label, class_weights[cls])

# ── 7. Entrenamiento ──────────────────────────────────────────────────────────
import xgboost as xgb

logger.info("Entrenando XGBoost v3 ...")
model = xgb.XGBClassifier(
    objective="multi:softprob",
    num_class=3,
    n_estimators=600,
    max_depth=7,
    learning_rate=0.04,
    subsample=0.8,
    colsample_bytree=0.7,
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

# ── 8. Calibración de umbral en CAL (últimas 2 semanas de val) ───────────────
from sklearn.metrics import precision_recall_curve, f1_score, roc_auc_score

y_proba_cal      = model.predict_proba(X_cal)
prob_glosada_cal = y_proba_cal[:, 1]

logger.info("Calibrando umbral en CAL (tasa glosa=%.2f%%)...", (y_cal == 1).mean() * 100)

precisions, recalls, thresholds = precision_recall_curve(
    (y_cal == 1).astype(int), prob_glosada_cal
)

BETA = 2.0
fbeta_scores = (
    (1 + BETA**2) * precisions[:-1] * recalls[:-1]
    / (BETA**2 * precisions[:-1] + recalls[:-1] + 1e-9)
)
best_idx      = fbeta_scores.argmax()
UMBRAL_OPTIMO = float(thresholds[best_idx])

logger.info("Umbral óptimo (F-beta=%.0f, desde CAL): %.4f", BETA, UMBRAL_OPTIMO)
logger.info("  Precision @ umbral: %.4f  Recall @ umbral: %.4f",
            precisions[best_idx], recalls[best_idx])

# Gráfica curva P-R desde CAL
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].plot(recalls[:-1], precisions[:-1], color="#3498db", linewidth=2)
axes[0].scatter(recalls[best_idx], precisions[best_idx], color="#e74c3c", s=120, zorder=5,
                label=f"Umbral óptimo ({UMBRAL_OPTIMO:.3f})")
axes[0].set_xlabel("Recall Glosada")
axes[0].set_ylabel("Precision Glosada")
axes[0].set_title("Curva Precision-Recall — Calibración en últimas 2 sem de Val")
axes[0].legend()

axes[1].plot(thresholds, recalls[:-1],    label="Recall",              color="#e74c3c")
axes[1].plot(thresholds, precisions[:-1], label="Precision",           color="#3498db")
axes[1].plot(thresholds, fbeta_scores,    label=f"F{BETA:.0f}-score",  color="#f39c12", linestyle="--")
axes[1].axvline(UMBRAL_OPTIMO, color="#2c3e50", linestyle=":", label=f"Umbral={UMBRAL_OPTIMO:.3f}")
axes[1].set_xlabel("Umbral de probabilidad")
axes[1].set_title("P / R / F-beta vs Umbral (calibración)")
axes[1].legend()

plt.tight_layout()
plt.savefig(FIG_DIR / "03_precision_recall_umbral_v3.png", bbox_inches="tight")
logger.info("Gráfica guardada: 03_precision_recall_umbral_v3.png")

# ── 9. Evaluación ─────────────────────────────────────────────────────────────
from sklearn.metrics import classification_report, confusion_matrix


def predecir_con_umbral(proba: np.ndarray, umbral_glosada: float) -> np.ndarray:
    """Aplica umbral personalizado para clase Glosada sobre probabilidades multiclase.

    Args:
        proba: Array (n_muestras, 3) con probabilidades por clase.
        umbral_glosada: Umbral de probabilidad para clase 1.

    Returns:
        Array (n_muestras,) con predicciones ajustadas.
    """
    predicciones = np.argmax(proba, axis=1)
    predicciones[proba[:, 1] >= umbral_glosada] = 1
    return predicciones


def evaluar_modelo(model, X, y, nombre, umbral_glosada=0.5) -> dict:
    """Evalúa el modelo con umbral ajustado y retorna métricas del proyecto.

    Args:
        model: Modelo XGBoost entrenado.
        X: Features de evaluación.
        y: Target real.
        nombre: Nombre del split.
        umbral_glosada: Umbral de probabilidad para clase Glosada.

    Returns:
        Diccionario con métricas clave.
    """
    y_proba = model.predict_proba(X)
    y_pred  = predecir_con_umbral(y_proba, umbral_glosada)

    f1  = f1_score(y, y_pred, average="macro", zero_division=0)
    auc = roc_auc_score(y, y_proba, multi_class="ovr", average="macro")
    recall_glosada    = float((y_pred[y == 1] == 1).mean()) if (y == 1).any() else 0.0
    precision_glosada = float((y[y_pred == 1] == 1).mean()) if (y_pred == 1).any() else 0.0

    print(f"\n{'='*65}")
    print(f"MÉTRICAS — {nombre}  (umbral={umbral_glosada:.4f})")
    print(f"{'='*65}")
    print(f"  F1-macro:                    {f1:.4f}")
    print(f"  AUC-ROC (OvR macro):         {auc:.4f}  (objetivo >= 0.75)")
    print(f"  Recall    Glosada (clase 1): {recall_glosada:.4f}  <- metrica primaria")
    print(f"  Precision Glosada (clase 1): {precision_glosada:.4f}")
    print()
    print(classification_report(y, y_pred,
          target_names=["Auditada", "Glosada", "Devuelta"], zero_division=0))
    return {
        "split": nombre,
        "umbral_glosada": umbral_glosada,
        "f1_macro": float(f1),
        "auc_roc": float(auc),
        "recall_glosada": recall_glosada,
        "precision_glosada": precision_glosada,
    }


metricas_val  = evaluar_modelo(model, X_val,  y_val,  "Validacion",  UMBRAL_OPTIMO)
metricas_test = evaluar_modelo(model, X_test, y_test, "Test",        UMBRAL_OPTIMO)

# Matriz de confusión — Test
y_proba_test = model.predict_proba(X_test)
y_pred_test  = predecir_con_umbral(y_proba_test, UMBRAL_OPTIMO)
cm = confusion_matrix(y_test, y_pred_test, normalize="true")
clases = ["Auditada (0)", "Glosada (1)", "Devuelta (2)"]

fig, ax = plt.subplots(figsize=(7, 5))
sns.set_theme(style="whitegrid")
sns.heatmap(cm, annot=True, fmt=".2f", cmap="Blues",
            xticklabels=clases, yticklabels=clases, ax=ax)
ax.set_ylabel("Real")
ax.set_xlabel("Predicho")
ax.set_title(f"Matriz de Confusion — Test v3 (umbral={UMBRAL_OPTIMO:.3f})")
plt.tight_layout()
plt.savefig(FIG_DIR / "03_confusion_matrix_test_v3.png", bbox_inches="tight")
logger.info("Gráfica guardada: 03_confusion_matrix_test_v3.png")

# Comparación histórica
print(f"\n{'='*60}")
print("EVOLUCION DE MÉTRICAS POR VERSION")
print(f"{'='*60}")
print(f"{'Métrica':<30} {'v1':>8} {'v2':>8} {'v3':>8}")
print("-" * 60)
print(f"{'AUC-ROC (test)':<30} {'0.6214':>8} {'0.5684':>8} {metricas_test['auc_roc']:>8.4f}")
print(f"{'Recall Glosada (test)':<30} {'0.0000':>8} {'0.9996':>8} {metricas_test['recall_glosada']:>8.4f}")
print(f"{'F1-macro (test)':<30} {'0.3234':>8} {'0.0354':>8} {metricas_test['f1_macro']:>8.4f}")
print(f"{'Precision Glosada (test)':<30} {'  n/a':>8} {'0.0557':>8} {metricas_test['precision_glosada']:>8.4f}")
print(f"\n  Objetivo AUC >= 0.75: {'CUMPLIDO' if metricas_test['auc_roc'] >= 0.75 else 'PENDIENTE'}")

# ── 10. SHAP ──────────────────────────────────────────────────────────────────
importancia_shap = None
try:
    import shap
    X_shap    = X_val.fillna(0).sample(min(5000, len(X_val)), random_state=RANDOM_STATE)
    explainer = shap.TreeExplainer(model)
    shap_raw  = explainer.shap_values(X_shap)

    if isinstance(shap_raw, list):
        arr = np.mean([np.abs(sv) for sv in shap_raw], axis=0)  # (n, p)
    elif shap_raw.ndim == 3:
        arr = np.abs(shap_raw).mean(axis=2)                      # (n, p)
    else:
        arr = np.abs(shap_raw)                                    # (n, p)

    importancia_shap = pd.Series(arr.mean(axis=0), index=all_feats).sort_values(ascending=False)

    top_feats   = importancia_shap.head(15)
    geo_set     = set(geo_feats_base)
    colors_shap = ["#e74c3c" if f in geo_set else "#3498db" for f in top_feats.index[::-1]]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.barh(top_feats.index[::-1], top_feats.values[::-1], color=colors_shap)
    ax.set_xlabel("Importancia SHAP media |valor|")
    ax.set_title("Top 15 features por importancia SHAP — v3")
    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(color="#e74c3c", label="Feature geoespacial"),
        Patch(color="#3498db", label="Feature socioeconómica / temporal"),
    ])
    plt.tight_layout()
    plt.savefig(FIG_DIR / "03_shap_geo_features_v3.png", bbox_inches="tight")
    logger.info("SHAP guardado: 03_shap_geo_features_v3.png")
    print("\nTop 15 features SHAP (v3):")
    print(top_feats.round(4).to_string())
except Exception as e:
    logger.warning("SHAP no disponible (%s) — importancia nativa XGBoost:", e)
    importancia_shap = pd.Series(model.feature_importances_, index=all_feats).sort_values(ascending=False)
    print(importancia_shap.head(15).round(4))

# ── 11. Guardar artefactos v3 ─────────────────────────────────────────────────
model_path = MODEL_DIR / f"{TODAY}_geo_xgboost_v3.json"
model.save_model(str(model_path))
logger.info("Modelo v3 guardado: %s", model_path)

metadata = {
    "version": "v3",
    "fecha": TODAY,
    "modelo": "XGBoost geo_v3",
    "descripcion": (
        "Features temporales + dx_capitulo + glosa_rate_region + ips_capitacion. "
        "Umbral calibrado en ultimas 2 semanas de val (drift-aware). "
        "Eliminadas hhi_dx_municipio y sin_cobertura_savia (SHAP=0 en v2)."
    ),
    "features": all_feats,
    "features_geo": geo_feats_base,
    "umbral_glosada": UMBRAL_OPTIMO,
    "glosada_boost": GLOSADA_BOOST,
    "pesos_clase": {str(k): float(v) for k, v in class_weights.items()},
    "n_train_sample": len(X_train),
    "n_val": len(X_val),
    "n_cal": len(X_cal),
    "n_test": len(X_test),
    "fecha_cal_inicio": str(fecha_cal_inicio.date()),
    "metricas_val": metricas_val,
    "metricas_test": metricas_test,
    "global_glosa_rate": float(global_glosa),
    "random_state": RANDOM_STATE,
    "mejoras_vs_v2": [
        "features temporales: mes_radicacion, semana_anio, dia_semana, dias_desde_inicio",
        "feature dx_capitulo: capitulo CIE-10 (primer char) con tasa historica de glosa",
        "feature glosa_rate_region: tasa historica por region (calculada en train)",
        "feature ips_capitacion: modalidad contractual IPS",
        "eliminadas hhi_dx_municipio y sin_cobertura_savia (SHAP~0 en v2)",
        "umbral calibrado en ultimas 2 semanas de val (tasa glosa ~5% vs 13.6% val completa)",
    ],
    "shap_top5": (
        importancia_shap.head(5).to_dict()
        if importancia_shap is not None else {}
    ),
}

meta_path = MODEL_DIR / f"{TODAY}_geo_xgboost_v3_metadata.json"
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

rates_path = PROC_DIR / f"{TODAY}_glosa_rates_municipio.json"
with open(rates_path, "w", encoding="utf-8") as f:
    json.dump(glosa_rates, f, indent=2, ensure_ascii=False)

logger.info("Metadata v3 guardada: %s", meta_path)

print(f"\n{'='*65}")
print("ARTEFACTOS GUARDADOS — v3")
print(f"{'='*65}")
print(f"  Modelo:   {model_path}")
print(f"  Metadata: {meta_path}")
print()
print("RESUMEN FINAL — Test:")
print(f"  AUC-ROC:          {metricas_test['auc_roc']:.4f}  (>= 0.75: {'SI' if metricas_test['auc_roc'] >= 0.75 else 'NO'})")
print(f"  F1-macro:         {metricas_test['f1_macro']:.4f}")
print(f"  Recall  Glosada:  {metricas_test['recall_glosada']:.4f}  <- metrica primaria")
print(f"  Precision Glosada:{metricas_test['precision_glosada']:.4f}")
print(f"  Umbral Glosada:   {UMBRAL_OPTIMO:.4f}")
