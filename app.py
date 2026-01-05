import streamlit as st
import pandas as pd
import plotly.express as px
from src.ml_engine import ScoutBrain

st.set_page_config(page_title="Garuda Scout AI", layout="wide")
st.title("🇮🇩 Garuda Scout AI v3.0: Squad Planner Edition")

# Load Data
try:
    brain = ScoutBrain()
    df = brain.df
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# --- SIDEBAR: HIERARCHICAL FILTER ---
st.sidebar.header("🛠️ Filter Bertingkat")

# Level 1: Negara
all_leagues = sorted(df['league'].unique())
selected_leagues = st.sidebar.multiselect("1. Pilih Negara/Liga", options=all_leagues, default=all_leagues)

# Filter DF sementara berdasarkan Liga
temp_df = df[df['league'].isin(selected_leagues)]

# Level 2: Klub (Opsional - Jika kosong berarti semua klub di negara itu)
available_teams = sorted(temp_df['team'].unique())
selected_teams = st.sidebar.multiselect("2. Pilih Klub (Opsional)", options=available_teams)

# Filter DF sementara berdasarkan Tim
if selected_teams:
    temp_df = temp_df[temp_df['team'].isin(selected_teams)]

# Level 3: Posisi
available_positions = sorted(temp_df['position'].unique())
selected_positions = st.sidebar.multiselect("3. Pilih Posisi", options=available_positions, default=available_positions)

# --- FINAL FILTERED DATAFRAME ---
filtered_df = temp_df[temp_df['position'].isin(selected_positions)]

# --- MAIN TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Market Explorer", "🤖 Squad Planner (AI)", "📝 Database"])

# TAB 1: Market Explorer (Grafik Posisi)
with tab1:
    st.subheader(f"Analisis Pasar ({len(filtered_df)} Pemain Terpantau)")
    
    # Check data availability
    if not filtered_df.empty:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # REQUEST: Sumbu X adalah Posisi
            fig = px.scatter(
                filtered_df, 
                x="position",  # <--- SUMBU X DIUBAH KE POSISI
                y="market_value_est", 
                color="league", 
                size="market_value_est",
                hover_data=['player_name', 'team', 'age', 'market_value_raw'],
                title="Peta Sebaran Harga per Posisi",
                labels={"market_value_est": "Valuasi (Est)", "position": "Posisi Pemain"},
                height=550
            )
            # Update layout agar label sumbu X miring jika terlalu padat
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.info("💡 **Cara Baca Grafik**")
            st.write("Setiap titik adalah satu pemain.")
            st.write("• **Atas:** Pemain Mahal (Bintang).")
            st.write("• **Bawah:** Pemain Murah/Muda.")
            st.write("• **Warna:** Menunjukkan asal Liga.")
            st.markdown("---")
            st.metric("Total Value (Filter)", f"Rp {filtered_df['market_value_est'].sum() / 1e9:.1f} M")
    else:
        st.warning("Data kosong dengan filter saat ini.")

# TAB 2: Squad Planner (Rekomendasi per Posisi)
with tab2:
    st.header("🤖 AI Squad Planner")
    st.write("Pilih klub dan posisi yang ingin diperkuat. AI akan mencari pemain yang **sesuai budget klub tersebut**.")
    
    col_input1, col_input2 = st.columns(2)
    
    with col_input1:
        # Pilih Klub Target (Untuk perencanaan)
        # Kita ambil list klub full dari database original agar user bisa pilih bebas
        target_team = st.selectbox("A. Klub Mana yang ingin belanja?", options=sorted(df['team'].unique()))
    
    with col_input2:
        # Pilih Posisi Target
        # Ambil daftar posisi unik dari database
        target_pos = st.selectbox("B. Butuh pemain posisi apa?", options=sorted(df['position'].unique()))
    
    if st.button("🔍 Cari Rekomendasi Pemain"):
        with st.spinner(f"AI sedang menganalisis kekuatan finansial {target_team}..."):
            recommendations = brain.recommend_for_team_needs(target_team, target_pos)
        
        if recommendations is not None and not recommendations.empty:
            st.success(f"Ditemukan {len(recommendations)} kandidat {target_pos} yang cocok untuk budget {target_team}:")
            
            # Tampilkan Hasil
            st.table(recommendations[['player_name', 'age', 'team', 'league', 'market_value_raw']])
            
            # Visualisasi Perbandingan Harga
            st.caption("Perbandingan Harga Kandidat vs Estimasi Budget Klub")
            st.bar_chart(recommendations.set_index('player_name')['market_value_est'])
            
        else:
            st.error("Tidak ditemukan pemain yang cocok.")
            st.write("Kemungkinan: Data klub target belum lengkap untuk menghitung budget, atau tidak ada pemain di range harga tersebut.")

# TAB 3: Raw Data
with tab3:
    st.dataframe(filtered_df)
