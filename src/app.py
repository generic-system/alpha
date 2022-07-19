import os

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import pymongo
from dash import Dash, dcc, html, dash_table
from dash.dash_table.Format import Format, Scheme, Sign
from dash.dependencies import Output, Input
from dash_bootstrap_templates import load_figure_template

MATURITY_OPTIONS = ['Date', 'Overnight', '1 Week', '2 Weeks', '1 Month', '2 Months', '3 Months', '6 Months', '12 Months']

COLOR_1 = '#16cc62'  # Green
COLOR_2 = '#196ee6'  # Blue
COLOR_3 = '#875F9A'  # Purple
COLOR_4 = '#e6b219'  # Orange
COLOR_5 = '#e6196e'  # Red

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.options.display.expand_frame_repr = True
pd.options.display.width = 1000

#############################################
# Query JSON results from MongoDB
#############################################

CONNECTION_STRING = os.environ['MONGODB_STRING']
client = pymongo.MongoClient(CONNECTION_STRING)

# sample dataset
db = client.get_default_database()

# sample collection
hibor_rates = db['hibor_rates']

# remove outliers that are clearly bad data, if needed
query = {}

# convert our cursor into a list
data = list(hibor_rates.find(query).sort([("Date", pymongo.DESCENDING)]).limit(10000))
df = pd.DataFrame(data).drop(columns=['_id'])
df['Date'] = df['Date'].dt.date
df_unpivot = pd.melt(df, id_vars='Date', value_vars=df.columns.drop('Date').tolist())
df_head = df.head(100)
# print(df_head.to_dict('records'))
#############################################

app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
load_figure_template('DARKLY')

columns = [
    dict(id='Date', name='Date', type='datetime'),
    dict(id='Overnight', name='Overnight', type='numeric', format=Format(scheme=Scheme.fixed, precision=6, sign=Sign.parantheses)),
    dict(id='1 Week', name='1 Week', type='numeric', format=Format(scheme=Scheme.fixed, precision=6, sign=Sign.parantheses)),
    dict(id='1 Month', name='1 Month', type='numeric', format=Format(scheme=Scheme.fixed, precision=6, sign=Sign.parantheses)),
    dict(id='2 Weeks', name='2 Weeks', type='numeric', format=Format(scheme=Scheme.fixed, precision=6, sign=Sign.parantheses)),
    dict(id='2 Months', name='2 Months', type='numeric', format=Format(scheme=Scheme.fixed, precision=6, sign=Sign.parantheses)),
    dict(id='3 Months', name='3 Months', type='numeric', format=Format(scheme=Scheme.fixed, precision=6, sign=Sign.parantheses)),
    dict(id='6 Months', name='6 Months', type='numeric', format=Format(scheme=Scheme.fixed, precision=6, sign=Sign.parantheses)),
    dict(id='12 Months', name='12 Months', type='numeric', format=Format(scheme=Scheme.fixed, precision=6, sign=Sign.parantheses)),
]

app.layout = html.Div([
    html.H4('Hibor per Maturity'),
    # dash_table.DataTable(df_head.to_dict('records'), [{"name": i, "id": i} for i in df_head.columns], id='tbl'),
    dash_table.DataTable(
        # data=df_head.to_dict('records'),
        data=df_head.to_dict('records'),
        # [{"name": i, "id": i} for i in MATURITY_OPTIONS],
        # [{"name": i, "id": i, "type": "numeric", "format": Format(scheme=Scheme.decimal, precision=6, sign=Sign.parantheses)} for i in MATURITY_OPTIONS],
        columns=columns,
        # style_header={
        #     'backgroundColor': 'rgb(210, 210, 210)',
        #     'color': 'black',
        #     'fontWeight': 'bold'
        # },
        # style_data={
        #     'color': 'black',
        #     'backgroundColor': 'white'
        # },
        style_header={
            'backgroundColor': 'rgb(30, 30, 30)',
            'color': 'white'
        },
        style_data={
            'backgroundColor': 'rgb(50, 50, 50)',
            'color': 'white'
        },
        style_cell_conditional=[
            {
                'if': {'column_id': c},
                'textAlign': 'left'
            } for c in ['Date', 'Region']
        ],
        style_data_conditional=
        [
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(80, 80, 80)',
            },
            {
                'if': {
                    'filter_query': '{{1 Month}} = {}'.format(df_head['1 Month'].max()),
                },
                'backgroundColor': COLOR_5,
                'color': 'white',
            },
            {
                'if': {
                    'filter_query': '{{1 Month}} = {}'.format(df_head['1 Month'].min()),
                },
                'backgroundColor': COLOR_2,
                'color': 'white',
            }
        ],

        page_current=0,
        page_action='custom',
        page_size=10,  # we have less data in this example, so setting to 20
        style_table={'height': '350px', 'overflowY': 'auto'},
        fixed_rows={'headers': True},
        style_cell={
            'minWidth': 95, 'maxWidth': 95, 'width': 95
        },
        id='datatable-paging-page-count',
    ),

    html.Br(),
    html.Br(),

    dcc.Graph(id="graph"),

    dcc.Checklist(
        id="checklist",
        options=[{'label': i, 'value': i} for i in list(df_unpivot.variable.unique())],  # + [{'label': 'All', 'value': 'All'}],
        value=['Overnight', '1 Month', '3 Months', '6 Months', '12 Months'],
        style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'},
        # inline=True
    ),
    # dcc.Slider(
    #     id='year-slider',
    #     min=df['Year'].min(),
    #     max=df['Year'].max(),
    #     value=df['Year'].min(),
    #     step=None,
    #     marks={str(Year): str(Year) for Year in df['Year'].unique()}
    # )
])


@app.callback(
    Output('datatable-paging-page-count', 'data'),
    Input('datatable-paging-page-count', "page_current"),
    Input('datatable-paging-page-count', "page_size"))
def update_table(page_current, page_size):
    return df.iloc[
           page_current * page_size:(page_current + 1) * page_size
           ].to_dict('records')


@app.callback(
    Output("graph", "figure"),
    Input("checklist", "value"))
def update_line_chart(maturity: str):
    if maturity == "All":
        filtered_df = df_unpivot
    else:
        mask = df_unpivot.variable.isin(maturity)
        filtered_df = df_unpivot[mask]
    fig = px.line(filtered_df, x="Date", y='value', color='variable')
    fig.update_yaxes(tick0=0.25, dtick=1.0)
    fig.update_layout(legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    ))
    return fig


app.run_server(debug=True)
