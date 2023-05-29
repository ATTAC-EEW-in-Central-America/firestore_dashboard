import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, Input, Output, State
from dash import html
import plotly.express as px
import plotly.figure_factory as ff
import plotly.express as px
import dash
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
import pandas as pd
import plotly.graph_objects as go
import datamanager, readfdsn, util
import logging as Log
import time, math
import datetime
from dash.exceptions import PreventUpdate
import statistics 
import numpy as np
##Imports for fdsnws retrieve data through pd.read_csv()
TIMEOUT_SEC = 10 # default timeout in seconds
import socket
socket.setdefaulttimeout(TIMEOUT_SEC)


# the class Data is for saving the configuration 
# and load the data stored in csv files.
# This also has some methods to update the csv data from Firebase Firestore DB.
# 
# Be sure not calling the refreshData() method many times.
#
class Data:
    def __init__(self):
        self.config = None
        self.datahandler = None
        self.dfEventsDelay = None
        self.dfSilentNotif = None
        self.dfAlertsIntensity = None
        self.cities = None
    def loadConfigData(self):
        try:
            #Reading the configuration values, using the datahandler to read the data from csv files.
            self.config = datamanager.config("dashconfig.cfg")
            self.config.readConfig()
            self.datahandler = datamanager.datahandler(self.config)
            self.dfEventsDelay = self.datahandler.getDfDelaysEvents()
            self.dfSilentNotif = self.datahandler.getDfSilentNotif()
            self.dfAlertsIntensity = self.datahandler.getDfIntensityAlerts()
            self.cities = util.csvFile2dic(self.config.citiesFile)
        except Exception as e:
            Log.error("Problem instancing and/or getting the data in dataframes")
            Log.error(repr(e))
    def refreshData(self):
        #This method should not be called many times to avoid to reach 
        #the max read quota on Firebase Firestore DB.
        #
        self.datahandler.getDataFirebaseForEvents()
        self.datahandler.getDataFirebaseForSilentNotif()


#instancing Data class
fdc = Data()
fdc.loadConfigData()

romanNumbersArr=["I", "II", "III", "IV","V","VI","VII","VIII","IX","X", "XI","XII"]
mapbox_access_token = open(".mapbox_token").read()    

#Initialise the app
dbc_css = (
    "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.1/dbc.min.css"
)

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

search_bar = dbc.Row(
    [
        dbc.Col(dbc.Input(id="eventid-input",type="search", placeholder="ID del evento...")),
        dbc.Col(
            dbc.Button("Buscar",id="eventid-button",
                color="primary", className="ms-2", n_clicks=0
            ),
            width="auto",
        ),
        dbc.Col(
            dbc.Button("Actualizar",id="buttonUpdate",
                color="success", className="ms-2", n_clicks=0
            ),
            width="auto",
        ),
    ],
    className="g-0 ms-auto flex-nowrap mt-3 mt-md-0",
    align="center",
)


navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src = app.get_asset_url(fdc.config.logoFile), height="100px")),
                        dbc.Col(dbc.NavbarBrand("Dashboard de Datos en Firebase", className="ms-2")),
                    ],
                    align="center",
                    className="g-0",
                ),
                href="/",
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                search_bar,
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ]
    ),
    color="dark",
    dark=True,
)

    
modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Modal Title")),
        dbc.ModalBody("This is the content of the modal"),
    ],
    id="modal",
    is_open=False,
)

modal = dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("ID de Evento No Encontrado")),
                        dbc.ModalBody("Por favor, verifique que el ID sea de un evento que fue notificado a través de la App."),
                    ],
                    id="modal-noevent",
                    is_open=False,
                )
                
                
#define the app
app.layout = dbc.Container(
    [
        dcc.Location(id='url', refresh=True),
        navbar,
        html.Br(),
        dcc.Interval(
            id="load_interval", 
            n_intervals=0, 
            max_intervals=0, #<-- only run once
            interval=1
        ),
        dbc.Tabs(
          [
            
            dbc.Tab([
                html.Br(),
                dbc.Row(id="resumenTab1",justify="center"),
                html.Br(),
                html.Hr(),
                dbc.Row(
                    [
                    dbc.Col([dcc.Graph(id="map-users")],md=5,className="shadow  bg-white rounded"),
                    dbc.Col([dcc.Graph(id="hist-time-source")],md=5, className="shadow  bg-white rounded"),       
                    ],className="d-flex justify-content-center"
                ),
                html.Hr(),
                dbc.Row(
                    [
                    dbc.Col([dcc.Graph(id="map-user-delays")],md=5,className="shadow  bg-white rounded"),
                    dbc.Col([dcc.Graph(id="plot-users-vs-time")],md=5,className="shadow  bg-white rounded"),
                    ],className="d-flex justify-content-center"
                ),
                html.Hr(),
                dbc.Row(
                    [
                    dbc.Col([
                        dcc.Graph(id='distr-events-delays'),
                        dbc.Row([
                            #dbc.Col([dcc.Graph(id='pie-first-notif-delays')],md=6),
                            dbc.Col([dbc.Spinner(children=[dcc.Graph(id="pie-first-notif-delays")], size="lg", color="primary", type="border", fullscreen=True,)], md=6),
                            dbc.Col([dcc.Graph(id='pie-updates-notif-delays')],md=6)
                        ])
                    ],md=6, className="shadow rounded"),
                    dbc.Col([
                        dcc.Graph(id='distr-silent-notif-delays'),
                        dbc.Row([
                            dbc.Col([dcc.Graph(id='pie-silent-notif-delays')], md=8)
                        ], className="d-flex justify-content-center")
                    ],md=6,className="shadow rounded"),
                    ]
                )
            ],label="Datos De Tiempo"),
            dbc.Tab(
            [   
                modal,
                html.Br(),
                dbc.Row(id="resumenTab2",justify="center"),
                html.Br(),
                dbc.Row(
                [
                    dbc.Col([dcc.Graph(id="intensity-map")], md=5),
                    dbc.Col([dcc.Graph(id="intensity-distance")],md=5)
                ], className="d-flex justify-content-center"),
                dbc.Row(
                [
                    dbc.Col([dbc.Spinner(children=[dcc.Graph(id="delay-distribution-event")], size="lg", color="primary", type="border", fullscreen=True,)], md=6),
                    dbc.Col([dcc.Graph(id="notification-histogram")],md=6)
                ])
            ],label="Datos por Evento"
            ),
        ],id="tabs", 
        
        ),
        html.Footer(
        html.Div([
        html.Small(['Alerta Temprana de Terremotos de América Central (ATTAC)'], className = "fw-bold"),
        html.Br(),
        html.Small('Una Colaboración con socios regionales en América Central, coordinado por El Servicio Sismológico de Suizo en ETH Zurich, Suiza.'),
        html.Br(),
        html.Small('Proyecto ATTAC financiado por la Agencia Suiza para el Desarrollo y Cooperación (COSUDE)'),
        html.Br(),
        html.Small('Dashboard Desarrollado por Billy Burgoa Rosso (Consultor Independiente) para el proyecto ATTAC.'),
        ]),
        className="bg-gray text-inverse text-center py-4",
        ),
        # dcc.Store stores the intermediate value
        dcc.Store(id='eventid')
        
    ],
    className=" dbc",
    fluid=True,
)

