import pandas as pd
import geopandas as gpd
import streamlit as st
from streamlit_folium import folium_static
import folium
from folium import GeoJson

# Load the CSV data
csv_file_path = 'data.csv'  # Adjust the path to your CSV file
csv_data = pd.read_csv(csv_file_path)

# Load the GeoJSON data
geojson_file_path = 'up_districts.geojson'  # Adjust the path to your GeoJSON file
geojson_data = gpd.read_file(geojson_file_path)

# Standardize district names to lower case and strip whitespace
csv_data['District'] = csv_data['District'].str.lower().str.strip()
geojson_data['district'] = geojson_data['district'].str.lower().str.strip()

# Create a Streamlit dropdown for selecting the year
year_columns = csv_data.columns[2:]  # Get columns for years
selected_year = st.selectbox('Select Year', year_columns)

# Prepare filtered data for the selected year
filtered_data = csv_data[['District', selected_year]].copy()
filtered_data.rename(columns={selected_year: 'Deaths'}, inplace=True)

# Merge the filtered data with the GeoJSON data
merged_data = geojson_data.merge(filtered_data, left_on='district', right_on='District', how='left')

# Fill NaN values in the Deaths column with 0
merged_data['Deaths'] = merged_data['Deaths'].fillna(0)

# Create a Folium map
m = folium.Map(location=[merged_data.geometry.centroid.y.mean(), merged_data.geometry.centroid.x.mean()], zoom_start=7)

# Define a color scale
def color_scale(deaths):
    if deaths == 0:
        return 'green'
    elif deaths < 10:
        return 'yellow'
    elif deaths < 50:
        return 'orange'
    else:
        return 'red'

# Add GeoJSON to the map with color coding and tooltips
GeoJson(
    merged_data,
    style_function=lambda feature: {
        'fillColor': color_scale(feature['properties']['Deaths']),
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.7,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['district', 'Deaths'],
        aliases=['District:', 'Deaths:'],
        localize=True,
        sticky=True
    )
).add_to(m)

# Create a legend for the map
legend_html = """
     <div style="position: fixed; 
     bottom: 50px; left: 50px; width: 150px; height: 150px; 
     border:2px solid grey; z-index:9999; font-size:14px;
     background-color:white; padding: 10px;">
     <strong>Legend</strong><br>
     <i style="background:green; width:18px; height:18px; float:left; margin-right:8px;"></i> 0 Deaths<br>
     <i style="background:yellow; width:18px; height:18px; float:left; margin-right:8px;"></i> 1-9 Deaths<br>
     <i style="background:orange; width:18px; height:18px; float:left; margin-right:8px;"></i> 10-49 Deaths<br>
     <i style="background:red; width:18px; height:18px; float:left; margin-right:8px;"></i> 50+ Deaths<br>
     </div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# Display the map in Streamlit
st.title(f'District-wise Deaths for {selected_year}')
folium_static(m)  # Render the Folium map in Streamlit

# Add a color scale section above the "Complete Data"
st.subheader('Color Scale Used in the Map')
st.markdown("""
- <span style="color: green;">**Green**</span>: 0 Deaths
- <span style="color: yellow;">**Yellow**</span>: 1-9 Deaths
- <span style="color: orange;">**Orange**</span>: 10-49 Deaths
- <span style="color: red;">**Red**</span>: 50+ Deaths
""", unsafe_allow_html=True)

# Display the complete CSV data
st.subheader('Complete Data')
st.dataframe(csv_data)

# Comparative Data Section with Statistical Metrics
selected_district = st.selectbox('Select District for Comparison', csv_data['District'].unique())
comparative_data = csv_data[csv_data['District'] == selected_district].set_index('District').T

# Calculate statistics
mean_deaths = comparative_data.mean().values[0]
std_deviation = comparative_data.std().values[0]
min_deaths = comparative_data.min().values[0]
max_deaths = comparative_data.max().values[0]

# Show comparative data and statistics
st.subheader(f'Comparative Death Data for {selected_district}')
st.dataframe(comparative_data)

# Display statistics
st.write(f"**Mean Deaths**: {mean_deaths:.2f}")
st.write(f"**Standard Deviation**: {std_deviation:.2f}")
st.write(f"**Minimum Deaths**: {min_deaths}")
st.write(f"**Maximum Deaths**: {max_deaths}")
