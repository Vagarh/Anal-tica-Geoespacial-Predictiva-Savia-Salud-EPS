# CLAUDE.MD — Proyecto: Analítica Geoespacial Predictiva · Savia Salud EPS
## Savia Salud EPS · Proyecto Interno · Ciencia de Datos

> **Propósito:** Índice maestro, reglas activas y estado del proyecto. Leer siempre al inicio de sesión.

---

## 0. ESTADO ACTUAL DEL PROYECTO *(Actualizado: 2026-05-06)*

### Descripción

Proyecto interno de Savia Salud EPS. Punto de partida: análisis descriptivo en Power BI. Objetivo: modelo predictivo geoespacial + dashboard Next.js publicado en Vercel.

### Avance por Fase

| Fase | Nombre | Estado | Avance |
|---|---|---|---|
| **0** | EDA Geoespacial | ✅ Completada | 100% |
| **1** | Ingeniería de Features Geoespaciales | ✅ Completada | 100% |
| **2** | Modelo Predictivo Geoespacial (XGBoost) | ✅ Completada | 100% |
| **3** | API Backend FastAPI | ⏳ Pendiente | 0% |
| **4** | Dashboard Next.js + Vercel | 🔄 En progreso | 40% |

### Estado Fase 2 — Evolución del Modelo XGBoost

| Versión | Fecha | AUC-ROC | Recall Glosada | Precision Glosada | F1-macro | Artefacto |
|---|---|---|---|---|---|---|
| v1 | 2026-04-20 | 0.621 | 0.000 | — | 0.323 | `20260420_geo_xgboost_v1.json` |
| v2 | 2026-05-05 | 0.568 | 0.999 | 5.6% | 0.035 | `20260505_geo_xgboost_v2.json` |
| v3 | 2026-05-05 | 0.546 | 0.974 | 5.7% | 0.073 | `20260505_geo_xgboost_v3.json` |
| v4 | 2026-05-05 | 0.604 | 0.995 | 12.8% | 0.082 | `20260505_geo_xgboost_v4.json` |
| **v5** | **2026-05-06** | **0.674** | **1.000** | **33.9%** | **0.169** | `20260506_geo_xgboost_v5.json` |

**v5 es el modelo en producción actual.**

#### Historia de mejoras
- **v1→v2:** `scale_pos_weight` ignorado en multiclase → corregido con `sample_weight` explícito + umbral F-beta=2
- **v2→v3:** Añadidas features temporales (`dia_semana`, `semana_anio`) y `glosa_rate_region`
- **v3→v4:** `dias_desde_inicio` dominaba SHAP (42%) — sesgo de rezago de auditoría. Filtro madurez ≥30 días elimina 2.76M facturas no auditadas. Features temporales contaminadas eliminadas. SHAP limpio: edad(19.7%), glosa_rate_municipio(16.1%)
- **v4→v5:** Dataset ampliado a 6 meses (6.28M facturas maduras). Precision Glosada sube 12.8%→33.9% (+21pp). AUC sube 0.604→0.674

#### Hallazgos importantes de datos
- **`codigo_dx` en `cm_detalles`:** La columna existe pero está prácticamente vacía en la BD (solo 1 registro con valor). No es un bug de SQL — el sistema no está cargando diagnósticos CIE-10 en esta tabla. Feature descartada hasta que se resuelva en origen.
- **Coordenadas GPS:** Solo 1.9% de afiliados tiene GPS propio; 98.1% usa centroide del municipio como fallback.
- **127 municipios** activos con datos en el período analizado.
- **SHAP v5:** `mes_radicacion` domina (pendiente investigar si es estacionalidad real o sesgo residual del split temporal), seguido de `glosa_rate_municipio` y `glosa_rate_region`.

### Estado Fase 4 — Dashboard Next.js

