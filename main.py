import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np
import traceback


def localizar(df):
    ubicaciones = [
        {'Latitud': -12.10972, 'Longitud': -77.05194, 'Ubicación': 'San Isidro 1'},
        {'Latitud': -12.07274, 'Longitud': -77.08269, 'Ubicación': 'San Miguel 1'},
        {'Latitud': -12.11000, 'Longitud': -77.05000, 'Ubicación': 'Miraflores 1'},
        {'Latitud': -12.07000, 'Longitud': -77.08000, 'Ubicación': 'San Miguel 2'},
        {'Latitud': -12.04028, 'Longitud': -77.04361, 'Ubicación': 'Cercado 1'},
        {'Latitud': -12.11913, 'Longitud': -77.02885, 'Ubicación': 'Miraflores 2'},
    ]

    df['Ubicación'] = np.nan
    df['Ubicación'] = df['Ubicación'].astype(str)
    for ubicacion in ubicaciones:
        df.loc[(df['Latitud'] == ubicacion['Latitud']) & (df['Longitud'] == ubicacion['Longitud']), 'Ubicación'] = ubicacion['Ubicación']
    return df

@st.cache_data
def cargar_datos():
    aire = pd.read_csv("data/aire.csv", delimiter=";", decimal=".")
    aire['Fecha'] = pd.to_datetime(aire['Fecha'], dayfirst=True)
    aire['H2S (ug/m3)'] = pd.to_numeric(aire['H2S (ug/m3)'], errors='coerce')
    aire['SO2 (ug/m3)'] = pd.to_numeric(aire['SO2 (ug/m3)'], errors='coerce')
    aire['Fecha'] = aire['Fecha'].dt.floor('D')
    aire = localizar(aire)
    fijos = ['Fecha', 'Latitud', 'Longitud', 'Ubicación']
    aire = aire.groupby(fijos).agg({col: 'mean' for col in aire.columns if col not in fijos}).reset_index()
    aire.rename(columns={'PM2.5 (ug/m3)': 'PM2,5 (ug/m3)'}, inplace=True)
    return aire

def agregar_grafico(elementos, dataset):
    columna1, columna2 = st.columns(2)
    n = 1
    for elemento in elementos:
        if n % 2 == 0:
            columna = columna2
        else:
            columna = columna1
        with columna:
            st.write("### " + elemento)
            st.line_chart(dataset, x='Fecha', y=elemento, color="Ubicación", use_container_width=True)
        n+=1

def imprimir_error(mensaje):
    st.error(
        """
        **No se pudieron cargar los datos**\n
        Error: %s
        """
        % str(mensaje)
    )

