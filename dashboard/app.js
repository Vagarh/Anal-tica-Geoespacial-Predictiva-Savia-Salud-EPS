/* ════════════════════════════════════════════════════════════
   SAVIA SALUD EPS · Analítica Geoespacial · app.js
   Leaflet maps + Chart.js · Datos reales modelo XGBoost geo_v1
   ════════════════════════════════════════════════════════════ */

// ── Datos reales del proyecto ─────────────────────────────────

const MUNS = [
  { id:'vigia',        nombre:'Vigía del Fuerte',   lat:6.9996, lng:-76.8981, tasa:21.0,  facturas:4200,   cat:'critico' },
  { id:'anza',         nombre:'Anza',               lat:6.2833, lng:-75.9167, tasa:19.5,  facturas:6100,   cat:'critico' },
  { id:'hispania',     nombre:'Hispania',            lat:6.2167, lng:-76.0833, tasa:19.5,  facturas:7800,   cat:'critico' },
  { id:'puerto_triunfo',nombre:'Puerto Triunfo',    lat:5.8750, lng:-74.7281, tasa:18.2,  facturas:9200,   cat:'critico' },
  { id:'briceno',      nombre:'Briceño',             lat:7.0833, lng:-75.5500, tasa:16.5,  facturas:5300,   cat:'critico' },
  { id:'nechi',        nombre:'Nechí',               lat:8.0983, lng:-74.7739, tasa:16.2,  facturas:8400,   cat:'critico' },
  { id:'angostura',    nombre:'Angostura',           lat:6.8833, lng:-75.3667, tasa:15.5,  facturas:6700,   cat:'critico' },
  { id:'yali',         nombre:'Yalí',                lat:6.9667, lng:-74.8000, tasa:14.0,  facturas:5100,   cat:'alto'    },
  { id:'turbo',        nombre:'Turbo',               lat:8.0989, lng:-76.7278, tasa:13.8,  facturas:165627, cat:'alto'    },
  { id:'puerto_berrio',nombre:'Puerto Berrío',       lat:6.4894, lng:-74.4028, tasa:13.8,  facturas:151074, cat:'alto'    },
  { id:'caucasia',     nombre:'Caucasia',            lat:7.9853, lng:-75.1964, tasa:12.4,  facturas:187421, cat:'moderado'},
  { id:'apartado',     nombre:'Apartadó',            lat:7.8833, lng:-76.6267, tasa:11.1,  facturas:244468, cat:'moderado'},
  { id:'carepa',       nombre:'Carepa',              lat:7.7589, lng:-76.6594, tasa:10.5,  facturas:208503, cat:'moderado'},
  { id:'rionegro',     nombre:'Rionegro',            lat:6.1552, lng:-75.3764, tasa:8.9,   facturas:188700, cat:'moderado'},
  { id:'sonson',       nombre:'Sonsón',              lat:5.7167, lng:-75.3167, tasa:8.6,   facturas:142512, cat:'moderado'},
  { id:'envigado',     nombre:'Envigado',            lat:6.1706, lng:-75.5867, tasa:9.6,   facturas:203055, cat:'moderado'},
  { id:'bello',        nombre:'Bello',               lat:6.3328, lng:-75.5614, tasa:7.8,   facturas:720917, cat:'bajo'    },
  { id:'medellin',     nombre:'Medellín',            lat:6.2518, lng:-75.5636, tasa:7.6,   facturas:3295701,cat:'bajo'    },
  { id:'itagui',       nombre:'Itagüí',              lat:6.1843, lng:-75.5997, tasa:7.5,   facturas:425963, cat:'bajo'    },
  { id:'caldas',       nombre:'Caldas',              lat:6.0928, lng:-75.6361, tasa:5.2,   facturas:147217, cat:'bajo'    },
  { id:'marinilla',    nombre:'Marinilla',           lat:6.1778, lng:-75.3389, tasa:4.8,   facturas:138967, cat:'bajo'    },
  { id:'copacabana',   nombre:'Copacabana',          lat:6.3500, lng:-75.5167, tasa:5.5,   facturas:129881, cat:'bajo'    },
  { id:'barbosa',      nombre:'Barbosa',             lat:6.4393, lng:-75.3314, tasa:6.1,   facturas:129876, cat:'bajo'    },
  { id:'andes',        nombre:'Andes',               lat:5.6558, lng:-75.8786, tasa:4.1,   facturas:129388, cat:'bajo'    },
  { id:'concordia',    nombre:'Concordia',           lat:6.0333, lng:-75.9000, tasa:3.8,   facturas:110523, cat:'bajo'    },
  { id:'santa_rosa',   nombre:'Santa Rosa de Osos',  lat:6.6500, lng:-75.4667, tasa:5.9,   facturas:108082, cat:'bajo'    },
  { id:'chigorodo',    nombre:'Chigorodó',           lat:7.6706, lng:-76.6858, tasa:7.0,   facturas:107681, cat:'bajo'    },
];

