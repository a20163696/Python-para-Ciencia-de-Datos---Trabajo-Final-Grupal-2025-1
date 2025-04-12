import streamlit as st
import pandas as pd
import pydeck as pdk
import time
import numpy as np
import altair as alt

from urllib.error import URLError

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

@st.cache_data
def cargar_datos():
    aire = pd.read_csv("data/aire.csv", delimiter=";", decimal=".")
    aire['Fecha'] = pd.to_datetime(aire['Fecha'], dayfirst=True)
    aire['H2S (ug/m3)'] = pd.to_numeric(aire['H2S (ug/m3)'], errors='coerce')
    aire['SO2 (ug/m3)'] = pd.to_numeric(aire['SO2 (ug/m3)'], errors='coerce')
    aire['Fecha'] = aire['Fecha'].dt.floor('D')
    aire = localizar(aire)
    aire = aire.groupby(['Fecha', 'Latitud', 'Longitud', 'Localización']).agg({col: 'mean' for col in aire.columns if col not in ['Fecha', 'Latitud', 'Longitud', 'Localización']}).reset_index()
    aire['Año'] = aire.Fecha.dt.year
    aire['Mes'] = aire.Fecha.dt.month
    #aire['Año-Mes'] = aire['Año'].astype(str) + '-' + aire['Mes'].astype(str).str.zfill(2)
    aire.rename(columns={'PM2.5 (ug/m3)': 'PM2,5 (ug/m3)'}, inplace=True)
    return aire

def cargar_inicio():
    st.write("# Monitoreo de Calidad de Aire QAIRA de la Municipalidad de Miraflores")

    st.markdown(
    """
        El monitoreo de calidad de aire se realizó en marco del convenio de colaboración interinstitucional que mantuvo la Municipalidad de Miraflores con la empresa Grupo qAIRa S.A.C
    """
    )

    st.markdown(
    """
        Durante el tiempo de monitoreo se evaluaron diferentes parámetros de calidad del aire mediante equipos de monitoreo “low cost”, denominados sensores qHAWAX que permitieron medir, registrar y/o transmitir datos de diversos parámetros de calidad de aire. Se situaron dos estaciones de monitoreo en el casco urbano del distrito de Miraflores, una primera estación en el Complejo Deportivo Manuel Bonilla y la segunda en el Ovalo de Miraflores.
    """
    )

    st.markdown(
    """
        El sensor “Low Cost”, de nombre qHAWAX, que en quechua significa “Guardián de Aire”, realizó mediciones de gases (CO, H2S, NO2, O3 y SO2), material particulado (PM 10 y PM 2.5), variables meteorológicas (humedad, UV, latitud, longitud, presión, temperatura) y niveles de presión sonora (ruido) durante el convenio interinstitucional, teniendo una duración de 18 meses iniciándose el mes de marzo del 2020 y culminando en agosto del año 2021.
    """
    )

    try:
        aire = cargar_datos()
        data = aire[['Latitud', 'Longitud', 'Localización']]
        data.drop_duplicates(inplace=True)
        data.reset_index(drop=True, inplace=True)
        point_layer = pdk.Layer(
            "HexagonLayer",
            data=data,
            id="Localizaciones",
            get_position=["Longitud", "Latitud"],
            radius=100,
            extruded=True,
            pickable=True,
            auto_highlight=True,
            coverage=1,
            tooltip=True
        )

        text_layer = pdk.Layer(
                "TextLayer",
                data=data,
                get_position=["Longitud", "Latitud"],
                get_text="Localización",
                get_color=[255, 255, 255, 500],
                get_size=15,
                get_alignment_baseline="'bottom'",
            )

        view_state = pdk.ViewState(
            latitude=-12.0850, longitude=-77.05000, controller=True, zoom=12, pitch=30
        )

        chart = pdk.Deck(
            layers=[point_layer, text_layer],
            initial_view_state=view_state,
        )

        st.write("## Ubicación de Sensores")
        st.pydeck_chart(chart)
    except Exception as e:
        st.error(
            """
            **No se pudieron cargar los datos**
            Error: %s
            """
            % str(e)
        )

