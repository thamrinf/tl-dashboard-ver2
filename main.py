import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go
from streamlit_folium import st_folium

from data_loader import load_activity_data, get_base_map_stats
from branca.element import Template, MacroElement
# Added the new functions to the import list

# Custom Modules
import data_loader
import analytics
import visuals
import ui_components

from data_loader import load_activity_data, get_base_map_stats
from analytics import (
    apply_filters, 
    get_data_quality_stats, 
    get_portfolio_metrics,
    get_funding_metrics,
    get_actor_summaries,
    get_sector_alignment_data,
    get_geographic_analysis_data,
    get_time_dynamics_data,
    get_map_data
)

# 1. CONFIG (Must be first)
st.set_page_config(page_title="Activity Portfolio Dashboard", layout="wide")

# 2. LOAD DATA ---
# 1. Load the Excel/CSV activity records
df_raw = data_loader.load_activity_data()

# 2A. Load the base map (Shapes + Population)
map_base = data_loader.get_base_map_stats()
gdf_raw = data_loader.load_geo_data("data/tls_admin1.geojson")

# 2B. Load raw stats (only if the raw population table elsewhere)
mdf_raw = data_loader.load_municipality_stats()

st.title("Development Activity Portfolio Dashboard")

# 3. SIDEBAR FILTERS
st.sidebar.header("Global Filters")

year_range = st.sidebar.slider(
    "Start Year Range",
    int(df_raw["YearStart"].min()),
    int(df_raw["YearStart"].max()),
    (int(df_raw["YearStart"].min()), int(df_raw["YearStart"].max()))
)

# 1. Level Filter (National vs Municipality)
level_options = sorted(df_raw["level_areas"].dropna().unique())
level_filter = st.sidebar.multiselect("Activities Level", level_options, default=None)

# 2. Municipality Filter (Only show relevant options)
if "Municipality" in level_filter:
    # Get only municipalities present in the raw data
    mun_options = sorted(df_raw[df_raw["level_areas"] == "Municipality"]["Municipality"].dropna().unique())
    municipality_filter = st.sidebar.multiselect("Municipality", mun_options)
else:
    # If National is the only thing selected, we don't filter by municipality
    municipality_filter = []

# 3. Others
sector_filter = st.sidebar.multiselect("Sector", sorted(df_raw["Sector"].dropna().unique()))
donor_filter = st.sidebar.multiselect("Donor", sorted(df_raw["Donor"].dropna().unique()))

# --- APPLY FILTERS ---
mask = (
    (df_raw["YearStart"] >= year_range[0]) & (df_raw["YearStart"] <= year_range[1]) &
    (df_raw["level_areas"].isin(level_filter))
)

if sector_filter:
    mask &= (df_raw["Sector"].isin(sector_filter))
if donor_filter:
    mask &= (df_raw["Donor"].isin(donor_filter))
if municipality_filter:
    # This ensures we only filter by municipality for rows that ARE municipality-level
    mask &= (df_raw["Municipality"].isin(municipality_filter) | (df_raw["level_areas"] == "National"))

#filtered_df = df_raw[mask].copy()

# --- 4. PROCESSING ---
filtered_df = analytics.apply_filters(df_raw, year_range, level_filter, sector_filter, municipality_filter, donor_filter)
t_sum, c_sum = analytics.get_time_analysis(filtered_df)

#CALCULATE COVERAGE ---
# Use 'map_base' as it contains your GeoJSON/official names
active_m, total_m, pct_m = analytics.get_municipality_coverage(filtered_df, map_base)

# Prepare the data for the map first and Pass the base map stats and the filtered projects
map_gdf = analytics.get_map_data(map_base, filtered_df)

# Now calculate the Gaps and Shares using the prepared map_gdf
geo_analysis = analytics.get_geographic_analysis_data(map_gdf)

#Create the data for the National Sankey
nat_data = filtered_df[filtered_df["level_areas"] == "National"]

#Create the data for the Municipal Sankey
mun_data = filtered_df[filtered_df["level_areas"] == "Administrative Post/Municipality"]

# 5. SIDEBAR STATS
st.sidebar.divider()
st.sidebar.metric("Filtered Activities", f"{len(filtered_df):,}")
if not df_raw.empty:
    coverage = (len(filtered_df) / len(df_raw))
    st.sidebar.progress(coverage)
    st.sidebar.caption(f"Showing {coverage*100:.1f}% of total portfolio")

# 6. TABS LAYOUT ('with tabs')
tabs = st.tabs([
    "Data & Methodology", "Portfolio Overview", "Funding & Actors", 
    "Sector & Thematic Alignment", "Geographic Distribution",  
    "Time Dynamics", "Interactive Map"
])

