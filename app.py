import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.ml_engine import ScoutBrain

# Setup Halaman
st.set_page_config(page_title="Garuda Scout AI", layout="wide")

# Judul & Intro
st.title("🇮🇩 Garuda Scout AI: Agentic Scouting Dashboard")
st.markdown("Automated Scouting System untuk Liga 1, 2, & 3 Indonesia")

# Load Brain
try:
    brain = ScoutBrain()
    df = brain.df
except FileNotFoundError:
    st.error("Data belum tersedia. Jalankan script scraper.py dulu!")
    st.stop()

# Sidebar Filters
st.sidebar.header("Filter Scouting")
league_filter = st.sidebar.multiselect("Pilih Liga", options=df['league'].unique(), default=df['league'].unique())
pos_filter = st.sidebar.multiselect("Posisi", options=df['position'].unique(), default=df['position'].unique())
age_range = st.sidebar.slider("Rentang Umur", 15, 40, (17, 30))

# Filter Dataframe
filtered_df = df[
    (df['league'].isin(league_filter)) &
    (df['position'].isin(pos_filter)) &
    (df['age'] >= age_range[0]) &
    (df['age'] <= age_range[1])
]

# Tab Layout
tab1, tab2, tab3 = st.tabs(["🔍 Player Explorer", "🤖 AI Recommender", "📈 Compare Tool"])

with tab1:
    st.write(f"Menampilkan {len(filtered_df)} pemain sesuai kriteria.")
    
    # Visualisasi Scatter Plot (Quadrant Analysis)
    col1, col2 = st.columns(2)
    with col1:
        x_axis = st.selectbox("X Axis (Metrik)", options=['passes_completed', 'minutes_played', 'age'])
    with col2:
        y_axis = st.selectbox("Y Axis (Metrik)", options=['interceptions_p90', 'goals_p90', 'assists_p90'])
        
    fig = px.scatter(filtered_df, x=x_axis, y=y_axis, color="league", hover_data=['player_name', 'team'],
                     title=f"Analisis Kuadran: {x_axis} vs {y_axis}")
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(filtered_df)

with tab2:
    st.subheader("Cari 'The Next...'")
    st.write("Gunakan AI untuk mencari pemain murah yang mirip dengan pemain bintang.")
    
    target_player = st.selectbox("Pilih Pemain Bintang (Target)", options=df['player_name'].unique())
    
    if st.button("Cari Rekomendasi AI"):
        recs = brain.get_similar_players(target_player)
        if recs is not None:
            st.success(f"Top 5 Pemain yang mirip dengan {target_player}:")
            st.table(recs)
        else:
            st.warning("Pemain tidak ditemukan.")

with tab3:
    st.subheader("Head-to-Head Comparison")
    p1 = st.selectbox("Pemain 1", options=df['player_name'].unique(), index=0)
    p2 = st.selectbox("Pemain 2", options=df['player_name'].unique(), index=1)
    
    p1_data = df[df['player_name'] == p1].iloc[0]
    p2_data = df[df['player_name'] == p2].iloc[0]
    
    categories = ['goals_p90', 'assists_p90', 'interceptions_p90', 'passes_completed']
    
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=[p1_data[c] for c in categories],
        theta=categories,
        fill='toself',
        name=p1
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=[p2_data[c] for c in categories],
        theta=categories,
        fill='toself',
        name=p2
    ))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True)
    st.plotly_chart(fig_radar, use_container_width=True)
