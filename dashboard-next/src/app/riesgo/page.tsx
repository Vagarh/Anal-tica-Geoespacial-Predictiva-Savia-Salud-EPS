"use client";

import dynamic from "next/dynamic";
import { MUNICIPIOS_RIESGO } from "@/lib/modelData";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid } from "recharts";

// Leaflet solo en cliente (no SSR)
const MapaRiesgo = dynamic(() => import("@/components/MapaRiesgo"), { ssr: false });

const sorted = [...MUNICIPIOS_RIESGO].sort((a, b) => b.tasa_glosa - a.tasa_glosa);

function colorByRate(rate: number): string {
  if (rate > 0.15) return "#ef4444";
  if (rate > 0.10) return "#f59e0b";
  if (rate > 0.06) return "#6366f1";
  return "#10b981";
}

export default function RiesgoPage() {
  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Mapa de Riesgo Geoespacial</h1>
        <p className="text-sm text-slate-500 mt-1">
          Tasa de glosa por municipio · Coordenadas agregadas (Ley 1581 — sin puntos individuales)
        </p>
      </div>

      {/* Leyenda */}
      <div className="flex gap-4 flex-wrap">
        {[
          { label: "Alto riesgo >15%",    color: "#ef4444" },
          { label: "Riesgo medio 10-15%", color: "#f59e0b" },
          { label: "Moderado 6-10%",      color: "#6366f1" },
          { label: "Bajo <6%",            color: "#10b981" },
        ].map(({ label, color }) => (
          <div key={label} className="flex items-center gap-1.5 text-xs text-slate-600">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
            {label}
          </div>
        ))}
      </div>

      {/* Mapa */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden" style={{ height: 480 }}>
        <MapaRiesgo municipios={MUNICIPIOS_RIESGO} colorFn={colorByRate} />
      </div>

      {/* Gráfica de barras */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
        <h2 className="font-bold text-slate-800 mb-4">Tasa de Glosa por Municipio (ordenado por riesgo)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={sorted} margin={{ left: 0, right: 20, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis
              dataKey="municipio"
              tick={{ fontSize: 10, fill: "#64748b" }}
              angle={-40}
              textAnchor="end"
            />
            <YAxis
              tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
              tick={{ fontSize: 10 }}
            />
            <Tooltip
              formatter={(v: number) => [`${(v * 100).toFixed(1)}%`, "Tasa glosa"]}
              contentStyle={{ fontSize: 12, borderRadius: 8 }}
            />
            <Bar dataKey="tasa_glosa" radius={[4, 4, 0, 0]}>
              {sorted.map((m) => (
                <Cell key={m.municipio} fill={colorByRate(m.tasa_glosa)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Tabla detalle */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100">
          <h2 className="font-bold text-slate-800">Detalle por Municipio</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-xs text-slate-400 uppercase tracking-wider">
                <th className="text-left px-6 py-3">Municipio</th>
                <th className="text-right px-6 py-3">Facturas</th>
                <th className="text-right px-6 py-3">Tasa Glosa</th>
                <th className="text-left px-6 py-3">Riesgo</th>
                <th className="text-left px-6 py-3">Barra</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {sorted.map((m) => (
                <tr key={m.municipio} className="hover:bg-slate-50">
                  <td className="px-6 py-3 font-medium text-slate-800">{m.municipio}</td>
                  <td className="px-6 py-3 text-right text-slate-500 font-mono text-xs">
                    {(m.n_facturas / 1000).toFixed(0)}K
                  </td>
                  <td className="px-6 py-3 text-right font-bold font-mono"
                      style={{ color: colorByRate(m.tasa_glosa) }}>
                    {(m.tasa_glosa * 100).toFixed(1)}%
                  </td>
                  <td className="px-6 py-3">
                    <span className="text-xs px-2 py-0.5 rounded-full font-medium"
                          style={{ backgroundColor: colorByRate(m.tasa_glosa) + "20", color: colorByRate(m.tasa_glosa) }}>
                      {m.tasa_glosa > 0.15 ? "Alto" : m.tasa_glosa > 0.10 ? "Medio" : m.tasa_glosa > 0.06 ? "Moderado" : "Bajo"}
                    </span>
                  </td>
                  <td className="px-6 py-3">
                    <div className="w-28 h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full rounded-full"
                           style={{ width: `${Math.min(m.tasa_glosa * 550, 100)}%`, backgroundColor: colorByRate(m.tasa_glosa) }} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
