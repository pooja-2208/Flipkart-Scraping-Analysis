import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import statsmodels
from db import get_engine
from scipy import stats

def render():
    engine=get_engine()
    flipkart_products=pd.read_sql("SELECT * FROM scraped_cleandata", engine)

    st.set_page_config(layout='wide')
    st.title("👥 CUSTOMER SATISFACTION ANALYSIS")

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
            <div style="font-size: 16px; font-weight: 700;">
                {value}
            </div>
        </div>
        """, unsafe_allow_html=True
        )

    col1, col2, col3, col4=st.columns(4)
    with col1:
        kpi_box("Average Rating",f"⭐{round(filtered['rating'].mean())}")

    max_rating_index = filtered['rating'].idxmax()
    toprated_product = filtered.loc[max_rating_index]
    with col2:
        kpi_box("Product with High Average Rating",f"{toprated_product['product_name']} : ⭐{toprated_product['rating']}")

    max_ratingcount_index = filtered['number_of_ratings'].idxmax()
    top_product = filtered.loc[max_ratingcount_index]
    with col3:
        kpi_box("Popular Product", f"{top_product['product_name']} with {int(top_product['number_of_ratings'])} ratings")

    high_rated_count = (filtered['rating'] >= 4).sum()
    total_products = filtered.shape[0]
    percentage_high_rated = (high_rated_count / total_products) * 100
    with col4:
        kpi_box("Products with Average Rating >=4",f"{percentage_high_rated:.2f}%")
    # Charts
    st.markdown('<h2 style="font-size:35px;">📈 Advanced Analytics</h2>', unsafe_allow_html=True)
    tab1, tab2, tab3  = st.tabs(
    ["Distribution Analysis", "Rating Analysis", "Statistical Analysis"] )

    with tab1:
        st.subheader("Product Rating Distribution Analysis")
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.histogram(
            filtered,
            x="rating",
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
                y="rating",           
            )
        c2.plotly_chart(fig2, width='stretch')

        st.subheader("Product Popularity Distribution Analysis")
        c3, c4=st.columns(2)
        with c3:
            fig1 = px.histogram(
            filtered.dropna(subset=['number_of_ratings']),
            x="number_of_ratings",
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
                filtered.dropna(subset=['number_of_ratings']),
                y="number_of_ratings",           
            )
        c4.plotly_chart(fig2, width='stretch')

    with tab2:
        brand_avg_rating = filtered.groupby('brand')['rating'].mean().reset_index()
        fig = px.bar(
            brand_avg_rating,
            x='brand',
            y='rating',
            title='BRAND WISE AVERAGE RATING',
            labels={'rating':'Average Rating', 'brand':'Brand'},
            text='rating',
            color='rating',
            color_continuous_scale='blues'
            )
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, width='stretch')
    
        c5, c6=st.columns(2)
        with c5:
            fig1 = px.scatter(
                    filtered.dropna(subset=['rating']),
                    x='discount',        
                    y='rating', 
                    size='rating',                  
                    hover_data=['discount', 'rating'],  
                    title='DISCOUNT VS RATING',
                    color='rating',
                    color_continuous_scale ='Cividis',
                    trendline='ols'
                    )

            fig1.update_layout(
                xaxis_title='Discount (%)',
                yaxis_title='Rating'
            )
            c5.plotly_chart(fig1, width='stretch')

        with c6:
            fig2 = px.scatter(
                    filtered.dropna(subset=['rating']),
                    x='price',        
                    y='rating', 
                    size='rating',                  
                    hover_data=['price', 'rating'],  
                    title='PRICE VS RATING',
                    color='rating',
                    color_continuous_scale ='plasma',
                    trendline='ols'
                    )
            
            fig2.update_layout(
                xaxis_title='Price',
                yaxis_title='Rating'
            )
            c6.plotly_chart(fig2, width='stretch')
    
    with tab3:
        c7, c8=st.columns(2)
        with c7:
            groups = [group['rating'].values for name, group in flipkart_products.dropna(subset=['rating']).groupby('brand')]
            f_stat, p_value = stats.f_oneway(*groups)
            st.markdown("<h3 style='font-size:20px;'>Statistical Test: Effect of Brand on Rating</h3>", 
                unsafe_allow_html=True)
            st.write(f"F-statistic: {f_stat:.2f}")
            st.write(f"P-value: {p_value:.4f}")
            if p_value < 0.05:
                st.success("The effect of brand on rating is **statistically significant** (p < 0.05).")
            else:
                st.info("There is no statistically significant evidence that brand affects rating (p ≥ 0.05).")

        with c8:
            groups2 = [group['rating'].values for name, group in flipkart_products.dropna(subset=['rating']).groupby('availability')]
            f_stat, p_value = stats.f_oneway(*groups2)
            st.markdown("<h3 style='font-size:20px;'>Statistical Test: Effect of Availability on Rating</h3>", 
                unsafe_allow_html=True)
            st.write(f"F-statistic: {f_stat:.2f}")
            st.write(f"P-value: {p_value:.4f}")
            if p_value < 0.05:
                st.success("The effect of availability on rating is **statistically significant** (p < 0.05).")
            else:
                st.info("There is no statistically significant evidence that availability affects rating (p ≥ 0.05).")