def cargar_introduccion():
    st.markdown(f'# {list(page_names_to_funcs.keys())[1]}')

    try:
        aire = cargar_datos()

        aire.drop(columns=['Latitud', 'Longitud', 'Localización'], inplace=True)
        #aire.drop(columns=['Longitud'], inplace=True)
        #aire.drop(columns=['Localización'], inplace=True)
        fijas = ['Fecha', 'Año', 'Mes']
        aire = aire.groupby(fijas).agg({col: 'mean' for col in aire.columns if col not in fijas}).reset_index()
        anios = st.sidebar.multiselect("Años", sorted(aire['Año'].unique()), sorted(aire['Año'].unique()))
        meses = st.sidebar.multiselect("Meses", sorted(aire['Mes'].unique()), sorted(aire['Mes'].unique()))
        gases = ['Fecha', 'CO (ug/m3)', 'H2S (ug/m3)', 'NO2 (ug/m3)', 'O3 (ug/m3)']
        material_particulados = ['Fecha', 'PM10 (ug/m3)', 'PM2,5 (ug/m3)']
        variables_meteorologicas = ['Fecha', 'Humedad (%)', 'UV', 'Presion (Pa)', 'Temperatura (C)']
        niveles_presion_sonora = ['Fecha', 'Ruido (dB)']

        if not anios and not meses:
            st.error("Por favor seleccione al menos un año y un mes.")
        else:
            data = aire.loc[aire['Año'].isin(anios) & aire['Mes'].isin(meses)]

            data_gases = data[gases]
            st.write("## Mediciones de gases (ug/m3)")
            st.bar_chart(data_gases, x='Fecha', y=gases[1:], use_container_width=True)

            data_material_particulados = data[material_particulados]
            st.write("## Materiales Particulados (ug/m3)")
            st.bar_chart(data_material_particulados, x='Fecha', y=material_particulados[1:], use_container_width=True)

            data_variables_meteorologicas = data[variables_meteorologicas]
            st.write("## Variables Meteorológicas")
            for variable_meteorologica in variables_meteorologicas[1:]:
                st.write("### " + variable_meteorologica)
                st.bar_chart(data_variables_meteorologicas, x='Fecha', y=variable_meteorologica, use_container_width=True)

            data_niveles_presion_sonora = data[niveles_presion_sonora]
            st.write("## Niveles Presión Sonora (Ruido)")
            st.bar_chart(data_niveles_presion_sonora, x='Fecha', y=niveles_presion_sonora[1:], use_container_width=True)
    except Exception as e:
        st.error(
            """
            **No se pudieron cargar los datos**
            Error: %s
            """
            % str(e)
        )

def cargar_gases():
    st.markdown(f'# {list(page_names_to_funcs.keys())[2]}')
    try:
        aire = cargar_datos()
        fijas = ['Fecha', 'Año', 'Mes', 'Localización', 'Latitud', 'Longitud']
        aire = aire.groupby(fijas).agg({col: 'mean' for col in aire.columns if col not in fijas}).reset_index()
        localizaciones = st.sidebar.multiselect("Localizaciones", sorted(aire['Localización'].unique()), sorted(aire['Localización'].unique()))
        anios = st.sidebar.multiselect("Años", sorted(aire['Año'].unique()), sorted(aire['Año'].unique()))
        meses = st.sidebar.multiselect("Meses", sorted(aire['Mes'].unique()), sorted(aire['Mes'].unique()))
        gases = ['Fecha', 'Localización', 'CO (ug/m3)', 'H2S (ug/m3)', 'NO2 (ug/m3)', 'O3 (ug/m3)']

        if not localizaciones and not anios and not meses:
            st.error("Por favor seleccione al menos una localización, un año y un mes.")
        else:
            data = aire.loc[aire['Localización'].isin(localizaciones) & aire['Año'].isin(anios) & aire['Mes'].isin(meses)]

            data_gases = data[gases]
            for gas in gases[2:]:
                st.write("## " + gas)
                st.line_chart(data_gases, x='Fecha', y=gas, color="Localización", use_container_width=True)

    except Exception as e:
        st.error(
            """
            **No se pudieron cargar los datos**
            Error: %s
            """
            % str(e)
        )

