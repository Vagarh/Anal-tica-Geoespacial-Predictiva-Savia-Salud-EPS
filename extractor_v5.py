"""Extracción dataset v5 — Savia Salud EPS.

Cambios respecto a extracción original (3 meses):
1. PERIODO: 6 meses en lugar de 3 — más datos maduros para aprender patrones.
2. FILTRO MADUREZ EN SQL: solo facturas con fecha_radicacion <= NOW() - 30 días,
   garantizando que la auditoría tuvo tiempo de completarse. Esto evita el sesgo
   de target=0 artificial en facturas recientes sin auditar.
3. codigo_dx CORRECTO: el query original traía NULL porque cm_detalles tiene
   múltiples filas por factura. Se agrega subconsulta con GROUP BY para traer
   el código CIE-10 más frecuente por factura (modo estadístico).
4. Salida: Data/raw/YYYYMMDD_geo_afiliados_6m.parquet (sagrado — solo lectura)
"""

import logging
import os
from datetime import date
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path("d:/Users/jcardonr/Documents/Savia")
RAW_DIR  = BASE_DIR / "Data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")

TODAY            = date.today().strftime("%Y%m%d")
MESES_PERIODO    = 6
MIN_DIAS_MADUREZ = 30   # días mínimos desde radicación para auditoría completa

# ── Conexión MySQL ────────────────────────────────────────────────────────────
try:
    import mysql.connector
    conn = mysql.connector.connect(
        host     = os.environ["SAVIA_DB_HOST"],
        database = os.environ["SAVIA_DB_NAME"],
        user     = os.environ["SAVIA_DB_USER"],
        password = os.environ["SAVIA_DB_PASSWORD"],
        connect_timeout = 30,
        charset  = "utf8mb4",
    )
    logger.info("Conexión BD exitosa: %s / %s",
                os.environ["SAVIA_DB_HOST"], os.environ["SAVIA_DB_NAME"])
except Exception as e:
    logger.error("No se pudo conectar a la BD: %s", e)
    logger.error("Verifica que estés en la red interna de Savia (VPN o sede).")
    raise

# ── Query principal ───────────────────────────────────────────────────────────
# NOTAS:
# - codigo_dx: subconsulta dx_agg trae el CIE-10 más frecuente por factura
#   usando SUBSTRING_INDEX(GROUP_CONCAT(...ORDER BY cnt DESC), ',', 1)
# - FILTRO MADUREZ: fecha_radicacion <= DATE_SUB(NOW(), INTERVAL 30 DAY)
#   excluye facturas recientes sin auditoría completa (target=0 artificial)
# - 6 meses: DATE_SUB(NOW(), INTERVAL 6 MONTH)
# - Solo SELECT — nunca INSERT/UPDATE/DELETE (regla §7 CLAUDE.md)

