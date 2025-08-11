import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from pygris import tracts
import geopandas as gpd

st.set_page_config(layout="wide")
st.title("US Trauma Hospital Locations")
st.caption("A sample Streamlit app to visualize US trauma hospital locations.")

with st.sidebar:
    st.write('Filte state')
    state = st.selectbox('State', options = ['All', 'CA', 'TX', 'FL', 'NY', 'IL'])

@st.cache_data
def get_data(st_filter):
    state_tracts = tracts(st_filter, ch=True, year = 2021, cache = True).to_crs(6571)
    state_tracts = state_tracts.to_crs('EPSG:4326')
    return state_tracts

state_tracts = get_data(state)
