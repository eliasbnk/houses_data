import tkinter as tk
from tkinter import ttk
import geopandas as gpd
import folium
from shapely.geometry import Polygon, MultiPolygon
import requests
import zipfile
import io
import os
import json
import webbrowser

# Function to download and unzip shapefile
def download_shapefile(url, extract_to='.'):
    response = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall(extract_to)

# Download US counties shapefile
shapefile_url = 'https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_county_20m.zip'
shapefile_dir = 'us_counties_shapefile'
if not os.path.exists(shapefile_dir):
    os.makedirs(shapefile_dir)
    download_shapefile(shapefile_url, shapefile_dir)

# Load the county shapefile
shapefile_path = os.path.join(shapefile_dir, 'cb_2021_us_county_20m.shp')
gdf = gpd.read_file(shapefile_path)

# State FIPS to state name mapping
state_fips_to_name = {
    '01': 'Alabama', '02': 'Alaska', '04': 'Arizona', '05': 'Arkansas', '06': 'California', 
    '08': 'Colorado', '09': 'Connecticut', '10': 'Delaware', '11': 'District of Columbia', 
    '12': 'Florida', '13': 'Georgia', '15': 'Hawaii', '16': 'Idaho', '17': 'Illinois', 
    '18': 'Indiana', '19': 'Iowa', '20': 'Kansas', '21': 'Kentucky', '22': 'Louisiana', 
    '23': 'Maine', '24': 'Maryland', '25': 'Massachusetts', '26': 'Michigan', '27': 'Minnesota', 
    '28': 'Mississippi', '29': 'Missouri', '30': 'Montana', '31': 'Nebraska', '32': 'Nevada', 
    '33': 'New Hampshire', '34': 'New Jersey', '35': 'New Mexico', '36': 'New York', 
    '37': 'North Carolina', '38': 'North Dakota', '39': 'Ohio', '40': 'Oklahoma', '41': 'Oregon', 
    '42': 'Pennsylvania', '44': 'Rhode Island', '45': 'South Carolina', '46': 'South Dakota', 
    '47': 'Tennessee', '48': 'Texas', '49': 'Utah', '50': 'Vermont', '51': 'Virginia', 
    '53': 'Washington', '54': 'West Virginia', '55': 'Wisconsin', '56': 'Wyoming'
}

# Simplify geometry for better performance in the interactive map
gdf['geometry'] = gdf['geometry'].simplify(0.01)

# Function to load data from the JSON file
def load_data(filename):
    with open(filename, 'r') as file:
        return json.load(file)

class RealEstateApp:

    def __init__(self, root, data, gdf):
        self.root = root
        self.root.title("Real Estate Search and Interactive Map")
        self.data = data
        self.gdf = gdf

        # Configure the grid to expand with window resize
        self.root.grid_rowconfigure(6, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Input fields
        self.price_var = tk.DoubleVar()
        self.beds_var = tk.IntVar()
        self.baths_var = tk.DoubleVar()
        self.sqft_var = tk.IntVar()
        self.lotsize_var = tk.DoubleVar()

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Max Price:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        tk.Entry(self.root, textvariable=self.price_var).grid(row=0, column=1, padx=10, pady=5, sticky="we")

        tk.Label(self.root, text="Beds:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        tk.Entry(self.root, textvariable=self.beds_var).grid(row=1, column=1, padx=10, pady=5, sticky="we")

        tk.Label(self.root, text="Baths:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        tk.Entry(self.root, textvariable=self.baths_var).grid(row=2, column=1, padx=10, pady=5, sticky="we")

        tk.Label(self.root, text="Sqft:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        tk.Entry(self.root, textvariable=self.sqft_var).grid(row=3, column=1, padx=10, pady=5, sticky="we")

        tk.Label(self.root, text="Lot Size:").grid(row=4, column=0, padx=10, pady=5, sticky="e")
        tk.Entry(self.root, textvariable=self.lotsize_var).grid(row=4, column=1, padx=10, pady=5, sticky="we")

        tk.Button(self.root, text="Search", command=self.search).grid(row=5, column=0, columnspan=2, pady=10)

        self.result_frame = tk.Frame(self.root)
        self.result_frame.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        # Make the result frame scrollable
        self.canvas = tk.Canvas(self.result_frame)
        self.scrollbar = tk.Scrollbar(self.result_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def search(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        max_price = self.price_var.get()
        max_beds = self.beds_var.get()
        max_baths = self.baths_var.get()
        max_sqft = self.sqft_var.get()
        max_lotsize = self.lotsize_var.get()

        results = []
        county_house_counts = {}
        
        for state, counties in self.data.items():
            for county, properties in counties.items():
                count = 0
                for property in properties:
                    if self.is_match(property, max_price, max_beds, max_baths, max_sqft, max_lotsize):
                        count += 1
                        results.append(
                            f"{property['price']} - {property['beds']} - {property['baths']} - {property['sqft']} - {property['lotsize']} - {county} - {state}"
                        )
                county_house_counts[county] = count

        # Update the map with the county house counts
        self.update_map(county_house_counts)

        for result in results:
            tk.Label(self.scrollable_frame, text=result, borderwidth=2, relief="groove").pack(fill="x", padx=5, pady=5)

    def is_match(self, property, max_price, max_beds, max_baths, max_sqft, max_lotsize):
        if any(value is None for value in property.values()):
            return False
        if max_price and property['price'] > max_price:
            return False
        if max_beds and property['beds'] < max_beds:
            return False
        if max_baths and property['baths'] < max_baths:
            return False
        if max_sqft and property['sqft'] < max_sqft:
            return False
        if max_lotsize and property['lotsize'] < max_lotsize:
            return False
        return True

    def update_map(self, county_house_counts):
        # Create a folium map centered on the US
        m = folium.Map(location=[37.8, -96.9], zoom_start=4)

        # Add county boundaries to the map with house count in the tooltip
        for _, row in self.gdf.iterrows():
            state_name = state_fips_to_name.get(row['STATEFP'], 'Unknown')
            county_name = row['NAME']
            house_count = county_house_counts.get(county_name, 0)
            tooltip = f"{county_name}, {state_name} - Houses found: {house_count}"
        folium.GeoJson(
        row['geometry'],
        name=county_name,
        tooltip=tooltip
        ).add_to(m)
        # Save the map to an HTML file
        map_path = 'us_counties_map.html'
        m.save(map_path)

        # Open the map in the default web browser
        webbrowser.open('file://' + os.path.abspath(map_path))


if __name__ == "__main__":
# Load data from JSON file
    data = load_data("combined_data.json")
    root = tk.Tk()
    app = RealEstateApp(root, data, gdf)
    root.mainloop()