- **Tecnología:** Next.js 14 (App Router) + TypeScript + Tailwind CSS + Recharts
- **Ubicación:** `dashboard-next/`
- **Node.js:** Instalado en `C:\Users\jcardonr\node-v20.19.0-win-x64\` (NO está en PATH por defecto — agregar manualmente)
- **Páginas implementadas:** `/` (resumen ejecutivo), `/features` (SHAP), `/modelo` (evolución v1→v5)
- **Datos:** Estáticos en `dashboard-next/src/lib/modelData.ts` — en Fase 3 vendrán del API FastAPI
- **Para levantar localmente:**
  ```powershell
  $env:PATH = "C:\Users\jcardonr\node-v20.19.0-win-x64;$env:PATH"
  cd dashboard-next
  npm run dev
  ```

### Próximos Pasos Inmediatos

1. **Investigar `mes_radicacion` en SHAP v5** — graficar glosa_rate por mes para confirmar si es estacionalidad real
2. **Fase 3:** Construir `src/api/geo_endpoints.py` con FastAPI
3. **Fase 4:** Completar páginas del dashboard (mapa de riesgo, predicción, prestadores) y publicar en Vercel

---

## 1. CONTEXTO Y VALOR ESTRATÉGICO

### Problema
La EPS tiene información de ubicación de afiliados e IPS pero solo la usa descriptivamente (Power BI). No existe un modelo que relacione la dimensión geoespacial con el riesgo en salud, patrones de glosa o acceso a la red prestadora.

### Objetivo
Construir un sistema analítico geoespacial que demuestre valor en 4 frentes:

**1. Gestión del Riesgo en Salud**
- Riesgo por territorio: municipios con alta concentración de glosas → zonas con sobreuso o fraude
- Brecha de acceso: afiliados lejos de su IPS → mayor probabilidad de urgencias no planificadas (mayor costo)
- Grupos de riesgo geográfico: SISBEN + municipio + grupo etario → perfiles de alto costo para intervención preventiva
- UPC diferencial: evidenciar si la UPC actual cubre el riesgo real por municipio

**2. Gestión de Red Prestadores**
- Zonas sin cobertura: municipios con afiliados pero sin IPS de nivel 1 cercana
- Concentración vs dispersión: red concentrada en zonas urbanas, municipios rurales sin cobertura
- Eficiencia por nivel de atención: afiliados alejados que consultan directamente nivel 3 (más caro)

**3. Auditoría Prestacional Geoespacial**
- Glosas por zona: municipios con tasas anómalas → posible fraude o error sistemático de prestador regional
- Rutas de concentración de enfermedad: CIE-10 por municipio → focos epidemiológicos

**4. Oportunidades de Rentabilidad**
- Capitación diferenciada por zona: municipios de alto riesgo → negociar capitación más alta con IPS
- Intervención preventiva focalizada: programas de gestión de enfermedad crónica localizados
- Renegociación de contratos: IPS en municipios con tasas de glosa altas

---

## 2. FUENTE DE DATOS — BD system_savia (10.250.5.36)

### Tablas Geoespaciales Principales

**`aseg_afiliado_coordenadas`** — Coordenadas GPS de afiliados
| Columna | Tipo | Notas |
|---|---|---|
| id | int PK | |
| id_afiliado | int FK | → aseg_afiliados.id |
| latitud | varchar(500) | Coordenada actual |
| longitud | varchar(500) | |
| consumido | tinyint | Flag procesamiento |
| latitud_nuevo | varchar(500) | Coordenada actualizada (preferida) |
| longitud_nuevo | varchar(500) | |

**`gn_ubicaciones`** — Tabla maestra geográfica (municipios/regiones)
| Columna | Tipo | Notas |
|---|---|---|
| id | int PK | |
| gn_ubicaciones_id | int | Self-join jerarquía municipio→departamento |
| nombre | varchar(32) | Nombre municipio/departamento |
| tipo | int | Nivel geográfico |
| gps_latitud | decimal(12,9) | Centroide municipio |
| gps_longitud | decimal(12,9) | |
| gps_georreferenciada | bit | Flag cobertura GPS |
| mae_region_valor | varchar(128) | Región/departamento |
| cobertura | bit | Si Savia tiene cobertura en ese municipio |

**`cnt_prestador_sedes`** — Sedes de IPS con geolocalización
| Columna | Tipo | Notas |
|---|---|---|
| id | int PK | |
| cnt_prestadores_id | int FK | → cnt_prestadores |
| ubicacion_id | int FK | → gn_ubicaciones.id |
| nombre | varchar(256) | Nombre de la sede |
| nivel_atencion | int | 1, 2 o 3 |
| direccion_georef_latitud | decimal(12,9) | GPS sede |
| direccion_georef_longitud | decimal(12,9) | |
| codigo_habilitacion | varchar(16) | Código MINSALUD |
| mae_clase_prestador_valor | varchar(128) | Tipo prestador |
| estado_sede | bit | Activa/inactiva |
| capitacion | bit | Modalidad capitación |
| zona_precedencia | varchar(1) | Zona |

### Tablas de Enriquecimiento
| Tabla | FK | Uso |
|---|---|---|
| `aseg_afiliados` | id_afiliado | SISBEN, régimen, zona, grupo poblacional, discapacidad, etnia, edad |
| `cm_facturas` | vía cm_detalles | Facturación, fecha_radicacion |
| `cm_detalles` | aseg_afiliados_id | CIE-10, CUPS |
| `cm_auditoria_motivos_glosas` | cm_detalles_id | TARGET clase Glosada |
| `cm_auditoria_devoluciones` | cm_facturas_id | TARGET clase Devuelta |
| `cnt_prestadores` | cnt_prestadores_id | Razón social, nivel atención IPS |

### Diagrama de Relaciones Geoespaciales
```
[aseg_afiliado_coordenadas] ─── lat/lng GPS afiliado
         │ id_afiliado
         ▼
