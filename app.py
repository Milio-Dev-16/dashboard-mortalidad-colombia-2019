import dash
from dash import dcc, html, dash_table, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

# --- Definición de la Paleta de Colores Temática ---
color_fondo_principal = '#1E1E1E'
color_fondo_elementos = '#2C2C2C'
color_texto_principal = '#F5F5F5'
color_texto_secundario = '#B0B0B0'
color_borde_elementos = '#444444'
color_acento_amarillo = '#FFCD00' # Amarillo Bandera
color_acento_azul = '#003893'     # Azul Bandera
color_acento_rojo = '#CE1126'     # Rojo Bandera

# Escala de color para el mapa, integrando el tema.
map_color_scale_simple = [[0, color_fondo_elementos], [1, color_acento_amarillo]]

# ========== CARGA DE DATOS ==========
# Se intenta cargar los datos desde los archivos Excel y GeoJSON.
# Es importante que estos archivos estén en la carpeta 'data/' o se ajuste la ruta.
try:
    mortalidad = pd.read_excel('data/Anexo1.NoFetal2019_CE_15-03-23.xlsx', sheet_name='No_Fetales_2019')
    codigos_muerte_raw = pd.read_excel('data/Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx', sheet_name=None)
    divipola = pd.read_excel('data/Anexo3.Divipola_CE_15-03-23.xlsx')
    with open('data/departamentos_colombia__plotly.geojson', encoding='utf-8') as f:
        geojson_departamentos = json.load(f)
except FileNotFoundError as e:
    # Manejo de error si no se encuentran los archivos de datos.
    print(f"Error: No se encontró el archivo de datos: {e.filename}. Se usarán DataFrames vacíos.")
    mortalidad = pd.DataFrame()
    codigos_muerte_raw = {}
    divipola = pd.DataFrame()
    geojson_departamentos = {"type": "FeatureCollection", "features": []}
except Exception as e:
    print(f"Ocurrió un error al cargar los datos: {e}. Se usarán DataFrames vacíos.")
    mortalidad = pd.DataFrame()
    codigos_muerte_raw = {}
    divipola = pd.DataFrame()
    geojson_departamentos = {"type": "FeatureCollection", "features": []}


# ========== PREPROCESAMIENTO DE DATOS ==========
# Se realizan varias operaciones para preparar los datos para la visualización.

# Procesamiento de códigos de departamento y cálculo de muertes por departamento.
if not mortalidad.empty:
    mortalidad['COD_DEPARTAMENTO'] = mortalidad['COD_DEPARTAMENTO'].astype(str).str.zfill(2)
    dep_muertes = mortalidad.groupby('COD_DEPARTAMENTO').size().reset_index(name='Total_Muertes')
else:
    dep_muertes = pd.DataFrame(columns=['COD_DEPARTAMENTO', 'Total_Muertes'])

# Procesamiento de datos geográficos para el mapa.
if geojson_departamentos and geojson_departamentos['features']:
    geo_departamentos_df = pd.DataFrame([
        {'DPTO_CCDGO': str(f['properties']['DPTO_CCDGO']).zfill(2), 'DPTO_CNMBR': f['properties']['DPTO_CNMBR']}
        for f in geojson_departamentos['features']
    ])
else:
    geo_departamentos_df = pd.DataFrame(columns=['DPTO_CCDGO', 'DPTO_CNMBR'])

# Unión de datos de muertes con datos geográficos.
df_mapa = geo_departamentos_df.merge(dep_muertes, left_on='DPTO_CCDGO', right_on='COD_DEPARTAMENTO', how='left')
df_mapa['Total_Muertes'] = df_mapa['Total_Muertes'].fillna(0)

# Unión de datos de mortalidad con información de DIVIPOLA para obtener nombres de municipios y departamentos.
if not mortalidad.empty and not divipola.empty and 'COD_DANE' in mortalidad.columns and 'COD_DANE' in divipola.columns:
    mortalidad['COD_DANE'] = mortalidad['COD_DANE'].astype(str)
    divipola['COD_DANE'] = divipola['COD_DANE'].astype(str)
    mortalidad = mortalidad.merge(divipola[['COD_DANE', 'MUNICIPIO', 'DEPARTAMENTO']], on='COD_DANE', how='left', suffixes=('', '_divipola'))
    # Consolidar columnas de municipio y departamento si hay duplicados por el merge.
    if 'MUNICIPIO_divipola' in mortalidad.columns:
        mortalidad['MUNICIPIO'] = mortalidad['MUNICIPIO_divipola']
        mortalidad.drop(columns=['MUNICIPIO_divipola'], inplace=True)
    if 'DEPARTAMENTO_divipola' in mortalidad.columns:
        mortalidad['DEPARTAMENTO'] = mortalidad['DEPARTAMENTO_divipola']
        mortalidad.drop(columns=['DEPARTAMENTO_divipola'], inplace=True)
