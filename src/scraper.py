import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import numpy as np

class FootballScraper:
    def __init__(self):
        # Folder untuk menyimpan data
        self.raw_path = 'data/raw'
        self.processed_path = 'data/processed'
        os.makedirs(self.raw_path, exist_ok=True)
        os.makedirs(self.processed_path, exist_ok=True)

    def scrape_league_data(self, url=None):
        """
        Fungsi utama scraping. 
        Note: Karena saya AI, saya tidak bisa direct hit website ber-IP block.
        Di bawah adalah logika BeautifulSoup standard.
        """
        print(f"[{datetime.now()}] Memulai Scouting Agent...")
        
        # --- BLOK LOGIKA SCRAPING NYATA (Uncomment & Sesuaikan Selector) ---
        # headers = {'User-Agent': 'Mozilla/5.0'}
        # response = requests.get(url, headers=headers)
        # soup = BeautifulSoup(response.content, 'html.parser')
        # table = soup.find('table', {'class': 'stats-table'}) # Sesuaikan class
        # df = pd.read_html(str(table))[0]
        # -------------------------------------------------------------------

        # --- BLOK DATA DUMMY (Agar script ini runnable & testable sekarang) ---
        # Membuat data sintetis Liga 1 & 2 Indonesia untuk testing logika ML
        print("Mode: Generating Synthetic Data (Simulasi Liga 1 & 2)")
        np.random.seed(42)
        n_players = 200
        data = {
            'player_name': [f'Pemain_{i}' for i in range(n_players)],
            'team': np.random.choice(['Persib', 'Persija', 'Persebaya', 'PSIS', 'Persis', 'Arema', 'PSIM', 'Persela'], n_players),
            'league': np.random.choice(['Liga 1', 'Liga 2'], n_players, p=[0.6, 0.4]),
            'position': np.random.choice(['FW', 'MF', 'DF', 'GK'], n_players),
            'age': np.random.randint(17, 35, n_players),
            'minutes_played': np.random.randint(0, 2700, n_players),
            'goals': np.random.poisson(3, n_players),
            'assists': np.random.poisson(2, n_players),
            'passes_completed': np.random.normal(300, 100, n_players),
            'interceptions': np.random.normal(15, 5, n_players),
            'market_value_eur': np.random.randint(25000, 500000, n_players)
        }
        df = pd.DataFrame(data)
        
        # Logika Bisnis: Hapus pemain yang menit bermainnya terlalu sedikit
        df = df[df['minutes_played'] > 500].reset_index(drop=True)
        
        # Simpan Raw Data
        filename = f"{self.raw_path}/scouted_players_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False)
        print(f"Data tersimpan di: {filename}")
        
        return df

    def run_pipeline(self):
        # 1. Scrape / Generate
        df = self.scrape_league_data()
        
        # 2. Feature Engineering Dasar
        # Normalisasi per 90 menit (Penting untuk perbandingan yang adil)
        df['goals_p90'] = df['goals'] / (df['minutes_played'] / 90)
        df['assists_p90'] = df['assists'] / (df['minutes_played'] / 90)
        df['interceptions_p90'] = df['interceptions'] / (df['minutes_played'] / 90)
        
        # 3. Simpan sebagai 'Current Database' untuk Dashboard
        df.to_csv(f"{self.processed_path}/master_player_db.csv", index=False)
        print("Pipeline Selesai. Database Updated.")

if __name__ == "__main__":
    bot = FootballScraper()
    bot.run_pipeline()