####Callbacks for first tab plots and graphs############

#multiple output callback
@app.callback(
    Output('map-users','figure'),
    Output('plot-users-vs-time','figure'),
    Output('hist-time-source','figure'),
    Output('map-user-delays','figure'),
    Output('distr-events-delays','figure'),
    Output('pie-first-notif-delays','figure'),
    Output('pie-updates-notif-delays','figure'),
    Output('distr-silent-notif-delays','figure'),
    Output('pie-silent-notif-delays','figure'),
    Output('resumenTab1','children'),
    Output("eventid","data"),
    Input("load_interval", "n_intervals"),
)
def updatePlotsGraphsFirstTab(n_intervals):

    fdc = Data()
    fdc.loadConfigData()
    colorMapDicPie = { "-0.5 to 0 s": "gray",
                    "0 to 1 s": "#00CC96",
                    "1 to 2 s": "#FFA15A",
                    "2 to 3 s": "#19D3F3",
                    "3 to 4 s": "#636EFA",
                    "4 to 5 s": "#EF553B",
                    "5 to 60 s": "#AB63FA"}
    
    lastSNtimestamp = fdc.dfSilentNotif["senttime"].max()
    
    dfMapPlot = fdc.dfSilentNotif.loc[(fdc.dfSilentNotif['delay']>-60)&(fdc.dfSilentNotif['delay']<=60)&(fdc.dfSilentNotif['userLat']>=-90)&(fdc.dfSilentNotif['userLat']<=90)&(fdc.dfSilentNotif["senttime"]==fdc.dfSilentNotif["senttime"].max())]
    dfMapPlot["isotime"] =  pd.to_datetime(dfMapPlot['userLocTime'], unit='ms')
    
    now = round(time.time()*1000.0)
    last24Hoursms = round(24*60*60*1000)
    last7Daysms = round(7*24*60*60*1000)
    last15Daysms = round(15*24*60*60*1000)
    fithteenMin = round(15*60*1000)
    lastHour = round(1*60*60*1000)
    today = round(1*24*260*60*1000)
    
   
    dfMapPlot['color']=''
    
    for index, row in dfMapPlot.iterrows():
        timediff =  lastSNtimestamp - round(row['userLocTime'])
        
        if timediff>=0 and timediff < fithteenMin:
            #print("last 24 hours")
            dfMapPlot['color'][index] = '< 15 minutes'
        elif timediff < lastHour and timediff >= fithteenMin:
            #print("last 7 days ")
            dfMapPlot['color'][index] = '>=15 min but < one hour'
        elif timediff < today and timediff >= lastHour:
            #print("last 15 days")
            dfMapPlot['color'][index] = '>= last hour but < 24 hours'
        else:
            #print("more than 15 days")
            dfMapPlot['color'][index] = '>= 24 hours'
            
    mapbox_access_token = open(".mapbox_token").read()
    
    px.set_mapbox_access_token(open(".mapbox_token").read())
    map_users = px.scatter_mapbox(dfMapPlot,
                        lat=dfMapPlot['userLat'],
                        lon=dfMapPlot['userLon'],
                        color=dfMapPlot['color'],
                        color_discrete_map={
                        "< 15 minutes": "green",
                        ">=15 min but < one hour": "yellow",
                        ">= last hour but < 24 hours": "orange",
                        ">= 24 hours": "gray"},
                        hover_name="isotime",
                       #color=dfMapPlot['color'],   
                       # color_discrete_map="identity",                      
                        zoom=1)
    
    map_users.update_layout(
    legend=dict(
        x=0,
        y=1,
        #traceorder="reversed",
        title_font_family="Times New Roman",
        font=dict(
            family="Courier",
            size=12,
            color="black"
        ),
        bgcolor="LightSteelBlue",
        bordercolor="Black",
        borderwidth=2
    )
    )
    map_users.update_layout(legend_x=0, legend_y=1)

    map_users.update_layout(margin={"r":20,"t":40,"l":20,"b":10})
    #map_users.update_layout(coloraxis_showscale=False)
    #map_users.update_coloraxes(showscale=False)
    #map_users.update_traces(showlegend=False)
    
    tmp = fdc.config.countrylatlon.split(",")
    
    countryLat = float(tmp[0])
    countryLon = float(tmp[1])
    map_users.update_layout(
    mapbox=dict(
        bearing=0,
        center=go.layout.mapbox.Center(
            lat=countryLat,
            lon=countryLon
        ),
        pitch=0,
        zoom=8
    )
    )
    map_users.update_layout(title = "Geographical Users' Distrubution and GPS Avalability",
    legend_title="Users' GPS Availability")
    
    
    ###Number of Users Vs Time ####
    tmpList = list(fdc.dfSilentNotif['senttime'].unique())
    dictt = {'numusers':[],
        'time': []}
    for i in tmpList:
        dictt['time'].append(i)
        dictt['numusers'].append(fdc.dfSilentNotif.loc[fdc.dfSilentNotif['senttime'] == i ]['userid'].count())
    dfTmp = pd.DataFrame(dictt)
    dfTmp["dt"] = pd.to_datetime(dfTmp['time'], unit='ms')
   
    plot_users_vs_time = px.scatter(dfTmp, x="dt", y="numusers",hover_data=['dt'],
                                    labels={
                                        "dt": "Date and Time",
                                        "numusers": "Users number",
                                    },
                                    title = 'Total Users Vs Time')
    plot_users_vs_time.update_layout({"plot_bgcolor": "rgb(240, 240, 240)"})
   
    
    ##USER TIME SOURCE Histogram ###
    timeSource=['< 15 minutes', '>=15 min but < one hour', '>= last hour but < 24 hours', '>= 24 hours']
    values = [  dfMapPlot.loc[dfMapPlot['color']=='< 15 minutes']['color'].count(),
                dfMapPlot.loc[dfMapPlot['color']=='>=15 min but < one hour']['color'].count(),
                dfMapPlot.loc[dfMapPlot['color']=='>= last hour but < 24 hours']['color'].count(),
                dfMapPlot.loc[dfMapPlot['color']=='>= 24 hours']['color'].count()
             ]
    colors = ["green","yellow","orange", "gray"]

    hist_time_source = go.Figure([go.Bar(x=timeSource, y=values)])
    
    hist_time_source = px.histogram( x=timeSource, y=values, color=colors,
                        color_discrete_map="identity",labels={
                                        "x": "Time Range",
                                        "y": "Users",
                                    })
    hist_time_source.update_layout(title = "Users' GPS Availability")
    hist_time_source.update_layout({"plot_bgcolor": "rgb(240, 240, 240)"})
    
    ## Users' GPS availability vs Time ##
    dfGPStime = pd.DataFrame(columns=['senttime','< 15 minutes','>=15 min but < one hour','>= last hour but < 24 hours','>= 24 hours'])
    #getting a series of unique 'senttime' values
    dfSilentSenttime = fdc.dfSilentNotif.sort_values(by='senttime', ascending=True)['senttime'].unique()

    for svalue in dfSilentSenttime:
        fval = sval = tval = fval = 0
        fval = fdc.dfSilentNotif[(fdc.dfSilentNotif["senttime"]==svalue)&(fdc.dfSilentNotif["senttime"] - fdc.dfSilentNotif["userLocTime"] < fithteenMin)]['userLocTime'].count()#&(not math.isnan(fdc.dfSilentNotif["userLat"]))&(fdc.dfSilentNotif["userLat"]!=0.0)]["userLocTime"].count()
        sval = fdc.dfSilentNotif[(fdc.dfSilentNotif["senttime"]==svalue)&(fdc.dfSilentNotif["senttime"] - fdc.dfSilentNotif["userLocTime"] >= fithteenMin)&(fdc.dfSilentNotif["senttime"] - fdc.dfSilentNotif["userLocTime"] < lastHour)]['userLocTime'].count()
        tval = fdc.dfSilentNotif[(fdc.dfSilentNotif["senttime"]==svalue)&(fdc.dfSilentNotif["senttime"] - fdc.dfSilentNotif["userLocTime"] >= lastHour)&(fdc.dfSilentNotif["senttime"] - fdc.dfSilentNotif["userLocTime"] < today)]['userLocTime'].count()
        foval = fdc.dfSilentNotif[(fdc.dfSilentNotif["senttime"]==svalue)&(fdc.dfSilentNotif["senttime"] - fdc.dfSilentNotif["userLocTime"] >= today)]['userLocTime'].count()
        dfGPStime = pd.concat([pd.DataFrame([[svalue,fval,sval,tval,foval]], columns=dfGPStime.columns), dfGPStime], ignore_index=True)
    
    #Some plot as a function of time but not presented on dashboard.
    #############dfGPStime["dt"] = pd.to_datetime(dfGPStime['senttime'], unit='ms')
    #############fig = go.Figure(data=[
    #############go.Bar(name='>= 24 hours', x=dfGPStime['dt'], y=dfGPStime['>= 24 hours'],width=8*60*60*1000, marker_color='gray'),
    #############go.Bar(name='>= last hour but < 24 hours', x=dfGPStime['dt'], y=dfGPStime['>= last hour but < 24 hours'],width=8*60*60*1000, marker_color='orange'),
    #############go.Bar(name='>=15 min but < one hour', x=dfGPStime['dt'], y=dfGPStime['>=15 min but < one hour'],width=8*60*60*1000, marker_color='yellow'),
    #############go.Bar(name='< 15 minutes', x=dfGPStime['dt'], y=dfGPStime['< 15 minutes'],width=8*60*60*1000, marker_color='green')])
    ############## Change the bar mode
    #############fig.update_layout(barmode='stack')
    ##############fig.show()
    
    ###Mode Value vs Time ###
    #############dfModeSilent = pd.DataFrame(columns=['senttime','mode'])
    #############for svalue in dfSilentSenttime:
    #############    tmpDf = fdc.dfSilentNotif[(fdc.dfSilentNotif["senttime"]==svalue)]
    #############    modeVal = 0
    #############    if tmpDf.size > 0:
    #############        p80 = np.percentile(tmpDf['delay'], 80)
    #############        df80=tmpDf[tmpDf['delay']<=p80]['delay']
    #############        modeVal = df80.mode() 
    #############        #if modeVal < 0:
    #############        #    print(df80)
    #############    dfModeSilent = pd.concat([pd.DataFrame([[svalue,modeVal]], columns=dfModeSilent.columns), dfModeSilent], ignore_index=True)
    #############
    #############dfModeSilent["dt"] = pd.to_datetime(dfModeSilent['senttime'], unit='ms')
    #############fig = px.line(dfModeSilent, x='dt', y='mode', markers=True)
    #############fig.show()
    
    
    #RESUME CARD
    totalUsers = fdc.dfSilentNotif.loc[fdc.dfSilentNotif['senttime']==lastSNtimestamp]['userid'].count()
    dtObj = datetime.datetime.fromtimestamp(lastSNtimestamp/1000.0)
    
    cardTotalUsers = [
    dbc.CardHeader("Usuarios Disponibles", className="card-title"),
    dbc.CardBody(
        [
            html.H2(str(totalUsers)+" usuarios", className="card-body fw-bold"),
        ]
    ),
    dbc.CardFooter("Verificado: "+ dtObj.strftime("%d-%m-%Y %H:%M:%S"),
                className="card-text",)
    ]
    
    diffFirstNotif = statistics.mode(fdc.dfEventsDelay.loc[fdc.dfEventsDelay['updateno']==0]['delay'])
    
    
    diffAllNotif = statistics.mode(fdc.dfEventsDelay.loc[fdc.dfEventsDelay['updateno']>0]['delay'])
    
    cardDelayFirstAndUpdates =[
    dbc.CardHeader("Delay de Notificaciones - Sismos",className="card-title"),
    dbc.CardBody(
        [
            html.P(html.H5(str(diffFirstNotif)+" s. (Primera Notificación)", className="card-body fw-bold")),
            html.P(html.H5(str(diffAllNotif)+ " s. (Actualizaciones)", className="card-body fw-bold"), className=' p-0')
            #html.H5(, className="card-body fw-bold"),
        ]
    ),
    dbc.CardFooter("Valor de Moda en Distribución"),
    ]
    
    diffSilentNotif = statistics.mode(fdc.dfSilentNotif['delay'])#.mean()
    
    cardDelaySilentNotif = [
        dbc.CardHeader("Delay de Notif. Silenciosas",className="card-title"),
        dbc.CardBody(
            [
                html.H1(str(diffSilentNotif)+" s.", className="card-body fw-bold"),
            ]
        ),
        dbc.CardFooter("Valor de Moda en Distribución")
    ]
        
    resumenTab1 =dbc.CardGroup( [
                dbc.Card(cardTotalUsers, color="info", inverse=True),
                dbc.Card(cardDelayFirstAndUpdates, color="info", inverse=True),
                dbc.Card(cardDelaySilentNotif, color="info", inverse=True),
                ]
                )
                
    ##"heat" map with delays ##
    
    dfMapPlot["logdelay"] = np.log( dfMapPlot['delay'])
    map_user_delays = px.scatter_mapbox(dfMapPlot, lat=dfMapPlot['userLat'], lon=dfMapPlot['userLon'], color="logdelay",# size="delay",
                  color_continuous_scale=px.colors.sequential.Bluyl, size_max=15, zoom=5,
                  hover_data= {
                            "delay": True,   
                            "userLat": False,
                            "userLon": False,
                            "logdelay": False
                        },
                        labels={
                                "logdelay": "Ln(Delay)"
                            })
    map_user_delays.update_layout(margin={"r":20,"t":40,"l":20,"b":10})
    map_user_delays.update_layout(title = "Geographical Distribution of Users' Delay",legend_title_text="Ln(Delay)")
    map_user_delays.update_layout(
    mapbox=dict(
        bearing=0,
        center=go.layout.mapbox.Center(
            lat=countryLat,
            lon=countryLon
        ),
        pitch=0,
        zoom=8
    )
    )
    map_user_delays.update_layout(mapbox_style="dark")
    map_user_delays.update_layout(legend_title_text="Ln(Delay)")
    
    ###Distribution - Events####
    x1 = fdc.dfEventsDelay.loc[(fdc.dfEventsDelay['updateno']==0)&(fdc.dfEventsDelay['delay']>-60)&(fdc.dfEventsDelay['delay']<=60)&(fdc.dfEventsDelay['eventid'].str.contains("2023"))]
    x2 = fdc.dfEventsDelay.loc[(fdc.dfEventsDelay['updateno']==1)&(fdc.dfEventsDelay['delay']>-60)&(fdc.dfEventsDelay['delay']<=60)&(fdc.dfEventsDelay['eventid'].str.contains("2023"))]
    x3 = fdc.dfEventsDelay.loc[(fdc.dfEventsDelay['updateno']==2)&(fdc.dfEventsDelay['delay']>-60)&(fdc.dfEventsDelay['delay']<=60)&(fdc.dfEventsDelay['eventid'].str.contains("2023"))]
    x4 = fdc.dfEventsDelay.loc[(fdc.dfEventsDelay['updateno']==3)&(fdc.dfEventsDelay['delay']>-60)&(fdc.dfEventsDelay['delay']<=60)&(fdc.dfEventsDelay['eventid'].str.contains("2023"))]
    
    ####print("Percentiles 20% - First Notification")
    ####p20first = np.percentile(x1['delay'], 20)
    ####p20second = np.percentile(x2['delay'], 20)
    ####p20third = np.percentile(x3['delay'], 20)
    ####p20fourth = np.percentile(x4['delay'], 20)
    ####print("First: "+str(p20first)+", second: "+ str(p20second)+", third: "+ str(p20third)+", forth: "+str(p20fourth) )
    ####print("Percentiles 50% - First Notification")
    ####p50first = np.percentile(x1['delay'], 50)
    ####p50second = np.percentile(x2['delay'], 50)
    ####p50third = np.percentile(x3['delay'], 50)
    ####p50fourth = np.percentile(x4['delay'], 50)
    ####print("First: "+str(p50first)+", second: "+ str(p50second)+", third: "+ str(p50third)+", forth: "+str(p50fourth) )
    ####
    ####print("Percentiles 80% - First Notification")
    ####p80first = np.percentile(x1['delay'], 80)
    ####p80second = np.percentile(x2['delay'], 80)
    ####p80third = np.percentile(x3['delay'], 80)
    ####p80fourth = np.percentile(x4['delay'], 80)
    ####print("First: "+str(p80first)+", second: "+ str(p80second)+", third: "+ str(p80third)+", forth: "+str(p80fourth) )
    ####
    ####print("Percentiles 95% - First Notification")
    ####p95first = np.percentile(x1['delay'], 95)
    ####p95second = np.percentile(x2['delay'], 95)
    ####p95third = np.percentile(x3['delay'], 95)
    ####p95fourth = np.percentile(x4['delay'], 95)
    ####print("First: "+str(p95first)+", second: "+ str(p95second)+", third: "+ str(p95third)+", forth: "+str(p95fourth) )
    
    hist_data = [x1["delay"], x2["delay"], x3["delay"], x4["delay"]]
    group_labels = ['First Notif.', 'Update 1', 'Update 2','Update 3']
    
    distr_events_delays = ff.create_distplot(hist_data, group_labels, colors=px.colors.qualitative.G10,
                         bin_size=[0.1, 0.1, 0.1, 0.1], show_curve=True,show_rug=False)
                         
    distr_events_delays.update_layout(title_text='Delay Distribution - EQs',xaxis=dict(
        title="Delay [s]"
    ))
    distr_events_delays.update_layout(xaxis_range=[-0.5,8])
    distr_events_delays.update_layout(barmode='stack')
    distr_events_delays.update_layout({"plot_bgcolor": "rgb(240, 240, 240)"})
    
    ### PIE For First Notification Events ####
    pieFirst = {"-0.5 to 0 s":0,"0 to 1 s":0,"1 to 2 s":0,"2 to 3 s":0,"3 to 4 s":0,"4 to 5 s":0,"5 to 60 s":0}
    pieUpdates = {"-0.5 to 0 s":0,"0 to 1 s":0,"1 to 2 s":0,"2 to 3 s":0,"3 to 4 s":0,"4 to 5 s":0,"5 to 60 s":0}
    
    pieFirst["-0.5 to 0 s"] = len( x1.loc[ (x1['delay'] > -0.5)&( x1['delay'] <= 0 ) ]['delay'] )
    pieFirst["0 to 1 s"] = len( x1.loc[ (x1['delay'] > 0 )&( x1['delay'] <= 1 ) ]['delay'] )
    pieFirst["1 to 2 s"] = len( x1.loc[ (x1['delay'] > 1 )&( x1['delay'] <= 2 ) ]['delay'] )
    pieFirst["2 to 3 s"] = len( x1.loc[ (x1['delay'] > 2 )&( x1['delay'] <= 3 ) ]['delay'] )
    pieFirst["3 to 4 s"] = len( x1.loc[ (x1['delay'] > 3 )&( x1['delay'] <= 4 ) ]['delay'] )
    pieFirst["4 to 5 s"] = len( x1.loc[ (x1['delay'] > 4 )&( x1['delay'] <= 5 ) ]['delay'] )
    pieFirst["5 to 60 s"] = len( x1.loc[ (x1['delay'] > 5 )&( x1['delay'] <= 60 ) ]['delay'] )
    
    pieUpdates["-0.5 to 0 s"] = len( fdc.dfEventsDelay.loc[ (fdc.dfEventsDelay['updateno']>0)&(fdc.dfEventsDelay['delay'] > -0.5)&( fdc.dfEventsDelay['delay'] <= 0 )&(fdc.dfEventsDelay['eventid'].str.contains("2023")) ]['delay'] )
    pieUpdates["0 to 1 s"] = len( fdc.dfEventsDelay.loc[ (fdc.dfEventsDelay['updateno']>0)&(fdc.dfEventsDelay['delay'] > 0)&( fdc.dfEventsDelay['delay'] <= 1 )&(fdc.dfEventsDelay['eventid'].str.contains("2023")) ]['delay'] )
    pieUpdates["1 to 2 s"] = len( fdc.dfEventsDelay.loc[ (fdc.dfEventsDelay['updateno']>0)&(fdc.dfEventsDelay['delay'] > 1)&( fdc.dfEventsDelay['delay'] <= 2 )&(fdc.dfEventsDelay['eventid'].str.contains("2023")) ]['delay'] )
    pieUpdates["2 to 3 s"] = len( fdc.dfEventsDelay.loc[ (fdc.dfEventsDelay['updateno']>0)&(fdc.dfEventsDelay['delay'] > 2)&( fdc.dfEventsDelay['delay'] <= 3 )&(fdc.dfEventsDelay['eventid'].str.contains("2023")) ]['delay'] )
    pieUpdates["3 to 4 s"] = len( fdc.dfEventsDelay.loc[ (fdc.dfEventsDelay['updateno']>0)&(fdc.dfEventsDelay['delay'] > 3)&( fdc.dfEventsDelay['delay'] <= 4 )&(fdc.dfEventsDelay['eventid'].str.contains("2023")) ]['delay'] )
    pieUpdates["4 to 5 s"] = len( fdc.dfEventsDelay.loc[ (fdc.dfEventsDelay['updateno']>0)&(fdc.dfEventsDelay['delay'] > 4)&( fdc.dfEventsDelay['delay'] <= 5 )&(fdc.dfEventsDelay['eventid'].str.contains("2023")) ]['delay'] )
    pieUpdates["5 to 60 s"] = len( fdc.dfEventsDelay.loc[ (fdc.dfEventsDelay['updateno']>0)&(fdc.dfEventsDelay['delay'] > 5)&( fdc.dfEventsDelay['delay'] <= 60 )&(fdc.dfEventsDelay['eventid'].str.contains("2023")) ]['delay'] )
    
    
    pie_first_notif_delays = go.Figure(data=[go.Pie(labels=list(pieFirst.keys()), values=list(pieFirst.values()),hole=.3,
    marker = {'colors':list(colorMapDicPie.values())})])
    pie_first_notif_delays.update_layout(title_text='% of Delays By Time Range<br>First Notification')
    pie_first_notif_delays.update_layout({"plot_bgcolor": "rgb(240, 240, 240)"})

    pie_updates_notif_delay = go.Figure(data=[go.Pie(labels=list(pieUpdates.keys()), values=list(pieUpdates.values()),hole=.3,
    marker = {'colors':list(colorMapDicPie.values())})])
    pie_updates_notif_delay.update_layout(title_text='% of Delays by Time Range<br>Updates')
    pie_updates_notif_delay.update_layout({"plot_bgcolor": "rgb(240, 240, 240)"})
    
    
    ### Distribution - Silent Notifications ####
    group_labels = ['Silent Notif.']
    x1 = fdc.dfSilentNotif.loc[(fdc.dfSilentNotif['delay']>-60)&(fdc.dfSilentNotif['delay']<=60)]["delay"]
    hist_data = [x1]
    
    ########print("Percentiles 20% - Silent Notifications")
    ########p20first = np.percentile(x1, 20)
    ########print("First: "+str(p20first))
    ########print("Percentiles 50% - Silent Notifications")
    ########p50first = np.percentile(x1, 50)
    ########print("First: "+str(p50first))
    ########
    ########print("Percentiles 80% - Silent Notifications")
    ########p80first = np.percentile(x1, 80)
    ########print("First: "+str(p80first))
    ########
    ########print("Percentiles 95% - Silent Notifications")
    ########p95first = np.percentile(x1, 95)
    ########print("First: "+str(p95first))
    
    #print(x1.mode().mean())
    distr_silent_notif_delays = ff.create_distplot(hist_data, group_labels, colors=px.colors.qualitative.G10,
                         bin_size=0.1, show_curve=True,show_rug=False)
    
    distr_silent_notif_delays.update_layout(title_text='Delay Distribution - Silent Notifications',xaxis=dict(
        title="Delay [s]"
    ))
    distr_silent_notif_delays.update_layout(xaxis_range=[-0.5,8])
    distr_silent_notif_delays.update_layout({"plot_bgcolor": "rgb(240, 240, 240)"})
    
    ###############################
    ### PIE for Events Updates ####
    ###############################
    pieSilentNotif = {"-0.5 to 0 s":0,"0 to 1 s":0,"1 to 2 s":0,"2 to 3 s":0,"3 to 4 s":0,"4 to 5 s":0,"5 to 60 s":0}
    x1 = fdc.dfSilentNotif.loc[(fdc.dfSilentNotif['delay']>-60)&(fdc.dfSilentNotif['delay']<=60)]
    pieSilentNotif["-0.5 to 0 s"] = len( x1.loc[ (x1['delay'] > -0.5)&( x1['delay'] <= 0 ) ]['delay'] )
    pieSilentNotif["0 to 1 s"] = len( x1.loc[ (x1['delay'] > 0 )&( x1['delay'] <= 1 ) ]['delay'] )
    pieSilentNotif["1 to 2 s"] = len( x1.loc[ (x1['delay'] > 1 )&( x1['delay'] <= 2 ) ]['delay'] )
    pieSilentNotif["2 to 3 s"] = len( x1.loc[ (x1['delay'] > 2 )&( x1['delay'] <= 3 ) ]['delay'] )
    pieSilentNotif["3 to 4 s"] = len( x1.loc[ (x1['delay'] > 3 )&( x1['delay'] <= 4 ) ]['delay'] )
    pieSilentNotif["4 to 5 s"] = len( x1.loc[ (x1['delay'] > 4 )&( x1['delay'] <= 5 ) ]['delay'] )
    pieSilentNotif["5 to 60 s"] = len( x1.loc[ (x1['delay'] > 5 )&( x1['delay'] <= 60 ) ]['delay'] )
    
    pie_silent_notif_delays = go.Figure(data=[go.Pie(labels=list(pieSilentNotif.keys()), values=list(pieSilentNotif.values()),hole=.3,
    marker = {'colors':list(colorMapDicPie.values())})])
    pie_silent_notif_delays.update_layout(title_text='% of Delays by Time Range <br>Silent Notifications')
    
    ##################SECOND TAB #########################
    
   
    lastEvtId = fdc.dfEventsDelay.loc[fdc.dfEventsDelay['eventid'].str.contains(fdc.config.datacentercode)].sort_values(by='eventid', ascending=False)['eventid'].unique()[0]
    # initialise data of lists.
    data = {'eventid':[lastEvtId]}
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Print the output.
    outfile = df.to_json(date_format='iso', orient='split')
    
    return map_users, plot_users_vs_time, hist_time_source, map_user_delays,distr_events_delays, pie_first_notif_delays,\
            pie_updates_notif_delay, distr_silent_notif_delays, pie_silent_notif_delays,resumenTab1, outfile# \

