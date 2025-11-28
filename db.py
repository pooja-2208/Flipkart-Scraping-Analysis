import streamlit as st
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv("encrypted.env")

username=os.getenv("azure_username")
password=os.getenv("azure_password")
server=os.getenv("azure_server")
database=os.getenv("azure_db")

@st.cache_resource
def get_engine():
    conn_str=f"mssql+pymssql://{username}:{password}@{server}:1433/{database}"
    return create_engine(conn_str)