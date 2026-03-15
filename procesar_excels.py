#!/usr/bin/env python3
"""
procesar_excels.py
==================
Procesa los 5 archivos Excel electorales y genera:
  public/data/historico.json   — consumido por el frontend

Uso:
  pip install pandas openpyxl
  python procesar_excels.py

Fuentes:
  MMV_PRECONTEO_CAMARA_CONSULTAS2025.xlsx    → Cámara 2026
  MMV_PRECONTEO_CONGRESO_CONSULTAS2025.xlsx  → Senado 2026
  MMV_PRECONTEO_PRESIDENTE_CONSULTAS2025.xlsx → Consultas Presidenciales 2026
  votos_agregados_2022.xlsx                  → Congreso 2022
  Presidencia 2022.xlsx                       → Presidenciales 2022
"""

import pandas as pd
import json
import os
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# MAPAS DE NORMALIZACIÓN
# ─────────────────────────────────────────────────────────────────────────────

PARTIDO_MAP = {
    "PACTO HISTÓRICO": "Pacto Histórico",
    "PACTO HISTORICO": "Pacto Histórico",
    "GRAN PACTO HISTÓRICO": "Pacto Histórico",
    "PARTIDO LIBERAL COLOMBIANO": "Partido Liberal",
    "PARTIDO LIBERAL": "Partido Liberal",
    "P. LIBERAL": "Partido Liberal",
    "PARTIDO CONSERVADOR COLOMBIANO": "P. Conservador",
    "PARTIDO CONSERVADOR": "P. Conservador",
    "P. CONSERVADOR": "P. Conservador",
    "CAMBIO RADICAL": "Cambio Radical",
    "PARTIDO DE LA U": "Partido de la U",
    "PARTIDO SOCIAL DE UNIDAD NACIONAL": "Partido de la U",
    "PARTIDO SOCIAL DE UNIDAD NACIONAL - PARTIDO DE LA U": "Partido de la U",
    "CENTRO DEMOCRÁTICO": "Centro Democrático",
    "CENTRO DEMOCRATICO": "Centro Democrático",
    "COALICIÓN CENTRO DEMOCRÁTICO": "Centro Democrático",
    "ALIANZA VERDE": "Alianza Verde",
    "PARTIDO ALIANZA VERDE": "Alianza Verde",
    "COLOMBIA JUSTA LIBRES": "Col. Justa Libres",
    "COLOMBIA JUSTA Y LIBRES": "Col. Justa Libres",
    "COAL. PARTIDOS CAMBIO RADICAL Y COLOMBIA JUSTA LIBRES": "Col. Justa Libres",
    "COMUNES": "Comunes",
    "MAIS": "MAIS",
    "MOVIMIENTO ALTERNATIVO INDÍGENA Y SOCIAL": "MAIS",
    "COLOMBIA RENACIENTE": "Col. Renaciente",
    "COLOMBIA RENACIENTE - MIRA": "Col. Renaciente",
    "FUERZA CIUDADANA": "Fuerza Ciudadana",
    "NUEVO LIBERALISMO": "Nuevo Liberalismo",
    "LIGA DE GOBERNANTES ANTICORRUPCIÓN": "Liga Gobernantes",
    "LIGA GOBERNANTES": "Liga Gobernantes",
    "COLOMBIA HUMANA": "Colombia Humana",
    "COLOMBIA HUMANA - VIA CIUDADANA": "Colombia Humana",
    "EQUIPO POR COLOMBIA": "Equipo por Colombia",
    "EQUIPO COLOMBIA": "Equipo por Colombia",
    "COALICIÓN EQUIPO POR COLOMBIA": "Equipo por Colombia",
    "COALICIÓN CENTRO ESPERANZA": "Coalición Centro Esperanza",
    "MOVIMIENTO DE SALVACIÓN NACIONAL": "Mov. Salvación Nacional",
    "PARTIDO MOVIMIENTO DE SALVACIÓN NACIONAL": "Mov. Salvación Nacional",
    "N/A": None,
    "": None,
}

