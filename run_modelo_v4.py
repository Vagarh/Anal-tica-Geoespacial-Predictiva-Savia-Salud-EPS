"""Modelo XGBoost v4 — Savia Salud EPS.

Cambio crítico respecto a v3:
- FILTRO DE REZAGO DE AUDITORÍA: excluir facturas radicadas en los últimos 30 días
  sin registro de auditoría cerrada. En v3, estas facturas tenían target=0 no porque
  fueran correctas sino porque la auditoría aún no había procesado. Esto hacía que
  dias_desde_inicio dominara SHAP (42%) aprendiendo el backlog, no el riesgo real.

- ELIMINACIÓN features temporales contaminadas: dias_desde_inicio, dia_semana,
  semana_anio → capturaban el rezago del proceso, no el riesgo de la factura.
  Se mantiene mes_radicacion (estacionalidad real: dic/ene tienen más glosas).

- DATASET LIMPIO: solo facturas con ≥ MIN_DIAS_MADUREZ días desde radicación,
  garantizando que la auditoría tuvo tiempo de completarse.
"""

import json
import logging
import sys
import warnings
import gc
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

# Días mínimos desde radicación para garantizar auditoría completa
# Análisis de v3: últimas 2-3 semanas tienen tasa glosa <0.5% vs 6-17% semanas previas
MIN_DIAS_MADUREZ = 30

# ── 1. Cargar datos ───────────────────────────────────────────────────────────
fase0_files = sorted(PROC_DIR.glob("*_geo_eda_fase0.parquet"))
df_base = pd.read_parquet(fase0_files[-1])
df_base["fecha_radicacion"] = pd.to_datetime(df_base["fecha_radicacion"])

logger.info("Dataset CRUDO: %d filas · período %s → %s",
            len(df_base),
            df_base["fecha_radicacion"].min().date(),
            df_base["fecha_radicacion"].max().date())

sedes_files = sorted((BASE_DIR / "Data" / "raw").glob("*_cnt_prestador_sedes.parquet"))
df_sedes = pd.read_parquet(sedes_files[-1])

# ── 2. FILTRO DE REZAGO DE AUDITORÍA ─────────────────────────────────────────
fecha_corte = df_base["fecha_radicacion"].max()
fecha_limite = fecha_corte - pd.Timedelta(days=MIN_DIAS_MADUREZ)

n_antes = len(df_base)
df_base = df_base[df_base["fecha_radicacion"] <= fecha_limite].copy()
n_filtradas = n_antes - len(df_base)

logger.info("FILTRO REZAGO: fecha_corte=%s  fecha_limite=%s",
            fecha_corte.date(), fecha_limite.date())
logger.info("  Filas eliminadas: %d (%.1f%%) — facturas sin auditoría completa",
            n_filtradas, n_filtradas / n_antes * 100)
logger.info("  Filas restantes: %d", len(df_base))

vc = df_base["target"].value_counts().sort_index()
for cls, label in [(0, "Auditada"), (1, "Glosada"), (2, "Devuelta")]:
    n = vc.get(cls, 0)
    logger.info("  Clase %d (%s): %d  (%.2f%%)", cls, label, n, n/len(df_base)*100)

# ── 3. Features — SOLO las causales (sin contaminación temporal) ──────────────
# mes_radicacion: estacionalidad real (diciembre/enero más glosas)
# EXCLUIDAS: dias_desde_inicio (42% SHAP en v3 = backlog auditoría)
#            dia_semana        (10% SHAP en v3 = patrón procesamiento)
#            semana_anio       (8%  SHAP en v3 = rezago semanal)
df_base["mes_radicacion"] = df_base["fecha_radicacion"].dt.month.astype(int)

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

logger.info("Features construidas: mes_radicacion + dx_capitulo (sin features de rezago)")

# ── 4. División temporal — 60/20/20 ──────────────────────────────────────────
df_sorted_base = df_base.sort_values("fecha_radicacion").reset_index(drop=True)
n       = len(df_sorted_base)
n_train = int(n * 0.60)
n_val   = int(n * 0.20)

