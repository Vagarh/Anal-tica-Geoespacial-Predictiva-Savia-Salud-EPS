# Mapa de Base de Datos — Cuentas Médicas Savia Salud EPS

**Generado:** 2026-03-04 | **Fuente:** Metadata BD MySQL `system_savia`
**Tablas totales:** 554 | **Relaciones FK:** 854

---

## 1. Flujo Completo de una Factura Médica

```
IPS (prestador de servicios)
    │
    ▼
[cm_fe_rips_cargas]         ←── Radicación electrónica (FEV + RIPS)
    │  cufe, cuv, factura_numero, factura_valor
    │  Validaciones DIAN: de1601, de4401, de5001...
    │
    ├──[cm_fe_rips_carga_contenidos]  ←── Almacenamiento JSON/XML
    │       tipo='json' → RIPS Res.2275  |  tipo='xml' → FEV DIAN
    │
    ▼
[cm_facturas]               ←── Cabecera en el sistema
    │  numero_radicado, valor_factura, estado_factura
    │  fecha_radicacion, cnt_prestadores_id, gn_empresas_id
    │
    ▼
[cm_detalles]               ←── Líneas de servicio (CUPS / CIE-10)
    │  ma_servicio_id, valor_facturado, valor_pagado, valor_glosa
    │  codigo_dx, aseg_afiliados_id
    │  aplica_glosa (flag), aplica_autorizacion
    │
    ├── SI hay glosa:
    │   [cm_auditoria_motivos_glosas]  ←── POR QUÉ se objetó
    │       mae_motivo_id, mae_motivo_especifico_id
    │       valor_motivo, tipologia
    │
    └── SI hay devolución:
        [cm_auditoria_devoluciones]   ←── Error de forma
            mae_devolucion_id, observacion

ESTADO FINAL (TARGET del modelo predictivo):
    0 = Auditada  → cm_detalles sin cm_auditoria_motivos_glosas
    1 = Glosada   → cm_auditoria_motivos_glosas tiene registros
    2 = Devuelta  → cm_auditoria_devoluciones tiene registros
```

---

## 2. Módulos del Sistema (por prefijo de tabla)

| Prefijo | Módulo | # Tablas |
|---|---|---|
| `cm_*` | Cuentas Médicas (facturas, glosas, auditoría) | 79 |
| `au_*` | Autorizaciones de Servicios | 70 |
| `cntj_*` | Otros | 41 |
| `gn_*` | Generales (usuarios, empresas, ubicaciones) | 37 |
| `mp_*` | Otros | 34 |
| `ma_*` | Catálogos Clínicos (CUPS, CIE-10, Medicamentos) | 29 |
| `pe_*` | Programas de Salud | 27 |
| `aseg_*` | Asegurados / Afiliados | 23 |
| `auc_*` | Auditoría Clínica | 23 |
| `cnt_*` | Contratos y Prestadores | 22 |
| `tu_*` | Otros | 20 |
| `gat_*` | Otros | 15 |
| `aus_*` | Auditoría de Solicitudes | 14 |
| `rco_*` | Otros | 11 |
| `gj_*` | Otros | 10 |
| `ref_*` | Remisiones | 10 |
| `ws_*` | Otros | 10 |
| `gs_*` | Otros | 9 |
| `inf_*` | Otros | 9 |
| `v_*` | Otros | 8 |
| `rt_*` | Otros | 8 |
| `car_*` | Caratulación | 6 |
| `aa_*` | Auxiliares / Temporales | 6 |
| `cs_*` | Otros | 6 |
| `ant_*` | Anticipos | 6 |
| `mpc_*` | Otros | 4 |
| `fin_*` | Otros | 3 |
| `fe_*` | Otros | 2 |
| `no_*` | Otros | 2 |
| `siifa_*` | Otros | 1 |
| `tmp_*` | Otros | 1 |
| `temp_*` | Otros | 1 |
| `flyway_*` | Otros | 1 |
| `sc_*` | Otros | 1 |
| `archivo_*` | Otros | 1 |
| `bases_*` | Otros | 1 |
| `giro_*` | Otros | 1 |
| `int_*` | Otros | 1 |
| `_*` | Otros | 1 |

---

## 3. Schema de Tablas Críticas para el Modelo Predictivo


### `cm_facturas` (68 columnas)

| Columna | Tipo | Nulos | Llave |
|---|---|---|---|
| `id` | int | NO | PRI |
| `gn_empresas_id` | int | NO | MUL |
| `cm_grupos_id` | int | NO | MUL |
| `cnt_prestadores_id` | int | NO | MUL |
| `cm_rips_cargas_id` | int | YES | MUL |
| `gn_usuarios_lider_id` | int | NO | MUL |
| `gn_usuarios_tecnico_id` | int | YES | MUL |
| `gn_usuarios_medico_id` | int | YES | MUL |
| `gn_usuarios_gestiona_id` | int | YES | MUL |
| `cm_fe_rips_cargas_id` | int | YES | MUL |
| `mae_tipo_contrato_id` | int | NO | MUL |
| `mae_tipo_contrato_codigo` | varchar(8) | YES | MUL |
| `mae_tipo_contrato_valor` | varchar(128) | YES | MUL |
| `nit` | varchar(16) | NO | MUL |
| `ips` | varchar(256) | NO | MUL |
| `numero_radicado` | int | NO | MUL |
| `numero_facturado` | varchar(32) | NO | MUL |
| `fecha_prestacion` | datetime | YES | nan |
| `fecha_radicacion` | datetime | NO | MUL |
| `multiusuario` | bit(1) | NO | nan |
| `valor_pendiente_actual` | decimal(20,4) | YES | MUL |
| `valor_inicial_glosa` | decimal(20,4) | NO | MUL |
| `marcacion` | int | NO | nan |
| `fecha_marcacion` | datetime | YES | nan |
| `fecha_vencimiento` | datetime | YES | nan |
| `tipo_auditoria` | int | NO | MUL |
| `historial_proceso` | varchar(512) | YES | nan |
| `valor_factura` | decimal(20,4) | NO | MUL |
| `valor_pagado_factura` | decimal(20,4) | YES | nan |
| `valor_copago` | decimal(20,4) | YES | MUL |
| `valor_bruto` | decimal(20,4) | YES | nan |
| `valor_cuota_moderadora` | decimal(20,4) | YES | nan |
| `mae_regimen_id` | int | NO | nan |
| `mae_regimen_codigo` | varchar(8) | YES | nan |
| `mae_regimen_valor` | varchar(128) | YES | nan |
| `estado_factura` | int | NO | MUL |
| `pbs` | bit(1) | YES | nan |
| `numero_contrato` | varchar(32) | NO | nan |
| `numero_contrato_auditoria` | varchar(32) | YES | nan |
| `impuesto_timbre` | bit(1) | NO | nan |
| `origen_factura` | int | NO | nan |
| `usuario_audita` | varchar(128) | YES | nan |
| `terminal_audita` | varchar(16) | YES | nan |
| `fecha_hora_audita` | datetime | YES | nan |
| `usuario_devuelve` | varchar(128) | YES | nan |
| `terminal_devuelve` | varchar(16) | YES | nan |
| `fecha_hora_devuelve` | datetime | YES | nan |
| `usuario_respuesta` | varchar(128) | YES | nan |
| `terminal_respuesta` | varchar(16) | YES | nan |
| `fecha_hora_respuesta` | datetime | YES | nan |
| `usuario_concilia` | varchar(128) | YES | nan |
| `terminal_concilia` | varchar(16) | YES | nan |
| `fecha_hora_concilia` | datetime | YES | nan |
| `respuesta_ips` | bit(1) | NO | nan |
| `fecha_marcacion_respuesta_ips` | datetime | YES | nan |
| `fecha_asignacion_tecnico` | datetime | YES | nan |
| `fecha_asignacion_medico` | datetime | YES | nan |
| `version` | tinyint(1) | NO | MUL |
| `ejecucion_glosa_aut_bot` | varchar(16) | NO | nan |
| `valor_no_acuerdo` | decimal(20,4) | YES | nan |
| `ejecucion_glosa_aut_ia` | varchar(16) | NO | nan |
| `estado_glosa_aut` | tinyint | NO | MUL |
| `usuario_crea` | varchar(128) | NO | nan |
| `terminal_crea` | varchar(16) | NO | nan |
| `fecha_hora_crea` | datetime | NO | nan |
| `usuario_modifica` | varchar(128) | YES | nan |
| `terminal_modifica` | varchar(16) | YES | nan |
| `fecha_hora_modifica` | datetime | YES | nan |

**Relaciones FK:**
**Referencia hacia:**
- `cm_fe_rips_cargas_id` → `cm_fe_rips_cargas.id`
- `cm_grupos_id` → `cm_grupos.id`
- `cm_rips_cargas_id` → `cm_rips_cargas.id`
- `cnt_prestadores_id` → `cnt_prestadores.id`
- `gn_empresas_id` → `gn_empresas.id`
- `gn_usuarios_lider_id` → `gn_usuarios.id`
- `gn_usuarios_medico_id` → `gn_usuarios.id`
- `gn_usuarios_tecnico_id` → `gn_usuarios.id`
- `gn_usuarios_gestiona_id` → `gn_usuarios.id`

**Es referenciada por:**
- `cm_auditoria_adjuntos.cm_facturas_id`
- `cm_auditoria_autorizaciones.cm_facturas_id`
- `cm_auditoria_cierres.cm_facturas_id`
- `cm_auditoria_devoluciones.cm_facturas_id`
- `cm_detalles.cm_facturas_id`
- `cm_factura_estados.cm_facturas_id`
- `cm_factura_transacciones.cm_facturas_id`
- `cm_fe_notas.cm_facturas_id`
- `cm_fe_rips_facturas.cm_facturas_id`
- `cm_fe_soportes.cm_facturas_id`
- `cm_glosa_respuestas.cm_facturas_id`
- `cm_historico_facturas.cm_facturas_id`
- `cm_pago_facturas.cm_facturas_id`
- `cs_copago_moderadora_historicos.cm_facturas_id`
- `rco_facturas.cm_facturas_id`
- `ws_cm_facturas.cm_facturas_id`


