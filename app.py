import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.ml_engine import ScoutBrain

# Setup Halaman
st.set_page_config(page_title="Garuda Scout AI", layout="wide")

# Judul & Intro
st.title("🇮🇩 Garuda Scout AI: Real Market Value Edition")
st.markdown("Sistem Scouting berbasis Data Harga Pasar & Profil Pemain ASEAN")

# Load Brain & Data
try:
    brain = ScoutBrain()
    df = brain.df
except Exception as e:
    st.error(f"Gagal memuat data. Error: {e}")
    st.info("Pastikan file 'data/processed/master_player_db.csv' ada dan tidak kosong.")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter Pemain")

# Filter 1: Liga (Otomatis mengambil dari kolom 'league' yang sudah direname di brain)
available_leagues = df['league'].unique()
league_filter = st.sidebar.multiselect("Pilih Liga/Negara", options=available_leagues, default=available_leagues)

# Filter 2: Posisi
available_positions = df['position'].unique()
pos_filter = st.sidebar.multiselect("Posisi", options=available_positions, default=available_positions)

# Filter 3: Umur
min_age = int(df['age'].min())
max_age = int(df['age'].max())
age_range = st.sidebar.slider("Rentang Umur", min_age, max_age, (min_age, 35))

# Terapkan Filter
filtered_df = df[
    (df['league'].isin(league_filter)) &
    (df['position'].isin(pos_filter)) &
    (df['age'] >= age_range[0]) &
    (df['age'] <= age_range[1])
]

# --- TABS VISUALIZATION ---
tab1, tab2, tab3 = st.tabs(["💰 Market Explorer", "🤖 AI Recommender", "📊 Data Table"])

# TAB 1: Eksplorasi Harga
with tab1:
    st.write(f"Menampilkan {len(filtered_df)} pemain.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Scatter Plot: Umur vs Harga
        # Kita gunakan 'market_value_est' (angka) untuk sumbu Y, 'market_value_raw' (teks) untuk tooltip
        fig = px.scatter(
            filtered_df, 
            x="age", 
            y="market_value_est", 
            color="league", 
            size="market_value_est",
            hover_data=['player_name', 'team', 'position', 'market_value_raw'],
            title="Analisis Potensi: Umur vs Harga Pasar",
            labels={"market_value_est": "Valuasi (Angka)", "age": "Umur"}
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        # Bar Chart: Top 10 Pemain Termahal
        top_players = filtered_df.nlargest(10, 'market_value_est')
        fig_bar = px.bar(
            top_players,
            x='market_value_est',
            y='player_name',
            orientation='h',
            color='league',
            text='market_value_raw',
            title="Top 10 Pemain Termahal (Sesuai Filter)"
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

# TAB 2: AI Similarity (Fix Error)
with tab2:
    st.subheader("Cari Pemain Serupa (Berdasarkan Profil)")
    st.write("Fitur ini mencari pemain dengan **Posisi, Umur, dan Rentang Harga** yang mirip.")
    
    # Dropdown pilih pemain
    target_player = st.selectbox("Pilih Pemain Target", options=df['player_name'].unique())
    
    if st.button("Jalankan AI Scout"):
        try:
            recs = brain.get_similar_players(target_player)
            if recs is not None:
                st.success(f"Rekomendasi Pemain yang mirip dengan {target_player}:")
                st.table(recs)
            else:
                st.warning("Data pemain tidak ditemukan.")
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")

# TAB 3: Data Mentah
with tab3:
    st.subheader("Database Lengkap")
    st.dataframe(filtered_df[['player_name', 'team', 'position', 'age', 'market_value_raw', 'league']])