COLOR_MAP = {
    "Pacto Histórico":           "#c92a2a",
    "Partido Liberal":           "#e85d04",
    "P. Conservador":            "#1864ab",
    "Cambio Radical":            "#0c7ead",
    "Partido de la U":           "#e67700",
    "Centro Democrático":        "#1e2b4a",
    "Alianza Verde":             "#2b8a3e",
    "Col. Justa Libres":         "#5f3dc4",
    "Comunes":                   "#94520a",
    "MAIS":                      "#087f5b",
    "Col. Renaciente":           "#0b6e4f",
    "Fuerza Ciudadana":          "#7048e8",
    "Nuevo Liberalismo":         "#b45309",
    "Liga Gobernantes":          "#f59e0b",
    "Colombia Humana":           "#9333ea",
    "Equipo por Colombia":       "#1864ab",
    "Coalición Centro Esperanza":"#2b8a3e",
    "Mov. Salvación Nacional":   "#868e96",
    "Otros":                     "#495057",
}

ORIENTACION_MAP = {
    "Pacto Histórico":           "Izquierda",
    "Partido Liberal":           "Centroizquierda",
    "P. Conservador":            "Centroderecha",
    "Cambio Radical":            "Centroderecha",
    "Partido de la U":           "Centro",
    "Centro Democrático":        "Derecha",
    "Alianza Verde":             "Centroizquierda",
    "Col. Justa Libres":         "Derecha",
    "Comunes":                   "Izquierda",
    "MAIS":                      "Izquierda",
    "Col. Renaciente":           "Derecha",
    "Fuerza Ciudadana":          "Centroizquierda",
    "Nuevo Liberalismo":         "Centroizquierda",
    "Liga Gobernantes":          "Centro",
    "Colombia Humana":           "Izquierda",
    "Equipo por Colombia":       "Centroderecha",
    "Coalición Centro Esperanza":"Centro",
    "Mov. Salvación Nacional":   "Derecha",
    "Otros":                     "Centro",
}

# Candidatos especiales que NO son partidos reales
CODIGOS_ESPECIALES = {996, 997, 998}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def dep_code(val):
    """Normaliza código de departamento a string de 2 dígitos: '01', '11', etc."""
    try:
        return str(int(str(val).strip())).zfill(2)
    except (ValueError, TypeError):
        return None


def normalizar_partido(nombre):
    """Normaliza nombre de partido usando el mapa; fallback a title-case."""
    if not isinstance(nombre, str):
        return None
    n = nombre.strip()
    n_upper = n.upper()
    # Búsqueda exacta (insensible a mayúsculas/acentos)
    if n_upper in PARTIDO_MAP:
        return PARTIDO_MAP[n_upper]
    # Búsqueda parcial (contiene)
    for k, v in PARTIDO_MAP.items():
        if k in n_upper or n_upper in k:
            return v
    return n.title()


def enrich(rec):
    """Agrega color y orientación a un dict con campo 'partido'."""
    p = rec.get("partido") or ""
    rec["color"] = COLOR_MAP.get(p, "#495057")
    rec["orientacion"] = ORIENTACION_MAP.get(p, "Centro")
    return rec


def agrupar_dep(df, col_dep, col_partido, col_votos, min_votos=100):
    """Agrupa por departamento y partido. Devuelve dict {dep: [lista partidos]}."""
    grp = df.groupby([col_dep, col_partido])[col_votos].sum().reset_index()
    grp.columns = ["dep", "partido", "votos"]
    grp["votos"] = grp["votos"].astype(int)
    grp = grp[grp["votos"] >= min_votos]
    result = {}
    for dep in grp["dep"].dropna().unique():
        sub = grp[grp["dep"] == dep].sort_values("votos", ascending=False)
        result[dep] = [enrich(r) for r in sub.drop(columns="dep").to_dict("records")]
    return result


