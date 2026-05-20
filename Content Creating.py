import os
import sys
import json
import time
from datetime import datetime
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, RateLimitError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt
from rich.progress import track
from rich import print as rprint
from rich.layout import Layout
import tabulate

console = Console()
SESSION_FILE = "ig_session.json"
DATA_FILE = "ig_data_cache.json"

class InstagramAnalyzer:
    def __init__(self):
        self.cl = Client()
        self.user_id = None
        self.username = None
        self.followers_count = 0
        self.posts_data = []

    def login(self, username, password):
        """Login to Instagram with session persistence."""
        self.username = username
        try:
            if os.path.exists(SESSION_FILE):
                console.print("[yellow]Memuat session tersimpan...[/yellow]")
                self.cl.load_settings(SESSION_FILE)
                self.cl.login(username, password)
                self.cl.get_timeline_feed() # Validate session
            else:
                console.print("[yellow]Login baru...[/yellow]")
                self.cl.login(username, password)
                self.cl.dump_settings(SESSION_FILE)
            
            console.print("[green]Login berhasil![/green]")
            
            # Get user info
            user_info = self.cl.user_info_by_username(username)
            self.user_id = user_info.pk
            self.followers_count = user_info.follower_count
            return True
        except Exception as e:
            console.print(f"[red]Error saat login: {e}[/red]")
            return False

    def fetch_data(self, limit=30):
        """Fetch recent posts data."""
        if not self.user_id:
            console.print("[red]Harap login terlebih dahulu![/red]")
            return False

        console.print(f"[yellow]Mengambil {limit} postingan terakhir... ini mungkin memakan waktu.[/yellow]")
        try:
            medias = self.cl.user_medias(self.user_id, amount=limit)
            self.posts_data = []
            
            for media in track(medias, description="Memproses data..."):
                # media_type: 1=Photo, 2=Video, 8=Carousel
                m_type = "Image"
                if media.media_type == 2:
                    if media.product_type == "clips":
                        m_type = "Reels"
                    else:
                        m_type = "Video"
                elif media.media_type == 8:
                    m_type = "Carousel"

                post_info = {
                    "id": media.pk,
                    "type": m_type,
                    "likes": media.like_count,
                    "comments": media.comment_count,
                    "taken_at": media.taken_at.isoformat(),
                    "day_of_week": media.taken_at.strftime("%A"),
                    "hour": media.taken_at.hour,
                    "caption": media.caption_text[:50] + "..." if media.caption_text else "No Caption",
                    "url": f"https://instagram.com/p/{media.code}/"
                }
                
                # Calculate ER for this post
                engagement = post_info["likes"] + post_info["comments"]
                post_info["engagement_rate"] = (engagement / self.followers_count) * 100 if self.followers_count > 0 else 0
                
                self.posts_data.append(post_info)
                
            # Save cache
            with open(DATA_FILE, 'w') as f:
                json.dump({"followers": self.followers_count, "posts": self.posts_data}, f)
                
            console.print("[green]Data berhasil diambil dan disimpan![/green]")
            return True
            
        except RateLimitError:
            console.print("[red]Terkena Rate Limit dari Instagram! Coba lagi nanti atau gunakan data cache.[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Error mengambil data: {e}[/red]")
            return False

    def load_cached_data(self):
        """Load data from local cache if exists."""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.followers_count = data.get("followers", 0)
                    self.posts_data = data.get("posts", [])
                console.print(f"[green]Berhasil memuat {len(self.posts_data)} data postingan dari cache lokal![/green]")
                return True
            except Exception as e:
                console.print(f"[red]Gagal memuat cache: {e}[/red]")
        return False

    def manual_data_input(self):
        """Allow user to input simple data manually if login fails/unwanted."""
        console.print("[cyan]--- Input Data Manual ---[/cyan]")
        self.followers_count = IntPrompt.ask("Berapa jumlah followers kakak?")
        num_posts = IntPrompt.ask("Berapa postingan yang mau diinput datanya?")
        
        self.posts_data = []
        for i in range(num_posts):
            console.print(f"\n[bold]Postingan #{i+1}[/bold]")
            p_type = Prompt.ask("Tipe konten", choices=["Reels", "Carousel", "Image"], default="Reels")
            likes = IntPrompt.ask("Jumlah Likes")
            comments = IntPrompt.ask("Jumlah Comments")
            day = Prompt.ask("Hari posting (bahasa Inggris, e.g., Monday, Tuesday)", default="Monday")
            hour = IntPrompt.ask("Jam posting (0-23)", default=17)
            
            engagement = likes + comments
            er = (engagement / self.followers_count) * 100 if self.followers_count > 0 else 0
            
            self.posts_data.append({
                "type": p_type,
                "likes": likes,
                "comments": comments,
                "day_of_week": day.capitalize(),
                "hour": hour,
                "engagement_rate": er,
                "caption": f"Manual Input #{i+1}"
            })
            
        console.print("[green]Data manual berhasil disimpan![/green]")
        return True

    def analyze_engagement(self):
        """Analyze the collected data."""
        if not self.posts_data:
            console.print("[red]Belum ada data! Silakan ambil data dulu.[/red]")
            return None

        df = pd.DataFrame(self.posts_data)
        
        # Overall metrics
        avg_er = df["engagement_rate"].mean()
        total_interactions = df["likes"].sum() + df["comments"].sum()
        
        # By Type
        type_er = df.groupby("type")["engagement_rate"].mean().to_dict()
        
        # By Day
        day_er = df.groupby("day_of_week")["engagement_rate"].mean().sort_values(ascending=False).to_dict()
        
        # By Hour
        hour_er = df.groupby("hour")["engagement_rate"].mean().sort_values(ascending=False).to_dict()
        
        # Top 3 Posts
        top_posts = df.nlargest(3, "engagement_rate").to_dict('records')

        return {
            "avg_er": avg_er,
            "type_er": type_er,
            "day_er": day_er,
            "hour_er": hour_er,
            "top_posts": top_posts,
            "df": df
        }

    def print_report(self, analysis):
        """Print analysis report to console."""
        if not analysis: return
        
        console.print("\n" + "="*50)
        console.print(Panel("[bold cyan]📊 HASIL ANALISIS ENGAGEMENT[/bold cyan]", expand=False))
        
        # Overall
        console.print(f"\n[bold]👥 Followers:[/bold] {self.followers_count:,}")
        
        er_color = "green" if analysis['avg_er'] > 3 else "yellow" if analysis['avg_er'] > 1 else "red"
        console.print(f"[bold]📈 Rata-rata Engagement Rate:[/bold] [{er_color}]{analysis['avg_er']:.2f}%[/{er_color}]")
        
        # By Type Table
        table = Table(title="Performa Berdasarkan Tipe Konten")
        table.add_column("Tipe", style="cyan")
        table.add_column("Avg Engagement Rate", style="magenta")
        for t, er in analysis['type_er'].items():
            table.add_row(t, f"{er:.2f}%")
        console.print(table)
        
        # Best Time
        best_day = list(analysis['day_er'].keys())[0] if analysis['day_er'] else "-"
        best_hour = list(analysis['hour_er'].keys())[0] if analysis['hour_er'] else "-"
        console.print(f"\n[bold]🕐 Waktu Posting Terbaik (Historis):[/bold] {best_day} jam {best_hour}:00")
        
        # Top Posts
        console.print("\n[bold]🏆 Top 3 Postingan Kakak:[/bold]")
        for i, p in enumerate(analysis['top_posts']):
            console.print(f"{i+1}. [{p['type']}] ER: {p['engagement_rate']:.2f}% | Likes: {p['likes']} | Caption: {p['caption']}")

    def generate_recommendations(self, analysis, niche="General"):
        """Generate content strategy recommendations."""
        if not analysis: return
        
        console.print("\n" + "="*50)
        console.print(Panel("[bold magenta]🎯 REKOMENDASI STRATEGI KONTEN (SIMPLE & HIGH ENGAGEMENT)[/bold magenta]", expand=False))
        
        # Determine best format
        best_format = max(analysis['type_er'], key=analysis['type_er'].get) if analysis['type_er'] else "Reels"
        
        console.print("\n[bold yellow]💡 Strategi Format:[/bold yellow]")
        if best_format == "Reels":
            console.print("- Data nunjukin **Reels** kakak paling rame! Fokus bikin video pendek 15-30 detik.")
            console.print("- Ga perlu ngedit ribet. Cukup rekam proses, B-roll estetik, atau ngomong depan kamera + text/caption menarik di layar.")
            console.print("- Pakai trending audio yang lagi naik daun.")
        elif best_format == "Carousel":
            console.print("- Data nunjukin **Carousel** (slide foto) kakak yang paling juara!")
            console.print("- Orang suka save konten kakak. Bikin konten edukasi, tips, atau cerita step-by-step dalam 5-7 slide.")
            console.print("- Slide 1: Hook/Judul clickbait jujur. Slide terakhir: Ajak mereka Save/Share/Komen.")
        else:
            console.print("- Konten Image (foto tunggal) kakak lumayan. Tapi di 2026, coba pelan-pelan transisi ke Reels atau Carousel biar jangkauannya lebih luas.")
            
        # Niche specific ideas
        console.print(f"\n[bold green]💡 Ide Konten Simple ({niche}):[/bold green]")
        if niche.lower() in ["kuliner", "food"]:
            console.print("1. [Reels] 'POV: Nemu cafe hidden gem' -> Rekam suasana 5 detik, rekam makanan 5 detik, kasih teks.")
            console.print("2. [Carousel] '3 Rekomendasi Menu Wajib Pesan di X' -> Simple foto + review jujur di tiap slide.")
        elif niche.lower() in ["edukasi", "tech", "coding"]:
            console.print("1. [Carousel] 'Cheat Sheet: 5 Fitur Python yang Jarang Diketahui' -> Tiap slide 1 tips singkat + kode simpel.")
            console.print("2. [Reels] Screen record ngerjain error, kasih teks 'Ketika nemu bug 3 jam ternyata typo' -> Relatable banget buat programmer.")
        elif niche.lower() in ["lifestyle", "daily"]:
            console.print("1. [Reels] 'A Day in My Life (Mini Vlog)' -> Kumpulin video 2 detik dari pagi-malam, gabungin pakai audio chill.")
            console.print("2. [Image/Carousel] OOTD/Setup Meja Kerja dengan rincian harga di caption -> Orang suka nanya beli dimana.")
        else:
            console.print(f"1. [Reels] Mitos vs Fakta seputar {niche}. (Video geleng kepala vs ngangguk + teks).")
            console.print(f"2. [Carousel] 'Kesalahan pemula saat main {niche} & cara atasinya'.")

        console.print("\n[bold cyan]📌 Tips Penting 2026:[/bold cyan]")
        console.print("- Engagement terbaik sekarang dinilai dari **Saves** & **Shares (DM)**. Bikin konten yang bikin orang mau nyimpen atau ngirim ke temennya.")
        console.print(f"- Coba jadwalkan posting di jam emas kakak: **{list(analysis['day_er'].keys())[0] if analysis['day_er'] else 'Rabu'} jam {list(analysis['hour_er'].keys())[0] if analysis['hour_er'] else '18'}:00**.")

    def visualize_data(self, analysis):
        """Create charts and save to file."""
        if not analysis: return
        df = analysis['df']
        
        plt.style.use('ggplot')
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Chart 1: ER by Type
        type_data = analysis['type_er']
        ax1.bar(type_data.keys(), type_data.values(), color=['#E1306C', '#F77737', '#405DE6'][:len(type_data)])
        ax1.set_title('Avg Engagement Rate by Content Type')
        ax1.set_ylabel('Engagement Rate (%)')
        
        # Chart 2: ER over time (last N posts)
        df_sorted = df.sort_index(ascending=False).reset_index() # Revert to chronological
        ax2.plot(df_sorted.index, df_sorted['engagement_rate'], marker='o', linestyle='-', color='#C13584')
        ax2.set_title('Engagement Trend (Last Posts)')
        ax2.set_xlabel('Recent Posts (Oldest to Newest)')
        ax2.set_ylabel('Engagement Rate (%)')
        
        plt.tight_layout()
        filename = "engagement_charts.png"
        plt.savefig(filename)
        console.print(f"\n[green]📈 Grafik divisualisasikan dan disimpan sebagai '{filename}'[/green]")

    def export_csv(self):
        if not self.posts_data:
            console.print("[red]Tidak ada data untuk di-export![/red]")
            return
        df = pd.DataFrame(self.posts_data)
        filename = "ig_data_export.csv"
        df.to_csv(filename, index=False)
        console.print(f"[green]💾 Data berhasil di-export ke '{filename}'[/green]")

