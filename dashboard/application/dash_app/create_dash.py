import dash
from dash import dash_table
import pandas as pd
import flask
import os
import sqlalchemy
import logging
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from functools import partial
# from application.utils.dash_utils import get_summary_stats, merge_rq_rp, merge_rq_rp_rs
from application.utils.dash_utils import get_market_share
# import dash_bootstrap_components as dbc

user = os.getenv('DATABASE_USER', 'deployment_benchmark')
passw = os.getenv('DATABASE_PASSWD', '$Wiseai031218')
host =  os.getenv('DATABASE_IP', '127.0.0.1')
port = os.getenv('DATABASE_PORT', 3306)
database = os.getenv('DATABASE_NAME', 'deployment_analysis')
REQUEST_TABLE = os.getenv('REQUEST_TABLE', "request")
RESPONSE_TABLE = os.getenv('RESPONSE_TABLE', "response")
RESOURCE_TABLE = os.getenv('RESOURCE_TABLE', "resource")
mysql_url = 'mysql+pymysql://%s:%s@%s/%s' % (user, passw, host, database)
# print("Connect to %s " % mysql_url)
# sql_engine = sqlalchemy.create_engine(mysql_url, pool_recycle=3600)

def init_dash_app(requests_pathname_prefix):
    server = flask.Flask(__name__)
    app = dash.Dash(__name__, server=server, requests_pathname_prefix=requests_pathname_prefix, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.title = "Want Join Analysis"
    return app

def main_component():
    return dbc.Row(dbc.Col(
            html.Div([
                html.H1(id='main-title',
                        children="Want Join Dashboard (WIP)",
                        style={'margin-bottom': '10px',
                            'margin-top': '10px', 'text-align': 'center'},
                        className="header")]
                    ),
            ),
        )

def nav_component():
    return html.Div(
        [
            # dcc.Location(id="url"),
            html.H2("Menu", className="display-5", style={'text-align': 'center'},),
            html.Hr(),
            dbc.Nav(
                [
                    dbc.NavLink("Home", href="/dash/", active="exact"),
                    # dbc.NavLink("Cross Experiments", href="/dash/cross", active="exact"),
                ],
                vertical=True,
                pills=True,
            ),
        ],
        # style=SIDEBAR_STYLE,
    )

def create_summary_layout(sql_engine):
# def create_dash_app(requests_pathname_prefix: str = None, request = None, response = None, resource = None) -> dash.Dash:
    """
    Sample Dash application from Plotly: https://github.com/plotly/dash-hello-world/blob/master/app.py
    """
    # server = flask.Flask(__name__)
    # db_connection = sql_engine.connect()
    # logging.info("ggg")
    # app = dash.Dash(__name__, server=server, requests_pathname_prefix=requests_pathname_prefix)
    try:
        # request = pd.read_sql("select * from %s" % REQUEST_TABLE, db_connection)
        # response = pd.read_sql("select * from %s" % RESPONSE_TABLE, db_connection)
        # resource = pd.read_sql("select * from %s" % RESOURCE_TABLE, db_connection)
        # merge_response = response.merge(request[['request_uuid', 'exp_name', 'exp_time']], on='request_uuid', how='left')
        # function_stats = partial(get_summary_stats, merge_response=merge_response)
        # stats = request.groupby("exp_name").exp_time.value_counts()
        stats = sql_engine["merge"]
        stats_columns_unique = stats.columns.to_list()
        dropdown1 = stats["RazerProduct"].unique().tolist()
        dropdown2 = stats["CompetitorProduct"].unique().tolist()
        # stats.rename(columns={"exp_time": "Total Request"}, inplace=True)
        # stats = stats.reset_index()
        # stats = stats.apply(function_stats, axis=1)
        stats_columns = [{"name": i, "id": i} for i in stats.columns]
        layout = html.Div([
                    # Main Title
            main_component(),
            nav_component(),
            html.Hr(),
            html.Div(
                [
                    html.Label(['Columns filter'], style={'font-weight': 'bold', "text-align": "center"}),
                    dcc.Dropdown(
                        id="filter_column1",
                        options=[{"label": st, "value": st} for st in stats_columns_unique],
                        placeholder="-Select Columns-",
                        multi=True,
                        value=stats_columns_unique,
                        ),
                    html.Label(['RazerProduct filter'], style={'font-weight': 'bold', "text-align": "center"}),
                    dcc.Dropdown(
                        id="filter_dropdown1",
                        options=[{"label": st, "value": st} for st in dropdown1],
                        placeholder="-Select a RazerProduct-",
                        multi=True,
                        value=dropdown1,
                        ),
                    html.Label(['CompetitorProduct filter'], style={'font-weight': 'bold', "text-align": "center"}),
                    dcc.Dropdown(
                        id="filter_dropdown2",
                        options=[{"label": st, "value": st} for st in dropdown2],
                        placeholder="-Select a CompetitorProduct-",
                        multi=True,
                        value=dropdown2,
                        ),
                    dash_table.DataTable(
                        id='stats_table', 
                        data=stats.to_dict('records'), 
                        columns=stats_columns,
                        page_action="native",
                        page_size=10
                        )
                ]
            ),
            html.Hr(),
            # html.Div([
            # html.Label(['Experiment Name:'], style={'font-weight': 'bold', "text-align": "center"}),
            # dcc.Dropdown(
            #     id='exp_name_dropdown',
            #     ),
            #     ],style={'width': '20%', 'display': 'inline-block'}),
            # html.Div([
            # html.Label(['Experiment Time:'], style={'font-weight': 'bold', "text-align": "center"}),
            # dcc.Dropdown(
            #     id='exp_time_dropdown',
            #     ),
            #     ],style={'width': '20%', 'display': 'inline-block'}
            # ),
            # html.Hr(),
            # html.Div(id="request_table")
            # dash_table.DataTable(
            #     id='request_table',
            #     columns=[{"name": i, "id": i} for i in request.columns],
            #     data=request.to_dict('records'),
                # editable=False,
                # filter_action="native",
                # sort_action="native",
                # row_selectable="multi",
                # row_deletable=False,
                # selected_rows=[],
                # page_action="native",
                # page_current=0,
                # page_size=6
                # )
        ])


    except Exception as e:
        logging.error(str(e))

    return layout

def create_cross_exp_layout(sql_engine):
    db_connection = sql_engine.connect()
    # logging.info("ggg")
    # app = dash.Dash(__name__, server=server, requests_pathname_prefix=requests_pathname_prefix)
    try:
        request = pd.read_sql("select * from %s" % REQUEST_TABLE, db_connection)
        response = pd.read_sql("select * from %s" % RESPONSE_TABLE, db_connection)
        resource = pd.read_sql("select * from %s" % RESOURCE_TABLE, db_connection)
        rq_rp_rs = merge_rq_rp_rs(request, response, resource)
        unique_exp_name = pd.DataFrame({"exp_name": rq_rp_rs.exp_name.unique()})
        unique_exp_name_columns = [{"name": i, "id": i} for i in unique_exp_name.columns]

        unique_exp_time = pd.DataFrame({"exp_time": []})
        unique_exp_time_columns = [{"name": i, "id": i} for i in unique_exp_time.columns]
        layout = html.Div([
            # Main Title
            main_component(),
            nav_component(),

            html.Hr(),
            
            # Selection Area
            dbc.Row(
                    [
                        dbc.Col(
                            dbc.Row([
                                dash_table.DataTable(
                                    id='select_exp_table',
                                    data=unique_exp_name.to_dict('record'),
                                    columns=unique_exp_name_columns,
                                    row_selectable="multi",
                                    page_action="native",
                                    page_size=10
                                )
                            ]
                            )
                        ),
                        dbc.Col(
                            dbc.Row(
                                [
                                    dash_table.DataTable(
                                        id='select_exp_table2',
                                        data=unique_exp_time.to_dict('record'),
                                        columns=unique_exp_time_columns,
                                        row_selectable="multi",
                                        page_action="native",
                                        page_size=10
                                        )
                                ]
                            )
                        )
                    ]
                ),

            html.Hr(),

            html.Div(id="cross_table")
            
            ]
        )
    except Exception as e:
        logging.info(str(e))
        layout = html.Div([
                    # Main Title
            main_component(),
            nav_component()
        ])
    return layout