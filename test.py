import tkinter as tk
from tkinter import ttk
import json
import os
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

class RealEstateApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Real Estate Map Viewer")
        self.geometry("800x600")
        self.data_dir = 'data'  # Directory containing the data
        self.all_data = self.load_data()

        # Set up the user interface
        self.create_widgets()

    def create_widgets(self):
        # Create entry fields for query parameters
        self.price_var = tk.StringVar()
        self.beds_var = tk.StringVar()
        self.baths_var = tk.StringVar()
        self.sqft_var = tk.StringVar()
        self.lotsize_var = tk.StringVar()

        ttk.Label(self, text="Price:").grid(row=0, column=0)
        ttk.Entry(self, textvariable=self.price_var).grid(row=0, column=1)

        ttk.Label(self, text="Beds:").grid(row=1, column=0)
        ttk.Entry(self, textvariable=self.beds_var).grid(row=1, column=1)

        ttk.Label(self, text="Baths:").grid(row=2, column=0)
        ttk.Entry(self, textvariable=self.baths_var).grid(row=2, column=1)

        ttk.Label(self, text="Sqft:").grid(row=3, column=0)
        ttk.Entry(self, textvariable=self.sqft_var).grid(row=3, column=1)

        ttk.Label(self, text="Lot Size:").grid(row=4, column=0)
        ttk.Entry(self, textvariable=self.lotsize_var).grid(row=4, column=1)

        # Button to perform search
        ttk.Button(self, text="Search", command=self.perform_search).grid(row=5, column=0, columnspan=2)

    def load_data(self):
        all_data = {}
        for state in os.listdir(self.data_dir):
            state_path = os.path.join(self.data_dir, state)
            if os.path.isdir(state_path):
                all_data[state] = {}
                for county_file in os.listdir(state_path):
                    county_name = county_file.replace('.json', '')
                    with open(os.path.join(state_path, county_file), 'r') as f:
                        all_data[state][county_name] = json.load(f)
        return all_data

    def filter_data(self, price=None, beds=None, baths=None, sqft=None, lotsize=None):
        filtered_data = {}

        for state, counties in self.all_data.items():
            filtered_data[state] = {}
            for county, houses in counties.items():
                matching_houses = [
                    house for house in houses
                    if (not price or int(house['price'].replace('$', '').replace(',', '')) <= int(price))
                    and (not beds or int(house['beds'].split()[0]) >= int(beds))
                    and (not baths or int(house['baths'].split()[0]) >= int(baths))
                    and (not sqft or int(house['sqft'].replace(',', '').split()[0]) >= int(sqft))
                    and (not lotsize or int(house['lotsize'].replace(',', '').split()[0]) >= int(lotsize))
                ]
                if matching_houses:
                    filtered_data[state][county] = matching_houses

        return filtered_data

    def plot_map(self, filtered_data):
        # Load a US counties shapefile
        counties = gpd.read_file('path/to/us_counties_shapefile.shp')  # Replace with actual path

        # Create a DataFrame to count matching houses per county
        county_matches = []
        for state, counties_data in filtered_data.items():
            for county_name, houses in counties_data.items():
                county_matches.append({
                    'state': state,
                    'county_name': county_name,
                    'match_count': len(houses)
                })

        matches_df = pd.DataFrame(county_matches)

        # Plot the map
        fig, ax = plt.subplots(1, 1, figsize=(15, 10))
        counties.boundary.plot(ax=ax, linewidth=1)

        # Merge the county shapefile with the match data
        counties = counties.merge(matches_df, left_on='NAME', right_on='county_name', how='left')
        counties['match_count'] = counties['match_count'].fillna(0)

        # Plot counties with color grading
        counties.plot(column='match_count', ax=ax, legend=True, cmap='OrRd', legend_kwds={'label': "Number of Matching Properties"})

        plt.title("Real Estate Map with Highlighted Counties")
        plt.show()

    def perform_search(self):
        # Fetch user input
        price = self.price_var.get()
        beds = self.beds_var.get()
        baths = self.baths_var.get()
        sqft = self.sqft_var.get()
        lotsize = self.lotsize_var.get()

        # Filter data
        filtered_data = self.filter_data(price, beds, baths, sqft, lotsize)

        # Plot map with filtered data
        self.plot_map(filtered_data)

if __name__ == "__main__":
    app = RealEstateApp()
    app.mainloop()