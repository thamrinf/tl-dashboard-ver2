import streamlit as st
import pandas as pd
import altair as alt

def apply_filters(df, year_range, levels, sectors, municipalities, donors):
    """Handles the sidebar filtering logic."""
    filtered = df[
        (df["YearStart"] >= year_range[0]) & 
        (df["YearStart"] <= year_range[1])
    ].copy()

    if levels:
        filtered = filtered[filtered["level_areas"].isin(levels)]
    if sectors:
        filtered = filtered[filtered["Sector"].isin(sectors)]
    if municipalities:
        filtered = filtered[filtered["Municipality"].isin(municipalities)]
    if donors:
        filtered = filtered[filtered["Donor"].isin(donors)]
    
    # Standardize Municipality for National records
    filtered.loc[filtered["level_areas"] == "National", "Municipality"] = "N/A"
    return filtered

def get_data_quality_stats(filtered_df):
    """Calculates percentages for data completeness and scale (6 values)."""
    total_count = len(filtered_df)
    if total_count == 0:
        return 0, 0.0, 0.0, 0.0, 0.0, 0.0

    missing_end = (filtered_df["YearEnd"].isna().sum() / total_count) * 100
    national_pct = (filtered_df["level_areas"].eq("National").sum() / total_count) * 100
    
    # Check for specific alignment columns
    missing_sdg = (filtered_df["SDGs_Alignment"].isna().sum() / total_count) * 100 if "SDGs_Alignment" in filtered_df.columns else 0
    missing_budget = (filtered_df["Budget"].isna().sum() / total_count) * 100
    
    partner_col = "Implementing Agency"
    missing_partners = 0.0
    if partner_col in filtered_df.columns:
        missing_partners = (filtered_df[partner_col].isna().sum() / total_count) * 100
            
    return total_count, missing_end, national_pct, missing_partners, missing_sdg, missing_budget

def get_portfolio_metrics(filtered_df, level_filter, municipality_filter):
    """Calculates logic-heavy metrics for the Portfolio Overview."""
    total_budget = filtered_df['Budget'].sum()
    
    # National Logic
    only_muni_level = len(level_filter) == 1 and "Municipality" in level_filter
    has_muni_selection = len(municipality_filter) > 0 and "National" not in level_filter
    
    if only_muni_level or has_muni_selection:
        nat_display = "N/A"
    else:
        nat_count = len(filtered_df[filtered_df["level_areas"] == "National"])
        nat_display = str(nat_count)

    # Municipality Logic
    if len(level_filter) == 1 and "National" in level_filter:
        mun_display = "N/A"
    else:
        mun_count = filtered_df["Municipality"].nunique()
        if "N/A" in filtered_df["Municipality"].values:
            mun_count = max(0, mun_count - 1)
        mun_display = str(mun_count)
        
    return total_budget, nat_display, mun_display

def get_funding_metrics(df):
    """Calculates specific funding KPIs for the Funding tab."""
    if df.empty:
        return 0, 0, 0, 0, 0, 0
    return (
        df['Donor'].nunique(),
        df['Implementing Agency'].nunique(),
        df['Budget'].sum(),
        df['Budget'].mean(),
        df[df['level_areas'] == 'National']['Budget'].sum(),
        df[df['level_areas'] == 'Municipality']['Budget'].sum()
    )

def get_partner_summary(df):
    summary = df.groupby("Implementing Agency").agg(
        Activities=("Implementing Agency", "count"),
        Total_Budget=("Budget", "sum")
    ).reset_index()

    summary["Avg_Budget_per_Activity"] = (
        summary["Total_Budget"] / summary["Activities"]
    ).fillna(0)
    
    return summary