### `cm_detalles` (63 columnas)

| Columna | Tipo | Nulos | Llave |
|---|---|---|---|
| `id` | int | NO | PRI |
| `cm_facturas_id` | int | NO | MUL |
| `aseg_afiliados_id` | int | YES | MUL |
| `estado` | int | NO | nan |
| `mae_tipo_documento_id` | int | NO | MUL |
| `mae_tipo_documento_codigo` | varchar(8) | YES | nan |
| `mae_tipo_documento_valor` | varchar(128) | YES | nan |
| `documento` | varchar(20) | NO | nan |
| `nombre_completo_afiliado` | varchar(512) | NO | nan |
| `consecutivo_item` | int | NO | nan |
| `ma_servicio_id` | int | NO | nan |
| `ma_servicio_codigo` | varchar(32) | YES | nan |
| `ma_servicio_valor` | varchar(512) | YES | nan |
| `cantidad` | int | YES | nan |
| `radicado_glosa` | int | YES | nan |
| `valor_copago` | decimal(20,4) | NO | nan |
| `valor_facturado` | decimal(20,4) | NO | nan |
| `valor_unitario` | decimal(20,4) | YES | nan |
| `valor_pagado` | decimal(20,4) | YES | nan |
| `valor_pendiente` | decimal(20,4) | YES | nan |
| `valor_pendiente_actual` | decimal(20,4) | YES | nan |
| `valor_aceptado_ips` | decimal(20,4) | YES | nan |
| `observacion` | longtext | YES | nan |
| `valor_pagado_eps` | decimal(20,4) | YES | nan |
| `porcentaje_pagado_eps` | decimal(20,4) | YES | nan |
| `porcentaje_aceptado_ips` | decimal(20,4) | YES | nan |
| `observacion_respuesta_detalles` | longtext | YES | nan |
| `aplica_ac` | bit(1) | YES | nan |
| `aplica_dc` | bit(1) | YES | nan |
| `aplica_pbs` | bit(1) | YES | nan |
| `tipo_servicio` | int | NO | nan |
| `fecha_prestacion` | datetime | YES | nan |
| `valor_copago_item` | decimal(20,4) | YES | nan |
| `aplica_glosa` | bit(1) | YES | nan |
| `aplica_concepto` | bit(1) | YES | nan |
| `aplica_dx` | bit(1) | YES | nan |
| `aplica_autorizacion` | bit(1) | YES | nan |
| `valor_glosa` | decimal(20,4) | YES | nan |
| `motivo_glosa` | varchar(1024) | YES | nan |
| `concepto_contable` | varchar(1024) | YES | nan |
| `porcentaje_concepto` | decimal(4,0) | YES | nan |
| `numero_autorizacion` | varchar(32) | YES | nan |
| `codigo_dx` | varchar(8) | YES | nan |
| `nombre_dx` | varchar(1024) | YES | nan |
| `mae_ambito_id` | int | YES | nan |
| `mae_ambito_codigo` | varchar(8) | YES | nan |
| `mae_ambito_valor` | varchar(128) | YES | nan |
| `copago_no_efectivo` | bit(1) | YES | nan |
| `aplica_recobro` | bit(1) | NO | nan |
| `mipres_numero_prescripcion` | varchar(32) | YES | nan |
| `mipres_id_entrega` | varchar(32) | YES | nan |
| `mae_motivo_respuesta_glosa_especifico_id` | int | YES | nan |
| `mae_motivo_respuesta_glosa_especifico_codigo` | varchar(8) | YES | nan |
| `mae_motivo_respuesta_glosa_especifico_valor` | varchar(128) | YES | nan |
| `mae_motivo_respuesta_glosa_aplicacion_id` | int | YES | nan |
| `mae_motivo_respuesta_glosa_aplicacion_codigo` | varchar(8) | YES | nan |
| `mae_motivo_respuesta_glosa_aplicacion_valor` | varchar(128) | YES | nan |
| `usuario_crea` | varchar(128) | NO | nan |
| `terminal_crea` | varchar(16) | NO | nan |
| `fecha_hora_crea` | datetime | NO | nan |
| `usuario_modifica` | varchar(128) | YES | nan |
| `terminal_modifica` | varchar(16) | YES | nan |
| `fecha_hora_modifica` | datetime | YES | nan |

**Relaciones FK:**
**Referencia hacia:**
- `aseg_afiliados_id` → `aseg_afiliados.id`
- `cm_facturas_id` → `cm_facturas.id`

**Es referenciada por:**
- `cm_auditoria_adjuntos.cm_detalles_id`
- `cm_auditoria_autorizaciones.cm_detalles_id`
- `cm_auditoria_capita_descuentos.cm_detalles_id`
- `cm_auditoria_conceptos_contables.cm_detalles_id`
- `cm_auditoria_diagnosticos.cm_detalles_id`
- `cm_auditoria_motivos_glosas.cm_detalles_id`
- `cm_gestion_usuarios.cm_detalles_id`
- `cm_glosa_respuesta_detalles.cm_detalles_id`
- `cnt_contrato_historico_prestaciones.cm_detalles_id`
- `rco_factura_detalles.cm_detalle_id`


### `cm_auditoria_motivos_glosas` (19 columnas)

| Columna | Tipo | Nulos | Llave |
|---|---|---|---|
| `id` | int | NO | PRI |
| `cm_detalles_id` | int | NO | MUL |
| `mae_motivo_id` | int | NO | nan |
| `mae_motivo_codigo` | varchar(8) | YES | nan |
| `mae_motivo_valor` | varchar(128) | YES | nan |
| `mae_motivo_especifico_id` | int | NO | nan |
| `mae_motivo_especifico_codigo` | varchar(8) | YES | nan |
| `mae_motivo_especifico_valor` | varchar(128) | YES | nan |
| `mae_motivo_glosa_aplicacion_id` | int | YES | nan |
| `mae_motivo_glosa_aplicacion_codigo` | varchar(8) | YES | nan |
| `mae_motivo_glosa_aplicacion_valor` | varchar(128) | YES | nan |
| `mae_motivo_glosa_aplicacion_descripcion` | varchar(512) | YES | nan |
| `porcentaje` | decimal(5,2) | YES | nan |
| `valor_motivo` | decimal(20,2) | YES | nan |
| `observacion` | longtext | YES | nan |
| `tipologia` | int | NO | nan |
| `usuario_crea` | varchar(128) | NO | nan |
| `terminal_crea` | varchar(16) | NO | nan |
| `fecha_hora_crea` | datetime | NO | nan |

**Relaciones FK:**
**Referencia hacia:**
- `cm_detalles_id` → `cm_detalles.id`


### `cm_fe_rips_cargas` (63 columnas)

| Columna | Tipo | Nulos | Llave |
|---|---|---|---|
| `id` | int | NO | PRI |
| `gn_empresas_id` | int | NO | MUL |
| `cnt_prestador_sedes_id` | int | YES | MUL |
| `carga_periodo_id` | int | YES | MUL |
| `tipo` | int | NO | nan |
| `cnt_contratos_id` | int | YES | MUL |
| `radicador_asignado` | int | YES | MUL |
| `contrato` | varchar(32) | YES | nan |
| `cnt_tipo_contrato_id` | int | YES | nan |
| `estado` | int | NO | nan |
| `mae_regimen_id` | int | YES | nan |
| `mae_regimen_codigo` | varchar(8) | YES | nan |
| `mae_regimen_valor` | varchar(128) | YES | nan |
| `mae_contrato_modalidad_id` | int | YES | nan |
| `mae_contrato_modalidad_codigo` | varchar(8) | YES | nan |
| `mae_contrato_modalidad_valor` | varchar(128) | YES | nan |
| `fecha_hora_inicio` | datetime | YES | nan |
| `fecha_hora_fin` | datetime | YES | nan |
| `tiempo` | int | YES | nan |
| `cobertura` | bit(1) | NO | nan |
| `factura_numero` | varchar(16) | YES | nan |
| `factura_valor` | decimal(18,2) | YES | nan |
| `soportes_numero` | int | NO | nan |
| `rechazo` | bit(1) | NO | nan |
| `fecha_hora_rechazo` | datetime | YES | nan |
| `observacion_rechazo` | varchar(512) | YES | nan |
| `devolucion` | bit(1) | NO | nan |
| `fecha_hora_devolucion` | datetime | YES | nan |
| `mae_devolucion_id` | int | YES | nan |
| `mae_devolucion_codigo` | varchar(8) | YES | nan |
| `mae_devolucion_valor` | varchar(128) | YES | nan |
| `observacion_devolucion` | varchar(512) | YES | nan |
| `observacion` | varchar(512) | YES | nan |
| `documento_prestador` | varchar(32) | NO | nan |
| `cuv` | varchar(128) | YES | nan |
| `cufe` | varchar(128) | YES | nan |
| `de1601_eps_erronea` | bit(1) | YES | nan |
| `de4401_profesional_red` | bit(1) | YES | nan |
| `de4402_profesional_independiente` | bit(1) | YES | nan |
| `de5001_pagada` | bit(1) | YES | nan |
| `de5002_radicada` | bit(1) | YES | nan |
| `de5601_soporte_fe` | bit(1) | YES | nan |
| `de5601_soportes` | bit(1) | YES | nan |
| `fecha_hora_emision` | datetime | NO | nan |
| `fecha_hora_ministerio` | datetime | NO | nan |
| `origen_carga` | int | NO | nan |
| `url_xml` | varchar(512) | YES | nan |
| `url_json` | varchar(512) | YES | nan |
| `valor_copago` | decimal(20,4) | YES | nan |
| `valor_cuota_moderadora` | decimal(20,4) | YES | nan |
| `origen` | int | YES | nan |
| `capita_periodo` | int | YES | nan |
| `numero_nota` | varchar(32) | YES | nan |
| `multiusuario` | bit(1) | YES | nan |
| `soporte_mercurio` | int | YES | nan |
| `id_mercurio` | varchar(16) | YES | MUL |
| `fecha_hora_mercurio` | datetime | YES | nan |
| `usuario_crea` | varchar(128) | NO | nan |
| `terminal_crea` | varchar(16) | NO | nan |
| `fecha_hora_crea` | datetime | NO | nan |
| `usuario_modifica` | varchar(128) | YES | nan |
| `terminal_modifica` | varchar(16) | YES | nan |
| `fecha_hora_modifica` | datetime | YES | nan |

