import { KPI_GENERAL, VERSIONS, MUNICIPIOS_RIESGO } from "@/lib/modelData";
import { TrendingUp, Users, MapPin, AlertTriangle, CheckCircle, XCircle } from "lucide-react";

function KpiCard({
  label, value, sub, color = "brand",
}: { label: string; value: string; sub: string; color?: string }) {
  const ring: Record<string, string> = {
    brand:   "border-brand-500/30 bg-brand-50",
    danger:  "border-red-400/30 bg-red-50",
    warning: "border-amber-400/30 bg-amber-50",
    success: "border-emerald-400/30 bg-emerald-50",
  };
  const text: Record<string, string> = {
    brand:   "text-brand-600",
    danger:  "text-red-600",
    warning: "text-amber-600",
    success: "text-emerald-600",
  };
  return (
    <div className={`rounded-xl border-2 p-5 ${ring[color]}`}>
      <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-1">{label}</p>
      <p className={`text-3xl font-extrabold ${text[color]}`}>{value}</p>
      <p className="text-xs text-slate-400 mt-1">{sub}</p>
    </div>
  );
}

export default function Home() {
  const best = VERSIONS.find(v => v.version === "v5")!;
  const topRiesgo = [...MUNICIPIOS_RIESGO]
    .sort((a, b) => b.tasa_glosa - a.tasa_glosa)
    .slice(0, 5);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Resumen Ejecutivo</h1>
        <p className="text-sm text-slate-500 mt-1">
          Analítica Geoespacial Predictiva · Últimos 3 meses · {KPI_GENERAL.n_municipios} municipios
        </p>
      </div>

      {/* KPIs principales */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Facturas analizadas"
          value={`${(KPI_GENERAL.total_facturas / 1e6).toFixed(1)}M`}
          sub="últimos 3 meses"
          color="brand"
        />
        <KpiCard
          label="Tasa de glosa global"
          value={`${(KPI_GENERAL.tasa_glosa_global * 100).toFixed(1)}%`}
          sub={`${Math.round(KPI_GENERAL.total_facturas * KPI_GENERAL.tasa_glosa_global / 1000)}K facturas glosadas`}
          color="danger"
        />
        <KpiCard
          label="Tasa devuelta"
          value={`${(KPI_GENERAL.tasa_devuelta_global * 100).toFixed(1)}%`}
          sub="error administrativo"
          color="warning"
        />
        <KpiCard
          label="Municipios activos"
          value={String(KPI_GENERAL.n_municipios)}
          sub="con facturas en período"
          color="success"
        />
      </div>

      {/* Comparación de versiones del modelo */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="font-bold text-slate-800">Evolución del Modelo Predictivo</h2>
          <span className="text-xs text-slate-400 bg-slate-100 px-3 py-1 rounded-full">XGBoost multiclase</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
                <th className="text-left px-6 py-3">Versión</th>
                <th className="text-left px-6 py-3">Descripción</th>
                <th className="text-center px-4 py-3">AUC-ROC test</th>
                <th className="text-center px-4 py-3">Recall Glosada</th>
                <th className="text-center px-4 py-3">F1-macro</th>
                <th className="text-center px-4 py-3">Umbral</th>
                <th className="text-center px-4 py-3">≥0.75</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {VERSIONS.map((v) => (
                <tr key={v.version} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4">
                    <span className="font-mono font-bold text-brand-600 bg-brand-50 px-2 py-0.5 rounded">
                      {v.version}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-600 max-w-xs">
                    <span>{v.descripcion}</span>
                    {v.nota && (
                      <p className="text-xs text-amber-500 mt-0.5">⚠ {v.nota}</p>
                    )}
                  </td>
                  <td className="px-4 py-4 text-center">
                    <span className={`font-mono font-semibold ${v.auc_roc_test >= 0.75 ? "text-emerald-600" : "text-slate-700"}`}>
                      {v.auc_roc_test.toFixed(3)}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-center">
                    <span className={`font-mono font-semibold ${v.recall_glosada_test > 0.3 ? "text-emerald-600" : "text-red-500"}`}>
                      {v.recall_glosada_test.toFixed(3)}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-center font-mono text-slate-600">
                    {v.f1_macro_test.toFixed(3)}
                  </td>
                  <td className="px-4 py-4 text-center font-mono text-slate-500 text-xs">
                    {v.umbral.toFixed(4)}
                  </td>
                  <td className="px-4 py-4 text-center">
                    {v.baseline_ok
                      ? <CheckCircle size={16} className="text-emerald-500 mx-auto" />
                      : <XCircle size={16} className="text-red-400 mx-auto" />}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="px-6 py-3 bg-emerald-50 border-t border-emerald-100 flex items-start gap-2">
          <CheckCircle size={14} className="text-emerald-500 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-emerald-700">
            <strong>v5 — 6 meses de datos maduros:</strong> 6.28M facturas con filtro de rezago ≥30 días.
            AUC-ROC subió 0.604 → <strong>0.674</strong>. Precision Glosada: 12.8% → <strong>33.9%</strong>.
            1 de cada 3 facturas marcadas como riesgo es realmente glosada.
          </p>
        </div>
      </div>

      {/* Top municipios de riesgo */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="font-bold text-slate-800">Top 5 Municipios de Alto Riesgo</h2>
            <p className="text-xs text-slate-400 mt-0.5">Por tasa de glosa · mín. 100K facturas</p>
          </div>
          <div className="divide-y divide-slate-100">
            {topRiesgo.map((m, i) => (
              <div key={m.municipio} className="px-6 py-3 flex items-center gap-4">
                <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-500 text-xs font-bold flex items-center justify-center flex-shrink-0">
                  {i + 1}
                </span>
                <div className="flex-1">
                  <p className="font-semibold text-slate-800 text-sm">{m.municipio}</p>
                  <p className="text-xs text-slate-400">{(m.n_facturas / 1000).toFixed(0)}K facturas</p>
                </div>
                <div className="text-right">
                  <span
                    className={`text-sm font-bold ${
                      m.tasa_glosa > 0.15
                        ? "text-red-600"
                        : m.tasa_glosa > 0.10
                        ? "text-amber-600"
                        : "text-slate-600"
                    }`}
                  >
                    {(m.tasa_glosa * 100).toFixed(1)}%
                  </span>
                  <p className="text-xs text-slate-400">tasa glosa</p>
                </div>
                {/* Barra */}
                <div className="w-20 h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      m.tasa_glosa > 0.15 ? "bg-red-500" : m.tasa_glosa > 0.10 ? "bg-amber-400" : "bg-brand-500"
                    }`}
                    style={{ width: `${Math.min(m.tasa_glosa * 500, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Estado fases */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="font-bold text-slate-800">Estado del Proyecto</h2>
          </div>
          <div className="divide-y divide-slate-100">
            {[
              { fase: "Fase 0", nombre: "EDA Geoespacial",                estado: "done",    pct: 100 },
              { fase: "Fase 1", nombre: "Ingeniería de Features",          estado: "done",    pct: 100 },
              { fase: "Fase 2", nombre: "Modelo Predictivo XGBoost (v5)",   estado: "done",    pct: 100  },
              { fase: "Fase 3", nombre: "API Backend FastAPI",             estado: "pending", pct: 0   },
              { fase: "Fase 4", nombre: "Dashboard Next.js",               estado: "inprog",  pct: 40  },
            ].map((f) => (
              <div key={f.fase} className="px-6 py-3 flex items-center gap-4">
                <div className="w-14 flex-shrink-0">
                  <span className="text-xs font-mono text-slate-400">{f.fase}</span>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-700">{f.nombre}</p>
                  <div className="mt-1.5 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        f.estado === "done"    ? "bg-emerald-500" :
                        f.estado === "warning" ? "bg-amber-400" :
                        f.estado === "inprog"  ? "bg-brand-500" :
                        "bg-slate-200"
                      }`}
                      style={{ width: `${f.pct}%` }}
                    />
                  </div>
                </div>
                <span className="text-xs font-bold text-slate-500 w-10 text-right">{f.pct}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