def cargar_material_particulados():
    st.markdown(f'# {list(page_names_to_funcs.keys())[3]}')
    try:
        aire = cargar_datos()
        fijas = ['Fecha', 'Año', 'Mes', 'Localización', 'Latitud', 'Longitud']
        aire = aire.groupby(fijas).agg({col: 'mean' for col in aire.columns if col not in fijas}).reset_index()
        localizaciones = st.sidebar.multiselect("Localizaciones", sorted(aire['Localización'].unique()), sorted(aire['Localización'].unique()))
        anios = st.sidebar.multiselect("Años", sorted(aire['Año'].unique()), sorted(aire['Año'].unique()))
        meses = st.sidebar.multiselect("Meses", sorted(aire['Mes'].unique()), sorted(aire['Mes'].unique()))
        material_particulados = ['Fecha', 'Localización', 'PM10 (ug/m3)', 'PM2,5 (ug/m3)']

        if not localizaciones and not anios and not meses:
            st.error("Por favor seleccione al menos una localización, un año y un mes.")
        else:
            data = aire.loc[aire['Localización'].isin(localizaciones) & aire['Año'].isin(anios) & aire['Mes'].isin(meses)]
            
            data_material_particulados = data[material_particulados]
            for material_particulado in material_particulados[2:]:
                st.write("## " + material_particulado)
                st.line_chart(data_material_particulados, x='Fecha', y=material_particulado, color="Localización", use_container_width=True)
    except Exception as e:
        st.error(
            """
            **No se pudieron cargar los datos**
            Error: %s
            """
            % str(e)
        )

def cargar_variables_meteorologicas():
    st.markdown(f'# {list(page_names_to_funcs.keys())[4]}')
    try:
        aire = cargar_datos()
        fijas = ['Fecha', 'Año', 'Mes', 'Localización', 'Latitud', 'Longitud']
        aire = aire.groupby(fijas).agg({col: 'mean' for col in aire.columns if col not in fijas}).reset_index()
        localizaciones = st.sidebar.multiselect("Localizaciones", sorted(aire['Localización'].unique()), sorted(aire['Localización'].unique()))
        anios = st.sidebar.multiselect("Años", sorted(aire['Año'].unique()), sorted(aire['Año'].unique()))
        meses = st.sidebar.multiselect("Meses", sorted(aire['Mes'].unique()), sorted(aire['Mes'].unique()))
        variables_meteorologicas = ['Fecha', 'Localización', 'Humedad (%)', 'UV', 'Presion (Pa)', 'Temperatura (C)']

        if not localizaciones and not anios and not meses:
            st.error("Por favor seleccione al menos una localización, un año y un mes.")
        else:
            data = aire.loc[aire['Localización'].isin(localizaciones) & aire['Año'].isin(anios) & aire['Mes'].isin(meses)]
            
            data_variables_meteorologicas = data[variables_meteorologicas]
            for variable_meteorologica in variables_meteorologicas[2:]:
                st.write("## " + variable_meteorologica)
                st.line_chart(data_variables_meteorologicas, x='Fecha', y=variable_meteorologica, color="Localización", use_container_width=True)
    except Exception as e:
        st.error(
            """
            **No se pudieron cargar los datos**
            Error: %s
            """
            % str(e)
        )

def cargar_niveles_presion_sonora():
    st.markdown(f'# {list(page_names_to_funcs.keys())[5]}')
    try:
        aire = cargar_datos()
        fijas = ['Fecha', 'Año', 'Mes', 'Localización', 'Latitud', 'Longitud']
        aire = aire.groupby(fijas).agg({col: 'mean' for col in aire.columns if col not in fijas}).reset_index()
        localizaciones = st.sidebar.multiselect("Localizaciones", sorted(aire['Localización'].unique()), sorted(aire['Localización'].unique()))
        anios = st.sidebar.multiselect("Años", sorted(aire['Año'].unique()), sorted(aire['Año'].unique()))
        meses = st.sidebar.multiselect("Meses", sorted(aire['Mes'].unique()), sorted(aire['Mes'].unique()))
        niveles_presion_sonora = ['Fecha', 'Localización', 'Ruido (dB)']

        if not localizaciones and not anios and not meses:
            st.error("Por favor seleccione al menos una localización, un año y un mes.")
        else:
            data = aire.loc[aire['Localización'].isin(localizaciones) & aire['Año'].isin(anios) & aire['Mes'].isin(meses)]
            
            data_variables_meteorologicas = data[niveles_presion_sonora]
            for variable_meteorologica in niveles_presion_sonora[2:]:
                st.write("## " + variable_meteorologica)
                st.line_chart(data_variables_meteorologicas, x='Fecha', y=variable_meteorologica, color="Localización", use_container_width=True)
    except Exception as e:
        st.error(
            """
            **No se pudieron cargar los datos**
            Error: %s
            """
            % str(e)
        )

page_names_to_funcs = {
    "Inicio": cargar_inicio,
    "Introducción": cargar_introduccion,
    "Mediciones de Gases": cargar_gases,
    "Material Particulado": cargar_material_particulados,
    "Variables Meteorológicas": cargar_variables_meteorologicas,
    "Niveles de Presión Sonora": cargar_niveles_presion_sonora,
}

demo_name = st.sidebar.selectbox("Elegir Página", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()