# 7. UI DISPLAY - TAB CONTENT
with tabs[0]:
    st.subheader("Data & Methodology")
    st.write("This tab provides a high-level summary and a searchable view of the raw activity records.")

    # 1. Fetch the stats from analytics
    t_rows, m_end, n_pct, m_part, m_sdg, m_bud = analytics.get_data_quality_stats(filtered_df)

    # 2. Render KPI Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Records", f"{t_rows:,}")
    m2.metric("National Scale", f"{n_pct:.1f}%")
    m3.metric("Partner Attribution", f"{100 - m_part:.1f}%")
    m4.metric("Missing Year End", f"{m_end:.1f}%")

    st.divider()

    # 3. Render the static text from our new component file
    ui_components.render_methodology_tab()
    
with tabs[1]:
    st.subheader("Portfolio Overview")

    # 1. Get Data Quality & Portfolio Stats
    t_rows, m_end, n_pct, m_part, m_sdg, m_bud = analytics.get_data_quality_stats(filtered_df)
    active_m, total_m, top_m, top_f, v1, v2 = analytics.get_geographic_kpis(filtered_df, map_base)
    
    # Use the shared analytics function for total budget
    total_budget = filtered_df["Budget"].sum()

    # 2. Logic for Municipalities (The "X / Y" Count)
    active_municipalities = filtered_df[filtered_df["level_areas"] == "Municipality"]["Municipality"].nunique()
    total_possible_mun = df_raw[df_raw["level_areas"] == "Municipality"]["Municipality"].nunique()
    mun_display = f"{active_municipalities} / {total_possible_mun}"

    # 3. Logic for National Count
    nat_count = len(filtered_df[filtered_df["level_areas"] == "National"])
    nat_display = f"{nat_count:,}"

    # 4. Render Metrics in Columns
    m1, m2, m3, m4, m5 = st.columns([1.5, 1, 1, 1, 1.2]) # Slightly wider for currency/municipalities
    
    m1.metric("Total Portfolio Budget", ui_components.format_currency(total_budget))
    m2.metric("Activities", f"{len(filtered_df):,}")
    m3.metric("Sectors", filtered_df["Sector"].nunique())
    m4.metric("National Level", nat_display)
    
    # The new dynamic municipality metric
    m5.metric(
        label="Active Regions", 
        value=f"{active_m}", 
        help="Number of municipalities with at least one active project"
    )

    st.divider()

    # 3. Render Table from ui_components
    ui_components.render_portfolio_table(filtered_df)

with tabs[2]:
    st.subheader("Funding & Actors")

    # 1. Fetch Data
    donor_sum, impl_sum = get_actor_summaries(filtered_df)
    t_donors, t_partners, t_budget, avg_size, nat_fund, mun_fund = get_funding_metrics(filtered_df)

    # 2. Render KPIs
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Donors", t_donors)
    c2.metric("Total Partners", t_partners)
    c3.metric("Total Budget", ui_components.format_currency(t_budget))
    c4.metric("Avg Project Size", ui_components.format_currency(avg_size))
    c5.metric("National Funding", ui_components.format_currency(nat_fund))
    c6.metric("Municipality Funding", ui_components.format_currency(mun_fund))

    st.divider()

    # 3. Charts
    st.subheader("Budget Allocation Across Donors")
    visuals.render_donor_exposure_chart(filtered_df)

    st.divider()
    
    # 4. Sankey Section
    st.markdown("### Financial Flow Control")

    # 1. Filter logic
    min_budget = int(filtered_df['Budget'].min())
    max_budget = int(filtered_df['Budget'].max())

    budget_range = st.slider(
        "Filter by Project Budget Size (USD)",
        min_value=min_budget, max_value=max_budget,
        value=(min_budget, max_budget), format="$%d"
    )

    sankey_filtered = filtered_df[
        (filtered_df['Budget'] >= budget_range[0]) & 
        (filtered_df['Budget'] <= budget_range[1])
    ].copy()

    # 2. Call the visual function
    tab_nat, tab_mun = st.tabs(["National Projects", "Municipality Projects"])

    with tab_nat:
        nat_data = sankey_filtered[sankey_filtered['level_areas'] == 'National']
        visuals.render_sankey_chart(nat_data, "National Level Funding Flow")

    with tab_mun:
        mun_data = sankey_filtered[sankey_filtered['level_areas'] == 'Municipality']
        visuals.render_sankey_chart(mun_data, "Municipality Level Funding Flow")

    st.divider()

    # --- ROW 4: PARTNER LOAD & INTENSITY ---
    # 1. Process Data via Analytics
    impl_summary = analytics.get_partner_summary(filtered_df)

    # 2. Render Charts via Visuals
    visuals.render_partner_charts(impl_summary)

    # 1. Calculate Donor Summary (Add this line!)
    donor_summary = filtered_df.groupby("Donor").agg(
        Activities=("Donor", "count"),
        Total_Budget=("Budget", "sum")
    ).reset_index()
    donor_summary["Avg_Budget_per_Activity"] = (
        donor_summary["Total_Budget"] / donor_summary["Activities"]
    ).fillna(0)

    st.divider()

    # 2. Coordination Table logic
    st.markdown("### Partner Coordination Table")
    view_option = st.radio(
        "View coordination by:",
        ["Donor", "Implementing Partner"],
        horizontal=True,
        key="coordination_toggle_national"
    )

    if view_option == "Donor":
        # Ensure donor_summary is also calculated via analytics.get_donor_summary(filtered_df)
        display_df = donor_summary.rename(columns={"Donor": "Entity"}).sort_values("Activities", ascending=False)
    else:
        display_df = impl_summary.rename(columns={"Implementing Agency": "Entity"}).sort_values("Activities", ascending=False)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Total_Budget": st.column_config.NumberColumn("Total Budget", format="$ %d"),
            "Avg_Budget_per_Activity": st.column_config.NumberColumn("Avg Budget/Act", format="$ %d"),
        }
    )

    #Footer: Data health check
   # Render the health dashboard
    st.divider() # Adds a nice line before the footer
    ui_components.render_data_health_dashboard(t_rows, m_end, n_pct, m_part, m_sdg, m_bud)

