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

# Create a Streamlit dropdown for selecting the year or total
year_columns = csv_data.columns[2:-1]  # Exclude 'Total' column from year selection
year_columns_with_total = year_columns.tolist() + ['Total']  # Add 'Total' to the list
selected_year = st.selectbox('Select Year or Total', year_columns_with_total)

# Prepare filtered data for the selected year or total
if selected_year == 'Total':
    filtered_data = csv_data[['District', 'Total']].copy()
    filtered_data.rename(columns={'Total': 'Deaths'}, inplace=True)
else:
    filtered_data = csv_data[['District', selected_year]].copy()
    filtered_data.rename(columns={selected_year: 'Deaths'}, inplace=True)

# Merge the filtered data with the GeoJSON data
merged_data = geojson_data.merge(filtered_data, left_on='district', right_on='District', how='left')

# Fill NaN values in the Deaths column with 0
merged_data['Deaths'] = merged_data['Deaths'].fillna(0)

# Create a Folium map
m = folium.Map(location=[merged_data.geometry.centroid.y.mean(), merged_data.geometry.centroid.x.mean()], zoom_start=7)

# Define a color scale with 5 shades of red
def color_scale(deaths):
    if deaths == 0:
        return 'white'
    elif deaths <= 50:
        return '#ffcccc'  # Light red
    elif deaths <= 100:
        return '#ff9999'  # Medium red
    elif deaths <= 150:
        return '#ff6666'  # Darker red
    else:
        return '#cc0000'  # Deep red

# Add GeoJson to the map with color coding and tooltips
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
     <i style="background:white; width:18px; height:18px; float:left; margin-right:8px;"></i> 0 Deaths<br>
     <i style="background:#ffcccc; width:18px; height:18px; float:left; margin-right:8px;"></i> 1-50 Deaths<br>
     <i style="background:#ff9999; width:18px; height:18px; float:left; margin-right:8px;"></i> 51-100 Deaths<br>
     <i style="background:#ff6666; width:18px; height:18px; float:left; margin-right:8px;"></i> 101-150 Deaths<br>
     <i style="background:#cc0000; width:18px; height:18px; float:left; margin-right:8px;"></i> 151+ Deaths<br>
     </div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# Display the map in Streamlit
st.title(f'District-wise Deaths for {selected_year}')
folium_static(m)  # Render the Folium map in Streamlit

# Add a color scale section above the "Complete Data"
st.subheader('Color Scale Used in the Map')
st.markdown("""
- <span style="color: white;">**White**</span>: 0 Deaths
- <span style="color: #ffcccc;">**Light Red**</span>: 1-50 Deaths
- <span style="color: #ff9999;">**Medium Red**</span>: 51-100 Deaths
- <span style="color: #ff6666;">**Darker Red**</span>: 101-150 Deaths
- <span style="color: #cc0000;">**Deep Red**</span>: 151+ Deaths
""", unsafe_allow_html=True)

# Display the complete CSV table
st.write("### Complete Data Table")
st.dataframe(csv_data)

# Percentage contribution of each district in the selected year
st.subheader(f'Percentage Contribution of Each District in {selected_year}')
total_deaths_in_year = csv_data[selected_year].sum() if selected_year != 'Total' else csv_data['Total'].sum()
percentage_contributions = (csv_data[selected_year] / total_deaths_in_year * 100).fillna(0)
contribution_table = pd.DataFrame({
    'District': csv_data['District'],
    'Percentage Contribution (%)': percentage_contributions
})
st.dataframe(contribution_table)

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

# Create a line graph for Year vs Deaths for the selected district and total deaths in the state
st.subheader(f'Year vs Deaths for {selected_district} vs Total State Deaths')
plt.figure(figsize=(10, 5))

# Extract the death values for the selected district, excluding 'Total'
deaths_over_years = csv_data[csv_data['District'] == selected_district].iloc[0, 2:-1].values

# Compute total deaths for the entire state for each year (sum across districts)
state_total_deaths = csv_data[year_columns].sum()

# Plot district deaths
plt.plot(year_columns, deaths_over_years, marker='o', label=f'{selected_district.title()} Deaths')

# Plot state total deaths
plt.plot(year_columns, state_total_deaths.values, marker='o', label='Total State Deaths', linestyle='--', color='red')

# Annotate values for the selected district deaths
for i, value in enumerate(deaths_over_years):
    plt.text(i, value, f'{value:.0f}', ha='center', va='bottom')

# Annotate values for the state total deaths
for i, value in enumerate(state_total_deaths):
    plt.text(i, value, f'{value:.0f}', ha='center', va='bottom')

# Add title and labels
plt.title(f'Deaths Over Years in {selected_district.title()} vs Total State')
plt.xlabel('Year')
plt.ylabel('Deaths')
plt.xticks(rotation=45)  # Rotate X-axis labels for better readability
plt.grid(True)
plt.legend()

# Render the plot in Streamlit
st.pyplot(plt)

# Add a section below "Color Scale Used in the Map"
st.subheader("District Insights")

# 1. District with the most deaths (based on total deaths across all years)
csv_data['Total Deaths'] = csv_data[year_columns].sum(axis=1)
district_most_deaths = csv_data.loc[csv_data['Total Deaths'].idxmax()]
st.write(f"**District with Most Deaths**: {district_most_deaths['District'].title()} with {district_most_deaths['Total Deaths']} deaths")

# 2. District with the least deaths
district_least_deaths = csv_data.loc[csv_data['Total Deaths'].idxmin()]
st.write(f"**District with Least Deaths**: {district_least_deaths['District'].title()} with {district_least_deaths['Total Deaths']} deaths")

# 3. District with the most increasing number of deaths
# Calculate the gradient of deaths year-over-year for each district
death_changes = csv_data[year_columns].diff(axis=1).sum(axis=1)
csv_data['Death Change'] = death_changes

district_most_increase = csv_data.loc[csv_data['Death Change'].idxmax()]
st.write(f"**District with the Most Increasing Deaths**: {district_most_increase['District'].title()}")

# 4. District with the most decreasing number of deaths
district_most_decrease = csv_data.loc[csv_data['Death Change'].idxmin()]
st.write(f"**District with the Most Decreasing Deaths**: {district_most_decrease['District'].title()}")

# Pie chart for contribution of the selected district in the selected year
total_deaths_in_year = csv_data[selected_year].sum()
selected_district_deaths = csv_data[csv_data['District'] == selected_district][selected_year].values[0]

# Prepare data for pie chart
pie_data = [selected_district_deaths, total_deaths_in_year - selected_district_deaths]
labels = [selected_district.title(), 'Other Districts']
colors = ['lightblue', 'lightgrey']

# Create pie chart
plt.figure(figsize=(7, 7))
plt.pie(pie_data, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
plt.title(f'Contribution of {selected_district.title()} in {selected_year}')
st.pyplot(plt)