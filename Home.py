import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import math
import time
from sqlalchemy import create_engine, text
from dashboards import product_brand_insights, customer_satisfaction
from login import login_page
from db import get_engine

st.set_page_config(layout="wide", page_title='Web Scraping')

def home():
    st.title('FLIPKART SCRAPER')
    url=st.text_input('Enter Flipkart Search URL:')
    if st.button('🚀Start Scraping'):
        try:
            headers={ "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0"}

            product_list=[]
            page=1

            progress_text = st.empty()
            total_products_text = st.empty()
            while True:
                progress_text.text(f"🕸️ Scraping page {page}...")
                if "page=" in url:
                    base_url = re.sub(r'page=\d+', f'page={page}', url)
                else:
                    base_url = url + f"&page={page}"
                source=requests.get(base_url, headers=headers, timeout=30)
                source.raise_for_status()

                soup=BeautifulSoup(source.text, 'html.parser')
                main_container=soup.find('div', class_='QSCKDh dLgFEE')
                product=main_container.find_all('div', class_='jIjQ8S') if main_container else []

                if not product:
                    break

                for p in product:
                    name=p.find('div', class_='RG5Slk') 
                    price_tag=p.find('div', class_='hZ3P6w DeU9vF')
                    clean_price = None
                    if price_tag:
                        price_text = price_tag.get_text(strip=True)
                        clean_price = ( price_text.replace('₹', '').replace(',', '') ).strip()

                    rating=p.find('div', class_='MKiFS6')

                    link_tag=p.find('a', href=True)
                    product_id=None
                    product_url=None
                    if link_tag:
                        product_url = "https://www.flipkart.com" + link_tag['href']
                        match = re.search(r'/p/(\w+)', link_tag['href'])
                        if match:
                            product_id = match.group(1)

                    discount = None
                    discount_tag = p.find('div', class_='HQe8jr')
                    if discount_tag:
                        discount_text = discount_tag.get_text(strip=True)
                        match = re.search(r'(\d+)', discount_text)
                        if match:
                            discount = int(match.group(1))

                    brand_name = None
                    if name:
                        name_text = name.get_text(strip=True)
                        n_parts=name_text.split()
                        if len(n_parts)>0:
                            brand_name=n_parts[0].lower()

                    stock_tag = p.find('div', class_='HZ0E6r Rm9_cy')  
                    stock = 'In Stock'
                    if stock_tag:
                        stock_text = stock_tag.get_text(strip=True)
                        if "Only" in stock_text and "left" in stock_text:
                            stock = stock_tag.get_text(strip=True)

                    ratings_reviews_tag = p.find('span', class_='PvbNMB') 
                    ratings_count = None
                    if ratings_reviews_tag:
                        ratings_text = ratings_reviews_tag.get_text(strip=True)
                        r_parts = ratings_text.split('&')  
                        if len(r_parts) >= 1:
                            ratings_count = r_parts[0].split()[0]

                    product_list.append({
                        'Product ID': product_id,
                        'Product Name':name.get_text(strip=True) if name else None,
                        'Brand':brand_name,
                        'Price':clean_price,
                        'Discount': discount,
                        'Availability':stock,
                        'Rating':rating.get_text(strip=True) if rating else None,
                        'Number of Ratings': ratings_count
                    })
                page+=1
                time.sleep(3)
            total_products_text.success(f"Total products scraped so far: {len(product_list)}")

            raw_data=pd.DataFrame(product_list)
            st.dataframe(raw_data)

            engine = get_engine()
        
            st.session_state["scraped_data"] = raw_data

            if raw_data.empty:
                st.error("Scraped DataFrame is Empty")
                return

        # Dataset Exploration
            # raw_data.head()
            # raw_data.shape
            # raw_data.columns
            # raw_data.duplicated().sum()
            # raw_data.isnull().sum()
            # raw_data.Brand.nunique()
            # raw_data.dtypes

            # raw_data.loc[raw_data['Discount']<0, :]
            

        # Data Cleaning
            raw_data.columns=raw_data.columns.str.strip().str.lower().str.replace(' ', '_')

            raw_data['price']=pd.to_numeric(raw_data['price'], errors='coerce')
            raw_data['rating']=pd.to_numeric(raw_data['rating'], errors='coerce')
            raw_data['number_of_ratings'] = (raw_data['number_of_ratings']
                                                .astype(str)
                                                .str.replace(',', '', regex=False)
                                                .str.strip()
                                                .replace(['nan', 'None', ''], None)
                                                .astype('Int64')
                                            )
            raw_data['discount']=raw_data['discount'].fillna(0)
            raw_data.drop_duplicates(inplace=True, ignore_index=True)
            raw_data.insert(0,'record_id', range(1, len(raw_data) + 1))

            raw_data.to_sql('scraped_cleandata', con=engine, if_exists='replace', index=False)

        except Exception as e:
            st.error(f"Error: {e}")

dashboards_dict={
    'Home':home,
    'Product & Brand Insights': product_brand_insights.render,
    'Customer Satisfaction Analysis': customer_satisfaction.render
}
if st.session_state.get("logged_in", False):
    page=st.sidebar.radio("Go to", list(dashboards_dict.keys()))

    if st.sidebar.button("Logout"):
        st.session_state['logged_in']=False
        st.session_state['username'] = ""
        st.rerun()

    dashboards_dict[page]()
else:
    login_page()
