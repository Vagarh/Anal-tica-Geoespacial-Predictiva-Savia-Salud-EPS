"use client";

import dynamic from "next/dynamic";
import { MUNICIPIOS_RIESGO } from "@/lib/modelData";

const MapaRiesgo = dynamic(() => import("@/components/MapaRiesgo"), { ssr: false });

// IPS sintéticas para demo — en prod vendrían del API FastAPI GET /v1/geo/ips
const IPS_DEMO = [
  { municipio: "MEDELLÍN",   nombre: "Clínica Las Américas",  nivel: 3, lat: 6.244,  lng: -75.593, capitacion: true  },
  { municipio: "MEDELLÍN",   nombre: "Hospital Pablo Tobón",  nivel: 3, lat: 6.253,  lng: -75.571, capitacion: false },
  { municipio: "BELLO",      nombre: "ESE Hospital Marco F.", nivel: 1, lat: 6.341,  lng: -75.558, capitacion: true  },
  { municipio: "ITAGÜÍ",     nombre: "IPS Comfama Itagüí",    nivel: 1, lat: 6.172,  lng: -75.601, capitacion: true  },
  { municipio: "APARTADÓ",   nombre: "Hospital Antonio Roldán", nivel: 2, lat: 7.881, lng: -76.631, capitacion: false },
  { municipio: "TURBO",      nombre: "ESE Hospital de Turbo", nivel: 1, lat: 8.099,  lng: -76.729, capitacion: false },
  { municipio: "CAUCASIA",   nombre: "ESE Hospital Caucasia", nivel: 2, lat: 7.989,  lng: -75.196, capitacion: false },
  { municipio: "QUIBDÓ",     nombre: "Hospital San Francisco", nivel: 2, lat: 5.693, lng: -76.659, capitacion: false },
  { municipio: "RIONEGRO",   nombre: "Clínica Somer",          nivel: 3, lat: 6.156, lng: -75.373, capitacion: true  },
  { municipio: "ENVIGADO",   nombre: "Soma Envigado",          nivel: 2, lat: 6.174, lng: -75.593, capitacion: true  },
];

const NIVEL_COLOR: Record<number, string> = { 1: "#10b981", 2: "#6366f1", 3: "#ef4444" };
const NIVEL_LABEL: Record<number, string> = { 1: "Nivel 1 — Básico", 2: "Nivel 2 — Mediano", 3: "Nivel 3 — Alta complejidad" };

export default function PrestadoresPage() {
  const porNivel = [1, 2, 3].map(n => ({
    nivel: n,
    total: IPS_DEMO.filter(i => i.nivel === n).length,
    capitacion: IPS_DEMO.filter(i => i.nivel === n && i.capitacion).length,
  }));

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Red de Prestadores IPS</h1>
        <p className="text-sm text-slate-500 mt-1">
          Distribución geoespacial · Nivel de atención · Modalidad capitación
        </p>
      </div>

      {/* KPIs IPS */}
      <div className="grid grid-cols-3 gap-4">
        {porNivel.map(({ nivel, total, capitacion }) => (
          <div key={nivel} className="bg-white rounded-2xl border-2 p-5"
               style={{ borderColor: NIVEL_COLOR[nivel] + "40" }}>
            <div className="flex items-center gap-2 mb-2">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: NIVEL_COLOR[nivel] }} />
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{NIVEL_LABEL[nivel]}</p>
            </div>
            <p className="text-3xl font-extrabold" style={{ color: NIVEL_COLOR[nivel] }}>{total}</p>
            <p className="text-xs text-slate-400 mt-1">{capitacion} en capitación ({Math.round(capitacion/total*100)}%)</p>
          </div>
        ))}
      </div>

      {/* Mapa */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden" style={{ height: 420 }}>
        <MapaRiesgo
          municipios={MUNICIPIOS_RIESGO}
          colorFn={(rate) => rate > 0.15 ? "#ef4444" : rate > 0.10 ? "#f59e0b" : "#6366f1"}
        />
      </div>

      {/* Tabla */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="font-bold text-slate-800">Sedes IPS</h2>
          <span className="text-xs text-slate-400 bg-slate-100 px-3 py-1 rounded-full">Demo · {IPS_DEMO.length} sedes</span>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 text-xs text-slate-400 uppercase tracking-wider">
              <th className="text-left px-6 py-3">Nombre sede</th>
              <th className="text-left px-6 py-3">Municipio</th>
              <th className="text-center px-4 py-3">Nivel</th>
              <th className="text-center px-4 py-3">Capitación</th>
              <th className="text-center px-4 py-3">Lat / Lng</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {IPS_DEMO.map((ips) => (
              <tr key={ips.nombre} className="hover:bg-slate-50">
                <td className="px-6 py-3 font-medium text-slate-800">{ips.nombre}</td>
                <td className="px-6 py-3 text-slate-500">{ips.municipio}</td>
                <td className="px-4 py-3 text-center">
                  <span className="text-xs font-bold px-2 py-0.5 rounded-full"
                        style={{ backgroundColor: NIVEL_COLOR[ips.nivel] + "20", color: NIVEL_COLOR[ips.nivel] }}>
                    N{ips.nivel}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  {ips.capitacion
                    ? <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-medium">Sí</span>
                    : <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full">No</span>}
                </td>
                <td className="px-4 py-3 text-center font-mono text-xs text-slate-400">
                  {ips.lat.toFixed(3)}, {ips.lng.toFixed(3)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
