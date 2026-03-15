import pandas as pd
df = pd.read_excel('votos_agregados_2022.xlsx', sheet_name='Base')
parties = df[['códigopartido','nombrepartido','codigoclasificación','clasificación']].drop_duplicates()
parties = parties[parties['códigopartido'] > 0].sort_values('códigopartido')
for _, r in parties.iterrows():
    cod = int(r['códigopartido'])
    clas = str(r['clasificación']).strip()
    nom = str(r['nombrepartido']).strip()
    print(f"codpar={cod:3d} | {clas:20s} | {nom}")
