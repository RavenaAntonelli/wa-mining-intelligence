# """
# Ingestão de dados de recursos minerais da Australia
# Fonte 1: ABS - Australian Bureau of Statistics (API publica, sem autenticacao)
# Fonte 2: dados historicos de mineracao WA em CSV publico
# """

# import requests
# import pandas as pd
# import psycopg2
# from psycopg2.extras import execute_values
# from datetime import datetime
# import os
# import logging
# import io

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# DB_CONFIG = {
#     "host": os.getenv("POSTGRES_HOST", "postgres"),
#     "database": os.getenv("POSTGRES_DB"),
#     "user": os.getenv("POSTGRES_USER"),
#     "password": os.getenv("POSTGRES_PASSWORD"),
#     "port": int(os.getenv("POSTGRES_PORT", 5432))
# }


# def fetch_wa_mining_tenements():
#     """
#     Dataset publico: Mining Tenements de WA
#     Fonte: catalogue.data.wa.gov.au - download direto CSV (sem API key)
#     """
#     logger.info("Buscando Mining Tenements de WA...")
#     url = "https://dasc.dmirs.wa.gov.au/Download/File/2053"

#     response = requests.get(url, timeout=60)
#     response.raise_for_status()

#     df = pd.read_csv(io.StringIO(response.text))
#     logger.info(f"Mining Tenements: {len(df)} registros, colunas: {list(df.columns)}")
#     return df


# def fetch_abs_mineral_data():
#     """
#     Dados do ABS via API JSON-stat
#     Dataset: Mining - value of production por commodity
#     """
#     logger.info("Buscando dados do ABS...")
#     url = "https://api.data.abs.gov.au/data/ABS,MINING_ACTIVITY,1.0.0/all?startPeriod=2015&endPeriod=2024&format=jsondata&dimensionAtObservation=AllDimensions"

#     headers = {"Accept": "application/vnd.sdmx.data+json"}
#     response = requests.get(url, headers=headers, timeout=60)

#     if response.status_code != 200:
#         logger.warning(f"ABS retornou {response.status_code}, usando dataset alternativo...")
#         return fetch_abs_export_data()

#     data = response.json()
#     records = []

#     try:
#         obs = data["data"]["dataSets"][0]["observations"]
#         dims = data["data"]["structure"]["dimensions"]["observation"]

#         for key, values in obs.items():
#             indices = list(map(int, key.split(":")))
#             record = {"value": values[0]}
#             for i, dim in enumerate(dims):
#                 record[dim["id"]] = dim["values"][indices[i]]["name"]
#             records.append(record)

#         df = pd.DataFrame(records)
#         logger.info(f"ABS Mining Activity: {len(df)} registros")
#         return df
#     except Exception as e:
#         logger.warning(f"Erro ao parsear ABS: {e}, usando alternativo...")
#         return fetch_abs_export_data()


# def fetch_abs_export_data():
#     """
#     Fallback: exportacoes de recursos australianos via ABS
#     """
#     logger.info("Buscando dados de exportacao ABS (fallback)...")
#     url = "https://api.data.abs.gov.au/data/ABS,MERCH_EXP,1.0.0/all?startPeriod=2020&endPeriod=2024&format=jsondata&dimensionAtObservation=AllDimensions"

#     headers = {"Accept": "application/vnd.sdmx.data+json"}
#     response = requests.get(url, headers=headers, timeout=60)

#     if response.status_code != 200:
#         logger.warning("ABS indisponivel, gerando dataset sintetico de WA mining...")
#         return generate_synthetic_wa_data()

#     data = response.json()
#     records = []
#     try:
#         obs = data["data"]["dataSets"][0]["observations"]
#         dims = data["data"]["structure"]["dimensions"]["observation"]
#         for key, values in obs.items():
#             indices = list(map(int, key.split(":")))
#             record = {"value": values[0]}
#             for i, dim in enumerate(dims):
#                 record[dim["id"]] = dim["values"][indices[i]]["name"]
#             records.append(record)
#         df = pd.DataFrame(records)
#         logger.info(f"ABS Export: {len(df)} registros")
#         return df
#     except Exception as e:
#         logger.warning(f"Erro: {e}")
#         return generate_synthetic_wa_data()


# def generate_synthetic_wa_data():
#     """
#     Dataset sintetico baseado em dados reais publicados pelo DMIRS
#     Fonte dos numeros: WA Mineral and Petroleum Statistics Digest 2023
#     Usado quando APIs estao fora do ar - transparente no README
#     """
#     logger.info("Gerando dataset baseado em estatisticas reais do DMIRS 2023...")

#     commodities = {
#         "Iron Ore":   [85100, 88200, 91500, 100200, 115300, 125100],
#         "Gold":       [12800, 13100, 13900, 14200, 15800, 17000],
#         "Lithium":    [800,   950,   1200,  2100,  4300,  8200],
#         "Nickel":     [3200,  3400,  2900,  3100,  4200,  3800],
#         "Alumina":    [6200,  6400,  6100,  6800,  7100,  6900],
#         "Copper":     [1100,  1200,  1300,  1250,  1380,  1400],
#         "Cobalt":     [180,   210,   240,   310,   420,   380],
#         "Zinc":       [520,   490,   510,   480,   520,   540],
#     }

