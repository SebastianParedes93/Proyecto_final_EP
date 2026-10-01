import yaml
import pandas as pd
import openpyxl
import datetime

with open("config/config.yaml", "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)


def extraer_datos(ruta:str, sheet_name:str=None)->pd.DataFrame: 

    # validar si el archivo es excel o csv
    if ruta.endswith(".xlsx") or ruta.endswith(".xls"):
        df = pd.read_excel(ruta, sheet_name=sheet_name, dtype=str)
    elif ruta.endswith(".csv"):
        df = pd.read_csv(ruta, encoding='utf-8', sep=None, engine='python')
    else:
        raise ValueError("Formato de archivo no soportado")

    print("empezando a extraer datos")
    return df



#print(config)


# # 1. Carga del source proyecciones_poblacion_dane

# print('Cargando source proyecciones_poblacion_dane')
# print(config["sources"]["proyecciones_poblacion_dane"]["path"])
# df_proyecciones_poblacion_dane = pd.read_excel(config["sources"]["proyecciones_poblacion_dane"]["path"], sheet_name=config["sources"]["proyecciones_poblacion_dane"]["sheetname"])
# #print(df_proyecciones_poblacion_dane)

# # 2. Carga del source relacion_ips_capacidad_instalada

# print('Cargando source relacion_ips_capacidad_instalada')
# print(config["sources"]["relacion_ips_capacidad_instalada"]["path"])
# df_relacion_ips_capacidad_instalada = pd.read_csv(config["sources"]["relacion_ips_capacidad_instalada"]["path"])
# print(df_relacion_ips_capacidad_instalada)

# # 3. Carga del source registro_prestadores_salud

# print('Cargando source registro_prestadores_salud')
# print(config["sources"]["registro_prestadores_salud"]["path"])
# df_registro_prestadores_salud = pd.read_excel(config["sources"]["registro_prestadores_salud"]["path"], sheet_name=config["sources"]["registro_prestadores_salud"]["sheetname"])
# print(df_registro_prestadores_salud)

# # 4. Carga del source divipola

# print('Cargando source divipola')
# print(config["sources"]["divipola"]["path"])
# df_divipola = pd.read_excel(config["sources"]["divipola"]["path"], sheet_name=config["sources"]["divipola"]["sheetname"])
# print(df_divipola)

# # 5. Carga del source TIEMPO

# print('Cargando source TIEMPO')
# print(config["sources"]["tiempo"]["path"])
# df_tiempo = pd.read_excel(config["sources"]["tiempo"]["path"])
# print(df_tiempo)