QUERY_PRINCIPAL = f"""
SELECT
    f.id                                                AS factura_id,
    f.fecha_radicacion,
    f.nit                                               AS nit_prestador,

    aa.id                                               AS afiliado_id,
    aa.mae_zona_valor                                   AS zona_afiliado,
    aa.nivel_sisben,
    aa.mae_regimen_valor                                AS regimen,
    aa.mae_grupo_poblacional_valor                      AS grupo_poblacional,
    aa.mae_genero_valor                                 AS genero,
    TIMESTAMPDIFF(YEAR, aa.fecha_nacimiento, CURDATE()) AS edad,
    aa.discapacidad,

    COALESCE(aac.latitud_nuevo,  aac.latitud)           AS lat_afiliado_raw,
    COALESCE(aac.longitud_nuevo, aac.longitud)          AS lng_afiliado_raw,

    gn_res.nombre                                       AS municipio_residencia,
    gn_res.mae_region_valor                             AS region_residencia,
    gn_res.gps_latitud                                  AS lat_municipio_res,
    gn_res.gps_longitud                                 AS lng_municipio_res,
    gn_res.cobertura                                    AS municipio_con_cobertura,

    cps.id                                              AS sede_id,
    cps.nombre                                          AS nombre_sede,
    cps.nivel_atencion                                  AS nivel_atencion_ips,
    cps.mae_clase_prestador_valor                       AS clase_prestador,
    cps.capitacion,
    cps.direccion_georef_latitud                        AS lat_ips,
    cps.direccion_georef_longitud                       AS lng_ips,
    gn_ips.nombre                                       AS municipio_ips,
    gn_ips.mae_region_valor                             AS region_ips,

    -- codigo_dx: CIE-10 más frecuente por factura (corrige 100% nulos del query anterior)
    dx_agg.codigo_dx_principal                          AS codigo_dx,

    -- TARGET: 0=Auditada / 1=Glosada / 2=Devuelta
    CASE
        WHEN cad.cm_facturas_id IS NOT NULL THEN 2
        WHEN cag.cm_detalles_id IS NOT NULL THEN 1
        ELSE 0
    END                                                 AS target

FROM cm_facturas f

INNER JOIN cm_detalles cd     ON cd.cm_facturas_id = f.id
INNER JOIN aseg_afiliados aa  ON aa.id = cd.aseg_afiliados_id

LEFT JOIN aseg_afiliado_coordenadas aac
    ON aac.id_afiliado = aa.id

LEFT JOIN gn_ubicaciones gn_res
    ON gn_res.id = aa.residencia_ubicacion_id

LEFT JOIN cnt_prestador_sedes cps
    ON cps.id = aa.primaria_cnt_prestador_sedes_id

LEFT JOIN gn_ubicaciones gn_ips
    ON gn_ips.id = cps.ubicacion_id

-- codigo_dx: modo estadístico por factura (CIE-10 más frecuente)
LEFT JOIN (
    SELECT
        cm_facturas_id,
        SUBSTRING_INDEX(
            GROUP_CONCAT(codigo_dx ORDER BY codigo_dx_cnt DESC SEPARATOR ','),
            ',', 1
        ) AS codigo_dx_principal
    FROM (
        SELECT
            cm_facturas_id,
            codigo_dx,
            COUNT(*) AS codigo_dx_cnt
        FROM cm_detalles
        WHERE codigo_dx IS NOT NULL
          AND codigo_dx != ''
        GROUP BY cm_facturas_id, codigo_dx
    ) dx_counts
    GROUP BY cm_facturas_id
) dx_agg ON dx_agg.cm_facturas_id = f.id

-- TARGET glosa: primer detalle glosado de la factura
LEFT JOIN cm_auditoria_motivos_glosas cag
    ON cag.cm_detalles_id = cd.id

-- TARGET devolución: a nivel de factura
LEFT JOIN cm_auditoria_devoluciones cad
    ON cad.cm_facturas_id = f.id

WHERE
    -- 6 meses de datos
    f.fecha_radicacion >= DATE_SUB(NOW(), INTERVAL {MESES_PERIODO} MONTH)
    -- FILTRO MADUREZ: solo facturas con >= 30 días — auditoría completa
    AND f.fecha_radicacion <= DATE_SUB(NOW(), INTERVAL {MIN_DIAS_MADUREZ} DAY)

GROUP BY
    f.id, f.fecha_radicacion, f.nit,
    aa.id, aa.mae_zona_valor, aa.nivel_sisben, aa.mae_regimen_valor,
    aa.mae_grupo_poblacional_valor, aa.mae_genero_valor, aa.fecha_nacimiento,
    aa.discapacidad,
    aac.latitud_nuevo, aac.latitud, aac.longitud_nuevo, aac.longitud,
    gn_res.nombre, gn_res.mae_region_valor, gn_res.gps_latitud,
    gn_res.gps_longitud, gn_res.cobertura,
    cps.id, cps.nombre, cps.nivel_atencion, cps.mae_clase_prestador_valor,
    cps.capitacion, cps.direccion_georef_latitud, cps.direccion_georef_longitud,
    gn_ips.nombre, gn_ips.mae_region_valor,
    dx_agg.codigo_dx_principal,
    cad.cm_facturas_id, cag.cm_detalles_id

ORDER BY f.fecha_radicacion ASC
"""

