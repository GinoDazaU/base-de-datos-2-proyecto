import pandas as pd

df = pd.read_csv("fma_metadata/raw_tracks.csv")

# Selecciona solo las columnas que realmente existen
columns_to_keep = ["track_id", "artist_name", "track_duration","track_genres", "track_title"]

# Filtrar el dataframe
df_filtered = df[columns_to_keep].copy()

# Renombrar columnas para simplificar
df_filtered.columns = ['id', 'artist', 'duration', 'genre', 'title']

# Verifica los primeros registros
print(df_filtered.head())

# nuevo CSV limpio
df_filtered.to_csv("canciones_filtradas.csv", index=False)