df_train = df_sorted_base.iloc[:n_train].copy()

fecha_val_inicio = df_sorted_base["fecha_radicacion"].iloc[n_train]
fecha_val_fin    = df_sorted_base["fecha_radicacion"].iloc[n_train + n_val - 1]
fecha_test_inicio = df_sorted_base["fecha_radicacion"].iloc[n_train + n_val]
fecha_test_fin    = df_sorted_base["fecha_radicacion"].iloc[-1]

# Calibración: último 30% de val
n_cal_start      = n_train + int(n_val * 0.70)
fecha_cal_inicio = df_sorted_base["fecha_radicacion"].iloc[n_cal_start]

del df_sorted_base
gc.collect()

logger.info("Splits definidos: train=%d  val=%d  test=%d", n_train, n_val, n - n_train - n_val)
logger.info("  Train: %s → %s  Glosa=%.2f%%",
            df_base["fecha_radicacion"].min().date(),
            df_train["fecha_radicacion"].max().date(),
            (df_train["target"] == 1).mean() * 100)
logger.info("  Val:  %s → %s", fecha_val_inicio.date(), fecha_val_fin.date())
logger.info("  Test: %s → %s", fecha_test_inicio.date(), fecha_test_fin.date())
logger.info("  Cal desde: %s (último 30%% de val)", fecha_cal_inicio.date())

# ── 5. Tasas históricas SOLO en train (anti-leakage) ─────────────────────────
glosa_rates  = compute_glosa_rate_by_municipio(df_train)
hhi_dict     = compute_hhi_dx_by_municipio(df_train)
global_glosa = (df_train["target"] == 1).mean()
global_hhi   = df_train.groupby(
    df_train["municipio_residencia"].str.strip().str.upper()
)["codigo_dx"].apply(lambda s: float((s.value_counts(normalize=True) ** 2).sum())).mean()

glosa_rates_region: dict[str, float] = (
    df_train.groupby(
        df_train["region_residencia"].str.strip().str.upper().fillna("DESCONOCIDA")
    )["target"]
    .apply(lambda x: (x == 1).mean())
    .to_dict()
)
global_glosa_region = float(global_glosa)

# Tasa histórica de glosa por capítulo CIE-10 (calculada solo en train)
glosa_rates_dx_capitulo: dict[str, float] = (
    df_train.groupby(
        df_train["dx_capitulo"].fillna("Z")
    )["target"]
    .apply(lambda x: (x == 1).mean())
    .to_dict()
)
global_glosa_dx = float(global_glosa)

logger.info("Tasas históricas: %d municipios · %d regiones · %d capítulos CIE-10",
            len(glosa_rates), len(glosa_rates_region), len(glosa_rates_dx_capitulo))

# Añadir features derivadas a df_base antes de splits
region_norm = df_base["region_residencia"].str.strip().str.upper().fillna("DESCONOCIDA")
df_base["glosa_rate_region"]     = region_norm.map(glosa_rates_region).fillna(global_glosa_region)
df_base["glosa_rate_dx_capitulo"] = df_base["dx_capitulo"].map(glosa_rates_dx_capitulo).fillna(global_glosa_dx)
df_base["ips_capitacion"] = pd.to_numeric(
    df_base["capitacion"] if "capitacion" in df_base.columns else 0,
    errors="coerce"
).fillna(0).astype("int8")
del region_norm
gc.collect()

# ── 6. Materializar splits y construir features geoespaciales ─────────────────
build_kwargs = dict(
    df_sedes=df_sedes,
    glosa_rates=glosa_rates,
    hhi_dict=hhi_dict,
    global_glosa_rate=global_glosa,
    global_hhi=global_hhi,
)

df_train["glosa_rate_region"]      = df_base.loc[df_train.index, "glosa_rate_region"].values
df_train["glosa_rate_dx_capitulo"] = df_base.loc[df_train.index, "glosa_rate_dx_capitulo"].values
df_train["ips_capitacion"]         = df_base.loc[df_train.index, "ips_capitacion"].values
df_train_geo = build_geo_features(df_train, **build_kwargs)
del df_train; gc.collect()