[aseg_afiliados] ──── zona, SISBEN, régimen, grupo etario, discapacidad, etnia
         │
         ├── residencia_ubicacion_id ──► [gn_ubicaciones] ── municipio, región, centroide GPS, cobertura
         │
         └── primaria_cnt_prestador_sedes_id ──► [cnt_prestador_sedes] ── nombre sede, nivel, lat/lng
                                                          │ ubicacion_id
                                                          └──► [gn_ubicaciones] ── municipio IPS
         │
[cm_detalles] ── CIE-10 ──► [cm_facturas] ──► TARGET (0=Auditada / 1=Glosada / 2=Devuelta)
```

### Query Base de Extracción (últimos 3 meses — SELECT ONLY)
```sql
SELECT
    f.id                            AS factura_id,
    f.fecha_radicacion,
    f.nit                           AS nit_prestador,
    aa.id                           AS afiliado_id,
    aa.mae_zona_valor               AS zona_afiliado,
    aa.nivel_sisben,
    aa.mae_regimen_valor            AS regimen,
    aa.mae_grupo_poblacional_valor  AS grupo_poblacional,
    aa.mae_genero_valor             AS genero,
    TIMESTAMPDIFF(YEAR, aa.fecha_nacimiento, CURDATE()) AS edad,
    COALESCE(aac.latitud_nuevo, aac.latitud)   AS lat_afiliado,
    COALESCE(aac.longitud_nuevo, aac.longitud) AS lng_afiliado,
    gn_res.nombre                   AS municipio_residencia,
    gn_res.mae_region_valor         AS region_residencia,
    gn_res.gps_latitud              AS lat_municipio_residencia,
    gn_res.gps_longitud             AS lng_municipio_residencia,
    cps.id                          AS sede_id,
    cps.nombre                      AS nombre_sede,
    cps.nivel_atencion              AS nivel_atencion_ips,
    cps.mae_clase_prestador_valor   AS clase_prestador,
    cps.direccion_georef_latitud    AS lat_ips,
    cps.direccion_georef_longitud   AS lng_ips,
    gn_ips.nombre                   AS municipio_ips,
    cd.codigo_dx,
    CASE
        WHEN cad.cm_facturas_id IS NOT NULL THEN 2
        WHEN cag.cm_detalles_id IS NOT NULL THEN 1
        ELSE 0
    END AS target