##Callback to update the local csv data with new information stored in Firestore DB
# press the "Actualizar" button when you consider is needed.
@app.callback(
    Output("url", "href"),
    Input("buttonUpdate", "n_clicks"),
    prevent_initial_call=True,
)
def reload_data(_):
    #This method will update the data collected from FIRESTORE
    
    try:
        fdc = Data()
        fdc.loadConfigData() 
        fdc.refreshData() #This is a straight request to Firebase. Don't use too much.
    except Exception as e:
        Log.error("Problem updating the data from Firestore DB")
        Log.error(repr(e))
        return
    return "/"
   

def plotsByEvent(eventid):
    
    fdc = Data()
    fdc.loadConfigData()
    mapbox_access_token = open(".mapbox_token").read()
    colorMapDicPie = { "-0.5 to 0 s": "gray",
                    "0 to 1 s": "#00CC96",
                    "1 to 2 s": "#FFA15A",
                    "2 to 3 s": "#19D3F3",
                    "3 to 4 s": "#636EFA",
                    "4 to 5 s": "#EF553B",
                    "5 to 60 s": "#AB63FA"}
    
    if eventid == "lastevent":
        lastEvtId = fdc.dfEventsDelay.loc[fdc.dfEventsDelay['eventid'].str.contains(fdc.config.datacentercode)].sort_values(by='eventid', ascending=False)['eventid'].unique()[0]
    else:
        lastEvtId = eventid
    
    fdsn = readfdsn.ReadFDSNWS(fdc.config.fdsnwsurl)
    
    
    dfEventInfo = fdsn.getEventInfoByID(lastEvtId)
    
    tmpInfoText = ''
    tmpDateTime = ''
    
    if dfEventInfo.empty:
        Log.error("No information from FDSN for event: "+ lastEvtId)
        tmpInfoText = "Sin Información desde FDSNWS"
        tmpInfoPlace=""
        
    else:
        tmpInfoText = "Magnitud: "+str(round(dfEventInfo['magnitude'][0],1))+", Prof.: "+str(round(dfEventInfo['depth'][0]))+ " km."
        dtObj = datetime.datetime.strptime(dfEventInfo['originTime(UTC)'][0] , "%Y-%m-%dT%H:%M:%S.%fZ")
        tmpDateTime = "Fecha y Hora del sismo: "+dtObj.strftime("%Y-%m-%d %H:%M:%S (UTC)") \
        #The cities file must be loaded
        nearPlace = util.findNearestPlace(fdc.cities, dfEventInfo['latitude'][0], dfEventInfo['longitude'][0])
        #print("NEAR PLACE")
        #print(nearPlace)
        tmpDist = util.distance([float(nearPlace['lat']),dfEventInfo['latitude'][0],float(nearPlace['lon']), dfEventInfo['longitude'][0]])
        azimuth = util.azimuth([float(nearPlace['lat']),dfEventInfo['latitude'][0],float(nearPlace['lon']), dfEventInfo['longitude'][0]])
        direction = util.direction(azimuth,"es-US")
        location = util.location( tmpDist, direction, nearPlace['city'], nearPlace['country'],"es-US")
        tmpInfoPlace= location
        
    eventResumenCard = [
    dbc.CardHeader("Evento "+lastEvtId),
    dbc.CardBody(
        [
            html.H4(tmpInfoText, className="card-title"),
            html.P(tmpInfoPlace, className="card-text"),
        ]
    ),
    dbc.CardFooter(tmpDateTime),
    ]
    
    
    dfTmpEvt = fdc.dfAlertsIntensity.loc[ fdc.dfAlertsIntensity['eventid'] == lastEvtId]
    dfTmpEvt['alert'] = dfTmpEvt['alert'].fillna(0)
    
    alertsFirstNotif = len(dfTmpEvt.loc[ (dfTmpEvt['updateno'] ==0)&(dfTmpEvt['alert']==1) ])
    quickNotifFirstNotif = len(dfTmpEvt.loc[ (dfTmpEvt['updateno'] ==0)&(dfTmpEvt['alert']==0) ])
    alertsInUpdates = len(dfTmpEvt.loc[ (dfTmpEvt['updateno'] >0)&(dfTmpEvt['alert']==1) ])
    quickNotifUpdates = len(dfTmpEvt.loc[ (dfTmpEvt['updateno'] >0)&(dfTmpEvt['alert']==0) ])
    
    alertsFirstTxt = str(alertsFirstNotif)+ " Alertas (Primera Notif.)"
    quickNotifFirstTxt = str(quickNotifFirstNotif)+ " Notificaciones Rápidas (Primera Notif.)"
    alertsInUpdatesTxt = str(alertsInUpdates)+ " Alertas en Actualizaciones"
    quickNotifUpdatesTxt = str(quickNotifUpdates)+ " Notificaciones Rápidas en Actualizaciones"
    
    notifCard = [
    dbc.CardHeader("Cantidad y Tipos de Notificación"),
    dbc.CardBody(
        [
            html.H5(alertsFirstTxt, className="card-title"),
            html.H5(quickNotifFirstTxt, className="card-title"),
            html.H5(alertsInUpdatesTxt, className="card-title"),
            html.H5(quickNotifUpdatesTxt, className="card-title"),
        ]
    ),
    ]
    
    try:
        maxIntensityRep = int(dfTmpEvt['intensity'].max())
        minIntensityRep = int(dfTmpEvt['intensity'].min())
        numUsersIntensityRep = int(dfTmpEvt.loc[dfTmpEvt['intensity']>0]['intensity'].count())
    except:
        maxIntensityRep = 0
        numUsersIntensityRep = 0
    maxIntensityTxt = ""
    numRepTxt = ""
    backColor = "#FFFFFF"
    
    if maxIntensityRep == 0 or math.isnan(maxIntensityRep):
        maxIntensityTxt = "Sin Reportes de Intensidad"
        numRepTxt = ""
    elif maxIntensityRep > 0:
        roman = util.intToColorDescription(maxIntensityRep)
        maxIntensityTxt = roman.split(";")[0]
        backColor= roman.split(";")[1] 
        numRepTxt = str(numUsersIntensityRep) + " Reportes de Usuarios"
    else:
        maxIntensityTxt = "Sin Reportes de Intensidad"
    
    intensityCard = [
    dbc.CardHeader("Máxima Intensidad Reportada" ),
    dbc.CardBody(
        [
            html.H1(maxIntensityTxt, className="card-title"),
        ],style={"background-color":backColor,"text-align": "center"}
    ),
    dbc.CardFooter(numRepTxt),
    ]
    
    dfTmp = fdc.dfEventsDelay[fdc.dfEventsDelay["eventid"]==eventid]
    
    tmpVal = dfTmp["updateno"].unique()
    
    if len(tmpVal) == 1:    
        numOfNotif = 1
    else:
        numOfNotif = dfTmp["updateno"].unique().max()
        
    
    modeFirstNotif = statistics.mode(dfTmp.loc[(dfTmp['updateno']==0)]['delay'])
    
    try:
        modeUpdatesNotif = statistics.mode(dfTmp.loc[(dfTmp['updateno']>0)]['delay'])
    except:
        modeUpdatesNotif = None
    
    if modeUpdatesNotif == None or math.isnan(modeUpdatesNotif):
        tmpTxt = ""
    else:
        tmpTxt = str(round(modeUpdatesNotif,3))+ " s. (Actualizaciones)"
    totalNotif = len(dfTmp['updateno'].unique())
    delayCard = [
    dbc.CardHeader("Delay de Notificaciones - Moda" ),
    dbc.CardBody(
        [
            html.H4(str(round(modeFirstNotif,3))+ " s. (Primera Notif.)", className="card-title"),
            html.H4(tmpTxt, className="card-title"),  
        ],
    ),
    dbc.CardFooter("Total de Notificaciones: "+ str(totalNotif)),
    ]
    
    resumenTab2 =dbc.CardGroup( [
                dbc.Card(eventResumenCard, color="primary", outline=True),
                dbc.Card(intensityCard, color="primary", outline=True),
                dbc.Card(notifCard, color="primary", outline=True),
                dbc.Card(delayCard, color="primary", outline=True),
                ]
                )
                
    ###EPICENTER MAP###
    epiMap = None
    if dfEventInfo.empty:
        Log.error("No info for this event from FDSN. No epimap")
    else:
        epiLat = [dfEventInfo['latitude'][0]]
        epiLon = [dfEventInfo['longitude'][0]]
        epiMag = round(dfEventInfo['magnitude'][0],1)
        
        epiMap = go.Figure(go.Scattermapbox(
            lat=epiLat,
            lon=epiLon,
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=14
            ),
            text="Mag: "+str(epiMag),
        ))
        # mapbox_access_token = open(".mapbox_token").read()
        epiMap.update_layout(
        hovermode='closest',
        mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=epiLat[0],
                lon=epiLon[0]
            ),
            pitch=0,
            zoom=5
        )
        )

        
    ####INTENSITY MAP DISTRIBUTION####
    dfIntensity = fdc.dfAlertsIntensity.loc[(fdc.dfAlertsIntensity['eventid']==lastEvtId)&(fdc.dfAlertsIntensity['lat']!=-999)&(fdc.dfAlertsIntensity['intensity']>0)]
    dfIntensity['color']=''
    dfIntensity['intDes']=''
    
    dfIntensity['intensity'] = dfIntensity['intensity'].astype(int)
    
    for index, row in dfIntensity.iterrows():
        intVal = row['intensity']
        intDesc = util.intToColorDescription(intVal).split(";")[0]
        colorCode = util.intToColorDescription(intVal).split(";")[1]
        dfIntensity['color'][index]=colorCode
        dfIntensity['intDes'][index]=intDesc
        
     
    px.set_mapbox_access_token(open(".mapbox_token").read())
    
    intensityMap = None
    
    color_intensities = []
    
    intensityMap = {}
    
    color_intensities = []
    
    rangeValue = 0
    
    if maxIntensityRep == 1:
        rangeValue = 2
    else:
        rangeValue = maxIntensityRep
    
    for i in range(1,rangeValue+1,1):
        tmp = util.intToColorDescription(i)
        color_intensities.append(tmp.split(";")[1])
        
    tmp = fdc.config.countrylatlon.split(",")
    countryLat = float(tmp[0])
    countryLon = float(tmp[1])
    
    if dfIntensity.empty:
        Log.error("No data to present on intensity map")
    else:
        #intensityMap = go.Figure(go.Scattermapbox(
        #  lat=dfIntensity["lat"],
        #  lon=dfIntensity["lon"],
        #  mode="markers",
        #  marker=go.scattermapbox.Marker(
        #       symbol =  "circle",
        #       size = 8,
        #       opacity = 0.9,
        #       color = dfIntensity['intensity'],
        #       colorscale = color_intensities,
        #       showscale = True,
        #        ),
        # ))
        
        intensityMap = px.scatter_mapbox(dfIntensity,
                            lat=dfIntensity['lat'],
                            lon=dfIntensity['lon'],
                            hover_name="intDes",
                            color=dfIntensity['intensity'],   
                            color_continuous_scale=color_intensities,                      
                            zoom=1,
                            labels={
                                "intensity": "MMI"
                            },
                            size=np.repeat(10,dfIntensity['intensity'].size),
                            opacity = 1,
                            size_max = 10
                            )
        
        #intensityMap.update_traces(cluster=dict(enabled=True,maxzoom=10))
        intensityMap.update_layout(coloraxis_colorbar=dict(
        title="MMI",
        tickvals=[1,2,3,4,5,6,7,8,9,10,11,12],
        ticktext=romanNumbersArr,
        ))
                  
        if not dfEventInfo.empty:
            intMapCenterLat =  dfEventInfo['latitude'][0]
            intMapCenterLon =  dfEventInfo['longitude'][0]
        else:
            intMapCenterLat =  countryLat
            intMapCenterLon =  countryLon
            
        intensityMap.update_layout(margin={"r":10,"t":40,"l":10,"b":10})
        intensityMap.update_traces(showlegend=False)
       
        
        intensityMap.update_layout(
        mapbox=dict(
            accesstoken= mapbox_access_token,
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=intMapCenterLat,
                lon=intMapCenterLon
            ),
            pitch=0,
            zoom=6
        )
        )
        
        
        intensityMap.update_layout(title = 'MMI Map',legend_title_text="MMI")
        
        #intensityMap.update_traces(marker=dict(size=10,
        #                      line=dict(width=1,
        #                                color='DarkSlateGrey')),
        #          selector=dict(mode='markers'))
        
        if not dfEventInfo.empty:
            epicenterMap = go.Scattermapbox(
                lat=epiLat,
                lon=epiLon,
                mode='markers',
                fillcolor= 'red',
                showlegend=False,
                marker=go.scattermapbox.Marker(
                    size=14,
                    symbol='star',
                    color='#FFFFFF',
                ),
                text="Mag: "+str(epiMag),
            )
            #epicenterMap.update_layout(showlegend=False)
            intensityMap.add_trace(epicenterMap)
            
    
    ###Intensity vs Epicentral Distance
    # Intensity reports with Location are used along the event information (epi lat,lon)
    
    dfIntensity['distance']=''
    dfIntensity['hypodistance']=''
    
    
    intensityVsDistancePlot= {}
    
    if dfEventInfo.empty or dfIntensity.empty:
        Log.error("No information about the event or not intensity values reported. Not possible to create the Intensity Vs EpiDistance plot")
    else:
        for index, row in dfIntensity.iterrows():
            dfIntensity['hypodistance'][index] = util.distanceHypoToPoint(dfEventInfo['latitude'],dfEventInfo['longitude'], dfEventInfo['depth'], dfIntensity['lat'][index], dfIntensity['lon'][index])     
            dfIntensity['distance'][index] = util.distanceEpiToPoint(dfEventInfo['latitude'],dfEventInfo['longitude'], dfIntensity['lat'][index], dfIntensity['lon'][index])     
        intensityVsDistancePlot =px.scatter(dfIntensity, x="hypodistance", y="intensity", color="color",color_discrete_map="identity", log_x=True,
                 title="MMI vs Distance",labels={
                    "hypodistance": "Hypocenter Distance [km]",
                    "intensity":"MMI" 
                 })
        intensityVsDistancePlot.update_layout({"plot_bgcolor": "rgb(240, 240, 240)"})
        intensityVsDistancePlot.update_traces(marker=dict(size=10,
                              line=dict(width=1,
                                        color='DarkSlateGrey')),
                  selector=dict(mode='markers'))
        intensityVsDistancePlot.update_yaxes(tickvals=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], ticktext=romanNumbersArr)
        #Adding a line with data from Allen 2012
        if not dfEventInfo.empty:
            allenDist = [x for x in range(0,500,10)]
            allenMMI = [ util.ipe_allen2012_hyp(x,dfEventInfo['magnitude'][0],dfEventInfo['depth'][0]) for x in range(0,410,10)]
            
            #Standard Deviation
            sigma = [util.ipe_allen2012_hyp_sigma(x,dfEventInfo['depth'][0]) for x in range(0,410,10)]
            allenMMIplusSigma = np.add(allenMMI,sigma)
            allenMMIminusSigma = np.subtract(allenMMI,sigma)
            
            allenTrace = go.Scatter(
                        x=allenDist,
                        y=allenMMI,
                        mode="lines",
                        line=go.scatter.Line(color="black"),
                        showlegend=True,
                         name="Allen's IPE 2012"  )
            intensityVsDistancePlot.add_trace(allenTrace)
            
            allenTracePlus = go.Scatter(
                        x=allenDist,
                        y=allenMMIplusSigma,
                       #     mode="dash",
                        line=dict(color='gray', dash='dash'),
                        showlegend=True,
                         name=u"+\u03c3"+" (SD)" )
            intensityVsDistancePlot.add_trace(allenTracePlus)
            allenTraceMinus = go.Scatter(
                        x=allenDist,
                        y=allenMMIminusSigma,
                       #     mode="dash",
                        line=dict(color='gray', dash='dash'),
                         showlegend=True,
                         name=u"-\u03c3"+" (SD)")
            intensityVsDistancePlot.add_trace(allenTraceMinus)
    
    #print(dfIntensity)
    ### Delays Distribution for the event###
    
    x1 = fdc.dfEventsDelay.loc[(fdc.dfEventsDelay['updateno']==0)&(fdc.dfEventsDelay['delay']>-60)&(fdc.dfEventsDelay['delay']<=60)&(fdc.dfEventsDelay['eventid']== lastEvtId)]
    x2 = fdc.dfEventsDelay.loc[(fdc.dfEventsDelay['updateno']==1)&(fdc.dfEventsDelay['delay']>-60)&(fdc.dfEventsDelay['delay']<=60)&(fdc.dfEventsDelay['eventid']== lastEvtId)]
    x3 = fdc.dfEventsDelay.loc[(fdc.dfEventsDelay['updateno']==2)&(fdc.dfEventsDelay['delay']>-60)&(fdc.dfEventsDelay['delay']<=60)&(fdc.dfEventsDelay['eventid']== lastEvtId)]
    x4 = fdc.dfEventsDelay.loc[(fdc.dfEventsDelay['updateno']==3)&(fdc.dfEventsDelay['delay']>-60)&(fdc.dfEventsDelay['delay']<=60)&(fdc.dfEventsDelay['eventid']== lastEvtId)]
    
    hist_data = []
    group_labels = []
    
    for i in range(0,4,1):
        x = fdc.dfEventsDelay.loc[(fdc.dfEventsDelay['updateno']==i)&(fdc.dfEventsDelay['delay']>-60)&(fdc.dfEventsDelay['delay']<=60)&(fdc.dfEventsDelay['eventid']== lastEvtId)]
        
        if not x.empty and len(x)>3:
            hist_data.append(x['delay'])
            if i == 0:
                group_labels.append("First Notif.")
            else:
                group_labels.append("Update "+ str(i))
    
    eventDelayDistribution = ff.create_distplot(hist_data, group_labels, colors=px.colors.qualitative.G10,
                         bin_size=0.1, show_curve=True,show_rug=False)
                         
    eventDelayDistribution.update_layout(title_text='Delays Distribution',xaxis=dict(
        title="Delay [s]"
    ))
    eventDelayDistribution.update_layout(xaxis_range=[-0.5,8])
    eventDelayDistribution.update_layout(barmode='stack')
    eventDelayDistribution.update_layout({"plot_bgcolor": "rgb(240, 240, 240)"})
    
    dfTmpEvt['alert'] = dfTmpEvt['alert'].fillna(0)
    dfTmpEvt['updateno'] = dfTmpEvt['updateno'].astype(int)
    dfTmpEvt['alert'] = dfTmpEvt['alert'].astype(int)
    
    #Notifications histograms
    notifHistogram = px.histogram(dfTmpEvt, x="updateno", color="alert",
                                    color_discrete_map={
                                        1: "#EF553B",
                                        0: "#636EFA"},
                                    labels={
                                        "alert": "Notification Type",
                                        
                                    }).update_xaxes(categoryorder='total ascending')
    
    newnames = {'1':'Alert', '0': 'Quick Notif.'}
    
    notifHistogram.update_layout(bargap=0.5)
    notifHistogram.update_layout(
    xaxis = dict(
        tickmode = 'linear',
        tick0 = 0,
        dtick = 1
    )
    )
    notifHistogram.update_layout(title_text='Notifications Number by Update',xaxis=dict(title="Update Number"))
    notifHistogram.for_each_trace(lambda t: t.update(name = newnames[t.name],
                                      legendgroup = newnames[t.name],
                                      hovertemplate = t.hovertemplate.replace(t.name, newnames[t.name])
                                     )
                  )
    notifHistogram.update_layout({"plot_bgcolor": "rgb(240, 240, 240)"})
    
    return resumenTab2, intensityMap, intensityVsDistancePlot, eventDelayDistribution,notifHistogram