def render_partner_metrics(summary_df):
    col_load, col_intensity = st.columns(2)
    
    # Get Top 10 for each
    top_volume = summary_df.nlargest(10, "Activities")
    top_intensity = summary_df.nlargest(10, "Avg_Budget_per_Activity")

    with col_load:
        st.subheader("Partner Load (Activity Volume)")
        load_chart = alt.Chart(top_volume).mark_bar().encode(
            x=alt.X("Activities:Q", title="Number of Activities"),
            y=alt.Y("Implementing Agency:N", sort="-x", title=None),
            color=alt.value("#3EC4D0"),
            tooltip=[
                alt.Tooltip("Implementing Agency", title="Partner"),
                alt.Tooltip("Activities:Q", title="Total Activities")
            ]
        ).properties(height=400)
        st.altair_chart(load_chart, use_container_width=True)

    with col_intensity:
        st.subheader("Partner Intensity (Avg Budget)")
        intensity_chart = alt.Chart(top_intensity).mark_bar().encode(
            x=alt.X("Avg_Budget_per_Activity:Q", title="Avg Budget per Activity (USD)"),
            y=alt.Y("Implementing Agency:N", sort="-x", title=None),
            color=alt.value("#43D9E7"),
            tooltip=[
                alt.Tooltip("Implementing Agency", title="Partner"),
                alt.Tooltip("Avg_Budget_per_Activity:Q", format="$,.0f", title="Avg Budget")
            ]
        ).properties(height=400)
        st.altair_chart(intensity_chart, use_container_width=True)

def get_actor_summaries(df):
    """Aggregates data for Donors and Implementing Agencies."""
    donor_summary = df.groupby("Donor").agg(
        Total_Activities=("Donor", "count"),
        Total_Budget=("Budget", "sum")
    ).reset_index()
    donor_summary["Avg_Budget_per_Activity"] = (donor_summary["Total_Budget"] / donor_summary["Total_Activities"]).fillna(0)

    impl_summary = df.groupby("Implementing Agency").agg(
        Total_Activities=("Implementing Agency", "count"),
        Total_Budget=("Budget", "sum")
    ).reset_index()
    impl_summary["Avg_Budget_per_Activity"] = (impl_summary["Total_Budget"] / impl_summary["Total_Activities"]).fillna(0)
    
    return donor_summary, impl_summary

def get_sector_thematic_kpis(df):
    # Sector Metrics
    total_sectors = df["Sector"].nunique()
    
    # Dominant Sector Calculation
    sector_counts = df["Sector"].value_counts()
    if not sector_counts.empty:
        dominant_sector_name = sector_counts.index[0]
        dominant_share = (sector_counts.iloc[0] / len(df)) * 100
    else:
        dominant_sector_name = "N/A"
        dominant_share = 0

    # SDG & Pillar Metrics (Dynamic Column Detection)
    sdg_col = [c for c in df.columns if 'SDG' in c.upper()]
    unique_sdgs = df[sdg_col[0]].nunique() if sdg_col else 0
    
    pillar_col = [c for c in df.columns if 'PILLAR' in c.upper() or 'NSDP' in c.upper()]
    unique_pillars = df[pillar_col[0]].nunique() if pillar_col else 0

    return {
        "total_sectors": total_sectors,
        "dominant_sector_name": dominant_sector_name,
        "dominant_share": dominant_share,
        "unique_sdgs": unique_sdgs,
        "unique_pillars": unique_pillars
    }

def get_sector_alignment_data(df):
    """Calculates shares and alignment gaps for the Sector tab."""
    sector_alignment = df.groupby("Sector").agg(
        Total_Activities=("Sector", "count"),
        Budget=("Budget", "sum")
    ).reset_index()

    total_act = sector_alignment["Total_Activities"].sum()
    total_bud = sector_alignment["Budget"].sum()

    if total_act > 0 and total_bud > 0:
        sector_alignment["Activity Share (%)"] = (sector_alignment["Total_Activities"] / total_act) * 100
        sector_alignment["Budget Share (%)"] = (sector_alignment["Budget"] / total_bud) * 100
        sector_alignment["Alignment Gap (%)"] = sector_alignment["Budget Share (%)"] - sector_alignment["Activity Share (%)"]
        
        def classify_gap(gap):
            if gap > 5: return "💰 Capital Heavy"
            elif gap < -5: return "🏃 Activity Heavy"
            return "⚖️ Balanced"
            
        sector_alignment["Classification"] = sector_alignment["Alignment Gap (%)"].apply(classify_gap)
    
    return sector_alignment.sort_values("Activity Share (%)", ascending=False)