FROM cm_facturas f
INNER JOIN cm_detalles cd     ON cd.cm_facturas_id = f.id
INNER JOIN aseg_afiliados aa  ON aa.id = cd.aseg_afiliados_id
LEFT JOIN aseg_afiliado_coordenadas aac ON aac.id_afiliado = aa.id
LEFT JOIN gn_ubicaciones gn_res ON gn_res.id = aa.residencia_ubicacion_id
LEFT JOIN cnt_prestador_sedes cps ON cps.id = aa.primaria_cnt_prestador_sedes_id
LEFT JOIN gn_ubicaciones gn_ips ON gn_ips.id = cps.ubicacion_id
LEFT JOIN cm_auditoria_motivos_glosas cag ON cag.cm_detalles_id = cd.id
LEFT JOIN cm_auditoria_devoluciones cad ON cad.cm_facturas_id = f.id
WHERE f.fecha_radicacion >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
```

---

## 3. ESTRUCTURA DEL REPOSITORIO

```
d:\Users\jcardonr\Documents\Savia\
├── .claude/
│   └── CLAUDE.md                        ← Este archivo (índice maestro)
├── Data/
│   ├── raw/                             ← SAGRADO — solo SELECT guardados como parquet
│   │   ├── YYYYMMDD_geo_afiliados_3m.parquet
│   │   ├── YYYYMMDD_gn_ubicaciones.parquet
│   │   └── YYYYMMDD_cnt_prestador_sedes.parquet
│   ├── processed/
│   │   └── YYYYMMDD_geo_features.parquet  ← Dataset analítico final
│   ├── database_analysis/               ← Muestras y análisis previos (no modificar)
│   └── Info_data_base/                  ← Documentación BD (no modificar)
│       ├── 01_mapa_bd_facturas.md       ← Mapa completo BD (554 tablas)
│       ├── 02_queries_dataset_entrenamiento.sql
│       ├── Estructura_columnas_llaves.csv
│       ├── ver_relaciones.csv
│       └── queries_exploracion_cm.sql
├── notebooks/
│   ├── 00_eda_geoespacial.ipynb         ← Fase 0: EDA y calidad de datos
│   └── 01_geo_features_modelo.ipynb     ← Fase 1: Features y modelo
├── src/
│   ├── data/
│   │   ├── extractors.py                ← Queries SELECT geoespaciales
│   │   └── geo_features.py             ← Haversine, densidad, rates
│   ├── models/
│   │   └── geo_model.py                ← XGBoost geoespacial
│   └── api/
│       └── geo_endpoints.py            ← FastAPI endpoints geo
├── dashboard/                           ← Next.js app (Fase 4)
│   ├── app/
│   │   ├── page.tsx                     ← Home: KPIs
│   │   ├── mapa-riesgo/page.tsx         ← Choropleth glosas por municipio
│   │   ├── concentracion/page.tsx       ← Concentración CIE-10 por zona
│   │   ├── prestadores/page.tsx         ← Mapa de IPS
│   │   └── prediccion/page.tsx          ← Formulario predicción
│   └── components/
│       ├── MapaRiesgo.tsx
│       ├── MapaPrestadores.tsx
│       └── GraficaConcentracion.tsx
├── models/
│   └── artifacts/                       ← YYYYMMDD_geo_xgboost_v1.json
├── reports/
│   └── figures/                         ← Mapas, SHAP, gráficas exportadas
└── tests/
    └── test_geo_features.py             ← Cobertura ≥80%
