import pandas as pd
import numpy as np
import yaml
import datetime
import matplotlib.pyplot as plt
import os
import re

with open("config/config.yaml", "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)

def transformar_datos_proyecciones_poblacion_dane(df:pd.DataFrame) -> pd.DataFrame:

    #1. renombrar las columnas de acuerdo a listado
    columns_rename = {
    "DP": "COD_DPTO",
    "DPNOM": "NOM_DPTO",
    "MPIO": "COD_MPIO",
    "DPMP": "NOM_MPIO",
    "AÑO": "ANIO",
    "Total": "TOTAL_POBLACION",    
    "Hombres": "TOTAL_HOMBRES",
    "Mujeres": "TOTAL_MUJERES"
    }

    df = df.rename(columns=columns_rename)



    # 2.convertir a entero desde TOTAL_POBLACION en adelante (las llaves quedan como texto)
    cols_num = df.columns[
        df.columns.get_loc("TOTAL_POBLACION"):
    ]
    df[cols_num] = (
        df[cols_num].apply(pd.to_numeric).astype("Int64")
    )
    
    #  3.calcular poblacion por sexo y rango de edad (cada columna trae sexo y edad en el nombre)
        # \s+ porque 'Total 100 años  y más' viene con doble espacio en la fuente
    patron_edad = r"^(Hombres|Mujeres|Total) (\d+) años?(?:\s+y más)?$"

    def cols_edad(sexo, edad_min, edad_max):    
        return [c for c in df.columns
                if (m := re.match(patron_edad, c)) and m.group(1) == sexo and edad_min <= int(m.group(2)) <= edad_max]

    df["HOMBRES_65_MAS"] = df[cols_edad("Hombres", 65, 100)].sum(axis=1)
    df["MUJERES_65_MAS"] = df[cols_edad("Mujeres", 65, 100)].sum(axis=1)
    df["HOMBRES_0_15"] = df[cols_edad("Hombres", 0, 15)].sum(axis=1)
    df["MUJERES_0_15"] = df[cols_edad("Mujeres", 0, 15)].sum(axis=1)

    df["TOTAL_65_MAS"] = df["HOMBRES_65_MAS"] + df["MUJERES_65_MAS"]
    df["TOTAL_0_15"] = df["HOMBRES_0_15"] + df["MUJERES_0_15"]

    # eliminar el detalle por edad (0 a 100 y más) de hombres, mujeres y total
    columnas_detalle_edad = [c for c in df.columns if re.match(patron_edad, c)]
    df = df.drop(columns=columnas_detalle_edad)

    
    ##guardar en silver y sobreescribir si existe
    df.to_csv(config["paths"]["silver_dir"] + "/datos_proyecciones_poblacion_dane_clean.csv", index=False)
    print("Archivo datos_proyecciones_poblacion_dane_clean.csv guardado en silver.")




    return df

def transformar_datos_relacion_ips_capacidad_instalada(df_ips: pd.DataFrame, df_divipola: pd.DataFrame,) -> pd.DataFrame:

    # aplicar mayúsculas a las columnas de texto
    columnas_texto = ['Departamento','naturaleza','nom descripcion capacidad ']
    # Convertir columnas de texto en mayúsculasc con un for 
    for col in columnas_texto:
        df_ips[col] = df_ips[col].apply(lambda x: x.upper() if isinstance(x, str) else x)

    
    # convertir las columnas a texto
    df_divipola = df_divipola.astype(str)
    # quitar tildes a las columnas seleccionadas
    df_divipola[['NOMBRE_DPTO','NOMBRE_MUN']] = df_divipola[['NOMBRE_DPTO','NOMBRE_MUN']].apply(lambda x: x.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8'))

    # quitar tildes a las columnas seleccionadas
    df_ips[['Departamento','Municipio']] = df_ips[['Departamento','Municipio']].apply(lambda x: x.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8'))
    

    ## correciones de los departamentos que estan en IPS y no en divipola
    valores_cambiar = {'BUENAVENTURA':'VALLE DEL CAUCA',
                   'CALI':'VALLE DEL CAUCA',
                   'BARRANQUILLA':'ATLANTICO',
                   'BOGOTA D.C':'BOGOTA, D.C.',
                   'SANTA MARTA':'MAGDALENA',
                   'CARTAGENA':'BOLIVAR',
                   'SAN ANDRES Y PROVIDENCIA':'ARCHIPIELAGO DE SAN ANDRES, PROVIDENCIA Y SANTA CATALINA'
                  }

    # Aplicar las correcciones a la columna de departamentos en la tabla df_ips
    df_ips['Departamento'] = df_ips['Departamento'].replace(valores_cambiar)

    ## correciones de los municipios en la tabla df_ips
    valores_cambiar = {'BARRANCO MINAS': 'BARRANCOMINAS',
                   'LEGUIZAMO': 'PUERTO LEGUIZAMO',
                   'LOPEZ': 'LOPEZ DE MICAY',
                   'BOGOTA': 'BOGOTA, D.C.',
                   'PURISIMA': 'PURISIMA DE LA CONCEPCION',
                   'MOMPOS': 'SANTA CRUZ DE MOMPOX',
                   'CALI': 'SANTIAGO DE CALI',
                   'SINCE': 'SAN LUIS DE SINCE',
                   'SAN VICENTE': 'SAN VICENTE FERRER',
                   'SAN ANDRES SOTAVENTO': 'SAN ANDRES DE SOTAVENTO',
                   'TOLU VIEJO': 'SAN JOSE DE TOLUVIEJO',
                   'CUASPUD': 'CUASPUD CARLOSAMA',
                   'CARTAGENA': 'CARTAGENA DE INDIAS',
                   'GUICAN': 'GUICAN DE LA SIERRA',
                   'SANTAFE DE ANTIOQUIA': 'SANTA FE DE ANTIOQUIA',
                   'CERRO SAN ANTONIO': 'CERRO DE SAN ANTONIO',
                   'DON MATIAS': 'DONMATIAS',
                   'CHIBOLO': 'CHIVOLO',
                   'SAN JUAN DE RIO SECO': 'SAN JUAN DE RIOSECO',
                   'PIENDAMO': 'PIENDAMO - TUNIA',
                   'MARIQUITA': 'SAN SEBASTIAN DE MARIQUITA',
                   'CUCUTA': 'SAN JOSE DE CUCUTA',
                   'SOTARA': 'SOTARA ',
                   'TUMACO': 'SAN ANDRES DE TUMACO'
                  }

     # Aplicar las correcciones a la columna de municipios en la tabla df_ips
    df_ips['Municipio'] = df_ips['Municipio'].replace(valores_cambiar)
    
    # merge entre df_ips y df_divipola para traer COD_MUN, COD_DPTO tomando como llave Departamento y Municipio
    df_ips = df_ips.merge(df_divipola[['COD_MUN', 'COD_DPTO', 'NOMBRE_MUN', 'NOMBRE_DPTO']],
                                            left_on=['Departamento', 'Municipio'],
                                            right_on=['NOMBRE_DPTO', 'NOMBRE_MUN'],
                                            how='left')
    df_ips.drop(columns=['NOMBRE_MUN', 'NOMBRE_DPTO'], inplace=True)

    ##guardar en silver
    df_ips.to_csv(config["paths"]["silver_dir"] + "/datos_relacion_ips_capacidad_instalada_clean.csv", index=False)
    print("Archivo datos_relacion_ips_capacidad_instalada_clean.csv guardado en silver.")

    return df_ips



def transformar_registro_prestadores_salud(df:pd.DataFrame) -> pd.DataFrame:

    df=df.astype(str)

        ##guardar en silver
    df.to_csv(config["paths"]["silver_dir"] + "/registro_prestadores_salud_clean.csv", index=False)
    print("Archivo registro_prestadores_salud_clean.csv guardado en silver.")

    return df

def transformar_divipola(df:pd.DataFrame) -> pd.DataFrame:

    df=df.astype(str)

        ##guardar en silver
    df.to_csv(config["paths"]["silver_dir"] + "/divipola_clean.csv", index=False)
    print("Archivo divipola_clean.csv guardado en silver.")

    return df

def transformar_tiempo(df:pd.DataFrame) -> pd.DataFrame:

    #convertir a texto las columnas
    df=df.astype(str)

    #quitar columna dias_con_venta
    df = df.drop(columns=['dias_con_venta'])

    #dejar la columna fecha como datetime
    #df['fecha'] = pd.to_datetime(df['fecha'],errors='coerce')

    ##guardar en silver
    df.to_csv(config["paths"]["silver_dir"] + "/tiempo_clean.csv", index=False)
    print("Archivo tiempo_clean.csv guardado en silver.")

    return df