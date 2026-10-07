import pandas as pd
import yaml

with open("config/config.yaml", "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)


def transformar_datos_a_gold(df: pd.DataFrame, cols: list) -> pd.DataFrame:

    df_gold = df.copy()

    # Quitar columnas según la lista cols
    if cols:
        df_gold = df_gold.drop(columns=cols, errors='ignore')

    # guardar según el tipo de tabla
    if "num cantidad capacidad instalada" in df_gold.columns:
        df_gold.to_csv(config["paths"]["gold_dir"] + "/capacidad_instalada_goldfile.csv", index=False)
        print("Archivo capacidad_instalada_goldfile.csv guardado en gold.")
    elif "ClasePrestadorDesc" in df_gold.columns:
        df_gold.to_csv(config["paths"]["gold_dir"] + "/registro_prestadores_salud_goldfile.csv", index=False)
        print("Archivo registro_prestadores_salud_goldfile.csv guardado en gold.")
    elif "LONG" in df_gold.columns:
        df_gold.to_csv(config["paths"]["gold_dir"] + "/divipola_goldfile.csv", index=False)
        print("Archivo divipola_goldfile.csv guardado en gold.")
    elif list(df_gold.columns) == ["periodo"]:
        df_gold.to_csv(config["paths"]["gold_dir"] + "/tiempo_goldfile.csv", index=False)
        print("Archivo tiempo_goldfile.csv guardado en gold.")

    return df_gold


def guardar_datos_gold(df_gold: pd.DataFrame, nombre_archivo: str) -> pd.DataFrame:
    df_gold.to_csv(config["paths"]["gold_dir"] + f"/{nombre_archivo}", index=False)
    print(f"Archivo {nombre_archivo} guardado en gold.")
    return df_gold