```

---

## 4. FEATURES GEOESPACIALES A CONSTRUIR (Fase 1)

| Feature | Origen | Descripción | Anti-leakage |
|---|---|---|---|
| `distancia_afiliado_ips_km` | Haversine(lat_afiliado, lat_ips) | Distancia GPS afiliado → IPS asignada | No aplica (geométrico) |
| `misma_municipio_afiliado_ips` | flag | Afiliado vive en municipio de su IPS | No aplica |
| `densidad_ips_municipio` | COUNT sedes por municipio | Oferta de IPS en municipio de residencia | Calcular sobre catálogo (no facturas) |
| `glosa_rate_municipio` | tasa histórica | Tasa de glosas del municipio | Calcular SOLO en train, aplicar en val/test |
| `concentracion_dx_municipio` | Índice Shannon | Diversidad diagnóstica por zona | Calcular SOLO en train |
| `municipio_sin_cobertura` | gn_ubicaciones.cobertura | Flag municipio fuera de cobertura Savia | Dato maestro, no leakage |
| `nivel_atencion_ips` | cnt_prestador_sedes | Nivel 1/2/3 del prestador asignado | Dato maestro |

---

## 5. MODELO PREDICTIVO (Fase 2)

**Variable objetivo (3 clases — NUNCA simplificar a binaria sin aprobación):**
- Clase 0 — Auditada: factura sin observaciones
- Clase 1 — Glosada: inconsistencia detectada (métrica primaria: Recall Glosada)
- Clase 2 — Devuelta: error de forma/administrativo

**Algoritmo:** XGBoost 2.0+, RANDOM_STATE = 42

**Métricas obligatorias:** Recall Glosada (primaria), F1-macro, AUC-ROC OvR, Matriz de Confusión

**Baseline esperado (datos 3 meses):** AUC-ROC ≥ 0.75

**División temporal:** Por `fecha_radicacion` — NUNCA split aleatorio

---

## 6. ARQUITECTURA DE ENTREGA (Fases 3-4)

**Backend:** FastAPI
```
GET  /v1/geo/municipios    → {municipio, tasa_glosa, densidad_ips, lat, lng}[]
GET  /v1/geo/ips           → {sede_id, nombre, municipio, nivel_atencion, lat, lng}[]
POST /v1/predict/geo       → predicción enriquecida con contexto geoespacial
GET  /v1/health
```

**Frontend:** Next.js 14+ (App Router) + TypeScript + Tailwind CSS + react-leaflet/deck.gl + Vercel

---

## 7. REGLAS CRÍTICAS (SIEMPRE ACTIVAS)

> **⚠️ OBLIGATORIAS EN TODA SESIÓN — NO NEGOCIABLES**

### Seguridad de Datos
1. **BD solo lectura:** NUNCA generar código con `INSERT`, `UPDATE`, `DELETE`, `DROP`, `TRUNCATE`, `ALTER`, `CREATE TABLE`
2. **`Data/raw/` es sagrado:** NUNCA modificar, sobreescribir o eliminar archivos en `Data/raw/`
3. **PII prohibida:** NUNCA extraer `nombre_completo_afiliado`, `numero_documento`, `email`, `telefono_movil` ni ningún dato identificable de pacientes
4. **Datos de prueba:** Solo usar últimos 3 meses (`fecha_radicacion >= DATE_SUB(NOW(), INTERVAL 3 MONTH)`)
5. **Sin fuentes externas:** Solo BD `system_savia` — no APIs externas, no datasets públicos

### Privacidad (Ley 1581 Colombia)
- Coordenadas de afiliados: agregar siempre a nivel municipio en dashboard (nunca puntos individuales)
- El modelo predice sobre perfiles (municipio + zona + SISBEN + grupo etario), no sobre individuos
- Identificador permitido: `aseg_afiliados.id` (interno, anonimizado)

### Calidad de Código
1. **Type hints obligatorios:** Toda función con type hints completos (parámetros + retorno)
2. **Docstrings Google Style:** Obligatorio en toda función pública
3. **No `print()` en `src/`:** Usar `logging.getLogger(__name__)`
4. **Tests obligatorios:** Cobertura mínima 80% para módulos en `src/`
5. **Reproducibilidad:** `RANDOM_STATE = 42` en todos los modelos
6. **Idioma:** Inglés para nombres de variables/funciones; español para docstrings, comentarios y logs
7. **Versionado de datos:** Prefijo `YYYYMMDD_` en archivos de `Data/processed/`

### Modelado
1. **Tarea multiclase:** NUNCA simplificar a binaria sin aprobación explícita
2. **Métrica primaria:** Recall de clase Glosada (clase=1)
3. **Métricas obligatorias:** F1-macro, AUC-ROC (OvR), Recall por clase, Matriz de Confusión
4. **División temporal:** NUNCA usar split aleatorio — siempre por `fecha_radicacion`
5. **Anti-leakage:** `glosa_rate_municipio` y `concentracion_dx_municipio` calculados SOLO en train, aplicados en val/test

---

## 8. GUÍA RÁPIDA DE SESIÓN

### Al iniciar cualquier sesión:
1. Leer este archivo completo
2. Revisar §0 (estado de fases) para saber en qué punto está el proyecto
3. Para trabajo con BD: revisar §2 (tablas y query base)
4. Para código: respetar §7 (reglas críticas)

### Flujo de datos obligatorio:
```
BD MySQL (SELECT) → Data/raw/ (parquet) → Data/processed/ (features) → src/ (código)
```
Nunca en sentido inverso. Nunca escribir de vuelta a la BD.

### Para actualizar documentación:
- **Estado del proyecto:** Actualizar tabla en §0
- **Nuevos hallazgos de BD:** Agregar en §2
- **Cambios de estructura:** Actualizar §3

---

## 9. VERIFICACIÓN END-TO-END

| Checkpoint | Comando / Criterio | Estado |
|---|---|---|
| EDA | `notebooks/00_eda_geoespacial.ipynb` ejecuta sin errores | ⏳ |
| Features | `pytest tests/test_geo_features.py` → cobertura ≥80% | ⏳ |
| Modelo | AUC-ROC ≥ 0.75 sobre datos 3 meses | ⏳ |
| API | `GET /v1/geo/municipios` retorna JSON válido | ⏳ |
| Dashboard | `npm run build` sin errores + `vercel deploy` exitoso | ⏳ |

---

*Última actualización: 2026-04-20 · Autor: jcardonr · Proyecto: Savia Salud EPS — Analítica Geoespacial*