def main_menu():
    analyzer = InstagramAnalyzer()
    
    # Try load cache first
    analyzer.load_cached_data()
    
    while True:
        console.print("\n" + "="*50)
        console.print("[bold magenta]📱 INSTAGRAM ENGAGEMENT ANALYZER & STRATEGY[/bold magenta]")
        console.print("="*50)
        console.print("1. 🔐 Ambil Data (Login Auto via instagrapi)")
        console.print("2. 📝 Input Data Manual (Aman, no login)")
        console.print("3. 📈 Analisis & Lihat Report")
        console.print("4. 🎯 Generate Rekomendasi Konten")
        console.print("5. 📊 Buat Visualisasi Grafik (PNG)")
        console.print("6. 💾 Export Data (CSV)")
        console.print("0. ❌ Keluar")
        
        choice = Prompt.ask("Pilih menu", choices=["0", "1", "2", "3", "4", "5", "6"])
        
        if choice == "1":
            console.print("\n[yellow]PERHATIAN: Menggunakan API tidak resmi bisa menyebabkan temporary block. Disarankan pakai akun tumbal/second.[/yellow]")
            username = Prompt.ask("Instagram Username")
            password = Prompt.ask("Instagram Password", password=True)
            if analyzer.login(username, password):
                limit = IntPrompt.ask("Berapa postingan terakhir yang mau dianalisis?", default=30)
                analyzer.fetch_data(limit=limit)
        
        elif choice == "2":
            analyzer.manual_data_input()
            
        elif choice == "3":
            analysis = analyzer.analyze_engagement()
            analyzer.print_report(analysis)
            
        elif choice == "4":
            analysis = analyzer.analyze_engagement()
            if analysis:
                niche = Prompt.ask("Apa topik/niche akun kakak? (misal: Kuliner, Edukasi, Lifestyle)", default="General")
                analyzer.generate_recommendations(analysis, niche)
                
        elif choice == "5":
            analysis = analyzer.analyze_engagement()
            analyzer.visualize_data(analysis)
            
        elif choice == "6":
            analyzer.export_csv()
            
        elif choice == "0":
            console.print("[cyan]Terima kasih telah menggunakan tools ini! Bye! 👋[/cyan]")
            break

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n[cyan]Program dihentikan oleh pengguna.[/cyan]")
        sys.exit(0)
