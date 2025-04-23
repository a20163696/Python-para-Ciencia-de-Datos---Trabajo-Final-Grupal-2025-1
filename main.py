import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np
import traceback
import plotly.graph_objects as go # Importar go
from plotly_calplot import calplot # <-- Importar calplot
import calendar # <-- Para nombres de meses
import plotly.express as px

descripciones = { 
    "Ruido (dB)": "El ruido 2 se mide en decibelios (dB), los niveles de ruido que no son perjudiciales para la audición son generalmente inferiores a los 85 dB, aunque esto depende del tiempo de exposición y si se utilizan o no protecciones auditivas.",
    "PM10 (ug/m3)": "Partículas atmosférica con un diámetro igual o inferior a 10 micrómetros (μm). Estas partículas pueden ser tanto sólidas como líquidas y están formadas principalmente por compuestos inorgánicos, metales pesados y material orgánico asociado a partículas de carbono (hollín). La concentración de PM10 se mide en microgramos por metro cúbico (μg/m³). Según la normativa europea se debe garantizar que no se superen más de 35 días al año el valor límite diario de 50 μg/m³.",
    "PM2,5 (ug/m3)": "Partículas atmosféricas con un diámetro menor a 2,5 micrómetros (μm) que pueden tener efectos negativos sobre la salud humana. Según la Organización Mundial de la Salud (OMS), los valores guía de protección para la salud establecen que 10 μg/m3 es el nivel más bajo a partir del cual se ha detectado una asociación entre efectos cardiopulmonares y mortalidad por cáncer de pulmón debido a la exposición prolongada a PM2,5.",
    "CO (ug/m3)": "Monóxido de carbono es un gas incoloro, sin olor y venenoso que se produce por la combustión incompleta de combustibles como el carbón, la madera, el aceite, el queroseno, el propano y el gas natural.",
    "H2S (ug/m3)": "Sulfuro de hidrógeno es un gas incoloro con un olor característico a huevo podrido. Este gas es inflamable en concentraciones entre 4 y 46 porciento en el aire y es tóxico en altas concentraciones.",
    "NO2 (ug/m3)": "Dióxido de nitrógeno es un gas tóxico que se forma principalmente por la combustión a altas temperaturas, especialmente en motores diésel y en instalaciones industriales de alta temperatura.",
    "O3 (ug/m3)": "Ozono se forma cuando las moléculas de oxígeno son excitadas lo suficiente para descomponerse en oxígeno atómico y las colisiones entre los diferentes átomos generan la formación del ozono.",
    "SO2 (ug/m3)": "Dióxido de azufre es un gas incoloro y extremadamente tóxico que se forma al quemar y fundir combustibles fósiles y minerales que contienen azufre, como el carbón, el petróleo, el diésel o el gas natural.",
    "Humedad (%)": "La humedad es la cantidad de vapor de agua presente en el aire, es la relación entre la cantidad de vapor de agua real que contiene el aire y la cantidad máxima que podría contener a una temperatura determinada.",
    "UV": "Radiación ultravioleta se encuentra entre el extremo violeta del espectro visible y los rayos X, y que provoca reacciones químicas de gran repercusión biológica.",
    "Presion (Pa)": "Presión Atmosférica se define como la fuerza por unidad de área y su unidad estándar es el pascal (Pa) en el Sistema Internacional de Unidades.",
    "Temperatura (C)": "La temperatura en grados Celsius (°C) es una unidad de medida de calor o frío que se utiliza comúnmente en el sistema métrico.",
    "Gases (ug/m3)": "Gases medidos en microgramos por metro cúbico (ug/m3)",
    "Material Particulado": "Material Particulado medido en microgramos por metro cúbico (ug/m3)",
    "Variables Meteorológicas": "Variables Meteorológicas medidas en diferentes unidades",
    "Niveles de Presión Sonora": "Niveles de Presión Sonora medidos en decibelios (dB)",
}

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
            st.write(descripciones[elemento])
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
        gases = ['Fecha', 'CO (ug/m3)', 'H2S (ug/m3)', 'NO2 (ug/m3)', 'O3 (ug/m3)', 'SO2 (ug/m3)']
        material_particulados = ['Fecha', 'PM10 (ug/m3)', 'PM2,5 (ug/m3)']
        variables_meteorologicas = ['Fecha', 'Humedad (%)', 'UV', 'Presion (Pa)', 'Temperatura (C)']
        niveles_presion_sonora = ['Fecha', 'Ruido (dB)']

        if not inicio and not fin:
            st.error("Por favor seleccione al menos una fecha de inicio y una fecha de fin.")
        else:
            data = aire.loc[aire['Fecha'].between(inicio, fin)]

            data_gases = data[gases]
            st.write("### Gases (ug/m3)")
            st.write(descripciones["Gases (ug/m3)"])
            st.bar_chart(data_gases, x='Fecha', y=gases[1:], use_container_width=True)

            data_material_particulados = data[material_particulados]
            st.write("### Materiales Particulados (ug/m3)")
            st.write(descripciones["Material Particulado"])
            st.bar_chart(data_material_particulados, x='Fecha', y=material_particulados[1:], use_container_width=True)

            data_variables_meteorologicas = data[variables_meteorologicas]
            st.write("### Variables Meteorológicas")
            st.write(descripciones["Variables Meteorológicas"])
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
            st.write(descripciones["Niveles de Presión Sonora"])
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
        gases = ['Fecha', 'Ubicación', 'CO (ug/m3)', 'H2S (ug/m3)', 'NO2 (ug/m3)', 'O3 (ug/m3)', 'SO2 (ug/m3)']

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
            st.write(descripciones[niveles_presion_sonora[2:][0]])
            st.line_chart(data_variables_meteorologicas, x='Fecha', y=niveles_presion_sonora[2:][0], color="Ubicación", use_container_width=True)
    except Exception as e:
        imprimir_error(traceback.print_exc(e))