else:
    # Asegurar que las columnas existan si los DataFrames originales estaban vacíos.
    if 'MUNICIPIO' not in mortalidad.columns: mortalidad['MUNICIPIO'] = None
    if 'DEPARTAMENTO' not in mortalidad.columns: mortalidad['DEPARTAMENTO'] = None

# ========== DEFINICIÓN DE FIGURAS DE PLOTLY CON TEMA OSCURO ==========
# Se crean las figuras base para cada visualización.
# Se aplica el tema 'plotly_dark' y se personalizan colores y layout.
# Se evita fijar alturas aquí para permitir mayor responsividad.

# --- Figura: Mapa de Coropletas ---
mapa = px.choropleth(
    df_mapa, geojson=geojson_departamentos, locations='DPTO_CCDGO',
    featureidkey='properties.DPTO_CCDGO', color='Total_Muertes',
    color_continuous_scale=map_color_scale_simple,
    labels={'Total_Muertes': 'Total de Muertes'}, hover_name='DPTO_CNMBR',
    template='plotly_dark'
)
mapa.update_geos(
    fitbounds="locations", visible=True, projection_type="mercator",
    bgcolor='rgba(0,0,0,0)', landcolor=color_fondo_elementos, subunitcolor=color_borde_elementos
)
mapa.update_layout(
    margin={"r":0,"t":0,"l":0,"b":0}, # Margen ajustado para previews
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font_color=color_texto_principal, geo_bgcolor='rgba(0,0,0,0)'
)

# --- Figura: Líneas de Muertes por Mes ---
if not mortalidad.empty and 'MES' in mortalidad.columns:
    muertes_mes_df = mortalidad.groupby('MES').size().reset_index(name='Muertes')
else:
    muertes_mes_df = pd.DataFrame({'MES': [], 'Muertes': []})
lineas = px.line(muertes_mes_df, x='MES', y='Muertes', markers=True, template='plotly_dark')
lineas.update_traces(line_color=color_acento_amarillo, marker_color=color_acento_amarillo)
lineas.update_layout(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font_color=color_texto_principal,
    xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
    yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
)

# --- Figura: Barras de Ciudades Violentas ---
if not mortalidad.empty and 'COD_MUERTE' in mortalidad.columns and 'MUNICIPIO' in mortalidad.columns:
    homicidios = mortalidad[mortalidad['COD_MUERTE'].str.startswith('X95', na=False)]
    violentas_df = homicidios.groupby('MUNICIPIO').size().reset_index(name='Homicidios')
    top_5_violentas = violentas_df.sort_values(by='Homicidios', ascending=False).head(5)
else:
    top_5_violentas = pd.DataFrame({'MUNICIPIO': [], 'Homicidios': []})
barras_violentas = px.bar(top_5_violentas, x='MUNICIPIO', y='Homicidios', template='plotly_dark')
barras_violentas.update_traces(marker_color=color_acento_rojo)
barras_violentas.update_layout(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font_color=color_texto_principal,
    xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
    yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
)

# --- Figura: Gráfico de Torta de Ciudades Menos Mortales ---
if not mortalidad.empty and 'MUNICIPIO' in mortalidad.columns:
    muertes_ciudad_df = mortalidad.groupby('MUNICIPIO').size().reset_index(name='Total')
    menos_muertes_df = muertes_ciudad_df.sort_values(by='Total').head(10)
else:
    menos_muertes_df = pd.DataFrame({'MUNICIPIO': [], 'Total': []})
pie = px.pie(menos_muertes_df, names='MUNICIPIO', values='Total', template='plotly_dark',
             color_discrete_sequence=[color_acento_azul, color_acento_amarillo, '#007A6C', '#FF8C00', '#708090'])
pie.update_layout(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font_color=color_texto_principal, legend_font_color=color_texto_principal
)

# --- Tablas: Causas de Muerte ---
if not mortalidad.empty and 'COD_MUERTE' in mortalidad.columns:
    causas_df = mortalidad.groupby('COD_MUERTE').size().reset_index(name='Total')
    top_causas_principal_df = causas_df.sort_values(by='Total', ascending=False).head(10)
    top_causas_preview_df = top_causas_principal_df.head(3)
else:
    top_causas_principal_df = pd.DataFrame({'COD_MUERTE': [], 'Total': []})
    top_causas_preview_df = pd.DataFrame({'COD_MUERTE': [], 'Total': []})

