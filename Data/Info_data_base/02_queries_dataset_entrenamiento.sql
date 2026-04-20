-- =============================================================================
-- QUERIES PARA CONSTRUCCIÓN DEL DATASET DE ENTRENAMIENTO
-- Proyecto: Analítica Predictiva para Auditoría Prestacional
-- Savia Salud EPS · Universidad EAFIT
-- Fecha: 2026-03-04
-- =============================================================================
-- IMPORTANTE: Estos queries son una PROPUESTA basada en la estructura de tablas.
-- Deben validarse contra los datos reales y ajustar los nombres de columnas
-- según el resultado de ejecutar queries_exploracion_cm.sql primero.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- PASO 1: Verificar universo de facturas disponibles con estado de auditoría
-- Ejecutar primero para entender la distribución de clases antes de construir
-- el dataset completo
-- -----------------------------------------------------------------------------

SELECT
    -- Determinar estado final de la factura (TARGET del modelo)
    CASE
        WHEN EXISTS (
            SELECT 1 FROM cm_auditoria_devoluciones cad
            INNER JOIN cm_detalles cd2 ON cad.cm_detalles_id = cd2.id
            WHERE cd2.cm_facturas_id = f.id
        ) THEN 2  -- Devuelta (error de forma)
        WHEN EXISTS (
            SELECT 1 FROM cm_auditoria_motivos_glosas camg
            INNER JOIN cm_detalles cd3 ON camg.cm_detalles_id = cd3.id
            WHERE cd3.cm_facturas_id = f.id
        ) THEN 1  -- Glosada (objeción clínica/tarifa)
        ELSE 0    -- Auditada (pago completo)
    END AS estado_label,
    COUNT(*) AS total_facturas,
    AVG(f.valor_factura) AS valor_promedio,
    SUM(f.valor_factura) AS valor_total
FROM cm_facturas f
WHERE f.fecha_radicacion >= DATE_SUB(NOW(), INTERVAL 24 MONTH)
GROUP BY estado_label
ORDER BY estado_label;

-- -----------------------------------------------------------------------------
-- PASO 2: Verificar distribución por año-mes (para división temporal del train/test)
-- -----------------------------------------------------------------------------

SELECT
    DATE_FORMAT(f.fecha_radicacion, '%Y-%m') AS periodo,
    COUNT(*) AS total,
    SUM(CASE WHEN camg_count.tiene_glosa = 1 THEN 1 ELSE 0 END) AS glosadas,
    SUM(CASE WHEN cad_count.tiene_devolucion = 1 THEN 1 ELSE 0 END) AS devueltas,
    SUM(CASE WHEN camg_count.tiene_glosa = 0 AND cad_count.tiene_devolucion = 0 THEN 1 ELSE 0 END) AS auditadas
FROM cm_facturas f
LEFT JOIN (
    SELECT cd.cm_facturas_id, 1 AS tiene_glosa
    FROM cm_detalles cd
    INNER JOIN cm_auditoria_motivos_glosas camg ON camg.cm_detalles_id = cd.id
    GROUP BY cd.cm_facturas_id
) camg_count ON camg_count.cm_facturas_id = f.id
LEFT JOIN (
    SELECT cd.cm_facturas_id, 1 AS tiene_devolucion
    FROM cm_detalles cd
    INNER JOIN cm_auditoria_devoluciones cad ON cad.cm_detalles_id = cd.id
    GROUP BY cd.cm_facturas_id
) cad_count ON cad_count.cm_facturas_id = f.id
WHERE f.fecha_radicacion >= DATE_SUB(NOW(), INTERVAL 24 MONTH)
GROUP BY periodo
ORDER BY periodo;

-- -----------------------------------------------------------------------------
-- PASO 3: DATASET PRINCIPAL — Una fila por factura con todas las features
-- Usar para entrenamiento del modelo multiclase
-- -----------------------------------------------------------------------------

