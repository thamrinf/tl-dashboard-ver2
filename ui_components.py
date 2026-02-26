import streamlit as st
import pandas as pd

def render_methodology_tab():
    """Renders the detailed methodology and metadata section."""
    st.markdown("## Platform Methodology & Data Governance")
    
    # 1. Purpose
    with st.expander("🎯 Purpose", expanded=True):
        st.write("""
        The platform enables users to analyze **financial allocations**, **geographic coverage**, **sectoral distribution**, **donor and implementation patterns**,
        as well as alignment with national and global development frameworks.  It aggregates activities-level data to support transparency, portfolio monitoring, 
        and strategic planning across sectors, municipalities, and thematic priorities.
        """)

    # 2. Data Coverage
    with st.expander("📖 Data Coverage"):
        st.markdown("""
        This dashboard provides a structured overview of development projects implemented across **Timor-Leste.**  Each row represents an **activity record**. 
        Records represent individual activity instances. Similar attributes do not necessarily indicate a single project, as no unique project identifier is available. 
        **700 activities** included in the current dataset.
        """)

    # 3. Time & Budget
    with st.expander("📅 Time & Budget Assumptions"):
        st.markdown("""
        Actvitites starting between **2022 - 2025** and analyzed using their **start year**. Ongoing activities without an end-year 
        are treated as active for analytical purposes. 
        All financial values are standardized in USD. **Budget values** represent **allocated funding**, not actual expenditure. 
        Comparisons reflect financial exposure, not performance.
        """)

    # 4. Geographic Levels
    with st.expander("📍 Definition of Geographic Levels"):
        st.markdown("""
        Activities classified as **National-level** refer to those implemented nationwide or not confined to a single municipality.  
        And **Municipality-level** projects refer to those implemented within a specific municipality. Analysis is based on the reported activities classified level. 
        """)

    # 5. Key Indicators
    with st.expander("⏳ Key Indicators Defined"):
        st.markdown("""
        Project Status includes three categories: **Completed**, **Ongoing – Active**, and **Not Identified**. 
        Project Duration is calculated based on the **start year** and **end year** ; where the end year is missing, the project is treated as **Ongoing – Active**. 
        Sector Allocation refers to the primary **sector classification** assigned to each activities. 
        **SDG / NSDP Alignment** reflects the self-reported alignment of projects with the Sustainable Development Goals and the National Strategic Development Plan priorities. 
        """)

    # 6. Data Sources
    with st.expander("🔍 Data Sources"):
        st.markdown("""
        The dataset was compiled from government administrative project records, donor-reported project information, and implementing partner disclosures. 
        Data cleaning included standardization of sector labels, harmonization of municipality names, identification of duplicate records, and currency consistency checks.
        """)

    # 7. Data Quality & Standardization (The "Missing" 7th/8th)
    with st.expander("🛠 Data Quality & Cleaning"):
        st.markdown("""
        Some projects may have incomplete budget or end-year data. SDG and NSDP alignment is based on reported classifications rather than independent verification. 
        National-level projects may include sub-national components that are not disaggregated in this dataset. 
        Budget figures reflect allocations and do not necessarily represent actual disbursement amounts. Some implementing partner fields contained missing values or were labeled as “Not Identified”. 
        For the purpose of analysis and consistency, these entries have been standardized as “No Information Available".
        """)

    # 8. Known Limitations
    with st.expander("📑 Known Limitations"):
        st.markdown("""
        Some records in the dataset are incomplete. To enhance transparency, a supplementary table highlights entries with missing values, 
        as well as records that may represent potential duplicates. These are identified based on similarities across key fields 
        (e.g., project name, location, and year) and should be interpreted with caution.
        """)
        
        # Define the raw data for the limitations table
        limitations_data = """No,Project_name,Municipality,Sector,Budget,YearStart,YearEnd,project_status
    171,"Constrution of Fatuk Metan Irrigation Project, Bemase",Baucau,Agriculture,50000.0,2025,,Ongoing
    173,Construction and Rehabilitation of Caraulun Irrigation Project,Baucau,Agriculture,50000.0,2025,,Ongoing
    529,UNESCO-VISUS Pilot Implementation in Timor-Leste,Timor-Leste,Education,26000.0,2024,2025,Completed
    530,Enhance the role of the National Institute of Science and Technology...,Timor-Leste,Education,26000.0,2024,2025,Completed
    3,Construction of new school building,Atauro,Infrastructure,41981.72,2025,,Ongoing
    4,Extension of roads,Atauro,Infrastructure,41981.72,2025,,Ongoing
    52,Safeguarding Rural Communities...,Timor-Leste,Infrastructure,26051809.0,2023,2026,Completed
    53,Safeguarding Rural Communities...,Timor-Leste,Infrastructure,26051809.0,2023,2026,Completed
    68,Construction of Archive & Museum and Deposit,Aileu,Infrastructure,100000.0,2025,,Ongoing
    75,Construction of Secondary Roads - Tasi Tolu,Dili,Infrastructure,100000.0,2025,,Ongoing
    77,"New Construction of Community Health Centre (CHC), Remixio",Aileu,Infrastructure,100000.0,2025,,Ongoing
    85,"New Construction for Health Post and Doctor House, Ariana",Baucau,Infrastructure,100000.0,2025,,Ongoing
    86,"New Construction for Health Post and Doctor House, Wacala",Baucau,Infrastructure,100000.0,2025,,Ongoing
    94,Consulting Services for Municipal Spatial Planning of Municipality of Dili,Dili,Infrastructure,100000.0,2025,,Ongoing
    99,Construction of Democracy & Civic Education Center,Dili,Infrastructure,100000.0,2025,,Ongoing
    104,Re-development of Becora secondary Technical- Vocational School,Dili,Infrastructure,100000.0,2025,,Ongoing
    57,UNDP Timor-Leste Accelerator Lab,Timor-Leste,Technology,1346852.0,2023,2025,Completed
    685,UNDP Timor-Leste Accelerator Lab,Timor-Leste,Technology,1346852.0,2023,2025,Completed"""

        # Convert to DataFrame
        import io
        import pandas as pd
        df_lim = pd.read_csv(io.StringIO(limitations_data))
        
        # Display as a clean interactive table
        st.dataframe(df_lim, use_container_width=True, hide_index=True)
    
    st.info("""
        **Disclaimer:** The findings are based on administrative data and are intended solely for analytical and coordination purposes. 
        They should not be considered a substitute for formal monitoring, evaluation, or audit processes. 
        The dataset and associated analyses do not represent official data of the Government of Timor-Leste, the United Nations, or development partners. 
        Data completeness and accuracy may vary across sources.
        """)

