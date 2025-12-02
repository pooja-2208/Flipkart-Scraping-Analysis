import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import statsmodels
from db import get_engine
from scipy.stats import ttest_ind

def render():
    engine=get_engine()
    flipkart_products=pd.read_sql("SELECT * FROM scraped_cleandata", engine)

    st.set_page_config(layout='wide')
    st.title("📊 PRODUCT & BRAND INSIGHTS")

    st.sidebar.header("Filters")

    # brand filter
    brands=flipkart_products['brand'].unique().tolist()
    brands.sort()
    brand_selected=st.sidebar.multiselect(
        "Select Brand :",
        options=brands,
        default=brands
    )

    # Applying filters
    if brand_selected:
        filtered=flipkart_products[flipkart_products['brand'].isin(brand_selected)]
    else:
        filtered=flipkart_products.copy()

    # KPIs
    def kpi_box(title, value):
        st.markdown(
        f"""
        <div style="
            padding: 15px;
            margin-bottom:20px;
            border-radius: 12px;
            border: 1px solid #d3d3d3;
            background-color: #e6f2ff;
            text-align: center;
            width: 100%;
            height: 120px;               
            display: flex;
            flex-direction: column;
            justify-content: center;  
            ">
            <div style="font-size: 15px; font-weight: 500; margin-bottom: 6px; white-space: normal;">
                {title}
            </div>
            <div style="font-size: 17px; font-weight: 700;">
                {value}
            </div>
        </div>
        """, unsafe_allow_html=True
        )

    col1, col2, col3, col4=st.columns(4)
    with col1:
        kpi_box("Total Products", f"{filtered['product_id'].count():,}")
    with col2:
        kpi_box("Unique Brands",f"{filtered['brand'].nunique():,}")

    brand_counts = filtered['brand'].value_counts()
    top_brand = brand_counts.idxmax()
    top_brand_count = brand_counts.max()
    with col3:
        kpi_box("Brand with the Most Product Variants", f"{top_brand} ({top_brand_count})")

    total_products = filtered.shape[0]
    instock_count = filtered[filtered['availability'] == "In Stock"].shape[0]
    instock_percent = (instock_count / total_products) * 100
    with col4:
        kpi_box("In-Stock Products %", f"{instock_percent:.1f}%")

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        kpi_box("Average Price",f"₹ {round(filtered['price'].mean(), 2):,}")

    costliest = filtered.loc[filtered['price'].idxmax()]
    with col6:
        kpi_box("Costliest Product", f"{costliest['product_name']} : {(costliest['price'])}")
    
    with col7:
        kpi_box("Average discount", f"{round(filtered['discount'].mean(),2):.2f}%")

    high_discount=filtered.loc[filtered['discount'].idxmax()]
    with col8:
        kpi_box("Product with the Highest Average Discount",f"{high_discount['product_name']} : {high_discount['discount']}%")

    # Charts
    st.markdown('<h2 style="font-size:35px;">📈 Advanced Analytics</h2>', unsafe_allow_html=True)
    tab1, tab2, tab3  = st.tabs(
    ["Distribution Analysis", "Brand Analysis", "Statistical Analysis"] )

    with tab1:
        st.subheader("Price Distribution Analysis")
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.histogram(
            filtered,
            x="price",
            nbins=30, 
            color_discrete_sequence=["green"]  
        )
            fig1.update_traces(
            marker_line_color="black",   
            marker_line_width=1          
        )
        c1.plotly_chart(fig1, width='stretch')

        with c2:
            fig2 = px.box(
                filtered,
                y="price",           
            )
        c2.plotly_chart(fig2, width='stretch')

        st.subheader("Discount Distribution Analysis")
        c3, c4=st.columns(2)
        with c3:
            fig1 = px.histogram(
            filtered,
            x="discount",
            nbins=20,   
            color_discrete_sequence=["green"]
        )
            fig1.update_traces(
            marker_line_color="black",   
            marker_line_width=1          
        )
        c3.plotly_chart(fig1, width='stretch')
        with c4:
            fig2 = px.box(
                filtered,
                y="discount",           
            )
        c4.plotly_chart(fig2, width='stretch')

        availability_status=filtered['availability'].value_counts().reset_index()
        availability_status.columns = ['stock_status', 'count']
        c5, c6=st.columns(2)
        with c5:
            st.subheader("Stock Availability Distribution Analysis")
            fig = px.pie(
            availability_status, 
            names='stock_status', 
            values='count',
            color='stock_status',
            color_discrete_map={'In Stock':'#1f77b4','Out of Stock':'#ff7f0e'},
            hole=0.6
            ) 
            fig.update_traces(
                textinfo='label+percent',         
                texttemplate=[
                '%{percent}' if s == 'In Stock' else '' 
                for s in availability_status['stock_status']
                ],
                textposition='inside',
                textfont_size=14
            )

        c5.plotly_chart(fig, width='stretch')

    with tab2:
        c6, c7=st.columns(2)
        brand_avg=flipkart_products.groupby(by='brand').agg(avg_price=('price','mean'), avg_discount=('discount','mean'),
                                                rating_count=('number_of_ratings','mean')).sort_values(by='avg_price', ascending=False).reset_index()
        median_price = brand_avg['avg_price'].median()
        costly_brands = brand_avg[brand_avg['avg_price'] > median_price].sort_values(by='avg_price', ascending=False).reset_index(drop=True).round(2)
        costly_brands.columns=['Brand','Average Price','Average Discount','Popularity']
        budget_friendly_brands = brand_avg[brand_avg['avg_price'] <= median_price].sort_values(by='avg_price', ascending=False).reset_index(drop=True).round(2)
        budget_friendly_brands.columns=['Brand','Average Price','Average Discount','Popularity']
        with c6:
            st.markdown(
                "<h1 style='font-size:20px;'>Costly Brands and their Popularity</h1>",
                unsafe_allow_html=True
            )
            costly_brands['Average Price'] = costly_brands['Average Price'].apply(lambda x: f"₹{x:.2f}")
            costly_brands['Average Discount']=costly_brands['Average Discount'].apply(lambda x:f"{x}%")
            costly_brands['Popularity'] = costly_brands['Popularity'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(
            costly_brands,
            height=400,
            )
        c8, c9= st.columns(2)
        with c8:
            st.markdown(
                "<h1 style='font-size:20px;'>Budget Friendly Brands and their Popularity</h1>",
                unsafe_allow_html=True
            )
            budget_friendly_brands['Average Price'] = budget_friendly_brands['Average Price'].apply(lambda x: f"₹{x:.2f}")
            budget_friendly_brands['Average Discount']=budget_friendly_brands['Average Discount'].apply(lambda x:f"{x}%")
            budget_friendly_brands['Popularity'] = budget_friendly_brands['Popularity'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(
            budget_friendly_brands,
            height=400,
            )

        c10, c11=st.columns(2)
        with c10:
            st.markdown("<h3 style='font-size:20px;'>BRAND WISE PRODUCT PERCENTAGE GETTING OUT OF STOCK</h3>", 
                unsafe_allow_html=True)
            filtered['getting_outofstock_flag'] = filtered['availability'].apply(lambda x: 1 if x != 'In Stock' else 0)
            only_left=filtered.groupby(by='brand').agg(stock_per=('getting_outofstock_flag','mean')).reset_index()
            only_left['stock_per']=(only_left['stock_per']*100).round(2)
            only_left.columns=['Brand','Getting Out of Stock%']

            only_left['label'] = only_left['Getting Out of Stock%'].apply(lambda x: f"{x:.1f}%" if x > 5 else "")
            fig = px.pie(
                only_left,
                names='Brand',
                values='Getting Out of Stock%',
                hole=0.6
            )
            fig.update_traces(
                text=only_left['label'],
                textposition='inside',
                textinfo="text"
            )
            c10.plotly_chart(fig, width='stretch')
    with tab3:
        col1, col2, col3 = st.columns(3)
        flipkart_products['stock_flag'] = flipkart_products['availability'].apply(lambda x: 1 if x=='In Stock' else 0)
        with col1:
            in_stock = flipkart_products[flipkart_products['stock_flag']==1]['price']
            out_stock = flipkart_products[flipkart_products['stock_flag']==0]['price']
            t_stat, p_value = ttest_ind(in_stock, out_stock)
            st.markdown("<h3 style='font-size:20px;'>Effect of Price on Stock</h3>", unsafe_allow_html=True)
            st.write(f"T-statistic: {t_stat:.2f}, P-value: {p_value:.4f}")
            if p_value < 0.05:
                st.success("Price significantly affects stock availability (p < 0.05)")
            else:
                st.info("Price does not significantly affect stock availability (p ≥ 0.05)")

        with col2:
            in_stock = flipkart_products[flipkart_products['stock_flag']==1]['discount']
            out_stock = flipkart_products[flipkart_products['stock_flag']==0]['discount']
            t_stat, p_value = ttest_ind(in_stock, out_stock)
            st.markdown("<h3 style='font-size:20px;'>Effect of Discount on Stock</h3>", 
                unsafe_allow_html=True)
            st.write(f"T-statistic: {t_stat:.2f}, P-value: {p_value:.4f}")
            if p_value < 0.05:
                st.success("Discount significantly affects stock availability (p < 0.05)")
            else:
                st.info("Discount does not significantly affect stock availability (p ≥ 0.05)")

        with col3:
            in_stock = flipkart_products[flipkart_products['stock_flag']==1]['rating'].dropna()
            out_stock = flipkart_products[flipkart_products['stock_flag']==0]['rating'].dropna()
            t_stat, p_value = ttest_ind(in_stock, out_stock, nan_policy='omit')
            st.markdown("<h3 style='font-size:20px;'>Effect of Rating on Stock</h3>", 
                unsafe_allow_html=True)
            st.write(f"T-statistic: {t_stat:.2f}, P-value: {p_value:.4f}")
            if p_value < 0.05:
                st.success("Rating significantly affects stock availability (p < 0.05)")
            else:
                st.info("Rating does not significantly affect stock availability (p ≥ 0.05)")