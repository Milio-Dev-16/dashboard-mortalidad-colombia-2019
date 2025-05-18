import dash
from dash import dcc, html, dash_table, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # Para más control en algunos casos
import json

# --- Paleta de Colores Colombia Oscuro ---
color_fondo_principal = '#1E1E1E'
color_fondo_elementos = '#2C2C2C'
color_texto_principal = '#F5F5F5'
color_texto_secundario = '#B0B0B0'
color_borde_elementos = '#444444'

color_acento_amarillo = '#FFCD00' # Amarillo Bandera
color_acento_azul = '#003893'     # Azul Bandera
color_acento_rojo = '#CE1126'     # Rojo Bandera (usar con moderación o para alertas)

# Escala para mapa (de un gris a amarillo)
map_color_scale = [
    [0.0, color_fondo_elementos],
    [0.2, px.colors.sequential.YlOrBr[2]],
    [0.4, px.colors.sequential.YlOrBr[3]],
    [0.6, px.colors.sequential.YlOrBr[4]],
    [0.8, px.colors.sequential.YlOrBr[5]],
    [1.0, color_acento_amarillo]
]
# O una escala más simple:
map_color_scale_simple = [[0, color_fondo_elementos], [1, color_acento_amarillo]]


# ========== CARGA DE DATOS (igual que antes) ==========
try:
    mortalidad = pd.read_excel('data/Anexo1.NoFetal2019_CE_15-03-23.xlsx', sheet_name='No_Fetales_2019')
    codigos_muerte_raw = pd.read_excel('data/Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx', sheet_name=None) # Descomentado
    divipola = pd.read_excel('data/Anexo3.Divipola_CE_15-03-23.xlsx')
    with open('data/departamentos_colombia__plotly.geojson', encoding='utf-8') as f:
        geojson_departamentos = json.load(f)
except FileNotFoundError as e:
    print(f"Error: No se encontró el archivo de datos: {e.filename}")
    mortalidad = pd.DataFrame()
    codigos_muerte_raw = {} # Vacío si no se carga
    divipola = pd.DataFrame()
    geojson_departamentos = {"type": "FeatureCollection", "features": []}

# ========== PREPROCESAMIENTO (igual que antes, con manejo de DataFrames vacíos) ==========
# ... (El código de preprocesamiento se mantiene, asegúrate que maneja bien los DF vacíos) ...
# Preprocesamiento (se ejecutará incluso si los datos están vacíos, lo que podría generar advertencias o errores si se esperan ciertas columnas)
if not mortalidad.empty:
    mortalidad['COD_DEPARTAMENTO'] = mortalidad['COD_DEPARTAMENTO'].astype(str).str.zfill(2)
    dep_muertes = mortalidad.groupby('COD_DEPARTAMENTO').size().reset_index(name='Total_Muertes')
else:
    dep_muertes = pd.DataFrame(columns=['COD_DEPARTAMENTO', 'Total_Muertes'])

if geojson_departamentos['features']:
    geo_departamentos_df = pd.DataFrame([
        {'DPTO_CCDGO': str(f['properties']['DPTO_CCDGO']).zfill(2), 'DPTO_CNMBR': f['properties']['DPTO_CNMBR']}
        for f in geojson_departamentos['features']
    ])
else:
    geo_departamentos_df = pd.DataFrame(columns=['DPTO_CCDGO', 'DPTO_CNMBR'])


df_mapa = geo_departamentos_df.merge(dep_muertes, left_on='DPTO_CCDGO', right_on='COD_DEPARTAMENTO', how='left')
df_mapa['Total_Muertes'] = df_mapa['Total_Muertes'].fillna(0)

