import os
import re
import pandas as pd
import streamlit as st
import plotly.express as px
import folium
from streamlit_folium import st_folium
import networkx as nx

# Optional (nice table)
try:
    from st_aggrid import AgGrid, GridOptionsBuilder
    HAS_AGGRID = True
except Exception:
    HAS_AGGRID = False

# ---------------------------
# App Config & Branding
# ---------------------------
st.set_page_config(page_title="Business Insights Dashboard", layout="wide")
col_logo, col_title = st.columns([1, 6])
with col_logo:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", use_container_width=True)
with col_title:
    st.title("📊 Business Insights Dashboard")

# ---------------------------
# Load & Clean
# ---------------------------
def load_data() -> pd.DataFrame:
    # support either /data/companies.csv or ./companies.csv
    candidate_paths = ["data/companies.csv", "companies.csv"]
    path = next((p for p in candidate_paths if os.path.exists(p)), None)
    if not path:
        st.error("Could not find data file. Place it at `data/companies.csv` or `./companies.csv`.")
        st.stop()
    df_ = pd.read_csv(path)

    # normalize columns expected by the app
    for col in ["website", "email", "phone", "keywords", "city", "co_name", "contact"]:
        if col not in df_.columns:
            df_[col] = pd.NA

    df_["website"] = df_["website"].fillna("No Website").astype(str)
    df_["email"] = df_["email"].fillna("No Email").astype(str)
    df_["phone"] = df_["phone"].astype(str)
    df_["city"] = df_["city"].astype(str)
    df_["co_name"] = df_["co_name"].astype(str)
    df_["contact"] = df_["contact"].astype(str)

    # basic validators
    df_["has_email"] = df_["email"].str.contains(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", flags=re.I, regex=True)
    df_["has_website"] = df_["website"].str.contains(r"\.", regex=True) & (df_["website"] != "No Website")
    df_["has_phone"] = df_["phone"].str.len() > 6

    # simple lead score (UI will filter on this)
    df_["lead_score"] = (
        df_["has_email"].astype(int) * 40
        + df_["has_phone"].astype(int) * 30
        + df_["has_website"].astype(int) * 20
        + df_["keywords"].fillna("").astype(str).apply(lambda s: min(10, len([k for k in s.split(",") if k.strip()])))
    )

    # explode keywords for charts
    df_["keywords_norm"] = (
        df_["keywords"].fillna("").astype(str).str.lower().str.split(",")
        .apply(lambda lst: [x.strip() for x in lst if x.strip()])
    )
    return df_

@st.cache_data
def get_data():
    return load_data()

df = get_data()

# ---------------------------
# Sidebar: Global Filters
# ---------------------------
st.sidebar.header("🔍 Global Filters")

all_cities = sorted(df["city"].dropna().unique().tolist())
sel_cities = st.sidebar.multiselect("City", options=all_cities, default=all_cities)

# build service list from keywords
all_services = sorted(set([k for ks in df["keywords_norm"] for k in ks])) if len(df) else []
sel_services = st.sidebar.multiselect("Service/Keyword", options=all_services, default=all_services)

min_ls, max_ls = int(df["lead_score"].min()), int(df["lead_score"].max())
sel_min, sel_max = st.sidebar.slider("Lead Score Range", min_ls, max_ls, (min_ls, max_ls))

# apply filters
def apply_filters(_df: pd.DataFrame) -> pd.DataFrame:
    out = _df[_df["city"].isin(sel_cities)]
    if sel_services:
        out = out[out["keywords_norm"].apply(lambda lst: any(k in lst for k in sel_services))]
    out = out[(out["lead_score"] >= sel_min) & (out["lead_score"] <= sel_max)]
    return out

filtered_df = apply_filters(df)

# keep in session (nice UX when switching tabs)
st.session_state["filters"] = {
    "cities": sel_cities,
    "services": sel_services,
    "lead_score": (sel_min, sel_max)
}

# ---------------------------
# KPI Header (sticky section)
# ---------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Companies", len(filtered_df))
k2.metric("Cities Covered", filtered_df["city"].nunique())
k3.metric("% with Website", f"{(filtered_df['has_website'].mean()*100):.1f}%")
k4.metric("Top City", filtered_df["city"].mode().iat[0] if len(filtered_df) else "—")

st.write("---")

# ---------------------------
# Tabs
# ---------------------------
tab_overview, tab_services, tab_leads, tab_map, tab_network, tab_quality = st.tabs(
    ["🏠 Overview", "📈 Services", "📊 Leads", "🗺️ Map", "🕸️ Network", "✅ Data Quality"]
)

# ---- Overview ----
with tab_overview:
    c1, c2 = st.columns(2)

    # city distribution
    city_counts = filtered_df["city"].value_counts().reset_index()
    city_counts.columns = ["City", "Count"]
    fig_city = px.bar(city_counts.head(15), x="City", y="Count", title="Top Cities by Company Count", text="Count")
    c1.plotly_chart(fig_city, use_container_width=True)

    # online presence
    presence = pd.DataFrame({
        "Channel": ["Phone", "Email", "Website"],
        "Count": [
            filtered_df["has_phone"].sum(),
            filtered_df["has_email"].sum(),
            filtered_df["has_website"].sum()
        ]
    })
    fig_presence = px.pie(presence, names="Channel", values="Count", title="Online Presence Mix")
    c2.plotly_chart(fig_presence, use_container_width=True)

    st.success(
        f"✅ {len(filtered_df)} companies match your filters. "
        f"{(filtered_df['has_website'].mean()*100):.1f}% have websites and "
        f"{(filtered_df['has_email'].mean()*100):.1f}% have valid emails — strong digital leads."
    )

# ---- Services ----
with tab_services:
    # build service frequency from filtered set
    services_series = (
        filtered_df["keywords_norm"]
        .explode()
        .dropna()
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Service", "keywords_norm": "Count"})
    )

    c1, c2 = st.columns(2)
    if not services_series.empty:
        fig_treemap = px.treemap(services_series, path=["Service"], values="Count", title="Service Distribution (Treemap)")
        c1.plotly_chart(fig_treemap, use_container_width=True)

        fig_bar = px.bar(services_series.head(15), x="Service", y="Count", title="Top Services", text="Count")
        c2.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No services to display for the current filters.")

# ---- Leads ----
with tab_leads:
    st.subheader("Lead List")

    show_cols = ["co_name", "contact", "email", "phone", "city", "lead_score", "website", "keywords"]
    leads_view = filtered_df[show_cols].sort_values(by="lead_score", ascending=False)

    if HAS_AGGRID:
        gb = GridOptionsBuilder.from_dataframe(leads_view)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_side_bar()
        gb.configure_default_column(filter=True, sortable=True, resizable=True, floatingFilter=True)
        gridOptions = gb.build()
        AgGrid(leads_view, gridOptions=gridOptions, theme="streamlit")
    else:
        st.dataframe(leads_view, use_container_width=True)

    st.download_button(
        "📥 Download Leads (CSV)",
        data=leads_view.to_csv(index=False),
        file_name="leads_export.csv",
        mime="text/csv",
        use_container_width=True
    )

# ---- Map ----
with tab_map:
    st.subheader("Interactive Map")
    # if you later geocode to lat/lon, use those columns; for now center on India
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5)
    # fallback: place city markers without lat/lon (rough demo)
    # You can replace this with geocoded lat/lon per row.
    for _, row in filtered_df.iterrows():
        popup = f"<b>{row['co_name']}</b><br>{row['city']}<br>Score: {row['lead_score']}<br>" \
                f"<a href='mailto:{row['email']}'>Email</a> | <a href='tel:{row['phone']}'>Call</a>"
        folium.Marker([20.5937, 78.9629], popup=folium.Popup(popup, max_width=300)).add_to(m)

    st_folium(m, height=550, use_container_width=True)

