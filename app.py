import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import re  # regex lib
from datetime import date, timedelta, datetime  # date lib
import numpy as np

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}
# ----------------------------------------------------------------------------------------------------------------------
# TODO:
#  Reproduktionszahl / TAG LiDiaG x
#  # täglicher Infektionen LiDiaG x
#  # der aktiven Fälle / Bundesland Barchart x
#  Geschlechtsverteilung Piechart x
#  Belegung Intensiv- und Normalbetten in % Barchart x
#  Epidemiologische Kurve (Genesene, Tote, Gesamterkrankte LiDiaG x
#  Altersverteilung vs. Todesfälle Barchart horizontal x
#  Kartendarstellung der Infektionszahlen Chropleth x
# ----------------------------------------------------------------------------------------------------------------------
# reading data into data Frame using pandas

dfRepo = pd.read_csv('https://www.ages.at/fileadmin/AGES2015/Wissen-Aktuell/COVID19/R_eff.csv', sep=';')
dfTaeInf = pd.read_csv('https://info.gesundheitsministerium.at/data/Epikurve.csv', sep=';')
dfAktivBndsld = pd.read_csv('https://covid19-dashboard.ages.at/data/CovidFaelle_Timeline.csv', sep=';')
dfSex = pd.read_csv('https://info.gesundheitsministerium.at/data/Geschlechtsverteilung.csv', sep=';')
dfAuslastung = pd.read_csv('https://info.gesundheitsministerium.at/data/IBAuslastung.csv', sep = ';')
dfNormal = pd.read_csv('https://info.gesundheitsministerium.at/data/NBAuslastung.csv', sep = ';')
dfEpiKur = pd.read_csv('https://covid19-dashboard.ages.at/data/CovidFaelle_Timeline.csv', sep=';')
dfGeneSum = pd.read_csv('https://info.gesundheitsministerium.at/data/GenesenTimeline.csv', sep=';')
dfTotSum = pd.read_csv('https://info.gesundheitsministerium.at/data/TodesfaelleTimeline.csv', sep=';')
dfAge = pd.read_csv('https://info.gesundheitsministerium.at/data/Altersverteilung.csv', sep=';')
dfAgeDeaths = pd.read_csv('https://info.gesundheitsministerium.at/data/AltersverteilungTodesfaelle.csv', sep=';')
dfGKZ = pd.read_csv('https://covid19-dashboard.ages.at/data/CovidFaelle_GKZ.csv', sep = ";")

# ----------------------------------------------------------------------------------------------------------------------
# cleaning data

# Reproduktionszahlen DF
repoString = ['R_eff', 'R_eff_lwr', 'R_eff_upr']
for i in range(len(repoString)):
    dfRepo[repoString[i]] = dfRepo[repoString[i]].str.replace(',', '.')
    dfRepo[repoString[i]] = dfRepo[repoString[i]].astype(float)
dfRepoMelt = dfRepo.melt(id_vars='Datum', value_vars=repoString)

# Aktive letzten 7 tage DF
id = []
for i in range (9):
  id.append(dfAktivBndsld.shape[0]-10+i)
dfAktivBndsld = dfAktivBndsld.iloc[id]

# Auslastung Betten
dfAuslastung.columns = dfAuslastung.columns.str.replace('Timestamp','Belegung Normalbetten in %')
dfAuslastung['Belegung Normalbetten in %'] = dfNormal['Belegung Normalbetten in %']
bettenString = ['Belegung Normalbetten in %', 'Belegung Intensivbetten in %']
for i in range(len(bettenString)):
    dfAuslastung[bettenString[i]] = dfAuslastung[bettenString[i]].str.replace(',', '.')
    dfAuslastung[bettenString[i]] = dfAuslastung[bettenString[i]].astype(float)

#EpiKurve
dfEpiKur = dfEpiKur[dfEpiKur.BundeslandID == 10]
dfEpiKur.drop(dfEpiKur.columns.difference(['Time','AnzahlFaelleSum']), 1, inplace=True)
dfEpiKur = dfEpiKur.reset_index(drop=True)
dfEpiKur['Genesen'] = dfGeneSum['Genesen']
dfEpiKur['Todesfaelle'] = dfTotSum['Todesfälle']
dfEpiKurMelted=pd.melt(dfEpiKur, id_vars=['Time'], value_vars=['AnzahlFaelleSum', 'Todesfaelle', 'Genesen'])

#Erkrankte vs Tode
dfAge['Timestamp'] = dfAgeDeaths['Anzahl']
dfAge.columns = dfAge.columns.str.replace('Timestamp','Tode')
dfAge.columns = dfAge.columns.str.replace('Anzahl','Erkrankte')

#Map 
dfGKZ.columns = dfGKZ.columns.str.replace('Anzahl','Anzahl Neuinfektionen')
dfGKZ['Anzahl logarithmisch'] = np.log10(dfGKZ['Anzahl Neuinfektionen'])
austria_districts = json.load(open('bezirke_999_.geojson', 'r'))
for feature in austria_districts['features']:
    feature['id'] = feature['properties']['iso']