if not mortalidad.empty and not divipola.empty and 'COD_DANE' in mortalidad.columns and 'COD_DANE' in divipola.columns:
    mortalidad['COD_DANE'] = mortalidad['COD_DANE'].astype(str)
    divipola['COD_DANE'] = divipola['COD_DANE'].astype(str)
    mortalidad = mortalidad.merge(divipola[['COD_DANE', 'MUNICIPIO', 'DEPARTAMENTO']], on='COD_DANE', how='left', suffixes=('', '_divipola'))
    if 'MUNICIPIO_divipola' in mortalidad.columns:
        mortalidad['MUNICIPIO'] = mortalidad['MUNICIPIO_divipola']
        mortalidad.drop(columns=['MUNICIPIO_divipola'], inplace=True)
    if 'DEPARTAMENTO_divipola' in mortalidad.columns:
        mortalidad['DEPARTAMENTO'] = mortalidad['DEPARTAMENTO_divipola']
        mortalidad.drop(columns=['DEPARTAMENTO_divipola'], inplace=True)
else:
    if 'MUNICIPIO' not in mortalidad.columns: mortalidad['MUNICIPIO'] = None
    if 'DEPARTAMENTO' not in mortalidad.columns: mortalidad['DEPARTAMENTO'] = None

# ========== FIGURAS CON TEMA OSCURO ==========

# --- Mapa ---
mapa = px.choropleth(
    df_mapa, geojson=geojson_departamentos, locations='DPTO_CCDGO',
    featureidkey='properties.DPTO_CCDGO', color='Total_Muertes',
    color_continuous_scale=map_color_scale_simple, # Usando la escala definida
    labels={'Total_Muertes': 'Total de Muertes'}, hover_name='DPTO_CNMBR',
    hover_data={'DPTO_CCDGO': False, 'Total_Muertes': True},
    template='plotly_dark' # Aplicando tema oscuro base
)
mapa.update_geos(
    fitbounds="locations", visible=True, projection_type="mercator",
    bgcolor='rgba(0,0,0,0)', # Fondo del geo transparente
    landcolor=color_fondo_elementos, # Color de la tierra si no hay datos
    subunitcolor=color_borde_elementos # Color de las fronteras
)
mapa.update_layout(
    margin={"r":0,"t":50,"l":0,"b":0},
    paper_bgcolor='rgba(0,0,0,0)', # Fondo del layout transparente
    plot_bgcolor='rgba(0,0,0,0)',  # Fondo del plot transparente
    font_color=color_texto_principal,
    title_font_color=color_texto_principal,
    geo_bgcolor='rgba(0,0,0,0)'
)


# --- Muertes por Mes ---
if not mortalidad.empty and 'MES' in mortalidad.columns:
    muertes_mes_df = mortalidad.groupby('MES').size().reset_index(name='Muertes')
else:
    muertes_mes_df = pd.DataFrame({'MES': [], 'Muertes': []})
lineas = px.line(muertes_mes_df, x='MES', y='Muertes', markers=True, template='plotly_dark')
lineas.update_traces(line_color=color_acento_amarillo, marker_color=color_acento_amarillo)
lineas.update_layout(
    xaxis_title="Mes", yaxis_title="Número de muertes", title_text='Total de muertes por mes en 2019',
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font_color=color_texto_principal, title_font_color=color_texto_principal,
    xaxis=dict(gridcolor='rgba(255,255,255,0.1)'), # Líneas de cuadrícula sutiles
    yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
)

# --- Ciudades Violentas ---
if not mortalidad.empty and 'COD_MUERTE' in mortalidad.columns and 'MUNICIPIO' in mortalidad.columns:
    homicidios = mortalidad[mortalidad['COD_MUERTE'].str.startswith('X95', na=False)]
    violentas_df = homicidios.groupby('MUNICIPIO').size().reset_index(name='Homicidios')
    top_5_violentas = violentas_df.sort_values(by='Homicidios', ascending=False).head(5)
else:
    top_5_violentas = pd.DataFrame({'MUNICIPIO': [], 'Homicidios': []})
barras_violentas = px.bar(top_5_violentas, x='MUNICIPIO', y='Homicidios', template='plotly_dark')
barras_violentas.update_traces(marker_color=color_acento_rojo) # Rojo para violencia
barras_violentas.update_layout(
    xaxis_title="Municipio", yaxis_title="Número de Homicidios", title_text='5 ciudades más violentas (Homicidios)',
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font_color=color_texto_principal, title_font_color=color_texto_principal,
    xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
    yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
)