def cargar_pagina_dispersion():
    st.header("Análisis de Dispersión", divider="blue")

    # --- Define el nuevo texto descriptivo usando Markdown ---
    descripcion_dispersion_markdown = """
**Análisis de Dispersión: ¡Descubre Conexiones Ocultas!** 🕵️‍♀️💨

Explora cómo interactúan dos variables del aire que tú elijas. Cada punto en el gráfico es el **promedio diario** de esas variables para una **ubicación específica**. ¿Ves patrones visuales?

*   **Suben Juntos (↗):** Posible relación positiva.
*   **Uno Sube, Otro Baja (↘):** Posible relación negativa.
*   **Dispersos (░):** Poca o ninguna relación *lineal*.

**Correlación de Pearson (`r`):** Este número (-1 a +1) te da una pista sobre la fuerza de esa relación lineal:
*   `r ≈ +1`: Fuerte Positiva.
*   `r ≈ -1`: Fuerte Negativa.
*   `r ≈ 0`: Sin relación lineal clara.

**¡Importante!** Correlación no siempre significa que una variable *cause* la otra.

**¡Tu Turno!** Selecciona variables para los ejes X e Y. Usa los filtros de ubicación y fecha. ¿Qué relación inesperada encuentras entre, por ejemplo, `Ruido` y `PM10`? ¿O entre `Temperatura` y `O3`? ¡Busca *insights* y sorpréndete con los datos!
"""
    # --- Usa st.markdown para mostrar el texto formateado ---
    st.markdown(descripcion_dispersion_markdown) # Reemplaza la línea anterior

    try:
        aire = cargar_datos()
        if aire.empty:
            st.warning("No hay datos disponibles para mostrar.")
            return

        st.sidebar.header("Filtros (Dispersión)", divider="gray")
        # Filtros estándar de ubicación y fecha
        ubicaciones_disponibles = sorted(aire['Ubicación'].unique())
        default_ubicaciones = ubicaciones_disponibles
        ubicaciones = st.sidebar.multiselect("Ubicaciones", ubicaciones_disponibles, default=default_ubicaciones, key="disp_ubicaciones")

        fecha_min = aire['Fecha'].min().date()
        fecha_max = aire['Fecha'].max().date()
        inicio = np.datetime64(st.sidebar.date_input("Fecha de Inicio", value=fecha_min, min_value=fecha_min, max_value=fecha_max, key='disp_inicio'), 'ns')
        fin = np.datetime64(st.sidebar.date_input("Fecha de Fin", value=fecha_max, min_value=fecha_min, max_value=fecha_max, key='disp_fin'), 'ns')

        if not ubicaciones:
            st.error("Por favor seleccione al menos una localización.")
            return
        if inicio > fin:
             st.error("La fecha de inicio no puede ser posterior a la fecha de fin.")
             return

        # Filtrar datos según selecciones
        data_filtrada = aire[aire['Ubicación'].isin(ubicaciones) & aire['Fecha'].between(inicio, fin)].copy() # Usar .copy() para evitar SettingWithCopyWarning

        if data_filtrada.empty:
            st.warning("No hay datos para las selecciones realizadas.")
            return

        # --- Selección de variables para los ejes ---
        columnas_numericas = sorted([col for col in data_filtrada.columns if data_filtrada[col].dtype in ['int64', 'float64'] and col not in ['Latitud', 'Longitud']])
        if not columnas_numericas:
             st.warning("No se encontraron columnas numéricas adecuadas para el gráfico de dispersión.")
             return

        col1, col2 = st.columns(2)
        with col1:
            x_axis = st.selectbox("Seleccione Variable para Eje X:", columnas_numericas, index=columnas_numericas.index('Temperatura (C)') if 'Temperatura (C)' in columnas_numericas else 0 )
        with col2:
            # Asegurar que la variable Y no sea la misma que X por defecto si es posible
            default_y_index = 0
            if x_axis in columnas_numericas:
                if 'Humedad (%)' in columnas_numericas and 'Humedad (%)' != x_axis:
                    default_y_index = columnas_numericas.index('Humedad (%)')
                elif 'PM2,5 (ug/m3)' in columnas_numericas and 'PM2,5 (ug/m3)' != x_axis:
                     default_y_index = columnas_numericas.index('PM2,5 (ug/m3)')
                elif len(columnas_numericas) > 1:
                     default_y_index = 1 if x_axis == columnas_numericas[0] else 0 # Elegir la siguiente o la primera


            y_axis = st.selectbox("Seleccione Variable para Eje Y:", columnas_numericas, index=default_y_index)

        # --- Mostrar gráfico de dispersión ---
        if x_axis and y_axis:
            if x_axis == y_axis:
                st.warning("Seleccione variables diferentes para el eje X y el eje Y.")
            else:
                st.write(f"### Dispersión: {y_axis} vs {x_axis}")
                # Añadir tooltips opcionales (requiere ajustar el formato si es necesario)
                # data_filtrada['tooltip'] = data_filtrada.apply(lambda row: f"Fecha: {row['Fecha'].strftime('%Y-%m-%d')}<br>Ubicación: {row['Ubicación']}<br>{x_axis}: {row[x_axis]:.2f}<br>{y_axis}: {row[y_axis]:.2f}", axis=1)

                st.scatter_chart(
                    data_filtrada,
                    x=x_axis,
                    y=y_axis,
                    color="Ubicación", # Colorea los puntos según la ubicación
                    # size=None, # Podrías añadir tamaño basado en otra variable si quisieras
                    use_container_width=True
                    # tooltip='tooltip' # Descomentar si definiste la columna tooltip
                )
                # Opcional: Mostrar correlación
                try:
                    correlation = data_filtrada[x_axis].corr(data_filtrada[y_axis])
                    st.write(f"Correlación de Pearson entre {x_axis} y {y_axis}: {correlation:.3f}")
                except Exception:
                    st.write("No se pudo calcular la correlación (podría haber valores NaN).")

        else:
            st.info("Seleccione variables para los ejes X e Y para ver el gráfico.")

    except Exception as e:
        imprimir_error("Error al cargar la página de análisis de dispersión", e)