df_sorted_rest = df_base.sort_values("fecha_radicacion").reset_index(drop=True)

df_val_raw  = df_sorted_rest.iloc[n_train : n_train + n_val].copy()
df_val_geo  = build_geo_features(df_val_raw, **build_kwargs)
logger.info("Val Glosa=%.2f%%", (df_val_raw["target"] == 1).mean() * 100)

df_cal_raw  = df_val_raw[df_val_raw["fecha_radicacion"] >= fecha_cal_inicio].copy()
df_cal_geo  = build_geo_features(df_cal_raw, **build_kwargs)
logger.info("Cal Glosa=%.2f%%  n=%d", (df_cal_raw["target"] == 1).mean() * 100, len(df_cal_raw))
del df_val_raw, df_cal_raw; gc.collect()

df_test_raw = df_sorted_rest.iloc[n_train + n_val :].copy()
df_test_geo = build_geo_features(df_test_raw, **build_kwargs)
logger.info("Test Glosa=%.2f%%", (df_test_raw["target"] == 1).mean() * 100)
del df_test_raw, df_sorted_rest; gc.collect()

# ── 7. Features — sin temporales contaminadas ────────────────────────────────
from sklearn.preprocessing import LabelEncoder

geo_feats_base = [
    f for f in get_geo_feature_names()
    if f not in ("nivel1_en_municipio", "hhi_dx_municipio", "sin_cobertura_savia")
]

feats_socio      = ["nivel_sisben", "edad"]
# mes_radicacion: estacionalidad válida. dias_desde_inicio/dia_semana/semana_anio: EXCLUIDAS
feats_nuevas_num = [
    "mes_radicacion",
    "glosa_rate_region",
    "glosa_rate_dx_capitulo",   # nueva en v4 — tasa histórica por capítulo CIE-10
    "ips_capitacion",
]

feats_categoricas_raw = ["zona_afiliado", "regimen", "grupo_poblacional", "genero", "dx_capitulo"]

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

# Submuestreo estratificado train
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

all_feats = [f for f in all_feats if f in df_train_sample.columns]
logger.info("Features finales (%d): %s", len(all_feats), all_feats)

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

# Pesos de clase
class_counts  = y_train.value_counts().sort_index()
n_total       = len(y_train)
n_clases      = len(class_counts)
class_weights = {cls: n_total / (n_clases * cnt) for cls, cnt in class_counts.items()}
GLOSADA_BOOST = 2.0
class_weights[1] = class_weights[1] * GLOSADA_BOOST
sample_weights = y_train.map(class_weights).values

for cls, label in [(0, "Auditada"), (1, "Glosada"), (2, "Devuelta")]:
    logger.info("Peso clase %d (%s): %.4f", cls, label, class_weights[cls])

# ── 8. Entrenamiento ──────────────────────────────────────────────────────────
import xgboost as xgb

logger.info("Entrenando XGBoost v4 ...")
model = xgb.XGBClassifier(
    objective="multi:softprob",
    num_class=3,
    n_estimators=600,
    max_depth=6,           # reducido vs v3 (7) — datos más limpios, menos overfitting
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.75,
    min_child_weight=5,    # aumentado — con datos filtrados hay menos ruido
    max_delta_step=1,
    reg_alpha=0.1,
    reg_lambda=1.5,        # más regularización — dataset más pequeño tras filtro
    random_state=RANDOM_STATE,
    eval_metric="mlogloss",
    early_stopping_rounds=50,
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

# ── 9. Calibración de umbral en CAL ──────────────────────────────────────────
from sklearn.metrics import precision_recall_curve, f1_score, roc_auc_score, classification_report, confusion_matrix

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

logger.info("Umbral óptimo (F-beta=%.0f): %.4f  Precision=%.4f  Recall=%.4f",
            BETA, UMBRAL_OPTIMO, precisions[best_idx], recalls[best_idx])

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].plot(recalls[:-1], precisions[:-1], color="#3498db", linewidth=2)
axes[0].scatter(recalls[best_idx], precisions[best_idx], color="#e74c3c", s=120, zorder=5,
                label=f"Umbral óptimo ({UMBRAL_OPTIMO:.3f})")
