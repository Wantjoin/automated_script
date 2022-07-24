from ast import In
from cgitb import html
import logging
import uvicorn
from fastapi import FastAPI, Body
from fastapi.middleware.wsgi import WSGIMiddleware
import pandas as pd
from sqlalchemy import create_engine
from pydantic import BaseModel
from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output
import os
from application.dash_app.create_dash import init_dash_app, create_summary_layout, create_cross_exp_layout
# from application.utils.dash_utils import check_success_status, get_single_stats, merge_rq_rp_rs
from application.utils.dash_utils import get_merge_compare

# class RequestData(BaseModel):
#     exp_name: str
#     exp_time: str
#     send_server_ip: str
#     request_server_ip: str
#     request_uuid: str
#     n: int
#     request_index: int
#     file_path: str
#     request_ts: str
#     request_type: str
#     is_return_image: int
#     extra_attributes: str

# class ResponseData(BaseModel):
#     request_uuid: str
#     response_ts: str
#     elapsed: float
#     response: str    

# class ResourceData(BaseModel):
#     timestamp: str
#     server_ip: str
#     cpu: float
#     memory: float
#     memory_mb: float
#     gpu_memory_mb: float
#     gpu_util: float
#     network_send_gb: float
#     network_receive_gb: float    

# user = os.getenv('DATABASE_USER', 'deployment_benchmark')
# passw = os.getenv('DATABASE_PASSWD', '$Wiseai031218')
# host =  os.getenv('DATABASE_IP', '127.0.0.1')
# port = os.getenv('DATABASE_PORT', 3306)
# database = os.getenv('DATABASE_NAME', 'deployment_analysis')
# request_table_name = os.getenv('REQUEST_TABLE', "request")
# response_table_name = os.getenv('RESPONSE_TABLE', "response")
# resource_table_name = os.getenv('RESOURCE_TABLE', "resource")

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """
    Initialize FastAPI and add variables
    """
    # mysql_url = 'mysql+pymysql://%s:%s@%s/%s' % (user, passw, host, database)
    # print("Connect to %s " % mysql_url)
    # sql_engine = create_engine(mysql_url, pool_recycle=3600)
    # dbConnection    = sqlEngine.connect()
    # add model and other preprocess tools too app state
    data = pd.read_csv("/root/automated_script/crawler/shopee_competitors.csv")
    competitor_data = pd.read_csv("/root/automated_script/crawler/concerned_seller_id.csv")
    sheet_id = "1xsWXxbFvUs55LHVlVOviJ2FqclUGegDQw9YhOQQq9s0"
    sheet_name = "Sheet1"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet='{sheet_name}'"
    competitor_reference = pd.read_csv(url) 
    concerned_competitor_columns = ["Product Full Name-Logitech G MY"]
    merge_compare = get_merge_compare(data, concerned_competitor_columns, competitor_reference)
    app.package = {
        "sql_engine": {
            "data": data,
            "reference": competitor_reference,
            "competitor": competitor_data,
            "merge": merge_compare 
        }
    }

    # db_connection = sql_engine.connect()
    # request = pd.read_sql("select * from %s" % request_table_name, db_connection)
    # response = pd.read_sql("select * from %s" % response_table_name, db_connection)
    # resource = pd.read_sql("select * from %s" % resource_table_name, db_connection)
    # resource['resource_ts'] = resource.timestamp.apply(lambda x: x[:-7])
    # db_connection.close()
    dash_app = init_dash_app(requests_pathname_prefix="/dash/")
    content = html.Div(id="page-content")
    dash_app.layout = html.Div([dcc.Location(id="url"), content])

    @dash_app.callback(
        [Output("stats_table", "data"), Output("stats_table", "columns")], 
        [Input("filter_column1", "value"), Input("filter_dropdown1", "value"), Input("filter_dropdown2", "value")]
    )
    def display_table(columns, razerproduct, competitorproduct):
        dff = merge_compare[(merge_compare["RazerProduct"].isin(razerproduct)) & merge_compare["CompetitorProduct"].isin(competitorproduct)][columns]
        return dff.to_dict("records"), [{"name": i, "id": i} for i in dff.columns]

    # Create the callback to update the page
    @dash_app.callback(Output("page-content", "children"), [Input("url", "pathname")])
    def render_page_content(pathname):

        if pathname == "/dash/":
            return create_summary_layout(sql_engine=app.package["sql_engine"])
            logging.info("trigger")
        elif pathname == "/dash/cross":
            return create_cross_exp_layout(sql_engine=app.package["sql_engine"])
        else:
            logging.info("other")
            return html.Div([
            html.Label(["Debug: %s not implemented" % pathname], style={'font-weight': 'bold', "text-align": "center"})])
    @dash_app.callback(
        Output('exp_time_dropdown', 'options'),
        [Input('exp_name_dropdown', 'value')]
    )
    def update_expdate_dropdown(name):
        dff = request.loc[request.exp_name == name]
        return [{'label': i, 'value': i} for i in sorted(dff.exp_time.unique(), reverse=True)]
    
    @dash_app.callback(
        Output('exp_name_dropdown', 'options'),
        [Input('exp_name_dropdown', 'value')]
    )
    def update_exp_name_dropdown(name):
        unique_exp_name = request.exp_name.unique()
        return [{'label': i, 'value': i} for i in unique_exp_name]

    @dash_app.callback(
        Output('request_table', 'children'), 
        [Input('exp_name_dropdown', 'value'), Input('exp_time_dropdown', 'value')]
    )
    def update_request_table(exp_name, exp_time):
        if(exp_name != None and exp_time != None):
            sub_request = request.loc[(request['exp_name'] == exp_name) & (request['exp_time'] == exp_time)]
            sub_request_with_rp_rs = merge_rq_rp_rs(sub_request, response, resource)
            sub_request_with_rp_rs['success_status'] = sub_request_with_rp_rs.apply(check_success_status, axis=1)
            sub_stats = sub_request_with_rp_rs.groupby(["request_type", "n"]).apply(get_single_stats).reset_index()            
            columns = [{"name": i, "id": i} for i in sub_stats.columns]
            return [dash_table.DataTable(data=sub_stats.to_dict('records'), columns=columns)]
        else:
            return []

    @dash_app.callback(
        # Output("test_label", "children"),
        Output("select_exp_table2", "data"),
        [Input('select_exp_table', 'derived_virtual_data'),
        Input('select_exp_table', 'derived_virtual_selected_rows')]
    )
    def update_cross_selection(rows, derived_virtual_selected_rows):
        if derived_virtual_selected_rows is None:
            derived_virtual_selected_rows = []
        df = pd.DataFrame({"exp_time":[]}) if rows is None else pd.DataFrame(rows)
        if len(df) != 0:
            selected_exp_name = df.exp_name.iloc[derived_virtual_selected_rows].tolist()
            db_connection = app.package["sql_engine"].connect()
            request = pd.read_sql("select * from %s" % request_table_name, db_connection)
            response = pd.read_sql("select * from %s" % response_table_name, db_connection)
            resource = pd.read_sql("select * from %s" % resource_table_name, db_connection)
            resource['resource_ts'] = resource.timestamp.apply(lambda x: x[:-7])
            rq_rp_rs = merge_rq_rp_rs(request, response, resource)
            db_connection.close()
            sub_df = rq_rp_rs.loc[rq_rp_rs.exp_name.isin(selected_exp_name)]
            df = pd.DataFrame({"exp_time": sorted(sub_df.exp_time.unique().tolist(), reverse=True)})
        return df.to_dict('record')

    @dash_app.callback(
        Output("cross_table", "children"),
        [Input('select_exp_table', 'derived_virtual_data'),
        Input('select_exp_table', 'derived_virtual_selected_rows'),
        Input('select_exp_table2', 'derived_virtual_data'),
        Input('select_exp_table2', 'derived_virtual_selected_rows')]
    )
    def update_compare_table(exp_name_rows, exp_name_indices, exp_time_rows, exp_time_indices):
        if len(exp_name_indices) != 0 and len(exp_time_indices) != 0:
            df_name = pd.DataFrame({"exp_name":[]}) if exp_name_rows is None else pd.DataFrame(exp_name_rows)
            df_time = pd.DataFrame({"exp_time":[]}) if exp_time_rows is None else pd.DataFrame(exp_time_rows)

            selected_exp_name = df_name.exp_name.iloc[exp_name_indices].tolist()
            selected_exp_time = df_time.exp_time.iloc[exp_time_indices].tolist()

            db_connection = app.package["sql_engine"].connect()
            request = pd.read_sql("select * from %s" % request_table_name, db_connection)
            response = pd.read_sql("select * from %s" % response_table_name, db_connection)
            resource = pd.read_sql("select * from %s" % resource_table_name, db_connection)
            resource['resource_ts'] = resource.timestamp.apply(lambda x: x[:-7])
            rq_rp_rs = merge_rq_rp_rs(request, response, resource)
            sub_df = rq_rp_rs.loc[rq_rp_rs.exp_name.isin(selected_exp_name) & rq_rp_rs.exp_time.isin(selected_exp_time)]
            sub_df['success_status'] = sub_df.apply(check_success_status, axis=1)
            sub_stats = sub_df.groupby(["request_type", "n", "exp_name", "exp_time"]).apply(get_single_stats).reset_index()
            columns = [{"name": i, "id": i} for i in sub_stats.columns]
            return [dash_table.DataTable(data=sub_stats.to_dict('records'), columns=columns)]
        else:
            return []            
    dash_app.server.debug = True
    app.mount("/dash", WSGIMiddleware(dash_app.server))    
    

