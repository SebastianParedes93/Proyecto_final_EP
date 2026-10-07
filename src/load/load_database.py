import re
import unicodedata

import numpy as np
import pandas as pd
from src.db import get_engine


def normalizar_columna(nombre: str) -> str:
    """'Teléfono Sede' -> 'telefono_sede'"""
    nombre = unicodedata.normalize("NFKD", str(nombre))
    nombre = nombre.encode("ascii", "ignore").decode("ascii")  # quita tildes y ñ
    nombre = nombre.strip().lower()
    nombre = re.sub(r"[^a-z0-9]+", "_", nombre)                # espacios y símbolos -> _
    return nombre.strip("_")


def load_gold(df: pd.DataFrame, tabla: str, modo: str = "replace"):
    df = df.copy()  # no modifica el DataFrame original

    # 1. Normalizar nombres de columnas
    df.columns = [normalizar_columna(c) for c in df.columns]

    duplicadas = df.columns[df.columns.duplicated()].tolist()
    if duplicadas:
        raise ValueError(f"Columnas duplicadas en {tabla} tras normalizar: {duplicadas}")

    # 2. Cadenas vacías o solo espacios -> NaN (se guardan como NULL)
    df = df.replace(r"^\s*$", np.nan, regex=True)

    # 3. Cargar a Supabase
    engine = get_engine()
    df.to_sql(
        tabla,
        engine,
        schema="gold",
        if_exists=modo,     # "replace" recrea la tabla, "append" agrega filas
        index=False,
        chunksize=1000,
        method="multi",
    )
    print(f"Cargada gold.{tabla}: {len(df)} filas, columnas: {list(df.columns)}")


def cargar_gold_a_database(tablas: dict, modo: str = "replace"):
    """Recibe un diccionario {nombre_tabla: DataFrame} y carga cada una."""
    for nombre, df in tablas.items():
        load_gold(df, nombre, modo)