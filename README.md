# Atlas Electoral Colombia 2022–2026

**URL de producción:** https://eleccciones-colombia-2022-2026.vercel.app  
**Repositorio:** https://github.com/M3l1ss4C4rd0n4/Eleccciones-Colombia-2022-2026

Dashboard interactivo de comparativa electoral departamental que cruza datos históricos de 2022 con resultados en vivo del Congreso 2026 y la Consulta Interpartidista Presidencial 2026. Incluye mapas coropléticos dobles, gráficos de barras y donut, estadísticas nacionales y por departamento, y estimación de curules via Cifra Repartidora (D'Hondt).

---

## Índice

1. [Tecnologías usadas](#1-tecnologías-usadas)
2. [Estructura del proyecto](#2-estructura-del-proyecto)
3. [Arquitectura general](#3-arquitectura-general)
4. [Funcionalidades por pestaña](#4-funcionalidades-por-pestaña)
5. [Cómo procesar los datos fuente](#5-cómo-procesar-los-datos-fuente)
6. [Cómo desplegar en Vercel](#6-cómo-desplegar-en-vercel)
7. [API de la Registraduría](#7-api-de-la-registraduría)
8. [Catálogo de partidos y colores](#8-catálogo-de-partidos-y-colores)
9. [Decisiones técnicas](#9-decisiones-técnicas)
10. [Problemas resueltos (troubleshooting)](#10-problemas-resueltos-troubleshooting)

---

## 1. Tecnologías usadas

| Tecnología | Versión | Uso |
|---|---|---|
| HTML/CSS/JavaScript puro | ES2022 | Frontend — archivo único sin bundler |
| [Leaflet.js](https://leafletjs.com/) | 1.9.4 | Mapas coropléticos interactivos |
| [Chart.js](https://www.chartjs.org/) | 4.4.0 | Gráficos de barras, donut y verticales |
| Python | 3.x | Procesamiento de datos locales + proxy Vercel |
| [Vercel](https://vercel.com/) | v2 | Hosting estático + serverless functions |
| [pandas](https://pandas.pydata.org/) | ≥ 2.0.0 | Lectura de archivos Excel |
| [openpyxl](https://openpyxl.readthedocs.io/) | ≥ 3.1.0 | Motor de lectura `.xlsx` para pandas |

**No hay framework de frontend.** El archivo `colombia_electoral_2026.html` es una SPA auto-contenida (~1 700 líneas) que no requiere Node.js, React, ni ningún bundler. Se carga directamente en el navegador.

---

## 2. Estructura del proyecto

```
prueba/
├── colombia_electoral_2026.html   ← SPA principal (el dashboard completo)
├── index.html                     ← Redirect shim: redirige "/" al SPA
│
├── api/
│   └── registraduria_proxy.py     ← Proxy CORS (Vercel Serverless Function)
│
├── public/
│   └── data/
│       ├── historico.json         ← Datos históricos procesados (767 KB)
│       └── 00.geojson             ← Polígonos departamentales de Colombia (731 KB)
│
├── vercel.json                    ← Configuración de rutas y builds en Vercel
├── requirements.txt               ← Dependencias Python (pandas, openpyxl)
├── procesar_excels.py             ← Script local que genera historico.json
├── write_dashboard.py             ← Script legacy (generador anterior del HTML)
├── .gitignore                     ← Excluye .venv/, *.xlsx, /00.geojson raíz
│
└── [Archivos Excel — NO se suben a git, produción los ignora]
    ├── votos_agregados_2022.xlsx
    ├── MMV_PRECONTEO_CAMARA_CONSULTAS2025.xlsx
    ├── MMV_PRECONTEO_CONGRESO_CONSULTAS2025.xlsx
    ├── MMV_PRECONTEO_PRESIDENTE_CONSULTAS2025.xlsx
    ├── Presidencia 2022.xlsx
    └── curules_2026.xlsx
```

> **Nota:** La carpeta `.venv/` (entorno virtual Python) y todos los `.xlsx` están en `.gitignore`. Solo se sube el JSON procesado.

---

## 3. Arquitectura general

```
┌──────────────────────────────────────────────────────────────────┐
│  FUENTES DE DATOS                                                │
│                                                                  │
│  Excels de la Registraduría ──► procesar_excels.py ──► historico.json │
│  (votos 2022, consultas 2025)       (script local)     (estáticos)   │
│                                                                  │
│  https://resultados.registraduria.gov.co/json/ACT/...json        │
│        (datos en vivo 2026) ──► api/registraduria_proxy.py ──►  │
│                                  (Vercel serverless)             │
└──────────────────────────┬───────────────────────────────────────┘
                           │ fetch()
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  FRONTEND  (colombia_electoral_2026.html)                        │
│                                                                  │
│  Al cargar:                                                      │
│   1. fetch('/data/00.geojson')         → GEO (polígonos DANE)    │
│   2. fetch('/data/historico.json')     → HIST (datos estáticos)  │
│   3. fetch proxy ACT/CA/00             → API_CA (Cámara 2026)    │
│   4. fetch proxy ACT/SE/00             → API_SE (Senado 2026)    │
│   5. fetch proxy ACT/CN/00             → API_CN (Consulta Pres.) │
│   6. fetch proxy ACT/CN/{amb} ×33      → API_CN_DEPT_WINNERS     │
│                                                                  │
│  Leaflet renderiza dos mapas (izquierda/derecha).                │
│  Chart.js renderiza 4–6 charts (nacional, curules, departamento).│
│  Al hacer clic en un depto → fetch departamental en vivo.        │
└──────────────────────────────────────────────────────────────────┘
```

### Por qué un proxy Python en Vercel

La Registraduría bloquea peticiones directas desde navegadores con error 403 (bloqueo CORS + posible bloqueo geográfico desde IPs no colombianas). El proxy:
- Corre en Vercel región `gru1` (São Paulo, IP sudamericana).
- Agrega headers de navegador colombiano (`User-Agent`, `Referer`, `Origin`, `X-Forwarded-For: 190.24.0.1`).
- Desactiva verificación SSL (`ssl.CERT_NONE`) porque la Registraduría a veces tiene certificado con cadena incompleta.
- Implementa una whitelist de paths para prevenir SSRF.

---

## 4. Funcionalidades por pestaña

### Pestaña 1 — Congreso 2022 vs 2026

| Modo (selector) | Mapa Izquierdo | Mapa Derecho |
|---|---|---|
| **Cámara** | Ganador por depto — Cámara 2022 (historico.json) | Ganador por depto — Cámara 2026 EN VIVO |
| **Senado** | Ganador por depto — Senado 2022 | Ganador por depto — Senado 2026 EN VIVO |
| **Presidencia** | Ganador por depto — Presidencial 2022 V1 | 2° candidato por depto — Consulta Interpartidista 2026 |

- Filtro de orientación (Izquierda / Centroizquierda / Centro / Centroderecha / Derecha).
- Panel izquierdo: gráfico de barras horizontal con votos nacionales 2022 + curules 2022 (D'Hondt).
- Panel derecho: gráfico de barras EN VIVO + curules estimadas 2026.
- Al hacer clic en un departamento: gráfico de barras del depto debajo de cada panel.

### Pestaña 2 — Presidenciales 2022

- Izquierda: Primera vuelta 2022, derecha: Segunda vuelta 2022.
- Ambos mapas históricos coloreados por candidato ganador por depto.
- Al hacer clic en un depto: detalle de votos por candidato en ese depto.

### Pestaña 3 — PH Consulta 2025 vs 2026

| Modo | Mapa Izquierdo | Mapa Derecho |
|---|---|---|
| **Senado** | PH Consulta 2025 — Senado | Congreso Senado 2026 EN VIVO |
| **Cámara** | PH Consulta 2025 — Cámara | Congreso Cámara 2026 EN VIVO |
| **Presidencia** | PH Consulta 2025 — Presidencia | 2° candidato Consulta Interpartidista 2026 EN VIVO |

- En modo Presidencia el gráfico derecho nacional es un **donut** con colores individuales por candidato.
- Al hacer clic en depto en modo Presidencia: **barras verticales** con votos de la consulta en ese depto.

---

## 5. Cómo procesar los datos fuente

Los datos históricos vienen de archivos Excel descargados de la Registraduría. El script `procesar_excels.py` los unifica en un solo `public/data/historico.json`.

### Requisitos previos

```powershell
# Crear entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install pandas openpyxl
```

### Archivos Excel necesarios (colocar en la raíz del proyecto)

| Archivo | Contenido |
|---|---|
| `votos_agregados_2022.xlsx` | Votos Senado y Cámara 2022 por depto |
| `MMV_PRECONTEO_CAMARA_CONSULTAS2025.xlsx` | Consulta PH Cámara 2025 |
| `MMV_PRECONTEO_CONGRESO_CONSULTAS2025.xlsx` | Consulta PH Senado 2025 |
| `MMV_PRECONTEO_PRESIDENTE_CONSULTAS2025.xlsx` | Consulta PH Presidencia 2025 |
| `Presidencia 2022.xlsx` | Resultados presidenciales 2022 (V1 y V2) |
| `curules_2026.xlsx` | Curules estimadas para 2026 |

### Ejecutar el procesamiento

```powershell
python procesar_excels.py
```

Esto genera o sobreescribe `public/data/historico.json`. El archivo tiene la siguiente estructura:

```json
{
  "congreso": {
    "2022": {
      "senado": { "nacional": [...], "departamentos": {"01": [...], ...} },
      "camara":  { "nacional": [...], "departamentos": {"01": [...], ...} }
    }
  },
  "presidencial": {
    "2022": {
      "vuelta1": { "nacional": [...], "departamentos": {...} },
      "vuelta2": { "nacional": [...], "departamentos": {...} }
    }
  },
  "consultas": {
    "2025": {
      "senado":     { "candidatos": [...], "departamentos": {...} },
      "camara":     { "candidatos": [...], "departamentos": {...} },
      "presidente": { "candidatos": [...], "departamentos": {...} }
    }
  },
  "curules": {
    "2022": {
      "senado": {...},
      "camara_nacional": [...],
      "camara_departamentos": {...}
    }
  },
  "curules_2026": {
    "senado": [...],
    "camara_departamentos": [...]
  }
}
```

> **Importante**: `historico.json` SÍ se sube a git; los `.xlsx` NO.

---

## 6. Cómo desplegar en Vercel

### Primera vez

1. Tener una cuenta en [vercel.com](https://vercel.com) y el CLI instalado (`npm i -g vercel`), o usar la integración GitHub.
2. Conectar el repositorio GitHub a Vercel (importar proyecto).
3. Vercel detecta `vercel.json` automáticamente.

### Configuración de `vercel.json`

```json
{
  "version": 2,
  "regions": ["gru1"],
  "builds": [
    { "src": "*.html",       "use": "@vercel/static" },
    { "src": "public/**",    "use": "@vercel/static" },
    { "src": "api/**/*.py",  "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/",            "dest": "/colombia_electoral_2026.html" },
    { "src": "/data/(.*)",   "dest": "/public/data/$1" },
    { "src": "/(.*)",        "dest": "/public/$1" }
  ]
}
```

- **`gru1`** = región São Paulo (Brasil) — importante para que el proxy tenga una IP latinoamericana.
- La ruta `/data/(.*)` redirige `/data/historico.json` y `/data/00.geojson` a `public/data/`.
- Los archivos `.py` en `api/` se convierten en serverless functions accesibles en `/api/nombre.py`.

### Desplegar actualizaciones

```powershell
git add .
git commit -m "descripción del cambio"
git push origin master:main   # rama local master → rama remota main
```

Vercel hace auto-deploy en cada push a `main`.

---

## 7. API de la Registraduría

La Registraduría expone JSON en:
```
https://resultados.registraduria.gov.co/json/{path}.json
```

### Endpoints conocidos

| Endpoint | Descripción |
|---|---|
| `ACT/CA/00` | Cámara 2026 — resultados nacionales |
| `ACT/SE/00` | Senado 2026 — resultados nacionales |
| `ACT/CN/00` | Consulta Interpartidista Presidencial 2026 — nacional |
| `ACT/CA/{amb}` | Cámara 2026 — resultados por departamento |
| `ACT/SE/{amb}` | Senado 2026 — por departamento |
| `ACT/CN/{amb}` | Consulta Presidencial 2026 — por departamento |

> `{amb}` es un código de 4 dígitos asignado por la Registraduría (distinto al código DANE de 2 dígitos).

### Tabla de códigos ambientales (`amb`) por departamento

```
91=Amazonas→6000  05=Antioquia→0100  81=Arauca→4000   08=Atlántico→0300
11=Bogotá→1600    13=Bolívar→0500    15=Boyacá→0700   17=Caldas→0900
18=Caquetá→4400   19=Cauca→1100      20=Cesar→1200    27=Chocó→1700
23=Córdoba→1300   25=Cundinamarca→1500  94=Guainía→5000  95=Guaviare→5400
41=Huila→1900     44=La Guajira→4800 47=Magdalena→2100 50=Meta→5200
52=Nariño→2300    54=N.Santander→2500  63=Quindío→2600  66=Risaralda→2400
68=Santander→2700 70=Sucre→2800      73=Tolima→2900   76=Valle→3100
85=Casanare→4600  86=Putumayo→6400   88=San Andrés→5600
97=Vaupés→6800    99=Vichada→7200
```

### Estructura del JSON de respuesta

```json
{
  "camaras": [{
    "partotabla": [{
      "act": {
        "codpar": "38",
        "nompar": "PACTO HISTÓRICO",
        "vot": "1234567",
        "cantotabla": [{
          "cedula": "79289575",
          "nomcan": "ROY",
          "apecan": "BARRERAS",
          "vot": "456789"
        }]
      }
    }]
  }]
}
```

- `partotabla` → array de partidos/consultas
- `act.codpar` → código del partido (se usa para buscar en el catálogo `PC{}`)
- `act.cantotabla` → array de candidatos dentro de ese partido
- `cedula` → cédula del candidato (identificador único para asignar color)

### Consulta Interpartidista Presidencial 2026 (`ACT/CN/00`)

| codpar | Consulta | Color |
|---|---|---|
| `31` | La Gran Consulta (centroderecha) | `#f59e0b` (amarillo) |
| `30` | Consulta Claudia López (centroizquierda) | `#ec4899` (rosado) |
| `32` | Consulta Pacto Histórico (izquierda) | `#dc2626` (rojo) |

**Paloma Valencia ganó los 33/33 departamentos**, por eso el mapa se colorea por el **2° candidato** (runner-up) para mostrar diversidad geográfica.

---

## 8. Catálogo de partidos y colores

### Catálogo principal `PC{}`

El catálogo `PC{}` mapea `codpar` (string) → `{n: nombre, c: color hex, o: orientación}`.

```javascript
const PC = {
  '2':  {n:'Partido Liberal',    c:'#f97316', o:'Centroizquierda'},
  '3':  {n:'P. Conservador',     c:'#3b82f6', o:'Centroderecha'},
  '38': {n:'Pacto Histórico',    c:'#ef4444', o:'Izquierda'},
  '52': {n:'Alianza Verde',      c:'#22c55e', o:'Centroizquierda'},
  '10': {n:'Cambio Radical',     c:'#06b6d4', o:'Centroderecha'},
  '17': {n:'Centro Democrático', c:'#38bdf8', o:'Derecha'},
  // ... y muchos más
  '30': {n:'Consulta Claudia López',    c:'#ec4899', o:'Centroizquierda'},
  '31': {n:'La Gran Consulta',          c:'#f59e0b', o:'Centroderecha'},
  '32': {n:'Consulta Pacto Histórico',  c:'#dc2626', o:'Izquierda'},
};
```

Para agregar un nuevo partido: añadir una línea al objeto `PC` con el `codpar` correspondiente.

### Colores individuales por candidato CN (`CN_CAND_COLORS`)

Para la Consulta Interpartidista, cada candidato tiene un color único identificado por su cédula:

```javascript
const CN_CAND_COLORS = {
  '25280205': '#f59e0b',  // Paloma Valencia
  '79941641': '#fb923c',  // Juan Daniel Oviedo
  '79589617': '#fde047',  // Juan Manuel Galán
  '79593847': '#a3e635',  // Juan Carlos Pinzón
  '66918051': '#34d399',  // Victoria Dávila
  '19333686': '#22d3ee',  // Peñalosa
  '70566243': '#818cf8',  // Aníbal Gaviria
  '79777591': '#c084fc',  // David Luna
  '79154695': '#6366f1',  // Mauricio Cárdenas
  '51992648': '#ec4899',  // Claudia López
  '10004127': '#f472b6',  // Leonardo Huerta
  '79289575': '#dc2626',  // Roy Barreras
  '71386360': '#ef4444',  // Daniel Quintero
};
function cnCandColor(cedula){ return CN_CAND_COLORS[String(cedula)] || '#94a3b8'; }
```

### Color para partidos desconocidos

Si un `codpar` no está en `PC{}`, se asigna un color determinista usando la función `_unknownColor(codpar)` que indexa una paleta de 24 colores vivos con `(n*7+13) % 24`. Esto garantiza que el mismo partido siempre reciba el mismo color sin colisiones evidentes.

---

## 9. Decisiones técnicas

### ¿Por qué un único archivo HTML?

- Simplifica el despliegue (no hay paso de build).
- Vercel sirve el HTML directamente como archivo estático.
- No requiere Node.js ni bundler en el servidor.
- Todo el estado de la aplicación vive en variables globales del script (apropiado para un dashboard de visualización sin rutas ni autenticación).

### ¿Por qué Python como proxy y no JS?

- Vercel soporta serverless functions en Python de forma nativa con `@vercel/python`.
- Python tiene control más fino sobre SSL (`ssl.CERT_NONE`) necesario por el certificado de la Registraduría.
- La librería `http.client` permite un segundo intento con control total de headers si `urllib` falla.

### Estimación de curules (D'Hondt / Cifra Repartidora)

```javascript
function dhondt(votes, seats) {
  const q = [];
  for (const [party, v] of Object.entries(votes)) {
    for (let s = 1; s <= seats; s++) q.push({ party, value: v/s });
  }
  q.sort((a,b) => b.value - a.value);
  const result = {};
  for (const { party } of q.slice(0, seats)) {
    result[party] = (result[party] || 0) + 1;
  }
  return result;
}
```

Se aplica al resultado nacional en vivo para estimar la distribución de las 100 bancas del Senado y las 188 de la Cámara.

### Sistema de mapas

- **GeoJSON**: `public/data/00.geojson` con los 33 departamentos, usando código DANE de 2 dígitos como propiedad `DPTO`.
- **Conversiones de código**: El frontend mantiene tres tablas de lookup para convertir entre códigos DANE (`05`), códigos `amb` de la Registraduría (`0100`), y códigos internos del `historico.json` (`01`).
- **Coloración**: `paintHistMap()` para datos históricos, `paintLiveMap()` para datos en vivo, `paintCNMapByCand()` para la consulta presidencial.
- **Tooltip**: Al hacer hover, muestra nombre del depto, candidato/partido ganador, porcentaje y votos.

### Tipos de gráficos dinámicos

El `chartRDept` (gráfico derecho de departamento) es un solo objeto `Chart.js` que cambia de tipo dinámicamente con tres helpers:

| Función | Tipo resultante | Usado para |
|---|---|---|
| `switchToBar(chart)` | Barras horizontales | Congreso 2022/2026 por depto |
| `switchToVBar(chart)` | Barras verticales | Consulta Presidencial por depto |
| `switchToDoughnut(chart)` | Donut | Consulta Presidencial nacional |

---

## 10. Problemas resueltos (troubleshooting)

| Problema | Causa | Solución |
|---|---|---|
| Error 403 al consultar la API directamente | La Registraduría bloquea IPs no colombianas y sin headers de navegador | Proxy Vercel en región `gru1` con headers de Chrome colombiano |
| El mapa de la consulta presidencial aparecía todo de un color (amarillo) | Paloma Valencia ganó los 33 departamentos | Colorear por el 2° candidato (runner-up) en lugar del ganador |
| Todos los candidatos de La Gran Consulta tenían el mismo color en el donut | Se usaba `consulta.c` (color de grupo) en vez del color individual | Usar `cnCandColor(c.cedula)` por cédula individual |
| El gráfico de departamento en modo consulta mostraba barras horizontales | Se usa el mismo chart para todos los modos | `switchToVBar(chartRDept)` antes de llenar los datos de consulta |
| GitHub Pages devolvía 404 | El archivo principal no se llamaba `index.html` | Añadir `index.html` como redirect shim apuntando al SPA real |
| Vercel no encontraba los archivos de datos | Ruta incorrecta en `vercel.json` | Regla `"/data/(.*)"` → `"/public/data/$1"` |
| `procesar_excels.py` fallaba al leer Excel | Hojas con nombres distintos entre archivos | Normalización con diccionario `PARTIDO_MAP` y lectura condicional por nombre de hoja |

---

## Notas adicionales

- El archivo `write_dashboard.py` es un generador legacy que escribía el HTML completo via Python. Fue reemplazado por el enfoque de edición directa del HTML, pero se conserva como referencia.
- Los datos se actualizan en tiempo real cada vez que el usuario carga la página o hace clic en un departamento (no hay auto-refresh periódico).
- El badge "EN VIVO 2026" en el header es decorativo y siempre visible; el estado real de la API se muestra en `#api-status` en la barra de filtros.
- Para agregar un nuevo torneo electoral, hay que: (1) añadir los datos a `historico.json` via `procesar_excels.py`, (2) agregar la opción en el selector HTML, (3) crear una función `render*` que consuma los datos y pinte los mapas.