**Relaciones FK:**
**Referencia hacia:**
- `carga_periodo_id` → `cm_fe_rips_cargas.id`
- `cnt_contratos_id` → `cnt_contratos.id`
- `cnt_prestador_sedes_id` → `cnt_prestador_sedes.id`
- `gn_empresas_id` → `gn_empresas.id`
- `radicador_asignado` → `gn_usuarios.id`

**Es referenciada por:**
- `cm_facturas.cm_fe_rips_cargas_id`
- `cm_fe_rips_carga_adjuntos.cm_fe_rips_cargas_id`
- `cm_fe_rips_carga_contenidos.cm_fe_rips_cargas_id`
- `cm_fe_rips_cargas.carga_periodo_id`
- `cm_fe_rips_facturas.cm_fe_rips_cargas_id`
- `cm_fe_soportes.cm_fe_rips_cargas_id`
- `cm_fe_transacciones.cm_fe_rips_cargas_id`
- `cm_radicados.cm_fe_rips_cargas_id`


### `cm_fe_rips_carga_contenidos` (10 columnas)

| Columna | Tipo | Nulos | Llave |
|---|---|---|---|
| `id` | int | NO | PRI |
| `cm_fe_rips_cargas_id` | int | NO | MUL |
| `tipo` | int | NO | nan |
| `json` | json | YES | nan |
| `xml` | mediumtext | YES | nan |
| `cuv` | text | YES | nan |
| `cuv_json` | json | YES | nan |
| `usuario_crea` | varchar(128) | NO | nan |
| `terminal_crea` | varchar(16) | NO | nan |
| `fecha_hora_crea` | datetime | NO | nan |

**Relaciones FK:**
**Referencia hacia:**
- `cm_fe_rips_cargas_id` → `cm_fe_rips_cargas.id`


### `cm_factura_estados` (7 columnas)

| Columna | Tipo | Nulos | Llave |
|---|---|---|---|
| `id` | int | NO | PRI |
| `cm_facturas_id` | int | NO | MUL |
| `estado_factura` | int | NO | nan |
| `tipo_auditoria` | int | YES | nan |
| `usuario_crea` | varchar(128) | NO | nan |
| `terminal_crea` | varchar(16) | NO | nan |
| `fecha_hora_crea` | datetime | NO | nan |

**Relaciones FK:**
**Referencia hacia:**
- `cm_facturas_id` → `cm_facturas.id`


### `cm_auditoria_devoluciones` (30 columnas)

| Columna | Tipo | Nulos | Llave |
|---|---|---|---|
| `id` | int | NO | PRI |
| `cm_facturas_id` | int | NO | MUL |
| `cm_devolucion_masiva_id` | int | YES | MUL |
| `mae_motivo_devolucion_id` | int | NO | nan |
| `mae_motivo_devolucion_codigo` | varchar(8) | YES | nan |
| `mae_motivo_devolucion_valor` | varchar(128) | YES | nan |
| `mae_contrato_modalidad_id` | int | NO | nan |
| `mae_contrato_modalidad_codigo` | varchar(8) | YES | nan |
| `mae_contrato_modalidad_valor` | varchar(128) | YES | nan |
| `mae_regimen_id` | int | NO | nan |
| `mae_regimen_codigo` | varchar(8) | YES | nan |
| `mae_regimen_valor` | varchar(128) | YES | nan |
| `nit` | varchar(16) | NO | nan |
| `ips` | varchar(256) | NO | nan |
| `numero_radicado` | varchar(32) | NO | nan |
| `numero_facturado` | varchar(32) | NO | nan |
| `fecha_radicacion` | datetime | NO | nan |
| `fecha_devolucion` | datetime | NO | nan |
| `valor_factura` | decimal(20,4) | NO | nan |
| `observacion` | longtext | YES | nan |
| `mae_devolucion_motivo_general_id` | int | YES | nan |
| `mae_devolucion_motivo_general_codigo` | varchar(8) | YES | nan |
| `mae_devolucion_motivo_general_valor` | varchar(128) | YES | nan |
| `mae_devolucion_motivo_general_descripcion` | varchar(512) | YES | nan |
| `usuario_crea` | varchar(128) | NO | nan |
| `terminal_crea` | varchar(16) | NO | nan |
| `fecha_hora_crea` | datetime | NO | nan |
| `usuario_modifica` | varchar(128) | YES | nan |
| `terminal_modifica` | varchar(16) | YES | nan |
| `fecha_hora_modifica` | datetime | YES | nan |

**Relaciones FK:**
**Referencia hacia:**
- `cm_devolucion_masiva_id` → `cm_devolucion_masiva.id`
- `cm_facturas_id` → `cm_facturas.id`

**Es referenciada por:**
- `cm_radicados.cm_auditoria_devoluciones_id`


### `cm_glosa_respuestas` (19 columnas)

| Columna | Tipo | Nulos | Llave |
|---|---|---|---|
| `id` | int | NO | PRI |
| `cm_facturas_id` | int | NO | MUL |
| `tipo_respuesta` | int | YES | nan |
| `cm_conciliaciones_id` | int | YES | MUL |
| `valor_cobro_detalle` | decimal(20,4) | NO | nan |
| `valor_facturado` | decimal(20,4) | NO | nan |
| `valor_pagado` | decimal(20,4) | NO | nan |
| `vaor_pagado_eps` | decimal(20,4) | NO | nan |
| `valor_pendiente` | decimal(20,4) | NO | nan |
| `valor_aceptado_ips` | decimal(20,4) | NO | nan |
| `observacion` | longtext | NO | nan |
| `estado_sincronizacion` | int | NO | nan |
| `representante_eps` | varchar(128) | YES | nan |
| `representante_ips` | varchar(128) | YES | nan |
| `cm_glosa_masiva_id` | int | YES | MUL |
| `valor_no_acuerdo` | decimal(20,4) | YES | nan |
| `usuario_crea` | varchar(128) | NO | nan |
| `terminal_crea` | varchar(16) | NO | nan |
| `fecha_hora_crea` | datetime | NO | nan |

**Relaciones FK:**
**Referencia hacia:**
- `cm_glosa_masiva_id` → `cm_glosa_masiva.id`
- `cm_conciliaciones_id` → `cm_conciliaciones.id`
- `cm_facturas_id` → `cm_facturas.id`

**Es referenciada por:**
- `cm_glosa_respuesta_detalles.cm_glosa_respuestas_id`
- `cm_radicados.cm_glosa_respuestas_id`
- `cm_radicados.cm_glosa_respuestas_conciliacion_id`
- `cm_sincronizaciones.cm_glosa_respuestas_id`
- `ws_cm_transacciones.cm_glosa_respuestas_id`


### `aseg_afiliados` (200 columnas)