with tabs[3]:
    st.subheader("Sector & Thematic Alignment")
    
    # 1. KPIs
    # 1. Calculate Metrics
    sector_kpis = analytics.get_sector_thematic_kpis(filtered_df)

    # 2. Display Metrics
    visuals.render_sector_kpis(sector_kpis)
    
    st.divider()

    # 2. Pareto Balance Chart
    visuals.render_sector_balance_chart(filtered_df)

    st.divider()

    # 3. Alignment Gap Analysis
    sector_alignment = get_sector_alignment_data(filtered_df)
    visuals.render_alignment_comparison(sector_alignment)

    st.divider()

    # 4. Get the data from analytics
    sdg_sum, sdg_col = analytics.get_sdg_summary(filtered_df)
    nsdp_sum, nsdp_col = analytics.get_nsdp_summary(filtered_df)

    # 6. Render the visuals
    visuals.render_sdg_chart(sdg_sum, sdg_col)
    visuals.render_nsdp_chart(nsdp_sum, nsdp_col)

    st.divider()

    # 6. Data Table
    st.write("### Strategic Analysis Table")
    st.dataframe(sector_alignment, use_container_width=True, hide_index=True)

with tabs[4]:
    st.subheader("Municipality Coverage & Geographic Distribution")
    
    # 1. Processing
    geo_analysis = get_geographic_analysis_data(map_gdf) # Using the map data 
    
    
    # 2. KPIs
    c1_total, c2_active, c3_name, c4_name, c3_val, c4_val = analytics.get_geographic_kpis(filtered_df, map_base)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Municipalities", f"{c1_total}")
        st.caption("Total municipalities in Timor-Leste")

    with c2:
        st.metric("Active Regions", f"{c2_active}")
        st.caption("All municipalities with activities")

    with c3:
        st.metric("Top Activities", c3_name)
        st.caption(f"Highest count: {c3_val} activities")

    with c4:
        # Using a helper for currency if you have one, or simple formatting
        formatted_fund = f"${c4_val/1e6:.1f}M" if c4_val >= 1e6 else f"${c4_val:,.0f}"
        st.metric("Top Funded", c4_name)
        st.caption(f"Total: {formatted_fund}")

    st.divider()

    # 3. Bar Charts
    visuals.render_muni_top_charts(filtered_df)
    st.divider()

    # 4. Intensity Chart
    chart_data = geo_analysis.drop(columns=['geometry'])
    visuals.render_spatial_intensity_chart(filtered_df)

    st.divider()

    # 5. Intensity table and Get the aggregated data
    geo_summary_df = analytics.get_geographic_summary_table(filtered_df)

    if not geo_summary_df.empty:
        # 2. Format the data for display
        # We create a copy to format numbers without breaking the math
        display_table = geo_summary_df.copy()
        
        # Optional: Format currency columns for better readability
        display_table["Total_Budget"] = display_table["Total_Budget"].map("${:,.0f}".format)
        display_table["Avg_Budget_Per_Project"] = display_table["Avg_Budget_Per_Project"].map("${:,.0f}".format)

        # 3. Render the table
        st.dataframe(
            display_table, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Municipality": "Region",
                "Total_Activities": "Activities",
                "Total_Budget": "Total Funding",
                "Unique_Donors": "Donors",
                "Unique_Sectors": "Sectors",
                "Avg_Budget_Per_Project": "Avg. Project Size"
            }
        )
    else:
        st.info("No municipality data available for the current filters.")

