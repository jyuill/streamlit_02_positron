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
    state = st.selectbox('State', options = ('CA', 'TX', 'FL', 'NY', 'IL'))

@st.cache_data
def get_data(st_filter):
    state_tracts = tracts(st_filter, cb=True, 
                            year = 2021, 
                            cache = True).to_crs(6571)
    state_tracts = state_tracts.to_crs('EPSG:4326')
    return(state_tracts)

state_tracts = get_data(state)

@st.cache_data
def load_data(state):
    trauma = gpd.read_file('trauma.geojson')
    trauma = trauma[trauma['STATE'] == state]
    return(trauma)

trauma = load_data(state)

col1, col2 = st.columns(2)

with st.container():
    with col1:
        st.subheader('Location of Trauma Hospitals')
        st.map(trauma)

    with col2:
        st.subheader('Raw data')
        st.write(trauma[['NAME', 'ADDRESS', 'CITY', 'STATE', 'ZIP']])
        state_tracts = state_tracts.to_crs(6571)
        trauma = trauma.to_crs(6571)
        state_buffer = gpd.GeoDataFrame(geometry=state_tracts.dissolve().buffer(100000))
        state_trauma = gpd.sjoin(trauma, state_buffer, how='inner')
        tract_centroids = state_tracts.centroid
        dist = tract_centroids.geometry.apply(lambda g: state_trauma.distance(g, align = False))
        min_dist = dist.min(axis = 'columns') / 1000
        hist_values = np.histogram(min_dist, bins=24, range = (0,24))[0]

with st.container():
    st.subheader('Min distance to trauma center from tract centroid')
    st.barchart(hist_values)