def cargar_comparativa_ubicacion():
    st.header("Comparativa por Ubicación", divider="blue")
    st.write("Compare la distribución de una variable ambiental entre diferentes ubicaciones.")

    try:
        aire = cargar_datos()
        if aire.empty:
            st.warning("No hay datos disponibles.")
            return

        # Variables categóricas y numéricas
        ubicaciones_disponibles = sorted(aire['Ubicación'].unique())
        columnas_numericas = sorted([
            col for col in aire.columns
            if aire[col].dtype in ['float64', 'int64'] and col not in ['Latitud', 'Longitud']
        ])

        st.sidebar.header("Filtros (Comparativa)", divider="gray")
        ubicaciones = st.sidebar.multiselect("Ubicaciones", ubicaciones_disponibles, ubicaciones_disponibles, key="comp_ubicaciones")
        variable = st.sidebar.selectbox("Variable a Comparar", columnas_numericas)

        if not ubicaciones or not variable:
            st.warning("Seleccione al menos una ubicación y una variable.")
            return

        data = aire[aire['Ubicación'].isin(ubicaciones)][['Ubicación', variable]].dropna()

        if data.empty:
            st.warning("No hay datos para la variable y ubicaciones seleccionadas.")
            return

        # Boxplot
        st.write(f"### Distribución de **{variable}** por Ubicación")
        fig = px.box(data, x='Ubicación', y=variable, color='Ubicación', points="all")
        st.plotly_chart(fig, use_container_width=True)

        st.caption("Este gráfico muestra la distribución estadística de la variable seleccionada para cada ubicación. Incluye mediana, cuartiles y posibles valores atípicos.")

    except Exception as e:
        imprimir_error("Error al cargar la página Comparativa por Ubicación", e)

