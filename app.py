import streamlit as st
import pandas as pd
import plotly.express as px
from src.ml_engine import ScoutBrain

st.set_page_config(page_title="Garuda Scout AI", layout="wide")
st.title("🇮🇩 Garuda Scout AI v4.0: Complete Suite")

# Load Data
try:
    brain = ScoutBrain()
    df = brain.df
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# --- TAB SETUP ---
tab1, tab2, tab3 = st.tabs(["📊 Market Explorer", "🤖 Squad Planner (Team)", "🔄 Replacement Finder (Player)"])

# ==========================================
# TAB 1: MARKET EXPLORER (General Analysis)
# ==========================================
with tab1:
    st.sidebar.header("🛠️ Filter Market Explorer")
    
    # Filter Sederhana untuk Grafik
    all_leagues = sorted(df['league'].unique())
    selected_leagues_tab1 = st.sidebar.multiselect("Pilih Negara", options=all_leagues, default=all_leagues, key="t1_league")
    
    filtered_df_tab1 = df[df['league'].isin(selected_leagues_tab1)]
    
    st.subheader(f"Analisis Pasar ({len(filtered_df_tab1)} Pemain)")
    
    if not filtered_df_tab1.empty:
        col1, col2 = st.columns([3, 1])
        with col1:
            fig = px.scatter(
                filtered_df_tab1, 
                x="position", 
                y="market_value_est", 
                color="league", 
                size="market_value_est",
                hover_data=['player_name', 'team', 'age', 'market_value_raw'],
                title="Peta Sebaran Harga per Posisi",
                labels={"market_value_est": "Valuasi (Est)", "position": "Posisi Pemain"},
                height=550
            )
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.info("Fitur Market Explorer")
            st.write("Gunakan tab ini untuk melihat tren harga pasar secara umum di berbagai liga.")

# ==========================================
# TAB 2: SQUAD PLANNER (Team Needs)
# ==========================================
with tab2:
    st.header("🤖 AI Squad Planner")
    st.write("Cari pemain baru berdasarkan **Kebutuhan & Budget Tim**.")
    
    c1, c2 = st.columns(2)
    with c1:
        target_team_planner = st.selectbox("Pilih Tim Anda", options=sorted(df['team'].unique()), key="t2_team")
    with c2:
        target_pos_planner = st.selectbox("Posisi yang dibutuhkan", options=sorted(df['position'].unique()), key="t2_pos")
        
    if st.button("🔍 Cari Pemain Sesuai Budget", key="btn_planner"):
        with st.spinner("Menghitung budget & mencari kandidat..."):
            recs_planner = brain.recommend_for_team_needs(target_team_planner, target_pos_planner)
            
        if recs_planner is not None and not recs_planner.empty:
            st.success(f"Kandidat {target_pos_planner} yang pas untuk dompet {target_team_planner}:")
            st.table(recs_planner)
        else:
            st.warning("Tidak ditemukan pemain yang cocok.")

# ==========================================
# TAB 3: REPLACEMENT FINDER (Similarity)
# ==========================================
with tab3:
    st.header("🔄 Replacement Finder")
    st.write("Cari pengganti yang **identik (mirip)** dengan pemain tertentu. Cocok jika pemain kunci Anda cedera atau pindah.")
    
    st.markdown("### 🎯 Siapa pemain yang ingin diganti?")
    
    # --- FILTER BERTINGKAT (CASCADING FILTERS) ---
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    
    # 1. Pilih Negara
    with col_f1:
        leagues_list = sorted(df['league'].unique())
        sel_league = st.selectbox("1. Negara/Liga", options=leagues_list, key="t3_league")
    
    # 2. Pilih Klub (Filter berdasarkan Negara diatas)
    with col_f2:
        teams_in_league = sorted(df[df['league'] == sel_league]['team'].unique())
        sel_team = st.selectbox("2. Klub Asal", options=teams_in_league, key="t3_team")
        
    # 3. Pilih Posisi (Filter berdasarkan Klub diatas)
    with col_f3:
        pos_in_team = sorted(df[(df['league'] == sel_league) & (df['team'] == sel_team)]['position'].unique())
        sel_pos = st.selectbox("3. Posisi", options=pos_in_team, key="t3_pos")
        
    # 4. Pilih Nama Pemain (Filter berdasarkan Posisi diatas)
    with col_f4:
        players_final = sorted(df[
            (df['league'] == sel_league) & 
            (df['team'] == sel_team) & 
            (df['position'] == sel_pos)
        ]['player_name'].unique())
        
        sel_player = st.selectbox("4. Nama Pemain", options=players_final, key="t3_player")
        
    st.markdown("---")
    
    # Tombol Eksekusi
    if st.button(f"🔍 Cari Pengganti {sel_player}", key="btn_replace"):
        with st.spinner(f"Mencari kembaran statistik {sel_player}..."):
            # Panggil fungsi similarity dari brain
            similar_players = brain.get_similar_players(sel_player, top_n=10)
            
        if similar_players is not None:
            st.success(f"Rekomendasi Pengganti untuk {sel_player} ({sel_team}):")
            
            # Tampilkan Data
            st.dataframe(
                similar_players, 
                column_config={
                    "similarity_score": st.column_config.ProgressColumn(
                        "Tingkat Kemiripan",
                        help="Semakin mendekati 100%, semakin mirip profil umur & harganya",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100,
                    ),
                },
                hide_index=True
            )
            
            st.caption("*Similarity Score dihitung berdasarkan kedekatan Umur dan Market Value.")
        else:
            st.error("Data pemain tidak ditemukan.")