| Columna | Tipo | Nulos | Llave |
|---|---|---|---|
| `id` | int | NO | PRI |
| `aseg_grupos_familiares_id` | int | YES | MUL |
| `nacionalidad_ubicaciones_id` | int | YES | MUL |
| `nacimiento_ubicaciones_id` | int | YES | MUL |
| `afiliacion_ubicaciones_id` | int | NO | MUL |
| `residencia_ubicacion_id` | int | YES | MUL |
| `gn_divisiones_id` | int | YES | MUL |
| `gn_ubicaciones_lugar_nacimiento_id` | int | YES | MUL |
| `gn_ubicacion_barrios_id` | int | YES | MUL |
| `id_afiliado` | varchar(45) | NO | MUL |
| `serial_bdua` | bigint | YES | nan |
| `registro_bdua` | tinyint(1) | NO | nan |
| `primer_nombre` | varchar(64) | NO | MUL |
| `segundo_nombre` | varchar(64) | YES | MUL |
| `primer_apellido` | varchar(64) | NO | MUL |
| `segundo_apellido` | varchar(64) | YES | MUL |
| `fecha_nacimiento` | date | NO | nan |
| `genero` | varchar(8) | NO | nan |
| `mae_genero_id` | int | YES | nan |
| `mae_genero_codigo` | varchar(8) | YES | nan |
| `mae_genero_valor` | varchar(128) | YES | nan |
| `fecha_expedicion_cedula` | date | YES | nan |
| `mae_tipo_documento_id` | int | NO | MUL |
| `mae_tipo_documento_codigo` | varchar(8) | YES | nan |
| `mae_tipo_documento_valor` | varchar(128) | YES | nan |
| `numero_documento` | varchar(16) | NO | MUL |
| `mae_tipo_documento_cf_id` | int | YES | nan |
| `mae_tipo_documento_cf_codigo` | varchar(8) | YES | nan |
| `mae_tipo_documento_cf_valor` | varchar(128) | YES | nan |
| `numero_documento_cf` | varchar(32) | YES | MUL |
| `fecha_afiliacion_sgsss` | date | NO | nan |
| `fecha_afiliacion_eps` | date | NO | nan |
| `afiliacion_legalizada` | tinyint(1) | YES | nan |
| `fecha_egreso_eps` | date | YES | nan |
| `fecha_suspension_eps` | date | YES | nan |
| `fecha_cambio_estado_eps` | datetime | YES | nan |
| `tipo_beneficiario` | varchar(8) | NO | nan |
| `mae_tipo_afiliado_id` | int | YES | nan |
| `mae_tipo_afiliado_codigo` | varchar(8) | YES | nan |
| `mae_tipo_afiliado_valor` | varchar(128) | YES | nan |
| `mae_estado_afiliacion_id` | int | NO | nan |
| `mae_estado_afiliacion_codigo` | varchar(8) | YES | nan |
| `mae_estado_afiliacion_valor` | varchar(128) | YES | nan |
| `mae_origen_afiliado_id` | int | NO | nan |
| `mae_origen_afiliado_codigo` | varchar(8) | YES | nan |
| `mae_origen_afiliado_valor` | varchar(128) | YES | nan |
| `parentesco_cotizante` | varchar(16) | YES | nan |
| `mae_parentesco_cotizante_id` | int | YES | nan |
| `mae_parentesco_cotizante_codigo` | varchar(8) | YES | nan |
| `mae_parentesco_cotizante_valor` | varchar(128) | YES | nan |
| `tratamiento_datos_autoriza` | bit(1) | YES | nan |
| `tratamient_datos_fecha_hora` | datetime | YES | nan |
| `autoriza_envio_sms` | tinyint(1) | YES | nan |
| `autoriza_envio_email` | tinyint(1) | YES | nan |
| `telefono_fijo` | varchar(32) | YES | nan |
| `telefono_movil` | varchar(32) | YES | nan |
| `email` | varchar(128) | YES | nan |
| `zona` | varchar(8) | NO | nan |
| `mae_zona_id` | int | YES | nan |
| `mae_zona_codigo` | varchar(8) | YES | nan |
| `mae_zona_valor` | varchar(128) | YES | nan |
| `direccion_residencia` | varchar(512) | NO | nan |
| `direccion_georeferenciada` | bit(1) | NO | nan |
| `direccion_georef_latitud` | decimal(12,9) | YES | nan |
| `direccion_georef_longitud` | decimal(12,9) | YES | nan |
| `barrio` | varchar(64) | YES | nan |
| `regimen` | varchar(8) | NO | nan |
| `mae_regimen_id` | int | NO | nan |
| `mae_regimen_codigo` | varchar(8) | NO | nan |
| `mae_regimen_valor` | varchar(128) | NO | nan |
| `mae_grupo_sisben_id` | int | YES | nan |
| `mae_grupo_sisben_codigo` | varchar(8) | YES | nan |
| `mae_grupo_sisben_valor` | varchar(128) | YES | nan |
| `mae_sub_grupo_sisben_id` | int | YES | nan |
| `mae_sub_grupo_sisben_codigo` | varchar(8) | YES | nan |
| `mae_sub_grupo_sisben_valor` | varchar(128) | YES | nan |
| `nivel_sisben` | varchar(8) | NO | nan |
| `mae_nivel_sisben_id` | int | NO | nan |
| `mae_nivel_sisben_codigo` | varchar(8) | NO | nan |
| `mae_nivel_sisben_valor` | varchar(128) | NO | nan |
| `puntaje_sisben` | decimal(4,2) | YES | nan |
| `ficha_sisben` | varchar(32) | YES | nan |
| `fecha_sisben` | date | YES | nan |
| `categoria_ibc` | varchar(16) | YES | nan |
| `mae_categoria_ibc_id` | int | YES | nan |
| `mae_categoria_ibc_codigo` | varchar(8) | YES | nan |
| `mae_categoria_ibc_valor` | varchar(128) | YES | nan |
| `primaria_cnt_prestador_sedes_id` | int | NO | MUL |
| `odontologia_cnt_prestador_sedes_id` | int | YES | MUL |
| `tiene_portabilidad` | tinyint(1) | YES | nan |
| `fecha_portabilidad` | date | YES | nan |
| `portabilidad_cnt_prestador_sedes_id` | int | YES | MUL |
| `tipo_cotizante` | varchar(8) | YES | nan |
| `mae_tipo_cotizante_id` | int | YES | nan |
| `mae_tipo_cotizante_codigo` | varchar(8) | YES | nan |
| `mae_tipo_cotizante_valor` | varchar(128) | YES | nan |
| `discapacidad` | tinyint(1) | NO | nan |
| `tipo_discapacidad` | varchar(16) | YES | nan |
| `mae_tipo_discapacidad_id` | int | YES | nan |
| `mae_tipo_discapacidad_codigo` | varchar(8) | YES | nan |
| `mae_tipo_discapacidad_valor` | varchar(128) | YES | nan |
| `condicion_discapacidad` | varchar(8) | YES | nan |
| `mae_discapacidad_condicion_id` | int | YES | nan |
| `mae_discapacidad_condicion_codigo` | varchar(8) | YES | nan |
| `mae_discapacidad_condicion_valor` | varchar(128) | YES | nan |
| `fecha_inicio_discapacidad` | date | YES | nan |
| `fecha_fin_discapacidad` | date | YES | nan |
| `mae_grupo_poblacional_id` | int | NO | nan |
| `mae_grupo_poblacional_codigo` | varchar(8) | YES | nan |
| `mae_grupo_poblacional_valor` | varchar(128) | YES | nan |
| `mae_metodologia_grupo_poblacional_id` | int | YES | nan |
| `mae_metodologia_grupo_poblacional_codigo` | varchar(8) | YES | nan |
| `mae_metodologia_grupo_poblacional_valor` | varchar(128) | YES | nan |
| `victima` | tinyint(1) | YES | nan |
| `etnia` | varchar(32) | NO | nan |
| `mae_etnia_id` | int | YES | nan |
| `mae_etnia_codigo` | varchar(8) | YES | nan |
| `mae_etnia_valor` | varchar(128) | YES | nan |
| `mae_comunidad_etnia_id` | int | YES | nan |
| `mae_comunidad_etnia_codigo` | varchar(8) | YES | nan |
| `mae_comunidad_etnia_valor` | varchar(128) | YES | nan |
| `mae_causa_novedad_id` | int | NO | nan |
| `mae_causa_novedad_codigo` | varchar(8) | YES | nan |
| `mae_causa_novedad_valor` | varchar(128) | YES | nan |
| `fecha_reactivacion` | datetime | YES | nan |
| `estado_civil` | varchar(8) | NO | nan |
| `mae_estado_civil_id` | int | YES | nan |
| `mae_estado_civil_codigo` | varchar(8) | YES | nan |
| `mae_estado_civil_valor` | varchar(128) | YES | nan |
| `fecha_movilidad` | date | YES | nan |
| `modelo_liquidacion` | varchar(8) | NO | nan |
| `mae_modelo_liquidacion_id` | int | YES | nan |
| `mae_modelo_liquidacion_codigo` | varchar(8) | YES | nan |
| `mae_modelo_liquidacion_valor` | varchar(128) | YES | nan |
| `mae_tipo_documento_aportante_id` | int | YES | nan |
| `mae_tipo_documento_aportante_codigo` | varchar(8) | YES | nan |
| `mae_tipo_documento_aportante_valor` | varchar(128) | YES | nan |
| `numero_documento_aportante` | varchar(32) | YES | nan |
| `mae_actividad_economica_id` | int | YES | nan |
| `mae_actividad_economica_codigo` | varchar(8) | YES | nan |
| `mae_actividad_economica_valor` | varchar(128) | YES | nan |
| `mae_arl_id` | int | YES | nan |
| `mae_arl_codigo` | varchar(8) | YES | nan |
| `mae_arl_valor` | varchar(128) | YES | nan |
| `mae_afp_id` | int | YES | nan |
| `mae_afp_codigo` | varchar(8) | YES | nan |
| `mae_afp_valor` | varchar(128) | YES | nan |
| `mae_caja_compensacion_id` | int | YES | nan |
| `mae_caja_compensacion_codigo` | varchar(8) | YES | nan |
| `mae_caja_compensacion_valor` | varchar(128) | YES | nan |
| `sincronizado` | int | YES | nan |
| `observacion` | varchar(1024) | YES | nan |
| `historico_afiliado` | longtext | YES | nan |
| `codigo_fonetico` | varchar(128) | YES | MUL |
| `origen_ultimo_registro` | int | YES | nan |
| `acepta_contribucion_solidaria` | bit(1) | YES | nan |
| `mae_solidaria_porcentaje_id` | int | YES | nan |
| `mae_solidaria_porcentaje_codigo` | varchar(8) | YES | nan |
| `mae_solidaria_porcentaje_valor` | varchar(128) | YES | nan |
| `mae_genero_identificacion_id` | int | YES | nan |
| `mae_genero_identificacion_codigo` | varchar(8) | YES | nan |
| `mae_genero_identificacion_valor` | varchar(128) | YES | nan |
| `incapacidad_prolongada` | bit(1) | YES | nan |
| `acuerdo_pago` | bit(1) | YES | nan |
| `fecha_acuerdo_pago` | datetime | YES | nan |
| `usuario_gestante` | bit(1) | YES | nan |
| `fecha_fin_periodo_gestacion` | datetime | YES | nan |
| `duplicado` | bit(1) | YES | nan |
| `traslado_preaprobado` | bit(1) | YES | nan |
| `direccion_alterna_contacto` | varchar(512) | YES | nan |
| `nombre_contacto_emergencia` | varchar(128) | YES | nan |
| `telefono_contacto_emergencia` | varchar(16) | YES | nan |
| `mae_tipo_portabilidad_id` | int | YES | nan |
| `mae_tipo_portabilidad_codigo` | varchar(8) | YES | nan |
| `mae_tipo_portabilidad_valor` | varchar(128) | YES | nan |
| `mae_motivo_portabilidad_id` | int | YES | nan |
| `mae_motivo_portabilidad_codigo` | varchar(8) | YES | nan |
| `mae_motivo_portabilidad_valor` | varchar(128) | YES | nan |
| `mae_origen_solicitud_portabilidad_id` | int | YES | nan |
| `mae_origen_solicitud_portabilidad_codigo` | varchar(8) | YES | nan |
| `mae_origen_solicitud_portabilidad_valor` | varchar(128) | YES | nan |
| `periodo_inicial_portabilidad` | date | YES | nan |
| `periodo_final_portabilidad` | date | YES | nan |
| `telefono_contacto_portabilidad` | varchar(10) | YES | nan |
| `direccion_portabilidad` | varchar(256) | YES | nan |
| `correo_electronico_portabilidad` | varchar(512) | YES | nan |
| `observacion_portabilidad` | text | YES | nan |
| `gn_ubicacion_actual_afiliado` | int | YES | MUL |
| `poblacion_especial` | bit(1) | NO | nan |
| `poblacion_lgtbiq` | bit(1) | NO | nan |
| `mae_tipo_documento_cn_id` | int | YES | nan |
| `mae_tipo_documento_cn_codigo` | varchar(8) | YES | nan |
| `mae_tipo_documento_cn_valor` | varchar(128) | YES | nan |
| `numero_documento_cn` | varchar(32) | YES | nan |
| `usuario_crea` | varchar(128) | NO | nan |
| `terminal_crea` | varchar(16) | NO | nan |
| `fecha_hora_crea` | datetime | NO | nan |
| `usuario_modifica` | varchar(128) | YES | nan |
| `terminal_modifica` | varchar(16) | YES | nan |
| `fecha_hora_modifica` | datetime | YES | nan |

