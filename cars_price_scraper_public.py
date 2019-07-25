# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 22:29:22 2019

Create a data scraper for a particular e-commerce website relating to auto sales.

Motivation is simple: 
        Shopping for a car is stressful- they are expensive purchase that quickly depreciate.
        I want to simplify the process for myself by scraping the data to identify the best deals without paging through hundreds of listings or manual data entry.
        Maybe there is a relationship between year+mileage+trim which can be modeled?
        
Current usage:
    - Use the website front-end to enter search terms such as make/model, price range, transmission, etc. and click the "search" button.
    - Copy the URL given by the front-end and provide to the .py
    - .py will scrape for you,
        
Todo:
    - clean up and provide as functions/classes
    - use argparse so script may be called from cmdline like "python cars_price_scraper.py --u={url} --o={output filepath}"
    - minimize code as data
    - improve scoring model
    - add &perPage=100 to provided url automatically

@author: emzilla-01
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
import datetime as dt
# =============================================================================
"""
# vars/settings
Definitions of use-case specific information.
These will undoubtedly change as the website's front-end changes.
Better move fast!
"""
# =============================================================================
pd.set_option('display.max_columns', 8)

#url='https://www.a-popular-cars-listing-website.com/for-sale/searchresults.action/?rd=30&fuelTypeId=31763&fuelTypeId=31764&mkId=20017&mkId=20017&mdId=20823&mdId=20606&searchSource=ADVANCED_SEARCH&prMx=8000&transTypeId=28113&kw=coupe&kwm=ANY&zc=08540&stkTypId=28881&perPage=100' # Civic
#url="https://www.a-popular-cars-listing-website.com/for-sale/searchresults.action/?mdId=20861&mkId=20088&prMx=8000&rd=50&searchSource=QUICK_FORM&stkTypId=28881&zc=08540&perPage=100" # Corolla
#url="https://www.a-popular-cars-listing-website.com/for-sale/searchresults.action/?mdId=20823&mkId=20017&prMx=8000&rd=50&searchSource=QUICK_FORM&zc=08540&perPage=100"
url="https://www.a-popular-cars-listing-website.com/for-sale/searchresults.action/?dealerType=all&drCntId=28002&mdId=20823&mkId=20017&page=1&perPage=100&prMx=8000&rd=50&searchSource=GN_REFINEMENT&sort=relevance&zc=08540"
headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36"}
cars_row_type= "shop-srp-listings__inner" #"listing-row__details"
price_name="listing-row__price"
stats_name = "listing-row__save switch-favorite unsaved saveVehicleHeart compare-switch-favorite"
# =============================================================================
"""
# helper functions
"""
# =============================================================================
def find_txt(s, d1="$", d2="\n"):
    """
    find_text(s, d1="$", d2="\n")...
    Simple helper function to find some particular information within a big string...
    ... takes one big string and two (often different) delimiters to return the value for a particular record within some html
    
    s: a string, generally from a BeautifulSoup.prettify()
    d1: delimiter 1 precedes targeted text
    d2: delimiter 2 follows targeted text
    """
    first=s.find(d1)
    second=s[first:].find(d2) + len(s[:first])
    return(s[first+len(d1):second])

def get_stats(row):
    """
    get_stats(row)
    We are looking at an e-commerce site to scrape pricing data relative to other features.
    This func is tuned to how the particular site returns rows for each listing.
    Idea is to parse key information about each listing from this func.
    """
    stats_dict=row.find("div", class_=stats_name).prettify()
    stats_dict=find_txt(stats_dict, d1="vehicle=\'", d2="\'>")
    stats_dict = eval(stats_dict)
    stats_dict.setdefault("link", f"https://www.a-popular-cars-listing-website.com/vehicledetail/detail/{stats_dict.get('listingId')}/overview/")
    price= find_txt(row.find("span", class_=price_name).prettify()).strip("$").strip(",")
    price= float(price.replace(",", ""))
    stats_dict.setdefault("price", price)
    mileage=row.find("span", class_ = "listing-row__mileage").prettify()
    mileage=find_txt(mileage, ">\n ", " mi.\n")
    mileage = int(mileage.replace(",", ""))
    stats_dict.setdefault("mileage", mileage)
    return stats_dict
    
