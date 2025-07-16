import os
import pandas as pd

base_dir = os.path.dirname(__file__)
df_true = pd.read_csv(os.path.join(base_dir, "True.csv"))
df_fake = pd.read_csv(os.path.join(base_dir, "Fake.csv"))

# Une ambos datasets
df = pd.concat([df_true, df_fake], ignore_index=True)

# Trunca a 32,000 registros
df = df.head(32000)

# Crea un id único
df["id"] = range(1, len(df) + 1)

# Selecciona solo las columnas que necesitas
df = df[["id", "title"]]

# Guarda el nuevo CSV
df.to_csv(os.path.join(base_dir, "news_large.csv"), index=False)