# Estilos para las tablas en tema oscuro.
table_style_dark = {
    'style_table':{'overflowX': 'auto', 'backgroundColor': color_fondo_elementos, 'width': '100%'}, # Asegurar ancho
    'style_cell': {'textAlign': 'left', 'padding': '10px', 'fontFamily': 'Arial, sans-serif',
                   'backgroundColor': color_fondo_elementos, 'color': color_texto_principal,
                   'border': f'1px solid {color_borde_elementos}'},
    'style_header': {'backgroundColor': color_fondo_principal, 'fontWeight': 'bold',
                     'color': color_acento_amarillo, 'border': f'1px solid {color_borde_elementos}'},
    'style_data_conditional': [{'if': {'row_index': 'odd'}, 'backgroundColor': '#363636'}]
}
preview_table_style_dark = {
    'style_table':{'overflow': 'hidden', 'height': '100%', 'backgroundColor': color_fondo_elementos},
    'style_cell': {'textAlign': 'left', 'padding': '5px', 'fontSize': '10px', 'fontFamily': 'Arial, sans-serif',
                   'whiteSpace': 'nowrap', 'overflow': 'hidden', 'textOverflow': 'ellipsis', 'maxWidth': '70px',
                   'backgroundColor': color_fondo_elementos, 'color': color_texto_principal,
                   'border': f'1px solid {color_borde_elementos}'},
    'style_header': {'backgroundColor': color_fondo_principal, 'fontWeight': 'bold', 'fontSize': '11px',
                     'fontFamily': 'Arial, sans-serif', 'padding': '5px', 'color': color_acento_amarillo,
                     'border': f'1px solid {color_borde_elementos}'},
    'style_data': {'borderBottom': f'1px solid {color_borde_elementos}'}
}

tabla_principal_causas = dash_table.DataTable(
    id='tabla-causas-principal',
    columns=[{'name': 'Código', 'id': 'COD_MUERTE'}, {'name': 'Total', 'id': 'Total'}],
    data=top_causas_principal_df.to_dict('records'),
    **table_style_dark
)
preview_tabla_causas = dash_table.DataTable(
    id='preview-tabla-causas',
    columns=[{'name': 'Cód.', 'id': 'COD_MUERTE'}, {'name': 'Cant.', 'id': 'Total'}],
    data=top_causas_preview_df.to_dict('records'),
    **preview_table_style_dark
)

# --- Figura: Histograma de Muertes por Edad ---
if not mortalidad.empty and 'GRUPO_EDAD1' in mortalidad.columns:
    histograma = px.histogram(mortalidad, x='GRUPO_EDAD1', template='plotly_dark')
else:
    histograma = px.histogram(pd.DataFrame({'GRUPO_EDAD1':[]}), x='GRUPO_EDAD1', template='plotly_dark')
histograma.update_traces(marker_color=color_acento_azul)
histograma.update_layout(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font_color=color_texto_principal, bargap=0.1,
    xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
    yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
)

# --- Figura: Barras de Muertes por Sexo y Departamento ---
if not mortalidad.empty and 'DEPARTAMENTO' in mortalidad.columns and 'SEXO' in mortalidad.columns:
    sexo_dep_df = mortalidad.groupby(['DEPARTAMENTO', 'SEXO']).size().reset_index(name='Total')
    sexo_dep_df['SEXO'] = sexo_dep_df['SEXO'].map({1: 'Hombre', 2: 'Mujer', '1':'Hombre', '2':'Mujer'}).fillna('No especificado')
else:
    sexo_dep_df = pd.DataFrame({'DEPARTAMENTO':[], 'SEXO':[], 'Total':[]})
barras_sexo = px.bar(sexo_dep_df, x='DEPARTAMENTO', y='Total', color='SEXO', template='plotly_dark',
                     color_discrete_map={'Hombre': color_acento_azul, 'Mujer': color_acento_amarillo, 'No especificado': '#777777'})
barras_sexo.update_layout(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font_color=color_texto_principal, legend_font_color=color_texto_principal,
    xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
    yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
)

# ========== INICIALIZACIÓN DE LA APP DASH ==========
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server # Necesario para el despliegue con Gunicorn

