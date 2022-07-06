from datetime import date
import time
import requests
import pandas as pd

#print date to help users to track down when the file was generated.
data = date.today()
data.strftime("%d/%m/%Y")
date_str = date.today()

#asks for seller id.
domain_order = int(input("Type in domain number (integer is enough):\n1. Malaysia\n2. Thailand\n"))
seller_shopee_id = input('\nType in the seller id: \n')
# seller_shopee_id = "15300402"

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
print("\nRunning for seller id in %s: %s:" % (domain_mapping[domain_order]["name"], seller_shopee_id))
start_time = time.time()
# url_api_request = 'https://shopee.com.my/api/v4/recommend/recommend?bundle=shop_page_product_tab_main&limit=999&offset=0&section=shop_page_product_tab_main_sec&shopid=' + seller_shopee_id
url_api_request = 'https://%s/api/v4/recommend/recommend?bundle=shop_page_product_tab_main&limit=999&offset=0&section=shop_page_product_tab_main_sec&shopid=' % (domain_mapping[domain_order]["domain"]) + seller_shopee_id
r = requests.get(url_api_request)

#define the number of ads published.
num_ads = (r.json()['data']['sections'][0]['data']['item'])
list_size = len(num_ads)

data = {
    "ad_id": [],
    "title": [],
    "stock": [],
    "price": [],
    "sales": [],
    "rating": [],
    "likes": [],
    "views": []
}
#creates a while statement using the number of ads created. Since the (index) json file stars with 0, the while statment starts with -1. 
creat_while = -1
while creat_while < list_size - 1:
    creat_while += 1
    #store the information displayed inside the json file. It's possible to extract even more data, you only need to add the exact json's children path you're interested in. The scrapper will sleep for 1 second and then get the next ad's information.
    ad_id = (r.json()['data']['sections'][0]['data']['item'][creat_while]['itemid'])
    title = (r.json()['data']['sections'][0]['data']['item'][creat_while]['name'])
    stock = (r.json()['data']['sections'][0]['data']['item'][creat_while]['stock'])
    sales = (r.json()['data']['sections'][0]['data']['item'][creat_while]['historical_sold'])
    likes = (r.json()['data']['sections'][0]['data']['item'][creat_while]['liked_count'])
    views = (r.json()['data']['sections'][0]['data']['item'][creat_while]['view_count'])
    price = (r.json()['data']['sections'][0]['data']['item'][creat_while]['price'])
    rating = (r.json()['data']['sections'][0]['data']['item'][creat_while]['item_rating']['rating_count'][0])
#     time.sleep(1)
    
    data["ad_id"].append(ad_id)
    data["title"].append(title)
    data["stock"].append(stock)
    data["sales"].append(sales)
    data["likes"].append(likes)
    data["views"].append(views)
    data["price"].append(price)
    data["rating"].append(rating)
data = pd.DataFrame(data)
data["price"] = data["price"]/100000
data.to_csv("shopee_%s_%s_%s.csv" % (domain_mapping[domain_order]["name"], seller_shopee_id, date_str), index=False)
end_time = time.time()
print("Done for %s in %.3f secs. \nThere are %d products" % (seller_shopee_id, end_time - start_time, len(data)))