**Relaciones FK:**
**Referencia hacia:**
- `aseg_grupos_familiares_id` → `aseg_grupos_familiares.id`
- `primaria_cnt_prestador_sedes_id` → `cnt_prestador_sedes.id`
- `portabilidad_cnt_prestador_sedes_id` → `cnt_prestador_sedes.id`
- `odontologia_cnt_prestador_sedes_id` → `cnt_prestador_sedes.id`
- `gn_divisiones_id` → `gn_divisiones.id`
- `nacionalidad_ubicaciones_id` → `gn_ubicaciones.id`
- `gn_ubicacion_actual_afiliado` → `gn_ubicaciones.id`
- `gn_ubicacion_barrios_id` → `gn_ubicacion_barrios.id`
- `nacimiento_ubicaciones_id` → `gn_ubicaciones.id`
- `afiliacion_ubicaciones_id` → `gn_ubicaciones.id`
- `residencia_ubicacion_id` → `gn_ubicaciones.id`
- `gn_ubicaciones_lugar_nacimiento_id` → `gn_ubicaciones.id`

**Es referenciada por:**
- `ant_anticipos.aseg_afiliados_id`
- `aseg_afiliado_certificados.aseg_afiliados_id`
- `aseg_afiliado_contactos.aseg_afiliados_id`
- `aseg_afiliado_coordenadas.id_afiliado`
- `aseg_afiliado_documentos.aseg_afiliados_id`
- `aseg_afiliado_historicos.aseg_afiliados_id`
- `aseg_anexos1.aseg_afiliados_id`
- `aseg_grupos_familiares.aseg_afiliados_id`
- `aseg_portabilidades.aseg_afiliados_id`
- `aseg_radicado_novedades.aseg_afiliados_id`
- `aseg_reporte_novedades.aseg_afiliados_id`
- `aseg_tabulacion_encuestas.aseg_afiliados_id`
- `aseg_traslados.aseg_afiliados_id`
- `au_anexo2_rescates.aseg_afiliados_id`
- `au_anexos2.aseg_afiliados_id`
- `au_anexos3.aseg_afiliados_id`
- `au_anexos4.aseg_afiliados_id`
- `au_cotizaciones.aseg_afiliados_id`
- `au_no_solicitudes.aseg_afiliados_id`
- `au_rechazos.aseg_afiliados_id`
- `au_seguimiento_afiliados.aseg_afiliados_id`
- `au_tope_afiliados.ase_afiliados_id`
- `auc_afiliados.aseg_afiliados_id`
- `aus_personas.aseg_afiliados_id`
- `cm_detalles.aseg_afiliados_id`
- `cnt_contrato_historico_prestaciones.aseg_afiliados_id`
- `cs_copago_moderadora_historicos.aseg_afiliados_id`
- `gat_usuarios.aseg_afiliados_id`
- `gj_terceros.aseg_afiliados_id`
- `mp_afiliados.aseg_afiliados_id`
- `mp_prescripciones.aseg_afiliados_id`
- `mp_recobrantes.aseg_afiliado_id`
- `mp_recobros_adres.aseg_afiliados_id`
- `mpc_prescripciones.aseg_afiliados_id`
- `mpc_prescripciones_historicos.aseg_afiliados_id`
- `pe_afiliados_programas.aseg_afiliados_id`
- `pe_afiliados_sugeridos.aseg_afiliados_id`
- `pe_direccionados.aseg_afiliados_id`
- `pe_programas_traslados.aseg_afiliados_id`
- `pe_telefonos.aseg_afiliados_id`
- `ref_anexos9.aseg_afiliados_id`


### `cnt_contratos` (32 columnas)

| Columna | Tipo | Nulos | Llave |
|---|---|---|---|
| `id` | int | NO | PRI |
| `gn_empresas_id` | int | YES | MUL |
| `cnt_prestadores_id` | int | NO | MUL |
| `negociacion` | varchar(32) | YES | nan |
| `contrato` | varchar(32) | NO | nan |
| `descripcion` | varchar(1024) | YES | nan |
| `activo` | bit(1) | NO | nan |
| `mae_estado_contrato_id` | int | NO | nan |
| `mae_estado_contrato_codigo` | varchar(8) | YES | nan |
| `mae_estado_contrato_valor` | varchar(128) | YES | nan |
| `fecha_inicio` | date | NO | nan |
| `fecha_fin` | date | NO | nan |
| `valor` | decimal(14,2) | NO | nan |
| `valor_mes` | decimal(14,2) | YES | nan |
| `valor_presupuesto_total` | decimal(14,2) | YES | nan |
| `dias_limite_pago` | int | YES | nan |
| `num_afiliados` | int | YES | nan |
| `mae_regimen_id` | int | YES | nan |
| `mae_regimen_codigo` | varchar(8) | YES | nan |
| `mae_regimen_valor` | varchar(128) | YES | nan |
| `autoriza_gestion` | bit(1) | NO | nan |
| `ejecucion_contrato_autorizado` | decimal(14,2) | YES | nan |
| `ejecucion_contrato_prestado` | decimal(14,2) | YES | nan |
| `ejecucion_total_contrato` | decimal(14,2) | YES | nan |
| `impuesto_timbre` | bit(1) | NO | nan |
| `compra_directa` | bit(1) | YES | nan |
| `usuario_crea` | varchar(128) | NO | nan |
| `terminal_crea` | varchar(16) | NO | nan |
| `fecha_hora_crea` | datetime | NO | nan |
| `usuario_modifica` | varchar(128) | YES | nan |
| `terminal_modifica` | varchar(16) | YES | nan |
| `fecha_hora_modifica` | datetime | YES | nan |

**Relaciones FK:**
**Referencia hacia:**
- `cnt_prestadores_id` → `cnt_prestadores.id`
- `gn_empresas_id` → `gn_empresas.id`

**Es referenciada por:**
- `au_anexos4.cnt_contratos_id`
- `auc_hospitalizacion_servicios.cnt_contratos_id`
- `cm_auditoria_capita_descuentos.cnt_contratos_id`
- `cm_fe_rips_cargas.cnt_contratos_id`
- `cm_rips_cargas.cnt_contratos_id`
- `cnt_contrato_adjuntos.cnt_contratos_id`
- `cnt_contrato_coberturas.cnt_contratos_id`
- `cnt_contrato_descuentos.cnt_contratos_id`
- `cnt_contrato_detalles.cnt_contratos_id`
- `cnt_contrato_giros_capita.cnt_contratos_id`
- `cnt_contrato_historico_prestaciones.cnt_contratos_id`
- `cnt_contrato_historico_validaciones.cnt_contratos_id`
- `cnt_contrato_historicos.cnt_contratos_id`
- `cnt_contrato_juridicos.cnt_contratos_id`
- `cnt_contrato_notas_tecnicas.cnt_contratos_id`
- `cnt_contrato_sedes.cnt_contratos_id`


### `cnt_prestadores` (30 columnas)

| Columna | Tipo | Nulos | Llave |
|---|---|---|---|
| `union_temporal` | bit(1) | YES | nan |
| `grupo_rips_ministerio` | int | YES | nan |
| `id` | int | NO | PRI |
| `codigo_min_salud` | varchar(16) | YES | nan |
| `activo` | bit(1) | NO | nan |
| `mae_tipo_documento_id` | int | NO | nan |
| `mae_tipo_documento_codigo` | varchar(8) | NO | nan |
| `mae_tipo_documento_valor` | varchar(128) | NO | nan |
| `numero_documento` | varchar(32) | YES | nan |
| `digito_verificacion` | varchar(8) | YES | nan |
| `razon_social` | varchar(256) | YES | MUL |
| `naturaleza_juridica` | varchar(16) | NO | nan |
| `prefijo` | varchar(8) | YES | nan |
| `facturacion_electronica` | tinyint(1) | YES | nan |
| `mae_clase_prestador_id` | int | NO | nan |
| `mae_clase_prestador_codigo` | varchar(8) | NO | nan |
| `mae_clase_prestador_valor` | varchar(128) | NO | nan |
| `categoria_prestador` | int | NO | nan |
| `nivel_atencion` | int | NO | nan |
| `mae_tipo_documento_rep_id` | int | NO | nan |
| `mae_tipo_documento_rep_codigo` | varchar(8) | NO | nan |
| `mae_tipo_documento_rep_valor` | varchar(128) | NO | nan |
| `numero_documento_rep` | varchar(32) | YES | nan |
| `nombre_representante_legal` | varchar(256) | YES | nan |
| `usuario_crea` | varchar(64) | NO | nan |
| `fecha_hora_crea` | datetime | NO | nan |
| `terminal_crea` | varchar(64) | NO | nan |
| `usuario_modifica` | varchar(64) | YES | nan |
| `fecha_hora_modifica` | datetime | YES | nan |
| `terminal_modifica` | varchar(64) | YES | nan |

**Relaciones FK:**