# @app.post("/request/store")
# async def store_request_log(
#     req_data: RequestData
# ):
#     try:
#         data = {"exp_name": [req_data.exp_name], "exp_time": [req_data.exp_time], "send_server_ip": [req_data.send_server_ip], "request_server_ip": [req_data.request_server_ip], 
#         "request_uuid": [req_data.request_uuid],"n": [req_data.n], "request_index": [req_data.request_index], "file_path": [req_data.file_path], 
#         "request_ts": [req_data.request_ts], "request_type": [req_data.request_type], "is_return_image": [req_data.is_return_image], "extra_attributes": [req_data.extra_attributes]}
        
#         response = pd.DataFrame(data)
#         connection = app.package["sql_engine"].connect()
#         response.to_sql(request_table_name, connection, if_exists='append', index=False)
#         connection.close()
#         return "request inserted successfully"
#     except Exception as e:
#         return str(e)

# @app.post("/response/store")
# async def store_response_log(
#     response_data: ResponseData
# ):
#     try:
#         data = {"request_uuid": [response_data.request_uuid], "response_ts": [response_data.response_ts], 
#         "elapsed": [response_data.elapsed], "response": [response_data.response]}
        
#         response = pd.DataFrame(data)
#         connection = app.package["sql_engine"].connect()
#         response.to_sql(response_table_name, connection, if_exists='append', index=False)
#         connection.close()
#         return "response inserted successfully"
#     except Exception as e:
#         return str(e)

# @app.post("/resource/store")
# async def store_log_to_resource(
#     resource_data: ResourceData
# ):
#     try:
#         data = {"timestamp": [resource_data.timestamp], "server_ip": [resource_data.server_ip], "cpu": [resource_data.cpu], 
#         "memory": [resource_data.memory], "memory_mb": [resource_data.memory_mb], "gpu_memory_mb": [resource_data.gpu_memory_mb], 
#         "gpu_util": [resource_data.gpu_util], "network_send_gb": [resource_data.network_send_gb], "network_receive_gb": [resource_data.network_receive_gb]
#         }
        
#         resource = pd.DataFrame(data)
#         connection = app.package["sql_engine"].connect()
#         resource.to_sql(resource_table_name, connection, if_exists='append', index=False)
#         connection.close()
#         return "resource inserted successfully"
#     except Exception as e:
#         return str(e)

# @app.on_event("shutdown")
# def shutdown_event():
#     # dbConnection.close()
#     with open("log.txt", mode="a") as log:
#         log.write("Application shutdown")