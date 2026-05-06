"use client";

import { VERSIONS, SHAP_V3 } from "@/lib/modelData";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend, CartesianGrid,
} from "recharts";

const COLORS: Record<string, string> = {
  temporal:       "#6366f1",
  geoespacial:    "#ef4444",
  "socioeconómica": "#f59e0b",
};

const METRIC_COLS = [
  { key: "auc_roc_val",           label: "AUC-ROC Val",   fmt: (v: number) => v.toFixed(3) },
  { key: "auc_roc_test",          label: "AUC-ROC Test",  fmt: (v: number) => v.toFixed(3) },
  { key: "recall_glosada_val",    label: "Recall Glosada Val",   fmt: (v: number) => v.toFixed(3) },
  { key: "recall_glosada_test",   label: "Recall Glosada Test",  fmt: (v: number) => v.toFixed(3) },
  { key: "precision_glosada_test",label: "Precision Glosada Test", fmt: (v: number | null) => v != null ? v.toFixed(3) : "—" },
  { key: "f1_macro_test",         label: "F1-macro Test", fmt: (v: number) => v.toFixed(3) },
  { key: "umbral",                label: "Umbral",        fmt: (v: number) => v.toFixed(4) },
];

// Datos para LineChart de evolución
const evo = VERSIONS.map(v => ({
  version: v.version,
  "AUC-ROC test":          v.auc_roc_test,
  "Recall Glosada test":   v.recall_glosada_test,
  "Precision Glosada test": v.precision_glosada_test ?? 0,
}));

// Radar data para v3
const radarData = [
  { metric: "AUC-ROC",         v1: 0.621, v2: 0.568, v3: 0.546 },
  { metric: "Recall Glosada",  v1: 0.000, v2: 0.999, v3: 0.974 },
  { metric: "Precision Glosa", v1: 0.000, v2: 0.056, v3: 0.057 },
  { metric: "F1-macro",        v1: 0.323, v2: 0.035, v3: 0.073 },
];