#This is a callback used to read the text input after user clicked the 
# button. If the input value is an event that exists in the dataframes then it will write
#in memory the new information through the output and this will trigger the callback
#that is used to create the plots and maps through plotsByEvent method.

@app.callback(Output('eventid', 'data',allow_duplicate=True),
              Output('tabs','active_tab'),
              Output('modal-noevent','is_open'),
              Input('eventid-button', 'n_clicks'),
              State('eventid-input', 'value'),prevent_initial_call=True)
def update_output(n_clicks, evtid):
    
    openBol = False
    
    if n_clicks is None or n_clicks == 0:
        raise PreventUpdate
        
    if len(evtid)==0:
        Log.error("empty!")
        text = "Introduzca un ID"
        
        raise PreventUpdate
    if evtid in fdc.dfAlertsIntensity.eventid.values and evtid in fdc.dfEventsDelay.eventid.values:
        Log.info("Event found")
        text= "Evento encontrado"
        data = {'eventid':[evtid]}
    else:
        Log.error("Evento No encontrado")
        
        #raise PreventUpdate
        openBol = True
        data = {'eventid':[""]}
    
     # initialise data of lists.
    
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Print the output.
    #print(df)
    outfile = df.to_json(date_format='iso', orient='split')
    
    return outfile, 'tab-1', openBol

#this callback is called when there is a new eventid on the dcc.Store component.
#It will read the eventid from memory and use the plotsByEvent method.
#Tab2 must be rendered properly.

@app.callback(Output("resumenTab2","children"),
    #Output("epi-map","figure"),
    Output("intensity-map","figure"),
    Output("intensity-distance","figure"),
    Output("delay-distribution-event","figure"), 
    Output("notification-histogram","figure"), 
    Input('eventid', 'data'),prevent_initial_call=True)
def update_table(jsonified_cleaned_data):
    try:
        df = pd.read_json(jsonified_cleaned_data, orient='split')
    except Exception as e:
        df = pd.DataFrame()
        log.error("Error reading the JSON file: "+str(e))
        raise PreventUpdate
    
    if df.size == 0 or df['eventid'][0] == "":
        raise PreventUpdate
    
    tab2 = plotsByEvent(df['eventid'][0])
    return tab2[0], tab2[1], tab2[2], tab2[3], tab2[4]

# NVABAR - add callback for toggling the collapse on small screens
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


#Run the app
if __name__ == '__main__':
    app.run_server( debug = True )
