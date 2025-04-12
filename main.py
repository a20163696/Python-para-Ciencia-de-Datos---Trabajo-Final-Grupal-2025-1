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
        {'Latitud': -12.04028, 'Longitud': -77.04361, 'Localización': 'Cercado 1'},
        {'Latitud': -12.11913, 'Longitud': -77.02885, 'Localización': 'Miraflores 2'},
    ]

    df['Localización'] = np.nan
    df['Localización'] = df['Localización'].astype(str)
    for localizacion in localizaciones:
        df.loc[(df['Latitud'] == localizacion['Latitud']) & (df['Longitud'] == localizacion['Longitud']), 'Localización'] = localizacion['Localización']
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
    aire.rename(columns={'PM2.5 (ug/m3)': 'PM2,5 (ug/m3)'}, inplace=True)
    return aire

def agregar_grafico(elementos, dataset):
    for elemento in elementos:
        st.write("## " + elemento)
        st.line_chart(dataset, x='Fecha', y=elemento, color="Localización", use_container_width=True)


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
        data = aire[['Latitud', 'Longitud', 'Localización']].drop_duplicates()
        localizaciones = st.sidebar.multiselect("Localizaciones", sorted(aire['Localización'].unique()), sorted(aire['Localización'].unique()))

        if not localizaciones:
            st.error("Por favor seleccione al menos una localización.")
        else:
            data = aire.loc[aire['Localización'].isin(localizaciones)]
            point_layer = pdk.Layer(
                "ScatterplotLayer",
                data=data,
                get_position=["Longitud", "Latitud"],
                auto_highlight=True,
                get_radius=50,
                get_fill_color=[0, 128, 0, 140],
                pickable=True,
            )

            text_layer = pdk.Layer(
                    "TextLayer",
                    data=data,
                    get_position=["Longitud", "Latitud"],
                    get_text="Localización",
                    get_color=[0, 0, 0, 10],
                    get_size=15,
                    get_alignment_baseline="'bottom'",
                )

            view_state = pdk.ViewState(
                latitude=-12.0850, longitude=-77.05000, controller=True, zoom=12, pitch=30
            )

            chart = pdk.Deck(
                map_style="mapbox://styles/mapbox/light-v9",
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
        fijas = ['Fecha']
        aire = aire.groupby(fijas).agg({col: 'mean' for col in aire.columns if col not in fijas}).reset_index()
        inicio = np.datetime64(st.sidebar.date_input("Fecha de Inicio", value=aire['Fecha'].min()), 'ns')
        fin = np.datetime64(st.sidebar.date_input("Fecha de Fin", value=aire['Fecha'].max()), 'ns')
        gases = ['Fecha', 'CO (ug/m3)', 'H2S (ug/m3)', 'NO2 (ug/m3)', 'O3 (ug/m3)']
        material_particulados = ['Fecha', 'PM10 (ug/m3)', 'PM2,5 (ug/m3)']
        variables_meteorologicas = ['Fecha', 'Humedad (%)', 'UV', 'Presion (Pa)', 'Temperatura (C)']
        niveles_presion_sonora = ['Fecha', 'Ruido (dB)']

        if not inicio and not fin:
            st.error("Por favor seleccione al menos una fecha de inicio y una fecha de fin.")
        else:
            data = aire.loc[aire['Fecha'].between(inicio, fin)]

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
        fijas = ['Fecha', 'Localización', 'Latitud', 'Longitud']
        aire = aire.groupby(fijas).agg({col: 'mean' for col in aire.columns if col not in fijas}).reset_index()
        localizaciones = st.sidebar.multiselect("Localizaciones", sorted(aire['Localización'].unique()), sorted(aire['Localización'].unique()))
        inicio = np.datetime64(st.sidebar.date_input("Fecha de Inicio", value=aire['Fecha'].min()), 'ns')
        fin = np.datetime64(st.sidebar.date_input("Fecha de Fin", value=aire['Fecha'].max()), 'ns')
        gases = ['Fecha', 'Localización', 'CO (ug/m3)', 'H2S (ug/m3)', 'NO2 (ug/m3)', 'O3 (ug/m3)']

        if not localizaciones and not inicio and not fin:
            st.error("Por favor seleccione al menos una localización, una fecha de inicio y una fecha de fin.")
        else:
            data = aire.loc[aire['Localización'].isin(localizaciones) & aire['Fecha'].between(inicio, fin)]

            data_gases = data[gases]
            agregar_grafico(gases[2:], data_gases)
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
        fijas = ['Fecha', 'Localización', 'Latitud', 'Longitud']
        aire = aire.groupby(fijas).agg({col: 'mean' for col in aire.columns if col not in fijas}).reset_index()
        localizaciones = st.sidebar.multiselect("Localizaciones", sorted(aire['Localización'].unique()), sorted(aire['Localización'].unique()))
        inicio = np.datetime64(st.sidebar.date_input("Fecha de Inicio", value=aire['Fecha'].min()), 'ns')
        fin = np.datetime64(st.sidebar.date_input("Fecha de Fin", value=aire['Fecha'].max()), 'ns')
        material_particulados = ['Fecha', 'Localización', 'PM10 (ug/m3)', 'PM2,5 (ug/m3)']

        if not localizaciones and not inicio and not fin:
            st.error("Por favor seleccione al menos una localización, una fecha de inicio y una fecha de fin.")
        else:
            data = aire.loc[aire['Localización'].isin(localizaciones) & aire['Fecha'].between(inicio, fin)]
            
            data_material_particulados = data[material_particulados]
            agregar_grafico(material_particulados[2:], data_material_particulados)
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
        fijas = ['Fecha', 'Localización', 'Latitud', 'Longitud']
        aire = aire.groupby(fijas).agg({col: 'mean' for col in aire.columns if col not in fijas}).reset_index()
        localizaciones = st.sidebar.multiselect("Localizaciones", sorted(aire['Localización'].unique()), sorted(aire['Localización'].unique()))
        inicio = np.datetime64(st.sidebar.date_input("Fecha de Inicio", value=aire['Fecha'].min()), 'ns')
        fin = np.datetime64(st.sidebar.date_input("Fecha de Fin", value=aire['Fecha'].max()), 'ns')
        variables_meteorologicas = ['Fecha', 'Localización', 'Humedad (%)', 'UV', 'Presion (Pa)', 'Temperatura (C)']

        if not localizaciones and not inicio and not fin:
            st.error("Por favor seleccione al menos una localización, una fecha de inicio y una fecha de fin.")
        else:
            data = aire.loc[aire['Localización'].isin(localizaciones) & aire['Fecha'].between(inicio, fin)]
            
            data_variables_meteorologicas = data[variables_meteorologicas]
            agregar_grafico(variables_meteorologicas[2:], data_variables_meteorologicas)
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
        fijas = ['Fecha', 'Localización', 'Latitud', 'Longitud']
        aire = aire.groupby(fijas).agg({col: 'mean' for col in aire.columns if col not in fijas}).reset_index()
        localizaciones = st.sidebar.multiselect("Localizaciones", sorted(aire['Localización'].unique()), sorted(aire['Localización'].unique()))
        inicio = np.datetime64(st.sidebar.date_input("Fecha de Inicio", value=aire['Fecha'].min()), 'ns')
        fin = np.datetime64(st.sidebar.date_input("Fecha de Fin", value=aire['Fecha'].max()), 'ns')
        niveles_presion_sonora = ['Fecha', 'Localización', 'Ruido (dB)']
        print(aire.dtypes)
        print(type(inicio))

        if not localizaciones and not inicio and not fin:
            st.error("Por favor seleccione al menos una localización, una fecha de inicio y una fecha de fin.")
        else:
            data = aire.loc[aire['Localización'].isin(localizaciones) & aire['Fecha'].between(inicio, fin)]
            
            data_variables_meteorologicas = data[niveles_presion_sonora]
            agregar_grafico(niveles_presion_sonora[2:], data_variables_meteorologicas)
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