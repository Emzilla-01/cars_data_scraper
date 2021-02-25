# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 22:29:22 2019
###############################################################################
retrospective 2-24-2021

QUICK AND DIRTY WEB SCRAPER FOR CARS DATA

TAKES A URLPATTERN FROM THE SITE FOR A PARTICULAR MAKE AND MODEL
OUTPUTS A CSV WITH SOME MINIMAL WEIGHTAGE FUNCTIONALITY

url   MAIN INPUT IS FROM WEBSITE COPIED AND SOME MANUAL TRIMMING IS APPLIED TO FORM QUERY
.xlsx MAIN OUTPUT 

EVEN IF IMPLEMENTATION IS UGLY OR NOT PEP8, 
THIS WAS A QUICK SCRIPT TO PERFORM
A BUSINESS FUNCTION,
IN THIS CASE TO SCRAPE LISTINGS RATHER THAN MAUALLY CLICKING THROUGH FRONTEND
AND RECORDING PRICES, & OTHER ATTRIBUTES

NAMES OF PRICES & OTHER ATTRIBUTES WERE EXPOSED INSIDE SEARCH PATTERNS RETURNED BY SEARCH FORM SELECTION.
SITE URL PATTERN INTO SCRIPT -> RECORD N PAGES OF AUTO LISTINGS INTO A TABULAR FILE LIKE CSV, EXCEL

TIME TO REVISE WILL COME AGAIN

###############################################################################

Create a data scraper for a particular e-commerce website relating to auto sales.

Motivation is simple: 
        Shopping for a car is stressful- they are expensive purchases that quickly depreciate.
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

@author: Emzilla
"""
#import cfg
import requests
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
import datetime as dt


pd.set_option('display.max_columns', 8)
###############################################################################
"""
# vars/settings
Definitions of use-case specific information.
These will undoubtedly change as the website's front-end changes.
Better move fast!
"""
###############################################################################
url=r"https://www.cars.com/for-sale/searchresults.action/?mdId=20823&mkId=20017&page=1&perPage=100&prMx=18000&rd=50&searchSource=GN_SELECT&sort=relevance&zc=19146"
#url="https://www.cars.com/for-sale/searchresults.action/?dealerType=all&drCntId=28002&mdId=20823&mkId=20017&page=1&perPage=100&prMx=18000&rd=50&searchSource=GN_REFINEMENT&sort=relevance&zc=19146"
headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36"}

c7ars_row_type= "shop-srp-listings__inner" #"listing-row__details"
price_name="listing-row__price"
stats_name = "listing-row__save switch-favorite unsaved saveVehicleHeart compare-switch-favorite"
###############################################################################
"""
# helper functions
"""
###############################################################################
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
    stats_dict=row.find("div", class_=stats_name).prettify().replace("false","False").replace('true',"True")
    stats_dict=find_txt(stats_dict, d1="vehicle=\'", d2="\'>")
    stats_dict = eval(stats_dict)
    stats_dict.setdefault("link", f"https://www.a-popular-cars-listing-website.com/vehicledetail/detail/{stats_dict.get('listingId')}/overview/")
    price= find_txt(row.find("span", class_=price_name).prettify()).strip("$").strip(",")
    price= float(price.replace(",", ""))
    stats_dict.setdefault("price", price)
    mileage=row.find("span", class_ = "listing-row__mileage").prettify()
    mileage=find_txt(mileage, ">\n ", " mi.\n")
    #print(mileage)
    try:
        mileage = int(mileage.replace(",", ""))
    except ValueError as e:
        mileage = 900009
    stats_dict.setdefault("mileage", mileage)
    return stats_dict

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
            

###############################################################################

if __name__ == '__main__':
    pass
    page = requests.get(url, headers=headers)
    type(page.content)
    soup0 = BeautifulSoup(page.content, 'html.parser')
    soup = BeautifulSoup(soup0.prettify(), 'html.parser') # Hacky two soups solution to parsing problem

    #help(soup.findAll)

    find_rows = soup.find_all("div", class_="shop-srp-listings__inner")

    #stats_dict=row.find("div", class_=stats_name).prettify()
    #stats_dict=find_txt(stats_dict, d1="vehicle=\'", d2="\'>")
    #stats_dict = eval(stats_dict)
    #stats_dict.setdefault("link", f"https://www.a-popular-cars-listing-website.com/vehicledetail/detail/{stats_dict.get('listingId')}/overview/")

    """
    'listingId' links to the page on a-popular-cars-listing-website.com like so:
        https://www.a-popular-cars-listing-website.com/vehicledetail/detail/{listingId}/overview/
    """

    first_page_stats = [get_stats(r) for r in find_rows]

    df= pd.DataFrame(first_page_stats)
    df.set_index("price")

    df.columns
    df.loc[:20][["modelYear", "mileage", "trimName", "price"]]

    min(df['modelYear']), max(df['modelYear'])
    
    # =============================================================================
    # scoring-- how to compare each listing quantitatively besides price?
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

    df.loc[0][['price', 'modelYear', 'mileage']].price

    df = df.assign(priceScore = lambda r: [score_row(int(rr), price_scoring) for rr in r.price])
    df = df.assign(mileageScore = lambda r: [score_row(int(rr), mileage_scoring) for rr in r.mileage])
    df = df.assign(modelYearScore = lambda r: [score_row(int(rr), modelYear_scoring) for rr in r.modelYear])

    df = df.assign(totalScore = lambda r: [np.mean(i) for i in list(zip(r.priceScore, r.mileageScore, r.modelYearScore))])
    df[['totalScore','price', 'priceScore', 'modelYear', 'modelYearScore', 'mileage', 'mileageScore']]
    df = df.sort_values('totalScore', ascending=0)
    df.head

    df.to_excel(f"cars_scrape_{dt.datetime.now().strftime('%m_%d_%y')}.xls")
    df.to_csv(f"cars_scrape_{dt.datetime.now().strftime('%m_%d_%y')}.csv")
    # Price
    # Mileage
    # Transmission
    # Trim
    # Color

    #print(title.strip())
    #with open('etc.txt', 'wt') as textfile:
    #    textfile.writelines(str(soup.contents))