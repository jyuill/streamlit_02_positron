# Enhanced trauma hospital dashboard with full state list and improved bar chart
# Enhancements:
# 1. State filter now includes all 51 states/territories in the dataset
# 2. Bar chart includes mean and median reference lines with labels
# 3. Dynamic x-axis scaling based on actual data distribution
# 4. Added collapsible insights section with natural language takeaways

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from pygris import tracts
import geopandas as gpd

st.set_page_config(layout="wide")

# Custom CSS to make metric labels larger and more prominent
st.markdown("""
<style>
.metric-container {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    text-align: center;
    margin: 0.5rem 0;
}
.metric-label {
    font-size: 1.2rem;
    font-weight: bold;
    color: #262730;
    margin-bottom: 0.5rem;
}
.metric-value {
    font-size: 2.5rem;
    font-weight: bold;
    color: #ff6b6b;
}
.stat-label {
    font-size: 1.4rem;
    font-weight: bold;
    color: #262730;
    margin-bottom: 0.3rem;
}
.stat-value {
    font-size: 3rem;
    font-weight: bold;
    color: #4dabf7;
}
.insights-content {
    font-size: 1.2rem;
    line-height: 1.7;
}
.insights-bullet {
    font-size: 1.15rem;
    margin-bottom: 0.8rem;
    line-height: 1.6;
}
.insights-bullet strong {
    color: #1f77b4;
    font-weight: 700;
}
.custom-caption {
    font-size: 1.2rem;
    font-style: italic;
    color: #777;
}
</style>
""", unsafe_allow_html=True)

st.title("US Trauma Hospital Locations")
#st.caption("A sample Streamlit app to visualize US trauma hospital locations. Based on Posit tutorial, with extensive help from Positron AI assistant.", fontsize="medium")
st.markdown('<div class="custom-caption">An example Streamlit app to visualize US trauma hospital locations. Based on Posit tutorial, with extensive help from Positron AI assistant.</div>', unsafe_allow_html=True)

# Load all trauma data to get unique states
@st.cache_data
def load_all_trauma_data():
    trauma_all = gpd.read_file('trauma.geojson')
    return trauma_all

# Get available states for the selectbox
trauma_all = load_all_trauma_data()
available_states = sorted(trauma_all['STATE'].unique())

with st.sidebar:
    st.write('## Select State of Interest')
    state = st.selectbox('State', options=available_states, index=available_states.index('AK'))

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

