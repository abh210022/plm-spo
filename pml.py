import json
import time
import random
import os
from datetime import datetime, timedelta
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# =========================
# CONFIGURATION
# =========================
OUTPUT_FILE = "premierleague.w3u"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

LEAGUE_LOGOS = {
    "Premier League": "https://images.dookeela4.live/1ea51f4905fd47abb43f7ba22c817198:dkl-images-storage/leagues/39.png",
    "Bundesliga": "https://images.dookeela4.live/1ea51f4905fd47abb43f7ba22c817198:dkl-images-storage/leagues/78.png",
    "Bundesliga 2": "https://upload.wikimedia.org/wikipedia/en/thumb/7/7b/2._Bundesliga_logo.svg/150px-2._Bundesliga_logo.svg.png",
    "La Liga": "https://images.dookeela4.live/1ea51f4905fd47abb43f7ba22c817198:dkl-images-storage/leagues/140.png",
    "Segunda Division": "https://www.gamesatlas.com/images/football/leagues/la-liga-2.png",
    "Serie A": "https://images.dookeela4.live/1ea51f4905fd47abb43f7ba22c817198:dkl-images-storage/leagues/135.png",
    "Ligue 1": "https://images.dookeela4.live/1ea51f4905fd47abb43f7ba22c817198:dkl-images-storage/leagues/61.png",
    "UEFA Champions League": "https://images.dookeela4.live/1ea51f4905fd47abb43f7ba22c817198:dkl-images-storage/leagues/2.png",
    "UEFA Europa League": "https://images.dookeela4.live/1ea51f4905fd47abb43f7ba22c817198:dkl-images-storage/leagues/3.png",
    "Default": "https://img2.pic.in.th/live-tvc2a1249d4f879b85.png"
}

SPECIAL_FLAGS = {
    "england": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "wales": "🏴󠁧󠁢󠁷󠁬สูตร",
    "eu": "🇪🇺", "uefa": "🇪🇺", "europe": "🇪🇺", "international": "🌍", "spain": "🇪🇸"
}

THAI_MONTHS = {
    "January": "ม.ค", "February": "ก.พ", "March": "มี.ค", "April": "เม.ย",
    "May": "พ.ค", "June": "มิ.ย", "July": "ก.ค", "August": "ส.ค",
    "September": "ก.ย", "October": "ต.ค", "November": "พ.ย", "December": "ธ.ค"
}

CHANNELS = [
    {"name": "Sky Sport Premier League (Germany)", "url": "https://www.livesoccertv.com/channels/sky-sport-premier-league-de/", "logo": "https://img2.pic.in.th/skp-de.png", "stream_url": "http://fomo.re/live/t3n1BFmZ1X5d3rLH/uUB0xtNxNYFzMpyo/90840.ts"},
    {"name": "Sky Sport Premier League (UK)", "url": "https://www.livesoccertv.com/channels/sky-sports-premier-league/", "logo": "https://img5.pic.in.th/file/secure-sv1/skp-gb.png", "stream_url": "https://github.com/cattviptv2605/sportworld/raw/refs/heads/main/skysportspremierleague.m3u8"},
    {"name": "Hub Premier 1 (Singapore)", "url": "https://www.livesoccertv.com/channels/221-hub-premier-1/", "logo": "https://api.letitgooooo.org/images/png/sg-hubpremier01.png", "stream_url": "https://github.com/cattviptv2605/sportworld/raw/refs/heads/main/hubpremier1.m3u8"},
    {"name": "beIN Sports 1 (Thailand)", "url": "https://www.livesoccertv.com/channels/bein-sports-1-hd-thailand/", "logo": "https://ball67.com/assets/channels-logo/bein1.png", "stream_url": "https://raw.githubusercontent.com/Asawin65/ASawin/refs/heads/main/m3u8/sport/bein1.m3u8"},
    {"name": "beIN Sports 2 (Thailand)", "url": "https://www.livesoccertv.com/channels/bein-sports-2-thailand/", "logo": "https://ball67.com/assets/channels-logo/bein2.png", "stream_url": "https://raw.githubusercontent.com/Asawin65/ASawin/refs/heads/main/m3u8/sport/bein2.m3u8"},
    {"name": "Now Premier League 1 (Hong Kong )", "url": "https://www.livesoccertv.com/channels/now-621-hong-kong/", "logo": "https://images.now-tv.com/shares/channelPreview/img/en_hk/color/ch620_425_305", "stream_url": "https://raw.githubusercontent.com/udzaa2238/now-sport/refs/heads/main/fastopen_live-now_premier-1.m3u8"},
    {"name": "V Sport Premier League (Norway )", "url": "https://www.livesoccertv.com/channels/v-sport-premier-league/", "logo": "https://static.wikia.nocookie.net/logopedia/images/d/db/V_Sport_Premier_League.svg/revision/latest/scale-to-width-down/300?cb=20220701201704", "stream_url": "http://fomo.re/live/t3n1BFmZ1X5d3rLH/uUB0xtNxNYFzMpyo/113250.ts"}
]