def agrupar_nacional(df, col_partido, col_votos, min_votos=100):
    """Agrupa nacional por partido. Devuelve lista ordenada por votos."""
    grp = df.groupby(col_partido)[col_votos].sum().reset_index()
    grp.columns = ["partido", "votos"]
    grp["votos"] = grp["votos"].astype(int)
    grp = grp[grp["votos"] >= min_votos].sort_values("votos", ascending=False)
    total = grp["votos"].sum()
    if total > 0:
        grp["pct"] = (grp["votos"] / total * 100).round(2)
    else:
        grp["pct"] = 0.0
    return [enrich(r) for r in grp.to_dict("records")]


def calcular_ganadores_dep(dep_dict):
    """Para cada dpto devuelve el ganador (partido con más votos)."""
    return {dep: partidos[0]["partido"] if partidos else "—"
            for dep, partidos in dep_dict.items()}


# ─────────────────────────────────────────────────────────────────────────────
# PROCESAMIENTO
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("  PROCESAMIENTO ELECTORAL — COLOMBIA 2022–2026")
print("=" * 60)
print()
print("NOTA: Los archivos MMV_PRECONTEO_*_CONSULTAS2025.xlsx contienen")
print("      la consulta interpartidista del Pacto Histórico (2025).")
print("      Fue celebrada en 2025 para elegir candidatos al Congreso 2026.")
print("      Los datos de Congreso general 2022 provienen de votos_agregados_2022.xlsx.")
print()

# ── 1/5 CONSULTA CÁMARA 2025 (Pacto Histórico) ──────────────────────────────
print("[1/5] Leyendo Consulta Cámara 2025 (PH) …")
df_cam26 = pd.read_excel(
    "MMV_PRECONTEO_CAMARA_CONSULTAS2025.xlsx",
    sheet_name="Table1",
    dtype={"dep": str, "votos": int},
)
df_cam26["dep"] = df_cam26["dep"].apply(dep_code)
df_cam26["nomcan_clean"] = df_cam26["nomcan"].str.strip().str.title()
# Filtrar votos nulos/blancos/no marcados
df_cam26 = df_cam26[~df_cam26["codcan"].isin([996, 997, 998])]
df_cam26 = df_cam26[df_cam26["partido"].notna()]

# Nacional por candidato (top 30 por votos)
grp_cam26_nac = df_cam26.groupby("nomcan_clean")["votos"].sum().reset_index()
grp_cam26_nac.columns = ["candidato", "votos"]
grp_cam26_nac["votos"] = grp_cam26_nac["votos"].astype(int)
grp_cam26_nac = grp_cam26_nac.sort_values("votos", ascending=False).head(50)
total_cam26 = grp_cam26_nac["votos"].sum()
grp_cam26_nac["pct"] = (grp_cam26_nac["votos"] / total_cam26 * 100).round(2) if total_cam26 > 0 else 0.0
grp_cam26_nac["partido"] = "Pacto Histórico"
cam26_cand_list = [enrich(r) for r in grp_cam26_nac.to_dict("records")]

# Por departamento: ganador = candidato con más votos
grp_cam26_dep_raw = df_cam26.groupby(["dep", "nomcan_clean"])["votos"].sum().reset_index()
grp_cam26_dep_raw.columns = ["dep", "candidato", "votos"]
grp_cam26_dep_raw["votos"] = grp_cam26_dep_raw["votos"].astype(int)
grp_cam26_dep_raw["partido"] = "Pacto Histórico"
cam26_dep = {}
cam26_gan = {}
for dep in grp_cam26_dep_raw["dep"].dropna().unique():
    sub = grp_cam26_dep_raw[grp_cam26_dep_raw["dep"] == dep].sort_values("votos", ascending=False)
    cam26_dep[dep] = [enrich(r) for r in sub.drop(columns="dep").to_dict("records")]
    cam26_gan[dep] = sub.iloc[0]["candidato"] if len(sub) > 0 else "—"

print(f"  → {len(df_cam26):,} filas | {len(cam26_gan)} departamentos | {len(cam26_cand_list)} candidatos")

