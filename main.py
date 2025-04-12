import streamlit as st
import pandas as pd
import numpy as np
import datetime

def agregar_caracteristicas(df):
    df['Dia'] = df.index.day
    df['Mes'] = df.index.month
    df['Año'] = df.index.year
    return df

def localizar(df):
    localizaciones = [
        {'Latitud': -12.10972, 'Longitud': -77.05194, 'Localización': 'San Isidro 1'},
        {'Latitud': -12.07274, 'Longitud': -77.08269, 'Localización': 'San Miguel 1'},
        {'Latitud': -12.11000, 'Longitud': -77.05000, 'Localización': 'Miraflores 1'},
        {'Latitud': -12.07000, 'Longitud': -77.08000, 'Localización': 'San Miguel 2'},
        {'Latitud': -12.04028, 'Longitud': -77.04361, 'Localización': 'Cercaso 1'},
        {'Latitud': -12.11913, 'Longitud': -77.02885, 'Localización': 'Miraflores 2'},
    ]

    df['Localización'] = np.nan
    for loc in localizaciones:
        lat = loc['Latitud']
        lon = loc['Longitud']
        loc_name = loc['Localización']
        df.loc[(df['Latitud'] == lat) & (df['Longitud'] == lon), 'Localización'] = loc_name
    return df

def cargar_datos():
    aire = pd.read_csv("data/aire.csv", delimiter=";", decimal=".")
    aire['Fecha'] = pd.to_datetime(aire['Fecha'], dayfirst=True)
    aire['H2S (ug/m3)'] = pd.to_numeric(aire['H2S (ug/m3)'], errors='coerce')
    aire['SO2 (ug/m3)'] = pd.to_numeric(aire['SO2 (ug/m3)'], errors='coerce')
    aire['Fecha'] = aire['Fecha'].dt.floor('D')
    aire = localizar(aire)
    aire = aire.groupby(['Fecha', 'Latitud', 'Longitud', 'Localización']).agg({col: 'mean' for col in aire.columns if col not in ['Fecha', 'Latitud', 'Longitud', 'Localización']}).reset_index()
    aire.set_index('Fecha', inplace=True)
    return aire

aire = cargar_datos()
aire = aire.groupby(['Latitud', 'Longitud', 'Localización']).agg({col: 'mean' for col in aire.columns if col not in ['Latitud', 'Longitud', 'Localización']}).reset_index()
localizaciones = aire['Localización'].unique()

capas = dict()
for localizacion in localizaciones:
    capas[localizacion] = ["HexagonLayer", aire[aire['Localización'] == localizacion], ["Longitud", "Latitud"]]

print(aire.head(5))