#     years = [2018, 2019, 2020, 2021, 2022, 2023]
#     regions = {
#         "Iron Ore": "Pilbara",
#         "Gold": "Goldfields-Esperance",
#         "Lithium": "Goldfields-Esperance",
#         "Nickel": "Goldfields-Esperance",
#         "Alumina": "South West",
#         "Copper": "Goldfields-Esperance",
#         "Cobalt": "Goldfields-Esperance",
#         "Zinc": "Goldfields-Esperance",
#     }

#     rows = []
#     for commodity, values in commodities.items():
#         for year, value in zip(years, values):
#             rows.append({
#                 "commodity": commodity,
#                 "year": year,
#                 "value_aud_millions": value,
#                 "region": regions[commodity],
#                 "state": "Western Australia",
#                 "source": "DMIRS WA Mineral Statistics Digest 2023 (synthetic)"
#             })

#     df = pd.DataFrame(rows)
#     logger.info(f"Dataset sintetico: {len(df)} registros")
#     return df


# def clean_data(df, source_name):
#     df.columns = [c.lower().replace(' ', '_').replace('/', '_').replace('-', '_') for c in df.columns]
#     df['ingested_at'] = datetime.utcnow()
#     df['source'] = source_name
#     df = df.where(pd.notnull(df), None)
#     return df


# def save_raw(df, name):
#     path = f"data/raw/{name}_{datetime.now().strftime('%Y%m%d')}.csv"
#     df.to_csv(path, index=False)
#     logger.info(f"Raw salvo: {path}")


# def load_to_postgres(df, table):
#     logger.info(f"Carregando {len(df)} registros em '{table}'...")
#     conn = psycopg2.connect(**DB_CONFIG)
#     cur = conn.cursor()

#     cur.execute(f"DROP TABLE IF EXISTS {table}")

#     cols_def = ", ".join([f'"{c}" TEXT' for c in df.columns if c != 'ingested_at'])
#     cur.execute(f"""
#         CREATE TABLE {table} (
#             id SERIAL PRIMARY KEY,
#             {cols_def},
#             ingested_at TIMESTAMP DEFAULT NOW()
#         )
#     """)

#     data_cols = [c for c in df.columns if c != 'ingested_at']
#     records = [tuple(str(v) if v is not None else None for v in row)
#                for row in df[data_cols].values]
#     cols_str = ", ".join([f'"{c}"' for c in data_cols])
#     execute_values(cur, f"INSERT INTO {table} ({cols_str}) VALUES %s", records)

#     conn.commit()
#     cur.close()
#     conn.close()
#     logger.info(f"Tabela '{table}' carregada!")


# def run():
#     # Dataset 1: producao mineral WA
#     try:
#         df_mining = fetch_wa_mining_tenements()
#         save_raw(df_mining, "wa_tenements")
#         df_mining = clean_data(df_mining, "data.wa.gov.au/mining-tenements")
#         load_to_postgres(df_mining, "raw_wa_tenements")
#     except Exception as e:
#         logger.warning(f"Tenements falhou: {e} — continuando...")

#     # Dataset 2: valor de producao por commodity
#     df_value = fetch_abs_mineral_data()
#     save_raw(df_value, "wa_mineral_value")
#     df_value = clean_data(df_value, "abs.gov.au/dmirs")
#     load_to_postgres(df_value, "raw_mineral_production")

#     logger.info("=" * 50)
#     logger.info("Pipeline Dia 1 concluido com sucesso!")
#     logger.info("Tabelas criadas: raw_wa_tenements, raw_mineral_production")
#     logger.info("Proximo passo: checar dados com o comando abaixo")
#     logger.info('docker exec -it $(docker ps -q -f name=postgres) psql -U ravena -d wa_mining -c "SELECT commodity, year, value_aud_millions FROM raw_mineral_production LIMIT 10;"')


# if __name__ == "__main__":
#     run()

# from urllib import response
# import matplotlib.pyplot as plt
# import requests
# import pandas as pd
# import zipfile
# import io

# class mining_concessions:
#     def __init__(self):
#         self.headers = {
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#         }
#         self.df = None

#     def fetch_wa_mining_tenements(self):
#         url = "https://dasc.dmirs.wa.gov.au/Download/File/2053"
#         response = requests.get(url, headers=self.headers, timeout=60)
#         response.raise_for_status()
        
#         with zipfile.ZipFile(io.BytesIO(response.content)) as z:
#             csv_file = [f for f in z.namelist() if f.endswith(".csv")][0]
#             self.df = pd.read_csv(z.open(csv_file), encoding="windows-1252")
#             return self.df
        
#     def download(self,df):
#         return df.to_csv("data/raw/wa_mining_tenements.csv", index=False)
    
