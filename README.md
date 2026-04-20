# Analítica Geoespacial Predictiva — Savia Salud EPS

> Un sistema de inteligencia artificial y visualización geográfica para proyectar, analizar y mitigar el riesgo de glosas médicas basado en la distribución territorial de los afiliados y la red de IPS.

![Estado](https://img.shields.io/badge/Estado-En_Desarrollo-orange)
![Pipeline](https://img.shields.io/badge/Pipeline-XGBoost_Multiclase-blue)
![Frontend](https://img.shields.io/badge/Dashboard-Vanilla_JS_Leaflet-success)

---

## 🎥 Demostración del Dashboard en Vivo

El sistema incluye un **Dashboard Ejecutivo** interactivo basado en los datos del set de entrenamiento y validación georreferenciados en Antioquia.

![Demostración interactiva de los mapas y predicciones](assets/savia_demo_dashboard.webp)

---

## 🎯 Objetivo del Proyecto

Transformar el proceso de auditoría prestacional de Savia Salud EPS de un modelo **reactivo** a uno **predictivo local-consciente**:
* Identificar con meses de anticipación qué facturas tienen mayor riesgo de ser Glosadas o Devueltas.
* Visualizar en mapas de calor las zonas rojas del departamento (municipios rurales con altas tasas atípicas).
* Optimizar el recurso de auditoría enfocando los esfuerzos en las IPS y perfiles demográficos marcados por el modelo de IA.

---

## 🏛️ Arquitectura del Sistema

El proyecto consta de tres componentes principales:

1. **Ingeniería de Features Espaciales:** (`src/data/geo_features.py`)
   Extracción de KPIs espaciales cruzando locación de afiliados con la red de sedes IPS.
2. **Motor de Deep ML:** (`Nootebook/01_geo_features_modelo.ipynb`)
   Modelo *XGBoost Multiclase (Auditada / Glosada / Devuelta)* entrenado sobre un bloque temporal estricto para evitar *Data Leakage*.
3. **Visor Estratégico:** (`dashboard/`)
   Dashboard de inteligencia de negocios de estilo premium (*Diseño inspirado en el panel analítico ARL*), construido con mapas dinámicos Leaflet y JS puro (cero dependencias build).

### Hallazgos Clave Actuales (Feature Importance SHAP)
* 🔴 La **Tasa histórica de glosa del municipio** es 5 veces más predictiva que características sociales abstractas.
* 🏥 La **Densidad de IPS** del municipio de residencia impulsa anomalías de sobrefacturación competitiva.
* 📍 La **Distancia Afiliado → IPS** evidencia fricciones donde pacientes en cola larga geográfica llegan a consultas especializadas sin historiales continuos disponibles.

---

## 🚀 Estado Actual y Pipeline (Abril 2026)

### Fase 1: Data Engineering & Geo-Features (Completada ✅)
* Dataset unificado y enriquecido espacialmente.
* Features calculadas: distancias haversine, concentraciones HHI diagnósticas, tasas relativas.

### Fase 2: Baseline Model (En Iteración ⚠️)
* AUC-ROC Validado: **0.662**
* Problema detectado: *Desbalanceo extremo* (Solo ~6.2% Glosadas). El sub-muestreo generó que el modelo decida converger localmente aprendiendo a predecir siempre clase 0 (*Recall Glosada actual = 0.0*).
* **Fix programado (Model v2):** Rebalanceo por `sample_weight="balanced"` y aumento de la capa minotiraria.

### Fase 3: Dashboard Desplegado Localmente (Completado ✅)
* Vistas interactivas de riesgos territoriales implementadas vía Mapas de Calor Leaflet y capas de distancias vectorizadas interactivas.

---

## 🛠️ Cómo Iniciar el Entorno Local

Para explorar los datos y arrancar el panel temporalmente:

1. Levanta un servidor local en la carpeta del dashboard:
```bash
# Windows Anaconda Prompt
python -m http.server 8765 --directory "d:\Users\jcardonr\Documents\Savia\dashboard"
```
2. Visita `http://localhost:8765` en tu navegador para interactuar con los mapas y el simulador socioespacial predictivo.

---

*Proyecto de Datos Savia Salud EPS — Protegido bajo políticas de privacidad PII.*