const IPS_SEDES = [
  { nombre:'Clínica Las Américas',   lat:6.2490, lng:-75.5801, nivel:3, municipio:'Medellín',   sedes:1 },
  { nombre:'Clínica El Rosario',     lat:6.2602, lng:-75.5684, nivel:3, municipio:'Medellín',   sedes:1 },
  { nombre:'Hospital Pablo Tobón',   lat:6.2516, lng:-75.5760, nivel:3, municipio:'Medellín',   sedes:1 },
  { nombre:'IPS Comfama Bello',      lat:6.3350, lng:-75.5590, nivel:1, municipio:'Bello',      sedes:12 },
  { nombre:'HospitalSan Juan Dios',  lat:6.1843, lng:-75.5910, nivel:2, municipio:'Itagüí',     sedes:1 },
  { nombre:'Hospital de Apartadó',   lat:7.8900, lng:-76.6210, nivel:2, municipio:'Apartadó',   sedes:1 },
  { nombre:'IPS Turbo Red Savia',    lat:8.1050, lng:-76.7200, nivel:1, municipio:'Turbo',      sedes:3 },
  { nombre:'Clínica Caucasia',       lat:7.9900, lng:-75.1900, nivel:2, municipio:'Caucasia',   sedes:1 },
  { nombre:'ESE Hospital Rionegro',  lat:6.1560, lng:-75.3740, nivel:2, municipio:'Rionegro',   sedes:1 },
  { nombre:'IPS Envigado Municipal', lat:6.1720, lng:-75.5840, nivel:1, municipio:'Envigado',   sedes:6 },
  { nombre:'Centro Médico Caldas',   lat:6.0940, lng:-75.6370, nivel:1, municipio:'Caldas',     sedes:4 },
  { nombre:'ESE Vigia del Fuerte',   lat:7.0000, lng:-76.9000, nivel:1, municipio:'Vigía del Fuerte', sedes:1 },
  { nombre:'Puesto Salud Anza',      lat:6.2800, lng:-75.9200, nivel:1, municipio:'Anza',       sedes:1 },
  { nombre:'ESE Puerto Berrío',      lat:6.4900, lng:-74.4050, nivel:2, municipio:'Puerto Berrío', sedes:1 },
];

const C = {
  navy:'#0033A0', blue:'#0049cb', red:'#E03131', orange:'#F59F00',
  green:'#2F9E44', muted:'#6B7280', surface:'#F2F4F8', grid:'#E8EBF2'
};

// ── Color helpers ──────────────────────────────────────────────

function riskColor(tasa) {
  if (tasa > 13) return '#7B0000';
  if (tasa > 10) return '#CC2200';
  if (tasa > 7.6) return '#F59F00';
  return '#2F9E44';
}

function catBadgeHTML(cat) {
  const map = {
    critico: `<span class="kpi-badge badge-red">🔴 Crítico</span>`,
    alto:    `<span class="kpi-badge badge-red">🟠 Alto</span>`,
    moderado:`<span class="kpi-badge badge-yellow">🟡 Moderado</span>`,
    bajo:    `<span class="kpi-badge badge-green">🟢 Bajo</span>`,
  };
  return map[cat] || '';
}

// ── Navigation ─────────────────────────────────────────────────

const VIEW_NAMES = {
  resumen:     'Resumen Ejecutivo',
  'mapa-riesgo':  'Mapa de Riesgo',
  'mapa-ips':     'Red IPS & Distancias',
  'mapa-glosa':   'Análisis Glosas',
  features:    'Features SHAP',
  modelo:      'Métricas Modelo',
  prediccion:  'Predicción Geo',
};

let activeView = 'resumen';
const inited = {};

function navigateTo(view) {
  if (view === activeView) return;
  document.querySelectorAll('.view').forEach(el => el.style.display = 'none');
  document.querySelectorAll('.sb-item').forEach(el => el.classList.remove('active'));
  const el = document.getElementById('view-' + view);
  if (el) { el.style.display = 'block'; el.style.animation = 'none'; el.offsetHeight; el.style.animation = ''; }
  const nav = document.getElementById('nav-' + view);
  if (nav) nav.classList.add('active');
  document.getElementById('bc-page').textContent = VIEW_NAMES[view] || view;
  activeView = view;
  if (!inited[view]) { inited[view] = true; setTimeout(() => initView(view), 60); }
}

document.querySelectorAll('.sb-item').forEach(item => {
  item.addEventListener('click', e => {
    e.preventDefault();
    const v = item.getAttribute('data-view');
    if (v) navigateTo(v);
  });
});

// ── Init per view ──────────────────────────────────────────────

