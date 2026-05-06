"use client";

import { SHAP_V3 } from "@/lib/modelData";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie, Legend,
} from "recharts";

const COLORS: Record<string, string> = {
  temporal:         "#6366f1",
  geoespacial:      "#ef4444",
  "socioeconómica": "#f59e0b",
};

// Importancia agrupada por tipo
const byTipo = Object.entries(
  SHAP_V3.reduce<Record<string, number>>((acc, f) => {
    acc[f.tipo] = (acc[f.tipo] ?? 0) + f.importancia;
    return acc;
  }, {})
).map(([tipo, valor]) => ({ tipo, valor }));

export default function FeaturesPage() {
  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Importancia de Features — SHAP</h1>
        <p className="text-sm text-slate-500 mt-1">
          Modelo v5 · Media |SHAP| sobre muestra de validación (n=5000) · 6 meses de datos maduros
        </p>
      </div>

      {/* Logro v4 */}
      <div className="bg-emerald-50 border-2 border-emerald-200 rounded-2xl p-5 flex gap-3">
        <div className="text-emerald-500 text-xl flex-shrink-0">✓</div>
        <div>
          <p className="font-bold text-emerald-800 text-sm">v5 — 6 meses de datos maduros · Precision Glosada 33.9%</p>
          <p className="text-sm text-emerald-700 mt-1">
            Con 6.28M facturas maduras (≥30 días desde radicación), AUC-ROC subió 0.604 → <strong>0.674</strong>
            y Precision Glosada saltó 12.8% → <strong>33.9%</strong>: 1 de cada 3 facturas marcadas como riesgo es realmente glosada.
            SHAP dominado por <strong>mes_radicacion</strong> (estacionalidad a investigar) y <strong>glosa_rate_municipio</strong> (patrón geoespacial real).
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Gráfica horizontal */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <h2 className="font-bold text-slate-800 mb-4">Top 15 features por importancia SHAP</h2>
          <ResponsiveContainer width="100%" height={380}>
            <BarChart
              data={[...SHAP_V3].reverse()}
              layout="vertical"
              margin={{ left: 160, right: 30, top: 0, bottom: 0 }}
            >
              <XAxis type="number" tick={{ fontSize: 10 }} tickFormatter={v => v.toFixed(2)} />
              <YAxis type="category" dataKey="feature" tick={{ fontSize: 10 }} width={160} />
              <Tooltip
                contentStyle={{ fontSize: 11, borderRadius: 8, border: "1px solid #e2e8f0" }}
                formatter={(v: number, _: string, { payload }: { payload: { tipo: string } }) => [
                  `${v.toFixed(4)}`,
                  payload.tipo,
                ]}
              />
              <Bar dataKey="importancia" radius={[0, 4, 4, 0]}>
                {[...SHAP_V3].reverse().map((f) => (
                  <Cell key={f.feature} fill={COLORS[f.tipo] ?? "#94a3b8"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pie por tipo */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 flex flex-col">
          <h2 className="font-bold text-slate-800 mb-4">Importancia por categoría</h2>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={byTipo}
                dataKey="valor"
                nameKey="tipo"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label={({ tipo, valor }) => `${(valor * 100).toFixed(0)}%`}
                labelLine={true}
              >
                {byTipo.map((b) => (
                  <Cell key={b.tipo} fill={COLORS[b.tipo] ?? "#94a3b8"} />
                ))}
              </Pie>
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 space-y-2">
            {byTipo.sort((a, b) => b.valor - a.valor).map(b => (
              <div key={b.tipo} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[b.tipo] }} />
                  <span className="text-slate-600 capitalize">{b.tipo}</span>
                </div>
                <span className="font-bold font-mono" style={{ color: COLORS[b.tipo] }}>
                  {(b.valor * 100).toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tabla detalle */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100">
          <h2 className="font-bold text-slate-800">Detalle de features</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 text-xs text-slate-400 uppercase tracking-wider">
              <th className="text-left px-6 py-3">Feature</th>
              <th className="text-left px-6 py-3">Tipo</th>
              <th className="text-right px-6 py-3">SHAP</th>
              <th className="text-left px-6 py-3">% total</th>
              <th className="text-left px-6 py-3">Barra</th>
              <th className="text-left px-6 py-3">Nota</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {SHAP_V3.map((f) => (
              <tr key={f.feature} className="hover:bg-slate-50">
                <td className="px-6 py-3 font-mono text-xs text-slate-700">{f.feature}</td>
                <td className="px-6 py-3">
                  <span className="text-xs px-2 py-0.5 rounded-full font-medium"
                        style={{ backgroundColor: COLORS[f.tipo] + "20", color: COLORS[f.tipo] }}>
                    {f.tipo}
                  </span>
                </td>
                <td className="px-6 py-3 text-right font-mono text-xs text-slate-600">
                  {f.importancia.toFixed(4)}
                </td>
                <td className="px-6 py-3 font-mono text-xs font-bold"
                    style={{ color: COLORS[f.tipo] }}>
                  {(f.importancia * 100).toFixed(1)}%
                </td>
                <td className="px-6 py-3">
                  <div className="w-24 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full rounded-full"
                         style={{ width: `${Math.min(f.importancia * 230, 100)}%`, backgroundColor: COLORS[f.tipo] }} />
                  </div>
                </td>
                <td className="px-6 py-3 text-xs text-slate-400">
                  {f.feature === "edad" && "✓ Top 1 SHAP v4 — riesgo real por grupo etario"}
                  {f.feature === "glosa_rate_municipio" && "✓ Top 2 SHAP v4 — geoespacial clave"}
                  {f.feature === "glosa_rate_region" && "✓ Top 3 SHAP v4 — patrón regional"}
                  {f.feature === "nivel_sisben" && "✓ Top 4 SHAP v4 — socioeconómico causal"}
                  {f.feature === "lejos_de_ips" && "SHAP bajo — considerar eliminar"}
                  {f.feature === "ips_capitacion" && "Nueva en v4 — modalidad contractual IPS"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
