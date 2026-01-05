import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
from datetime import datetime

class RealScout:
    def __init__(self):
        self.raw_path = 'data/raw'
        self.processed_path = 'data/processed'
        os.makedirs(self.raw_path, exist_ok=True)
        os.makedirs(self.processed_path, exist_ok=True)
        
        # Base URL Transfermarkt (Versi Indonesia agar mudah diparsing)
        self.base_url = "https://www.transfermarkt.co.id"
        
        # Target Liga (URL Startseite masing-masing liga)
        # ID: Liga 1, TH: Thai League, MY: Super League, VN: V.League 1
        self.targets = {
            'Indonesia': 'https://www.transfermarkt.co.id/super-league/startseite/wettbewerb/IN1L',
            'Thailand': 'https://www.transfermarkt.co.id/thai-league/startseite/wettbewerb/THA1',
            'Malaysia': 'https://www.transfermarkt.co.id/super-league/startseite/wettbewerb/MYS1',
            'Vietnam': 'https://www.transfermarkt.co.id/v-league-1/startseite/wettbewerb/VIE1'
        }

    def _get_headers(self):
        """Memalsukan identitas browser agar tidak ditolak server"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
        ]
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.google.com/'
        }

    def get_soup(self, url):
        """Helper function untuk request + parsing dengan error handling"""
        try:
            # Random Delay (PENTING: Agar tidak di-banned)
            delay = random.uniform(3, 7)
            print(f"⏳ Waiting {delay:.1f}s before fetching {url.split('/')[-1]}...")
            time.sleep(delay)
            
            response = requests.get(url, headers=self._get_headers(), timeout=15)
            
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
            elif response.status_code == 403:
                print(f"⛔ Akses Ditolak (403) ke {url}. IP mungkin di-blokir.")
                return None
            else:
                print(f"⚠️ Error {response.status_code} ke {url}")
                return None
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            return None

    def scrape_teams_from_league(self, league_url):
        """Mengambil URL setiap tim dari halaman klasemen liga"""
        soup = self.get_soup(league_url)
        if not soup: return []
        
        team_urls = []
        # Mencari tabel klasemen/klub (Selector ini spesifik Transfermarkt)
        table = soup.find('table', class_='items')
        if table:
            # Cari semua link nama tim
            links = table.find_all('td', class_='hauptlink')
            for link in links:
                a_tag = link.find('a', href=True)
                if a_tag:
                    full_url = self.base_url + a_tag['href']
                    # Filter: hindari link yang bukan tim (kadang ada link sorting)
                    if '/verein/' in full_url and full_url not in team_urls:
                        team_urls.append(full_url)
        
        # Hapus duplikat dan bersihkan
        return list(set(team_urls))

    def scrape_players_from_team(self, team_url, country_name):
        """Mengambil data skuad pemain dari halaman tim"""
        soup = self.get_soup(team_url)
        if not soup: return []
        
        players_data = []
        
        # Ambil Nama Tim dari Header
        try:
            team_name = soup.find('h1', class_='data-header__headline-wrapper').text.strip()
        except:
            team_name = "Unknown Team"

        print(f"   ⚽ Scouting Squad: {team_name}...")
        
        # Cari Tabel Pemain (Selector "items" biasanya tabel utama di TM)
        table = soup.find('table', class_='items')
        if not table: return []

        # Loop setiap baris pemain (odd/even rows)
        rows = table.find_all('tr', class_=['odd', 'even'])
        
        for row in rows:
            try:
                # 1. Nama & Posisi
                td_name = row.find('table', class_='inline-table')
                if not td_name: continue
                
                name_tag = td_name.find('td', class_='hauptlink').find('a')
                player_name = name_tag.text.strip()
                
                # Posisi biasanya di baris terakhir cell tersebut
                pos_tag = td_name.find_all('tr')[-1].find('td')
                position = pos_tag.text.strip() if pos_tag else "Unknown"

                # 2. Umur (Kolom ke-3 biasanya di TM, tapi bisa geser)
                # Kita cari berdasarkan cell text content yang angka
                cells = row.find_all('td', class_='zentriert')
                age = "0"
                for cell in cells:
                    # Mencari cell yang berisi umur (2 digit)
                    if cell.text.strip().isdigit() and 15 < int(cell.text.strip()) < 45:
                        age = cell.text.strip()
                        break
                
                # 3. Kewarganegaraan
                nat_cell = row.find('td', class_='zentriert', recursive=False)
                # Logic extraksi bendera (skip untuk simplifikasi, anggap local jika tidak ada data)
                
                # 4. Market Value (Harga Pasar)
                mv_cell = row.find('td', class_='rechts hauptlink')
                market_value = mv_cell.text.strip() if mv_cell else "Rp0"
                
                # Bersihkan format Market Value (contoh: "Rp1,2Mlyr")
                market_value_clean = market_value.replace('Rp', '').replace('Mlyr.', '000000').replace('Jt.', '000').replace(',', '').strip()
                if not market_value_clean.isdigit(): market_value_clean = 0
                
                players_data.append({
                    'player_name': player_name,
                    'team': team_name,
                    'league_country': country_name,
                    'position': position,
                    'age': int(age),
                    'market_value_raw': market_value,
                    'market_value_est': int(market_value_clean),
                    'scraped_date': datetime.now().strftime('%Y-%m-%d')
                })
                
            except Exception as e:
                # Skip row jika error parsing
                continue
                
        return players_data

    def run(self):
        print(f"🚀 Memulai Real Data Scraping Agent...")
        all_players = []
        
        for country, league_url in self.targets.items():
            print(f"\n🌍 Masuk ke Liga Negara: {country}")
            print(f"🔗 URL: {league_url}")
            
            # 1. Dapatkan Link semua tim
            team_links = self.scrape_teams_from_league(league_url)
            print(f"📊 Menemukan {len(team_links)} tim di {country}.")
            
            # 2. Loop setiap tim (Batasi 3 tim per negara untuk testing awal, HAPUS [:3] untuk full)
            for team_url in team_links: 
                try:
                    squad = self.scrape_players_from_team(team_url, country)
                    all_players.extend(squad)
                except Exception as e:
                    print(f"Error scraping team {team_url}: {e}")
        
        # 3. Simpan Data
        if all_players:
            df = pd.DataFrame(all_players)
            
            # Basic Cleaning
            df = df.drop_duplicates(subset=['player_name', 'team'])
            
            # Simpan Raw
            filename = f"{self.raw_path}/real_scout_{datetime.now().strftime('%Y%m%d')}.csv"
            df.to_csv(filename, index=False)
            
            # Simpan Processed untuk Dashboard
            df.to_csv(f"{self.processed_path}/master_player_db.csv", index=False)
            
            print(f"\n✅ SCRAPING SELESAI!")
            print(f"Total Pemain: {len(df)}")
            print(f"File tersimpan di: {filename}")
        else:
            print("\n❌ Gagal mendapatkan data (Mungkin terblokir atau struktur web berubah).")

if __name__ == "__main__":
    scout = RealScout()
    scout.run()
