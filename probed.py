import pandas as pd
import geopandas as gpd
import streamlit as st
from streamlit_folium import folium_static
import folium
from folium import GeoJson
import matplotlib.pyplot as plt
import numpy as np

csv_file_path = 'data.csv'
csv_data = pd.read_csv(csv_file_path)

geojson_file_path = 'up_districts.geojson'
geojson_data = gpd.read_file(geojson_file_path)

csv_data['District'] = csv_data['District'].str.lower().str.strip()
geojson_data['district'] = geojson_data['district'].str.lower().str.strip()

year_columns = csv_data.columns[2:]
selected_year = st.selectbox('Select Year', year_columns)

filtered_data = csv_data[['District', selected_year]].copy()
filtered_data.rename(columns={selected_year: 'Deaths'}, inplace=True)

merged_data = geojson_data.merge(filtered_data, left_on='district', right_on='District', how='left')

merged_data['Deaths'] = merged_data['Deaths'].fillna(0)

m = folium.Map(location=[merged_data.geometry.centroid.y.mean(), merged_data.geometry.centroid.x.mean()], zoom_start=7)

def color_scale(deaths):
    if deaths == 0:
        return '#CFBD99'
    elif deaths <= 50:
        return '#FFFF00'
    elif deaths <= 100:
        return '#FFA500'
    elif deaths <= 150:
        return '#FF0000'
    else:
        return '#800000'

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

st.title(f'District-wise Deaths for {selected_year}')
folium_static(m)  

st.subheader('Color Scale Used in the Map')
st.markdown("""
- <span style="color: #800000;">**Maroon**</span>: 151+ Deaths
- <span style="color: #FF0000;">**Red**</span>: 101-150 Deaths
- <span style="color: #FFA500;">**Orange**</span>: 51-100 Deaths
- <span style="color: #FFFF00;">**Yellow**</span>: 1-50 Deaths
- <span style="color: #CFBD99;">**Pale Cream**</span>: 0 Deaths
""", unsafe_allow_html=True)

st.write("### Complete Data Table")
st.dataframe(csv_data)

st.subheader(f"Percentage Contribution of Each District in '{selected_year}'")
total_deaths_in_year = csv_data[selected_year].sum()
csv_data['Percentage Contribution'] = (csv_data[selected_year] / total_deaths_in_year) * 100

st.dataframe(csv_data[['District', selected_year, 'Percentage Contribution']])

selected_district = st.selectbox('Select District for Comparison', csv_data['District'].unique())
comparative_data = csv_data[csv_data['District'] == selected_district].set_index('District').T

mean_deaths = comparative_data.mean().values[0]
std_deviation = comparative_data.std().values[0]
min_deaths = comparative_data.min().values[0]
max_deaths = comparative_data.max().values[0]

st.subheader(f'Comparative Death Data for {selected_district}')
st.dataframe(comparative_data.astype(int)) 

st.write(f"**Mean Deaths**: {int(mean_deaths)}") 
st.write(f"**Standard Deviation**: {int(std_deviation)}")
st.write(f"**Minimum Deaths**: {int(min_deaths)}") 
st.write(f"**Maximum Deaths**: {int(max_deaths)}")

st.subheader(f'Year vs Deaths for {selected_district}')
plt.figure(figsize=(10, 7))

deaths_over_years = csv_data[csv_data['District'] == selected_district].iloc[0, 2:9].values  

plt.plot(year_columns[:-1], deaths_over_years, marker='o')

for i, txt in enumerate(deaths_over_years):
    plt.annotate(txt, (year_columns[i], deaths_over_years[i]), textcoords="offset points", xytext=(0,10), ha='center')

plt.title(f'Deaths Over Years in {selected_district.title()}')
plt.xlabel('Year')
plt.ylabel('Deaths')
plt.xticks(rotation=45)
plt.grid(True)

st.pyplot(plt)

st.subheader(f'Contribution of {selected_district.title()} in {selected_year}')
selected_district_deaths = csv_data[csv_data['District'] == selected_district][selected_year].values[0]
district_contributions = [selected_district_deaths, total_deaths_in_year - selected_district_deaths]
plt.figure(figsize=(6, 6))
plt.pie(district_contributions, labels=[selected_district.title(), 'Rest of State'], autopct='%1.1f%%', startangle=90)
plt.title(f'Contribution of {selected_district.title()} in {selected_year}')
st.pyplot(plt)

st.subheader("State Insight")

yearly_columns = ['2018-19', '2019-20', '2020-21', '2021-22', '2022-23', '2023-24' , '2024-25']

csv_data['Total Deaths'] = csv_data[yearly_columns].sum(axis=1)
district_most_deaths = csv_data.loc[csv_data['Total Deaths'].idxmax()]
st.write(f"**District with Most Deaths**: {district_most_deaths['District'].title()} with {district_most_deaths['Total Deaths']} deaths")

district_least_deaths = csv_data.loc[csv_data['Total Deaths'].idxmin()]
st.write(f"**District with Least Deaths**: {district_least_deaths['District'].title()} with {district_least_deaths['Total Deaths']} deaths")

death_changes = csv_data[yearly_columns].diff(axis=1).sum(axis=1)
csv_data['Death Change'] = death_changes

district_most_increase = csv_data.loc[csv_data['Death Change'].idxmax()]
st.write(f"**District with the Most Increasing Deaths**: {district_most_increase['District'].title()}")

district_most_decrease = csv_data.loc[csv_data['Death Change'].idxmin()]
st.write(f"**District with the Most Decreasing Deaths**: {district_most_decrease['District'].title()}")

st.subheader("Top 5 Districts with the Most Deaths")
top_5_districts = csv_data.nlargest(5, 'Total Deaths')[['District', 'Total Deaths']]
st.dataframe(top_5_districts)

st.subheader("Bottom 5 Districts with the Least Deaths")
bottom_5_districts = csv_data.nsmallest(5, 'Total Deaths')[['District', 'Total Deaths']]
st.dataframe(bottom_5_districts)