def get_geographic_analysis_data(map_gdf):
    """Calculates spatial gaps and investment intensity."""
    df = map_gdf.copy()
    
    total_nat_activities = df["Total_Activities"].sum()
    total_nat_budget = df["Total_Budget"].sum()

    df["Activity Share (%)"] = (df["Total_Activities"] / total_nat_activities * 100).fillna(0)
    df["Budget Share (%)"] = (df["Total_Budget"] / total_nat_budget * 100).fillna(0)
    df["Gap (%)"] = df["Budget Share (%)"] - df["Activity Share (%)"]
    df["Avg_Budget_Per_Activity"] = (df["Total_Budget"] / df["Total_Activities"].replace(0, 1)).fillna(0)

    def classify_gap(row):
        if row["Total_Activities"] == 0: return "⚠️ No Activity"
        gap = row["Gap (%)"]
        if gap > 5: return "💰 Capital Heavy"
        elif gap < -5: return "🏃 Activity Heavy"
        return "⚖️ Balanced"

    df["Classification"] = df.apply(classify_gap, axis=1)
    return df

def get_geographic_kpis(filtered_df, map_base):
    # C1: Total Municipalities from Map Data (The Baseline)
    name_col = 'mun_clean' if 'mun_clean' in map_base.columns else 'adm1_name'
    official_munis = [n for n in map_base[name_col].unique() if n != "Timor-Leste"]
    total_muni_count = len(official_munis)

    # C2: Count active municipalities (Projects only, excluding Timor-Leste/National)
    # Ensure we only look at rows tagged as Municipality
    muni_data = filtered_df[filtered_df["level_areas"] == "Municipality"].copy()
    muni_data["Municipality"] = muni_data["Municipality"].astype(str).str.strip().str.title()
    
    # Filter out National labels
    active_muni_list = muni_data[~muni_data["Municipality"].isin(["Timor-Leste", "National", "Nan"])]
    active_muni_count = active_muni_list["Municipality"].nunique()

    # C3 & C4: Top Municipality by Activities and Funding
    if not active_muni_list.empty:
        stats = active_muni_list.groupby("Municipality").agg(
            activity_count=("activity_id", "count"),
            total_funding=("Budget", "sum")
        )
        
        top_activity_muni = stats["activity_count"].idxmax()
        top_funding_muni = stats["total_funding"].idxmax()
        
        # Get the actual values for the sub-label
        top_act_val = stats["activity_count"].max()
        top_fund_val = stats["total_funding"].max()
    else:
        top_activity_muni, top_funding_muni = "N/A", "N/A"
        top_act_val, top_fund_val = 0, 0

    return total_muni_count, active_muni_count, top_activity_muni, top_funding_muni, top_act_val, top_fund_val

def get_municipality_coverage(filtered_df, geo_df):
    """
    Calculates coverage using the correct column names from the GeoJSON.
    """
    # 1. Identify the correct column
    # Check for 'mun_clean' first, then 'adm1_name', then fallback to 'ADM_NAME1'
    if "mun_clean" in geo_df.columns:
        name_col = "mun_clean"
    elif "adm1_name" in geo_df.columns:
        name_col = "adm1_name"
    else:
        name_col = "ADM_NAME1"

    # 2. Get official names (Excluding National labels)
    # We use .astype(str) to prevent errors with numeric names
    official_names = [
        str(n).strip().title() for n in geo_df[name_col].unique() 
        if str(n).strip() not in ["Timor-Leste", "National", "nan"]
    ]
    total_count = len(official_names)

    # 3. Get unique names from the project 'Municipality' column
    # Standardize to match the map names
    project_munis = filtered_df["Municipality"].dropna().astype(str).str.strip().str.title().unique()

    # 4. Count intersections
    active_count = sum(1 for name in official_names if name in project_munis)
    
    # 5. Calculate percentage
    coverage_pct = (active_count / total_count * 100) if total_count > 0 else 0
    
    return active_count, total_count, coverage_pct

