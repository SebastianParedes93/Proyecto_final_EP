# importar librerias

import pandas as pd
import numpy as np
import yaml
import datetime
import matplotlib.pyplot as plt
import os
import re
import datetime


# importar mis modulos (extract, load, transform)
import src.extract.extract_source as datos
import src.transform.clean as transform



def main():

    #0. leer mi archivo yaml para obtener la configuración
    with open("config/config.yaml", "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    # extraer los datos de las diferentes fuentes usando el modulo extract (datos)

    # extraer los datos de proyecciones_poblacion_dane
    print("Extrayendo datos de proyecciones_poblacion_dane...")
    df_proyecciones_poblacion_dane = datos.extraer_datos(config["sources"]["proyecciones_poblacion_dane"]["path"], config["sources"]["proyecciones_poblacion_dane"]["sheetname"])
    print(df_proyecciones_poblacion_dane)
    print("Datos de proyecciones_poblacion_dane cargados correctamente")

    # extraer los datos de relacion_ips_capacidad_instalada
    print("Extrayendo datos de relacion_ips_capacidad_instalada...")
    df_relacion_ips_capacidad_instalada = datos.extraer_datos(config["sources"]["relacion_ips_capacidad_instalada"]["path"])
    print(df_relacion_ips_capacidad_instalada)
    print("Datos de relacion_ips_capacidad_instalada cargados correctamente")

    # extraer los datos de registro_prestadores_salud
    print("Extrayendo datos de registro_prestadores_salud...")
    df_registro_prestadores_salud = datos.extraer_datos(config["sources"]["registro_prestadores_salud"]["path"], config["sources"]["registro_prestadores_salud"]["sheetname"])
    print(df_registro_prestadores_salud)
    print("Datos de registro_prestadores_salud cargados correctamente")

    # extraer los datos de divipola
    print("Extrayendo datos de divipola...")
    df_divipola = datos.extraer_datos(config["sources"]["divipola"]["path"], config["sources"]["divipola"]["sheetname"])
    print(df_divipola)
    print("Datos de divipola cargados correctamente")

    # extraer los datos de tiempo
    print("Extrayendo datos de tiempo...")  
    df_tiempo = datos.extraer_datos(config["sources"]["tiempo"]["path"])
    print(df_tiempo)
    print("Datos de tiempo cargados correctamente")


    # 1. transformar los datos (transform)

    # transformar los datos usando el modulo transform (transform)
    
    print("Transformando datos de proyecciones_poblacion_dane...")
    df_transformado_proyecciones_poblacion_dane = transform.transformar_datos_proyecciones_poblacion_dane(df_proyecciones_poblacion_dane)
    print(df_transformado_proyecciones_poblacion_dane)
    print("Datos de proyecciones_poblacion_dane transformados correctamente")

    print("Transformando datos de relacion_ips_capacidad_instalada...")
    df_transformado_relacion_ips_capacidad_instalada = transform.transformar_datos_relacion_ips_capacidad_instalada(df_relacion_ips_capacidad_instalada, df_divipola)
    print(df_transformado_relacion_ips_capacidad_instalada)
    print("Datos de relacion_ips_capacidad_instalada transformados correctamente")

    print("Transformando datos de registro_prestadores_salud...")
    df_transformado_registro_prestadores_salud = transform.transformar_registro_prestadores_salud(df_registro_prestadores_salud)
    print(df_transformado_registro_prestadores_salud)
    print("Datos de registro_prestadores_salud transformados correctamente")

    print("Transformando datos de divipola...")
    df_transformado_divipola = transform.transformar_divipola(df_divipola)
    print(df_transformado_divipola)
    print("Datos de divipola transformados correctamente")

    print("Transformando datos de tiempo...")
    df_transformado_tiempo = transform.transformar_tiempo(df_tiempo)
    print(df_transformado_tiempo)
    print("Datos de tiempo transformados correctamente")



    # 2. guardar los datos transformados usando el modulo load (load)
   

if __name__ == "__main__":
    main()




