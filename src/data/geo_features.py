"""Ingeniería de features geoespaciales para modelo predictivo de glosas.

Fase 1 del proyecto de Analítica Geoespacial · Savia Salud EPS.
Todas las funciones son puras (sin efectos secundarios en BD).
Regla: calcular tasas históricas SOLO sobre train, aplicar en val/test.
"""

import logging
import math
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

RANDOM_STATE = 42

# Rango geográfico válido para Colombia
LAT_MIN, LAT_MAX = -4.5, 14.0
LNG_MIN, LNG_MAX = -82.0, -66.0

# Umbral de distancia para flag "lejos de IPS" (percentil 75 esperado ~50 km)
DISTANCIA_ALTA_KM = 50.0


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades geométricas
# ─────────────────────────────────────────────────────────────────────────────

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calcula distancia en km entre dos puntos GPS usando fórmula Haversine.

    Args:
        lat1: Latitud punto 1 en grados decimales.
        lng1: Longitud punto 1 en grados decimales.
        lat2: Latitud punto 2 en grados decimales.
        lng2: Longitud punto 2 en grados decimales.

    Returns:
        Distancia en kilómetros. Retorna NaN si algún argumento es NaN.
    """
    if any(math.isnan(v) for v in [lat1, lng1, lat2, lng2]):
        return float("nan")
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def is_valid_colombia_coord(lat: float, lng: float) -> bool:
    """Verifica si unas coordenadas están dentro del rango geográfico de Colombia.

    Args:
        lat: Latitud en grados decimales.
        lng: Longitud en grados decimales.

    Returns:
        True si las coordenadas son válidas para Colombia.
    """
    return (
        not (math.isnan(lat) or math.isnan(lng))
        and LAT_MIN <= lat <= LAT_MAX
        and LNG_MIN <= lng <= LNG_MAX
    )


def haversine_series(
    lat1: pd.Series,
    lng1: pd.Series,
    lat2: pd.Series,
    lng2: pd.Series,
) -> pd.Series:
    """Calcula distancias Haversine vectorizadas sobre Series de pandas.

    Args:
        lat1: Latitudes origen.
        lng1: Longitudes origen.
        lat2: Latitudes destino.
        lng2: Longitudes destino.

    Returns:
        Serie con distancias en km (NaN donde faltan coordenadas).
    """
    lat1_r = np.radians(lat1.astype(float))
    lat2_r = np.radians(lat2.astype(float))
    dlat   = np.radians((lat2 - lat1).astype(float))
    dlng   = np.radians((lng2 - lng1).astype(float))

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlng / 2) ** 2
    return pd.Series(6371.0 * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a)), index=lat1.index)


# ─────────────────────────────────────────────────────────────────────────────
# Preparación de coordenadas
# ─────────────────────────────────────────────────────────────────────────────

def prepare_afiliado_coords(df: pd.DataFrame) -> pd.DataFrame:
    """Resuelve coordenadas del afiliado priorizando GPS propio sobre centroide municipal.

    Columnas requeridas en df:
        lat_afiliado_raw, lng_afiliado_raw (GPS propio, puede ser str)
        lat_municipio_res, lng_municipio_res (centroide gn_ubicaciones, numeric)

    Columnas añadidas:
        lat_origen, lng_origen: coordenada efectiva a usar
        fuente_geo: 'gps_propio' | 'centroide_municipio' | 'sin_geo'

    Args:
        df: DataFrame con datos del afiliado y municipio de residencia.

    Returns:
        DataFrame con columnas de coordenadas resueltas añadidas.
    """
    out = df.copy()

    def _get_col(df: pd.DataFrame, *candidates: str) -> pd.Series:
        """Retorna la primera columna candidata encontrada, o NaNs si ninguna existe."""
        for col in candidates:
            if col in df.columns:
                return pd.to_numeric(df[col], errors="coerce")
        return pd.Series(np.nan, index=df.index)

    # Acepta tanto lat_afiliado_raw (desde BD) como lat_afiliado (ya procesada en EDA)
    lat_gps = _get_col(out, "lat_afiliado_raw", "lat_afiliado")
    lng_gps = _get_col(out, "lng_afiliado_raw", "lng_afiliado")

    gps_valido = (
        lat_gps.between(LAT_MIN, LAT_MAX) &
        lng_gps.between(LNG_MIN, LNG_MAX)
    )

    lat_mun = _get_col(out, "lat_municipio_res")
    lng_mun = _get_col(out, "lng_municipio_res")
    mun_valido = lat_mun.between(LAT_MIN, LAT_MAX) & lng_mun.between(LNG_MIN, LNG_MAX)

    out["lat_origen"] = np.where(gps_valido, lat_gps, np.where(mun_valido, lat_mun, np.nan))
    out["lng_origen"] = np.where(gps_valido, lng_gps, np.where(mun_valido, lng_mun, np.nan))
    out["fuente_geo"] = np.where(
        gps_valido, "gps_propio",
        np.where(mun_valido, "centroide_municipio", "sin_geo")
    )

    logger.info(
        "Coordenadas resueltas — GPS propio: %d (%.1f%%) · Centroide: %d (%.1f%%) · Sin geo: %d (%.1f%%)",
        gps_valido.sum(), gps_valido.mean() * 100,
        (~gps_valido & mun_valido).sum(), (~gps_valido & mun_valido).mean() * 100,
        (~gps_valido & ~mun_valido).sum(), (~gps_valido & ~mun_valido).mean() * 100,
    )
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Features geoespaciales individuales
# ─────────────────────────────────────────────────────────────────────────────

def compute_distancia_afiliado_ips(df: pd.DataFrame) -> pd.Series:
    """Calcula distancia en km entre la ubicación del afiliado y su IPS asignada.

    Columnas requeridas: lat_origen, lng_origen, lat_ips, lng_ips (numeric).

    Args:
        df: DataFrame con coordenadas resueltas de afiliado e IPS.

    Returns:
        Serie con distancias en km (NaN donde faltan coordenadas).
    """
    lat_ips = pd.to_numeric(df["lat_ips"], errors="coerce")
    lng_ips = pd.to_numeric(df["lng_ips"], errors="coerce")

    ips_valida = lat_ips.between(LAT_MIN, LAT_MAX) & lng_ips.between(LNG_MIN, LNG_MAX)
    origen_valido = df["lat_origen"].notna() & df["lng_origen"].notna()

    mask = ips_valida & origen_valido
    result = pd.Series(np.nan, index=df.index)
    if mask.any():
        result.loc[mask] = haversine_series(
            df.loc[mask, "lat_origen"], df.loc[mask, "lng_origen"],
            lat_ips.loc[mask], lng_ips.loc[mask],
        )
    return result


def compute_misma_municipio(df: pd.DataFrame) -> pd.Series:
    """Flag 1 si el afiliado reside en el mismo municipio que su IPS asignada.

    Columnas requeridas: municipio_residencia, municipio_ips.

    Args:
        df: DataFrame con municipios de afiliado e IPS.

    Returns:
        Serie binaria (int) 0/1 con NaN donde faltan municipios.
    """
    mismo = (
        df["municipio_residencia"].str.strip().str.upper() ==
        df["municipio_ips"].str.strip().str.upper()
    )
    # float en lugar de Int64 nullable: XGBoost requiere float/int, no nullable Int64
    return mismo.astype(float)


def compute_ips_density(
    df: pd.DataFrame,
    df_sedes: pd.DataFrame,
) -> pd.Series:
    """Cuenta sedes de IPS activas en el municipio de residencia de cada fila.

    No usa datos de facturas para calcularse → no hay riesgo de leakage temporal.

    Args:
        df: DataFrame principal con columna municipio_residencia.
        df_sedes: Catálogo de sedes IPS activas con columna municipio.

    Returns:
        Serie con número de sedes IPS en el municipio de residencia.
    """
    densidad = (
        df_sedes[df_sedes.get("estado_sede", pd.Series(True)) == True]  # noqa: E712
        .groupby("municipio")
        .size()
        .rename("densidad_ips_municipio")
    )
    municipios_norm = df["municipio_residencia"].str.strip().str.upper()
    densidad.index = densidad.index.str.strip().str.upper()
    return municipios_norm.map(densidad).fillna(0).astype(int)


def compute_nivel1_en_municipio(
    df: pd.DataFrame,
    df_sedes: pd.DataFrame,
) -> pd.Series:
    """Flag 1 si el municipio de residencia tiene al menos 1 IPS de nivel 1.

    Args:
        df: DataFrame principal con columna municipio_residencia.
        df_sedes: Catálogo de sedes IPS activas con columnas municipio y nivel_atencion.

    Returns:
        Serie binaria (int) 1 si hay IPS nivel 1 en el municipio, 0 si no.
    """
    municipios_nivel1 = set(
        df_sedes.loc[df_sedes["nivel_atencion"] == 1, "municipio"]
        .str.strip().str.upper().dropna()
    )
    municipios_norm = df["municipio_residencia"].str.strip().str.upper()
    return municipios_norm.isin(municipios_nivel1).astype(int)


# ─────────────────────────────────────────────────────────────────────────────
# Tasas históricas (SOLO calcular en train, aplicar en val/test)
# ─────────────────────────────────────────────────────────────────────────────

def compute_glosa_rate_by_municipio(df_train: pd.DataFrame) -> dict[str, float]:
    """Calcula tasa histórica de glosas por municipio sobre el conjunto de entrenamiento.

    ADVERTENCIA: Llamar SOLO con df_train. Aplicar el resultado en val/test usando
    apply_glosa_rate_municipio() para evitar data leakage temporal.

    Args:
        df_train: DataFrame de entrenamiento con columnas municipio_residencia y target.

    Returns:
        Diccionario {municipio_normalizado: tasa_glosa} (float entre 0 y 1).
    """
    rates = (
        df_train.groupby(df_train["municipio_residencia"].str.strip().str.upper())["target"]
        .apply(lambda x: (x == 1).mean())
        .to_dict()
    )
    logger.info("Tasas de glosa calculadas para %d municipios", len(rates))
    return rates


def apply_glosa_rate_municipio(
    df: pd.DataFrame,
    rates: dict[str, float],
    global_rate: float,
) -> pd.Series:
    """Aplica tasas históricas de glosa por municipio a un DataFrame.

    Args:
        df: DataFrame con columna municipio_residencia.
        rates: Diccionario de tasas calculado sobre train con compute_glosa_rate_by_municipio().
        global_rate: Tasa global usada como fallback para municipios sin historial.

    Returns:
        Serie con tasa de glosa del municipio (fallback a global_rate).
    """
    municipios_norm = df["municipio_residencia"].str.strip().str.upper()
    return municipios_norm.map(rates).fillna(global_rate)


def compute_hhi_dx_by_municipio(df_train: pd.DataFrame) -> dict[str, float]:
    """Calcula índice de Herfindahl-Hirschman de concentración diagnóstica por municipio.

    HHI alto → pocos diagnósticos dominan (zona de perfil epidemiológico específico).
    ADVERTENCIA: Llamar SOLO con df_train.

    Args:
        df_train: DataFrame de entrenamiento con columnas municipio_residencia y codigo_dx.

    Returns:
        Diccionario {municipio_normalizado: hhi} (float entre 0 y 1).
    """
    def _hhi(s: pd.Series) -> float:
        counts = s.value_counts(normalize=True)
        return float((counts ** 2).sum())

    hhi = (
        df_train.groupby(df_train["municipio_residencia"].str.strip().str.upper())["codigo_dx"]
        .apply(_hhi)
        .to_dict()
    )
    logger.info("HHI diagnóstico calculado para %d municipios", len(hhi))
    return hhi


def apply_hhi_dx(
    df: pd.DataFrame,
    hhi_dict: dict[str, float],
    global_hhi: float = 0.05,
) -> pd.Series:
    """Aplica índice HHI diagnóstico por municipio a un DataFrame.

    Args:
        df: DataFrame con columna municipio_residencia.
        hhi_dict: Diccionario calculado con compute_hhi_dx_by_municipio().
        global_hhi: Fallback para municipios sin historial.

    Returns:
        Serie con HHI del municipio.
    """
    municipios_norm = df["municipio_residencia"].str.strip().str.upper()
    return municipios_norm.map(hhi_dict).fillna(global_hhi)


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline completo
# ─────────────────────────────────────────────────────────────────────────────

def build_geo_features(
    df: pd.DataFrame,
    df_sedes: pd.DataFrame,
    glosa_rates: dict[str, float],
    hhi_dict: dict[str, float],
    global_glosa_rate: float,
    global_hhi: float = 0.05,
    distancia_alta_km: float = DISTANCIA_ALTA_KM,
) -> pd.DataFrame:
    """Construye todas las features geoespaciales sobre un DataFrame.

    Usar glosa_rates y hhi_dict previamente calculados SOLO sobre train.
    Para el conjunto de train, calcular primero con compute_*_by_municipio()
    y luego llamar esta función.

    Args:
        df: DataFrame con datos de facturas + afiliados + IPS (resultado de Fase 0).
        df_sedes: Catálogo de sedes IPS activas.
        glosa_rates: Tasas de glosa por municipio (del train).
        hhi_dict: HHI diagnóstico por municipio (del train).
        global_glosa_rate: Tasa global de glosa (fallback).
        global_hhi: HHI global fallback.
        distancia_alta_km: Umbral para flag lejos_de_ips.

    Returns:
        DataFrame con features geoespaciales añadidas como columnas nuevas.
    """
    out = prepare_afiliado_coords(df)

    out["distancia_afiliado_ips_km"] = compute_distancia_afiliado_ips(out)
    out["misma_municipio_afiliado_ips"] = compute_misma_municipio(out)
    out["densidad_ips_municipio"] = compute_ips_density(out, df_sedes)
    out["nivel1_en_municipio"] = compute_nivel1_en_municipio(out, df_sedes)
    out["glosa_rate_municipio"] = apply_glosa_rate_municipio(out, glosa_rates, global_glosa_rate)
    out["hhi_dx_municipio"] = apply_hhi_dx(out, hhi_dict, global_hhi)

    # Features derivadas
    # float en lugar de Int64 nullable: XGBoost requiere float/int, no nullable Int64
    out["lejos_de_ips"] = (out["distancia_afiliado_ips_km"] > distancia_alta_km).astype(float)
    out["nivel_atencion_ips"] = pd.to_numeric(
        out["nivel_atencion_ips"] if "nivel_atencion_ips" in out.columns else pd.Series(np.nan, index=out.index),
        errors="coerce",
    )
    cobertura_col = out["municipio_con_cobertura"] if "municipio_con_cobertura" in out.columns else pd.Series(True, index=out.index)
    out["sin_cobertura_savia"] = (~cobertura_col.astype(bool)).astype(int)

    geo_cols = [
        "distancia_afiliado_ips_km", "misma_municipio_afiliado_ips",
        "densidad_ips_municipio", "nivel1_en_municipio",
        "glosa_rate_municipio", "hhi_dx_municipio",
        "lejos_de_ips", "nivel_atencion_ips", "sin_cobertura_savia",
        "fuente_geo", "lat_origen", "lng_origen",
    ]
    logger.info(
        "Features geoespaciales construidas: %s",
        [c for c in geo_cols if c in out.columns],
    )
    return out


def get_geo_feature_names() -> list[str]:
    """Retorna lista de nombres de features geoespaciales para usar en el modelo.

    Returns:
        Lista de nombres de columnas que son features geoespaciales numéricas.
    """
    return [
        "distancia_afiliado_ips_km",
        "misma_municipio_afiliado_ips",
        "densidad_ips_municipio",
        "nivel1_en_municipio",
        "glosa_rate_municipio",
        "hhi_dx_municipio",
        "lejos_de_ips",
        "nivel_atencion_ips",
        "sin_cobertura_savia",
    ]
