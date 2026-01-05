import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans

class ScoutBrain:
    def __init__(self, data_path='data/processed/master_player_db.csv'):
        self.df = pd.read_csv(data_path)
        # Fitur numerik untuk analisis ML
        self.features = ['goals_p90', 'assists_p90', 'interceptions_p90', 'passes_completed', 'age']
        self.scaler = StandardScaler()
        
    def get_similar_players(self, player_name, top_n=5):
        """
        Mencari pemain yang mirip secara statistik (Cosine Similarity).
        Use Case: "Cari pemain murah yang mainnya mirip Marck Klok"
        """
        if player_name not in self.df['player_name'].values:
            return None
            
        # Prepare Data Matrix
        X = self.df[self.features].fillna(0)
        X_scaled = self.scaler.fit_transform(X)
        
        # Cari index pemain target
        target_idx = self.df[self.df['player_name'] == player_name].index[0]
        target_vector = X_scaled[target_idx].reshape(1, -1)
        
        # Hitung Similarity
        similarity_scores = cosine_similarity(target_vector, X_scaled)[0]
        
        # Ambil Top N (exclude diri sendiri)
        similar_indices = similarity_scores.argsort()[::-1][1:top_n+1]
        
        result = self.df.iloc[similar_indices].copy()
        result['similarity_score'] = similarity_scores[similar_indices]
        return result[['player_name', 'team', 'league', 'position', 'age', 'similarity_score']]

    def cluster_players(self, n_clusters=4):
        """
        Mengelompokkan pemain berdasarkan gaya main (bukan posisi di kertas).
        """
        X = self.df[self.features].fillna(0)
        X_scaled = self.scaler.fit_transform(X)
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        self.df['cluster_role'] = kmeans.fit_predict(X_scaled)
        
        return self.df
