import pandas as pd
import json
import ast
import numpy as np

def get_market_share(x):
    razer = x["RazerSalesDiff"]
    competitor = x["CompetitorSalesDiff"]
    market_total = razer + competitor
    if market_total != 0:
        return 100 * razer/market_total
    else:
        return np.nan

def get_merge_compare(data, concerned_competitor_columns, competitor_reference):
    reference_name = "Razer"
    merge_compare = []
    for c in concerned_competitor_columns:
        sub = competitor_reference.loc[(~competitor_reference[c].isna())]
        for i, r in sub.iterrows():
            category = r.Category
            reference_product = r["Product Full Name-Razer WJMY"]
            sub_reference_data = data.loc[data["title"] == reference_product].copy()
            sub_reference_data.rename(columns={"title": "%sProduct" % reference_name, "price": "%sPrice" % reference_name, "sales": "%sSales" % reference_name, "likes": "%sLikes" % reference_name, "rating": "%sRating" % reference_name, "stock": "%sStock" % reference_name}, inplace=True)
            concerned_product = r["Product Full Name-Logitech G MY"]
            sub_concerned_data = data.loc[data["title"] == concerned_product].copy()
            sub_concerned_data.rename(columns={"title": "CompetitorProduct", "price": "CompetitorPrice", "sales": "CompetitorSales", "likes": "CompetitorLikes", "rating": "CompetitorRating", "stock": "CompetitorStock"}, inplace=True)

            for cc in ["RazerStock", "RazerPrice", "RazerSales", "RazerRating", "RazerLikes"]:
                sub_reference_data["%sDiff"% cc] = sub_reference_data[cc].diff()

            for cc in ["CompetitorStock", "CompetitorPrice", "CompetitorSales", "CompetitorRating", "CompetitorLikes"]:
                sub_concerned_data["%sDiff"% cc] = sub_concerned_data[cc].diff()        

            merge_tmp = pd.merge(sub_reference_data[["date"] + [c for c in sub_reference_data.columns if reference_name in c]], sub_concerned_data[["date"] + [c for c in sub_concerned_data.columns if "titor" in c]], how="outer", on="date")
            merge_tmp["category"] = category
            merge_compare.append(merge_tmp.copy())
            
    merge_compare = pd.concat(merge_compare).reset_index(drop=True)
    merge_compare["ComparePrice"] = merge_compare["RazerPrice"] - merge_compare["CompetitorPrice"]
    merge_compare["MarketShare"] = merge_compare.apply(get_market_share, axis=1)
    return merge_compare

def merge_rq_rp(request, response):
    rq_rp = request.merge(response, how='left', on='request_uuid')
    return rq_rp

def merge_rq_rp_rs(request, response, resource):
    rq_rp = merge_rq_rp(request, response)
    rq_rp['resource_ts'] = rq_rp.request_ts.apply(lambda x: x[:-7])
    resource['resource_ts'] = resource.timestamp.apply(lambda x: x[:-7])
    rq_rp_rs = rq_rp.merge(resource, how='left', on='resource_ts')
    return rq_rp_rs

def check_success_status(row):
    if row.request_type in ["face_compare", "face_detect"]:
        res = row.response.split(",")[0].split(":")[-1].replace(" ", "").replace("\'", "")
    elif row.request_type in ["mykad_back", "mykad_front", "segmentation", "landmark"]:
        try:
            res = json.loads(row.response.replace("\'", "\"").replace("False}", "\"False\"}").replace("True}", "\"True\"}").replace("False,", "\"False\",").replace("True,", "\"True\","))
            if 'status' in res:
                if  'ocr_results' in res:
                    res = "Success"
                else:
                    res = res['status']['message']
            else:
                res = "Status can't found"
        except Exception as e: 
            res = str(row.response) + "\n" + str(e)
    elif row.request_type in ["liveness"]:
        try:
            res = json.loads(row.response.replace("\'", "\""))
            if 'status' in res:
                if  'liveness_probability' in res:
                    res = "Success"
                else:
                    res = res['status']['message']
            else:
                res = "Status can't found"
        except Exception as e:
            res = str(row.response) + "\n" + str(e)
    elif row.request_type == "face_all":
        try:
            res = ast.literal_eval(row.response)
            if 'fr' in res and 'liveness' in res:
                if  'liveness_probability' in res['liveness'] and 'confidence' in res['fr']:
                    res = "Success"
                else:
                    res = res['liveness']['status']['message']
            else:
                res = "Status can't found"
        except Exception as e:
            res = str(row.response) + "\n" + str(e)
    elif row.request_type in ["segmentation_flask_oss", "segmentation_rabbitmq_oss"]:
        try:
            res = ast.literal_eval(row.response)
            if 'data' in res:
                if 'img' in res['data']:
                    if 'code' in res['data']['img']:
                        if res['data']['img']['code'] == "SUCCESS":
                            res = "Success"
            else:
                res = "data can't found"
        except Exception as e:
            res = str(row.response) + "\n" + str(e)
    return res

def get_summary_stats(r, merge_response):
    dff = merge_response.loc[(merge_response.exp_name == r.exp_name) & (merge_response.exp_time == r.exp_time)]
    r['Total Response'] = len(dff)
    r['Ruturn Rate (%)'] = 100 * r['Total Response'] / r['Total Request']
    r['Successful Rate (%)'] = 100 * r['Total Response'] / r['Total Request'] # pending
    return r

def get_single_stats(r):
    total = len(r)
    
    # latency
    average_elapsed = r.elapsed.mean()
    
    # return rate
    n_return = (~r.response.isna()).sum()
    return_rate = n_return / total
    
    # success rate
    n_success = (r.success_status == "Success").sum()
    success_rate = n_success/total

    # cpu
    cpu = r.cpu.mean()
    
    # memory
    memory = r.memory.mean()
    # network send
    network_send_gb = r.network_send_gb.mean()
    # network recv
    network_receive_gb = r.network_receive_gb.mean()
    
    d = {}
    d['Total Request'] = total
    d['Average Latency (sec)'] = average_elapsed
    d['Return Rate'] = 100 * return_rate
    d['Success Rate'] = 100 * success_rate
    d['Average CPU'] = cpu
    d['Average Memory'] = memory
    d['Average Network Send'] = network_send_gb
    d['Average Network Receive'] = network_receive_gb
    return pd.Series(d, index=['Total Request', 'Average Latency (sec)', 'Return Rate', 'Success Rate', 'Average CPU', 'Average Memory', 'Average Network Send', 'Average Network Receive'])