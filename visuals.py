import streamlit as st
import altair as alt
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import folium
from streamlit_folium import st_folium
import branca.colormap as cm
from branca.element import Template, MacroElement

def render_donor_exposure_chart(df):
    """Horizontal bar chart for top 10 donors."""
    exposure = df.groupby("Donor")["Budget"].sum().nlargest(10).reset_index()
    chart = alt.Chart(exposure).mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3).encode(
        x=alt.X("Budget:Q", title="Total Budget (USD)"),
        y=alt.Y("Donor:N", title=None, sort='-x'),
        color=alt.value("#1f4e79"),
        tooltip=["Donor", alt.Tooltip("Budget:Q", format="$,.0f")]
    ).properties(height=350)
    st.altair_chart(chart, use_container_width=True)

def render_sankey_chart(df, title):
    if df.empty:
        st.warning(f"No projects found for {title} in this budget range.")
        return
    
    df_clean = df.copy()
    
    # 1. THE SPACE TRICK: Ensures three distinct columns
    df_clean['Donor_Label'] = df_clean['Donor'].astype(str) + " "
    df_clean['Agency_Label'] = " " + df_clean['Implementing Agency'].astype(str) + "  "
    df_clean['Sector_Label'] = "   " + df_clean['Sector'].astype(str)

    # 2. GROUP DATA
    d1 = df_clean.groupby(['Donor_Label', 'Agency_Label'])['Budget'].sum().reset_index()
    d1.columns = ['source', 'target', 'value']
    
    d2 = df_clean.groupby(['Agency_Label', 'Sector_Label'])['Budget'].sum().reset_index()
    d2.columns = ['source', 'target', 'value']
    
    links = pd.concat([d1, d2], axis=0)
    
    # 3. MAPPING
    nodes = list(pd.concat([links['source'], links['target']]).unique())
    node_dict = {s: i for i, s in enumerate(nodes)}
    links['source_id'] = links['source'].map(node_dict)
    links['target_id'] = links['target'].map(node_dict)

    # 4. BUILD FIGURE
    fig = go.Figure(data=[go.Sankey(
        arrangement="perpendicular", 
        node=dict(
            pad=30, thickness=20, label=nodes, color="#3283a8",
            line=dict(color="white", width=0.5)
        ),
        link=dict(
            source=links['source_id'], target=links['target_id'], 
            value=links['value'], color="rgba(200, 200, 200, 0.3)"
        )
    )])

    # 1. Update traces to kill the shadow/halo
    fig.update_traces(
        textfont_color="black",
        textfont_size=12,
        textfont_family="Arial",
        selector=dict(type='sankey')
    )

    # 2. Update layout (White background and crisp black text)
    fig.update_layout(
        title_text=title, 
        height=800, 
        paper_bgcolor='white', 
        plot_bgcolor='white',
        font=dict(size=12, color="black"),
        margin=dict(l=20, r=20, t=60, b=20)
    )

    # 3. Force CSS-level text shadow removal (Streamlit specific injection)
    st.markdown(
        """
        <style>
        .main svg g.sankey-node text {
            text-shadow: none !important;
            stroke: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.plotly_chart(fig, use_container_width=True)

def render_partner_charts(summary_df):
    import altair as alt
    import streamlit as st
    
    # 1. Prepare the Top 10 internally
    top_volume = summary_df.nlargest(10, "Activities")
    top_intensity = summary_df.nlargest(10, "Avg_Budget_per_Activity")

    col_load, col_intensity = st.columns(2)

    with col_load:
        st.subheader("Partner Load (Activity Volume)")
        load_chart = alt.Chart(top_volume).mark_bar().encode(
            x=alt.X("Activities:Q", title="Number of Activities"),
            y=alt.Y("Implementing Agency:N", sort="-x", title=None),
            color=alt.value("#3EC4D0"),
            tooltip=["Implementing Agency", "Activities"]
        ).properties(height=400)
        st.altair_chart(load_chart, use_container_width=True)

    with col_intensity:
        st.subheader("Partner Intensity (Avg Budget)")
        intensity_chart = alt.Chart(top_intensity).mark_bar().encode(
            x=alt.X("Avg_Budget_per_Activity:Q", title="Avg Budget (USD)"),
            y=alt.Y("Implementing Agency:N", sort="-x", title=None),
            color=alt.value("#43D9E7"),
            tooltip=[
                alt.Tooltip("Implementing Agency"),
                alt.Tooltip("Avg_Budget_per_Activity:Q", format="$,.0f")
            ]
        ).properties(height=400)
        st.altair_chart(intensity_chart, use_container_width=True)

def render_time_intensity_chart(time_summary):
    """Renders intensity chart with mean reference line."""
    base = alt.Chart(time_summary).mark_bar(color="#e76f51").encode(
        x=alt.X("YearStart:O", title=None), 
        y=alt.Y("Avg_Budget_per_Activity:Q", title="Avg Budget (USD)")
    )
    
    mean_line = alt.Chart(time_summary).mark_rule(color="black", strokeDash=[5, 5]).encode(
        y="mean(Avg_Budget_per_Activity):Q"
    )
    
    st.altair_chart(base + mean_line, use_container_width=True)

def show_coordination_table(df, unique_id):
    view_option = st.radio(
        "View coordination by:",
        ["Donor", "Implementing Partner"],
        key=f"toggle_{unique_id}" # <--- Dynamic Unique Key
    )

def render_sector_balance_chart(df):
    """Renders the dual-axis Pareto chart for sector prioritization."""
    # Logic moved from main to visuals to keep main clean
    sector_share = df.groupby("Sector").size().reset_index(name="Total_Activities")
    total_activities = sector_share["Total_Activities"].sum()
    sector_share["Share (%)"] = (sector_share["Total_Activities"] / total_activities) * 100
    sector_share = sector_share.sort_values("Share (%)", ascending=False).reset_index(drop=True)
    sector_share['Rank'] = sector_share.index + 1 
    sector_share['Cumulative (%)'] = sector_share['Share (%)'].cumsum()

    base = alt.Chart(sector_share).encode(
        y=alt.Y("Sector:N", sort=alt.EncodingSortField(field="Share (%)", order="descending"), title=None)
    )

    bar = base.mark_bar(cornerRadiusTopRight=4).encode(
        x=alt.X("Share (%):Q", scale=alt.Scale(domain=[0, 100]), title="Project Share (%)"),
        color=alt.Color("Share (%):Q", scale=alt.Scale(scheme="teals"), legend=None),
        tooltip=["Rank:Q", "Sector:N", "Total_Activities:Q", "Share (%):Q", "Cumulative (%):Q"]
    )

    line = base.mark_line(color="#1f4e79", point=True).encode(
        x=alt.X("Cumulative (%):Q", title="Cumulative Portfolio (%)")
    )
    
    chart = alt.layer(bar, line).properties(height=500, title="Sector Concentration (Pareto)")
    st.altair_chart(chart, use_container_width=True)

def render_sector_kpis(kpi_data):
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        st.metric("Total Sectors", f"{kpi_data['total_sectors']}")

    with kpi_col2:
        st.metric(
            "Dominant Sector", 
            f"{kpi_data['dominant_share']:.1f}%", 
            help=f"Highest concentration: {kpi_data['dominant_sector_name']}"
        )

    with kpi_col3:
        st.metric("SDG Goals Covered", f"{kpi_data['unique_sdgs']}")

    with kpi_col4:
        st.metric("NSDP Pillars Covered", f"{kpi_data['unique_pillars']}")

def render_sdg_chart(summary, col_name):
    if summary is None:
        st.warning("SDG Goal column not found.")
        return

    chart = alt.Chart(summary).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
        y=alt.Y(f"{col_name}:N", sort="-x", title=None),
        x=alt.X("Activities:Q", title="Number of Activities"),
        color=alt.Color("Activities:Q", scale=alt.Scale(scheme="greens"), legend=None),
        tooltip=[col_name, "Activities", alt.Tooltip("Budget Share (%)", format=".1f")]
    ).properties(height=300)
    
    st.subheader("Activities by SDG Goal")
    st.altair_chart(chart, use_container_width=True)

def render_nsdp_chart(summary, col_name):
    if summary is None:
        st.warning("NSDP Pillar column not found.")
        return

    chart = alt.Chart(summary).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
        y=alt.Y(f"{col_name}:N", sort="-x", title=None),
        x=alt.X("Total Budget:Q", title="Total Budget (USD)"),
        color=alt.Color("Total Budget:Q", scale=alt.Scale(scheme="purples"), legend=None),
        tooltip=[col_name, alt.Tooltip("Total Budget:Q", format="$,.0f"), alt.Tooltip("Budget Share (%)", format=".1f")]
    ).properties(height=300)
    
    st.subheader("National Alignment: Budget Allocation by NSDP Pillar")
    st.altair_chart(chart, use_container_width=True)

def render_alignment_comparison(sector_alignment):
    """Side-by-side charts for Activity Share vs Budget Share."""
    sorted_order = sector_alignment["Sector"].tolist()
    
    c_act = alt.Chart(sector_alignment).mark_bar().encode(
        y=alt.Y("Sector:N", sort=sorted_order, title=None),
        x=alt.X("Activity Share (%):Q", title="Activities (%)"),
        color=alt.value("#2a9d8f")
    ).properties(title="Activity Share", height=500)

    c_bud = alt.Chart(sector_alignment).mark_bar().encode(
        y=alt.Y("Sector:N", sort=sorted_order, axis=None),
        x=alt.X("Budget Share (%):Q", title="Budget (%)"),
        color=alt.value("#e76f51")
    ).properties(title="Budget Share", height=500)

    col1, col2 = st.columns(2)
    col1.altair_chart(c_act, use_container_width=True)
    col2.altair_chart(c_bud, use_container_width=True)

def render_muni_top_charts(df):
    """
    Renders Top 10 charts using the activity dataframe.
    """
    # 1. Check if the required column exists
    if "level_areas" not in df.columns:
        # If the column is missing, we try to use the whole DF 
        # but still exclude known National labels
        muni_data = df.copy()
    else:
        # Standard filter
        muni_data = df[df["level_areas"] == "Municipality"].copy()

    # 2. Safety filter for names
    if "Municipality" in muni_data.columns:
        muni_data = muni_data[
            ~muni_data["Municipality"].str.title().isin(["Timor-Leste", "National", "Unknown"])
        ]
    else:
        st.error("Column 'Municipality' not found in data.")
        return

    # 3. Check if we have data left to plot
    if muni_data.empty:
        st.warning("No municipality-specific data found for these filters.")
        return

    # 4. Aggregate
    muni_stats = muni_data.groupby("Municipality").agg(
        Total_Activities=("activity_id", "count"),
        Total_Budget=("Budget", "sum")
    ).reset_index()

    # 5. Sort and slice
    top_act = muni_stats.sort_values("Total_Activities", ascending=False).head(10)
    top_bud = muni_stats.sort_values("Total_Budget", ascending=False).head(10)

    # 6. Render
    col_left, col_right = st.columns(2)

    with col_left:
        chart_act = alt.Chart(top_act).mark_bar(color="#2a9d8f").encode(
            y=alt.Y("Municipality:N", sort="-x", title=None),
            x=alt.X("Total_Activities:Q", title="Number of Activities"),
            tooltip=["Municipality", "Total_Activities"]
        ).properties(title="Top 10 by Activity Count", height=350)
        st.altair_chart(chart_act, use_container_width=True)

    with col_right:
        chart_bud = alt.Chart(top_bud).mark_bar(color="#7b2cbf").encode(
            y=alt.Y("Municipality:N", sort="-x", title=None),
            x=alt.X("Total_Budget:Q", title="Budget Allocation (USD)"),
            tooltip=["Municipality", alt.Tooltip("Total_Budget:Q", format="$,.0f")]
        ).properties(title="Top 10 by Budget Allocation", height=350)
        st.altair_chart(chart_bud, use_container_width=True)

def render_spatial_intensity_chart(df):
    """
    Bar chart showing average project size. 
    Calculated directly from project records to exclude National labels.
    """
    # 1. Filter for Municipality level and exclude National/Timor-Leste
    muni_data = df[
        (df["level_areas"] == "Municipality") & 
        (~df["Municipality"].str.title().isin(["Timor-Leste", "National", "Unknown"]))
    ].copy()

    if muni_data.empty:
        st.warning("No municipality-level budget data available for intensity analysis.")
        return

    # 2. Aggregate to find the Intensity (Average Budget per Activity)
    intensity_stats = muni_data.groupby("Municipality").agg(
        Total_Activities=("activity_id", "count"),
        Total_Budget=("Budget", "sum")
    ).reset_index()

    # Calculate the Average (Intensity)
    intensity_stats["Avg_Budget_Per_Activity"] = (
        intensity_stats["Total_Budget"] / intensity_stats["Total_Activities"]
    )
    
    # Filter out 0s just in case
    intensity_stats = intensity_stats[intensity_stats["Total_Activities"] > 0]
    
    # 3. Calculate the mean for the reference line
    mean_val = intensity_stats["Avg_Budget_Per_Activity"].mean()
    
    # 4. Create the Chart
    chart = alt.Chart(intensity_stats).mark_bar().encode(
        x=alt.X("Avg_Budget_Per_Activity:Q", title="Avg Budget per Activity (USD)"),
        y=alt.Y("Municipality:N", sort="-x", title=None),
        color=alt.condition(
            alt.datum.Avg_Budget_Per_Activity > mean_val,
            alt.value("#e63946"), # Red for above average
            alt.value("#457b9d")  # Blue for below average
        ),
        tooltip=[
            "Municipality", 
            "Total_Activities", 
            alt.Tooltip("Avg_Budget_Per_Activity:Q", format="$,.0f", title="Avg Size"),
            alt.Tooltip("Total_Budget:Q", format="$,.0f", title="Total Budget")
        ]
    ).properties(height=450, title="Project Intensity: Average Budget per Activity")

    # 5. Add the Mean Reference Line
    mean_line = alt.Chart(pd.DataFrame({'mean_val': [mean_val]})).mark_rule(
        color="black", 
        strokeDash=[5, 5],
        size=2
    ).encode(
        x="mean_val:Q"
    )
    
    # Combine and render
    st.altair_chart(chart + mean_line, use_container_width=True)

def get_geographic_summary_table(df):
    """
    Creates a summary table for municipalities, 
    excluding National/Timor-Leste labels.
    """
    # 1. Filter for Municipality-level only
    muni_data = df[
        (df["level_areas"] == "Municipality") & 
        (~df["Municipality"].str.title().isin(["Timor-Leste", "National", "Unknown"]))
    ].copy()

    if muni_data.empty:
        return pd.DataFrame()

    # 2. Aggregate metrics
    table_data = muni_data.groupby("Municipality").agg(
        Total_Activities=("activity_id", "count"),
        Total_Budget=("Budget", "sum"),
        Unique_Donors=("Donor", "nunique"),
        Unique_Sectors=("Sector", "nunique")
    ).reset_index()

    # 3. Calculate Average Intensity
    table_data["Avg_Budget_Per_Project"] = table_data["Total_Budget"] / table_data["Total_Activities"]

    # 4. Sort by highest activity count by default
    return table_data.sort_values("Total_Activities", ascending=False)

def render_annual_pipeline_charts(time_summary):
    """Annual bar charts for volume and value."""
    col_left, col_right = st.columns(2)
    with col_left:
        chart = alt.Chart(time_summary).mark_bar(color="#457b9d").encode(
            x="YearStart:O", y="Total_Activities:Q", tooltip=["YearStart", "Total_Activities"]
        ).properties(title="Volume: New Activities per Year", height=350)
        st.altair_chart(chart, use_container_width=True)
    
    with col_right:
        chart = alt.Chart(time_summary).mark_bar(color="#1d3557").encode(
            x="YearStart:O", y="Budget:Q", tooltip=["YearStart", alt.Tooltip("Budget:Q", format="$,.0f")]
        ).properties(title="Value: Financial Entry per Year", height=350)
        st.altair_chart(chart, use_container_width=True)

def render_cohort_status_chart(cohort_summary):
    """Stacked bar chart for project status cohorts with legend at bottom."""
    
    # 1. Update the color scale to match your actual data labels exactly
    # Make sure "Ongoing – Active" matches the text in your CSV/Excel
    chart = alt.Chart(cohort_summary).mark_bar().encode(
        x=alt.X("YearStart:O", title="Start Year (Cohort)"),
        y=alt.Y("Count:Q", title="Number of Projects"),
        color=alt.Color(
            "Status:N", 
            scale=alt.Scale(
                domain=["Ongoing – Active", "Completed", "Not Identified"], 
                range=["#2a9d8f", "#e9c46a", "#a8dadc"]
            ),
            # 2. Move legend to the bottom
            legend=alt.Legend(
                orient='bottom', 
                title="Project Status",
                direction='horizontal'
            )
        ),
        tooltip=["YearStart", "Status", "Count"]
    ).properties(
        height=450, 
        title="Project Status by Year of Entry"
    )
    
    st.altair_chart(chart, use_container_width=True)

def render_cohort_status_chart(df_input): # I named the input df_input for clarity
    chart = alt.Chart(df_input).mark_bar().encode(
        # ... rest of the chart code ...
    )

def render_interactive_map(map_df, map_metric, map_key="default_map"):
    import folium
    from streamlit_folium import st_folium
    import branca.colormap as cm

    # 1. Initialize Map
    m = folium.Map(location=[-8.85, 125.6], zoom_start=7, tiles="cartodbpositron")

    # 2. Define the Friendly Label for the Legend
    metric_label = "Budget (USD)" if map_metric == "Total_Budget" else "Activities"

    # 3. Define the Style Function with specific color buckets
    def style_function(feature):
        val = feature["properties"].get(map_metric, 0)
        
        # Color Logic to match your legend
        if val == 0 or val is None:
            color = "#ABA9A9" # Grey
        elif val < 25:
            color = '#FFEDA0' # Light Yellow
        elif val < 35:
            color = '#FED976'
        elif val < 44:
            color = '#FEB24C'
        elif val < 54:
            color = '#FD8D3C'
        elif val < 63:
            color = '#FC4E2A'
        else:
            color = '#E31A1C' # Dark Red

        return {
            "fillOpacity": 0.7,
            "weight": 0.5,
            "color": "black",
            "fillColor": color,
        }

    # 4. Prepare GeoJSON features
    features = []
    for _, row in map_df.iterrows():
        budget_fmt = f"${row['Total_Budget']:,.0f}"
        act_count = int(row['Total_Activities'])
        mun_name = str(row['adm1_name'])
        
        status_text = "No Activities" if act_count == 0 else f"{act_count} Activities"
        tooltip_text = f"<b>{mun_name}</b><br>{status_text}<br>{budget_fmt}"

        features.append({
            "type": "Feature",
            "geometry": row["geometry"].__geo_interface__,
            "properties": {
                "adm1_name": mun_name,
                "Total_Activities": act_count,
                "Total_Budget": float(row["Total_Budget"]),
                "tooltip": tooltip_text 
            }
        })

    # 5. Add GeoJSON to Map
    folium.GeoJson(
        data={"type": "FeatureCollection", "features": features},
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(fields=["tooltip"], labels=False)
    ).add_to(m)

    # 6. ADD THE CUSTOM VERTICAL LEGEND
    from branca.element import Template, MacroElement # Ensure these are imported
    
    legend_html = f'''
    {{% macro html(this, kwargs) %}}
    <div style="
        position: fixed; 
        bottom: 50px; 
        right: 50px; 
        width: 150px; 
        background-color: white; border: 1px solid grey; 
        z-index: 9999; font-size: 14px;
        padding: 10px; border-radius: 5px;
    ">
        <b>{metric_label}</b><br>
        <i style="background:#D3D3D3; width:18px; height:18px; float:left; margin-right:8px; opacity:0.7;"></i> 0 / No Data<br>
        <i style="background:#FFEDA0; width:18px; height:18px; float:left; margin-right:8px; opacity:0.7;"></i> 1 - 24<br>
        <i style="background:#FED976; width:18px; height:18px; float:left; margin-right:8px; opacity:0.7;"></i> 25 - 34<br>
        <i style="background:#FEB24C; width:18px; height:18px; float:left; margin-right:8px; opacity:0.7;"></i> 34 - 43<br>
        <i style="background:#FD8D3C; width:18px; height:18px; float:left; margin-right:8px; opacity:0.7;"></i> 43 - 53<br>
        <i style="background:#FC4E2A; width:18px; height:18px; float:left; margin-right:8px; opacity:0.7;"></i> 53 - 62<br>
        <i style="background:#E31A1C; width:18px; height:18px; float:left; margin-right:8px; opacity:0.7;"></i> 62 - 71<br>
    </div>
    {{% endmacro %}}
    '''
    
    macro = MacroElement()
    macro._template = Template(legend_html)
    m.get_root().add_child(macro)

    return st_folium(m, width=None, height=650, key=map_key)

def create_interactive_map(map_df, map_metric):
    """Generates the Folium map with dynamic coloring and clean HTML tooltips."""
    
    # 1. SETUP COLORS
    zero_color = "#dddddd"
    active_colors = ["#c6dbef", "#6baed6", "#4292c6", "#2171b5", "#08306b"]
    pos_values = map_df[map_df[map_metric] > 0][map_metric]
    
    if not pos_values.empty:
        bins = np.linspace(pos_values.min(), pos_values.max(), len(active_colors) + 1).tolist()
    else:
        bins = [0] * (len(active_colors) + 1)

    def get_color(val):
        if val <= 0: return zero_color
        for i in range(len(active_colors)):
            if val <= bins[i+1]: return active_colors[i]
        return active_colors[-1]

    # 2. CREATE THE GEOJSON DATA (Moved from main to here)
    features = []
    for _, row in map_df.iterrows():
        # CLEAN TOOLTIP HTML
        tooltip_html = f"""
            <div style="font-family: 'Helvetica Neue', Arial; font-size: 13px; padding: 10px; min-width: 150px;">
                <strong style="font-size: 15px; color: #1f77b4;">{row['adm1_name']}</strong><br/>
                <hr style="margin: 5px 0; border: 0; border-top: 1px solid #eee;">
                <table style="width: 100%;">
                    <tr><td><b>Activities:</b></td><td style="text-align: right;">{int(row['Activities'])}</td></tr>
                    <tr><td><b>Budget:</b></td><td style="text-align: right;">${row['Total_Budget']:,.0f}</td></tr>
                </table>
                <div style="margin-top: 8px; font-size: 10px; color: #999; text-align: center;">Click municipality for details</div>
            </div>
        """
        
        feature = {
            "type": "Feature",
            "geometry": row["geometry"].__geo_interface__,
            "properties": {
                "adm1_name": str(row["adm1_name"]),
                "metric_val": row[map_metric],
                "clean_tooltip": tooltip_html # Passing the HTML string here
            }
        }
        features.append(feature)

    geo_json_safe = {"type": "FeatureCollection", "features": features}

    # 3. BUILD THE MAP
    m = folium.Map(location=[-8.8, 125.70], zoom_start=8.5, tiles="cartodbpositron")

    folium.GeoJson(
        geo_json_safe,
        style_function=lambda f: {
            "fillColor": get_color(f["properties"]["metric_val"]),
            "color": "white", "weight": 1, "fillOpacity": 0.8,
        },
        highlight_function=lambda x: {"weight": 3, "color": "#f39c12", "fillOpacity": 0.9},
        tooltip=folium.GeoJsonTooltip(
            fields=["clean_tooltip"], 
            labels=False, 
            sticky=True
        )
    ).add_to(m)

    # 3. CONSTRUCT THE DYNAMIC VERTICAL LEGEND
    title = map_metric.replace('_', ' ')
    
    # CSS for the vertical floating legend
    legend_html = f'''
    <div style="
        position: fixed; 
        bottom: 30px; /* Changed from top to bottom */
        right: 20px;  /* Adjusted spacing from the right edge */
        width: 160px; 
        height: auto; 
        background-color: white; 
        border: 1px solid #ccc; 
        z-index:9999; 
        font-family: 'Helvetica Neue', Arial; 
        font-size: 12px;
        padding: 12px; 
        border-radius: 8px; 
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        ">
        <strong style="font-size: 13px;">{title}</strong><br>
        <div style="margin-top: 8px;">
            <i style="background: {zero_color}; width: 18px; height: 18px; float: left; margin-right: 8px; border: 1px solid #ddd;"></i> 
            0 / No Data
        </div>
    '''
    
    # Generate legend rows dynamically
    for i in range(len(active_colors)):
        # Format the numbers for the legend (use $ for budget)
        fmt = lambda x: f"${x:,.0f}" if "Budget" in map_metric else f"{int(x)}"
        low = fmt(bins[i])
        high = fmt(bins[i+1])
        
        legend_html += f'''
        <div style="margin-top: 5px; clear: both;">
            <i style="background: {active_colors[i]}; width: 18px; height: 18px; float: left; margin-right: 8px;"></i> 
            {low} - {high}
        </div>
        '''
    
    legend_html += '</div>'
    m.get_root().html.add_child(folium.Element(legend_html))

    # 4. ADD THE GEOJSON LAYER (with your previous tooltip logic)
    # ... [Keep your previous features loop and folium.GeoJson code here] ...
    # (Ensure you use the get_color function created above)

    return m