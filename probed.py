import pandas as pd
import geopandas as gpd
import streamlit as st
from streamlit_folium import folium_static
import folium
from folium import GeoJson
import matplotlib.pyplot as plt
import numpy as np

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
        return 'blue'
    elif deaths <= 50:
        return 'green'
    elif deaths <= 100:
        return 'yellow'
    elif deaths <= 150:
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
     <i style="background:blue; width:18px; height:18px; float:left; margin-right:8px;"></i> 0 Deaths<br>
     <i style="background:green; width:18px; height:18px; float:left; margin-right:8px;"></i> 1-50 Deaths<br>
     <i style="background:yellow; width:18px; height:18px; float:left; margin-right:8px;"></i> 51-100 Deaths<br>
     <i style="background:orange; width:18px; height:18px; float:left; margin-right:8px;"></i> 101-150 Deaths<br>
     <i style="background:red; width:18px; height:18px; float:left; margin-right:8px;"></i> 151+ Deaths<br>
     </div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# Display the map in Streamlit
st.title(f'District-wise Deaths for {selected_year}')
folium_static(m)  # Render the Folium map in Streamlit

# Add a color scale section above the "Complete Data"
st.subheader('Color Scale Used in the Map')
st.markdown("""
- <span style="color: blue;">**Blue**</span>: 0 Deaths
- <span style="color: green;">**Green**</span>: 1-50 Deaths
- <span style="color: yellow;">**Yellow**</span>: 51-100 Deaths
- <span style="color: orange;">**Orange**</span>: 101-150 Deaths
- <span style="color: red;">**Red**</span>: 151+ Deaths
""", unsafe_allow_html=True)

# Display the complete CSV table
st.write("### Complete Data Table")
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

# Create a line graph for Year vs Deaths for the selected district
st.subheader(f'Year vs Deaths for {selected_district}')
plt.figure(figsize=(10, 5))

# Extract the death values for the selected district
deaths_over_years = csv_data[csv_data['District'] == selected_district].iloc[0, 2:].values

# Plot column headers (years) from the CSV on X-axis and deaths on Y-axis
plt.plot(year_columns, deaths_over_years, marker='o')

# Add title and labels
plt.title(f'Deaths Over Years in {selected_district.title()}')
plt.xlabel('Year')
plt.ylabel('Deaths')
plt.xticks(rotation=45)  # Rotate X-axis labels for better readability
plt.grid(True)

# Render the plot in Streamlit
st.pyplot(plt)

# Add a section below "Color Scale Used in the Map"
st.subheader("District Insights")

# Yearly columns, excluding 'Total Deaths' if it exists
yearly_columns = ['2018-19', '2019-20', '2020-21', '2021-22', '2022-23', '2023-24']

# 1. District with the most deaths (based on total deaths across all years)
csv_data['Total Deaths'] = csv_data[yearly_columns].sum(axis=1)
district_most_deaths = csv_data.loc[csv_data['Total Deaths'].idxmax()]
st.write(f"**District with Most Deaths**: {district_most_deaths['District'].title()} with {district_most_deaths['Total Deaths']} deaths")

# 2. District with the least deaths
district_least_deaths = csv_data.loc[csv_data['Total Deaths'].idxmin()]
st.write(f"**District with Least Deaths**: {district_least_deaths['District'].title()} with {district_least_deaths['Total Deaths']} deaths")

# 3. District with the most increasing number of deaths
# Calculate the gradient of deaths year-over-year for each district
death_changes = csv_data[yearly_columns].diff(axis=1).sum(axis=1)
csv_data['Death Change'] = death_changes

district_most_increase = csv_data.loc[csv_data['Death Change'].idxmax()]
st.write(f"**District with the Most Increasing Deaths**: {district_most_increase['District'].title()}")

# Calculate average percentage increase for the district with the most increasing deaths
# Use the row corresponding to the district and access the yearly columns
percentage_increase = csv_data.loc[district_most_increase.name, yearly_columns].pct_change() * 100
average_percentage_increase = percentage_increase.mean()
st.write(f"**Average Percentage Increase in Deaths**: {average_percentage_increase:.2f}%")

# 4. District with the most decreasing number of deaths
district_most_decrease = csv_data.loc[csv_data['Death Change'].idxmin()]
st.write(f"**District with the Most Decreasing Deaths**: {district_most_decrease['District'].title()}")

# Calculate average percentage decrease for the district with the most decreasing deaths
# Use the row corresponding to the district and access the yearly columns
percentage_decrease = csv_data.loc[district_most_decrease.name, yearly_columns].pct_change() * 100
average_percentage_decrease = percentage_decrease.mean()
st.write(f"**Average Percentage Decrease in Deaths**: {average_percentage_decrease:.2f}%")