# --- Ciudades Menos Mortales ---
if not mortalidad.empty and 'MUNICIPIO' in mortalidad.columns:
    muertes_ciudad_df = mortalidad.groupby('MUNICIPIO').size().reset_index(name='Total')
    menos_muertes_df = muertes_ciudad_df.sort_values(by='Total').head(10)
else:
    menos_muertes_df = pd.DataFrame({'MUNICIPIO': [], 'Total': []})
pie = px.pie(menos_muertes_df, names='MUNICIPIO', values='Total', template='plotly_dark',
             color_discrete_sequence=[color_acento_azul, color_acento_amarillo, '#007A6C', '#FF8C00', '#708090']) # Paleta para pie
pie.update_layout(
    title_text='10 ciudades con menor índice de mortalidad',
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font_color=color_texto_principal, title_font_color=color_texto_principal,
    legend_font_color=color_texto_principal
)

# --- Causas de Muerte (Tablas) ---
if not mortalidad.empty and 'COD_MUERTE' in mortalidad.columns:
    causas_df = mortalidad.groupby('COD_MUERTE').size().reset_index(name='Total')
    top_causas_principal_df = causas_df.sort_values(by='Total', ascending=False).head(10)
    top_causas_preview_df = top_causas_principal_df.head(3)
else:
    top_causas_principal_df = pd.DataFrame({'COD_MUERTE': [], 'Total': []})
    top_causas_preview_df = pd.DataFrame({'COD_MUERTE': [], 'Total': []})

table_style_dark = {
    'style_table':{'overflowX': 'auto', 'backgroundColor': color_fondo_elementos},
    'style_cell': {
        'textAlign': 'left', 'padding': '10px', 'fontFamily': 'Arial, sans-serif',
        'backgroundColor': color_fondo_elementos,
        'color': color_texto_principal,
        'border': f'1px solid {color_borde_elementos}'
    },
    'style_header': {
        'backgroundColor': color_fondo_principal,
        'fontWeight': 'bold',
        'color': color_acento_amarillo, # Cabecera con acento amarillo
        'border': f'1px solid {color_borde_elementos}'
    },
    'style_data_conditional': [
        {'if': {'row_index': 'odd'},
         'backgroundColor': '#363636'} # Un gris ligeramente diferente para filas impares
    ]
}
preview_table_style_dark = {
    'style_table':{'overflow': 'hidden', 'height': '100%', 'backgroundColor': color_fondo_elementos},
    'style_cell': {
        'textAlign': 'left', 'padding': '5px', 'fontSize': '10px', 'fontFamily': 'Arial, sans-serif',
        'whiteSpace': 'nowrap', 'overflow': 'hidden', 'textOverflow': 'ellipsis',
        'maxWidth': '70px',
        'backgroundColor': color_fondo_elementos, 'color': color_texto_principal,
        'border': f'1px solid {color_borde_elementos}'
    },
    'style_header': {
        'backgroundColor': color_fondo_principal, 'fontWeight': 'bold', 'fontSize': '11px',
        'fontFamily': 'Arial, sans-serif', 'padding': '5px',
        'color': color_acento_amarillo,
        'border': f'1px solid {color_borde_elementos}'
    },
    'style_data': {'borderBottom': f'1px solid {color_borde_elementos}'}
}

tabla_principal_causas = dash_table.DataTable(
    id='tabla-causas-principal',
    columns=[{'name': 'Código', 'id': 'COD_MUERTE'}, {'name': 'Total', 'id': 'Total'}],
    data=top_causas_principal_df.to_dict('records'),
    **table_style_dark # Aplicando estilos oscuros
)
preview_tabla_causas = dash_table.DataTable(
    id='preview-tabla-causas',
    columns=[{'name': 'Cód.', 'id': 'COD_MUERTE'}, {'name': 'Cant.', 'id': 'Total'}],
    data=top_causas_preview_df.to_dict('records'),
    **preview_table_style_dark # Aplicando estilos oscuros
)