function initView(view) {
  switch (view) {
    case 'resumen':    initResumen();    break;
    case 'mapa-riesgo':initMapaRiesgo(); break;
    case 'mapa-ips':   initMapaIPS();   break;
    case 'mapa-glosa': initMapaGlosa(); break;
    case 'features':   initFeatures();  break;
    case 'modelo':     /* static */     break;
    case 'prediccion': initPrediccion();break;
  }
}

// ── RESUMEN ────────────────────────────────────────────────────

let miniMap = null;

function initResumen() {
  // Mini mapa
  if (!miniMap) {
    miniMap = L.map('mini-map', { zoomControl: true, scrollWheelZoom: false }).setView([6.8, -75.5], 7);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '© OpenStreetMap © CARTO', maxZoom: 18
    }).addTo(miniMap);

    MUNS.forEach(m => {
      const r = Math.max(8, Math.min(28, Math.log10(m.facturas) * 4));
      L.circleMarker([m.lat, m.lng], {
        radius: r, fillColor: riskColor(m.tasa), color: '#fff',
        weight: 1.5, opacity: 1, fillOpacity: 0.85
      }).bindTooltip(`<b>${m.nombre}</b><br>Tasa: ${m.tasa.toFixed(1)}%`, { sticky: true })
        .addTo(miniMap);
    });
  }

  // Donut target
  const ctx = document.getElementById('chart-donut-resumen');
  if (ctx && !Chart.getChart(ctx)) {
    new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Auditada (0)','Glosada (1)','Devuelta (2)'],
        datasets: [{ data: [87.2, 6.2, 6.6], backgroundColor: [C.navy, C.red, C.orange], borderWidth: 0, hoverOffset: 6 }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: '70%',
        plugins: {
          legend: { position: 'bottom', labels: { padding: 14, boxWidth: 11, font: { size: 10 } } },
          tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.toFixed(1)}%` } }
        }
      }
    });
  }

  // Top risk list
  const el = document.getElementById('top-risk-list');
  if (el && !el.children.length) {
    const top = MUNS.filter(m => m.cat === 'critico' || m.cat === 'alto').sort((a,b) => b.tasa - a.tasa);
    el.innerHTML = top.map(m => `
      <div class="trisk-item" style="border-left:3px solid ${riskColor(m.tasa)}">
        <span class="trisk-name">${m.nombre}</span>
        <span class="trisk-rate" style="color:${riskColor(m.tasa)}">${m.tasa.toFixed(1)}%</span>
      </div>`).join('');
  }
}

// ── MAPA RIESGO ────────────────────────────────────────────────

let mapRiesgo = null;
let riskMarkers = [];
let riskMode = 'size';

function initMapaRiesgo() {
  if (mapRiesgo) { setTimeout(() => mapRiesgo.invalidateSize(), 100); return; }

  mapRiesgo = L.map('map-riesgo', { zoomControl: true }).setView([6.8, -75.5], 7);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap © CARTO', maxZoom: 18
  }).addTo(mapRiesgo);

  // Add radio reference circle at media global
  MUNS.forEach(m => {
    const r = Math.max(10, Math.min(40, Math.log10(m.facturas) * 5));
    const marker = L.circleMarker([m.lat, m.lng], {
      radius: r, fillColor: riskColor(m.tasa), color: '#fff',
      weight: 1.5, opacity: 1, fillOpacity: 0.82
    });

    marker.bindPopup(buildMapPopup(m));
    marker.on('click', () => showMapDetail(m));
    marker.addTo(mapRiesgo);
    riskMarkers.push({ marker, m });
  });

  // Tabla
  buildRiskTable();
}

function buildMapPopup(m) {
  return `<div>
    <div class="lp-title">📍 ${m.nombre}</div>
    <div class="lp-row"><span>Tasa de Glosa</span><span class="lp-val" style="color:${riskColor(m.tasa)}">${m.tasa.toFixed(1)}%</span></div>
    <div class="lp-row"><span>N° Facturas</span><span class="lp-val">${m.facturas.toLocaleString('es-CO')}</span></div>
    <div class="lp-row"><span>vs Media (7.6%)</span><span class="lp-val" style="color:${m.tasa > 7.6 ? C.red : C.green}">${((m.tasa-7.6)/7.6*100).toFixed(0)}%</span></div>
    <div class="lp-row"><span>Categoría</span><span class="lp-val">${m.cat.charAt(0).toUpperCase()+m.cat.slice(1)}</span></div>
  </div>`;
}

function showMapDetail(m) {
  const panel = document.getElementById('map-detail-panel');
  if (!panel) return;
  const vsMedia = ((m.tasa - 7.6) / 7.6 * 100);
  panel.innerHTML = `
    <div class="det-title">📍 ${m.nombre}</div>
    <div class="det-row"><span class="det-key">Tasa de glosa</span><span class="det-val" style="color:${riskColor(m.tasa)}">${m.tasa.toFixed(1)}%</span></div>
    <div class="det-row"><span class="det-key">N° facturas</span><span class="det-val">${m.facturas.toLocaleString('es-CO')}</span></div>
    <div class="det-row"><span class="det-key">vs Media global</span><span class="det-val" style="color:${vsMedia > 0 ? C.red : C.green}">${vsMedia > 0 ? '+' : ''}${vsMedia.toFixed(0)}%</span></div>
    <div class="det-row"><span class="det-key">Categoría</span><span class="det-val">${catBadgeHTML(m.cat)}</span></div>
    <div class="det-row"><span class="det-key">Coordenadas</span><span class="det-val">${m.lat.toFixed(4)}, ${m.lng.toFixed(4)}</span></div>
  `;
}

function setRiskLayer(mode) {
  riskMode = mode;
  document.getElementById('btn-size').classList.toggle('active', mode === 'size');
  document.getElementById('btn-heat').classList.toggle('active', mode === 'heat');

  riskMarkers.forEach(({ marker, m }) => {
    const r = mode === 'size'
      ? Math.max(10, Math.min(40, Math.log10(m.facturas) * 5))
      : Math.max(10, Math.min(40, m.tasa * 2.5));
    marker.setStyle({ radius: r });
  });
}

function buildRiskTable() {
  const tbody = document.getElementById('tbody-riesgo-full');
  if (!tbody || tbody.children.length > 0) return;
  const sorted = [...MUNS].sort((a,b) => b.tasa - a.tasa);
  tbody.innerHTML = sorted.map((m, i) => {
    const vs = ((m.tasa - 7.6) / 7.6 * 100).toFixed(0);
    const vsStr = parseFloat(vs) > 0 ? `+${vs}%` : `${vs}%`;
    return `<tr>
      <td style="font-weight:700;color:${C.muted}">${i+1}</td>
      <td style="font-weight:700;color:${C.navy}">${m.nombre}</td>
      <td style="font-weight:800;color:${riskColor(m.tasa)};font-size:14px">${m.tasa.toFixed(1)}%</td>
      <td style="font-weight:600;color:${C.muted}">${m.facturas.toLocaleString('es-CO')}</td>
      <td style="font-weight:700;color:${m.tasa > 7.6 ? C.red : C.green}">${vsStr}</td>
      <td>${catBadgeHTML(m.cat)}</td>
    </tr>`;
  }).join('');
}

// ── MAPA IPS ───────────────────────────────────────────────────

let mapIPS = null;
let ipsLayerGroup = null;
let distLayerGroup = null;
let ipsMode = 'ips';

// IPS level colors
const IPS_COLORS = { 1: '#2F9E44', 2: '#F59F00', 3: '#E03131' };
const IPS_LABELS = { 1: 'Nivel 1 — Primaria', 2: 'Nivel 2 — Especialista', 3: 'Nivel 3 — Alta Complejidad' };

function initMapaIPS() {
  if (mapIPS) { setTimeout(() => mapIPS.invalidateSize(), 100); return; }

  mapIPS = L.map('map-ips', { zoomControl: true }).setView([6.8, -75.5], 7);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap © CARTO', maxZoom: 18
  }).addTo(mapIPS);

  // IPS markers layer
  ipsLayerGroup = L.layerGroup();
  IPS_SEDES.forEach(ips => {
    const icon = L.divIcon({
      className: '',
      html: `<div style="width:14px;height:14px;border-radius:50%;background:${IPS_COLORS[ips.nivel]};border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.3)"></div>`,
      iconSize: [14,14], iconAnchor: [7,7]
    });
    const m = L.marker([ips.lat, ips.lng], { icon });
    m.bindPopup(`<div>
      <div class="lp-title">🏥 ${ips.nombre}</div>
      <div class="lp-row"><span>Municipio</span><span class="lp-val">${ips.municipio}</span></div>
      <div class="lp-row"><span>Nivel</span><span class="lp-val" style="color:${IPS_COLORS[ips.nivel]}">${IPS_LABELS[ips.nivel]}</span></div>
      <div class="lp-row"><span>Sedes</span><span class="lp-val">${ips.sedes}</span></div>
    </div>`);
    ipsLayerGroup.addLayer(m);
  });

  // Add municipality reference circles (faint)
  MUNS.forEach(m => {
    L.circleMarker([m.lat, m.lng], {
      radius: 6, fillColor: riskColor(m.tasa), color: 'transparent', fillOpacity: 0.3
    }).bindTooltip(m.nombre, { sticky: true }).addTo(mapIPS);
  });

  ipsLayerGroup.addTo(mapIPS);

  // Distance lines layer (afiliado → IPS)
  distLayerGroup = L.layerGroup();
  // Visualize distance from Medellín afiliados to each IPS (simulation)
  const medellin = MUNS.find(m => m.id === 'medellin');
  const turbo    = MUNS.find(m => m.id === 'turbo');
  const vigia    = MUNS.find(m => m.id === 'vigia');

  // Sample: local afiliado (close)
  L.polyline([[medellin.lat, medellin.lng], [6.2490, -75.5801]], {
    color: '#2F9E44', weight: 2, opacity: 0.7, dashArray: '6,4'
  }).bindTooltip('Afiliado Medellín → Clínica Las Américas · 3.2 km').addTo(distLayerGroup);

  // Sample: medium distance afiliados
  L.polyline([[turbo.lat, turbo.lng], [7.8900, -76.6210]], {
    color: '#F59F00', weight: 2.5, opacity: 0.7, dashArray: '6,4'
  }).bindTooltip('Afiliado Turbo → Hospital Apartadó · 48 km').addTo(distLayerGroup);

  // Sample: far afiliados (rural)
  L.polyline([[vigia.lat, vigia.lng], [8.0989, -76.7278]], {
    color: '#E03131', weight: 3, opacity: 0.8, dashArray: '6,4'
  }).bindTooltip('Afiliado Vigía del Fuerte → IPS Turbo · 121 km 🔴', { sticky: true }).addTo(distLayerGroup);

  // Add sample afiliado points
  [[medellin.lat, medellin.lng], [turbo.lat, turbo.lng], [vigia.lat, vigia.lng]].forEach((c, i) => {
    const colors = ['#2F9E44','#F59F00','#E03131'];
    L.circleMarker(c, { radius: 7, fillColor: colors[i], color: '#fff', weight: 2, fillOpacity: 1 })
      .bindTooltip(['Afiliado (cerca)','Afiliado (medio)','Afiliado (lejos)'][i])
      .addTo(distLayerGroup);
  });

  // Dist chart
  const ctx2 = document.getElementById('chart-dist-ips');
  if (ctx2 && !Chart.getChart(ctx2)) {
    new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: ['0-5 km','5-20 km','20-50 km','50-100 km','100-200 km','200+ km'],
        datasets: [{ data: [71.2,12.4,8.1,4.8,2.2,1.3],
          backgroundColor: ['#2F9E44','#74C476','#F59F00','#F59F00','#E03131','#7B0000'],
          borderRadius: 5, borderSkipped: false }]
      },
      options: {
        responsive: true, maintainAspectRatio: true,
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => ` ${c.parsed.y}% de afiliados` } } },
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: 9 } } },
          y: { grid: { color: C.grid }, ticks: { callback: v => v + '%', font: { size: 10 } } }
        }
      }
    });
  }

  // IPS density list
  const el = document.getElementById('ips-density-list');
  if (el && !el.children.length) {
    const top = [
      { nombre:'Medellín', val:6200 }, { nombre:'Bello', val:1840 }, { nombre:'Itagüí', val:1250 },
      { nombre:'Envigado', val:980 },  { nombre:'Rionegro', val:720 }, { nombre:'Caldas', val:680 },
      { nombre:'Apartadó', val:450 }, { nombre:'Caucasia', val:210 },
    ];
    const max = top[0].val;
    el.innerHTML = top.map(d => `
      <div class="ips-d-item">
        <div style="width:72px;font-size:11px;font-weight:600;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${d.nombre}</div>
        <div class="ips-d-bar"><div class="ips-d-fill" style="width:${(d.val/max*100).toFixed(0)}%"></div></div>
        <div class="ips-d-val">${d.val >= 1000 ? (d.val/1000).toFixed(1)+'K' : d.val}</div>
      </div>`).join('');
  }
}

function setIpsLayer(mode) {
  ipsMode = mode;
  document.getElementById('btn-ips').classList.toggle('active', mode === 'ips');
  document.getElementById('btn-dist').classList.toggle('active', mode === 'dist');
  if (mode === 'ips') {
    if (distLayerGroup) mapIPS.removeLayer(distLayerGroup);
    if (ipsLayerGroup)  mapIPS.addLayer(ipsLayerGroup);
  } else {
    if (ipsLayerGroup)  mapIPS.removeLayer(ipsLayerGroup);
    if (distLayerGroup) mapIPS.addLayer(distLayerGroup);
  }
}

// ── MAPA GLOSA ─────────────────────────────────────────────────

let mapGlosa = null;

function initMapaGlosa() {
  // Bubble chart
  const ctx1 = document.getElementById('chart-bubble-glosa');
  if (ctx1 && !Chart.getChart(ctx1)) {
    const datasets = MUNS.map(m => ({
      label: m.nombre,
      data: [{ x: m.facturas, y: m.tasa, r: Math.max(5, Math.min(30, Math.log10(m.facturas) * 4)) }],
      backgroundColor: riskColor(m.tasa) + 'aa',
      borderColor: riskColor(m.tasa), borderWidth: 1.5,
    }));
    new Chart(ctx1, {
      type: 'bubble',
      data: { datasets },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: {
            title: items => items[0].dataset.label,
            label: item => [` Tasa: ${item.parsed.y.toFixed(1)}%`, ` Facturas: ${item.parsed.x.toLocaleString('es-CO')}`]
          }}
        },
        scales: {
          x: { grid: { color: C.grid }, title: { display:true, text:'N° Facturas', font:{size:11} },
               ticks: { callback: v => v >= 1e6 ? (v/1e6).toFixed(1)+'M' : (v/1e3).toFixed(0)+'K' } },
          y: { grid: { color: C.grid }, title: { display:true, text:'Tasa Glosa (%)', font:{size:11} },
               ticks: { callback: v => v + '%' }, min:0, max:24 }
        }
      }
    });
  }

  // Mapa glosa — foco norte Antioquia (alta tasa)
  if (!mapGlosa) {
    mapGlosa = L.map('map-glosa', { zoomControl: false }).setView([7.2, -75.8], 7);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '© CartoDB', maxZoom: 18
    }).addTo(mapGlosa);

    MUNS.forEach(m => {
      const r = Math.max(8, Math.min(35, m.tasa * 2.2));
      L.circleMarker([m.lat, m.lng], {
        radius: r, fillColor: riskColor(m.tasa), color: '#fff',
        weight: 1.5, opacity: 1, fillOpacity: 0.85
      }).bindTooltip(`<b>${m.nombre}</b><br>Glosa: <b style="color:${riskColor(m.tasa)}">${m.tasa.toFixed(1)}%</b>`, { sticky: true })
        .addTo(mapGlosa);
    });

    // Labels for critical municipalities
    MUNS.filter(m => m.cat === 'critico').forEach(m => {
      L.tooltip({ permanent: true, direction:'right', className:'leaflet-tooltip' })
        .setLatLng([m.lat, m.lng])
        .setContent(`<span style="font-size:9px;font-weight:800;color:#7B0000">${m.nombre}</span>`)
        .addTo(mapGlosa);
    });
  }

  // Correlación chart
  const ctx3 = document.getElementById('chart-corr-glosa');
  if (ctx3 && !Chart.getChart(ctx3)) {
    const labels = ['glosa_rate_municipio','densidad_ips_municipio','nivel_atencion_ips','misma_municipio_afiliado_ips','distancia_afiliado_ips_km','lejos_de_ips'];
    const vals   = [0.076, 0.040, -0.009, -0.010, -0.025, -0.031];
    new Chart(ctx3, {
      type: 'bar',
      data: {
        labels,
        datasets: [{ data: vals, backgroundColor: vals.map(v => v > 0 ? C.red+'bb' : C.blue+'bb'),
          borderColor: vals.map(v => v > 0 ? C.red : C.blue), borderWidth: 1, borderRadius: 4, borderSkipped: false }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, indexAxis: 'y',
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => ` Pearson: ${c.parsed.x.toFixed(4)}` } } },
        scales: {
          x: { grid: { color: C.grid }, ticks: { callback: v => v.toFixed(2) } },
          y: { grid: { display: false }, ticks: { font: { size: 10 } } }
        }
      }
    });
  }

  // Nivel atención chart
  const ctx4 = document.getElementById('chart-nivel-glosa');
  if (ctx4 && !Chart.getChart(ctx4)) {
    new Chart(ctx4, {
      type: 'doughnut',
      data: {
        labels: ['Nivel 1 — Primaria','Nivel 2 — Especialista','Nivel 3 — Alta Complejidad'],
        datasets: [{ data: [68.4, 24.7, 6.9], backgroundColor: ['#2F9E44','#F59F00','#E03131'], borderWidth: 0, hoverOffset: 6 }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: '65%',
        plugins: {
          legend: { position: 'bottom', labels: { padding: 12, boxWidth: 11, font: { size: 10 } } },
          tooltip: { callbacks: { label: c => ` ${c.parsed.toFixed(1)}% de facturas` } }
        }
      }
    });
  }
}

// ── FEATURES ───────────────────────────────────────────────────

function initFeatures() {
  const SHAP = {
    labels: ['glosa_rate_municipio','nivel_sisben','genero_enc','densidad_ips_municipio',
             'edad','grupo_poblacional_enc','distancia_afiliado_ips_km','zona_afiliado_enc',
             'regimen_enc','nivel_atencion_ips','lejos_de_ips','misma_municipio_afiliado_ips',
             'hhi_dx_municipio','sin_cobertura_savia'],
    vals:   [0.109,0.071,0.062,0.061,0.059,0.032,0.021,0.009,0.008,0.0018,0.0014,0.0002,0.0001,0.00004],
    isGeo:  [true,false,false,true,false,false,true,false,false,true,true,true,true,true]
  };

  const ctx1 = document.getElementById('chart-shap-main');
  if (ctx1 && !Chart.getChart(ctx1)) {
    const labs = [...SHAP.labels].reverse();
    const vals = [...SHAP.vals].reverse();
    const geo  = [...SHAP.isGeo].reverse();
    new Chart(ctx1, {
      type: 'bar',
      data: {
        labels: labs,
        datasets: [{ data: vals,
          backgroundColor: geo.map(g => g ? C.red+'cc' : C.blue+'cc'),
          borderColor:     geo.map(g => g ? C.red : C.blue),
          borderWidth: 1, borderRadius: 4, borderSkipped: false }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, indexAxis: 'y',
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: c => ` SHAP: ${c.parsed.x.toFixed(4)} · ${geo[c.dataIndex] ? '🌍 Geoespacial' : '👤 Socioeconómica'}` } }
        },
        scales: {
          x: { grid: { color: C.grid }, ticks: { callback: v => v.toFixed(3) } },
          y: { grid: { display: false }, ticks: { font: { size: 10 } } }
        }
      }
    });
  }

  const ctx2 = document.getElementById('chart-corr-feat');
  if (ctx2 && !Chart.getChart(ctx2)) {
    const labels = ['glosa_rate','densidad_ips','nivel_atencion','misma_municipio','distancia_km','lejos_de_ips'];
    const vals   = [0.076, 0.040, -0.009, -0.010, -0.025, -0.031];
    new Chart(ctx2, {
      type: 'bar',
      data: {
        labels,
        datasets: [{ data: vals,
          backgroundColor: vals.map(v => v > 0 ? C.red+'bb' : C.blue+'bb'),
          borderColor: vals.map(v => v > 0 ? C.red : C.blue),
          borderWidth: 1, borderRadius: 4, borderSkipped: false }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, indexAxis: 'y',
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: C.grid } },
          y: { grid: { display: false }, ticks: { font: { size: 9 } } }
        }
      }
    });
  }
}

// ── PREDICCIÓN ─────────────────────────────────────────────────

let mapPred = null;
let predMarker = null;
let predDistLine = null;

const MUN_GEO = {};
MUNS.forEach(m => { MUN_GEO[m.id] = m; });

function initPrediccion() {
  if (mapPred) { setTimeout(() => mapPred.invalidateSize(), 100); return; }

  mapPred = L.map('map-pred', { zoomControl: false }).setView([6.2518, -75.5636], 9);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '© CartoDB', maxZoom: 18
  }).addTo(mapPred);

  // Background municipalities
  MUNS.forEach(m => {
    L.circleMarker([m.lat, m.lng], {
      radius: 5, fillColor: riskColor(m.tasa), color: 'transparent', fillOpacity: 0.25
    }).addTo(mapPred);
  });

  updatePredMap();
}

function updatePredMap() {
  if (!mapPred) return;
  const munId = document.getElementById('pred-mun')?.value || 'medellin';
  const mun   = MUN_GEO[munId] || MUN_GEO['medellin'];
  const nivel = parseInt(document.getElementById('pred-nivel')?.value || '1');

  if (predMarker) mapPred.removeLayer(predMarker);
  if (predDistLine) mapPred.removeLayer(predDistLine);

  // Afiliado marker
  predMarker = L.circleMarker([mun.lat, mun.lng], {
    radius: 12, fillColor: riskColor(mun.tasa), color: '#fff', weight: 3, fillOpacity: 1
  }).bindPopup(`<div><div class="lp-title">📍 Afiliado · ${mun.nombre}</div><div class="lp-row"><span>Tasa glosa municipio</span><span class="lp-val" style="color:${riskColor(mun.tasa)}">${mun.tasa.toFixed(1)}%</span></div></div>`)
    .addTo(mapPred);

  // Nearest IPS (simulated by picking closest)
  let nearestIPS = IPS_SEDES.filter(i => i.nivel === nivel)[0] || IPS_SEDES[0];
  let minDist = Infinity;
  IPS_SEDES.filter(i => i.nivel === nivel).forEach(ips => {
    const d = Math.sqrt(Math.pow(ips.lat - mun.lat, 2) + Math.pow(ips.lng - mun.lng, 2));
    if (d < minDist) { minDist = d; nearestIPS = ips; }
  });

  // Distance line
  predDistLine = L.polyline([[mun.lat, mun.lng], [nearestIPS.lat, nearestIPS.lng]], {
    color: riskColor(mun.tasa), weight: 2.5, opacity: 0.8, dashArray: '8,5'
  }).bindTooltip(`Dist. estimada: ${(minDist * 111).toFixed(1)} km`, { sticky: true })
    .addTo(mapPred);

  // IPS marker
  L.circleMarker([nearestIPS.lat, nearestIPS.lng], {
    radius: 8, fillColor: IPS_COLORS[nivel], color: '#fff', weight: 2, fillOpacity: 1
  }).bindTooltip(`🏥 ${nearestIPS.nombre}`).addTo(mapPred);

  mapPred.setView([mun.lat, mun.lng], 9);
}

function updateDistLine() { updatePredMap(); }

function ejecutarPrediccion() {
  const munId    = document.getElementById('pred-mun').value;
  const sisben   = parseInt(document.getElementById('pred-sisben').value);
  const edad     = parseInt(document.getElementById('pred-edad').value);
  const nivel    = parseInt(document.getElementById('pred-nivel').value);
  const distKm   = parseInt(document.getElementById('pred-dist').value);
  const mun      = MUN_GEO[munId] || MUN_GEO['medellin'];

  // Score basado en features SHAP del modelo
  let sGlosa = mun.tasa / 100;
  sGlosa += sisben === 1 ? 0.04 : sisben === 2 ? 0.02 : sisben === 3 ? 0.01 : -0.01;
  if (edad > 60)     sGlosa += 0.04;
  else if (edad > 45) sGlosa += 0.02;
  else if (edad < 18) sGlosa += 0.01;
  if (nivel === 3) sGlosa += 0.05;
  else if (nivel === 2) sGlosa += 0.02;
  if (distKm > 100) sGlosa -= 0.02;
  sGlosa = Math.max(0.02, Math.min(0.6, sGlosa));

  const sDev     = Math.max(0.02, 0.05 + nivel * 0.01 + (mun.tasa > 13 ? 0.04 : 0));
  const sAud     = Math.max(0.02, 1 - sGlosa - sDev);
  const tot      = sAud + sGlosa + sDev;
  const probs    = { aud: sAud/tot, glos: sGlosa/tot, dev: sDev/tot };
  const classes  = ['aud','glos','dev'];
  const maxC     = classes.reduce((a,b) => probs[a] > probs[b] ? a : b);
  const cLabels  = { aud:'✅ Auditada (0)', glos:'⚠️ Glosada (1)', dev:'🔁 Devuelta (2)' };
  const cColors  = { aud: C.blue, glos: C.red, dev: C.orange };

  document.getElementById('pred-wait-card').style.display = 'none';
  const rc = document.getElementById('pred-result-card');
  rc.style.display = 'block'; rc.style.animation = 'none'; rc.offsetHeight; rc.style.animation = 'page-in .25s ease both';

  document.getElementById('res-class-label').textContent = cLabels[maxC];
  document.getElementById('res-class-label').style.color = cColors[maxC];
  document.getElementById('res-prob-big').textContent = (probs[maxC]*100).toFixed(1) + '%';
  document.getElementById('res-prob-big').style.color = cColors[maxC];

  document.getElementById('prob-bars').innerHTML = [
    { key:'aud', lbl:'Auditada', color: C.blue   },
    { key:'glos',lbl:'Glosada',  color: C.red    },
    { key:'dev', lbl:'Devuelta', color: C.orange  },
  ].map(b => `
    <div class="pb-row">
      <div class="pb-lbl">${b.lbl}</div>
      <div class="pb-track"><div class="pb-fill" style="width:${(probs[b.key]*100).toFixed(1)}%;background:${b.color}"></div></div>
      <div class="pb-val">${(probs[b.key]*100).toFixed(1)}%</div>
    </div>`).join('');

  const factors = [];
  if (mun.tasa > 13) factors.push({ lv:'high',   tx:`🌍 Municipio crítico · ${mun.tasa.toFixed(1)}% tasa glosa` });
  else if (mun.tasa > 7.6) factors.push({ lv:'medium', tx:`🌍 Municipio moderado · ${mun.tasa.toFixed(1)}%` });
  else factors.push({ lv:'low', tx:`🌍 Municipio bajo riesgo · ${mun.tasa.toFixed(1)}%` });
  if (nivel === 3) factors.push({ lv:'high', tx:`🏥 IPS Nivel 3 · Mayor frecuencia de inconsistencias formales` });
  if (sisben === 1) factors.push({ lv:'medium', tx:`👤 SISBEN I · Alta vulnerabilidad socioeconómica` });
  if (edad > 60) factors.push({ lv:'medium', tx:`👴 Adulto mayor (${edad} años) · Uso frecuente de prestación` });
  if (distKm > 100) factors.push({ lv:'low', tx:`📍 Distancia ${distKm} km · Afiliado lejos de su IPS` });

  document.getElementById('risk-tags').innerHTML = factors.map(f =>
    `<div class="risk-tag ${f.lv}">${f.tx}</div>`).join('');

  updatePredMap();
}

// ── Init ────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  inited['resumen'] = true;
  Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
  Chart.defaults.color = C.muted;
  setTimeout(initResumen, 80);
});