# ── 2/5 CONSULTA SENADO 2025 (Pacto Histórico) ──────────────────────────────
print("\n[2/5] Leyendo Consulta Senado 2025 (PH) …")
df_sen26 = pd.read_excel(
    "MMV_PRECONTEO_CONGRESO_CONSULTAS2025.xlsx",
    sheet_name="Table1",
    dtype={"dep": str, "votos": int},
)
df_sen26["dep"] = df_sen26["dep"].apply(dep_code)
df_sen26["nomcan_clean"] = df_sen26["nomcan"].str.strip().str.title()
df_sen26 = df_sen26[~df_sen26["codcan"].isin([996, 997, 998])]
df_sen26 = df_sen26[df_sen26["partido"].notna()]

grp_sen26_nac = df_sen26.groupby("nomcan_clean")["votos"].sum().reset_index()
grp_sen26_nac.columns = ["candidato", "votos"]
grp_sen26_nac["votos"] = grp_sen26_nac["votos"].astype(int)
grp_sen26_nac = grp_sen26_nac.sort_values("votos", ascending=False).head(50)
total_sen26 = grp_sen26_nac["votos"].sum()
grp_sen26_nac["pct"] = (grp_sen26_nac["votos"] / total_sen26 * 100).round(2) if total_sen26 > 0 else 0.0
grp_sen26_nac["partido"] = "Pacto Histórico"
sen26_cand_list = [enrich(r) for r in grp_sen26_nac.to_dict("records")]

grp_sen26_dep_raw = df_sen26.groupby(["dep", "nomcan_clean"])["votos"].sum().reset_index()
grp_sen26_dep_raw.columns = ["dep", "candidato", "votos"]
grp_sen26_dep_raw["votos"] = grp_sen26_dep_raw["votos"].astype(int)
grp_sen26_dep_raw["partido"] = "Pacto Histórico"
sen26_dep = {}
sen26_gan = {}
for dep in grp_sen26_dep_raw["dep"].dropna().unique():
    sub = grp_sen26_dep_raw[grp_sen26_dep_raw["dep"] == dep].sort_values("votos", ascending=False)
    sen26_dep[dep] = [enrich(r) for r in sub.drop(columns="dep").to_dict("records")]
    sen26_gan[dep] = sub.iloc[0]["candidato"] if len(sub) > 0 else "—"

print(f"  → {len(df_sen26):,} filas | {len(sen26_gan)} departamentos | {len(sen26_cand_list)} candidatos")

# ── 3/5 CONSULTA PRESIDENCIAL 2025 (Pacto Histórico) ────────────────────────
print("\n[3/5] Leyendo Consulta Presidencial 2025 (PH) …")
df_pres26 = pd.read_excel(
    "MMV_PRECONTEO_PRESIDENTE_CONSULTAS2025.xlsx",
    sheet_name="Table1",
    dtype={"dep": str, "votos": int},
)
df_pres26["dep"] = df_pres26["dep"].apply(dep_code)
df_pres26["nomcan_clean"] = df_pres26["nomcan"].str.strip().str.title()
df_pres26 = df_pres26[~df_pres26["codcan"].isin([996, 997, 998])]
df_pres26 = df_pres26[df_pres26["partido"].notna()]

# Nacional por candidato
grp_cand26 = df_pres26.groupby(["nomcan_clean", "codcan"])["votos"].sum().reset_index()
grp_cand26.columns = ["candidato", "codcan", "votos"]
grp_cand26["votos"] = grp_cand26["votos"].astype(int)
grp_cand26 = grp_cand26.sort_values("votos", ascending=False)
total_p26 = grp_cand26["votos"].sum()
grp_cand26["pct"] = (grp_cand26["votos"] / total_p26 * 100).round(2) if total_p26 > 0 else 0.0
grp_cand26["partido"] = "Pacto Histórico"
pres26_nac = [enrich(r) for r in grp_cand26.drop(columns="codcan").to_dict("records")]