# --- Histograma por Edad ---
if not mortalidad.empty and 'GRUPO_EDAD1' in mortalidad.columns:
    histograma = px.histogram(mortalidad, x='GRUPO_EDAD1', template='plotly_dark')
else:
    histograma = px.histogram(pd.DataFrame({'GRUPO_EDAD1':[]}), x='GRUPO_EDAD1', template='plotly_dark')
histograma.update_traces(marker_color=color_acento_azul)
histograma.update_layout(
    xaxis_title="Grupo de Edad", yaxis_title="Número de Muertes", title_text='Distribución de muertes por grupo de edad quinquenal',
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font_color=color_texto_principal, title_font_color=color_texto_principal,
    bargap=0.1,
    xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
    yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
)

# --- Muertes por Sexo y Departamento ---
if not mortalidad.empty and 'DEPARTAMENTO' in mortalidad.columns and 'SEXO' in mortalidad.columns:
    sexo_dep_df = mortalidad.groupby(['DEPARTAMENTO', 'SEXO']).size().reset_index(name='Total')
    sexo_dep_df['SEXO'] = sexo_dep_df['SEXO'].map({1: 'Hombre', 2: 'Mujer', '1':'Hombre', '2':'Mujer'}).fillna('No especificado')
else:
    sexo_dep_df = pd.DataFrame({'DEPARTAMENTO':[], 'SEXO':[], 'Total':[]})
barras_sexo = px.bar(sexo_dep_df, x='DEPARTAMENTO', y='Total', color='SEXO', template='plotly_dark',
                     color_discrete_map={'Hombre': color_acento_azul, 'Mujer': color_acento_amarillo, 'No especificado': '#777777'})
barras_sexo.update_layout(
    xaxis_title="Departamento", yaxis_title="Número de Muertes", title_text='Muertes por sexo en cada departamento',
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font_color=color_texto_principal, title_font_color=color_texto_principal,
    legend_font_color=color_texto_principal,
    xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
    yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
)


