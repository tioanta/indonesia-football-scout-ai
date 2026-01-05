import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.ml_engine import ScoutBrain

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Garuda Scout AI", layout="wide")
st.title("🇮🇩 Garuda Scout AI v5.1: Pro Scouting Suite")

# --- LOAD DATA ---
try:
    brain = ScoutBrain()
    df = brain.df
except Exception as e:
    st.error(f"Gagal memuat data: {e}")
    st.stop()

# ==========================================
# 🛠️ SIDEBAR GLOBAL FILTER
# ==========================================
st.sidebar.header("🛠️ Filter Utama")
st.sidebar.caption("Filter ini mempengaruhi Tab Market Explorer & Data")

# 1. Filter Negara/Liga
all_leagues = sorted(df['league'].unique())
sel_leagues = st.sidebar.multiselect("1. Pilih Negara", options=all_leagues, default=all_leagues)

# Filter Data Sementara (Level 1)
df_l1 = df[df['league'].isin(sel_leagues)]

# 2. Filter Klub (Dinamis berdasarkan Liga yg dipilih)
# Jika User belum pilih klub, anggap semua klub terpilih
available_teams = sorted(df_l1['team'].unique())
sel_teams = st.sidebar.multiselect("2. Pilih Klub (Opsional)", options=available_teams)

# Filter Data Sementara (Level 2)
if sel_teams:
    df_l2 = df_l1[df_l1['team'].isin(sel_teams)]
else:
    df_l2 = df_l1 # Tidak ada filter klub

# 3. Filter Posisi (Dinamis berdasarkan Klub yg dipilih)
available_positions = sorted(df_l2['position'].unique())
sel_positions = st.sidebar.multiselect("3. Pilih Posisi (Opsional)", options=available_positions)

# --- FINAL FILTERED DATAFRAME ---
# Ini adalah Dataframe utama yang akan dipakai di Tab 1 & Tab 5 (Data)
main_df = df_l2.copy()
if sel_positions:
    main_df = main_df[main_df['position'].isin(sel_positions)]

# Tampilkan Info Jumlah Data di Sidebar
st.sidebar.markdown("---")
st.sidebar.metric("Data Terpantau", f"{len(main_df)} Pemain")

# ==========================================
# 📑 TABS MENU
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Market Explorer", 
    "🤖 Squad Planner", 
    "🔄 Replacement Finder", 
    "📱 Content Creator",
    "📝 Database"
])