st.set_page_config(
    page_title="Monitoreo de Calidad de Aire QAIRA",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

def cargar_inicio():
    st.header("Monitoreo de Calidad de Aire QAIRA de la Municipalidad de Miraflores", divider="blue")
    columna1, columna2 = st.columns(2)
    with columna2:
        st.markdown(
        """
            El monitoreo de :green[calidad de aire] se :green[realizó] en marco del convenio de colaboración interinstitucional que mantuvo la :green[Municipalidad de Miraflores] con la empresa :green[Grupo qAIRa S.A.C.]
        """
        )

        st.markdown(
        """
            Durante el :green[tiempo de monitoreo] se evaluaron diferentes :green[parámetros de calidad del aire] mediante :green[equipos de monitoreo “low cost”], denominados :green[sensores qHAWAX] que permitieron medir, registrar y/o transmitir datos de diversos parámetros de calidad de aire. Los sensores se :green[situaron] como se indica en el :green[mapa].
        """
        )

        st.markdown(
        """
            El sensor “Low Cost”, de nombre :green[qHAWAX], que en :green[quechua] significa :green[“Guardián de Aire”], realizó :green[mediciones] de :green[gases] (CO, H2S, NO2, O3 y SO2), :green[material particulado] (PM 10 y PM 2.5), :green[variables meteorológicas] (humedad, UV, latitud, longitud, presión, temperatura) y :green[niveles de presión sonora] (ruido).
        """
        )

        st.markdown(
        """
            El :green[convenio] tuvo una :green[duración] de :green[18 meses] iniciándose el mes de :green[marzo del 2020] y culminando en :green[agosto del año 2021].
        """
        )

        st.markdown(
        """
            El :green[objetivo] de los :green[dashboards] generados es el de :green[mostrar] el resultado de las :green[mediciones] realizadas en el periodo de tiempo que duró el convenio. Los :green[parámetros de calidad de aire] se encuentran agrupados en :green[diferentes categorías], las cuales pueden ser :green[seleccionadas] desde el :green[menú lateral izquierdo]. Cada :green[categoría] tiene un gráfico que :green[muestra la evolución de los parámetros] a lo largo del tiempo. Además, se puede observar la ubicación de los sensores en el mapa, así como :green[filtrar] los datos por :green[ubicación del sensor] y :green[fecha].
        """
        )

    with columna1:
        try:
            aire = cargar_datos()
            data = aire[['Latitud', 'Longitud', 'Ubicación']].drop_duplicates()
            st.sidebar.header("Filtros", divider="gray")
            ubicaciones = st.sidebar.multiselect("Ubicaciones", sorted(aire['Ubicación'].unique()), sorted(aire['Ubicación'].unique()))

            if not ubicaciones:
                st.error("Por favor seleccione al menos una localización.")
            else:
                data = aire.loc[aire['Ubicación'].isin(ubicaciones)]
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
                        get_text="Ubicación",
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

                st.write("### Ubicación de Sensores")
                st.pydeck_chart(chart)
        except Exception as e:
            imprimir_error(traceback.print_exc(e))

def cargar_resumen():
    st.header(f'{list(paginas_a_funciones.keys())[1]}', divider="blue")

    try:
        aire = cargar_datos()

        aire.drop(columns=['Latitud', 'Longitud', 'Ubicación'], inplace=True)
        fijas = ['Fecha']
        aire = aire.groupby(fijas).agg({col: 'mean' for col in aire.columns if col not in fijas}).reset_index()
        st.sidebar.header("Filtros", divider="gray")
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
            st.write("### Gases (ug/m3)")
            st.bar_chart(data_gases, x='Fecha', y=gases[1:], use_container_width=True)

            data_material_particulados = data[material_particulados]
            st.write("### Materiales Particulados (ug/m3)")
            st.bar_chart(data_material_particulados, x='Fecha', y=material_particulados[1:], use_container_width=True)

            data_variables_meteorologicas = data[variables_meteorologicas]
            st.write("### Variables Meteorológicas")
            columna1, columna2 = st.columns(2)
            n = 1
            for variable_meteorologica in variables_meteorologicas[1:]:
                if n % 2 == 0:
                    columna = columna2
                else:
                    columna = columna1
                with columna:
                    st.write("#### " + variable_meteorologica)
                    st.bar_chart(data_variables_meteorologicas, x='Fecha', y=variable_meteorologica, use_container_width=True)
                n+=1

            data_niveles_presion_sonora = data[niveles_presion_sonora]
            st.write("### Niveles Presión Sonora (Ruido)")
            st.bar_chart(data_niveles_presion_sonora, x='Fecha', y=niveles_presion_sonora[1:], use_container_width=True)
    except Exception as e:
        imprimir_error(traceback.print_exc(e))

def cargar_gases():
    st.header(f'{list(paginas_a_funciones.keys())[2]}', divider="blue")
    try:
        aire = cargar_datos()
        fijas = ['Fecha', 'Ubicación', 'Latitud', 'Longitud']
        aire = aire.groupby(fijas).agg({col: 'mean' for col in aire.columns if col not in fijas}).reset_index()
        st.sidebar.header("Filtros", divider="gray")
        ubicaciones = st.sidebar.multiselect("Ubicaciones", sorted(aire['Ubicación'].unique()), sorted(aire['Ubicación'].unique()))
        inicio = np.datetime64(st.sidebar.date_input("Fecha de Inicio", value=aire['Fecha'].min()), 'ns')
        fin = np.datetime64(st.sidebar.date_input("Fecha de Fin", value=aire['Fecha'].max()), 'ns')
        gases = ['Fecha', 'Ubicación', 'CO (ug/m3)', 'H2S (ug/m3)', 'NO2 (ug/m3)', 'O3 (ug/m3)']

        if not ubicaciones and not inicio and not fin:
            st.error("Por favor seleccione al menos una localización, una fecha de inicio y una fecha de fin.")
        else:
            data = aire.loc[aire['Ubicación'].isin(ubicaciones) & aire['Fecha'].between(inicio, fin)]

            data_gases = data[gases]
            agregar_grafico(gases[2:], data_gases)
    except Exception as e:
        imprimir_error(traceback.print_exc(e))

def cargar_material_particulados():
    st.header(f'{list(paginas_a_funciones.keys())[3]}', divider="blue")
    try:
        aire = cargar_datos()
        fijas = ['Fecha', 'Ubicación', 'Latitud', 'Longitud']
        aire = aire.groupby(fijas).agg({col: 'mean' for col in aire.columns if col not in fijas}).reset_index()
        st.sidebar.header("Filtros", divider="gray")
        ubicaciones = st.sidebar.multiselect("Ubicaciones", sorted(aire['Ubicación'].unique()), sorted(aire['Ubicación'].unique()))
        inicio = np.datetime64(st.sidebar.date_input("Fecha de Inicio", value=aire['Fecha'].min()), 'ns')
        fin = np.datetime64(st.sidebar.date_input("Fecha de Fin", value=aire['Fecha'].max()), 'ns')
        material_particulados = ['Fecha', 'Ubicación', 'PM10 (ug/m3)', 'PM2,5 (ug/m3)']

        if not ubicaciones and not inicio and not fin:
            st.error("Por favor seleccione al menos una localización, una fecha de inicio y una fecha de fin.")
        else:
            data = aire.loc[aire['Ubicación'].isin(ubicaciones) & aire['Fecha'].between(inicio, fin)]
            
            data_material_particulados = data[material_particulados]
            agregar_grafico(material_particulados[2:], data_material_particulados)
    except Exception as e:
        imprimir_error(traceback.print_exc(e))

def cargar_variables_meteorologicas():
    st.header(f'{list(paginas_a_funciones.keys())[4]}', divider="blue")
    try:
        aire = cargar_datos()
        fijas = ['Fecha', 'Ubicación', 'Latitud', 'Longitud']
        aire = aire.groupby(fijas).agg({col: 'mean' for col in aire.columns if col not in fijas}).reset_index()
        st.sidebar.header("Filtros", divider="gray")
        ubicaciones = st.sidebar.multiselect("Ubicaciones", sorted(aire['Ubicación'].unique()), sorted(aire['Ubicación'].unique()))
        inicio = np.datetime64(st.sidebar.date_input("Fecha de Inicio", value=aire['Fecha'].min()), 'ns')
        fin = np.datetime64(st.sidebar.date_input("Fecha de Fin", value=aire['Fecha'].max()), 'ns')
        variables_meteorologicas = ['Fecha', 'Ubicación', 'Humedad (%)', 'UV', 'Presion (Pa)', 'Temperatura (C)']

        if not ubicaciones and not inicio and not fin:
            st.error("Por favor seleccione al menos una localización, una fecha de inicio y una fecha de fin.")
        else:
            data = aire.loc[aire['Ubicación'].isin(ubicaciones) & aire['Fecha'].between(inicio, fin)]
            
            data_variables_meteorologicas = data[variables_meteorologicas]
            agregar_grafico(variables_meteorologicas[2:], data_variables_meteorologicas)
    except Exception as e:
        imprimir_error(traceback.print_exc(e))

def cargar_niveles_presion_sonora():
    st.header(f'{list(paginas_a_funciones.keys())[5]}', divider="blue")
    try:
        aire = cargar_datos()
        fijas = ['Fecha', 'Ubicación', 'Latitud', 'Longitud']
        aire = aire.groupby(fijas).agg({col: 'mean' for col in aire.columns if col not in fijas}).reset_index()
        st.sidebar.header("Filtros", divider="gray")
        ubicaciones = st.sidebar.multiselect("Ubicaciones", sorted(aire['Ubicación'].unique()), sorted(aire['Ubicación'].unique()))
        inicio = np.datetime64(st.sidebar.date_input("Fecha de Inicio", value=aire['Fecha'].min()), 'ns')
        fin = np.datetime64(st.sidebar.date_input("Fecha de Fin", value=aire['Fecha'].max()), 'ns')
        niveles_presion_sonora = ['Fecha', 'Ubicación', 'Ruido (dB)']

        if not ubicaciones and not inicio and not fin:
            st.error("Por favor seleccione al menos una localización, una fecha de inicio y una fecha de fin.")
        else:
            data = aire.loc[aire['Ubicación'].isin(ubicaciones) & aire['Fecha'].between(inicio, fin)]
            
            data_variables_meteorologicas = data[niveles_presion_sonora]

            st.write("### " + niveles_presion_sonora[2:][0])
            st.line_chart(data_variables_meteorologicas, x='Fecha', y=niveles_presion_sonora[2:][0], color="Ubicación", use_container_width=True)
    except Exception as e:
        imprimir_error(traceback.print_exc(e))

paginas_a_funciones = {
    "Inicio": cargar_inicio,
    "Resumen": cargar_resumen,
    "Gases": cargar_gases,
    "Material Particulado": cargar_material_particulados,
    "Variables Meteorológicas": cargar_variables_meteorologicas,
    "Niveles de Presión Sonora": cargar_niveles_presion_sonora,
}

st.sidebar.header("Calidad de Aire QAIRA", divider="blue")
st.sidebar.header("Navegación", divider="gray")
pagina = st.sidebar.selectbox("Elegir Página", paginas_a_funciones.keys())
paginas_a_funciones[pagina]()

footer_html = """
<div style='position:fixed; left:0; bottom:0; width:100%; background-color:#000; color:white; text-align:center;'>
Desarrollado por el Grupo 3: Julio Enrique Barrios Aedo, Luis Alberto Castañeda Salazar, Giancarlo Lamadrid Cotrina y Carlos Hugo Martín Carranza Olivera.
</div>"""
st.sidebar.markdown(footer_html, unsafe_allow_html=True)