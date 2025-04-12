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
    aire.set_index('Fecha', inplace=True)
    return aire

def inicio():
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
        aire['Año'] = aire.index.year
        aire['Mes'] = aire.index.month
        aire.drop(columns=['Latitud'], inplace=True)
        aire.drop(columns=['Longitud'], inplace=True)
        aire = aire.groupby(['Año', 'Mes', 'Localización']).agg({col: 'mean' for col in aire.columns if col not in ['Año', 'Mes', 'Localización']}).reset_index()
        aire['Año-Mes'] = aire['Año'].astype(str) + '-' + aire['Mes'].astype(str).str.zfill(2)
        localizaciones = st.sidebar.multiselect("Localizaciones", sorted(aire['Localización'].unique()), sorted(aire['Localización'].unique()))
        anios = st.sidebar.multiselect("Años", sorted(aire['Año'].unique()), sorted(aire['Año'].unique()))
        meses = st.sidebar.multiselect("Meses", sorted(aire['Mes'].unique()), sorted(aire['Mes'].unique()))
        gases = ['Año', 'Mes', 'Localización', 'Año-Mes', 'CO (ug/m3)', 'H2S (ug/m3)', 'NO2 (ug/m3)', 'O3 (ug/m3)']
        material_particulados = ['Año', 'Mes', 'Localización', 'Año-Mes', 'PM10 (ug/m3)', 'PM2.5 (ug/m3)']
        variables_meteorologicas = ['Año', 'Mes', 'Localización', 'Año-Mes', 'Humedad (%)', 'UV', 'Presion (Pa)', 'Temperatura (C)']
        niveles_presion_sonora = ['Año', 'Mes', 'Localización', 'Año-Mes', 'Ruido (dB)']

        if not localizaciones and not anios and not meses:
            st.error("Por favor seleccione al menos una localización, un año y un mes.")
        else:
            data = aire.loc[aire['Localización'].isin(localizaciones) & aire['Año'].isin(anios) & aire['Mes'].isin(meses)]
            print(data.head(5))

            data_gases = data[gases]
            st.write("### Mediciones de gases (ug/m3)")
            st.bar_chart(data_gases, x='Año-Mes', y=gases[4:], use_container_width=True)

            data_material_particulados = data[material_particulados]
            st.write("### Materiales Particulados (ug/m3)")
            st.bar_chart(data_material_particulados, x='Año-Mes', y=material_particulados[4:], use_container_width=True)

            data_variables_meteorologicas = data[variables_meteorologicas]
            st.write("### Variables Meteorológicas")
            st.write("#### Humedad (%)")
            st.bar_chart(data_variables_meteorologicas, x='Año-Mes', y="Humedad (%)", use_container_width=True)
            st.write("#### UV")
            st.bar_chart(data_variables_meteorologicas, x='Año-Mes', y="UV", use_container_width=True)
            st.write("#### Presion (Pa)")
            st.bar_chart(data_variables_meteorologicas, x='Año-Mes', y="Presion (Pa)", use_container_width=True)
            st.write("#### Temperatura (C)")
            st.bar_chart(data_variables_meteorologicas, x='Año-Mes', y="Temperatura (C)", use_container_width=True)

            data_niveles_presion_sonora = data[niveles_presion_sonora]
            st.write("### Niveles Presión Sonora (Ruido)")
            st.bar_chart(data_niveles_presion_sonora, x='Año-Mes', y=niveles_presion_sonora[4:], use_container_width=True)
    except Exception as e:
        st.error(
            """
            **No se pudieron cargar los datos**
            Error: %s
            """
            % str(e)
        )

def inicio2():
    try:
        aire = cargar_datos()
        aire = aire.groupby(['Latitud', 'Longitud', 'Localización']).agg({col: 'mean' for col in aire.columns if col not in ['Latitud', 'Longitud', 'Localización']}).reset_index()
        localizaciones = sorted(aire['Localización'].unique())
        print(aire.head(5))
        capas = dict()
        for localizacion in localizaciones:
            capas[localizacion] = pdk.Layer("HexagonLayer", 
                                            data=aire[aire['Localización'] == localizacion], 
                                            get_position=["Longitud", "Latitud"],
                                            radius=200,
                                            elevation_scale=4,
                                            elevation_range=[0, 1000],
                                            extruded=True,
                                            pickable=True,
                                            auto_highlight=True,)

        st.sidebar.markdown("### Sensores")
        capas_seleccionadas = [
            capa
            for nombre_capa, capa in capas.items()
            if st.sidebar.checkbox(nombre_capa, True)
        ]
        if capas_seleccionadas:
            st.pydeck_chart(
                pdk.Deck(
                    map_style="mapbox://styles/mapbox/light-v9",
                    initial_view_state={
                        "latitude": -12.0950,
                        "longitude": -77.0500,
                        "zoom": 12.7,
                        "pitch": 50,
                    },
                    layers=capas_seleccionadas,
                )
            )
        else:
            st.error("Por favor seleccione uno de los sensores")
    except Exception as e:
        st.error(
            """
            **No se pudieron cargar los datos**
            Error: %s
            """
            % e.reason
        )