def get_time_analysis(df):
    """Generates annual pipeline and cohort status summaries."""
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # 1. Annual Pipeline (Volume & Value)
    t_sum = df.groupby("YearStart").agg(
        Total_Activities=("activity_id", "count"),
        Budget=("Budget", "sum")
    ).reset_index()
    
    # Calculate Average Intensity per Year
    t_sum["Avg_Budget_per_Activity"] = t_sum["Budget"] / t_sum["Total_Activities"]

    # 2. Cohort Status
    c_sum = df.groupby(["YearStart", "Status"]).size().reset_index(name="Count")
    
    return t_sum, c_sum

def get_time_dynamics_data(df):
    """Prepares cohort and annual trend data based on project status."""
    
    # 1. Annual Trends (Budget/Activities over time)
    time_summary = df.groupby("YearStart").agg(
        Total_Activities=("activity_id", "count"),
        Budget=("Budget", "sum")
    ).reset_index()
    
    time_summary["Avg_Budget_per_Activity"] = (time_summary["Budget"] / time_summary["Total_Activities"]).fillna(0)

    # 2. Cohort Data (Based on your manual 'Status' column)
    # Note: Ensure your 'Status' column contains values like 'Ongoing' or 'Completed'
    if "Status" in df.columns:
        cohort_summary = df.groupby(["YearStart", "Status"]).size().reset_index(name="Count")
        
        # 3. Calculate metrics for the Metric Cards
        ongoing_count = len(df[df["Status"] == "Ongoing - Active"])
        ongoing_pct = (ongoing_count / len(df)) * 100 if len(df) > 0 else 0
    else:
        # Fallback if the column is missing
        cohort_summary = None
        ongoing_pct = 0
    
    return time_summary, cohort_summary, ongoing_pct

def get_cohort_data(df, reference_year=2026):
    """
    Calculates project status and aggregates counts by year.
    Logic moved from main.py to keep things clean.
    """
    if df.empty:
        return pd.DataFrame()

    def determine_status(row):
        if pd.isna(row["YearEnd"]) or row["YearEnd"] >= reference_year:
            return "Ongoing – Active"
        return "Completed"

    cohort_df = df.copy()
    cohort_df["Status"] = cohort_df.apply(determine_status, axis=1)
    
    # Aggregation
    summary = cohort_df.groupby(["YearStart", "Status"]).size().reset_index(name="Count")
    return summary

def get_sdg_summary(df):
    sdg_cols = [c for c in df.columns if 'SDG' in c.upper()]
    if not sdg_cols:
        return None, None
    
    col = sdg_cols[0]
    summary = df.groupby(col).agg(
        Activities=("Sector", "count"),
        Budget=("Budget", "sum")
    ).reset_index()
    
    total_budget = summary["Budget"].sum()
    summary["Budget Share (%)"] = (summary["Budget"] / total_budget) * 100
    return summary.sort_values("Activities", ascending=False), col

def get_nsdp_summary(df):
    pillar_cols = [c for c in df.columns if 'PILLAR' in c.upper() or 'NSDP' in c.upper()]
    if not pillar_cols:
        return None, None
    
    col = pillar_cols[0]
    summary = df.groupby(col)["Budget"].sum().reset_index(name="Total Budget")
    
    total_budget = summary["Total Budget"].sum()
    summary["Budget Share (%)"] = (summary["Total Budget"] / total_budget) * 100
    return summary.sort_values("Total Budget", ascending=False), col