# Por departamento
pres26_dep_raw = df_pres26.groupby(["dep", "nomcan_clean"])["votos"].sum().reset_index()
pres26_dep_raw.columns = ["dep", "candidato", "votos"]
pres26_dep_raw["votos"] = pres26_dep_raw["votos"].astype(int)
pres26_dep_raw["partido"] = "Pacto Histórico"
pres26_dep = {}
pres26_gan = {}
for dep in pres26_dep_raw["dep"].dropna().unique():
    sub = pres26_dep_raw[pres26_dep_raw["dep"] == dep].sort_values("votos", ascending=False)
    pres26_dep[dep] = [enrich(r) for r in sub.drop(columns="dep").to_dict("records")]
    pres26_gan[dep] = sub.iloc[0]["candidato"] if len(sub) > 0 else "—"

print(f"  → {len(df_pres26):,} filas | {len(pres26_gan)} departamentos | {len(pres26_nac)} candidatos")
for c in pres26_nac:
    print(f"     {c['candidato']}: {c['votos']:,} votos ({c['pct']}%)")

# ── 4/5 CONGRESO 2022 ────────────────────────────────────────────────────────
print("\n[4/5] Leyendo Congreso 2022 …")
df_22 = pd.read_excel("votos_agregados_2022.xlsx", sheet_name="Base")
df_22["dep"] = df_22["codigodepartamento"].apply(dep_code)
df_22["partido_clean"] = df_22["nombrepartido"].apply(normalizar_partido)
# Filtrar códigos especiales (996=blanco, 997=nulo, 998=no marcado)
df_22 = df_22[~df_22["códigocandidato"].isin(CODIGOS_ESPECIALES)]
df_22 = df_22[df_22["partido_clean"].notna()]

# SENADO 2022 (códigocorporación == 1)
df_sen22 = df_22[df_22["códigocorporación"] == 1]
sen22_nac = agrupar_nacional(df_sen22, "partido_clean", "totalvotos")
sen22_dep = agrupar_dep(df_sen22, "dep", "partido_clean", "totalvotos")
sen22_gan = calcular_ganadores_dep(sen22_dep)
print(f"  → Senado 2022: {len(df_sen22):,} filas | {len(sen22_gan)} dptos | {len(sen22_nac)} partidos")

# CÁMARA 2022 (códigocorporación == 2)
df_cam22 = df_22[df_22["códigocorporación"] == 2]
cam22_nac = agrupar_nacional(df_cam22, "partido_clean", "totalvotos")
cam22_dep = agrupar_dep(df_cam22, "dep", "partido_clean", "totalvotos")
cam22_gan = calcular_ganadores_dep(cam22_dep)
print(f"  → Cámara 2022: {len(df_cam22):,} filas | {len(cam22_gan)} dptos | {len(cam22_nac)} partidos")

# ── 5/5 PRESIDENCIALES 2022 ──────────────────────────────────────────────────
print("\n[5/5] Leyendo Presidenciales 2022 …")
df_p22 = pd.read_excel("Presidencia 2022.xlsx", sheet_name="Resultados")
df_p22["dep"] = df_p22["Código Departamento"].apply(dep_code)
df_p22["partido_clean"] = df_p22["Partido"].apply(normalizar_partido)
df_p22["cand_clean"] = df_p22["Nombre Candidato"].str.strip().str.title()
df_p22 = df_p22[df_p22["partido_clean"].notna()]

pres22 = {}
for vuelta in [1, 2]:
    sub_v = df_p22[df_p22["Vuelta"] == vuelta]

    # Nacional
    grp_nac = sub_v.groupby(["cand_clean", "partido_clean"])["Votos"].sum().reset_index()
    grp_nac.columns = ["candidato", "partido", "votos"]
    grp_nac["votos"] = grp_nac["votos"].astype(int)
    grp_nac = grp_nac.sort_values("votos", ascending=False)
    total_vv = grp_nac["votos"].sum()
    grp_nac["pct"] = (grp_nac["votos"] / total_vv * 100).round(2) if total_vv > 0 else 0.0
    nac_list = [enrich(r) for r in grp_nac.to_dict("records")]

    # Por departamento
    grp_dep = sub_v.groupby(["dep", "cand_clean", "partido_clean"])["Votos"].sum().reset_index()
    grp_dep.columns = ["dep", "candidato", "partido", "votos"]
    grp_dep["votos"] = grp_dep["votos"].astype(int)
    dep_dict = {}
    ganadores = {}
    for dep in grp_dep["dep"].dropna().unique():
        d_sub = grp_dep[grp_dep["dep"] == dep].sort_values("votos", ascending=False)
        dep_dict[dep] = [enrich(r) for r in d_sub.drop(columns="dep").to_dict("records")]
        ganadores[dep] = d_sub.iloc[0]["candidato"] if len(d_sub) > 0 else "—"

    pres22[vuelta] = {"nacional": nac_list, "departamentos": dep_dict, "ganadores": ganadores}
    print(f"  → Vuelta {vuelta}: {len(sub_v):,} filas | {len(ganadores)} dptos | {len(nac_list)} candidatos")