# Function to generate insights based on distance statistics
def generate_insights(state, mean_dist, median_dist, max_dist, metrics):
    insights = []
    
    # Accessibility assessment based on mean distance
    if mean_dist <= 10:
        insights.append(f"<strong>Excellent Access</strong>: {state} has excellent trauma care accessibility with an average distance of {mean_dist:.1f} km to the nearest trauma center.")
    elif mean_dist <= 25:
        insights.append(f"<strong>Good Access</strong>: {state} provides reasonable trauma care access, with most residents within {mean_dist:.1f} km of emergency care.")
    elif mean_dist <= 50:
        insights.append(f"<strong>Moderate Access</strong>: {state} has moderate trauma care accessibility, with residents traveling an average of {mean_dist:.1f} km to reach care.")
    else:
        insights.append(f"<strong>Limited Access</strong>: {state} faces accessibility challenges, with residents traveling {mean_dist:.1f} km on average to reach trauma care.")
    
    # Distribution analysis (mean vs median comparison)
    diff_percentage = abs(mean_dist - median_dist) / median_dist * 100
    if diff_percentage < 10:
        insights.append(f"<strong>Even Distribution</strong>: The mean ({mean_dist:.1f} km) and median ({median_dist:.1f} km) distances are very close, indicating fairly even trauma center distribution across the state.")
    elif mean_dist > median_dist * 1.2:
        insights.append(f"<strong>Geographic Disparities</strong>: Some areas face significantly longer travel distances (mean {mean_dist:.1f} km vs median {median_dist:.1f} km), suggesting rural or remote areas with limited access.")
    else:
        insights.append(f"<strong>Slight Variation</strong>: There's some variation in access across the state, with mean distance ({mean_dist:.1f} km) slightly different from median ({median_dist:.1f} km).")
    
    # Maximum distance analysis
    if max_dist > 100:
        insights.append(f"<strong>Remote Areas</strong>: Some residents face extreme distances up to {max_dist:.1f} km to reach trauma care, likely in very rural or isolated regions.")
    elif max_dist > 50:
        insights.append(f"<strong>Rural Challenges</strong>: The maximum distance of {max_dist:.1f} km indicates some rural areas have limited trauma care access.")
    else:
        insights.append(f"<strong>Reasonable Coverage</strong>: Even the most remote areas are within {max_dist:.1f} km of trauma care, showing good statewide coverage.")
    
    # Helipad analysis
    helipad_percentage = (metrics['helipads'] / metrics['hospitals']) * 100 if metrics['hospitals'] > 0 else 0
    if helipad_percentage > 50:
        insights.append(f"<strong>Air Transport Ready</strong>: {helipad_percentage:.0f}% of trauma hospitals have helipads, providing excellent air transport capabilities for critical patients from remote areas.")
    elif helipad_percentage > 25:
        insights.append(f"<strong>Moderate Air Access</strong>: {helipad_percentage:.0f}% of hospitals have helipads, offering some air transport options for emergency cases.")
    else:
        insights.append(f"<strong>Limited Air Transport</strong>: Only {helipad_percentage:.0f}% of hospitals have helipads, which may impact rapid transport from distant locations.")
    
    # Level 1 trauma center assessment
    level1_percentage = (metrics['level_1_centers'] / metrics['hospitals']) * 100 if metrics['hospitals'] > 0 else 0
    if metrics['level_1_centers'] == 0:
        insights.append(f"<strong>No Level 1 Centers</strong>: {state} has no Level 1 trauma centers, meaning the most critical cases may need transfer to neighboring states.")
    elif level1_percentage > 25:
        insights.append(f"<strong>Strong Critical Care</strong>: {metrics['level_1_centers']} Level 1 trauma centers ({level1_percentage:.0f}% of hospitals) provide excellent critical care capacity.")
    else:
        insights.append(f"<strong>Limited Level 1 Care</strong>: {metrics['level_1_centers']} Level 1 trauma center(s) serve the entire state, which may strain resources during major incidents.")
    
    return insights

metrics = calculate_metrics(trauma)

# Display summary metrics with enhanced styling
st.markdown(f"# 📊 Summary Metrics for {state}")
st.markdown("---")  # Add a horizontal line for visual separation

col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-label">Total Hospitals</div>
        <div class="metric-value">{metrics['hospitals']}</div>
    </div>
    """, unsafe_allow_html=True)

with col_m2:
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-label">Hospitals with Helipads</div>
        <div class="metric-value">{metrics['helipads']}</div>
    </div>
    """, unsafe_allow_html=True)