SELECT

    -- === IDENTIFICADORES (NO usar como features) ===
    f.id                                AS factura_id,
    f.numero_radicado                   AS numero_factura,
    p.nit                               AS nit_prestador,
    f.fecha_radicacion                  AS fecha_radicacion,

    -- === TARGET: Estado final de la factura ===
    CASE
        WHEN cad_agg.tiene_devolucion = 1 THEN 2
        WHEN camg_agg.tiene_glosa = 1     THEN 1
        ELSE 0
    END AS estado_label,  -- 0=Auditada, 1=Glosada, 2=Devuelta

    -- === FEATURES FINANCIERAS ===
    f.valor_factura                     AS valor_total_factura,
    COALESCE(d_agg.num_items, 0)        AS num_items_factura,
    COALESCE(d_agg.valor_max_item, 0)   AS valor_max_item,
    CASE
        WHEN f.valor_factura > 0
        THEN COALESCE(d_agg.valor_max_item, 0) / f.valor_factura
        ELSE 0
    END                                 AS porcentaje_mayor_item,
    -- Discrepancia fiscal JSON vs XML (VAL-001)
    ABS(COALESCE(rips.factura_valor, 0) - f.valor_factura)
                                        AS discrepancia_fiscal_abs,

    -- === FEATURES ADMINISTRATIVAS / TEMPORALES ===
    DATEDIFF(f.fecha_radicacion, f.fecha_factura)
                                        AS dias_hasta_radicacion,
    QUARTER(f.fecha_radicacion)         AS trimestre_facturacion,
    DAYOFWEEK(f.fecha_radicacion)       AS dia_semana_radicacion,
    MONTH(f.fecha_radicacion)           AS mes_radicacion,

    -- === FEATURES DEL CONTRATO ===
    COALESCE(c.tipo_contrato, 'desconocido')
                                        AS tipo_contrato,
    COALESCE(c.modalidad, 0)            AS modalidad_pago_encoded,
    COALESCE(c.regimen, 'desconocido')  AS regimen,

    -- === FEATURES DEL PRESTADOR ===
    COALESCE(ps.nivel_atencion, 0)      AS nivel_habilitacion_ips,

    -- Historial prestador: tasa de glosa (últimos 12 meses)
    COALESCE(hist.tasa_glosa_12m, 0)    AS tasa_glosa_historica_nit,
    COALESCE(hist.tasa_dev_12m, 0)      AS tasa_devolucion_historica_nit,
    COALESCE(hist.valor_prom_12m, 0)    AS valor_promedio_factura_nit,
    COALESCE(hist.dias_prom_rad_12m, 0) AS dias_promedio_radicacion_nit,

    -- === FEATURES CLÍNICAS (desde cm_detalles) ===
    COALESCE(d_agg.num_diagnosticos, 0) AS num_dx_secundarios,
    -- Inconsistencia diagnóstico-sexo (VAL-004)
    COALESCE(dx_sexo.inconsistente, 0)  AS dx_sexo_inconsistente,

    -- === FEATURES DE VALIDACIÓN ELECTRÓNICA (FEV) ===
    COALESCE(rips.de1601_eps_erronea, 0)      AS fev_eps_erronea,
    COALESCE(rips.de4401_profesional_red, 0)  AS fev_profesional_no_red,
    COALESCE(rips.de5001_pagada, 0)           AS fev_ya_pagada,

    -- === CAUSAL DE GLOSA (si existe — para análisis post-predicción) ===
    camg_agg.motivo_principal_id        AS motivo_glosa_principal,
    camg_agg.valor_total_glosado        AS valor_total_glosado,
    cad_agg.motivo_devolucion_id        AS motivo_devolucion

FROM cm_facturas f

-- Prestador
LEFT JOIN cnt_prestadores p
    ON p.id = f.cnt_prestadores_id

-- Sede del prestador (nivel de habilitación)
LEFT JOIN cnt_prestador_sedes ps
    ON ps.cnt_prestadores_id = p.id
    AND ps.principal = 1  -- AJUSTAR: verificar nombre exacto del campo

-- Contrato vigente
LEFT JOIN cnt_contratos c
    ON c.cnt_prestadores_id = p.id
    AND f.fecha_radicacion BETWEEN c.fecha_inicio AND COALESCE(c.fecha_fin, '9999-12-31')

-- RIPS electrónico asociado
LEFT JOIN cm_fe_rips_cargas rips
    ON rips.id = f.cm_fe_rips_cargas_id  -- AJUSTAR: verificar nombre de FK

-- Agregación de detalles de la factura
LEFT JOIN (
    SELECT
        cm_facturas_id,
        COUNT(*)                        AS num_items,
        MAX(valor_facturado)            AS valor_max_item,
        COUNT(DISTINCT codigo_dx)       AS num_diagnosticos
    FROM cm_detalles
    GROUP BY cm_facturas_id
) d_agg ON d_agg.cm_facturas_id = f.id

-- Indicador de glosa (TARGET componente 1)
LEFT JOIN (
    SELECT
        cd.cm_facturas_id,
        1                               AS tiene_glosa,
        MIN(camg.mae_motivo_id)         AS motivo_principal_id,
        SUM(camg.valor_motivo)          AS valor_total_glosado
    FROM cm_detalles cd
    INNER JOIN cm_auditoria_motivos_glosas camg ON camg.cm_detalles_id = cd.id
    GROUP BY cd.cm_facturas_id
) camg_agg ON camg_agg.cm_facturas_id = f.id

