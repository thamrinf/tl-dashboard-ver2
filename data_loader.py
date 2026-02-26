import streamlit as st
import pandas as pd
import geopandas as gpd

@st.cache_data
def load_activity_data(path="data/activities.csv"):
    df = pd.read_csv(path)
    
    # Clean up sectors/municipalities
    df["Sector"] = df["Sector"].str.strip().str.title()
    df["Municipality"] = df["Municipality"].fillna("Unknown")
    
    # Generate unique ID via hashing
    df["activity_group"] = (
        df["Municipality"].astype(str) + " | " + 
        df["Sector"].astype(str) + " | " + 
        df["Implementing Agency"].fillna("Unknown") + " | " + 
        df["Donor"].fillna("Unknown") + " | " + 
        df["YearStart"].astype(str) + " | " + 
        df["Budget"].fillna(0).astype(str) + " | " +
        df["level_areas"].fillna("Unknown").astype(str)
    )
    df["activity_id"] = pd.util.hash_pandas_object(df["activity_group"], index=False)
    df["budget_usd"] = pd.to_numeric(df["Budget"], errors='coerce').fillna(0)
    return df

@st.cache_data
def load_geo_data(path="data/tls_admin1.geojson"):
    gdf = gpd.read_file(path)
    gdf = gdf.to_crs(epsg=4326)
    gdf["mun_clean"] = gdf["adm1_name"].str.strip().str.title()
    return gdf

@st.cache_data
def load_municipality_stats(path="data/municipality_stats.csv"):
    mdf = pd.read_csv(path)
    mdf["Municipality"] = mdf["Municipality"].str.strip().str.title()
    
    if mdf["Population (2022)"].dtype == object:
        mdf["Population (2022)"] = mdf["Population (2022)"].str.replace(r'[^\d]', '', regex=True).astype(int)
    return mdf

@st.cache_data
def get_base_map_stats():
    gdf_raw = load_geo_data()
    mdf_raw = load_municipality_stats()
    
    # Static Join: Shapes + Population info
    gdf_with_stats = gdf_raw.merge(
        mdf_raw, 
        left_on="mun_clean", 
        right_on="Municipality", 
        how="left"
    )
    return gdf_with_stats