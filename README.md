# Proyecto Final EP — Oferta de servicios de salud vs. población en Colombia

Pipeline ETL en Python que integra fuentes públicas de salud y demografía de Colombia en un modelo analítico unificado, siguiendo una **arquitectura Medallion** (bronze → silver → gold) y publicando la capa final en **Supabase (PostgreSQL)**.

**Autores:** Sebastian Paredes · Eduardo Villa · Alejandro Mosquera · Michael Escobar
**Licencia:** MIT

---

## Tabla de contenido

1. [Contexto del problema](#1-contexto-del-problema)
2. [Objetivo](#2-objetivo)
3. [Fuentes de datos](#3-fuentes-de-datos)
4. [Arquitectura y metodología](#4-arquitectura-y-metodología)
5. [Proceso ETL](#5-proceso-etl)
6. [Modelo de datos (capa gold)](#6-modelo-de-datos-capa-gold)
7. [Resultados: bronze vs. gold](#7-resultados-bronze-vs-gold)
8. [Stack tecnológico](#8-stack-tecnológico)
9. [Estructura del proyecto](#9-estructura-del-proyecto)
10. [Instalación y ejecución](#10-instalación-y-ejecución)
11. [Configuración](#11-configuración)
12. [Análisis exploratorio (EDA)](#12-análisis-exploratorio-eda)

---

## 1. Contexto del problema

En Colombia la información sobre oferta de servicios de salud y sobre población está dispersa en distintas entidades y formatos:

- El **DANE** publica las proyecciones de población por municipio, área, sexo y edad simple.
- El **Ministerio de Salud**, a través del **REPS** (Registro Especial de Prestadores de Servicios de Salud), publica los prestadores habilitados, sus sedes y la capacidad instalada (camas, salas, ambulancias, etc.).
- La **DIVIPOLA** define la codificación oficial de departamentos, municipios y centros poblados.

Estas fuentes no comparten un formato ni, en todos los casos, una llave común: algunas identifican el municipio por código DANE y otras solo por nombre (con tildes, abreviaturas y variaciones de escritura). Esto impide cruzar directamente la **oferta** (prestadores y capacidad instalada) con la **demanda potencial** (población, y en particular grupos de mayor necesidad de atención como **niños de 0 a 15 años** y **adultos mayores de 65 años**).

## 2. Objetivo

Construir un pipeline reproducible que:

1. **Extraiga** las fuentes oficiales en su formato original (Excel y CSV).
2. **Limpie y estandarice** los datos: nombres de columnas, tipos, texto, duplicados y homologación de nombres de municipios y departamentos.
3. **Integre** las fuentes mediante los códigos DANE de departamento y municipio.
4. **Derive** indicadores de población por grupos de edad relevantes para salud.
5. **Publique** un modelo analítico en una base de datos PostgreSQL listo para consultas, tableros y análisis.

## 3. Fuentes de datos

| # | Fuente | Entidad | Formato | Contenido |
|---|---|---|---|---|
| 1 | Proyecciones de población municipal | DANE | `.xlsx` (hoja `PobMunicipalxÁreaSexoEdad`) | Población por municipio, año (2018–2042), área geográfica, sexo y edad simple |
| 2 | Relación IPS — capacidad instalada | MinSalud (REPS) | `.csv` (`;`) | Capacidad instalada por sede de IPS (grupo, descripción y cantidad) |
| 3 | Registro Especial de Prestadores de Salud | MinSalud (REPS) | `.xlsx` (hoja `Registro_Especial_de_Prestadore`) | Prestadores y sedes habilitadas, naturaleza jurídica y clase de prestador |
| 4 | DIVIPOLA | DANE | `.xlsx` (hoja `Cabeceras - Centros Poblados`) | Códigos y nombres de departamentos, municipios y centros poblados, con coordenadas |
| 5 | Tiempo | Construida | `.csv` (`;`) | Calendario con atributos de fecha |

> El archivo de proyecciones DANE (~131 MB) no se versiona en GitHub por exceder el límite de tamaño; debe ubicarse manualmente en `data/bronze/`.

## 4. Arquitectura y metodología

El proyecto sigue la **arquitectura Medallion**, que organiza los datos en capas de calidad creciente:

```
 ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
 │   BRONZE     │     │   SILVER     │     │    GOLD      │     │  SUPABASE        │
 │ Datos crudos │ ──► │ Datos limpios│ ──► │ Datos para   │ ──► │  PostgreSQL      │
 │ (xlsx / csv) │     │ (csv)        │     │ consumo (csv)│     │  schema "gold"   │
 └──────────────┘     └──────────────┘     └──────────────┘     └──────────────────┘
     Extract            Transform            Transform              Load
                        (limpieza)           (selección)
```

| Capa | Propósito | Ubicación |
|---|---|---|
| **Bronze** | Copia fiel de las fuentes originales, sin modificaciones | `data/bronze/` |
| **Silver** | Datos limpios, tipados, estandarizados e integrados | `data/silver/` |
| **Gold** | Datos depurados, sin información de contacto, listos para análisis | `data/gold/` + Supabase |

### Metodología de trabajo

1. **Análisis exploratorio (EDA)** en `notebooks/EDA.ipynb`: se inspeccionó cada fuente, se identificaron inconsistencias (nombres de municipios distintos entre fuentes, columnas por edad simple, duplicados) y se diseñaron las reglas de limpieza.
2. **Modularización**: las reglas validadas en el notebook se trasladaron a módulos de Python separados por etapa (`extract`, `transform`, `load`).
3. **Configuración externa**: rutas, fuentes y hojas de Excel se definen en `config/config.yaml`, de modo que el código no depende de rutas fijas.
4. **Orquestación**: `main.py` ejecuta todas las etapas en orden para las cinco fuentes.
5. **Publicación**: la capa gold se carga a Supabase, con credenciales gestionadas mediante variables de entorno.

## 5. Proceso ETL

### 5.1 Extract — `src/extract/extract_source.py`

Función única `extraer_datos(ruta, sheet_name)` que selecciona el lector según la extensión del archivo:

- **Excel** (`.xlsx`, `.xls`): `pd.read_excel` leyendo todas las columnas como texto para preservar los códigos con ceros a la izquierda (p. ej. `05001`).
- **CSV**: `pd.read_csv` con detección automática del separador.

### 5.2 Transform → silver — `src/transform/clean.py`

**Proyecciones de población DANE**
- Renombrado de columnas a un estándar: `DP→COD_DPTO`, `DPNOM→NOM_DPTO`, `MPIO→COD_MPIO`, `DPMP→NOM_MPIO`, `AÑO→ANIO`, `Total→TOTAL_POBLACION`, `Hombres→TOTAL_HOMBRES`, `Mujeres→TOTAL_MUJERES`.
- Conversión de los conteos a enteros; los códigos se mantienen como texto.
- Cálculo de grupos de edad mediante expresiones regulares sobre los nombres de columna (`Hombres 15 años`, `Mujeres 100 años y más`, …):
  - `HOMBRES_0_15`, `MUJERES_0_15`, `TOTAL_0_15`
  - `HOMBRES_65_MAS`, `MUJERES_65_MAS`, `TOTAL_65_MAS`
- Eliminación de las columnas de detalle por edad simple.

**Relación IPS — capacidad instalada**
- Estandarización de la llave `Código sede` como texto.
- Conversión a mayúsculas y eliminación de tildes (normalización Unicode NFKD) en departamento y municipio, igual que en DIVIPOLA.
- Homologación de nombres de departamentos y municipios hacia los nombres oficiales de DIVIPOLA (p. ej. `CALI → SANTIAGO DE CALI`, `CUCUTA → SAN JOSE DE CUCUTA`, `BOGOTA → BOGOTA, D.C.`).
- Cruce con DIVIPOLA por (departamento, municipio) para incorporar `COD_MUN` y `COD_DPTO`.
- Validación de integridad: el proceso se detiene si el cruce duplica registros.

**Registro de prestadores de salud (REPS)**
- Conversión a texto, eliminación de registros sin código de habilitación de sede y deduplicación por `CodigoHabilitacionSede`.

**DIVIPOLA**
- Conversión a texto y deduplicación por `COD_MUN`, obteniendo un registro por municipio.

**Tiempo**
- Deduplicación por `periodo` y eliminación de la columna `dias_con_venta`.

### 5.3 Transform → gold — `src/transform/gold_data.py`

Selección final de columnas para cada tabla:

| Tabla | Columnas eliminadas |
|---|---|
| Capacidad instalada | Departamento, Municipio (reemplazados por códigos), dígito de verificación, gerente, dirección, email, teléfono |
| Prestadores de salud | Dirección, email y teléfono de la sede |
| DIVIPOLA | Código, nombre y tipo de centro poblado |
| Tiempo | Atributos de calendario (se conserva `periodo`) |
| Proyecciones DANE | — (se guarda completa desde silver) |

Se excluye la información de contacto personal (nombres, correos, teléfonos y direcciones) de la capa de consumo.

### 5.4 Load — `src/load/load_database.py`

1. **Normalización de nombres de columna** a `snake_case` ASCII, compatible con PostgreSQL (`Teléfono Sede → telefono_sede`, `ÁREA GEOGRÁFICA → area_geografica`), validando que no se generen nombres duplicados.
2. **Tratamiento de vacíos**: cadenas vacías o con solo espacios se convierten a `NULL`.
3. **Carga** con `pandas.to_sql` sobre SQLAlchemy al esquema `gold`, en lotes de 1.000 filas con inserción múltiple. Por defecto la tabla se recrea en cada ejecución (`replace`).

## 6. Modelo de datos (capa gold)

Las tablas forman un modelo en estrella, con dos tablas de hechos y tres dimensiones:

```
                        ┌───────────────────────┐
                        │    dim: divipola      │
                        │ cod_dpto, nombre_dpto │
                        │ cod_mun (PK)          │
                        │ nombre_mun, lat, long │
                        └──────────┬────────────┘
                     cod_mpio      │      cod_mun
             ┌─────────────────────┴──────────────────────┐
┌────────────┴──────────────────┐          ┌──────────────┴───────────────────┐
│ hecho: proyecciones_poblacion │          │ hecho: capacidad_instalada       │
│ cod_dpto, cod_mpio, anio      │          │ código prestador, código sede    │
│ area_geografica               │          │ naturaleza, nivel de atención    │
│ total_poblacion, hombres,     │          │ grupo y descripción de capacidad │
│ mujeres, grupos 0–15 y 65+    │          │ cantidad capacidad instalada     │
└────────────┬──────────────────┘          └──────────────┬───────────────────┘
             │ anio                                       │ sede
┌────────────┴──────────┐                  ┌──────────────┴───────────────────┐
│   dim: tiempo         │                  │ dim: registro_prestadores_salud  │
│   periodo             │                  │ codigohabilitacionsede (PK)      │
└───────────────────────┘                  │ prestador, naturaleza, clase     │
                                           └──────────────────────────────────┘
```

| Tabla | Tipo | Granularidad |
|---|---|---|
| `gold.proyecciones_poblacion_dane` | Hecho | Municipio × año × área geográfica |
| `gold.capacidad_instalada` | Hecho | Sede × tipo de capacidad |
| `gold.registro_prestadores_salud` | Dimensión | Sede de prestador |
| `gold.divipola` | Dimensión | Municipio |
| `gold.tiempo` | Dimensión | Año |

## 7. Resultados: bronze vs. gold

| Fuente | Filas (bronze → gold) | Columnas (bronze → gold) | Tamaño en disco | Principal aporte |
|---|---|---|---|---|
| Proyecciones DANE | 84.150 → 84.150 | 312 → 15 | 131,5 MB → 8,1 MB | Agregación por grupos de edad; 6 variables nuevas; reducción de memoria ~19× |
| Capacidad instalada | 41.427 → 41.427 | 20 → 15 | 15,7 MB → 11,4 MB | Incorporación de `COD_MUN` y `COD_DPTO`, que habilitan el cruce con población |
| Prestadores (REPS) | 76.821 → 76.821 | 22 → 19 | 12,3 MB (xlsx) → 23,9 MB (csv) | Exclusión de datos de contacto; una fila por sede |
| DIVIPOLA | 8.560 → 1.122 | 9 → 6 | 1,1 MB → 0,1 MB | Dimensión a nivel municipio con coordenadas |
| Tiempo | 3.667 → 25 | 17 → 1 | 0,3 MB → <0,1 MB | Dimensión de años alineada con las proyecciones |

## 8. Stack tecnológico

| Categoría | Herramienta | Versión |
|---|---|---|
| Lenguaje | Python | 3.13 |
| Manipulación de datos | pandas | 3.0 |
| Cálculo numérico | NumPy | 2.5 |
| Lectura de Excel | openpyxl | 3.1 |
| Configuración | PyYAML | 6.0 |
| Variables de entorno | python-dotenv | 1.2 |
| Conexión a base de datos | SQLAlchemy + psycopg2 | 2.1 |
| Base de datos | Supabase (PostgreSQL) | — |
| Exploración | Jupyter Notebook + Matplotlib | 3.11 |

Las versiones exactas de todas las dependencias están en `requirements.txt`.

## 9. Estructura del proyecto

```
Proyecto_final_EP/
├── main.py                        # Orquestador del pipeline ETL
├── config/
│   └── config.yaml                # Metadatos, rutas y definición de las fuentes
├── src/
│   ├── db.py                      # Conexión a Supabase (SQLAlchemy engine)
│   ├── extract/
│   │   └── extract_source.py      # Lectura de fuentes xlsx / csv
│   ├── transform/
│   │   ├── clean.py               # Limpieza e integración → silver
│   │   └── gold_data.py           # Selección de columnas → gold
│   └── load/
│       └── load_database.py       # Normalización y carga a PostgreSQL
├── data/
│   ├── bronze/                    # Fuentes originales
│   ├── silver/                    # Datos limpios
│   └── gold/                      # Datos listos para consumo
├── notebooks/
│   └── EDA.ipynb                  # Análisis exploratorio
├── tests/                         # Pruebas
├── logs/                          # Registros de ejecución
├── test_connection.py             # Verificación de conexión a la base de datos
├── requirements.txt               # Dependencias
└── README.md
```

## 10. Instalación y ejecución

### Requisitos previos
- Python 3.13 o superior
- Proyecto en Supabase (o cualquier PostgreSQL) con un esquema `gold` creado

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/sebastianparedes93/Proyecto_final_EP.git
cd Proyecto_final_EP

# 2. Crear y activar el entorno virtual
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ubicar el archivo de proyecciones DANE en data/bronze/
#    data/bronze/1.proyecciones_poblacion_dane.xlsx

# 5. Crear el archivo .env en la raíz del proyecto
echo 'SUPABASE_DB_URL=postgresql://usuario:password@host:5432/postgres' > .env

# 6. Verificar la conexión a la base de datos
python test_connection.py

# 7. Ejecutar el pipeline completo
python main.py
```

> Los comandos deben ejecutarse desde la raíz del proyecto, ya que las rutas de `config.yaml` son relativas a ella.

Al finalizar, los archivos de cada capa quedan en `data/silver/` y `data/gold/`, y las cinco tablas se publican en el esquema `gold` de la base de datos.

## 11. Configuración

### `config/config.yaml`

Define los metadatos del proyecto, las rutas de cada capa y las fuentes. Para agregar o modificar una fuente basta con editar este archivo:

```yaml
paths:
  bronze_dir: data/bronze
  silver_dir: data/silver
  gold_dir: data/gold

sources:
  divipola:
    path: data/bronze/4.divipola.xlsx
    filetype: xlsx
    sheetname: Cabeceras - Centros Poblados
```

### `.env`

| Variable | Descripción |
|---|---|
| `SUPABASE_DB_URL` | Cadena de conexión PostgreSQL (`postgresql://usuario:password@host:puerto/base`) |

El archivo `.env` está excluido del control de versiones.

## 12. Análisis exploratorio (EDA)

El notebook `notebooks/EDA.ipynb` documenta el análisis previo a la construcción del pipeline, organizado por tabla:

- **Tabla 1 — Proyecciones DANE:** estructura de columnas por sexo y edad, renombrado y cálculo de grupos de edad.
- **Tabla 2 — Capacidad instalada:** identificación de que la fuente no trae códigos DANE, solo nombres de departamento y municipio.
- **Tabla 4 — DIVIPOLA:** comparación de nombres entre fuentes, detección de municipios y departamentos sin coincidencia y construcción del diccionario de homologación.
- **Integración Tabla 2 + Tabla 4:** cruce para obtener `COD_MUN` y `COD_DPTO`, y validación de las correcciones.
- **Tabla 3 — Prestadores de salud:** revisión de columnas y llaves.
- **Tabla 5 — Tiempo:** revisión de la estructura del calendario.
