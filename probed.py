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

# Define a new color scale with maroon to pale cream
def color_scale(deaths):
    if deaths == 0:
        return '#800000'  # Maroon
    elif deaths <= 50:
        return '#FF0000'  # Red
    elif deaths <= 100:
        return '#FFA500'  # Orange
    elif deaths <= 150:
        return '#FFFF00'  # Yellow
    else:
        return '#CFBD99'  # Pale Cream

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
     <i style="background:#800000; width:18px; height:18px; float:left; margin-right:8px;"></i> 0 Deaths<br>
     <i style="background:#FF0000; width:18px; height:18px; float:left; margin-right:8px;"></i> 1-50 Deaths<br>
     <i style="background:#FFA500; width:18px; height:18px; float:left; margin-right:8px;"></i> 51-100 Deaths<br>
     <i style="background:#FFFF00; width:18px; height:18px; float:left; margin-right:8px;"></i> 101-150 Deaths<br>
     <i style="background:#CFBD99; width:18px; height:18px; float:left; margin-right:8px;"></i> 151+ Deaths<br>
     </div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# Display the map in Streamlit
st.title(f'District-wise Deaths for {selected_year}')
folium_static(m)  # Render the Folium map in Streamlit

# Add a color scale section above the "Complete Data"
st.subheader('Color Scale Used in the Map')
st.markdown("""
- <span style="color: #800000;">**Maroon**</span>: 0 Deaths
- <span style="color: #FF0000;">**Red**</span>: 1-50 Deaths
- <span style="color: #FFA500;">**Orange**</span>: 51-100 Deaths
- <span style="color: #FFFF00;">**Yellow**</span>: 101-150 Deaths
- <span style="color: #CFBD99;">**Pale Cream**</span>: 151+ Deaths
""", unsafe_allow_html=True)

# Display the complete CSV table
st.write("### Complete Data Table")
st.dataframe(csv_data)

# Percentage contribution of each district for the selected year
st.subheader(f"Percentage Contribution of Each District in '{selected_year}'")
total_deaths_in_year = csv_data[selected_year].sum()
csv_data['Percentage Contribution'] = (csv_data[selected_year] / total_deaths_in_year) * 100

# Display percentage contribution table
st.dataframe(csv_data[['District', selected_year, 'Percentage Contribution']])

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
st.dataframe(comparative_data.astype(int))  # Convert to integers for display

# Display statistics in integer form
st.write(f"**Mean Deaths**: {int(mean_deaths)}")  # Convert to integer
st.write(f"**Standard Deviation**: {int(std_deviation)}")  # Convert to integer
st.write(f"**Minimum Deaths**: {int(min_deaths)}")  # Convert to integer
st.write(f"**Maximum Deaths**: {int(max_deaths)}")  # Convert to integer

# Create a line graph for Year vs Deaths for the selected district
st.subheader(f'Year vs Deaths for {selected_district}')
plt.figure(figsize=(10, 5))

# Extract the death values for the selected district excluding the last column
deaths_over_years = csv_data[csv_data['District'] == selected_district].iloc[0, 2:8].values  # Adjust index to ensure it selects only the year columns

# Plot column headers (years) from the CSV on X-axis and deaths on Y-axis
plt.plot(year_columns[:-1], deaths_over_years, marker='o')  # Exclude the last year from the x-axis

# Show values at each point
for i, txt in enumerate(deaths_over_years):
    plt.annotate(txt, (year_columns[i], deaths_over_years[i]), textcoords="offset points", xytext=(0,10), ha='center')

# Add title and labels
plt.title(f'Deaths Over Years in {selected_district.title()}')
plt.xlabel('Year')
plt.ylabel('Deaths')
plt.xticks(rotation=45)  # Rotate X-axis labels for better readability
plt.grid(True)

# Render the plot in Streamlit
st.pyplot(plt)

# Add pie chart showing contribution of selected district
st.subheader(f'Contribution of {selected_district.title()} in {selected_year}')
selected_district_deaths = csv_data[csv_data['District'] == selected_district][selected_year].values[0]
district_contributions = [selected_district_deaths, total_deaths_in_year - selected_district_deaths]
plt.figure(figsize=(6, 6))
plt.pie(district_contributions, labels=[selected_district.title(), 'Rest of State'], autopct='%1.1f%%', startangle=90)
plt.title(f'Contribution of {selected_district.title()} in {selected_year}')
st.pyplot(plt)

# Add "State Insight" section (formerly District Insights)
st.subheader("State Insight")

# Yearly columns, excluding '2018-19 till 2023-24' column
yearly_columns = ['2018-19', '2019-20', '2020-21', '2021-22', '2022-23', '2023-24']

# 1. District with the most deaths (based on total deaths across all years)
csv_data['Total Deaths'] = csv_data[yearly_columns].sum(axis=1)
district_most_deaths = csv_data.loc[csv_data['Total Deaths'].idxmax()]
st.write(f"**District with Most Deaths**: {district_most_deaths['District'].title()} with {district_most_deaths['Total Deaths']} deaths")

# 2. District with the least deaths
district_least_deaths = csv_data.loc[csv_data['Total Deaths'].idxmin()]
st.write(f"**District with Least Deaths**: {district_least_deaths['District'].title()} with {district_least_deaths['Total Deaths']} deaths")

# 3. District with the most increasing number of deaths
death_changes = csv_data[yearly_columns].diff(axis=1).sum(axis=1)
csv_data['Death Change'] = death_changes

district_most_increase = csv_data.loc[csv_data['Death Change'].idxmax()]
st.write(f"**District with the Most Increasing Deaths**: {district_most_increase['District'].title()}")

# 4. District with the most decreasing number of deaths
district_most_decrease = csv_data.loc[csv_data['Death Change'].idxmin()]
st.write(f"**District with the Most Decreasing Deaths**: {district_most_decrease['District'].title()}")
