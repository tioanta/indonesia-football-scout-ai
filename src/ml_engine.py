import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans

class ScoutBrain:
    def __init__(self, data_path='data/processed/master_player_db.csv'):
        # Load Data
        self.df = pd.read_csv(data_path)
        
        # --- PERBAIKAN PENTING ---
        # Rename kolom 'league_country' menjadi 'league' agar konsisten
        if 'league_country' in self.df.columns:
            self.df.rename(columns={'league_country': 'league'}, inplace=True)
            
        # Tentukan fitur yang ADA di data Real Scraper (Hanya Age & Market Value)
        # Kita hapus goals_p90 dll karena tidak ada di CSV hasil scraping
        self.features = ['age', 'market_value_est']
        
        # Bersihkan data NaN (jika ada)
        self.df[self.features] = self.df[self.features].fillna(0)
        
        # Siapkan Scaler
        self.scaler = StandardScaler()
        
    def get_similar_players(self, player_name, top_n=5):
        """Mencari pemain mirip berdasarkan Umur dan Harga Pasar"""
        if player_name not in self.df['player_name'].values:
            return None
            
        # Ambil posisi pemain target (karena kita hanya ingin membandingkan sesama posisi)
        target_pos = self.df[self.df['player_name'] == player_name]['position'].values[0]
        
        # Filter: Hanya bandingkan dengan pemain di POSISI YANG SAMA
        df_pos = self.df[self.df['position'] == target_pos].reset_index(drop=True)
        
        # Siapkan Data Matrix
        X = df_pos[self.features]
        X_scaled = self.scaler.fit_transform(X)
        
        # Cari index pemain target
        target_idx = df_pos[df_pos['player_name'] == player_name].index[0]
        target_vector = X_scaled[target_idx].reshape(1, -1)
        
        # Hitung Similarity
        similarity_scores = cosine_similarity(target_vector, X_scaled)[0]
        
        # Ambil Top N
        similar_indices = similarity_scores.argsort()[::-1][1:top_n+1]
        
        result = df_pos.iloc[similar_indices].copy()
        # Ubah skor 0-1 menjadi persentase 0-100%
        result['similarity_score'] = (similarity_scores[similar_indices] * 100).round(1)
        
        return result[['player_name', 'team', 'league', 'age', 'market_value_raw', 'similarity_score']]

    def cluster_players(self, n_clusters=3):
        X = self.df[self.features]
        X_scaled = self.scaler.fit_transform(X)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        self.df['cluster_group'] = kmeans.fit_predict(X_scaled)
        return self.df