def render_data_health_dashboard(t_rows, m_end, n_pct, m_part, m_sdg, m_bud):
    """Renders a visual summary of data quality metrics."""
    # 1. Wrap the entire contents in an expander
    with st.expander("🔍 View Data Health Metrics"):
        st.subheader("Data Quality & Portfolio Health")
        
        # Custom CSS for the metric cards to look more like a 'health check'
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            st.metric("Total Records", f"{t_rows:,}")
            st.caption("Total activities analyzed")
        with c2:
            # We want missing budget to be low, so we show 100 - missing
            st.metric("Budget Coverage", f"{100 - m_bud:.1f}%", delta=f"{-m_bud:.1f}%", delta_color="inverse")
        with c3:
            st.metric("Timeline Integrity", f"{100 - m_end:.1f}%", help="Projects with a defined end-year")
        with c4:
            st.metric("National Scale", f"{n_pct:.1f}%", help="% of activities classified as National vs Regional")

        if m_bud > 10 or m_end > 10:
            st.error(f"⚠️ **Data Alert:** {m_bud:.1f}% of projects are missing budget data. Results may be skewed toward reported values.")

def format_currency(value):
    """Standardized currency shortener for KPIs."""
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    return f"${value:,.0f}"

def render_portfolio_table(df):
    """Handles the multiselect and formatting for the main data table."""
    st.markdown("### Filtered Activity Records")
    all_columns = df.columns.tolist()
    default_cols = ["Project Name", "Municipality", "Sector", "Budget", "Donor", "Status"]
    valid_defaults = [c for c in default_cols if c in all_columns]

    selected_cols = st.multiselect("Columns to view:", options=all_columns, default=valid_defaults)

    if selected_cols:
        display_df = df[selected_cols].copy()
        
        # Apply formatting for the view only
        if "Budget" in display_df.columns:
            display_df["Budget"] = display_df["Budget"].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "$0")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("Select columns above to display the data table.")