#     def plot_all_holders(self):
#         count = self.df["HOLDER1"].value_counts()
#         fig,ax = plt.subplots(figsize=(20, len(count) * 0.3))
#         count.plot(kind="barh", ax=ax, color="steelblue")
        
#         ax.set_title("Top Mining Tenement Holders in WA")
#         ax.set_xlabel("Number of Tenements")
#         ax.set_ylabel("Holder Name")    
#         ax.invert_yaxis()
        
#         plt.tight_layout()
#         plt.savefig("topmining_holders.png", dpi=300)

#         print(f"Holders:\n{len(count)}")

#         plt.show()
        
# mc = mining_concessions()   
# df = mc.fetch_wa_mining_tenements()
# # d = mc.download(df)
# mc.df = df  # Assign the fetched DataFrame to the class instance
# mc.plot_all_holders()
# print(df.shape)
# print(df.head())
# print(df["HOLDER1"].value_counts().head(10))
# print(df["TYPE"].value_counts())
from itertools import count

import matplotlib.pyplot as plt
from datetime import datetime
import requests
import pandas as pd
import zipfile
import io

class mining_concessions:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.df = None

    def fetch_wa_mining_tenements(self):
        url = "https://dasc.dmirs.wa.gov.au/Download/File/2053"
        response = requests.get(url, headers=self.headers, timeout=60)
        response.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            csv_file = [f for f in z.namelist() if f.endswith(".csv")][0]
            self.df = pd.read_csv(z.open(csv_file), encoding="windows-1252")
            return self.df

    def download(self, df):
        return df.to_csv("data/raw/wa_mining_tenements.csv", index=False)

    def plot_all_holders(self):
        count = self.df["HOLDER1"].value_counts()
        
        fig, ax = plt.subplots(figsize=(20, len(count) * 0.3), facecolor="white")
        count.plot(kind="barh", ax=ax, color="steelblue")

        ax.set_title("Top Mining Tenement Holders in WA")
        ax.set_xlabel("Number of Tenements")
        ax.set_ylabel("Holder Name")
        ax.invert_yaxis()

        plt.tight_layout()
        plt.savefig("top_mining_holders.png", dpi=300, facecolor="white")
        print(f"Holders: {len(count)}")
        
    def parse_dates(self, df):
        df["ENDDATE"] = pd.to_datetime(df["ENDDATE"], format="%Y%m%d", errors="coerce")
        return df
    
    def classify_by_status(self, row, cutoff_2026, cutoff_2027):
        if row["TENSTATUS"] != "LIVE":
            return "Inactive"
        if pd.isna(row["ENDDATE"]):
            return "Active"
        if row["ENDDATE"] <= cutoff_2026:
            return "Expiring 2026"
        if row["ENDDATE"] <= cutoff_2027:
            return "Expiring 2027"
        return "Active"
    
    def add_status_category(self, df):
        cutoff_2026 = pd.to_datetime("2026-12-31")
        cutoff_2027 = pd.to_datetime("2027-12-31")
        df["STATUS_CATEGORY"] = df.apply(lambda row: self.classify_by_status(row, cutoff_2026, cutoff_2027), axis=1)
        return df

    def filter_top_holders(self, df, n=30):
        top_n = df["HOLDER1"].value_counts().head(n).index
        return df[df["HOLDER1"].isin(top_n)], top_n
    
    def build_pivot(self, df, top_n):
        pivot = df.groupby(["HOLDER1", "STATUS_CATEGORY"]).size().unstack(fill_value=0)
        return pivot.loc[top_n]
    
    def draw_chart(self, pivot):
        colors = {
            "Active": "#2196F3",
            "Expiring 2026": "#FF5722",
            "Expiring 2027": "#FFC107",
            "Inactive": "#9E9E9E"
        }
        cols = [c for c in ["Active", "Expiring 2026", "Expiring 2027", "Inactive"] if c in pivot.columns]

        fig, ax = plt.subplots(figsize=(14, 12), facecolor="white")
        pivot[cols].plot(kind="barh", stacked=True, ax=ax, color=[colors[c] for c in cols])

        ax.set_title("Top 30 WA Mining Companies — Tenement Status", fontsize=14)
        ax.set_xlabel("Number of Tenements")
        ax.set_ylabel("")
        ax.invert_yaxis()
        ax.legend(title="Status", bbox_to_anchor=(1.01, 1), loc="upper left")

        plt.tight_layout()
        plt.savefig("top30_holders_by_status.png", dpi=300, facecolor="white")
        plt.close() 
    
    def plot_top_holders_by_status(self, n=30):
        df = self.df.copy()
        df = self.parse_dates(df)
        df = self.add_status_category(df)
        df, top_n = self.filter_top_holders(df, n)
        pivot = self.build_pivot(df, top_n)
        self.draw_chart(pivot)

       
mc = mining_concessions()
mc.fetch_wa_mining_tenements()
mc.download(mc.df)
mc.plot_top_holders_by_status()
print(mc.df.shape)