def get_geographic_summary_table(df):
    """
    Creates an aggregated summary of activities by Municipality with name standardization.
    """
    # 1. Filter for Municipality-level only and exclude National labels
    # Use str.contains to be safer against leading/trailing spaces
    muni_data = df[
        (df["level_areas"] == "Municipality") & 
        (~df["Municipality"].str.contains("Timor|National|Unknown", case=False, na=False))
    ].copy()

    if muni_data.empty:
        return pd.DataFrame()

    # --- NEW STEP: STANDARDIZE NAMES ---
    # Strip spaces and convert to TITLE CASE (or UPPER to match your map)
    # This prevents "Dili " and "Dili" from being two different rows.
    muni_data["Municipality"] = muni_data["Municipality"].str.strip().str.title()

    # 2. Aggregate metrics: Group by the Municipality name
    table_data = muni_data.groupby("Municipality").agg(
        Total_Activities=("activity_id", "count"),
        Total_Budget=("Budget", "sum"),
        Unique_Donors=("Donor", "nunique"),
        Unique_Sectors=("Sector", "nunique")
    ).reset_index()

    # 3. Calculate Average Project Size
    table_data["Avg_Budget_Per_Project"] = table_data["Total_Budget"] / table_data["Total_Activities"]

    # 4. Sort by highest activity count
    return table_data.sort_values("Total_Activities", ascending=False)

# def get_geographic_summary_table(df):
#     """
#     Creates an aggregated summary of activities by Municipality.
#     """
#     # 1. Filter for Municipality-level only and exclude National labels
#     muni_data = df[
#         (df["level_areas"] == "Municipality") & 
#         (~df["Municipality"].str.title().isin(["Timor-Leste", "National", "Unknown"]))
#     ].copy()

#     if muni_data.empty:
#         return pd.DataFrame()

#     # 2. Aggregate metrics: Group by the Municipality name
#     table_data = muni_data.groupby("Municipality").agg(
#         Total_Activities=("activity_id", "count"),
#         Total_Budget=("Budget", "sum"),
#         Unique_Donors=("Donor", "nunique"),
#         Unique_Sectors=("Sector", "nunique")
#     ).reset_index()

#     # 3. Calculate Average Project Size
#     table_data["Avg_Budget_Per_Project"] = table_data["Total_Budget"] / table_data["Total_Activities"]

#     # 4. Sort by highest activity count
#     return table_data.sort_values("Total_Activities", ascending=False)

def get_map_data(gdf_raw, subnational_df):
    """Joins sub-national activity data with shapefile."""
    geo_summary = (
        subnational_df.groupby(subnational_df["Municipality"].str.strip().str.upper())
        .agg(
            Total_Activities=("Municipality", "count"), 
            Total_Budget=("Budget", "sum")
        )
        .reset_index()
        .rename(columns={"Municipality": "mun_clean"})
    )

    gdf_raw["mun_clean"] = gdf_raw["adm1_name"].str.strip().str.upper()
    map_df = gdf_raw.merge(geo_summary, on="mun_clean", how="left").fillna(0)
    
    if map_df.crs is None:
        map_df.set_crs(epsg=4326, inplace=True)
    else:
        map_df = map_df.to_crs(epsg=4326)
    
    map_df["geometry"] = map_df["geometry"].buffer(0)
    return map_df

def merge_geo_data(gdf_raw, geo_summary):
    """Joins shapefile with aggregated activity data."""
    gdf_raw["mun_clean"] = gdf_raw["adm1_name"].str.strip().str.upper()
    map_df = gdf_raw.merge(geo_summary, on="mun_clean", how="left").fillna(0)
    
    # Ensure CRS is correct
    if map_df.crs is None:
        map_df.set_crs(epsg=4326, inplace=True)
    else:
        map_df = map_df.to_crs(epsg=4326)
    
    # Fix geometries
    map_df = map_df[map_df.geometry.notnull()]
    map_df["geometry"] = map_df["geometry"].buffer(0)
    return map_df

def prepare_geo_summary(subnational_df):
    """Aggregates data by municipality for mapping."""
    summary = (
        subnational_df.groupby(subnational_df["Municipality"].str.strip().str.upper())
        .agg(
            Activities=("Municipality", "count"),
            Total_Budget=("Budget", "sum"),
            Ongoing=("Status", lambda x: (x == "Ongoing").sum()),
            Completed=("Status", lambda x: (x == "Completed").sum())
        )
        .reset_index()
        .rename(columns={"Municipality": "mun_clean"})
    )

    return summary
    
def get_national_split(df):
    """Splits data into National and Sub-national dataframes."""
    is_national = df["Municipality"].str.contains("timor|leste|national|nationwide", case=False, na=False)
    return df[is_national], df[~is_national]