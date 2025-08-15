# this app created by posit assistant
# based on prompt in assistant chat:
# I want to add a row of summary of metrics for each state
#    to my dashboard app sample-app.py, 
# based on the state selected in st.sidebar filter. 
# i want the number of hospitals, number of helipads, 
# and number of level 1 trauma centers, 
# number of beds for level 1 trauma centers.  
# assistant created this entire file with changes needed.
# new code is lines 46-83 (from what i can tell)
# works perfectly

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
    st.write('Filter by State')
    state = st.selectbox('State', options=('CA', 'TX', 'FL', 'NY', 'IL'))

@st.cache_data
def get_data(st_filter):
    state_tracts = tracts(st_filter, cb=True, 
                            year=2021, 
                            cache=True).to_crs(6571)
    state_tracts = state_tracts.to_crs('EPSG:4326')
    return(state_tracts)

state_tracts = get_data(state)

@st.cache_data
def load_data(state):
    trauma = gpd.read_file('trauma.geojson')
    trauma = trauma[trauma['STATE'] == state]
    return(trauma)

trauma = load_data(state)

# Calculate summary metrics
def calculate_metrics(trauma_df):
    total_hospitals = len(trauma_df)
    
    # Count helipads (Y = yes)
    total_helipads = (trauma_df['HELIPAD'] == 'Y').sum()
    
    # Count Level 1 trauma centers (including combinations with Level 1)
    level_1_centers = trauma_df['TRAUMA'].str.contains('LEVEL I', na=False).sum()
    
    # Calculate total beds for Level 1 trauma centers
    level_1_trauma_df = trauma_df[trauma_df['TRAUMA'].str.contains('LEVEL I', na=False)]
    level_1_beds = level_1_trauma_df['BEDS'].sum()
    
    return {
        'hospitals': total_hospitals,
        'helipads': total_helipads,
        'level_1_centers': level_1_centers,
        'level_1_beds': level_1_beds
    }

metrics = calculate_metrics(trauma)

# Display summary metrics
st.subheader(f'Summary Metrics for {state}')
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    st.metric("Total Hospitals", metrics['hospitals'])

with col_m2:
    st.metric("Hospitals with Helipads", metrics['helipads'])

with col_m3:
    st.metric("Level 1 Trauma Centers", metrics['level_1_centers'])

with col_m4:
    st.metric("Level 1 Trauma Center Beds", metrics['level_1_beds'])

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
        dist = tract_centroids.geometry.apply(lambda g: state_trauma.distance(g, align=False))
        min_dist = dist.min(axis='columns') / 1000
        hist_values = np.histogram(min_dist, bins=24, range=(0,24))[0]

with st.container():
    st.subheader('Min distance to trauma center from tract centroid')
    st.bar_chart(hist_values)