# ── Query sedes IPS (sin cambios respecto a extracción original) ──────────────
QUERY_SEDES = """
SELECT
    cps.id,
    cps.cnt_prestadores_id,
    cps.ubicacion_id,
    cps.nombre,
    cps.nivel_atencion,
    cps.direccion_georef_latitud,
    cps.direccion_georef_longitud,
    cps.codigo_habilitacion,
    cps.mae_clase_prestador_valor,
    cps.estado_sede,
    cps.capitacion,
    cps.zona_precedencia,
    gn.nombre AS municipio,
    gn.mae_region_valor AS region
FROM cnt_prestador_sedes cps
LEFT JOIN gn_ubicaciones gn ON gn.id = cps.ubicacion_id
WHERE cps.estado_sede = 1
"""

# ── Ejecución ─────────────────────────────────────────────────────────────────
logger.info("Extrayendo dataset principal (%d meses, madurez >= %d días)...",
            MESES_PERIODO, MIN_DIAS_MADUREZ)
logger.info("Esto puede tomar 10-30 minutos dependiendo de la red y el servidor.")

try:
    # Leer en chunks para manejar memoria con 11M+ filas esperadas
    CHUNK_SIZE = 500_000
    chunks = []
    cursor = conn.cursor(dictionary=True)
    cursor.execute(QUERY_PRINCIPAL)

    total = 0
    while True:
        rows = cursor.fetchmany(CHUNK_SIZE)
        if not rows:
            break
        chunks.append(pd.DataFrame(rows))
        total += len(rows)
        logger.info("  Leídas %d filas...", total)

    cursor.close()
    df = pd.concat(chunks, ignore_index=True)
    logger.info("Dataset principal: %d filas · %d columnas", len(df), len(df.columns))

except Exception as e:
    logger.error("Error en query principal: %s", e)
    conn.close()
    raise

# ── Diagnóstico codigo_dx ─────────────────────────────────────────────────────
n_nulos = df["codigo_dx"].isna().sum()
pct_nulos = n_nulos / len(df) * 100
logger.info("codigo_dx nulos: %d / %d = %.1f%%", n_nulos, len(df), pct_nulos)
if pct_nulos < 100:
    capitulos = df["codigo_dx"].dropna().str[:1].str.upper().value_counts()
    logger.info("Top 5 capítulos CIE-10:\n%s", capitulos.head())

# ── Distribución de clases ────────────────────────────────────────────────────
vc = df["target"].value_counts().sort_index()
for cls, label in [(0, "Auditada"), (1, "Glosada"), (2, "Devuelta")]:
    n = vc.get(cls, 0)
    logger.info("Clase %d (%s): %d  (%.2f%%)", cls, label, n, n / len(df) * 100)

# ── Rango de fechas ───────────────────────────────────────────────────────────
df["fecha_radicacion"] = pd.to_datetime(df["fecha_radicacion"])
logger.info("Periodo: %s → %s",
            df["fecha_radicacion"].min().date(),
            df["fecha_radicacion"].max().date())

# ── Guardar parquet principal ─────────────────────────────────────────────────
out_path = RAW_DIR / f"{TODAY}_geo_afiliados_6m.parquet"
df.to_parquet(out_path, index=False, compression="snappy")
logger.info("Guardado: %s  (%.1f MB)", out_path, out_path.stat().st_size / 1e6)

# ── Extraer sedes IPS ─────────────────────────────────────────────────────────
logger.info("Extrayendo sedes IPS...")
try:
    df_sedes = pd.read_sql(QUERY_SEDES, conn)
    sedes_path = RAW_DIR / f"{TODAY}_cnt_prestador_sedes.parquet"
    df_sedes.to_parquet(sedes_path, index=False, compression="snappy")
    logger.info("Sedes guardadas: %d sedes · %s", len(df_sedes), sedes_path)
except Exception as e:
    logger.warning("No se pudo extraer sedes: %s — usando archivo existente.", e)

conn.close()
logger.info("Conexion cerrada. Extraccion completa.")
logger.info("")
logger.info("SIGUIENTE PASO: ejecutar run_modelo_v5.py con el nuevo parquet:")
logger.info("  python run_modelo_v5.py")