# =============================================================================
"""
# Imperative/explorative operations
"""
# =============================================================================


page = requests.get(url, headers=headers)
type(page.content)
soup0 = BeautifulSoup(page.content, 'html.parser')
soup = BeautifulSoup(soup0.prettify(), 'html.parser') # Hacky two soups solution to parsing problem

help(soup.findAll)

find_rows = soup.find_all("div", class_="shop-srp-listings__inner")

#stats_dict=row.find("div", class_=stats_name).prettify()
#stats_dict=find_txt(stats_dict, d1="vehicle=\'", d2="\'>")
#stats_dict = eval(stats_dict)
#stats_dict.setdefault("link", f"https://www.a-popular-cars-listing-website.com/vehicledetail/detail/{stats_dict.get('listingId')}/overview/")

"""
'listingId' links to the page on a-popular-cars-listing-website.com like so:
    https://www.a-popular-cars-listing-website.com/vehicledetail/detail/{listingId}/overview/
"""
#price= find_txt(row.find("span", class_=price_name).prettify()).strip("$").strip(",")
#price= float(price.replace(",", ""))
#stats_dict.setdefault("price", price)
#row




first_page_stats = [get_stats(r) for r in find_rows]

df= pd.DataFrame(first_page_stats)
df.set_index("price")
#df["price", "modelYear", "]
df.columns
df.loc[:20][["modelYear", "mileage", "trimName", "price"]]

min(df['modelYear']), max(df['modelYear'])


# =============================================================================
# Scoring for year, mileage, and price
# currently linear, probably should be exponential curve?
# 
# =============================================================================
modelYear_range = [i for i in range(min(df['modelYear']), max(df['modelYear'])+1)]
modelYear_coeffs= np.linspace(0,1,len(modelYear_range)+1)[1:]
modelYear_scoring = list(zip(modelYear_range, modelYear_coeffs))

mileage_ranges = np.arange(0, 202000, 20000)[::-1]
mileage_coeffs = np.linspace(0,1,len(mileage_ranges)+1)[1:]
mileage_scoring = list(zip(mileage_ranges, mileage_coeffs))[::-1]

price_ranges = np.arange(min(df['price']), max(df['price']+500), 500)[::-1]
price_coeffs = np.linspace(0,1,len(price_ranges )+1)[1:]
price_scoring= list(zip(price_ranges, price_coeffs))[::-1]



def score_row(val, l):
    """
    val: the observed value such as price, mileage, year
    l: the {value}_scoring list which 
    """
    for r in l:
        if val==r[0]:
            return r[1]
        elif val <=r[0]:
            return r[1]
        elif val > r[0]:
            continue
        else:
            return 0
        

score_row(2006, modelYear_scoring)
score_row(4895, price_scoring)
score_row(151476, mileage_scoring)

df.loc[0][['price', 'modelYear', 'mileage']].price

df = df.assign(priceScore = lambda r: [score_row(int(rr), price_scoring) for rr in r.price])
df = df.assign(mileageScore = lambda r: [score_row(int(rr), mileage_scoring) for rr in r.mileage])
df = df.assign(modelYearScore = lambda r: [score_row(int(rr), modelYear_scoring) for rr in r.modelYear])

df = df.assign(totalScore = lambda r: [np.mean(i) for i in list(zip(r.priceScore, r.mileageScore, r.modelYearScore))])
df[['totalScore','price', 'priceScore', 'modelYear', 'modelYearScore', 'mileage', 'mileageScore']]
df = df.sort_values('totalScore', ascending=0)
df.head


df.to_excel(f"cars_scrape_{dt.datetime.now().strftime('%m_%d_%y')}.xls")
# Price
# Mileage
# Transmission
# Trim
# Color


#print(title.strip())

#with open('etc.txt', 'wt') as textfile:
#    textfile.writelines(str(soup.contents))