# ----------------------------------------------------------------------------------------------------------------------
# df to figures

# Reproduktionszahlen FIG
figRepo = px.line(dfRepoMelt, x='Datum', y='value', title='Reproduktionszahlen', color='variable')
figRepo.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)

# TäglicheInfektionen FIG
#figTaeInf = px.line(dfTaeInf, x='time', y='tägliche Erkrankungen', title='Tägliche Neuinfektionen')
figTaeInf =go.Figure()
figTaeInf.add_trace(go.Scatter(
                    x=dfTaeInf['time'], 
                    y=dfTaeInf['tägliche Erkrankungen'],
                    mode='lines+markers',
                    name='lines+markers',
                    line_color= '#fcad00',
                    )
)
figTaeInf.update_layout(
    title = 'Tägliche Neuinfektionen',
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)

# Anzahl 7 Tagen Bundesland FIG
# Keine Daten zu den aktuellen Fällen
figAktivBndsld = px.bar(dfAktivBndsld, x='Bundesland', y='AnzahlFaelle7Tage',title='Anzahl der in den letzten 7 Tagen Erkrankten pro Bundesland')
figAktivBndsld.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text'],
)
figAktivBndsld.update_traces(marker_color='#fcad00')

# Geschlächtsverteilung FIG
figSex = px.pie(dfSex, 
                values = 'Anzahl in %', 
                names = 'Geschlecht', title='Geschlechtsverteilung',
                color = 'Geschlecht',
                color_discrete_map={
                                    'weiblich':'red',
                                    'männlich':'royalblue'
                }
)
figSex.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)

# Auslasutung Intensiv und Normalbetten
figAuslastung = go.Figure()
figAuslastung.add_trace(go.Bar(
    x=dfAuslastung['time'],
    y=dfAuslastung['Belegung Normalbetten in %'],
    name='Belegung Normalbetten in %',
    marker_color='lightsalmon'#indianred
    )
)
figAuslastung.add_trace(go.Bar(
    x=dfAuslastung['time'],
    y=dfAuslastung['Belegung Intensivbetten in %'],
    name='Belegung Intensivbetten in %',
    marker_color='red'
    )
)
figAuslastung.update_layout(
    title = 'Auslasutung der Intensiv und Normalbetten in %',
    barmode='group', 
    xaxis_tickangle=-45,
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)
#Epikurve

figEpi =  px.line(dfEpiKurMelted, x='Time', y='value', color='variable', title = 'Epidemiologische Kurve')
figEpi.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)
#Erkrankte vs Tote
figAge = go.Figure()
figAge.add_trace(go.Bar(
    y=dfAge['Altersgruppe'],
    x=dfAge['Erkrankte'],
    name='Erkrankte',
    marker_color='green',
    orientation='h'
    )
)
figAge.add_trace(go.Bar(
    y=dfAge['Altersgruppe'],
    x=dfAge['Tode'],
    name='Tode',
    marker_color='indianred',
    orientation='h'
    )
)

figAge.update_layout(
    title = 'ALtersverteilung Erkrankte - Todesfälle',
    barmode='group', 
    xaxis_tickangle=-45,
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)

#Map
figMap = px.choropleth_mapbox(
    dfGKZ,
    locations='GKZ',
    geojson=austria_districts,
    color='Anzahl logarithmisch',
    hover_name='Bezirk',
    #locationmode='Austria',
    hover_data=['Anzahl Neuinfektionen'],
    labels='Anzahl Fälle',
    mapbox_style="carto-positron",
    center={'lat':47.70,'lon':13.65},
    zoom=5.6,
    opacity = 0.8,
    title = 'Anzahl Neuinfektionen in Bezriken',
)
figMap.update_geos(fitbounds='locations', visible = False)
figMap.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)
# ----------------------------------------------------------------------------------------------------------------------
# App Layout

today = date.today() - timedelta(days=0)
dateformat = today.strftime("%d/%m/%Y")
nums = [int(n) for n in dateformat.split("/")]


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[

    #html.H1("Covid Dashboard by Vinzenz Wratschko", style={'backgroundColor': colors['background']}),
    html.H1(
        children='COVID 19 Dashboard by Vinzenz Wratschko',
        style={
            'textAlign': 'center',
            'color': colors['text']
        }
    ),

    dcc.Graph(id='RepoGraph', figure=figRepo),
    dcc.Graph(id='TaeInfGraph', figure=figTaeInf),
    dcc.Graph(id='AktvBndslndGraph', figure=figAktivBndsld),
    dcc.Graph(id='SexGraph', figure=figSex),
    dcc.Graph(id='AuslastungGraph', figure=figAuslastung),
    dcc.Graph(id='EpikurveGraph', figure=figEpi),
    dcc.Graph(id='AgeGraph', figure=figAge),
    dcc.Graph(id='austrian_map', figure=figMap),
])

# ----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