# ========== INICIALIZACIÓN ==========
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# ========== LAYOUT GENERAL  ==========

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        html.H2("Visualización Mortalidad Colombia 2019", style={'textAlign': 'center', 'color': color_acento_amarillo}) # Título con acento
    ], className='sidebar'),

    html.Div([
        # Preview Mapa
        dcc.Link([
            html.Div([
                dcc.Graph(
                    id='preview-mapa',
                    figure=mapa.update_layout(margin=dict(l=0,r=0,t=0,b=0), showlegend=False, title_text='', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'), # Fondos transparentes para preview
                    config={'displayModeBar': False},
                    style={'height': '160px', 'width': '100%'}
                ),
                html.Div("Mapa de Muertes", className='preview-title')
            ], className='preview-card-content')
        ], href='/mapa', className='preview-card-link'),

        # Preview Muertes por Mes
        dcc.Link([
            html.Div([
                dcc.Graph(
                    id='preview-mes',
                    figure=lineas.update_layout(
                        margin=dict(l=15,r=5,t=5,b=15), showlegend=False, title_text='',
                        xaxis=dict(showticklabels=False, title=None, showgrid=False, zeroline=False),
                        yaxis=dict(showticklabels=False, title=None, showgrid=False, zeroline=False),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                    ),
                    config={'displayModeBar': False}, style={'height': '160px', 'width': '100%'}
                ),
                html.Div("Muertes por Mes", className='preview-title')
            ], className='preview-card-content')
        ], href='/mes', className='preview-card-link'),

        # ... Repetir la misma lógica para las otras previews, asegurando que los update_layout
        #     para las previews quiten elementos pero mantengan el tema oscuro (fondos transparentes)

        # Preview Ciudades Violentas
        dcc.Link([
            html.Div([
                dcc.Graph(
                    id='preview-violencia',
                    figure=barras_violentas.update_layout(
                        margin=dict(l=15,r=5,t=5,b=20), showlegend=False, title_text='',
                        xaxis=dict(showticklabels=False, title=None, showgrid=False, zeroline=False, tickangle=0),
                        yaxis=dict(showticklabels=False, title=None, showgrid=False, zeroline=False),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                    ),
                    config={'displayModeBar': False}, style={'height': '160px', 'width': '100%'}
                ),
                html.Div("Ciudades Violentas", className='preview-title')
            ], className='preview-card-content')
        ], href='/violencia', className='preview-card-link'),

        # Preview Ciudades Menos Mortales
        dcc.Link([
            html.Div([
                dcc.Graph(
                    id='preview-menos',
                    figure=pie.update_layout(margin=dict(l=0,r=0,t=0,b=0), showlegend=False, title_text='', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'),
                    config={'displayModeBar': False}, style={'height': '160px', 'width': '100%'}
                ),
                html.Div("Ciudades Seguras", className='preview-title')
            ], className='preview-card-content')
        ], href='/menos', className='preview-card-link'),

        # Preview Causas de Muerte (con tabla)
        dcc.Link([
            html.Div([
                html.Div(preview_tabla_causas, style={'height': '160px', 'padding': '5px', 'boxSizing': 'border-box', 'overflow': 'hidden'}),
                html.Div("Causas de Muerte", className='preview-title')
            ], className='preview-card-content')
        ], href='/causas', className='preview-card-link'),

        # Preview Histograma por Edad
        dcc.Link([
            html.Div([
                dcc.Graph(
                    id='preview-edad',
                    figure=histograma.update_layout(
                        margin=dict(l=15,r=5,t=5,b=15), showlegend=False, title_text='', bargap=0.2,
                        xaxis=dict(showticklabels=False, title=None, showgrid=False, zeroline=False),
                        yaxis=dict(showticklabels=False, title=None, showgrid=False, zeroline=False),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                    ),
                    config={'displayModeBar': False}, style={'height': '160px', 'width': '100%'}
                ),
                html.Div("Muertes por Edad", className='preview-title')
            ], className='preview-card-content')
        ], href='/edad', className='preview-card-link'),

        # Preview Sexo y Departamento
        dcc.Link([
            html.Div([
                dcc.Graph(
                    id='preview-sexo',
                    figure=barras_sexo.update_layout(
                        margin=dict(l=15,r=5,t=5,b=15), showlegend=False, title_text='',
                        xaxis=dict(showticklabels=False, title=None, showgrid=False, zeroline=False),
                        yaxis=dict(showticklabels=False, title=None, showgrid=False, zeroline=False),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                    ),
                    config={'displayModeBar': False}, style={'height': '160px', 'width': '100%'}
                ),
                html.Div("Muertes por Sexo", className='preview-title')
            ], className='preview-card-content')
        ], href='/sexo', className='preview-card-link'),

    ], className='preview-container'),

    html.Div(id='page-content', className='content')
])