# ---- Network ----
with tab_network:
    st.subheader("Company–City Network")
    # Simple bipartite graph: city <-> company
    G = nx.Graph()
    for _, r in filtered_df.iterrows():
        city_node = f"city::{r['city']}"
        comp_node = f"co::{r['co_name']}"
        G.add_node(city_node, type="city")
        G.add_node(comp_node, type="company", score=int(r["lead_score"]))
        G.add_edge(city_node, comp_node)

    # centrality as "reach"
    if len(G.nodes) > 0:
        centrality = nx.betweenness_centrality(G)
        top10 = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        top_df = pd.DataFrame([{"Node": k, "Betweenness": v} for k, v in top10])
        st.write("**Top 10 nodes by betweenness centrality (reach):**")
        st.table(top_df)
    else:
        st.info("Network is empty for the selected filters.")

    st.caption("Tip: later, render the network with PyVis for an interactive graph.")

# ---- Data Quality ----
with tab_quality:
    st.subheader("Data Quality Report")
    dq = pd.DataFrame({
        "column": df.columns,
        "missing_%": [float(df[c].isna().mean()*100) for c in df.columns],
        "unique": [df[c].nunique() for c in df.columns],
        "dtype": [str(df[c].dtype) for c in df.columns],
    }).sort_values("missing_%", ascending=False)
    st.dataframe(dq, use_container_width=True)

    dupes = df.duplicated(subset=["co_name", "city"], keep=False)
    st.write(f"**Duplicate rows (by company+city): {dupes.sum()}**")
    if dupes.any():
        st.dataframe(df.loc[dupes, ["co_name", "city", "email", "phone"]].sort_values(["co_name", "city"]))
