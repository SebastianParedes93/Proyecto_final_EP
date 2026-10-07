import pandas as pd
import numpy as np
import yaml
import re

with open("config/config.yaml", "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)


def transformar_datos_proyecciones_poblacion_dane(df: pd.DataFrame) -> pd.DataFrame:

    # 1. renombrar las columnas de acuerdo a listado
    columns_rename = {
        "DP": "COD_DPTO",
        "DPNOM": "NOM_DPTO",
        "MPIO": "COD_MPIO",
        "DPMP": "NOM_MPIO",
        "AÑO": "ANIO",
        "Total": "TOTAL_POBLACION",
        "Hombres": "TOTAL_HOMBRES",
        "Mujeres": "TOTAL_MUJERES",
    }
    df = df.rename(columns=columns_rename)

    # 2. convertir a entero desde TOTAL_POBLACION en adelante (las llaves quedan como texto)
    cols_num = df.columns[df.columns.get_loc("TOTAL_POBLACION"):]
    df[cols_num] = df[cols_num].apply(pd.to_numeric).astype("Int64")

    # 3. calcular poblacion por sexo y rango de edad
    patron_edad = r"^(Hombres|Mujeres|Total) (\d+) años?(?:\s+y más)?$"

    def cols_edad(sexo, edad_min, edad_max):
        return [c for c in df.columns
                if (m := re.match(patron_edad, c)) and m.group(1) == sexo
                and edad_min <= int(m.group(2)) <= edad_max]

    df["HOMBRES_65_MAS"] = df[cols_edad("Hombres", 65, 100)].sum(axis=1)
    df["MUJERES_65_MAS"] = df[cols_edad("Mujeres", 65, 100)].sum(axis=1)
    df["HOMBRES_0_15"] = df[cols_edad("Hombres", 0, 15)].sum(axis=1)
    df["MUJERES_0_15"] = df[cols_edad("Mujeres", 0, 15)].sum(axis=1)

    df["TOTAL_65_MAS"] = df["HOMBRES_65_MAS"] + df["MUJERES_65_MAS"]
    df["TOTAL_0_15"] = df["HOMBRES_0_15"] + df["MUJERES_0_15"]

    # eliminar el detalle por edad
    columnas_detalle_edad = [c for c in df.columns if re.match(patron_edad, c)]
    df = df.drop(columns=columnas_detalle_edad)

    # guardar en silver
    df.to_csv(config["paths"]["silver_dir"] + "/datos_proyecciones_poblacion_dane_clean.csv", index=False)
    print("Archivo datos_proyecciones_poblacion_dane_clean.csv guardado en silver.")

    return df


def transformar_datos_relacion_ips_capacidad_instalada(df_ips: pd.DataFrame, df_divipola: pd.DataFrame) -> pd.DataFrame:

    # llave a texto, sin espacios y sin '.0' final
    df_ips['Código sede'] = (
        df_ips['Código sede']
        .astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )

    # mayúsculas en columnas de texto
    columnas_texto = ['Departamento', 'naturaleza', 'nom descripcion capacidad ']
    for col in columnas_texto:
        df_ips[col] = df_ips[col].apply(lambda x: x.upper() if isinstance(x, str) else x)

    # divipola a texto y UNA fila por municipio (evita multiplicar filas en el merge)
    df_divipola = df_divipola.astype(str)
    df_divipola = df_divipola.drop_duplicates(subset=['COD_MUN'])

    # quitar tildes
    df_divipola[['NOMBRE_DPTO', 'NOMBRE_MUN']] = df_divipola[['NOMBRE_DPTO', 'NOMBRE_MUN']].apply(
        lambda x: x.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8'))
    df_ips[['Departamento', 'Municipio']] = df_ips[['Departamento', 'Municipio']].apply(
        lambda x: x.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8'))

    # correcciones de departamentos
    valores_cambiar = {'BUENAVENTURA': 'VALLE DEL CAUCA',
                       'CALI': 'VALLE DEL CAUCA',
                       'BARRANQUILLA': 'ATLANTICO',
                       'BOGOTA D.C': 'BOGOTA, D.C.',
                       'SANTA MARTA': 'MAGDALENA',
                       'CARTAGENA': 'BOLIVAR',
                       'SAN ANDRES Y PROVIDENCIA': 'ARCHIPIELAGO DE SAN ANDRES, PROVIDENCIA Y SANTA CATALINA'}
    df_ips['Departamento'] = df_ips['Departamento'].replace(valores_cambiar)

    # correcciones de municipios
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
                       'TUMACO': 'SAN ANDRES DE TUMACO'}
    df_ips['Municipio'] = df_ips['Municipio'].replace(valores_cambiar)

    # merge para traer COD_MUN y COD_DPTO
    n_antes = len(df_ips)
    df_ips = df_ips.merge(df_divipola[['COD_MUN', 'COD_DPTO', 'NOMBRE_MUN', 'NOMBRE_DPTO']],
                          left_on=['Departamento', 'Municipio'],
                          right_on=['NOMBRE_DPTO', 'NOMBRE_MUN'],
                          how='left')
    df_ips.drop(columns=['NOMBRE_MUN', 'NOMBRE_DPTO'], inplace=True)
    print(f"Filas antes del merge: {n_antes}, después: {len(df_ips)}")
    if len(df_ips) != n_antes:
        raise ValueError("El merge con divipola duplicó filas de capacidad instalada")

    # guardar en silver
    df_ips.to_csv(config["paths"]["silver_dir"] + "/datos_relacion_ips_capacidad_instalada_clean.csv", index=False)
    print("Archivo datos_relacion_ips_capacidad_instalada_clean.csv guardado en silver.")

    return df_ips


def transformar_registro_prestadores_salud(df: pd.DataFrame) -> pd.DataFrame:

    df = df.astype(str)

    # una fila por sede (es la PK de la tabla)
    df = df[df['CodigoHabilitacionSede'] != 'nan']
    df = df.drop_duplicates(subset=['CodigoHabilitacionSede'])

    df.to_csv(config["paths"]["silver_dir"] + "/registro_prestadores_salud_clean.csv", index=False)
    print("Archivo registro_prestadores_salud_clean.csv guardado en silver.")

    return df


def transformar_divipola(df: pd.DataFrame) -> pd.DataFrame:

    df = df.astype(str)

    # quitar duplicados por la columna COD_MUN
    df = df.drop_duplicates(subset=['COD_MUN'])

    df.to_csv(config["paths"]["silver_dir"] + "/divipola_clean.csv", index=False)
    print("Archivo divipola_clean.csv guardado en silver.")

    return df


def transformar_tiempo(df: pd.DataFrame) -> pd.DataFrame:

    df = df.astype(str)

    # quitar duplicados por periodo
    df = df.drop_duplicates(subset=['periodo'])

    # quitar columna dias_con_venta
    df = df.drop(columns=['dias_con_venta'])

    df.to_csv(config["paths"]["silver_dir"] + "/tiempo_clean.csv", index=False)
    print("Archivo tiempo_clean.csv guardado en silver.")

    return df