**Es referenciada por:**
- `ant_anticipos.cnt_prestadores_id`
- `au_anexo2_rescates.cnt_prestadores_origen_id`
- `au_anexo2_rescates.cnt_prestadores_destino_id`
- `au_grupo_sedes.cnt_prestadores_id`
- `au_no_solicitudes.cnt_prestador_id`
- `auc_auditores.cnt_prestadores_id`
- `auc_cargas.cnt_prestadores_id`
- `auc_hospitalizaciones.cnt_prestadores_id`
- `car_cargas.cnt_prestadores_id`
- `car_proceso_prestadores.cnt_prestadores_id`
- `cm_auditoria_masiva.cnt_prestadores_id`
- `cm_conciliaciones.cnt_prestadores_id`
- `cm_devolucion_masiva.cnt_prestadores_id`
- `cm_facturas.cnt_prestadores_id`
- `cm_glosa_masiva.cnt_prestadores_id`
- `cm_grupo_prestadores.cnt_prestadores_id`
- `cm_pagos.cnt_prestadores_id`
- `cnt_contrato_historico_prestaciones.cnt_prestadores_id`
- `cnt_contrato_historico_validaciones.cnt_prestadores_id`
- `cnt_contratos.cnt_prestadores_id`
- `cnt_prestador_contactos.cnt_prestadores_id`
- `cnt_prestador_sedes.cnt_prestadores_id`
- `cnt_prestador_union_temporal.cnt_prestadores_id`
- `cnt_prestador_union_temporal.cnt_prestador_union_temporal_id`
- `cnt_profesional_prestadores.cnt_prestadores_id`
- `cntj_terceros.cnt_prestadores_id`
- `fin_postulaciones.cnt_prestadores_id`
- `gj_terceros.cnt_prestadores_id`
- `gn_empresas.cnt_prestadores_id`
- `mp_prestadores.cnt_prestadores_id`
- `pe_direccionados.cnt_prestadores_id`
- `rco_facturas.cnt_prestadores_id`
- `rco_grupo_prestadores.cnt_prestador_id`


### `cnt_prestador_sedes` (34 columnas)

| Columna | Tipo | Nulos | Llave |
|---|---|---|---|
| `id` | int | NO | PRI |
| `cnt_prestadores_id` | int | NO | MUL |
| `codigo_prestador` | varchar(16) | NO | nan |
| `ubicacion_id` | int | NO | nan |
| `mae_region_id` | int | YES | nan |
| `mae_region_codigo` | varchar(8) | YES | nan |
| `mae_region_valor` | varchar(128) | YES | nan |
| `direccion` | varchar(256) | YES | nan |
| `direccion_georreferenciada` | bit(1) | NO | nan |
| `direccion_georef_latitud` | decimal(12,9) | YES | nan |
| `direccion_georef_longitud` | decimal(12,9) | YES | nan |
| `nombre` | varchar(256) | YES | MUL |
| `codigo` | varchar(16) | YES | nan |
| `codigo_habilitacion` | varchar(16) | YES | MUL |
| `zona_precedencia` | varchar(1) | NO | nan |
| `estado_sede` | bit(1) | YES | nan |
| `nivel_atencion` | int | YES | nan |
| `mae_clase_prestador_id` | int | YES | nan |
| `mae_clase_prestador_codigo` | varchar(8) | YES | nan |
| `mae_clase_prestador_valor` | varchar(128) | YES | nan |
| `fax` | varchar(32) | YES | nan |
| `telefono_citas` | varchar(64) | YES | nan |
| `correo_electronico` | varchar(64) | YES | nan |
| `telefono_administrativo` | varchar(64) | YES | nan |
| `capitacion` | bit(1) | YES | nan |
| `interoperabilidad` | bit(1) | NO | nan |
| `fecha_factura_electronica` | date | YES | nan |
| `grupo_rips_ministerio` | int | YES | nan |
| `usuario_crea` | varchar(64) | NO | nan |
| `fecha_hora_crea` | datetime | NO | nan |
| `terminal_crea` | varchar(64) | NO | nan |
| `usuario_modifica` | varchar(64) | YES | nan |
| `fecha_hora_modifica` | datetime | YES | nan |
| `terminal_modifica` | varchar(64) | YES | nan |

**Relaciones FK:**
**Referencia hacia:**
- `cnt_prestadores_id` → `cnt_prestadores.id`

**Es referenciada por:**
- `ant_anticipos.cnt_prestador_sedes_id`
- `aseg_afiliados.primaria_cnt_prestador_sedes_id`
- `aseg_afiliados.portabilidad_cnt_prestador_sedes_id`
- `aseg_afiliados.odontologia_cnt_prestador_sedes_id`
- `aseg_portabilidades.cnt_prestador_sedes_id`
- `au_anexo2_rescate_sedes.cnt_prestador_sede_origen_id`
- `au_anexo2_rescate_sedes.cnt_prestador_sede_capita_id`
- `au_anexo2_rescates.cnt_prestador_sedes_origen_id`
- `au_anexo2_rescates.cnt_prestador_sedes_destino_id`
- `au_anexo3_cargas.cnt_prestador_sedes_id`
- `au_anexos2.cnt_prestador_sedes_id`
- `au_anexos3.cnt_prestador_sedes_id`
- `au_anexos4.cnt_prestador_sedes_id`
- `au_cotizaciones.cnt_prestador_sedes_id`
- `au_grupo_sedes.cnt_prestador_sedes_id`
- `au_no_solicitud_cargas.cnt_prestador_sedes_id`
- `au_seguimiento_prestador_asignados.cnt_prestador_sedes_id`
- `au_seguimientos.cnt_prestador_sede_asignado_id`
- `auc_auditores.cnt_prestador_sedes_id`
- `auc_carga_cierres.cnt_prestador_sedes_id`
- `auc_cargas.cnt_prestador_sedes_id`
- `auc_hospitalizaciones.cnt_prestador_sedes_id`
- `aus_caso_servicios.cnt_prestador_sede_prescriptora_id`
- `aus_caso_servicios.cnt_prestador_sede_destino_id`
- `cm_fe_rips_cargas.cnt_prestador_sedes_id`
- `cm_rips_cargas.gn_prestador_sedes_id`
- `cnt_contrato_coberturas.cnt_prestador_sedes_id`
- `cnt_contrato_detalles.cnt_prestador_sedes_interdependencia_id`
- `cnt_contrato_historico_prestaciones.cnt_prestador_sedes_id`
- `cnt_contrato_historico_validaciones.cnt_prestador_sedes_id`
- `cnt_contrato_sedes.cnt_prestador_sedes_id`
- `cnt_prestador_contactos.cnt_prestador_sedes_id`
- `cnt_prestador_sede_capacidades.cnt_prestador_sedes_id`
- `cnt_prestador_sede_servicios_habilitacion.cnt_prestador_sedes_id`
- `mpc_prescripciones.cnt_prescriptor_prestador_sedes_id`
- `mpc_prescripciones.cnt_direccionado_prestador_sedes_id`
- `mpc_prescripciones_historicos.cnt_direccionado_prestador_sedes_id`
- `mpc_prescripciones_historicos.cnt_prescriptor_prestador_sedes_id`
- `pe_afiliados_programas.cnt_prestador_sedes_id`
- `pe_carga_historicos.cnt_prestador_sedes_id`
- `pe_cargas_variables.cnt_prestador_sedes_id`
- `pe_direccionados.cnt_prestador_sedes_id`
- `pe_ips_programas.cnt_prestador_sedes_id`
- `rco_conciliaciones.cnt_presadores_sedes_id`
- `rco_factura_detalles.cnt_prestadores_sedes_id`
- `ref_anexo9_gestiones.cnt_prestador_sedes_id`
- `ref_anexos9.cnt_ips_destino_id`
- `ref_anexos9.cnt_prestador_sedes_id`
- `ref_anexos9.cnt_prestador_sedes_ubicacion_id`
- `ref_transportes.cnt_prestador_sedes_id`
- `tu_tutela_items.destino_cnt_prestador_sede_id`
- `tu_tutela_items.prescripcion_cnt_prestador_sede_id`

---

## 4. Todas las Relaciones entre Tablas cm_

