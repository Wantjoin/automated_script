from datetime import date
import time
import requests
import pandas as pd
import os

output_csv_file = "/root/automated_script/crawler/shopee_competitors.csv"
#print date to help users to track down when the file was generated.
data = date.today()
data.strftime("%d/%m/%Y")
date_str = date.today()

concerned_data = pd.read_csv("/root/automated_script/crawler/concerned_seller_id.csv")

#asks for seller id.
domain_mapping = {
    1: {
        "domain": "shopee.com.my",
        "name": "Malaysia"
    },
    2: {
        "domain": "shopee.co.th",
        "name": "Thailand" 
    }
}
# domain_order = int(input("Type in domain number (integer is enough):\n1. Malaysia\n2. Thailand\n"))

data = {
    "seller_id": [],
    "date": [],
    "ad_id": [],
    "title": [],
    "stock": [],
    "price": [],
    "sales": [],
    "rating": [],
    "likes": [],
    "views": []
}

for _, row in concerned_data.iterrows():
    
    # seller_shopee_id = input('\nType in the seller id: \n')
    # seller_shopee_id = "15300402"
    seller_shopee_id = str(row.seller_id)
    domain_order = 1 if row.country == "MY" else 2

    print("\nRunning for seller id in %s: %s:" % (domain_mapping[domain_order]["name"], seller_shopee_id))
    start_time = time.time()
    # url_api_request = 'https://shopee.com.my/api/v4/recommend/recommend?bundle=shop_page_product_tab_main&limit=999&offset=0&section=shop_page_product_tab_main_sec&shopid=' + seller_shopee_id
    url_api_request = 'https://%s/api/v4/recommend/recommend?bundle=shop_page_product_tab_main&limit=999&offset=0&section=shop_page_product_tab_main_sec&shopid=' % (domain_mapping[domain_order]["domain"]) + seller_shopee_id
    r = requests.get(url_api_request)

    #define the number of ads published.
    num_ads = (r.json()['data']['sections'][0]['data']['item'])
    list_size = len(num_ads)

    #creates a while statement using the number of ads created. Since the (index) json file stars with 0, the while statment starts with -1. 
    creat_while = -1
    while creat_while < list_size - 1:
        creat_while += 1
        #store the information displayed inside the json file. It's possible to extract even more data, you only need to add the exact json's children path you're interested in. The scrapper will sleep for 1 second and then get the next ad's information.
        d = r.json()['data']['sections'][0]['data']['item'][creat_while]
        ad_id = (d['itemid'])
        title = (d['name'])
        stock = (d['stock'])
        sales = (d['historical_sold'])
        likes = (d['liked_count'])
        views = (d['view_count'])
        price = (d['price'])
        rating = (d['item_rating']['rating_count'][0])

        data["seller_id"].append(seller_shopee_id)
        data["date"].append("%s" % date_str)
        data["ad_id"].append(ad_id)
        data["title"].append(title)
        data["stock"].append(stock)
        data["sales"].append(sales)
        data["likes"].append(likes)
        data["views"].append(views)
        data["price"].append(price)
        data["rating"].append(rating)
    end_time = time.time()
    print("Done for %s in %.3f secs. \nThere are %d products" % (seller_shopee_id, end_time - start_time, len(num_ads)))
data = pd.DataFrame(data)
data["price"] = data["price"]/100000



if os.path.exists(output_csv_file):
    data.to_csv(output_csv_file, mode="a", index=False, header=False)
else:
    data.to_csv(output_csv_file, index=False)