def cargar_pagina_calmap():
    st.header("Mapa de Calor Calendario Anual", divider="blue")
    st.write("""
    Visualiza la intensidad diaria de una variable a lo largo de un año completo.
    Los colores más intensos indican valores más altos de la variable seleccionada.
    Permite identificar patrones estacionales, semanales o días específicos con valores anómalos.
    Los datos mostrados son el **promedio diario de todas las ubicaciones**.
    """)

    try:
        aire_full = cargar_datos() # Carga los datos agrupados por día y ubicación
        if aire_full.empty:
            st.warning("No hay datos disponibles para mostrar.")
            return

        # --- Calcular Promedio Diario General ---
        # 1. Identificar columnas numéricas (excluyendo Lat/Lon si aún están)
        columnas_numericas = sorted([
            col for col in aire_full.columns
            if pd.api.types.is_numeric_dtype(aire_full[col]) and col not in ['Latitud', 'Longitud']
        ])
        if not columnas_numericas:
            st.warning("No se encontraron variables numéricas para promediar.")
            return

        # 2. Agrupar por Fecha (diaria) y calcular la media de las numéricas
        try:
            # Asegurarse que 'Fecha' está como datetime
            aire_full['Fecha'] = pd.to_datetime(aire_full['Fecha'])
            # Agrupar solo si hay columnas numéricas
            aire_daily_avg = aire_full.groupby('Fecha')[columnas_numericas].mean().reset_index()
        except KeyError as ke:
             st.error(f"Error al agrupar: La columna {ke} no se encontró después de cargar los datos.")
             return
        except Exception as agg_e:
             st.error(f"Error inesperado durante la agregación diaria: {agg_e}")
             st.code(traceback.format_exc())
             return


        if aire_daily_avg.empty:
            st.warning("No se pudieron calcular los promedios diarios.")
            return

        # --- Filtros en Sidebar ---
        st.sidebar.header("Filtros (Calendario)", divider="gray")

        # Selector de Variable
        # Filtrar nuevamente las columnas numéricas DESPUÉS de la agregación diaria
        variables_disponibles = sorted([
            col for col in aire_daily_avg.columns
            if pd.api.types.is_numeric_dtype(aire_daily_avg[col])
        ])
        if not variables_disponibles:
             st.warning("No hay variables numéricas disponibles después de promediar.")
             return
        variable_seleccionada = st.sidebar.selectbox(
            "Seleccione Variable",
            variables_disponibles,
            key="calmap_variable"
        )

        # Selector de Año
        available_years = sorted(aire_daily_avg['Fecha'].dt.year.unique())
        if not available_years:
             st.warning("No se encontraron años en los datos.")
             return
        selected_year = st.sidebar.selectbox(
            "Seleccione Año",
            available_years,
            index=len(available_years)-1, # Seleccionar el último año por defecto
            key="calmap_year"
        )

        # --- Preparar Datos para Calplot ---
        # Filtrar por año
        year_data = aire_daily_avg[aire_daily_avg['Fecha'].dt.year == selected_year].copy()

        if year_data.empty:
            st.warning(f"No hay datos disponibles para el año {selected_year}.")
            return

        # Crear la Serie requerida por calplot (Índice Datetime, Valores de la variable)
        # Asegurarse que no hay fechas duplicadas (no debería si agrupamos bien)
        year_data = year_data.drop_duplicates(subset='Fecha')
        data_series = year_data.set_index('Fecha')[variable_seleccionada]

        # Eliminar NaNs si calplot no los maneja bien (opcional, probar primero sin esto)
        data_series.dropna(inplace=True)

        if data_series.empty:
            st.warning(f"No hay datos válidos (no nulos) para '{variable_seleccionada}' en el año {selected_year}.")
            return

        # --- Generar y Mostrar el Gráfico Calplot ---
        st.write(f"### Intensidad Diaria de **{variable_seleccionada}** en {selected_year}")

        try:
            # Crear la figura calplot
            fig = calplot(
                data_series,
                cmap='viridis', # Puedes cambiar el mapa de color (e.g., 'YlGnBu', 'Reds', 'coolwarm')
                figsize=(1000, 250), # Ajustar tamaño si es necesario
                month_lines_color="#D3D3D3", # Color de líneas entre meses
                month_lines_width=2,
                year_label_fontsize=14,
                month_label_fontsize=10
            )

            # Añadir un título más descriptivo a la figura de Plotly
            fig.update_layout(
                title_text=f"Calendario de {variable_seleccionada} - Año {selected_year}",
                title_x=0.5 # Centrar título
            )

            st.plotly_chart(fig, use_container_width=True)

        except ImportError:
             st.error("La librería 'plotly_calplot' no está instalada. Ejecuta: pip install plotly_calplot")
        except Exception as plot_err:
             st.error(f"Ocurrió un error al generar el mapa de calor del calendario: {plot_err}")
             st.code(traceback.format_exc())


    except Exception as e:
        # Usar la función imprimir_error corregida
        imprimir_error("Error general al cargar la página del Mapa de Calor Calendario", e)

paginas_a_funciones = {
    "Inicio": cargar_inicio,
    "Resumen": cargar_resumen,
    "Gases": cargar_gases,
    "Material Particulado": cargar_material_particulados,
    "Variables Meteorológicas": cargar_variables_meteorologicas,
    "Niveles de Presión Sonora": cargar_niveles_presion_sonora,
    "Análisis de Dispersión": cargar_pagina_dispersion,
    "Comparativa por Ubicación": cargar_comparativa_ubicacion,
    "Calendario Anual": cargar_pagina_calmap,
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