# ========== CALLBACK DE NAVEGACIÓN ==========
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    def graph_container(title_H2, graph_component_original, component_id=None, is_table=False): # Renombré 'title' a 'title_H2' para claridad
        if isinstance(graph_component_original, go.Figure):
            graph_component_fig = go.Figure(graph_component_original)
        else:
            graph_component_fig = graph_component_original

        if isinstance(graph_component_fig, go.Figure):
            graph_component_fig.update_layout(
                # ELIMINAR EL TÍTULO INTERNO DE PLOTLY PARA LA VISTA PRINCIPAL
                title_text=None, # O title=None, o simplemente no incluir esta línea
                title_x=None,    # Ya no es necesario
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color=color_texto_principal,
                legend_font_color=color_texto_secundario,
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)', title_font_color=color_texto_secundario, tickfont_color=color_texto_secundario),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title_font_color=color_texto_secundario, tickfont_color=color_texto_secundario),
            )
            # Re-establecer títulos de ejes si se borraron con el update_layout general
            # Esto depende de si los títulos de los ejes ya están en las figuras base
            # (mapa, lineas, barras_violentas, etc.)

            # Ejemplo para asegurar que los títulos de ejes se mantengan o se definan aquí:
            if component_id == 'main-mes-graph': # Asumiendo que pasas un component_id único
                 graph_component_fig.update_layout(xaxis_title="Mes", yaxis_title="Número de muertes")
            elif component_id == 'main-violencia-graph':
                 graph_component_fig.update_layout(xaxis_title="Ciudad", yaxis_title="Número de homicidios")
            # ... y así sucesivamente para otros gráficos que necesiten títulos de ejes específicos ...


            graph_component = dcc.Graph(figure=graph_component_fig, id=component_id if component_id else title_H2.replace(" ", "-").lower())
        else:
            graph_component = graph_component_fig

        return html.Div([
            # Este es el título H2 que SÍ queremos ver
            html.H2(title_H2, style={'marginBottom': '20px', 'color': color_acento_amarillo, 'fontFamily': 'Arial, sans-serif'}),
            html.Div(
                graph_component,
                className='graph-container-main',
            )
        ], className='content-container')

    base_fig_height = 550
    map_height = 650

    # Ahora, al llamar a graph_container, nos aseguramos que el update_layout dentro
    # de graph_container o el update_layout específico de cada 'if pathname =='
    # NO establezca un title_text para la figura de Plotly.

    if pathname == '/mapa':
        fig = go.Figure(mapa)
        # No establecer title_text aquí, se elimina en graph_container
        fig.update_layout(height=map_height, margin={"r":0,"t":0,"l":0,"b":0}) # Ajustar margen t si el título H2 está muy pegado
        return graph_container('1. Mapa de muertes por departamento', fig, component_id='main-mapa-graph')

    elif pathname == '/mes':
        fig = go.Figure(lineas)
        # No title_text aquí
        fig.update_layout(height=base_fig_height, xaxis_title="Mes", yaxis_title="Número de muertes", xaxis_showticklabels=True, yaxis_showticklabels=True)
        return graph_container('2. Total de muertes por mes', fig, component_id='main-mes-graph')

    elif pathname == '/violencia':
        fig = go.Figure(barras_violentas)
        # No title_text aquí
        fig.update_layout(height=base_fig_height, xaxis_title="Ciudad", yaxis_title="Número de homicidios", xaxis_showticklabels=True, yaxis_showticklabels=True, xaxis_tickangle=-45)
        return graph_container('3. 5 ciudades más violentas (homicidios)', fig, component_id='main-violencia-graph')

    elif pathname == '/menos':
        fig = go.Figure(pie)
        # No title_text aquí
        fig.update_layout(height=base_fig_height, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
        return graph_container('4. 10 ciudades con menor mortalidad', fig, component_id='main-menos-graph')

    elif pathname == '/causas':
        # Las tablas no tienen un 'title_text' de Plotly, así que esto está bien.
        return graph_container('5. Top 10 causas de muerte', tabla_principal_causas, is_table=True)

    elif pathname == '/edad':
        fig = go.Figure(histograma)
        # No title_text aquí
        fig.update_layout(height=base_fig_height, xaxis_title="Grupo de Edad", yaxis_title="Número de muertes", xaxis_showticklabels=True, yaxis_showticklabels=True, bargap=0.1)
        return graph_container('6. Histograma de muertes por edad', fig, component_id='main-edad-graph')

    elif pathname == '/sexo':
        fig = go.Figure(barras_sexo)
        # No title_text aquí
        fig.update_layout(height=base_fig_height, xaxis_title="Departamento", yaxis_title="Número de muertes", xaxis_showticklabels=True, yaxis_showticklabels=True, xaxis_tickangle=-45, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
        return graph_container('7. Muertes por sexo en cada departamento', fig, component_id='main-sexo-graph')

    else: # Página de bienvenida
        return html.Div([
            html.H1("Análisis de Mortalidad en Colombia 2019", style={'textAlign': 'center', 'marginTop': '100px', 'color': color_acento_amarillo, 'fontFamily': 'Arial, sans-serif'}),
            html.P("Seleccione una visualización del menú superior o haga clic en cualquiera de las miniaturas arriba.", style={'textAlign': 'center', 'color': color_texto_principal, 'fontSize': '18px', 'fontFamily': 'Arial, sans-serif'})
        ], className='welcome-container', style={'padding': '20px'})


# ========== EJECUCIÓN ==========
if __name__ == '__main__':
    app.run(debug=True)