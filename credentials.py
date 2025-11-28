import os
from dotenv import load_dotenv

load_dotenv("streamlit.env")

USER_CREDENTIALS={
    os.getenv("streamlit_user"): os.getenv("streamlit_password")
}
print(USER_CREDENTIALS)