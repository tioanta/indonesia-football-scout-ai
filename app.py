import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.ml_engine import ScoutBrain

# Setup Halaman
st.set_page_config(page_title="Garuda Scout AI", layout="wide")

# Judul & Intro
st.title("🇮🇩 Garuda Scout AI: Agentic Scouting Dashboard")
st.markdown("Automated Scouting System (Real Market Value Data)")

# Load Brain
try:
    brain = ScoutBrain()
    df = brain.df
    
    # -----------------------------------------------------------
    # FIX 1: Rename kolom agar kompatibel dengan logika lama
    # Mengubah 'league_country' menjadi 'league' agar tidak KeyError
    # -----------------------------------------------------------
    if 'league_country' in df.columns:
        df.rename(columns={'league_country': 'league'}, inplace=True)
        
except Exception as e:
    st.error(f"Terjadi kesalahan saat memuat data: {e}")
    st.info("Pastikan Anda sudah menjalankan 'python src/scraper.py' sukses.")
    st.stop()

# Sidebar Filters
st.sidebar.header("Filter Scouting")

# Filter Negara/Liga
available_leagues = df['league'].unique() if 'league' in df.columns else []
league_filter = st.sidebar.multiselect("Pilih Negara Liga", options=available_leagues, default=available_leagues)

# Filter Posisi
available_positions = df['position'].unique() if 'position' in df.columns else []
pos_filter = st.sidebar.multiselect("Posisi", options=available_positions, default=available_positions)

# Filter Umur
min_age, max_age = int(df['age'].min()), int(df['age'].max())
age_range = st.sidebar.slider("Rentang Umur", min_age, max_age, (min_age, 35))

# Filter Dataframe
filtered_df = df[
    (df['league'].isin(league_filter)) &
    (df['position'].isin(pos_filter)) &
    (df['age'] >= age_range[0]) &
    (df['age'] <= age_range[1])
]

# Tab Layout
tab1, tab2, tab3 = st.tabs(["🔍 Market Explorer", "🤖 AI Similarity", "⚖️ Head-to-Head"])

with tab1:
    st.write(f"Menampilkan {len(filtered_df)} pemain.")
    
    # FIX 2: Visualisasi disesuaikan dengan Data yang ADA (Market Value & Age)
    # Kita tidak memakai goals/assists karena Real Scraper belum mengambilnya
    
    col1, col2 = st.columns(2)
    with col1:
        # Scatter Plot: Umur vs Harga Pasaran
        fig = px.scatter(
            filtered_df, 
            x="age", 
            y="market_value_est", 
            color="league", 
            size="market_value_est",
            hover_data=['player_name', 'team', 'position', 'market_value_raw'],
            title="Analisis Potensi: Umur vs Harga Pasar",
            labels={"market_value_est": "Estimasi Harga (Rupiah)", "age": "Umur"}
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        # Bar Chart: Top 10 Pemain Termahal di Filter Terpilih
        top_players = filtered_df.nlargest(10, 'market_value_est')
        fig_bar = px.bar(
            top_players,
            x='market_value_est',
            y='player_name',
            orientation='h',
            color='league',
            title="Top 10 Pemain Termahal (Sesuai Filter)",
            text='market_value_raw'
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.dataframe(filtered_df[['player_name', 'team', 'position', 'age', 'market_value_raw', 'league']])

with tab2:
    st.subheader("Cari Pemain Mirip (Berdasarkan Profil & Harga)")
    st.write("Algoritma mencari kemiripan berdasarkan: Umur, Harga Pasar, dan Posisi.")
    
    target_player = st.selectbox("Pilih Pemain Target", options=df['player_name'].unique())
    
    if st.button("Jalankan AI Recommender"):
        try:
            recs = brain.get_similar_players(target_player)
            if recs is not None:
                st.success(f"Rekomendasi untuk alternatif {target_player}:")
                st.table(recs)
            else:
                st.warning("Pemain tidak ditemukan.")
        except Exception as e:
            st.error(f"Error pada AI Engine: {e}")

with tab3:
    st.subheader("Perbandingan Pemain")
    c1, c2 = st.columns(2)
    with c1:
        p1 = st.selectbox("Pemain 1", options=df['player_name'].unique(), index=0)
    with c2:
        p2 = st.selectbox("Pemain 2", options=df['player_name'].unique(), index=1)
    
    p1_data = df[df['player_name'] == p1].iloc[0]
    p2_data = df[df['player_name'] == p2].iloc[0]
    
    # Simple Comparison Metric
    col_a, col_b = st.columns(2)
    col_a.metric(label=f"Harga {p1}", value=p1_data['market_value_raw'])
    col_b.metric(label=f"Harga {p2}", value=p2_data['market_value_raw'], 
                 delta=int(p2_data['market_value_est'] - p1_data['market_value_est']))
    
    st.info("Fitur Radar Chart dinonaktifkan sementara karena data statistik detail (Gol/Assist) belum tersedia di Real Scraper.")
