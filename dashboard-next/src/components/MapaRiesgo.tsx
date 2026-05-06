"use client";

import { useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";

interface Municipio {
  municipio: string;
  tasa_glosa: number;
  n_facturas: number;
  lat: number;
  lng: number;
}

interface Props {
  municipios: Municipio[];
  colorFn: (rate: number) => string;
}

export default function MapaRiesgo({ municipios, colorFn }: Props) {
  useEffect(() => {
    // Fix leaflet icon en Next.js
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const L = require("leaflet");
    delete (L.Icon.Default.prototype as { _getIconUrl?: unknown })._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
      iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
      shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    });
  }, []);

  return (
    <MapContainer
      center={[6.5, -75.5]}
      zoom={7}
      style={{ height: "100%", width: "100%" }}
      scrollWheelZoom={true}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
      />
      {municipios.map((m) => (
        <CircleMarker
          key={m.municipio}
          center={[m.lat, m.lng]}
          radius={Math.max(6, Math.sqrt(m.n_facturas / 50000) * 4)}
          pathOptions={{
            color:       colorFn(m.tasa_glosa),
            fillColor:   colorFn(m.tasa_glosa),
            fillOpacity: 0.75,
            weight:      1.5,
          }}
        >
          <Tooltip>
            <div className="text-xs">
              <p className="font-bold text-slate-800">{m.municipio}</p>
              <p>Tasa glosa: <strong>{(m.tasa_glosa * 100).toFixed(1)}%</strong></p>
              <p>Facturas: {(m.n_facturas / 1000).toFixed(0)}K</p>
            </div>
          </Tooltip>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
