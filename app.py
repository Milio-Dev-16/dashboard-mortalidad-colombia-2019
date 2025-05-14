import dash
from dash import dcc, html, dash_table
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Cargar los datos desde los archivos Excel
mortalidad = pd.read_excel('data/Anexo1.NoFetal2019_CE_15-03-23.xlsx', sheet_name='No_Fetales_2019')
codigos = pd.read_excel('data/Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx', sheet_name=None)
divipola = pd.read_excel('data/Anexo3.Divipola_CE_15-03-23.xlsx')

# Limpiar y unir datos con nombres de departamentos y municipios
mortalidad = mortalidad.merge(divipola[['COD_DANE', 'DEPARTAMENTO', 'MUNICIPIO']], on='COD_DANE', how='left')

# Gráfico 1: Mapa de muertes por departamento
dep_muertes = mortalidad.groupby('DEPARTAMENTO').size().reset_index(name='Total_Muertes')
mapa = px.choropleth(dep_muertes,
                     locations='DEPARTAMENTO',
                     locationmode='country names',
                     color='Total_Muertes',
                     title='Distribución de muertes por departamento (2019)',
                     color_continuous_scale='Reds')

# Gráfico 2: Líneas de muertes por mes
muertes_mes = mortalidad.groupby('MES').size().reset_index(name='Muertes')
lineas = px.line(muertes_mes, x='MES', y='Muertes', markers=True,
                 title='Total de muertes por mes en 2019')

# Gráfico 3: Barras de ciudades más violentas (códigos X95)
homicidios = mortalidad[mortalidad['COD_MUERTE'].str.startswith('X95', na=False)]
violentas = homicidios.groupby('MUNICIPIO').size().reset_index(name='Homicidios')
top_5 = violentas.sort_values(by='Homicidios', ascending=False).head(5)
barras_violentas = px.bar(top_5, x='MUNICIPIO', y='Homicidios',
                          title='5 ciudades más violentas (Homicidios)')

# Gráfico 4: Circular de las 10 ciudades con menor mortalidad
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

# Inicializar la aplicación Dash
app = dash.Dash(__name__)

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
    app.run_server(debug=True, port=8050)  # Cambia debug=False en producción
