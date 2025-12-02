import streamlit as st
import time
from credentials import USER_CREDENTIALS

if "logged_in" not in st.session_state:
    st.session_state["logged_in"]=False
if "username" not in st.session_state:
    st.session_state['username']=""

def login_page():
    st.markdown(""" 
    <style>.block-container{
                padding-top:5rem;
                padding-bottom:2rem;
                max-width:600px
                } 
    </style> """, unsafe_allow_html=True)
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)

    username=st.text_input("👤 Username")
    password=st.text_input("🔑 Password", type="password")

    if st.button("Login"):
        if USER_CREDENTIALS.get(username)==password:
            st.session_state["logged_in"]=True
            st.session_state["username"]=username
            st.success("✅ Welcome Pooja Pravallika Anthati")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

    st.markdown("</div>", unsafe_allow_html=True)