with col_m3:
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-label">Level 1 Trauma Centers</div>
        <div class="metric-value">{metrics['level_1_centers']}</div>
    </div>
    """, unsafe_allow_html=True)

with col_m4:
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-label">Level 1 Trauma Center Beds</div>
        <div class="metric-value">{metrics['level_1_beds']}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")  # Add another horizontal line after metrics

col1, col2 = st.columns(2)

with st.container():
    with col1:
        st.subheader('Location of Trauma Hospitals')
        st.map(trauma)

    with col2:
        st.subheader('Hospital Name and Address')
        st.dataframe(trauma[['NAME', 'ADDRESS', 'CITY', 'STATE', 'ZIP']], height=500)
        
        # Calculate distances for histogram
        state_tracts = state_tracts.to_crs(6571)
        trauma = trauma.to_crs(6571)
        state_buffer = gpd.GeoDataFrame(geometry=state_tracts.dissolve().buffer(100000))
        state_trauma = gpd.sjoin(trauma, state_buffer, how='inner')
        tract_centroids = state_tracts.centroid
        dist = tract_centroids.geometry.apply(lambda g: state_trauma.distance(g, align=False))
        min_dist = dist.min(axis='columns') / 1000

# Calculate statistics for reference lines
mean_distance = min_dist.mean()
median_distance = min_dist.median()
max_distance = min_dist.max()

with st.container():
    st.subheader('Min distance to trauma center from tract centroid')
    
    # Create the bar chart with matplotlib for better customization
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Dynamic x-axis scaling based on actual data
    # Add some padding (10% of range) to make the chart look better
    x_min = 0
    x_max = max_distance * 1.1  # Add 10% padding to max distance
    
    # Create dynamic bins based on the data range
    # Use reasonable bin width (1 km for smaller ranges, adjust for larger ranges)
    if x_max <= 20:
        bin_width = 0.5  # 0.5 km bins for small ranges
    elif x_max <= 50:
        bin_width = 1    # 1 km bins for medium ranges
    else:
        bin_width = 2    # 2 km bins for large ranges
    
    bins = np.arange(x_min, x_max + bin_width, bin_width)
    
    # Create the histogram
    ax.hist(min_dist, bins=bins, alpha=0.7, color='steelblue', edgecolor='black', linewidth=0.5)
    
    # Add mean and median reference lines
    ax.axvline(mean_distance, color='red', linestyle='--', linewidth=2, alpha=0.8)
    ax.axvline(median_distance, color='orange', linestyle='--', linewidth=2, alpha=0.8)
    
    # Add labels for the reference lines
    # Position labels dynamically based on chart dimensions
    y_max = ax.get_ylim()[1]
    label_offset = x_max * 0.01  # 1% of x-range for label positioning
    
    ax.text(mean_distance + label_offset, y_max * 0.9, 
            f'Mean: {mean_distance:.1f} km', 
            rotation=0, color='red', fontweight='bold', fontsize=10)
    ax.text(median_distance + label_offset, y_max * 0.8, 
            f'Median: {median_distance:.1f} km', 
            rotation=0, color='orange', fontweight='bold', fontsize=10)
    
    # Customize the chart
    ax.set_xlabel('Distance (km)', fontsize=12)
    ax.set_ylabel('Number of Census Tracts', fontsize=12)
    ax.set_title(f'Distribution of Minimum Distance to Trauma Centers - {state}', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(x_min, x_max)  # Dynamic x-axis limit based on data
    
    # Display the plot in Streamlit
    st.pyplot(fig)
    
    # Display the statistics below the chart with enhanced styling
    st.markdown(f"# 📈 Distance Statistics for {state}")
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="stat-label">Mean Distance</div>
            <div class="stat-value">{mean_distance:.1f} km</div>
        </div>
        """, unsafe_allow_html=True)
    with col_s2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="stat-label">Median Distance</div>
            <div class="stat-value">{median_distance:.1f} km</div>
        </div>
        """, unsafe_allow_html=True)
    with col_s3:
        st.markdown(f"""
        <div class="metric-container">
            <div class="stat-label">Maximum Distance</div>
            <div class="stat-value">{max_distance:.1f} km</div>
        </div>
        """, unsafe_allow_html=True)

    # Add collapsible insights section with larger title
    st.markdown("---")
    st.markdown("## 📋 Key Insights & Takeaways")
    
    with st.expander("Click to view detailed analysis and insights", expanded=False):
        st.markdown('<div class="insights-content">', unsafe_allow_html=True)
        st.markdown("### What do these numbers tell us about trauma care access?")
        
        insights = generate_insights(state, mean_distance, median_distance, max_distance, metrics)
        
        for insight in insights:
            st.markdown(f'<div class="insights-bullet">• {insight}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("*These insights are based on distance analysis and hospital infrastructure data. Actual emergency response times may vary due to traffic, weather, and other factors.*")
        st.markdown('</div>', unsafe_allow_html=True)