export default function ModeloPage() {
  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Evaluación del Modelo</h1>
        <p className="text-sm text-slate-500 mt-1">
          Comparativa v1 → v4 · XGBoost multiclase (Auditada / Glosada / Devuelta)
        </p>
      </div>

      {/* Logro v4 */}
      <div className="bg-emerald-50 border-2 border-emerald-200 rounded-2xl p-5 flex gap-3">
        <div className="text-emerald-500 text-xl flex-shrink-0">✓</div>
        <div>
          <p className="font-bold text-emerald-800 text-sm">v4 — Bias temporal eliminado · SHAP limpio · Features causales reales</p>
          <p className="text-sm text-emerald-700 mt-1">
            Filtro de rezago (≥30 días): 2.76M facturas sin auditoría completa excluidas del entrenamiento.
            AUC-ROC test subió de 0.546 → <strong>0.604</strong>. Precision Glosada: 5.7% → <strong>12.8%</strong>.
            SHAP ahora dominado por <code className="bg-emerald-100 px-1 rounded">edad</code> (19.7%),{" "}
            <code className="bg-emerald-100 px-1 rounded">glosa_rate_municipio</code> (16.1%) y{" "}
            <code className="bg-emerald-100 px-1 rounded">nivel_sisben</code> (13.6%) — riesgo real, no ruido de proceso.
          </p>
        </div>
      </div>

      {/* Diagnóstico */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            version: "v1", color: "bg-slate-50 border-slate-200",
            badge: "bg-red-100 text-red-700",
            title: "Baseline",
            issues: ["scale_pos_weight ignorado en multiclase", "Recall Glosada = 0%", "El modelo nunca predice glosas"],
            fix: null,
          },
          {
            version: "v2", color: "bg-amber-50 border-amber-200",
            badge: "bg-amber-100 text-amber-700",
            title: "Corrección desbalance",
            issues: ["sample_weight explícito", "Umbral calibrado en val completa (drift 13.6%)", "Umbral 0.05 → todo clasificado como glosa"],
            fix: "Recall ↑ 0→99.9% · AUC 0.57",
          },
          {
            version: "v3", color: "bg-orange-50 border-orange-200",
            badge: "bg-orange-100 text-orange-700",
            title: "Features temporales",
            issues: ["dias_desde_inicio domina SHAP (42%)", "Capta backlog auditoría, no riesgo real", "Glosas últimas 2 sem = 0% (sin auditar)"],
            fix: "AUC 0.546 · Precision 5.7%",
          },
          {
            version: "v4", color: "bg-emerald-50 border-emerald-200",
            badge: "bg-emerald-100 text-emerald-700",
            title: "Filtro rezago + causales",
            issues: ["Excluidas 2.76M facturas sin auditar", "Eliminadas dias_desde_inicio/dia_semana/semana_anio", "SHAP: edad · glosa_rate_municipio · SISBEN"],
            fix: "AUC 0.604 · Precision 12.8%",
          },
        ].map(({ version, color, badge, title, issues, fix }) => (
          <div key={version} className={`rounded-2xl border-2 p-5 ${color}`}>
            <div className="flex items-center gap-2 mb-3">
              <span className={`font-mono font-bold text-sm px-2 py-0.5 rounded ${badge}`}>{version}</span>
              <span className="font-semibold text-slate-700 text-sm">{title}</span>
            </div>
            <ul className="space-y-1">
              {issues.map(i => (
                <li key={i} className="text-xs text-slate-600 flex gap-1.5">
                  <span className="text-slate-400 mt-0.5">•</span>{i}
                </li>
              ))}
            </ul>
            {fix && (
              <p className="mt-3 text-xs font-semibold text-indigo-700 bg-white/60 px-2 py-1 rounded border border-indigo-200">
                → {fix}
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Evolución de métricas */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
        <h2 className="font-bold text-slate-800 mb-4">Evolución de Métricas por Versión</h2>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={evo} margin={{ left: 0, right: 20, top: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="version" tick={{ fontSize: 12 }} />
            <YAxis domain={[0, 1.05]} tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e2e8f0" }}
              formatter={(v: number) => v.toFixed(4)}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line dataKey="AUC-ROC test"           stroke="#6366f1" strokeWidth={2} dot={{ r: 4 }} />
            <Line dataKey="Recall Glosada test"     stroke="#ef4444" strokeWidth={2} dot={{ r: 4 }} />
            <Line dataKey="Precision Glosada test"  stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} strokeDasharray="4 2" />
            {/* Línea objetivo AUC */}
            <Line dataKey={() => 0.75} stroke="#10b981" strokeDasharray="6 3" strokeWidth={1.5}
                  name="Objetivo AUC 0.75" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* SHAP + tabla */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* SHAP importancia v3 */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <h2 className="font-bold text-slate-800 mb-1">Importancia SHAP — v3</h2>
          <p className="text-xs text-slate-400 mb-4">Media |SHAP| sobre muestra de validación</p>
          <ResponsiveContainer width="100%" height={340}>
            <BarChart
              data={[...SHAP_V3].reverse()}
              layout="vertical"
              margin={{ left: 140, right: 20, top: 0, bottom: 0 }}
            >
              <XAxis type="number" tick={{ fontSize: 10 }} />
              <YAxis type="category" dataKey="feature" tick={{ fontSize: 10 }} width={140} />
              <Tooltip
                contentStyle={{ fontSize: 11, borderRadius: 8 }}
                formatter={(v: number) => [v.toFixed(4), "SHAP"]}
              />
              <Bar dataKey="importancia" radius={[0, 4, 4, 0]}>
                {SHAP_V3.map((entry, i) => (
                  <rect key={i} fill={COLORS[entry.tipo] ?? "#94a3b8"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="flex gap-4 mt-3 flex-wrap">
            {Object.entries(COLORS).map(([tipo, color]) => (
              <div key={tipo} className="flex items-center gap-1.5 text-xs text-slate-500">
                <span className="w-3 h-3 rounded-sm flex-shrink-0" style={{ backgroundColor: color }} />
                {tipo}
              </div>
            ))}
          </div>
        </div>

        {/* Tabla de métricas */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="font-bold text-slate-800">Tabla de Métricas Comparativa</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-slate-50 text-slate-400 uppercase tracking-wider">
                  <th className="text-left px-4 py-3">Métrica</th>
                  {VERSIONS.map(v => (
                    <th key={v.version} className="text-center px-3 py-3">{v.version}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {METRIC_COLS.map(col => (
                  <tr key={col.key} className="hover:bg-slate-50">
                    <td className="px-4 py-2.5 text-slate-600 font-medium">{col.label}</td>
                    {VERSIONS.map(v => {
                      const val = (v as Record<string, unknown>)[col.key] as number | null;
                      return (
                        <td key={v.version} className="px-3 py-2.5 text-center font-mono text-slate-700">
                          {col.fmt(val as never)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Próximo paso */}
      <div className="bg-indigo-50 border-2 border-indigo-200 rounded-2xl p-5">
        <h3 className="font-bold text-indigo-800 mb-2">Próximo paso v5 — Datos de 6 meses + código CIE-10 real</h3>
        <p className="text-sm text-indigo-700">
          v4 entrena solo sobre 3 meses filtrados (~8.9M facturas). Con 6 meses de datos maduros
          el modelo tendría más ejemplos de glosa por municipio y región para aprender patrones estacionales.
          Adicionalmente, <code className="bg-indigo-100 px-1 rounded">codigo_dx</code> tiene 100% nulos
          en la extracción actual — conectar la columna correcta habilitaría <code className="bg-indigo-100 px-1 rounded">glosa_rate_dx_capitulo</code>
          como feature real (actualmente constante). AUC objetivo: ≥ 0.70.
        </p>
      </div>
    </div>
  );
}