-- Indicador de devolución (TARGET componente 2)
LEFT JOIN (
    SELECT
        cd.cm_facturas_id,
        1                               AS tiene_devolucion,
        MIN(cad.mae_devolucion_id)      AS motivo_devolucion_id  -- AJUSTAR columna
    FROM cm_detalles cd
    INNER JOIN cm_auditoria_devoluciones cad ON cad.cm_detalles_id = cd.id
    GROUP BY cd.cm_facturas_id
) cad_agg ON cad_agg.cm_facturas_id = f.id

-- Inconsistencia diagnóstico-sexo (VAL-004)
LEFT JOIN (
    SELECT
        cd.cm_facturas_id,
        MAX(CASE
            WHEN (aa.genero = 'M' AND cd.codigo_dx IN (
                'Z34','Z35','Z36','Z37','O00','O01','O02','O10','O11','O12',
                'O20','O21','O30','O40','N70','N71','N72','N73','N80','N81',
                'N83','N92','N94','N95'
            )) THEN 1
            WHEN (aa.genero = 'F' AND cd.codigo_dx IN (
                'Z88.9','N40','N41','N42','N43','N44','N45','N46','N47','N48','N49'
            )) THEN 1
            ELSE 0
        END) AS inconsistente
    FROM cm_detalles cd
    INNER JOIN aseg_afiliados aa ON aa.id = cd.aseg_afiliados_id
    GROUP BY cd.cm_facturas_id
) dx_sexo ON dx_sexo.cm_facturas_id = f.id

-- Historial del prestador (últimos 12 meses, excluyendo la factura actual)
LEFT JOIN (
    SELECT
        f_hist.cnt_prestadores_id,
        AVG(CASE WHEN camg_h.tiene_glosa = 1 THEN 1.0 ELSE 0.0 END)
                                        AS tasa_glosa_12m,
        AVG(CASE WHEN cad_h.tiene_devolucion = 1 THEN 1.0 ELSE 0.0 END)
                                        AS tasa_dev_12m,
        AVG(f_hist.valor_factura)       AS valor_prom_12m,
        AVG(DATEDIFF(f_hist.fecha_radicacion, f_hist.fecha_factura))
                                        AS dias_prom_rad_12m
    FROM cm_facturas f_hist
    LEFT JOIN (
        SELECT cd_h.cm_facturas_id, 1 AS tiene_glosa
        FROM cm_detalles cd_h
        INNER JOIN cm_auditoria_motivos_glosas camg_h2 ON camg_h2.cm_detalles_id = cd_h.id
        GROUP BY cd_h.cm_facturas_id
    ) camg_h ON camg_h.cm_facturas_id = f_hist.id
    LEFT JOIN (
        SELECT cd_h.cm_facturas_id, 1 AS tiene_devolucion
        FROM cm_detalles cd_h
        INNER JOIN cm_auditoria_devoluciones cad_h2 ON cad_h2.cm_detalles_id = cd_h.id
        GROUP BY cd_h.cm_facturas_id
    ) cad_h ON cad_h.cm_facturas_id = f_hist.id
    WHERE f_hist.fecha_radicacion >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
    GROUP BY f_hist.cnt_prestadores_id
) hist ON hist.cnt_prestadores_id = f.cnt_prestadores_id

WHERE
    f.fecha_radicacion >= DATE_SUB(NOW(), INTERVAL 24 MONTH)
    AND f.valor_factura > 0  -- Excluir facturas sin valor

ORDER BY f.fecha_radicacion ASC;

-- =============================================================================
-- NOTAS DE IMPLEMENTACIÓN
-- =============================================================================
-- 1. Ejecutar PRIMERO las queries de exploración (queries_exploracion_cm.sql)
--    para verificar los nombres exactos de columnas antes de usar este script.
--
-- 2. Columnas a VALIDAR (pueden tener nombres distintos en la BD real):
--    - cm_facturas.cm_fe_rips_cargas_id  (FK hacia RIPS electrónico)
--    - cm_facturas.fecha_factura          (puede llamarse fecha_emision)
--    - cnt_prestador_sedes.nivel_atencion (puede llamarse nivel_complejidad)
--    - cnt_prestador_sedes.principal      (campo para sede principal)
--    - cm_auditoria_devoluciones.mae_devolucion_id (FK a maestro devoluciones)
--    - aseg_afiliados.genero              (puede ser 'M'/'F' o 1/0)
--
-- 3. Si cm_auditoria_devoluciones no existe con ese nombre exacto, buscar:
--    SELECT * FROM information_schema.tables
--    WHERE table_name LIKE '%devolu%' AND table_schema = 'system_savia';
--
-- 4. Ajustar filtro de fecha según disponibilidad real de datos.
--    El periodo de 24 meses busca ~10,000+ registros etiquetados.
-- =============================================================================