# ─────────────────────────────────────────────────────────────────────────────
# ENSAMBLAR JSON FINAL
# ─────────────────────────────────────────────────────────────────────────────
print("\nEnsemblando historico.json …")

historico = {
    "meta": {
        "generado": pd.Timestamp.now().isoformat(),
        "descripcion": {
            "consultas_2025": "Consulta interpartidista Pacto Histórico — 2025 (candidatos para Congreso 2026)",
            "congreso_2022": "Resultados generales Congreso — 13 Mar 2022",
            "presidencial_2022": "Resultados Presidenciales 2022 (1ra y 2da vuelta)",
        },
        "fuentes": [
            "MMV_PRECONTEO_CAMARA_CONSULTAS2025.xlsx",
            "MMV_PRECONTEO_CONGRESO_CONSULTAS2025.xlsx",
            "MMV_PRECONTEO_PRESIDENTE_CONSULTAS2025.xlsx",
            "votos_agregados_2022.xlsx",
            "Presidencia 2022.xlsx",
        ],
    },
    # Datos reales del Congreso 2022 (todas las fuerzas políticas)
    "congreso": {
        "2022": {
            "camara": {
                "nacional":      cam22_nac,
                "departamentos": cam22_dep,
                "ganadores":     cam22_gan,
            },
            "senado": {
                "nacional":      sen22_nac,
                "departamentos": sen22_dep,
                "ganadores":     sen22_gan,
            },
        },
        # El Congreso 2026 general no está disponible en los Excel;
        # se consigue en tiempo real vía /api/registraduria_proxy
        "2026": None,
    },
    # Presidenciales 2022
    "presidencial": {
        "2022": {
            "vuelta1": {
                "nacional":      pres22[1]["nacional"],
                "departamentos": pres22[1]["departamentos"],
                "ganadores":     pres22[1]["ganadores"],
            },
            "vuelta2": {
                "nacional":      pres22[2]["nacional"],
                "departamentos": pres22[2]["departamentos"],
                "ganadores":     pres22[2]["ganadores"],
            },
        }
    },
    # Consulta interpartidista Pacto Histórico — 2025
    "consultas": {
        "2025": {
            "presidente": {
                "candidatos":    pres26_nac,
                "departamentos": pres26_dep,
                "ganadores":     pres26_gan,
                "total_votos":   int(sum(c["votos"] for c in pres26_nac)),
            },
            "camara": {
                "candidatos":    cam26_cand_list,
                "departamentos": cam26_dep,
                "ganadores":     cam26_gan,
                "total_votos":   int(sum(c["votos"] for c in cam26_cand_list)),
            },
            "senado": {
                "candidatos":    sen26_cand_list,
                "departamentos": sen26_dep,
                "ganadores":     sen26_gan,
                "total_votos":   int(sum(c["votos"] for c in sen26_cand_list)),
            },
        }
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# GUARDAR
# ─────────────────────────────────────────────────────────────────────────────
output_path = Path("public/data/historico.json")
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(historico, f, ensure_ascii=False, separators=(",", ":"))

size_kb = output_path.stat().st_size / 1024
print(f"\n✅  Generado: {output_path}  ({size_kb:.0f} KB)")
print("   Listo para servir desde el frontend.\n")
print("Tip: para previsualizar localmente corre:")
print("   python -m http.server 8080")
print("   y abre  http://localhost:8080/public/index.html\n")