def render_geographic_context_box():
    """Renders color-coded info boxes for spatial intensity interpretation."""
    col_a, col_b = st.columns(2)
    with col_a:
        st.info("**💰 Capital-Heavy Areas (Red):** High average cost per project. Suggests infrastructure or large-scale equipment procurement.")
    with col_b:
        st.success("**🏃 Service-Heavy Areas (Blue):** Low average cost per project. Suggests training, social services, or community engagement.")

def render_geographic_gap_table(df):
    # 1. Check if we need to filter by level. 
    # If the column isn't there, we assume the data is already filtered/summarized.
    if "level_areas" in df.columns:
        table_df = df[df["level_areas"] == "Municipality"].copy()
    else:
        table_df = df.copy()

    # 2. Drop geometry if it exists (prevents the Arrow error)
    if hasattr(table_df, 'geometry') or 'geometry' in table_df.columns:
        table_df = pd.DataFrame(table_df.drop(columns=['geometry'], errors='ignore'))

    if table_df.empty:
        st.info("No data to display.")
        return

    # 3. If the data is already summarized (has columns 'Municipality' and 'Activities')
    # we can skip the groupby.
    if "Activities" in table_df.columns:
        gap_data = table_df
    else:
        # Otherwise, we perform the grouping
        gap_data = (
            table_df.groupby("Municipality", as_index=False)
            .agg(
                Activities=("activity_id", "count") if "activity_id" in table_df.columns else ("Sector", "count"),
                Total_Budget=("Budget", "sum")
            )
        )

    # 4. Final Sort and Display
    gap_data = gap_data.sort_values("Activities", ascending=False)
    
    st.write("#### Activity Distribution Detail")
    st.dataframe(gap_data, use_container_width=True, hide_index=True)

def render_cohort_explanation():
    """Renders strategic insights for the Time Dynamics tab."""
    with st.expander("💡 How to read project cohorts"):
        st.markdown("""
        - **Fresh Pipeline (Recent Years):** Should show high **Ongoing** counts. 
        - **Legacy Tail:** Older cohorts still marked as 'Ongoing' may indicate long-term strategic projects or implementation delays.
        - **Turnover:** The point where 'Completed' projects begin to outnumber 'Ongoing' ones defines the average portfolio lifecycle.
        """)

def render_municipality_details(muni_name, filtered_df):
    """Renders the metrics and dataframe for a specific municipality."""
    st.divider()
    st.subheader(f"Detailed Analysis: {muni_name}")
    
    muni_df = filtered_df[filtered_df["Municipality"].str.upper() == muni_name.upper()]
    
    d1, d2, d3 = st.columns(3)
    d1.metric("Activities", len(muni_df))
    d2.metric("Total Budget", f"${muni_df['Budget'].sum():,.0f}")
    
    lead_partner = "N/A"
    if not muni_df.empty and not muni_df['Implementing Agency'].isna().all():
        lead_partner = muni_df['Implementing Agency'].mode()[0]
    d3.metric("Lead Partner", lead_partner)
    
    st.dataframe(muni_df[["Project Name", "Sector", "Budget", "Status"]], use_container_width=True, hide_index=True)