# =========================
# HELPER FUNCTIONS
# =========================

def get_league_logo(league_name):
    for key, url in LEAGUE_LOGOS.items():
        if key.lower() in league_name.lower():
            return url
    return LEAGUE_LOGOS["Default"]

def convert_date_to_thai(dt_obj):
    month_en = dt_obj.strftime("%B")
    month_th = THAI_MONTHS.get(month_en, month_en)
    return f"{dt_obj.day} {month_th} {dt_obj.year + 543}"

def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={USER_AGENT}")
    driver = webdriver.Chrome(options=options)
    return driver

def scrape_channel(ch):
    max_retries = 2
    now = datetime.now()
    date_limit = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=3)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    for attempt in range(max_retries):
        local_matches = []
        driver = None
        try:
            driver = create_driver()
            driver.get(ch["url"])
            wait = WebDriverWait(driver, 30)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.schedules")))
            
            soup = BeautifulSoup(driver.page_source, "html.parser")
            table = soup.find("table", class_="schedules")
            
            if table:
                rows = table.find_all("tr")
                current_dt = None
                year = now.year

                for row in rows:
                    if "drow" in row.get("class", []):
                        date_str = row.get_text(strip=True)
                        try:
                            parts = date_str.replace(",", "").split()
                            m_en = next((p for p in parts if p in THAI_MONTHS), None)
                            d_num = next((p for p in parts if p.isdigit()), None)
                            if m_en and d_num:
                                current_dt = datetime.strptime(f"{m_en} {d_num} {year}", "%B %d %Y")
                        except: current_dt = None
                        continue

                    if "matchrow" in row.get("class", []) and current_dt:
                        if not (today_start <= current_dt <= date_limit): continue

                        time_tag = row.select_one(".timecell span")
                        match_link = row.select_one("td#match a")
                        league_tag = row.select_one(".compcell_right a") or row.select_one(".compcell_right")
                        
                        if time_tag and match_link:
                            time_str = time_tag.get_text(strip=True)
                            try:
                                h, m = map(int, time_str.split(':'))
                                match_full_dt = current_dt.replace(hour=h, minute=m)
                                if match_full_dt < now: continue 
                            except: pass

                            l_name = league_tag.get_text(strip=True) if league_tag else "League"
                            local_matches.append({
                                "dt_obj": current_dt,
                                "time_str": time_str,
                                "match_name": match_link.get_text(strip=True),
                                "league_full": l_name,
                                "channel_name": ch["name"],
                                "channel_logo": ch["logo"],
                                "stream_url": ch["stream_url"]
                            })
                print(f"✅ {ch['name']} Success")
                return local_matches
        except Exception:
            if attempt < max_retries - 1: time.sleep(5)
        finally:
            if driver: driver.quit()
    return []

if __name__ == "__main__":
    today_thai = convert_date_to_thai(datetime.now())
    all_raw_data = []

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(scrape_channel, CHANNELS))

    for res in results: all_raw_data.extend(res)

    if all_raw_data:
        grouped = defaultdict(lambda: defaultdict(list))
        for m in all_raw_data:
            dt_key = m["dt_obj"]
            time_str = m["time_str"]
            h, mm = map(int, time_str.split(':'))
            time_mins = h * 60 + mm

            display_name = f"{time_str} | {m['match_name']}"
            unique_key = f"{display_name} | {m['league_full']}"
            
            grouped[dt_key][(time_mins, unique_key)].append({
                "name": display_name,
                "image": m["channel_logo"],
                "url": m["stream_url"],
                "userAgent": USER_AGENT,
                "info": m["league_full"]
            })

        final_output = {
            "name": f"Premier League @{today_thai}",
            "author": f"Update@{today_thai}",
            "image": "https://img2.pic.in.th/live-tvc2a1249d4f879b85.png",
            "groups": []
        }

        for dt in sorted(grouped.keys()):
            match_list = []
            for _, u_key in sorted(grouped[dt].keys()):
                stations_list = grouped[dt][(_, u_key)]
                league_logo = get_league_logo(stations_list[0]["info"])
                clean_name = u_key.split(" | ")[0] + " | " + u_key.split(" | ")[1]

                match_list.append({
                    "name": clean_name,
                    "image": league_logo,
                    "stations": stations_list
                })
            
            final_output["groups"].append({
                "name": f"วันที่ {convert_date_to_thai(dt)}",
                "image": "https://img2.pic.in.th/live-tvc2a1249d4f879b85.png",
                "groups": match_list
            })

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(final_output, f, ensure_ascii=False, indent=2)
        print(f"Done: {OUTPUT_FILE}")