with tabs[5]:
    st.subheader("Temporal Trends: 2022–2025")
    
    # 1. Math
    t_sum, c_sum, ongoing_p = analytics.get_time_dynamics_data(filtered_df)

    # Peak Activity (Volume)
    peak_act_row = t_sum.loc[t_sum['Total_Activities'].idxmax()]
    peak_act_year = int(peak_act_row['YearStart'])
    peak_act_count = int(peak_act_row['Total_Activities'])

    # Peak budget year row correctly
    peak_bd_idx = t_sum['Budget'].idxmax()
    peak_bd_row = t_sum.loc[peak_bd_idx]
    peak_bud_year = int(peak_bd_row['YearStart'])
    peak_bud_value = peak_bd_row['Budget']
    
    # 2. KPIs
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        # Shows the range of years available in the data
        c1.metric("Year Coverage", f"{int(t_sum['YearStart'].min())} - {int(t_sum['YearStart'].max())}")

    with c2:
        # Shows the year with the highest count of projects
        c2.metric(
            "Peak Activity Year",
            peak_act_year,
            delta=f"{peak_act_count} projects"
        )

    with c3:
        # Fixed the missing comma and the internal quote error for [Budget]
        # 'delta' must be a string; added f-string formatting for the currency
        c3.metric(
            "Peak Funding Year", 
            peak_bud_year, 
            delta=f"${peak_bud_value:,.0f}", 
            delta_color="normal"
        )

    with c4:
        # Shows the percentage of projects currently marked as 'Ongoing'
        c4.metric("% Ongoing", f"{ongoing_p:.1f}%")

    st.divider()

    # 3. Charts
    st.subheader("Annual Pipeline Trends")

    visuals.render_annual_pipeline_charts(t_sum)
    st.divider()

    st.subheader("Cohort Lifecycle: Ongoing vs. Completed Projects")

    # 1. Fetch data from analytics
    cohort_summary = analytics.get_cohort_data(filtered_df)

    if not cohort_summary.empty:
        # 2. Build and display the chart (The 'Visual' part)
        cohort_chart = alt.Chart(cohort_summary).mark_bar().encode(
            x=alt.X("YearStart:O", title=None),
            y=alt.Y("Count:Q", title="Number of Activities"),
            color=alt.Color(
                "Status:N", 
                scale=alt.Scale(domain=["Ongoing – Active", "Completed"], range=["#2a9d8f", "#e9c46a"]),
                legend=alt.Legend(orient='bottom', title=None)
            )
        ).properties(height=400)

        st.altair_chart(cohort_chart, use_container_width=True)
    
    # Explanation from UI Components
    ui_components.render_cohort_explanation()
    
    st.divider()

    st.subheader("Investment Intensity: Average Budget per Activity")
    st.markdown("###### Average Project Financial Weight by Start Year")
    visuals.render_time_intensity_chart(t_sum)

    # 4. Contextual Guidance
    col_x, col_y = st.columns(2)

    with col_x:
        st.info("""
        **High Average (Above Line):** Indicates years dominated by 
        'Mega-Projects' or Infrastructure. Fewer, but high-risk/high-value activities.
        """)

    with col_y:
        st.success("""
        **Low Average (Below Line):** Indicates 'Fragmentation' or 
        Service-Heavy years. Many small activities (training, equipment, etc.).
        """)

with tabs[6]:

    # 1. Logic via analytics.py
    national_df, subnational_df = analytics.get_national_split(filtered_df)

    #st.write("Debug - geo_summary type:", type(geo_summary)) 
    # If this says <class 'NoneType'>, the problem is inside prepare_geo_summary()

    if not subnational_df.empty:
        geo_summary = analytics.prepare_geo_summary(subnational_df)
        
        # Final check to ensure geo_summary is a valid DataFrame
        if geo_summary is not None:
            map_df = analytics.merge_geo_data(gdf_raw, geo_summary)
            # ... rest of your mapping code ...
        else:
            st.warning("Could not calculate regional summary.")
    else:
        st.info("No sub-national data available for the current filters.")


    geo_summary = analytics.prepare_geo_summary(subnational_df)
    map_df = analytics.merge_geo_data(gdf_raw, geo_summary)

    # 2. UI Controls
    st.subheader("Geographic Distribution of Activities & Funding")
    map_metric = st.selectbox("Select Map Metric", ["Activities", "Total_Budget"], key="map_metric")

    # 3. Visualization via visuals.py
    m = visuals.create_interactive_map(map_df, map_metric)
    map_output = st_folium(m, width=None, height=600, key=f"map_{map_metric}")

    # 4. Detail View via ui_components.py
    if map_output and map_output.get("last_active_drawing"):
        muni_name = map_output["last_active_drawing"]["properties"]['adm1_name']
        ui_components.render_municipality_details(muni_name, filtered_df)
        
    