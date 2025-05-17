import dash
from dash import dcc, html, dash_table
import pandas as pd
import plotly.express as px
import json

# Cargar los datos
mortalidad = pd.read_excel('data/Anexo1.NoFetal2019_CE_15-03-23.xlsx', sheet_name='No_Fetales_2019')
codigos = pd.read_excel('data/Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx', sheet_name=None)
divipola = pd.read_excel('data/Anexo3.Divipola_CE_15-03-23.xlsx')

# ================== MAPA POR DEPARTAMENTO (con código) ====================

# Cargar GeoJSON
with open('data/departamentos.geojson', encoding='utf-8') as f:
    geojson_departamentos = json.load(f)

# Verificar que los datos de mortalidad tengan el formato correcto
print(mortalidad['COD_DEPARTAMENTO'].head())

# Rellenar códigos con ceros a la izquierda para que tengan dos dígitos
mortalidad['COD_DEPARTAMENTO'] = mortalidad['COD_DEPARTAMENTO'].astype(str).str.zfill(2)

# Agrupar por código de departamento
dep_muertes = mortalidad.groupby('COD_DEPARTAMENTO').size().reset_index(name='Total_Muertes')

# Extraer códigos del GeoJSON
geo_departamentos = pd.DataFrame([
    {
        'DPTO_CCDGO': feature['properties']['DPTO_CCDGO'],
        'DPTO_CNMBR': feature['properties']['DPTO_CNMBR']
    }
    for feature in geojson_departamentos['features']
])

# Verificar los códigos en el GeoJSON
print(geo_departamentos['DPTO_CCDGO'].unique())

# Hacer el merge asegurando que los tipos de datos coincidan
df_mapa = geo_departamentos.merge(
    dep_muertes,
    left_on='DPTO_CCDGO',
    right_on='COD_DEPARTAMENTO',
    how='left'
)

# Rellenar NA con 0 y convertir a entero
df_mapa['Total_Muertes'] = df_mapa['Total_Muertes'].fillna(0).astype(int)

# Verificar el dataframe resultante
print(df_mapa.head())

# Crear el mapa
mapa = px.choropleth(
    df_mapa,
    geojson=geojson_departamentos,
    locations='DPTO_CCDGO',
    featureidkey='properties.DPTO_CCDGO',
    color='Total_Muertes',
    color_continuous_scale='Reds',
    range_color=(0, df_mapa['Total_Muertes'].max()),
    labels={'Total_Muertes': 'Total de Muertes'},
    hover_name='DPTO_CNMBR',
    hover_data={'DPTO_CCDGO': False, 'Total_Muertes': True}
)
mapa.update_geos(fitbounds="locations", visible=False)

# =============== RESTO DE GRÁFICOS CON DIVIPOLA ===============

# Cruzar para obtener MUNICIPIO y DEPARTAMENTO (nombre)
mortalidad = mortalidad.merge(divipola[['COD_DANE', 'MUNICIPIO', 'DEPARTAMENTO']], on='COD_DANE', how='left')

# Gráfico 2: Muertes por mes
muertes_mes = mortalidad.groupby('MES').size().reset_index(name='Muertes')
lineas = px.line(muertes_mes, x='MES', y='Muertes', markers=True,
                 title='Total de muertes por mes en 2019')

# Gráfico 3: 5 ciudades más violentas (códigos X95)
homicidios = mortalidad[mortalidad['COD_MUERTE'].str.startswith('X95', na=False)]
violentas = homicidios.groupby('MUNICIPIO').size().reset_index(name='Homicidios')
top_5 = violentas.sort_values(by='Homicidios', ascending=False).head(5)
barras_violentas = px.bar(top_5, x='MUNICIPIO', y='Homicidios',
                          title='5 ciudades más violentas (Homicidios)')

# Gráfico 4: Circular 10 ciudades con menor mortalidad
muertes_ciudad = mortalidad.groupby('MUNICIPIO').size().reset_index(name='Total')
menos_muertes = muertes_ciudad.sort_values(by='Total').head(10)
pie = px.pie(menos_muertes, names='MUNICIPIO', values='Total',
             title='10 ciudades con menor índice de mortalidad')

# Tabla: Top 10 causas de muerte
causas = mortalidad.groupby('COD_MUERTE').size().reset_index(name='Total')
top_causas = causas.sort_values(by='Total', ascending=False).head(10)
tabla = dash_table.DataTable(
    columns=[
        {'name': 'Código', 'id': 'COD_MUERTE'},
        {'name': 'Total', 'id': 'Total'}
    ],
    data=top_causas.to_dict('records'),
    style_table={'overflowX': 'auto'},
    style_cell={'textAlign': 'left'},
)

# Histograma: Muertes por grupo de edad
histograma = px.histogram(mortalidad, x='GRUPO_EDAD1',
                          title='Distribución de muertes por grupo de edad quinquenal')

# Barras apiladas: Muertes por sexo por departamento
sexo_dep = mortalidad.groupby(['DEPARTAMENTO', 'SEXO']).size().reset_index(name='Total')
sexo_dep['SEXO'] = sexo_dep['SEXO'].map({1: 'Hombre', 2: 'Mujer'})
barras_sexo = px.bar(sexo_dep, x='DEPARTAMENTO', y='Total', color='SEXO',
                     title='Muertes por sexo en cada departamento')

# ==================== Dash Layout ====================
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1('Análisis de Mortalidad en Colombia - 2019'),

    html.H2('1. Mapa de muertes por departamento'),
    dcc.Graph(figure=mapa),

    html.H2('2. Total de muertes por mes'),
    dcc.Graph(figure=lineas),

    html.H2('3. 5 ciudades más violentas (homicidios)'),
    dcc.Graph(figure=barras_violentas),

    html.H2('4. 10 ciudades con menor mortalidad'),
    dcc.Graph(figure=pie),

    html.H2('5. Top 10 causas de muerte'),
    tabla,

    html.H2('6. Histograma de muertes por edad'),
    dcc.Graph(figure=histograma),

    html.H2('7. Muertes por sexo en cada departamento'),
    dcc.Graph(figure=barras_sexo),
])

server = app.server
# Ejecutar la app localmente

if __name__ == '__main__':
    app.run(debug=False, port=8050)
