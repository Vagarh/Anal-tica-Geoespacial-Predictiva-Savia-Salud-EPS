"""Tests unitarios para src/data/geo_features.py — cobertura objetivo ≥80%.

Ejecutar con: pytest tests/test_geo_features.py -v --tb=short
"""

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.geo_features import (
    DISTANCIA_ALTA_KM,
    LAT_MAX,
    LAT_MIN,
    LNG_MAX,
    LNG_MIN,
    apply_glosa_rate_municipio,
    apply_hhi_dx,
    build_geo_features,
    compute_distancia_afiliado_ips,
    compute_glosa_rate_by_municipio,
    compute_hhi_dx_by_municipio,
    compute_ips_density,
    compute_misma_municipio,
    compute_nivel1_en_municipio,
    get_geo_feature_names,
    haversine_distance,
    haversine_series,
    is_valid_colombia_coord,
    prepare_afiliado_coords,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def df_facturas_basico() -> pd.DataFrame:
    """DataFrame mínimo con datos de facturas, afiliados e IPS."""
    return pd.DataFrame({
        "factura_id":            [1, 2, 3, 4],
        "municipio_residencia":  ["MEDELLÍN", "BOGOTÁ", "CALI", "MEDELLÍN"],
        "lat_afiliado_raw":      ["6.244", "4.711", "3.420", None],
        "lng_afiliado_raw":      ["-75.574", "-74.072", "-76.522", None],
        "lat_municipio_res":     [6.244, 4.711, 3.420, 6.244],
        "lng_municipio_res":     [-75.574, -74.072, -76.522, -75.574],
        "lat_ips":               [6.250, 4.700, 3.430, 6.250],
        "lng_ips":               [-75.580, -74.080, -76.530, -75.580],
        "municipio_ips":         ["MEDELLÍN", "BOGOTÁ", "PEREIRA", "MEDELLÍN"],
        "nivel_atencion_ips":    [1, 2, 1, 3],
        "municipio_con_cobertura": [True, True, False, True],
        "codigo_dx":             ["J06", "I10", "E11", "J06"],
        "target":                [0, 1, 0, 1],
        "fecha_radicacion":      pd.to_datetime(["2026-01-01", "2026-01-15", "2026-02-01", "2026-02-15"]),
    })


@pytest.fixture
def df_sedes_basico() -> pd.DataFrame:
    """DataFrame de sedes IPS activas."""
    return pd.DataFrame({
        "municipio":        ["MEDELLÍN", "MEDELLÍN", "BOGOTÁ", "CALI"],
        "nivel_atencion":   [1, 2, 1, 2],
        "estado_sede":      [True, True, True, True],
        "lat_ips":          [6.250, 6.260, 4.700, 3.430],
        "lng_ips":          [-75.580, -75.590, -74.080, -76.530],
    })


# ─────────────────────────────────────────────────────────────────────────────
# haversine_distance
# ─────────────────────────────────────────────────────────────────────────────

class TestHaversineDistance:
    def test_misma_ubicacion_es_cero(self):
        assert haversine_distance(6.244, -75.574, 6.244, -75.574) == pytest.approx(0.0)

    def test_distancia_conocida_medellin_bogota(self):
        # Medellín → Bogotá ≈ 243 km en línea recta
        dist = haversine_distance(6.244, -75.574, 4.711, -74.072)
        assert 230 <= dist <= 260

    def test_retorna_nan_si_lat1_es_nan(self):
        assert math.isnan(haversine_distance(float("nan"), -75.574, 4.711, -74.072))

    def test_retorna_nan_si_lng2_es_nan(self):
        assert math.isnan(haversine_distance(6.244, -75.574, 4.711, float("nan")))

    def test_simetria(self):
        d1 = haversine_distance(6.244, -75.574, 4.711, -74.072)
        d2 = haversine_distance(4.711, -74.072, 6.244, -75.574)
        assert d1 == pytest.approx(d2)

    def test_resultado_positivo(self):
        dist = haversine_distance(3.420, -76.522, 6.244, -75.574)
        assert dist > 0


# ─────────────────────────────────────────────────────────────────────────────
# haversine_series
# ─────────────────────────────────────────────────────────────────────────────

class TestHaversineSeries:
    def test_longitud_resultado_igual_al_input(self, df_facturas_basico):
        df = df_facturas_basico.copy()
        result = haversine_series(
            pd.Series([6.244, 4.711]),
            pd.Series([-75.574, -74.072]),
            pd.Series([6.244, 4.711]),
            pd.Series([-75.574, -74.072]),
        )
        assert len(result) == 2

    def test_distancias_iguales_a_escalar(self):
        lat1 = pd.Series([6.244])
        lng1 = pd.Series([-75.574])
        lat2 = pd.Series([4.711])
        lng2 = pd.Series([-74.072])
        dist_vec = haversine_series(lat1, lng1, lat2, lng2).iloc[0]
        dist_esc = haversine_distance(6.244, -75.574, 4.711, -74.072)
        assert dist_vec == pytest.approx(dist_esc, rel=1e-6)


# ─────────────────────────────────────────────────────────────────────────────
# is_valid_colombia_coord
# ─────────────────────────────────────────────────────────────────────────────

class TestIsValidColombiaCoord:
    def test_medellin_es_valido(self):
        assert is_valid_colombia_coord(6.244, -75.574) is True

    def test_fuera_de_rango_lat(self):
        assert is_valid_colombia_coord(20.0, -75.574) is False

    def test_fuera_de_rango_lng(self):
        assert is_valid_colombia_coord(6.244, -60.0) is False

    def test_nan_es_invalido(self):
        assert is_valid_colombia_coord(float("nan"), -75.574) is False


# ─────────────────────────────────────────────────────────────────────────────
# prepare_afiliado_coords
# ─────────────────────────────────────────────────────────────────────────────

class TestPrepareAfiliadorCoords:
    def test_usa_gps_propio_si_valido(self, df_facturas_basico):
        out = prepare_afiliado_coords(df_facturas_basico)
        # Fila 0 tiene GPS propio válido
        assert out.loc[0, "fuente_geo"] == "gps_propio"
        assert out.loc[0, "lat_origen"] == pytest.approx(6.244, rel=1e-4)

    def test_usa_centroide_cuando_no_hay_gps(self, df_facturas_basico):
        out = prepare_afiliado_coords(df_facturas_basico)
        # Fila 3 no tiene GPS (lat_afiliado_raw = None)
        assert out.loc[3, "fuente_geo"] == "centroide_municipio"

    def test_sin_geo_si_ambos_nulos(self):
        df = pd.DataFrame({
            "lat_afiliado_raw": [None],
            "lng_afiliado_raw": [None],
            "lat_municipio_res": [None],
            "lng_municipio_res": [None],
        })
        out = prepare_afiliado_coords(df)
        assert out.loc[0, "fuente_geo"] == "sin_geo"
        assert math.isnan(out.loc[0, "lat_origen"])

    def test_columnas_nuevas_existen(self, df_facturas_basico):
        out = prepare_afiliado_coords(df_facturas_basico)
        assert "lat_origen" in out.columns
        assert "lng_origen" in out.columns
        assert "fuente_geo" in out.columns


# ─────────────────────────────────────────────────────────────────────────────
# compute_distancia_afiliado_ips
# ─────────────────────────────────────────────────────────────────────────────

class TestComputeDistanciaAfiliadorIps:
    def test_calcula_distancia_para_coordenadas_validas(self, df_facturas_basico):
        df = prepare_afiliado_coords(df_facturas_basico)
        dists = compute_distancia_afiliado_ips(df)
        assert dists.notna().any()
        assert (dists.dropna() >= 0).all()

    def test_nan_cuando_ips_fuera_de_rango(self, df_facturas_basico):
        df = prepare_afiliado_coords(df_facturas_basico).copy()
        df["lat_ips"] = 999.0
        dists = compute_distancia_afiliado_ips(df)
        assert dists.isna().all()

    def test_longitud_igual_al_input(self, df_facturas_basico):
        df = prepare_afiliado_coords(df_facturas_basico)
        dists = compute_distancia_afiliado_ips(df)
        assert len(dists) == len(df)


# ─────────────────────────────────────────────────────────────────────────────
# compute_misma_municipio
# ─────────────────────────────────────────────────────────────────────────────

class TestComputeMismaMunicipio:
    def test_mismo_municipio_retorna_1(self, df_facturas_basico):
        result = compute_misma_municipio(df_facturas_basico)
        assert result.iloc[0] == 1  # MEDELLÍN == MEDELLÍN

    def test_diferente_municipio_retorna_0(self, df_facturas_basico):
        result = compute_misma_municipio(df_facturas_basico)
        assert result.iloc[2] == 0  # CALI != PEREIRA

    def test_case_insensitive(self):
        df = pd.DataFrame({
            "municipio_residencia": ["medellín", "Bogotá"],
            "municipio_ips":        ["MEDELLÍN", "bogotá"],
        })
        result = compute_misma_municipio(df)
        assert result.iloc[0] == 1
        assert result.iloc[1] == 1


# ─────────────────────────────────────────────────────────────────────────────
# compute_ips_density
# ─────────────────────────────────────────────────────────────────────────────

class TestComputeIpsDensity:
    def test_medellin_tiene_2_sedes(self, df_facturas_basico, df_sedes_basico):
        result = compute_ips_density(df_facturas_basico, df_sedes_basico)
        assert result.iloc[0] == 2  # MEDELLÍN tiene 2 sedes

    def test_municipio_sin_sedes_retorna_0(self, df_sedes_basico):
        df = pd.DataFrame({"municipio_residencia": ["TUMACO"]})
        result = compute_ips_density(df, df_sedes_basico)
        assert result.iloc[0] == 0

    def test_longitud_igual_al_input(self, df_facturas_basico, df_sedes_basico):
        result = compute_ips_density(df_facturas_basico, df_sedes_basico)
        assert len(result) == len(df_facturas_basico)


# ─────────────────────────────────────────────────────────────────────────────
# compute_nivel1_en_municipio
# ─────────────────────────────────────────────────────────────────────────────

class TestComputeNivel1EnMunicipio:
    def test_medellin_tiene_nivel1(self, df_facturas_basico, df_sedes_basico):
        result = compute_nivel1_en_municipio(df_facturas_basico, df_sedes_basico)
        assert result.iloc[0] == 1

    def test_cali_sin_nivel1_retorna_0(self, df_sedes_basico):
        # df_sedes_basico tiene CALI solo con nivel 2
        df = pd.DataFrame({"municipio_residencia": ["CALI"]})
        result = compute_nivel1_en_municipio(df, df_sedes_basico)
        assert result.iloc[0] == 0


# ─────────────────────────────────────────────────────────────────────────────
# compute_glosa_rate_by_municipio
# ─────────────────────────────────────────────────────────────────────────────

class TestComputeGlosaRate:
    def test_tasa_correcta_para_medellin(self, df_facturas_basico):
        # MEDELLÍN: facturas [0,3], targets [0,1] → tasa = 0.5
        rates = compute_glosa_rate_by_municipio(df_facturas_basico)
        assert rates.get("MEDELLÍN") == pytest.approx(0.5)

    def test_retorna_dict(self, df_facturas_basico):
        rates = compute_glosa_rate_by_municipio(df_facturas_basico)
        assert isinstance(rates, dict)

    def test_todos_los_municipios_presentes(self, df_facturas_basico):
        rates = compute_glosa_rate_by_municipio(df_facturas_basico)
        for m in ["MEDELLÍN", "BOGOTÁ", "CALI"]:
            assert m in rates

    def test_tasas_entre_0_y_1(self, df_facturas_basico):
        rates = compute_glosa_rate_by_municipio(df_facturas_basico)
        for v in rates.values():
            assert 0.0 <= v <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# apply_glosa_rate_municipio
# ─────────────────────────────────────────────────────────────────────────────

class TestApplyGlosaRate:
    def test_aplica_tasa_conocida(self, df_facturas_basico):
        rates = {"MEDELLÍN": 0.5, "BOGOTÁ": 0.2}
        result = apply_glosa_rate_municipio(df_facturas_basico, rates, global_rate=0.1)
        assert result.iloc[0] == pytest.approx(0.5)

    def test_fallback_global_para_municipio_desconocido(self):
        df = pd.DataFrame({"municipio_residencia": ["TUMACO"]})
        result = apply_glosa_rate_municipio(df, {}, global_rate=0.13)
        assert result.iloc[0] == pytest.approx(0.13)

    def test_longitud_igual_al_input(self, df_facturas_basico):
        rates = compute_glosa_rate_by_municipio(df_facturas_basico)
        result = apply_glosa_rate_municipio(df_facturas_basico, rates, 0.1)
        assert len(result) == len(df_facturas_basico)


# ─────────────────────────────────────────────────────────────────────────────
# compute_hhi_dx_by_municipio
# ─────────────────────────────────────────────────────────────────────────────

class TestComputeHhiDx:
    def test_hhi_entre_0_y_1(self, df_facturas_basico):
        hhi = compute_hhi_dx_by_municipio(df_facturas_basico)
        for v in hhi.values():
            assert 0.0 < v <= 1.0

    def test_municipio_un_solo_dx_hhi_1(self):
        df = pd.DataFrame({
            "municipio_residencia": ["BOGOTÁ", "BOGOTÁ"],
            "codigo_dx": ["I10", "I10"],
            "target": [1, 1],
        })
        hhi = compute_hhi_dx_by_municipio(df)
        assert hhi.get("BOGOTÁ") == pytest.approx(1.0)

    def test_retorna_dict(self, df_facturas_basico):
        hhi = compute_hhi_dx_by_municipio(df_facturas_basico)
        assert isinstance(hhi, dict)


# ─────────────────────────────────────────────────────────────────────────────
# apply_hhi_dx
# ─────────────────────────────────────────────────────────────────────────────

class TestApplyHhiDx:
    def test_aplica_hhi_conocido(self, df_facturas_basico):
        hhi_dict = {"MEDELLÍN": 0.8}
        result = apply_hhi_dx(df_facturas_basico, hhi_dict, global_hhi=0.05)
        assert result.iloc[0] == pytest.approx(0.8)

    def test_fallback_global(self):
        df = pd.DataFrame({"municipio_residencia": ["DESCONOCIDO"]})
        result = apply_hhi_dx(df, {}, global_hhi=0.05)
        assert result.iloc[0] == pytest.approx(0.05)


# ─────────────────────────────────────────────────────────────────────────────
# build_geo_features (pipeline completo)
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildGeoFeatures:
    def test_columnas_geo_presentes(self, df_facturas_basico, df_sedes_basico):
        rates = compute_glosa_rate_by_municipio(df_facturas_basico)
        hhi   = compute_hhi_dx_by_municipio(df_facturas_basico)
        out = build_geo_features(
            df_facturas_basico, df_sedes_basico,
            rates, hhi,
            global_glosa_rate=0.13,
        )
        for col in get_geo_feature_names():
            assert col in out.columns, f"Falta columna: {col}"

    def test_no_modifica_filas(self, df_facturas_basico, df_sedes_basico):
        rates = compute_glosa_rate_by_municipio(df_facturas_basico)
        hhi   = compute_hhi_dx_by_municipio(df_facturas_basico)
        out = build_geo_features(
            df_facturas_basico, df_sedes_basico,
            rates, hhi,
            global_glosa_rate=0.13,
        )
        assert len(out) == len(df_facturas_basico)

    def test_no_modifica_input(self, df_facturas_basico, df_sedes_basico):
        cols_orig = set(df_facturas_basico.columns)
        rates = compute_glosa_rate_by_municipio(df_facturas_basico)
        hhi   = compute_hhi_dx_by_municipio(df_facturas_basico)
        build_geo_features(df_facturas_basico, df_sedes_basico, rates, hhi, 0.13)
        assert set(df_facturas_basico.columns) == cols_orig

    def test_lejos_de_ips_es_binario(self, df_facturas_basico, df_sedes_basico):
        rates = compute_glosa_rate_by_municipio(df_facturas_basico)
        hhi   = compute_hhi_dx_by_municipio(df_facturas_basico)
        out = build_geo_features(df_facturas_basico, df_sedes_basico, rates, hhi, 0.13)
        lejos = out["lejos_de_ips"].dropna()
        assert set(lejos.unique()).issubset({0, 1})


# ─────────────────────────────────────────────────────────────────────────────
# get_geo_feature_names
# ─────────────────────────────────────────────────────────────────────────────

class TestGetGeoFeatureNames:
    def test_retorna_lista_no_vacia(self):
        names = get_geo_feature_names()
        assert isinstance(names, list)
        assert len(names) > 0

    def test_contiene_features_criticas(self):
        names = get_geo_feature_names()
        criticas = ["distancia_afiliado_ips_km", "glosa_rate_municipio", "nivel_atencion_ips"]
        for feat in criticas:
            assert feat in names