axes[0].set_xlabel("Recall Glosada"); axes[0].set_ylabel("Precision Glosada")
axes[0].set_title("Curva Precision-Recall — v4 (datos filtrados)")
axes[0].legend()

axes[1].plot(thresholds, recalls[:-1],    label="Recall",    color="#e74c3c")
axes[1].plot(thresholds, precisions[:-1], label="Precision", color="#3498db")
axes[1].plot(thresholds, fbeta_scores,    label=f"F{BETA:.0f}-score", color="#f39c12", linestyle="--")
axes[1].axvline(UMBRAL_OPTIMO, color="#2c3e50", linestyle=":", label=f"Umbral={UMBRAL_OPTIMO:.3f}")
axes[1].set_xlabel("Umbral"); axes[1].set_title("P / R / F-beta vs Umbral — v4")
axes[1].legend()
plt.tight_layout()
plt.savefig(FIG_DIR / "04_precision_recall_umbral_v4.png", bbox_inches="tight")
logger.info("Guardado: 04_precision_recall_umbral_v4.png")

# ── 10. Evaluación ────────────────────────────────────────────────────────────
def predecir_con_umbral(proba: np.ndarray, umbral_glosada: float) -> np.ndarray:
    """Aplica umbral personalizado para clase Glosada.

    Args:
        proba: Array (n_muestras, 3) con probabilidades por clase.
        umbral_glosada: Umbral de probabilidad para clase 1.

    Returns:
        Array (n_muestras,) con predicciones ajustadas.
    """
    predicciones = np.argmax(proba, axis=1)
    predicciones[proba[:, 1] >= umbral_glosada] = 1
    return predicciones