# ========== LAYOUT GENERAL DE LA APLICACIÓN ==========
# Se define la estructura HTML de la página.
# Se utiliza un Div principal para controlar el ancho máximo y evitar desbordamientos.
app.layout = html.Div([
    dcc.Location(id='url', refresh=False), # Componente para manejar la URL y la navegación
    html.Div([
        html.H2("Visualización Mortalidad Colombia 2019", style={'textAlign': 'center', 'color': color_acento_amarillo})
    ], className='sidebar'),

    # Contenedor para las tarjetas de previsualización de los gráficos.
    html.Div([
        dcc.Link([html.Div([dcc.Graph(id='preview-mapa',figure=mapa.update_layout(margin=dict(l=0,r=0,t=0,b=0), showlegend=False, title_text=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'),config={'displayModeBar': False},style={'height': '160px', 'width': '100%'},),html.Div("Mapa de Muertes", className='preview-title')], className='preview-card-content')], href='/mapa', className='preview-card-link'),
        dcc.Link([html.Div([dcc.Graph(id='preview-mes',figure=lineas.update_layout(margin=dict(l=15,r=5,t=5,b=15), showlegend=False, title_text=None, xaxis=dict(showticklabels=False, title=None, showgrid=False, zeroline=False), yaxis=dict(showticklabels=False, title=None, showgrid=False, zeroline=False), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)') ,config={'displayModeBar': False}, style={'height': '160px', 'width': '100%'}),html.Div("Muertes por Mes", className='preview-title')], className='preview-card-content')], href='/mes', className='preview-card-link'),
        dcc.Link([html.Div([dcc.Graph(id='preview-violencia',figure=barras_violentas.update_layout(margin=dict(l=15,r=5,t=5,b=20), showlegend=False, title_text=None, xaxis=dict(showticklabels=False, title=None, showgrid=False, zeroline=False, tickangle=0), yaxis=dict(showticklabels=False, title=None, showgrid=False, zeroline=False),paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'),config={'displayModeBar': False}, style={'height': '160px', 'width': '100%'}),html.Div("Ciudades Violentas", className='preview-title')], className='preview-card-content')], href='/violencia', className='preview-card-link'),
        dcc.Link([html.Div([dcc.Graph(id='preview-menos',figure=pie.update_layout(margin=dict(l=0,r=0,t=0,b=0), showlegend=False, title_text=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'),config={'displayModeBar': False}, style={'height': '160px', 'width': '100%'}),html.Div("Ciudades Seguras", className='preview-title')], className='preview-card-content')], href='/menos', className='preview-card-link'),
        dcc.Link([html.Div([html.Div(preview_tabla_causas, style={'height': '160px', 'padding': '5px', 'boxSizing': 'border-box', 'overflow': 'hidden', 'width':'100%'}),html.Div("Causas de Muerte", className='preview-title')], className='preview-card-content')], href='/causas', className='preview-card-link'),
        dcc.Link([html.Div([dcc.Graph(id='preview-edad',figure=histograma.update_layout(margin=dict(l=15,r=5,t=5,b=15), showlegend=False, title_text=None, bargap=0.2, xaxis=dict(showticklabels=False, title=None, showgrid=False, zeroline=False), yaxis=dict(showticklabels=False, title=None, showgrid=False, zeroline=False), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'), config={'displayModeBar': False}, style={'height': '160px', 'width': '100%'}),html.Div("Muertes por Edad", className='preview-title')], className='preview-card-content')], href='/edad', className='preview-card-link'),
        dcc.Link([html.Div([dcc.Graph(id='preview-sexo',figure=barras_sexo.update_layout(margin=dict(l=15,r=5,t=5,b=15), showlegend=False, title_text=None, xaxis=dict(showticklabels=False, title=None, showgrid=False, zeroline=False), yaxis=dict(showticklabels=False, title=None, showgrid=False, zeroline=False), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'), config={'displayModeBar': False}, style={'height': '160px', 'width': '100%'}),html.Div("Muertes por Sexo", className='preview-title')], className='preview-card-content')], href='/sexo', className='preview-card-link'),
    ], className='preview-container'),

    # Contenedor donde se renderizará el contenido de cada página/vista.
    html.Div(id='page-content', className='content')
], style={'maxWidth': '100%', 'overflowX': 'hidden'}) # Control del ancho general y desbordamiento

# ========== CALLBACK PARA LA NAVEGACIÓN Y RENDERIZADO DE PÁGINAS ==========
# Este callback actualiza el contenido de 'page-content' según la URL.
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    # Función auxiliar para crear un contenedor estándar para cada gráfico/tabla principal.
    def graph_container(title_H2, graph_component_original, component_id=None, is_table=False):
        graph_fig_to_show = go.Figure(graph_component_original) if isinstance(graph_component_original, go.Figure) else graph_component_original

        if isinstance(graph_fig_to_show, go.Figure):
            # Ajustes generales de layout para los gráficos en la vista principal.
            graph_fig_to_show.update_layout(
                title_text=None, # No se usa el título interno de Plotly, se usa el H2.
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color=color_texto_principal,
                legend_font_color=color_texto_secundario,
                # Se definen configuraciones base para los ejes.
                xaxis=dict(showticklabels=True, gridcolor='rgba(255,255,255,0.1)', title_font_color=color_texto_secundario, tickfont_color=color_texto_secundario),
                yaxis=dict(showticklabels=True, gridcolor='rgba(255,255,255,0.1)', title_font_color=color_texto_secundario, tickfont_color=color_texto_secundario),
                # Permitir que el gráfico se ajuste automáticamente a su contenedor.
                # No se define una altura fija aquí, se espera que el CSS o el estilo del dcc.Graph lo manejen.
                # height=None, # Podría ser explícito para forzar autosize si hay problemas.
                autosize=True
            )
            # Ajustes específicos por tipo de gráfico (títulos de ejes, leyendas, etc.)
            if component_id == 'main-mapa-graph':
                graph_fig_to_show.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            elif component_id == 'main-mes-graph':
                 graph_fig_to_show.update_layout(xaxis_title="Mes", yaxis_title="Número de muertes")
            elif component_id == 'main-violencia-graph':
                 graph_fig_to_show.update_layout(xaxis_title="Ciudad", yaxis_title="Número de homicidios", xaxis_tickangle=-45)
            elif component_id == 'main-menos-graph':
                 graph_fig_to_show.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            elif component_id == 'main-edad-graph':
                 graph_fig_to_show.update_layout(xaxis_title="Grupo de Edad", yaxis_title="Número de muertes", bargap=0.1)
            elif component_id == 'main-sexo-graph':
                 graph_fig_to_show.update_layout(xaxis_title="Departamento", yaxis_title="Número de muertes", xaxis_tickangle=-45, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))

            # Se crea el componente dcc.Graph. Se puede añadir un estilo para altura relativa si es necesario.
            graph_component_to_render = dcc.Graph(
                figure=graph_fig_to_show,
                id=component_id if component_id else title_H2.replace(" ", "-").lower(),
                style={'height': '65vh'} # Altura relativa al viewport para gráficos principales
            )
        else: # Para tablas
            graph_component_to_render = graph_fig_to_show

        return html.Div([
            html.H2(title_H2, style={'marginBottom': '20px', 'color': color_acento_amarillo, 'fontFamily': 'Arial, sans-serif'}),
            html.Div(graph_component_to_render, className='graph-container-main')
        ], className='content-container')

    # Rutas para cada visualización. Se clonan las figuras base para evitar modificaciones accidentales.
    if pathname == '/mapa':
        return graph_container('1. Mapa de muertes por departamento', go.Figure(mapa), component_id='main-mapa-graph')
    elif pathname == '/mes':
        return graph_container('2. Total de muertes por mes', go.Figure(lineas), component_id='main-mes-graph')
    elif pathname == '/violencia':
        return graph_container('3. 5 ciudades más violentas (homicidios)', go.Figure(barras_violentas), component_id='main-violencia-graph')
    elif pathname == '/menos':
        return graph_container('4. 10 ciudades con menor mortalidad', go.Figure(pie), component_id='main-menos-graph')
    elif pathname == '/causas':
        return graph_container('5. Top 10 causas de muerte', tabla_principal_causas, is_table=True)
    elif pathname == '/edad':
        return graph_container('6. Histograma de muertes por edad', go.Figure(histograma), component_id='main-edad-graph')
    elif pathname == '/sexo':
        return graph_container('7. Muertes por sexo en cada departamento', go.Figure(barras_sexo), component_id='main-sexo-graph')
    else: # Página de bienvenida por defecto
        return html.Div([
            html.H1("Análisis de Mortalidad en Colombia 2019", style={'textAlign': 'center', 'marginTop': '50px', 'color': color_acento_amarillo, 'fontFamily': 'Arial, sans-serif', 'fontSize':'2em'}),
            html.P("Seleccione una visualización del menú superior o haga clic en cualquiera de las miniaturas arriba.", style={'textAlign': 'center', 'color': color_texto_principal, 'fontSize': '1.1em', 'fontFamily': 'Arial, sans-serif', 'marginTop':'20px'})
        ], className='welcome-container', style={'padding': '20px', 'minHeight': '60vh'})

# ========== EJECUCIÓN DE LA APLICACIÓN ==========
if __name__ == '__main__':
    # Ejecutar el servidor Dash. 'debug=True' es útil para desarrollo.
    app.run(debug=True)