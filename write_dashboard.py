#!/usr/bin/env python3
"""
write_dashboard.py — Writes the new dual-map electoral dashboard HTML to:
  public/index.html
  colombia_electoral_2026.html
"""
import os, textwrap

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Atlas Electoral Colombia 2022&#8211;2026</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0d1117;color:#e6edf3;font-family:'Segoe UI',system-ui,sans-serif;height:100vh;display:flex;flex-direction:column;overflow:hidden}
header{background:#161b22;border-bottom:1px solid #30363d;padding:8px 18px;display:flex;align-items:center;gap:14px;flex-shrink:0;flex-wrap:wrap}
header h1{font-size:1rem;font-weight:700;color:#58a6ff;white-space:nowrap}
header .sub{font-size:.76rem;color:#8b949e}
#live-badge{background:#238636;color:#fff;font-size:.68rem;font-weight:700;padding:2px 8px;border-radius:10px;animation:pulse 2s infinite;white-space:nowrap}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
#update-time{font-size:.68rem;color:#8b949e;margin-left:auto;white-space:nowrap}
nav{background:#161b22;border-bottom:1px solid #30363d;display:flex;flex-shrink:0}
nav button{background:none;border:none;border-bottom:3px solid transparent;color:#8b949e;cursor:pointer;padding:9px 18px;font-size:.82rem;font-weight:600;transition:.2s;white-space:nowrap}
nav button:hover{color:#e6edf3;background:#1c2128}
nav button.active{color:#58a6ff;border-bottom-color:#58a6ff}
#filterbar{background:#161b22;border-bottom:1px solid #30363d;padding:6px 14px;display:flex;align-items:center;gap:14px;flex-shrink:0;flex-wrap:wrap}
#filterbar label{font-size:.75rem;color:#8b949e}
#filterbar select{background:#21262d;border:1px solid #30363d;color:#e6edf3;padding:3px 8px;border-radius:5px;font-size:.75rem;cursor:pointer}
#filterbar select:focus{outline:none;border-color:#58a6ff}
#filterbar select:disabled{opacity:.45;cursor:default}
#api-status{font-size:.72rem;margin-left:4px}
#main{flex:1;display:flex;min-height:0;overflow:hidden}
#left-panel{flex:1;display:flex;flex-direction:column;min-width:0;overflow:hidden}
#maps-area{flex:1;display:grid;grid-template-columns:1fr 1fr;gap:4px;padding:6px;min-height:0}
.map-container{display:flex;flex-direction:column;min-height:0;background:#161b22;border:1px solid #30363d;border-radius:7px;overflow:hidden}
.map-header{padding:5px 11px;background:#1c2128;border-bottom:1px solid #30363d;font-size:.75rem;color:#8b949e;display:flex;align-items:center;gap:7px;flex-shrink:0}
.map-header strong{color:#e6edf3;font-size:.78rem}
.mhd{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.map-wrapper{flex:1;position:relative;min-height:200px}
.map-wrapper .leaflet-container{position:absolute!important;inset:0;background:#0d1117!important}
#curules-area{padding:6px 14px 8px;background:#161b22;border-top:1px solid #30363d;flex-shrink:0}
#curules-area h3{font-size:.74rem;color:#8b949e;margin-bottom:5px}
.curules-bar{display:flex;height:24px;border-radius:4px;overflow:hidden;gap:1px}
.curules-seg{display:flex;align-items:center;justify-content:center;font-size:.62rem;font-weight:700;color:#fff;min-width:0;overflow:hidden;cursor:pointer}
.curules-seg span{white-space:nowrap;padding:0 3px;overflow:hidden;text-overflow:ellipsis}
.curules-legend{display:flex;flex-wrap:wrap;gap:8px;margin-top:5px}
.cleg-item{display:flex;align-items:center;gap:4px;font-size:.65rem;color:#8b949e}
.cleg-item .cdot{width:8px;height:8px;border-radius:2px;flex-shrink:0}
#right-panel{width:290px;flex-shrink:0;background:#161b22;border-left:1px solid #30363d;display:flex;flex-direction:column;overflow:hidden}
.rp-head{font-size:.78rem;color:#8b949e;padding:8px 13px 5px;border-bottom:1px solid #30363d;flex-shrink:0}
.chart-section{flex:1;padding:8px 10px;min-height:0;display:flex;flex-direction:column;gap:4px;overflow:hidden}
.chart-section h4{font-size:.72rem;color:#8b949e;flex-shrink:0}
.chart-wrap{flex:1;position:relative;min-height:100px;max-height:46%}
.map-legend{background:rgba(22,27,34,.92);border:1px solid #30363d;border-radius:6px;padding:6px 10px;font-size:.65rem;max-width:170px}
.map-legend h4{color:#8b949e;margin-bottom:3px;font-size:.65rem}
.leg-item{display:flex;align-items:center;gap:5px;margin:2px 0;white-space:nowrap;overflow:hidden}
.leg-color{width:11px;height:11px;border-radius:2px;flex-shrink:0}
.spinner{display:inline-block;width:11px;height:11px;border:2px solid #30363d;border-top-color:#58a6ff;border-radius:50%;animation:spin .7s linear infinite;vertical-align:middle}
@keyframes spin{to{transform:rotate(360deg)}}
.dept-tooltip{background:#1c2128;border:1px solid #30363d;border-radius:6px;padding:7px 11px;font-size:.75rem;color:#e6edf3;pointer-events:none;box-shadow:0 4px 16px rgba(0,0,0,.6)}
.dept-tooltip strong{display:block;margin-bottom:3px;font-size:.8rem}
@media(max-width:850px){
  #main{flex-direction:column}
  #right-panel{width:100%;max-height:260px;border-left:none;border-top:1px solid #30363d}
  #maps-area{grid-template-columns:1fr}
}
</style>
</head>
<body>

<header>
  <h1>&#127758; Atlas Electoral Colombia 2022&#8211;2026</h1>
  <span class="sub">Comparativa departamental</span>
  <span id="live-badge">&#9679; EN VIVO 2026</span>
  <span id="update-time"></span>
</header>

<nav>
  <button class="active" data-tab="congreso">&#128203; Congreso 2022 vs 2026</button>
  <button data-tab="presidencial">&#127963; Presidenciales 2022</button>
  <button data-tab="consulta_ph">&#9889; PH Consulta 2025 vs 2026</button>
</nav>

<div id="filterbar">
  <label>Corporaci&#243;n:</label>
  <select id="sel-corp">
    <option value="camara">C&#225;mara de Representantes</option>
    <option value="senado">Senado</option>
  </select>
  <label>Orientaci&#243;n:</label>
  <select id="sel-orient">
    <option value="todas">Todas</option>
    <option value="Izquierda">Izquierda</option>
    <option value="Centroizquierda">Centroizquierda</option>
    <option value="Centro">Centro</option>
    <option value="Centroderecha">Centroderecha</option>
    <option value="Derecha">Derecha</option>
  </select>
  <span id="api-status"></span>
</div>

<div id="main">
  <div id="left-panel">
    <div id="maps-area">
      <div class="map-container">
        <div class="map-header">
          <div class="mhd" style="background:#58a6ff"></div>
          <strong id="left-title">Cargando...</strong>
        </div>
        <div class="map-wrapper"><div id="map-left" style="width:100%;height:100%"></div></div>
      </div>
      <div class="map-container">
        <div class="map-header">
          <div class="mhd" style="background:#3fb950"></div>
          <strong id="right-title">Cargando...</strong>
          <span class="spinner" id="right-spinner" style="display:none;margin-left:4px"></span>
        </div>
        <div class="map-wrapper"><div id="map-right" style="width:100%;height:100%"></div></div>
      </div>
    </div>

    <div id="curules-area">
      <h3>Votos por partido <span id="curules-subtitle" style="color:#8b949e;font-weight:400;font-size:.68rem"></span></h3>
      <div class="curules-bar" id="curules-bar"></div>
      <div class="curules-legend" id="curules-legend"></div>
    </div>
  </div>

  <div id="right-panel">
    <div class="rp-head" id="chart-panel-title">Resultados Nacionales</div>
    <div class="chart-section">
      <h4 id="chart-nat-title">Nacional</h4>
      <div class="chart-wrap"><canvas id="chart-national"></canvas></div>
      <h4 id="chart-dept-title" style="margin-top:6px;color:#8b949e">Haga clic en un departamento</h4>
      <div class="chart-wrap"><canvas id="chart-dept"></canvas></div>
    </div>
  </div>
</div>

<script>
'use strict';

// ═══════════════════════════════════════════════════════════
// AMB (4-digit registraduria) → DPTO (2-digit geojson)
// ═══════════════════════════════════════════════════════════
const AMB_TO_DPTO = {
  '6000':'91','0100':'05','4000':'81','0300':'08','1600':'11','0500':'13',
  '0700':'15','0900':'17','4400':'18','1100':'19','1200':'20','1700':'27',
  '8800':null,'1300':'23','1500':'25','5000':'94','5400':'95','1900':'41',
  '4800':'44','2100':'47','5200':'50','2300':'52','2500':'54','2600':'63',
  '2400':'66','2700':'68','2800':'70','2900':'73','3100':'76','4600':'85',
  '6400':'86','5600':'88','6800':'97','7200':'99'
};
const DPTO_TO_AMB = Object.fromEntries(
  Object.entries(AMB_TO_DPTO).filter(([,v])=>v).map(([k,v])=>[v,k])
);

// ═══════════════════════════════════════════════════════════
// PARTY CATALOG: codpar (string) → {name, color, ori}
// ═══════════════════════════════════════════════════════════
const PC = {
  '2': {n:'Partido Liberal',         c:'#e85d04', o:'Centroizquierda'},
  '3': {n:'P. Conservador',          c:'#1864ab', o:'Centroderecha'},
  '4': {n:'Partido de la U',         c:'#e67700', o:'Centro'},
  '5': {n:'Partido de la U',         c:'#e67700', o:'Centro'},
  '6': {n:'MAIS',                    c:'#2b8a3e', o:'Izquierda'},
  '7': {n:'MIRA',                    c:'#9c36b5', o:'Centro'},
  '8': {n:'ASI',                     c:'#495057', o:'Centro'},
  '9': {n:'La Fuerza de la Paz',     c:'#d63384', o:'Izquierda'},
  '10':{n:'Cambio Radical',          c:'#0c7ead', o:'Centroderecha'},
  '15':{n:'Mov. MIO',                c:'#20c997', o:'Centro'},
  '16':{n:'Fuerza y Corazon',        c:'#fd7e14', o:'Centroderecha'},
  '17':{n:'Centro Democratico',      c:'#1e2b4a', o:'Derecha'},
  '20':{n:'Opcion Ciudadana',        c:'#74b9ff', o:'Centro'},
  '22':{n:'Somos Region',            c:'#74c69d', o:'Centro'},
  '26':{n:'MAIS Narino',             c:'#2b8a3e', o:'Izquierda'},
  '33':{n:'Col. Progresista',        c:'#f72585', o:'Izquierda'},
  '35':{n:'AAU',                     c:'#7209b7', o:'Centro'},
  '38':{n:'Pacto Historico',         c:'#c92a2a', o:'Izquierda'},
  '41':{n:'Mov. Politico Regional',  c:'#6ea8fe', o:'Centro'},
  '42':{n:'Mov. Verde Oxigeno',      c:'#2b8a3e', o:'Centro'},
  '45':{n:'Colombia Humana Reg.',    c:'#c92a2a', o:'Izquierda'},
  '46':{n:'Mov. Alternativo',        c:'#6ea8fe', o:'Izquierda'},
  '51':{n:'Partido Liberal Reg.',    c:'#e85d04', o:'Centroizquierda'},
  '52':{n:'Alianza Verde',           c:'#2f9e44', o:'Centroizquierda'},
  '53':{n:'Pacto Historico',         c:'#c92a2a', o:'Izquierda'},
  '54':{n:'Nuevo Liberalismo Reg.',  c:'#fd7e14', o:'Centro'},
  '58':{n:'Col. Justa Libres',       c:'#5f3dc4', o:'Derecha'},
  '59':{n:'Col. Justa Libres',       c:'#5f3dc4', o:'Derecha'},
  '61':{n:'Mov. Independiente',      c:'#6f42c1', o:'Centro'},
  '65':{n:'Autoridades Trad.',       c:'#2b8a3e', o:'Izquierda'},
  '67':{n:'Uribe Uribe',             c:'#1e2b4a', o:'Derecha'},
  '71':{n:'Col. Humana Putumayo',    c:'#c92a2a', o:'Izquierda'},
  '78':{n:'Republica Comun',         c:'#1e2b4a', o:'Derecha'},
  '80':{n:'Somos Pacifico',          c:'#2b8a3e', o:'Centroizquierda'},
  '81':{n:'Colombia Somos Todos',    c:'#0c7ead', o:'Centro'},
  '84':{n:'Nuevo Liberalismo',       c:'#fd7e14', o:'Centro'},
  '85':{n:'Colombia Humana',         c:'#c92a2a', o:'Izquierda'},
  '86':{n:'Nuevo Liberalismo',       c:'#fd7e14', o:'Centro'},
  '89':{n:'Alianza Verde Reg.',      c:'#2f9e44', o:'Centroizquierda'},
  '90':{n:'Potencial Ciudadano',     c:'#6ea8fe', o:'Centro'},
  '91':{n:'Mov. Civico Cundinamarca',c:'#0c7ead', o:'Centro'},
  '93':{n:'Pacto Historico',         c:'#c92a2a', o:'Izquierda'},
  '96':{n:'Mov. Guajira',            c:'#adb5bd', o:'Centro'},
  '97':{n:'Mov. Ciudadano',          c:'#adb5bd', o:'Centro'},
  '98':{n:'AICO',                    c:'#2b8a3e', o:'Izquierda'},
  '99':{n:'Caqueta Primero',         c:'#6ea8fe', o:'Centro'},
  '103':{n:'Alianza Ciudadana',      c:'#6ea8fe', o:'Centro'},
  '107':{n:'Paz Colombia',           c:'#2b8a3e', o:'Centroizquierda'},
  '112':{n:'Col. Mas Segura',        c:'#0c7ead', o:'Centroderecha'},
  '113':{n:'Acierta Colombia',       c:'#6ea8fe', o:'Centro'},
  '119':{n:'Mov. Firmes',            c:'#adb5bd', o:'Centro'},
  '124':{n:'Centro Esperanza',       c:'#2b8a3e', o:'Centroizquierda'},
  '125':{n:'Mov. Quindio',           c:'#6ea8fe', o:'Centro'},
  '127':{n:'Mov. Putumayo',          c:'#2b8a3e', o:'Izquierda'},
  '139':{n:'Mov. Independiente',     c:'#adb5bd', o:'Centro'},
  '142':{n:'Mov. Risaralda',         c:'#fd7e14', o:'Centro'},
  '153':{n:'Mov. Sucre',             c:'#adb5bd', o:'Centro'},
  '156':{n:'Mov. Democratico',       c:'#adb5bd', o:'Centro'},
};
function getParty(codpar){
  return PC[String(codpar)]||{n:'Partido '+codpar,c:'#6e7681',o:'Centro'};
}

// Colors for historico.json named parties/candidates
const NAMED_COLORS = {
  'Pacto Historico':'#c92a2a','Pacto Hist\u00f3rico':'#c92a2a',
  'Partido Liberal':'#e85d04','P. Conservador':'#1864ab',
  'Partido Conservador':'#1864ab','Cambio Radical':'#0c7ead',
  'Centro Democratico':'#1e2b4a','Centro Democr\u00e1tico':'#1e2b4a',
  'Partido de la U':'#e67700','P. de la U':'#e67700',
  'Alianza Verde':'#2f9e44','Col. Justa Libres':'#5f3dc4',
  'Colombia Justa Libres':'#5f3dc4','Colombia Humana':'#c92a2a',
  'Nuevo Liberalismo':'#fd7e14','Centro Esperanza':'#2b8a3e',
  'Coalici\u00f3n Centro Esperanza':'#2b8a3e','Equipo por Colombia':'#1864ab',
  'Liga Gobernantes':'#f59e0b','Gustavo Petro':'#c92a2a',
  'Rodolfo Hern\u00e1ndez':'#f59e0b','Federico Guti\u00e9rrez':'#1864ab',
  'Ivan Cepeda Castro':'#c92a2a','Diana Carolina Corcho Mejia':'#e85d04',
  'Daniel Quintero Calle':'#f59e0b',
};
function namedColor(name){return NAMED_COLORS[name]||'#6e7681';}

// ═══════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════
let GEO=null, HIST=null;
let API_CA=null, API_SE=null;
let mapL=null, mapR=null;
let layerL=null, layerR=null;
let legendL=null, legendR=null;
let chartNat=null, chartDept=null;
let currentTab='congreso';
let selectedDept=null;

// ═══════════════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════════════
window.addEventListener('DOMContentLoaded', async ()=>{
  initMaps();
  const [geo,hist]=await Promise.all([loadGeo(),loadHistorico()]);
  fetchLiveData(); // also renders
  setInterval(()=>fetchLiveData(),60000);
});

document.querySelectorAll('nav button').forEach(btn=>{
  btn.addEventListener('click',()=>{
    document.querySelectorAll('nav button').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    currentTab=btn.dataset.tab;
    selectedDept=null;
    const selCorp=document.getElementById('sel-corp');
    selCorp.disabled=(currentTab==='presidencial');
    render();
  });
});
document.getElementById('sel-corp').addEventListener('change',()=>{fetchLiveData();});
document.getElementById('sel-orient').addEventListener('change',()=>render());

// ═══════════════════════════════════════════════════════════
// MAPS INIT
// ═══════════════════════════════════════════════════════════
function initMaps(){
  const tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
  const opts={zoom:5,center:[4.5,-74.5],zoomControl:false,attributionControl:false};
  mapL=L.map('map-left',opts);
  L.tileLayer(tiles).addTo(mapL);
  L.control.zoom({position:'topright'}).addTo(mapL);
  mapR=L.map('map-right',{...opts});
  L.tileLayer(tiles).addTo(mapR);
  L.control.zoom({position:'topright'}).addTo(mapR);
}

// ═══════════════════════════════════════════════════════════
// DATA LOAD
// ═══════════════════════════════════════════════════════════
async function loadGeo(){
  try{const r=await fetch('data/00.geojson');if(!r.ok)throw Error(r.status);GEO=await r.json();}
  catch(e){console.error('GeoJSON:',e);}
}
async function loadHistorico(){
  try{const r=await fetch('data/historico.json');if(!r.ok)throw Error(r.status);HIST=await r.json();}
  catch(e){console.error('historico.json:',e);}
}
async function fetchLiveData(){
  const corp=document.getElementById('sel-corp').value;
  const path=corp==='senado'?'ACT/SE/00':'ACT/CA/00';
  setStatus('Actualizando\u2026','#58a6ff');
  show('right-spinner',true);
  try{
    const r=await fetch(`/api/registraduria_proxy?path=${path}`);
    if(!r.ok) throw Error(r.status);
    const d=await r.json();
    if(corp==='senado') API_SE=d; else API_CA=d;
    const mdhm=d.mdhm||'';
    document.getElementById('update-time').textContent=mdhm?'Actualizado: '+mdhm:'';
    setStatus('\u25cf EN VIVO','#2ea043');
  }catch(e){
    setStatus('\u26a0 Offline','#d29922');
    console.error('Live:',e);
  }
  show('right-spinner',false);
  if(GEO&&HIST) render();
}
function setStatus(msg,color){
  const el=document.getElementById('api-status');
  el.textContent=msg; el.style.color=color; el.style.fontSize='.72rem';
}
function show(id,visible){document.getElementById(id).style.display=visible?'inline-block':'none';}

// ═══════════════════════════════════════════════════════════
// CHARTS INIT
// ═══════════════════════════════════════════════════════════
function mkChart(id){
  return new Chart(document.getElementById(id),{
    type:'bar',
    data:{labels:[],datasets:[{data:[],backgroundColor:[]}]},
    options:{
      responsive:true,maintainAspectRatio:false,indexAxis:'y',
      plugins:{legend:{display:false},tooltip:{callbacks:{
        label:ctx=>' '+fmt(ctx.raw)+' votos'
      }}},
      scales:{
        x:{ticks:{color:'#8b949e',font:{size:9},callback:v=>fmtK(v)},grid:{color:'#21262d'},border:{color:'#30363d'}},
        y:{ticks:{color:'#e6edf3',font:{size:9},maxRotation:0},grid:{display:false},border:{color:'#30363d'}}
      }
    }
  });
}
chartNat =mkChart('chart-national');
chartDept=mkChart('chart-dept');

function fillChart(chart,items){
  const top=items.slice(0,12);
  chart.data.labels=top.map(i=>truncate(i.label,22));
  chart.data.datasets[0].data=top.map(i=>i.value);
  chart.data.datasets[0].backgroundColor=top.map(i=>i.color);
  chart.update('none');
}
function clearChart(chart){fillChart(chart,[]);}

// ═══════════════════════════════════════════════════════════
// MAIN RENDER DISPATCHER
// ═══════════════════════════════════════════════════════════
function render(){
  if(!GEO||!HIST) return;
  const corp=document.getElementById('sel-corp').value;
  const orient=document.getElementById('sel-orient').value;
  if(currentTab==='congreso')     renderCongreso(corp,orient);
  else if(currentTab==='presidencial') renderPresidencial(orient);
  else                            renderConsultaPH(corp,orient);
}

// ─ Tab 1: Congreso 2022 vs 2026 live ─────────────────────
function renderCongreso(corp,orient){
  document.getElementById('left-title').textContent=`Congreso 2022 \u2014 ${corp==='senado'?'Senado':'C\u00e1mara'}`;
  document.getElementById('right-title').textContent=`2026 EN VIVO \u2014 ${corp==='senado'?'Senado':'C\u00e1mara'}`;
  document.getElementById('chart-panel-title').textContent='Resultados Nacionales';

  const histCorp=(corp==='senado')?HIST.congreso['2022'].senado:HIST.congreso['2022'].camara;

  // Left map: historico 2022
  layerL=paintHistMap(mapL,layerL,histCorp.departamentos,orient,'left',false);

  // Right map: live 2026
  const liveData=corp==='senado'?API_SE:API_CA;
  layerR=paintLiveMap(mapR,layerR,liveData,orient,'right');

  // National chart: 2022
  const natItems=filterOrient(histCorp.nacional,orient,'orientacion')
    .sort((a,b)=>b.votos-a.votos)
    .map(p=>({label:p.partido,value:p.votos,color:p.color||namedColor(p.partido)}));
  fillChart(chartNat,natItems);
  document.getElementById('chart-nat-title').textContent=`Nacional 2022 \u2014 ${corp==='senado'?'Senado':'C\u00e1mara'}`;

  // Curules bar: 2022 proportional
  renderCurules(histCorp.nacional,orient,`(${corp==='senado'?'Senado':'C\u00e1mara'} 2022)`);

  // Dept chart
  refreshDeptChart();
}

// ─ Tab 2: Presidenciales 2022 V1 vs V2 ───────────────────
function renderPresidencial(orient){
  document.getElementById('left-title').textContent='Presidencial 2022 \u2014 1\u00aa Vuelta';
  document.getElementById('right-title').textContent='Presidencial 2022 \u2014 2\u00aa Vuelta';
  document.getElementById('chart-panel-title').textContent='Resultados Presidenciales 2022';

  const v1=HIST.presidencial['2022'].vuelta1;
  const v2=HIST.presidencial['2022'].vuelta2;

  layerL=paintHistMap(mapL,layerL,v1.departamentos,orient,'left',true);
  layerR=paintHistMap(mapR,layerR,v2.departamentos,orient,'right',true);

  const nat1=filterOrient(v1.nacional,orient,'orientacion')
    .sort((a,b)=>b.votos-a.votos)
    .map(p=>({label:p.candidato||p.partido,value:p.votos,color:p.color||namedColor(p.candidato||p.partido)}));
  fillChart(chartNat,nat1);
  document.getElementById('chart-nat-title').textContent='Nacional \u2014 1\u00aa Vuelta';

  renderCurules(v1.nacional,orient,'(presidenciales 2022)');
  refreshDeptChart();
}

// ─ Tab 3: PH Consulta 2025 vs 2026 live ──────────────────
function renderConsultaPH(corp,orient){
  document.getElementById('left-title').textContent=`PH Consulta 2025 \u2014 ${corp==='senado'?'Senado':'C\u00e1mara'}`;
  document.getElementById('right-title').textContent=`Congreso 2026 EN VIVO \u2014 ${corp==='senado'?'Senado':'C\u00e1mara'}`;
  document.getElementById('chart-panel-title').textContent='Pacto Hist\u00f3rico: Consulta 2025 vs 2026';

  const ph=HIST.consultas['2025'][corp==='senado'?'senado':'presidente'];

  layerL=paintPHMap(mapL,layerL,ph,'left');
  layerR=paintLiveMap(mapR,layerR,corp==='senado'?API_SE:API_CA,orient,'right');

  const cands=(ph.candidatos||[]).slice().sort((a,b)=>b.votos-a.votos)
    .map(c=>({label:c.candidato||c.partido,value:c.votos,color:c.color||namedColor(c.candidato||c.partido)}));
  fillChart(chartNat,cands);
  document.getElementById('chart-nat-title').textContent='PH Consulta 2025 \u2014 Nacional';

  renderCurules(null,orient,'(consulta interna \u2014 sin esca\u00f1os)');
  refreshDeptChart();
}

// ═══════════════════════════════════════════════════════════
// MAP PAINT FUNCTIONS
// ═══════════════════════════════════════════════════════════

/** Paint historical map from departamentos dict: {dpto:{[{partido,votos,color,orientacion}]}} */
function paintHistMap(map,oldLayer,departamentos,orient,side,isCandidato){
  if(oldLayer) map.removeLayer(oldLayer);
  removeLegend(map,side);
  if(!GEO) return null;

  const winners={};
  for(const [rawDept,arr] of Object.entries(departamentos)){
    const dpto=pad2(rawDept);
    const filtered=orient==='todas'?arr:arr.filter(p=>(p.orientacion||'')=== orient);
    if(!filtered.length) continue;
    const sorted=[...filtered].sort((a,b)=>b.votos-a.votos);
    const total=sorted.reduce((s,p)=>s+p.votos,0);
    const top=sorted[0];
    const name=isCandidato?(top.candidato||top.partido):top.partido;
    winners[dpto]={
      name, color:top.color||namedColor(name),
      pct:total>0?(top.votos/total)*100:0,
      arr:sorted
    };
  }

  const layer=L.geoJSON(GEO,{
    style:f=>deptStyle(pad2(f.properties.DPTO),winners),
    onEachFeature:(f,fl)=>deptEvents(fl,pad2(f.properties.DPTO),winners,side,false)
  });
  layer.addTo(map);
  addLegend(map,side,buildWinLegend(winners));
  return layer;
}

/** Paint PH consulta 2025 map */
function paintPHMap(map,oldLayer,ph,side){
  if(oldLayer) map.removeLayer(oldLayer);
  removeLegend(map,side);
  if(!GEO) return null;

  const winners={};
  for(const [rawDept,arr] of Object.entries(ph.departamentos)){
    const dpto=pad2(rawDept);
    if(!arr||!arr.length) continue;
    const sorted=[...arr].sort((a,b)=>b.votos-a.votos);
    const total=sorted.reduce((s,p)=>s+p.votos,0);
    const top=sorted[0];
    const name=top.candidato||top.partido;
    winners[dpto]={name,color:top.color||namedColor(name),pct:total>0?(top.votos/total)*100:0,arr:sorted};
  }

  const layer=L.geoJSON(GEO,{
    style:f=>deptStyle(pad2(f.properties.DPTO),winners),
    onEachFeature:(f,fl)=>deptEvents(fl,pad2(f.properties.DPTO),winners,side,false)
  });
  layer.addTo(map);
  addLegend(map,side,buildWinLegend(winners));
  return layer;
}

/** Paint live API map */
function paintLiveMap(map,oldLayer,liveData,orient,side){
  if(oldLayer) map.removeLayer(oldLayer);
  removeLegend(map,side);
  if(!GEO||!liveData) return null;

  const cam=liveData.camaras?.[0];
  if(!cam) return null;

  const winners={};
  for(const m of (cam.mapagan||[])){
    const dpto=AMB_TO_DPTO[m.amb];
    if(!dpto) continue;
    const party=getParty(m.codpar);
    const pvot=parseFloat((m.pvot||'0').replace(',','.'));
    winners[dpto]={name:party.n,color:party.c,ori:party.o,pct:pvot,codpar:m.codpar,vot:parseInt(m.vot||0)};
  }

  const winsFiltered=(orient==='todas')?winners:
    Object.fromEntries(Object.entries(winners).filter(([,w])=>w.ori===orient));

  const layer=L.geoJSON(GEO,{
    style:f=>{
      const d=pad2(f.properties.DPTO);
      const w=winsFiltered[d];
      if(!w){
        // Has winner but filtered out by orientation?
        const wo=winners[d];
        return wo
          ? {fillColor:'#21262d',color:'#30363d',weight:.5,fillOpacity:.35}
          : {fillColor:'#0d1117',color:'#21262d',weight:.5,fillOpacity:.3};
      }
      const op=0.35+(w.pct/100)*0.57;
      return {fillColor:w.color,color:'#1c2128',weight:1,fillOpacity:Math.min(op,0.92)};
    },
    onEachFeature:(f,fl)=>deptEventsLive(fl,pad2(f.properties.DPTO),winners,side)
  });
  layer.addTo(map);

  // Legend for live: top parties by wins
  const winCount={};
  for(const w of Object.values(winsFiltered)){
    if(!winCount[w.name]) winCount[w.name]={color:w.color,count:0};
    winCount[w.name].count++;
  }
  const legItems=Object.entries(winCount).sort((a,b)=>b[1].count-a[1].count).slice(0,7)
    .map(([name,d])=>({label:`${name} (${d.count})`,color:d.color}));
  addLegend(map,side,legItems);
  return layer;
}

// ═══════════════════════════════════════════════════════════
// DEPT INTERACTION
// ═══════════════════════════════════════════════════════════
function deptStyle(dpto,winners){
  const w=winners[dpto];
  if(!w) return {fillColor:'#0d1117',color:'#21262d',weight:.5,fillOpacity:.3};
  const op=0.35+(w.pct/100)*0.57;
  return {fillColor:w.color,color:'#1c2128',weight:1,fillOpacity:Math.min(op,0.92)};
}

function deptEvents(fl,dpto,winners,side,isLive){
  fl.on({
    mouseover(e){
      fl.setStyle({weight:2.5,color:side==='left'?'#58a6ff':'#3fb950'});
      const w=winners[dpto];
      const tt=w
        ? `<strong>${dpto}</strong><br>${w.name}<br>${w.pct.toFixed(1)}%`
        : `<strong>${dpto}</strong><br>Sin datos`;
      fl.bindTooltip(tt,{className:'dept-tooltip',sticky:true,direction:'top'}).openTooltip(e.latlng);
    },
    mouseout(){
      fl.setStyle(deptStyle(dpto,winners));
      fl.closeTooltip();
    },
    click(){
      selectedDept=dpto;
      refreshDeptChart();
    }
  });
}

function deptEventsLive(fl,dpto,winners,side){
  fl.on({
    mouseover(e){
      fl.setStyle({weight:2.5,color:'#3fb950'});
      const w=winners[dpto];
      const tt=w
        ? `<strong>${dpto}</strong><br>${w.name}<br>${w.pct.toFixed(1)}% &bull; ${fmt(w.vot)} votos`
        : `<strong>${dpto}</strong><br>Sin datos`;
      fl.bindTooltip(tt,{className:'dept-tooltip',sticky:true,direction:'top'}).openTooltip(e.latlng);
    },
    mouseout(){fl.setStyle({fillColor:winners[dpto]?winners[dpto].color:'#0d1117',color:'#1c2128',weight:1,fillOpacity:winners[dpto]?0.35+(winners[dpto].pct/100)*0.57:.3});fl.closeTooltip();},
    click(){ selectedDept=dpto; fetchAndShowDeptLive(dpto); }
  });
}

// ═══════════════════════════════════════════════════════════
// DEPT CHART
// ═══════════════════════════════════════════════════════════
function refreshDeptChart(){
  if(!selectedDept){
    document.getElementById('chart-dept-title').textContent='Haga clic en un departamento';
    clearChart(chartDept);
    return;
  }
  const corp=document.getElementById('sel-corp').value;
  const orient=document.getElementById('sel-orient').value;
  const dpto=selectedDept;

  if(currentTab==='congreso'){
    const hc=(corp==='senado')?HIST.congreso['2022'].senado:HIST.congreso['2022'].camara;
    const arr=hc.departamentos[dpto]||hc.departamentos[parseInt(dpto)]||[];
    const filtered=filterOrient(arr,orient,'orientacion').sort((a,b)=>b.votos-a.votos);
    document.getElementById('chart-dept-title').textContent=`Dpto ${dpto} \u2014 ${corp==='senado'?'Senado':'C\u00e1mara'} 2022`;
    fillChart(chartDept,filtered.map(p=>({label:p.partido,value:p.votos,color:p.color||namedColor(p.partido)})));
  } else if(currentTab==='presidencial'){
    const v1=HIST.presidencial['2022'].vuelta1;
    const arr=v1.departamentos[dpto]||[];
    const filtered=filterOrient(arr,orient,'orientacion').sort((a,b)=>b.votos-a.votos);
    document.getElementById('chart-dept-title').textContent=`Dpto ${dpto} \u2014 1\u00aa Vuelta 2022`;
    fillChart(chartDept,filtered.map(p=>({label:p.candidato||p.partido,value:p.votos,color:p.color||namedColor(p.candidato||p.partido)})));
  } else {
    const ph=HIST.consultas['2025'][corp==='senado'?'senado':'presidente'];
    const arr=ph.departamentos[dpto]||[];
    document.getElementById('chart-dept-title').textContent=`Dpto ${dpto} \u2014 PH Consulta 2025`;
    fillChart(chartDept,arr.sort((a,b)=>b.votos-a.votos).map(c=>({label:c.candidato||c.partido,value:c.votos,color:c.color||'#c92a2a'})));
  }
}

async function fetchAndShowDeptLive(dpto){
  const corp=document.getElementById('sel-corp').value;
  const amb=DPTO_TO_AMB[dpto];
  if(!amb){
    document.getElementById('chart-dept-title').textContent=`Dpto ${dpto} \u2014 sin datos`;
    clearChart(chartDept);
    return;
  }
  const endpoint=`${corp==='senado'?'ACT/SE':'ACT/CA'}/${amb}`;
  document.getElementById('chart-dept-title').textContent=`Dpto ${dpto} \u2014 cargando\u2026`;
  try{
    const r=await fetch(`/api/registraduria_proxy?path=${endpoint}`);
    if(!r.ok) throw Error(r.status);
    const data=await r.json();
    const cam=data.camaras?.[0];
    if(!cam?.partotabla) throw Error('no data');
    const items=cam.partotabla
      .map(p=>{const a=p.act;const party=getParty(a.codpar);return {label:party.n,value:parseInt(a.vot||0),color:party.c};})
      .filter(i=>i.value>0).sort((a,b)=>b.value-a.value);
    document.getElementById('chart-dept-title').textContent=`Dpto ${dpto} \u2014 2026 en vivo`;
    fillChart(chartDept,items);
  }catch(e){
    document.getElementById('chart-dept-title').textContent=`Dpto ${dpto} \u2014 error`;
    clearChart(chartDept);
  }
}

// ═══════════════════════════════════════════════════════════
// LEGEND HELPERS
// ═══════════════════════════════════════════════════════════
const legendControls={left:null,right:null};

function addLegend(map,side,items){
  removeLegend(map,side);
  const div=L.DomUtil.create('div','map-legend');
  div.innerHTML='<h4>Ganador dpto</h4>'+items.slice(0,7).map(i=>`
    <div class="leg-item"><span class="leg-color" style="background:${i.color}"></span><span>${truncate(i.label,24)}</span></div>`).join('');
  const Ctrl=L.Control.extend({onAdd:()=>div,onRemove:()=>{}});
  legendControls[side]=new Ctrl({position:'bottomleft'});
  legendControls[side].addTo(map);
}

function removeLegend(map,side){
  if(legendControls[side]){try{map.removeControl(legendControls[side]);}catch(e){} legendControls[side]=null;}
}

function buildWinLegend(winners){
  const wc={};
  for(const w of Object.values(winners)){
    if(!wc[w.name]) wc[w.name]={color:w.color,count:0};
    wc[w.name].count++;
  }
  return Object.entries(wc).sort((a,b)=>b[1].count-a[1].count).slice(0,7)
    .map(([name,d])=>({label:`${name} (${d.count})`,color:d.color}));
}

// ═══════════════════════════════════════════════════════════
// CURULES / VOTE-SHARE BAR
// ═══════════════════════════════════════════════════════════
function renderCurules(nacional,orient,subtitle){
  document.getElementById('curules-subtitle').textContent=subtitle||'';
  const bar=document.getElementById('curules-bar');
  const leg=document.getElementById('curules-legend');
  bar.innerHTML=''; leg.innerHTML='';
  if(!nacional) return;

  const filtered=filterOrient(nacional,orient,'orientacion');
  const total=filtered.reduce((s,p)=>s+(p.votos||0),0);
  if(!total) return;

  filtered.sort((a,b)=>b.votos-a.votos).forEach(p=>{
    const pct=(p.votos/total)*100;
    if(pct<1) return;
    const color=p.color||namedColor(p.partido||p.candidato);
    const seg=document.createElement('div');
    seg.className='curules-seg'; seg.style.background=color; seg.style.width=pct+'%';
    seg.title=`${p.partido||p.candidato}: ${pct.toFixed(1)}%`;
    seg.innerHTML=`<span>${pct.toFixed(0)}%</span>`;
    bar.appendChild(seg);

    const li=document.createElement('div'); li.className='cleg-item';
    li.innerHTML=`<span class="cdot" style="background:${color}"></span>${truncate(p.partido||p.candidato,22)}: ${pct.toFixed(1)}%`;
    leg.appendChild(li);
  });
}

// ═══════════════════════════════════════════════════════════
// UTILS
// ═══════════════════════════════════════════════════════════
function filterOrient(arr,orient,key){
  if(!arr) return [];
  return orient==='todas'?arr:arr.filter(p=>(p[key]||'')=== orient);
}
function pad2(v){if(v==null) return '';return String(v).trim().padStart(2,'0');}
function fmt(n){return (n||0).toLocaleString('es-CO');}
function fmtK(n){if(n>=1e6) return (n/1e6).toFixed(1)+'M'; if(n>=1e3) return (n/1e3).toFixed(0)+'k'; return n;}
function truncate(s,n){s=String(s||'');return s.length>n?s.slice(0,n-1)+'\u2026':s;}
</script>
</body>
</html>
"""

base = r"c:\Users\RYZEN\Downloads\prueba"
for path in [
    base + r"\colombia_electoral_2026.html",
    base + r"\public\index.html",
]:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(HTML)
    print(f"Written {len(HTML):,} chars to {path}")