def mapping_demo():
    st.markdown(f"# {list(page_names_to_funcs.keys())[2]}")
    st.write(
        """
        This demo shows how to use
[`st.pydeck_chart`](https://docs.streamlit.io/develop/api-reference/charts/st.pydeck_chart)
to display geospatial data.
"""
    )

    @st.cache_data
    def from_data_file(filename):
        url = (
            "http://raw.githubusercontent.com/streamlit/"
            "example-data/master/hello/v1/%s" % filename
        )
        return pd.read_json(url)

    try:
        ALL_LAYERS = {
            "Bike Rentals": pdk.Layer(
                "HexagonLayer",
                data=from_data_file("bike_rental_stats.json"),
                get_position=["lon", "lat"],
                radius=200,
                elevation_scale=4,
                elevation_range=[0, 1000],
                extruded=True,
            ),
            "Bart Stop Exits": pdk.Layer(
                "ScatterplotLayer",
                data=from_data_file("bart_stop_stats.json"),
                get_position=["lon", "lat"],
                get_color=[200, 30, 0, 160],
                get_radius="[exits]",
                radius_scale=0.05,
            ),
            "Bart Stop Names": pdk.Layer(
                "TextLayer",
                data=from_data_file("bart_stop_stats.json"),
                get_position=["lon", "lat"],
                get_text="name",
                get_color=[0, 0, 0, 200],
                get_size=15,
                get_alignment_baseline="'bottom'",
            )
        }
        st.sidebar.markdown("### Map Layers")
        selected_layers = [
            layer
            for layer_name, layer in ALL_LAYERS.items()
            if st.sidebar.checkbox(layer_name, True)
        ]
        if selected_layers:
            st.pydeck_chart(
                pdk.Deck(
                    map_style="mapbox://styles/mapbox/light-v9",
                    initial_view_state={
                        "latitude": 37.76,
                        "longitude": -122.4,
                        "zoom": 11,
                        "pitch": 50,
                    },
                    layers=selected_layers,
                )
            )
        else:
            st.error("Please choose at least one layer above.")
    except URLError as e:
        st.error(
            """
            **This demo requires internet access.**

            Connection error: %s
        """
            % e.reason
        )

def plotting_demo():
    st.markdown(f'# {list(page_names_to_funcs.keys())[1]}')
    st.write(
        """
        This demo illustrates a combination of plotting and animation with
Streamlit. We're generating a bunch of random numbers in a loop for around
5 seconds. Enjoy!
"""
    )

    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    last_rows = np.random.randn(1, 1)
    chart = st.line_chart(last_rows)

    for i in range(1, 101):
        new_rows = last_rows[-1, :] + np.random.randn(5, 1).cumsum(axis=0)
        status_text.text("%i%% Complete" % i)
        chart.add_rows(new_rows)
        progress_bar.progress(i)
        last_rows = new_rows
        time.sleep(0.05)

    progress_bar.empty()

    # Streamlit widgets automatically run the script from top to bottom. Since
    # this button is not connected to any other logic, it just causes a plain
    # rerun.
    st.button("Re-run")


def data_frame_demo():
    st.markdown(f"# {list(page_names_to_funcs.keys())[3]}")
    st.write(
        """
        This demo shows how to use `st.write` to visualize Pandas DataFrames.

(Data courtesy of the [UN Data Explorer](http://data.un.org/Explorer.aspx).)
"""
    )

    @st.cache_data
    def get_UN_data():
        AWS_BUCKET_URL = "http://streamlit-demo-data.s3-us-west-2.amazonaws.com"
        df = pd.read_csv(AWS_BUCKET_URL + "/agri.csv.gz")
        return df.set_index("Region")

    try:
        df = get_UN_data()
        countries = st.multiselect(
            "Choose countries", list(df.index), ["China", "United States of America"]
        )
        if not countries:
            st.error("Please select at least one country.")
        else:
            data = df.loc[countries]
            data /= 1000000.0
            st.write("### Gross Agricultural Production ($B)", data.sort_index())

            data = data.T.reset_index()
            data = pd.melt(data, id_vars=["index"]).rename(
                columns={"index": "year", "value": "Gross Agricultural Product ($B)"}
            )
            chart = (
                alt.Chart(data)
                .mark_area(opacity=0.3)
                .encode(
                    x="year:T",
                    y=alt.Y("Gross Agricultural Product ($B):Q", stack=None),
                    color="Region:N",
                )
            )
            st.altair_chart(chart, use_container_width=True)
    except URLError as e:
        st.error(
            """
            **This demo requires internet access.**

            Connection error: %s
        """
            % e.reason
        )

page_names_to_funcs = {
    "Inicio": inicio,
    "Mediciones de Gases": plotting_demo,
    "Material Particulado": mapping_demo,
    "Variables Meteorológicas": data_frame_demo,
    "Niveles de Presión Sonora": data_frame_demo
}

demo_name = st.sidebar.selectbox("Elegir Página", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()