def evaluar_modelo(model, X, y, nombre: str, umbral_glosada: float = 0.5) -> dict:
    """Evalúa el modelo con umbral ajustado y retorna métricas del proyecto.

    Args:
        model: Modelo XGBoost entrenado.
        X: Features de evaluación.
        y: Target real.
        nombre: Nombre del split para logging.
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
ax.set_ylabel("Real"); ax.set_xlabel("Predicho")
ax.set_title(f"Matriz de Confusión — Test v4 (umbral={UMBRAL_OPTIMO:.3f})")
plt.tight_layout()
plt.savefig(FIG_DIR / "04_confusion_matrix_test_v4.png", bbox_inches="tight")
logger.info("Guardado: 04_confusion_matrix_test_v4.png")

# ── 11. Guardar modelo inmediatamente (antes de prints y SHAP) ───────────────
model_path = MODEL_DIR / f"{TODAY}_geo_xgboost_v4.json"
model.save_model(str(model_path))
logger.info("Modelo v4 guardado: %s", model_path)

# ── 12. SHAP ──────────────────────────────────────────────────────────────────
importancia_shap = None
try:
    import shap
    X_shap    = X_val.fillna(0).sample(min(5000, len(X_val)), random_state=RANDOM_STATE)
    explainer = shap.TreeExplainer(model)
    shap_raw  = explainer.shap_values(X_shap)

    if isinstance(shap_raw, list):
        arr = np.mean([np.abs(sv) for sv in shap_raw], axis=0)
    elif shap_raw.ndim == 3:
        arr = np.abs(shap_raw).mean(axis=2)
    else:
        arr = np.abs(shap_raw)

    importancia_shap = pd.Series(arr.mean(axis=0), index=all_feats).sort_values(ascending=False)

    top_feats   = importancia_shap.head(15)
    geo_set     = set(geo_feats_base)
    colors_shap = ["#e74c3c" if f in geo_set else "#3498db" for f in top_feats.index[::-1]]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.barh(top_feats.index[::-1], top_feats.values[::-1], color=colors_shap)
    ax.set_xlabel("Importancia SHAP media |valor|")
    ax.set_title("Top 15 features por importancia SHAP — v4 (sin rezago)")
    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(color="#e74c3c", label="Feature geoespacial"),
        Patch(color="#3498db", label="Feature socioeconómica / causal"),
    ])
    plt.tight_layout()
    plt.savefig(FIG_DIR / "04_shap_geo_features_v4.png", bbox_inches="tight")
    logger.info("SHAP guardado: 04_shap_geo_features_v4.png")
    print("\nTop 15 features SHAP (v4):")
    print(importancia_shap.head(15).round(4).to_string())
except Exception as e:
    logger.warning("SHAP no disponible (%s) — importancia nativa XGBoost:", e)
    importancia_shap = pd.Series(model.feature_importances_, index=all_feats).sort_values(ascending=False)
    print(importancia_shap.head(15).round(4))

# ── 13. Guardar metadata y rates ─────────────────────────────────────────────
metadata = {
    "version": "v4",
    "fecha": TODAY,
    "modelo": "XGBoost geo_v4",
    "descripcion": (
        f"Filtro rezago auditoría (≥{MIN_DIAS_MADUREZ} días). "
        "Eliminadas features temporales contaminadas (dias_desde_inicio, dia_semana, semana_anio). "
        "Añadida glosa_rate_dx_capitulo (tasa histórica por capítulo CIE-10)."
    ),
    "features": all_feats,
    "features_geo": geo_feats_base,
    "umbral_glosada": UMBRAL_OPTIMO,
    "glosada_boost": GLOSADA_BOOST,
    "pesos_clase": {str(k): float(v) for k, v in class_weights.items()},
    "min_dias_madurez": MIN_DIAS_MADUREZ,
    "n_train_sample": len(X_train),
    "n_val": len(X_val),
    "n_cal": len(X_cal),
    "n_test": len(X_test),
    "fecha_cal_inicio": str(fecha_cal_inicio.date()),
    "metricas_val": metricas_val,
    "metricas_test": metricas_test,
    "global_glosa_rate": float(global_glosa),
    "random_state": RANDOM_STATE,
    "cambios_vs_v3": [
        f"FILTRO REZAGO: solo facturas con >= {MIN_DIAS_MADUREZ} días desde radicación",
        "ELIMINADAS: dias_desde_inicio (42% SHAP en v3 = backlog auditoría)",
        "ELIMINADAS: dia_semana (10% SHAP = patrón procesamiento, no riesgo)",
        "ELIMINADAS: semana_anio (8% SHAP = rezago semanal)",
        "MANTENIDA: mes_radicacion (estacionalidad real válida)",
        "NUEVA: glosa_rate_dx_capitulo (tasa histórica por capítulo CIE-10, anti-leakage)",
        "Hiperparámetros ajustados: max_depth=6, min_child_weight=5, reg_lambda=1.5",
    ],
    "shap_top5": (
        importancia_shap.head(5).to_dict()
        if importancia_shap is not None else {}
    ),
}

meta_path = MODEL_DIR / f"{TODAY}_geo_xgboost_v4_metadata.json"
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

rates_path = PROC_DIR / f"{TODAY}_glosa_rates_municipio_v4.json"
with open(rates_path, "w", encoding="utf-8") as f:
    json.dump(glosa_rates, f, indent=2, ensure_ascii=False)

logger.info("Metadata v4 guardada: %s", meta_path)

print(f"\n{'='*65}")
print("ARTEFACTOS GUARDADOS — v4")
print(f"{'='*65}")
print(f"  Modelo:   {model_path}")
print(f"  Metadata: {meta_path}")
print()
print("RESUMEN FINAL — Test:")
print(f"  AUC-ROC:           {metricas_test['auc_roc']:.4f}  (>= 0.75: {'SI' if metricas_test['auc_roc'] >= 0.75 else 'NO - ver analisis'})")
print(f"  F1-macro:          {metricas_test['f1_macro']:.4f}")
print(f"  Recall  Glosada:   {metricas_test['recall_glosada']:.4f}")
print(f"  Precision Glosada: {metricas_test['precision_glosada']:.4f}")
print(f"  Umbral Glosada:    {UMBRAL_OPTIMO:.4f}")
print(f"  Filas filtradas:   {n_filtradas:,} ({n_filtradas/n_antes*100:.1f}% del dataset original)")