| Tabla Origen | Columna FK | Tabla Destino | Columna Ref |
|---|---|---|---|
| `cm_auditoria_adjuntos` | `cm_facturas_id` | `cm_facturas` | `id` |
| `cm_auditoria_adjuntos` | `cm_detalles_id` | `cm_detalles` | `id` |
| `cm_auditoria_autorizaciones` | `au_anexos4_id` | `au_anexos4` | `id` |
| `cm_auditoria_autorizaciones` | `cm_detalles_id` | `cm_detalles` | `id` |
| `cm_auditoria_autorizaciones` | `cm_facturas_id` | `cm_facturas` | `id` |
| `cm_auditoria_capita_descuentos` | `cm_detalles_id` | `cm_detalles` | `id` |
| `cm_auditoria_capita_descuentos` | `cnt_contratos_id` | `cnt_contratos` | `id` |
| `cm_auditoria_cierres` | `cm_auditoria_masiva_id` | `cm_auditoria_masiva` | `id` |
| `cm_auditoria_cierres` | `cm_facturas_id` | `cm_facturas` | `id` |
| `cm_auditoria_conceptos_contables` | `cm_detalles_id` | `cm_detalles` | `id` |
| `cm_auditoria_devoluciones` | `cm_devolucion_masiva_id` | `cm_devolucion_masiva` | `id` |
| `cm_auditoria_devoluciones` | `cm_facturas_id` | `cm_facturas` | `id` |
| `cm_auditoria_diagnosticos` | `cm_detalles_id` | `cm_detalles` | `id` |
| `cm_auditoria_masiva` | `cnt_prestadores_id` | `cnt_prestadores` | `id` |
| `cm_auditoria_motivos_glosas` | `cm_detalles_id` | `cm_detalles` | `id` |
| `cm_conciliaciones` | `cnt_prestadores_id` | `cnt_prestadores` | `id` |
| `cm_detalles` | `aseg_afiliados_id` | `aseg_afiliados` | `id` |
| `cm_detalles` | `cm_facturas_id` | `cm_facturas` | `id` |
| `cm_devolucion_masiva` | `cnt_prestadores_id` | `cnt_prestadores` | `id` |
| `cm_factura_estados` | `cm_facturas_id` | `cm_facturas` | `id` |
| `cm_factura_transacciones` | `cm_facturas_id` | `cm_facturas` | `id` |
| `cm_facturas` | `gn_usuarios_gestiona_id` | `gn_usuarios` | `id` |
| `cm_facturas` | `gn_usuarios_medico_id` | `gn_usuarios` | `id` |
| `cm_facturas` | `gn_usuarios_lider_id` | `gn_usuarios` | `id` |
| `cm_facturas` | `gn_empresas_id` | `gn_empresas` | `id` |
| `cm_facturas` | `gn_usuarios_tecnico_id` | `gn_usuarios` | `id` |
| `cm_facturas` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_facturas` | `cm_grupos_id` | `cm_grupos` | `id` |
| `cm_facturas` | `cnt_prestadores_id` | `cnt_prestadores` | `id` |
| `cm_facturas` | `cm_fe_rips_cargas_id` | `cm_fe_rips_cargas` | `id` |
| `cm_fe_notas` | `cm_fe_rips_facturas_id` | `cm_fe_rips_facturas` | `id` |
| `cm_fe_notas` | `cm_facturas_id` | `cm_facturas` | `id` |
| `cm_fe_rips_carga_adjuntos` | `cm_fe_rips_cargas_id` | `cm_fe_rips_cargas` | `id` |
| `cm_fe_rips_carga_contenidos` | `cm_fe_rips_cargas_id` | `cm_fe_rips_cargas` | `id` |
| `cm_fe_rips_cargas` | `carga_periodo_id` | `cm_fe_rips_cargas` | `id` |
| `cm_fe_rips_cargas` | `cnt_contratos_id` | `cnt_contratos` | `id` |
| `cm_fe_rips_cargas` | `cnt_prestador_sedes_id` | `cnt_prestador_sedes` | `id` |
| `cm_fe_rips_cargas` | `gn_empresas_id` | `gn_empresas` | `id` |
| `cm_fe_rips_cargas` | `radicador_asignado` | `gn_usuarios` | `id` |
| `cm_fe_rips_facturas` | `cm_facturas_id` | `cm_facturas` | `id` |
| `cm_fe_rips_facturas` | `cm_fe_rips_cargas_id` | `cm_fe_rips_cargas` | `id` |
| `cm_fe_rips_validaciones_historicos` | `cm_fe_rips_validaciones_id` | `cm_fe_rips_validaciones` | `id` |
| `cm_fe_soportes` | `cm_facturas_id` | `cm_facturas` | `id` |
| `cm_fe_soportes` | `cm_fe_rips_cargas_id` | `cm_fe_rips_cargas` | `id` |
| `cm_fe_soportes` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_fe_soportes` | `gn_empresas_id` | `gn_empresas` | `id` |
| `cm_fe_transacciones` | `cm_fe_rips_cargas_id` | `cm_fe_rips_cargas` | `id` |
| `cm_gestion_usuarios` | `cm_detalles_id` | `cm_detalles` | `id` |
| `cm_glosa_masiva` | `cnt_prestadores_id` | `cnt_prestadores` | `id` |
| `cm_glosa_respuesta_detalles` | `cm_detalles_id` | `cm_detalles` | `id` |
| `cm_glosa_respuesta_detalles` | `cm_glosa_respuestas_id` | `cm_glosa_respuestas` | `id` |
| `cm_glosa_respuestas` | `cm_glosa_masiva_id` | `cm_glosa_masiva` | `id` |
| `cm_glosa_respuestas` | `cm_conciliaciones_id` | `cm_conciliaciones` | `id` |
| `cm_glosa_respuestas` | `cm_facturas_id` | `cm_facturas` | `id` |
| `cm_grupo_historicos` | `cm_grupos_id` | `cm_grupos` | `id` |
| `cm_grupo_prestadores` | `cm_grupos_id` | `cm_grupos` | `id` |
| `cm_grupo_prestadores` | `cnt_prestadores_id` | `cnt_prestadores` | `id` |
| `cm_grupo_usuarios` | `gn_usuarios_id` | `gn_usuarios` | `id` |
| `cm_grupo_usuarios` | `cm_grupos_id` | `cm_grupos` | `id` |
| `cm_historico_facturas` | `cm_facturas_id` | `cm_facturas` | `id` |
| `cm_marcacion_ips_masiva` | `gn_empresas_id` | `gn_empresas` | `id` |
| `cm_pago_factura_retenciones` | `cm_pago_facturas_id` | `cm_pago_facturas` | `id` |
| `cm_pago_facturas` | `cm_facturas_id` | `cm_facturas` | `id` |
| `cm_pago_facturas` | `cm_pagos_id` | `cm_pagos` | `id` |
| `cm_pago_facturas` | `cm_pago_transacciones_id` | `cm_pago_transacciones` | `id` |
| `cm_pago_transacciones` | `cm_pagos_id` | `cm_pagos` | `id` |
| `cm_pagos` | `cnt_prestadores_id` | `cnt_prestadores` | `id` |
| `cm_radicados` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_radicados` | `cm_glosa_respuestas_conciliacion_id` | `cm_glosa_respuestas` | `id` |
| `cm_radicados` | `cm_glosa_respuestas_id` | `cm_glosa_respuestas` | `id` |
| `cm_radicados` | `cm_devolucion_masiva_id` | `cm_devolucion_masiva` | `id` |
| `cm_radicados` | `cm_fe_rips_cargas_id` | `cm_fe_rips_cargas` | `id` |
| `cm_radicados` | `cm_auditoria_masiva_id` | `cm_auditoria_masiva` | `id` |
| `cm_radicados` | `cm_auditoria_devoluciones_id` | `cm_auditoria_devoluciones` | `id` |
| `cm_radicados` | `cm_auditoria_cierres_id` | `cm_auditoria_cierres` | `id` |
| `cm_radicados` | `cm_conciliaciones_id` | `cm_conciliaciones` | `id` |
| `cm_rips_ac_consultas` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_ad_servicios_agrupados` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_af_facturas` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_af_facturas_temp` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_ah_hospitalizaciones` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_am_medicamentos` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_an_recien_nacidos` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_ap_procedimientos` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_at_otros_servicios` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_au_urgencias` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_carga_ac_consultas` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_carga_ad_servicios_agrupados` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_carga_af_facturas` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_carga_ah_hospitalizaciones` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_carga_am_medicamentos` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_carga_an_recien_nacidos` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_carga_anexos` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_carga_ap_procedimientos` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_carga_at_otros_servicios` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_carga_au_urgencias` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_carga_ct_control` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_carga_estados` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_carga_us_usuarios` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_cargas` | `gn_empresas_id` | `gn_empresas` | `id` |
| `cm_rips_cargas` | `gn_prestador_sedes_id` | `cnt_prestador_sedes` | `id` |
| `cm_rips_cargas` | `cnt_contratos_id` | `cnt_contratos` | `id` |
| `cm_rips_ct_control` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_estructura_errores` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_regla_entradas` | `cm_rips_reglas_id` | `cm_rips_reglas` | `id` |
| `cm_rips_regla_salidas` | `cm_rips_reglas_id` | `cm_rips_reglas` | `id` |
| `cm_rips_sucesos` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_rips_us_usuarios` | `cm_rips_cargas_id` | `cm_rips_cargas` | `id` |
| `cm_sincronizacion_detalles` | `cm_sincronizacion_encabezados_id` | `cm_sincronizacion_encabezados` | `id` |
| `cm_sincronizacion_encabezados` | `cm_radicados_id` | `cm_radicados` | `id` |
| `cm_sincronizacion_paquetes` | `cm_sincronizaciones_id` | `cm_sincronizaciones` | `id` |
| `cm_sincronizaciones` | `cm_glosa_respuestas_id` | `cm_glosa_respuestas` | `id` |
| `cm_sincronizaciones` | `cm_auditoria_cierres_id` | `cm_auditoria_cierres` | `id` |
| `cm_sincronizaciones` | `cm_conciliaciones_id` | `cm_conciliaciones` | `id` |
| `cm_sincronizaciones` | `cm_radicados_id` | `cm_radicados` | `id` |

---

## 5. Columnas Candidatas para Variable TARGET

Las siguientes columnas en tablas `cm_` son candidatas para determinar
el estado final de la factura (Auditada=0 / Glosada=1 / Devuelta=2):

| Tabla | Columna | Tipo |
|---|---|---|
| `cm_auditoria_autorizaciones` | `nombre_prestador` | varchar(264) |
| `cm_auditoria_masiva` | `cnt_prestadores_id` | int |
| `cm_auditoria_masiva` | `estado_proceso` | int |
| `cm_conciliaciones` | `cnt_prestadores_id` | int |
| `cm_conciliaciones` | `estado_proceso` | int |
| `cm_detalles` | `estado` | int |
| `cm_devolucion_masiva` | `cnt_prestadores_id` | int |
| `cm_devolucion_masiva` | `estado_proceso` | int |
| `cm_factura_estados` | `estado_factura` | int |
| `cm_factura_transacciones` | `estado` | int |
| `cm_facturas` | `cnt_prestadores_id` | int |
| `cm_facturas` | `estado_factura` | int |
| `cm_facturas` | `estado_glosa_aut` | tinyint |
| `cm_fe_mercurio_sincronizaciones` | `estado` | tinyint |
| `cm_fe_rips_cargas` | `cnt_prestador_sedes_id` | int |
| `cm_fe_rips_cargas` | `estado` | int |
| `cm_fe_rips_cargas` | `documento_prestador` | varchar(32) |
| `cm_fe_rips_validaciones` | `estado` | bit(1) |
| `cm_fe_rips_validaciones_historicos` | `estado` | bit(1) |
| `cm_fe_transacciones` | `estado` | int |
| `cm_gestion_usuarios` | `estado` | int |
| `cm_glosa_masiva` | `cnt_prestadores_id` | int |
| `cm_glosa_masiva` | `estado_proceso` | int |
| `cm_glosa_respuestas` | `estado_sincronizacion` | int |
| `cm_grupo_prestadores` | `cnt_prestadores_id` | int |
| `cm_informes` | `estado` | int |
| `cm_marcacion_ips_masiva` | `estado` | int |
| `cm_pago_facturas` | `cm_factura_estado` | int |
| `cm_pagos` | `cnt_prestadores_id` | int |
| `cm_radicados` | `estado` | tinyint |
| `cm_radicados` | `estado_radicado` | tinyint(1) |
| `cm_rips_ah_hospitalizaciones` | `mae_estado_salida_codigo` | varchar(8) |
| `cm_rips_ah_hospitalizaciones` | `mae_estado_salida_id` | int |
| `cm_rips_ah_hospitalizaciones` | `mae_estado_salida_valor` | varchar(128) |
| `cm_rips_au_urgencias` | `mae_estado_salida_codigo` | varchar(8) |
| `cm_rips_au_urgencias` | `mae_estado_salida_id` | int |
| `cm_rips_au_urgencias` | `mae_estado_salida_valor` | varchar(128) |
| `cm_rips_carga_ah_hospitalizaciones` | `mae_estado_salida_codigo` | varchar(8) |
| `cm_rips_carga_ah_hospitalizaciones` | `mae_estado_salida_id` | int |
| `cm_rips_carga_ah_hospitalizaciones` | `mae_estado_salida_valor` | varchar(128) |
| `cm_rips_carga_au_urgencias` | `mae_estado_salida_codigo` | varchar(8) |
| `cm_rips_carga_au_urgencias` | `mae_estado_salida_id` | int |
| `cm_rips_carga_au_urgencias` | `mae_estado_salida_valor` | varchar(128) |
| `cm_rips_carga_estados` | `estado` | int |
| `cm_rips_cargas` | `gn_prestador_sedes_id` | int |
| `cm_rips_cargas` | `estado` | int |
| `cm_sincronizacion_encabezados` | `estado` | int |
| `cm_sincronizacion_paquetes` | `estado_transacion` | int |
| `cm_sincronizaciones` | `estado_transacion` | int |
| `cm_auditoria_cierres` | `valor_glosado` | decimal(16,2) |
| `cm_auditoria_masiva` | `valor_glosado` | decimal(16,2) |
| `cm_auditoria_motivos_glosas` | `mae_motivo_glosa_aplicacion_id` | int |
| `cm_auditoria_motivos_glosas` | `mae_motivo_glosa_aplicacion_codigo` | varchar(8) |
| `cm_auditoria_motivos_glosas` | `mae_motivo_glosa_aplicacion_valor` | varchar(128) |
| `cm_auditoria_motivos_glosas` | `mae_motivo_glosa_aplicacion_descripcion` | varchar(512) |
| `cm_detalles` | `radicado_glosa` | int |
| `cm_detalles` | `aplica_glosa` | bit(1) |
| `cm_detalles` | `valor_glosa` | decimal(20,4) |
| `cm_detalles` | `motivo_glosa` | varchar(1024) |
| `cm_detalles` | `mae_motivo_respuesta_glosa_especifico_id` | int |
| `cm_detalles` | `mae_motivo_respuesta_glosa_especifico_codigo` | varchar(8) |
| `cm_detalles` | `mae_motivo_respuesta_glosa_especifico_valor` | varchar(128) |
| `cm_detalles` | `mae_motivo_respuesta_glosa_aplicacion_id` | int |
| `cm_detalles` | `mae_motivo_respuesta_glosa_aplicacion_codigo` | varchar(8) |
| `cm_detalles` | `mae_motivo_respuesta_glosa_aplicacion_valor` | varchar(128) |
| `cm_facturas` | `valor_inicial_glosa` | decimal(20,4) |
| `cm_facturas` | `ejecucion_glosa_aut_bot` | varchar(16) |
| `cm_facturas` | `ejecucion_glosa_aut_ia` | varchar(16) |
| `cm_facturas` | `estado_glosa_aut` | tinyint |
| `cm_glosa_masiva` | `cantidad_facturas_con_respuesta_glosa` | int |
| `cm_glosa_masiva` | `cantidad_facturas_con_ratificacion_glosa` | int |
| `cm_glosa_respuesta_detalles` | `cm_glosa_respuestas_id` | int |
| `cm_glosa_respuesta_detalles` | `mae_motivo_respuesta_glosa_especifico_id` | int |
| `cm_glosa_respuesta_detalles` | `mae_motivo_respuesta_glosa_especifico_codigo` | varchar(8) |
| `cm_glosa_respuesta_detalles` | `mae_motivo_respuesta_glosa_especifico_valor` | varchar(128) |
| `cm_glosa_respuesta_detalles` | `mae_motivo_respuesta_glosa_aplicacion_id` | int |
| `cm_glosa_respuesta_detalles` | `mae_motivo_respuesta_glosa_aplicacion_codigo` | varchar(8) |
| `cm_glosa_respuesta_detalles` | `mae_motivo_respuesta_glosa_aplicacion_valor` | varchar(128) |
| `cm_glosa_respuestas` | `cm_glosa_masiva_id` | int |
| `cm_radicados` | `cm_glosa_respuestas_id` | int |
| `cm_radicados` | `cm_glosa_respuestas_conciliacion_id` | int |
| `cm_radicados` | `cm_glosa_masiva_id` | int |
| `cm_sincronizacion_encabezados` | `valor_glosado` | decimal(20,4) |
| `cm_sincronizaciones` | `cm_glosa_respuestas_id` | int |
| `cm_auditoria_devoluciones` | `cm_devolucion_masiva_id` | int |
| `cm_auditoria_devoluciones` | `mae_motivo_devolucion_id` | int |
| `cm_auditoria_devoluciones` | `mae_motivo_devolucion_codigo` | varchar(8) |
| `cm_auditoria_devoluciones` | `mae_motivo_devolucion_valor` | varchar(128) |
| `cm_auditoria_devoluciones` | `fecha_devolucion` | datetime |
| `cm_auditoria_devoluciones` | `mae_devolucion_motivo_general_id` | int |
| `cm_auditoria_devoluciones` | `mae_devolucion_motivo_general_codigo` | varchar(8) |
| `cm_auditoria_devoluciones` | `mae_devolucion_motivo_general_valor` | varchar(128) |
| `cm_auditoria_devoluciones` | `mae_devolucion_motivo_general_descripcion` | varchar(512) |
| `cm_fe_rips_cargas` | `devolucion` | bit(1) |
| `cm_fe_rips_cargas` | `fecha_hora_devolucion` | datetime |
| `cm_fe_rips_cargas` | `mae_devolucion_id` | int |
| `cm_fe_rips_cargas` | `mae_devolucion_codigo` | varchar(8) |
| `cm_fe_rips_cargas` | `mae_devolucion_valor` | varchar(128) |
| `cm_fe_rips_cargas` | `observacion_devolucion` | varchar(512) |
| `cm_radicados` | `cm_auditoria_devoluciones_id` | int |
| `cm_radicados` | `cm_devolucion_masiva_id` | int |
| `cm_auditoria_devoluciones` | `cm_devolucion_masiva_id` | int |
| `cm_auditoria_devoluciones` | `mae_motivo_devolucion_id` | int |
| `cm_auditoria_devoluciones` | `mae_motivo_devolucion_codigo` | varchar(8) |
| `cm_auditoria_devoluciones` | `mae_motivo_devolucion_valor` | varchar(128) |
| `cm_auditoria_devoluciones` | `fecha_devolucion` | datetime |
| `cm_auditoria_devoluciones` | `mae_devolucion_motivo_general_id` | int |
| `cm_auditoria_devoluciones` | `mae_devolucion_motivo_general_codigo` | varchar(8) |
| `cm_auditoria_devoluciones` | `mae_devolucion_motivo_general_valor` | varchar(128) |
| `cm_auditoria_devoluciones` | `mae_devolucion_motivo_general_descripcion` | varchar(512) |
| `cm_fe_rips_cargas` | `devolucion` | bit(1) |
| `cm_fe_rips_cargas` | `fecha_hora_devolucion` | datetime |
| `cm_fe_rips_cargas` | `mae_devolucion_id` | int |
| `cm_fe_rips_cargas` | `mae_devolucion_codigo` | varchar(8) |
| `cm_fe_rips_cargas` | `mae_devolucion_valor` | varchar(128) |
| `cm_fe_rips_cargas` | `observacion_devolucion` | varchar(512) |
| `cm_radicados` | `cm_auditoria_devoluciones_id` | int |
| `cm_radicados` | `cm_devolucion_masiva_id` | int |

---

## 6. Propuesta de Features para el Modelo Predictivo

### 6.1 Features de Pertinencia Clínica (desde cm_detalles + RIPS)
| Feature | Fuente | Tipo | Justificación |
|---|---|---|---|
| `codigo_dx` / CIE-10 | cm_detalles | categorical | Diagnóstico principal |
| `ma_servicio_id` / CUPS | cm_detalles | categorical | Procedimiento facturado |
| `dx_sexo_inconsistente` | cm_detalles + aseg_afiliados | bool | VAL-004 Res.2284 |
| `num_dx_secundarios` | cm_rips_* | int | Complejidad del caso |
| `nivel_complejidad_cups` | ma_servicios_habilitacion | int | Nivel requerido |
| `nivel_habilitacion_ips` | cnt_prestador_sedes | int | Nivel real de la IPS |
| `complejidad_mismatch` | derivada | bool | CUPS vs nivel IPS (VAL-003) |
| `tiene_anestesiologia` | cm_detalles | bool | Cirugía sin anestesiólogo (VAL-005) |
| `cups_autorizado_contrato` | cnt_contrato_detalles | bool | Servicio cubierto (VAL-003) |

### 6.2 Features de Comportamiento del Prestador
| Feature | Fuente | Tipo | Justificación |
|---|---|---|---|
| `tasa_glosa_historica_nit` | cm_facturas (12m) | float | Historial del prestador |
| `tasa_devolucion_historica_nit` | cm_facturas (12m) | float | Historial devoluciones |
| `valor_promedio_factura_nit` | cm_facturas | float | Patrón de facturación |
| `dias_promedio_radicacion_nit` | cm_facturas | float | Puntualidad del prestador |
| `concentracion_cups_prestador` | cm_detalles | float | HHI de CUPS facturados |
| `trimestre_facturacion` | cm_facturas | int | Estacionalidad |

### 6.3 Features Financieras y Administrativas
| Feature | Fuente | Tipo | Justificación |
|---|---|---|---|
| `valor_total_factura` | cm_facturas | float | Magnitud económica |
| `num_items_factura` | cm_detalles | int | Complejidad de la factura |
| `modalidad_pago_encoded` | cm_facturas / cnt_contratos | int | Evento=0, Capita=1, Paquete=2 |
| `dias_hasta_radicacion` | cm_facturas | int | VAL-002: extemporaneidad |
| `discrepancia_fiscal_abs` | cm_facturas + cm_fe_rips_cargas | float | VAL-001: JSON vs XML |
| `porcentaje_mayor_item` | cm_detalles | float | Concentración de valor |

---

*Documento generado automáticamente desde metadata BD — 2026-03-04*