# ==========================================
# TAB 1: MARKET EXPLORER (Updated with Sidebar)
# ==========================================
with tab1:
    st.subheader(f"Analisis Pasar: {', '.join(sel_leagues)}")
    
    if not main_df.empty:
        col1, col2 = st.columns([3, 1])
        with col1:
            # Grafik Scatter yang merespon filter Sidebar
            fig = px.scatter(
                main_df, 
                x="position", 
                y="market_value_est", 
                color="league", 
                size="market_value_est",
                hover_data=['player_name', 'team', 'age', 'market_value_raw'],
                title=f"Sebaran Harga Pemain ({len(main_df)} Data)",
                labels={"market_value_est": "Valuasi (Est)", "position": "Posisi"},
                height=550
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.info("💡 Insight Filter")
            if sel_teams:
                st.write(f"Menampilkan data spesifik untuk klub: **{', '.join(sel_teams)}**")
            else:
                st.write("Menampilkan seluruh klub di liga yang dipilih.")
                
            st.markdown("---")
            avg_val = main_df['market_value_est'].mean()
            st.metric("Rata-rata Harga", f"Rp {avg_val/1e6:,.0f} Jt")
            st.metric("Pemain Termahal", f"Rp {main_df['market_value_est'].max()/1e9:,.1f} M")
    else:
        st.warning("Data kosong. Silakan atur ulang filter di Sidebar.")

# ==========================================
# TAB 2: SQUAD PLANNER (Independent)
# ==========================================
with tab2:
    st.header("🤖 AI Squad Planner")
    st.write("Cari pemain baru berdasarkan **Kebutuhan & Budget Tim**.")
    st.caption("*(Fitur ini menggunakan database global, tidak terpengaruh filter sidebar)*")
    
    c1, c2 = st.columns(2)
    with c1:
        # Menggunakan df original agar bisa memilih tim di luar filter sidebar
        target_team_planner = st.selectbox("Pilih Tim Target", options=sorted(df['team'].unique()), key="t2_team")
    with c2:
        target_pos_planner = st.selectbox("Posisi Dibutuhkan", options=sorted(df['position'].unique()), key="t2_pos")
        
    if st.button("🔍 Cari Pemain Sesuai Budget", key="btn_planner"):
        with st.spinner("Menghitung budget & mencari kandidat..."):
            recs_planner = brain.recommend_for_team_needs(target_team_planner, target_pos_planner)
            
        if recs_planner is not None and not recs_planner.empty:
            st.success(f"Kandidat {target_pos_planner} yang pas untuk budget {target_team_planner}:")
            st.table(recs_planner)
        else:
            st.warning("Tidak ditemukan kandidat yang cocok.")

# ==========================================
# TAB 3: REPLACEMENT FINDER (Player Specific)
# ==========================================
with tab3:
    st.header("🔄 Replacement Finder")
    st.write("Cari pengganti yang **identik** dengan pemain tertentu.")
    
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    # Filter khusus tab ini (agar user bisa cari pemain di luar filter sidebar)
    with col_f1:
        leagues_list = sorted(df['league'].unique())
        sel_league_t3 = st.selectbox("1. Liga", options=leagues_list, key="t3_league")
    with col_f2:
        teams_in_league = sorted(df[df['league'] == sel_league_t3]['team'].unique())
        sel_team_t3 = st.selectbox("2. Klub", options=teams_in_league, key="t3_team")
    with col_f3:
        pos_in_team = sorted(df[(df['league'] == sel_league_t3) & (df['team'] == sel_team_t3)]['position'].unique())
        sel_pos_t3 = st.selectbox("3. Posisi", options=pos_in_team, key="t3_pos")
    with col_f4:
        players_final = sorted(df[(df['league'] == sel_league_t3) & (df['team'] == sel_team_t3) & (df['position'] == sel_pos_t3)]['player_name'].unique())
        sel_player_t3 = st.selectbox("4. Pemain", options=players_final, key="t3_player")
        
    if st.button(f"🔍 Cari Pengganti {sel_player_t3}", key="btn_replace"):
        similar_players = brain.get_similar_players(sel_player_t3, top_n=10)
        if similar_players is not None:
            st.success(f"Rekomendasi Pengganti untuk {sel_player_t3}:")
            st.dataframe(similar_players, hide_index=True)
        else:
            st.error("Data pemain tidak ditemukan.")

# ==========================================
# TAB 4: CONTENT CREATOR
# ==========================================
with tab4:
    st.header("📱 Content Creator Studio")
    st.markdown("Generasi konten visual otomatis.")
    
    st.subheader("1. Fact Finding (Global Data)")
    col_fact1, col_fact2 = st.columns(2)
    
    # Gunakan DF Original untuk Fact Finding agar valid secara statistik global
    with col_fact1:
        st.markdown("#### 💰 The Sultan Clubs")
        team_values = df.groupby('team')['market_value_est'].sum().sort_values(ascending=False).head(5)
        fig_sultan = px.bar(x=team_values.values/1e9, y=team_values.index, orientation='h', 
                           title="Top 5 Skuad Termahal (Milyar Rp)", labels={'x':'Value (Milyar)', 'y':'Club'},
                           color=team_values.values, color_continuous_scale='Viridis')
        fig_sultan.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_sultan, use_container_width=True)

    with col_fact2:
        st.markdown("#### 👶 The Young Guns")
        team_age = df.groupby('team')['age'].mean().sort_values(ascending=True).head(5)
        fig_age = px.bar(x=team_age.values, y=team_age.index, orientation='h',
                        title="Top 5 Skuad Termuda", labels={'x':'Rata-rata Umur', 'y':'Club'},
                        color=team_age.values, color_continuous_scale='Blues_r')
        fig_age.update_layout(yaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig_age, use_container_width=True)

    st.markdown("---")
    st.subheader("2. Player to Watch Generator 📸")
    
    c_gen1, c_gen2 = st.columns([1, 2])
    with c_gen1:
        target_league_content = st.selectbox("Liga Target", options=sorted(df['league'].unique()))
        criteria = st.radio("Tipe Konten", ["💎 Wonderkid", "🛡️ Senior Leader"])
        generate_btn = st.button("🎲 Generate Visual!", type="primary")
    
    if generate_btn:
        with c_gen2:
            subset = df[df['league'] == target_league_content]
            avg_val = subset['market_value_est'].mean()
            
            if "Wonderkid" in criteria:
                candidates = subset[(subset['age'] <= 23) & (subset['market_value_est'] > avg_val)]
                tag, desc = "#Wonderkid", "bintang muda"
            else:
                candidates = subset[(subset['age'] >= 30) & (subset['market_value_est'] > avg_val)]
                tag, desc = "#Veteran", "pemain senior"
            
            if not candidates.empty:
                player = candidates.sample(1).iloc[0]
                
                # Visualisasi Kotak Instagram
                fig_ig = go.Figure()
                fig_ig.add_trace(go.Bar(
                    x=[player['age'], player['market_value_est']], y=['Umur', 'Market Value'],
                    name=player['player_name'], orientation='h', marker_color='#E1306C'
                ))
                fig_ig.update_layout(title=f"PLAYER TO WATCH: {player['player_name']}", template="plotly_dark", height=400, width=400)
                st.plotly_chart(fig_ig)
                
                caption = f"""🔥 PLAYER TO WATCH: {player['player_name']} 🔥\n\nNama: {player['player_name']}\nKlub: {player['team']}\nUmur: {player['age']}\nValue: {player['market_value_raw']}\n\n#GarudaScout {tag} #{player['team'].replace(' ','')}"""
                st.text_area("Caption:", value=caption)
            else:
                st.warning("Belum ada kandidat di kategori ini.")

# ==========================================
# TAB 5: DATABASE (Raw Data)
# ==========================================
with tab5:
    st.header("📝 Database Pemain")
    st.write("Data di bawah ini mengikuti filter Sidebar.")
    st.dataframe(main_df)
