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
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# =========================
# CONFIGURATION
# =========================
SAVE_DIR = "output"
OUTPUT_FILE = os.path.join(SAVE_DIR, "pml.txt")
USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko)"

# ตารางแปลงชื่อคลาสเป็น Emoji พิเศษ (คงเดิม 100%)
SPECIAL_FLAGS = {
    "england": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    "eu": "🇪🇺", "uefa": "🇪🇺", "europe": "🇪🇺",
    "international": "🌍", "world": "🌎"
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
    {"name": "Hub Premier 2 (Singapore)", "url": "https://www.livesoccertv.com/channels/222-hub-premier-2/", "logo": "https://api.letitgooooo.org/images/png/sg-hubpremier02.png", "stream_url": "https://github.com/cattviptv2605/sportworld/raw/refs/heads/main/hubpremier2.m3u8"},
    {"name": "Hub Premier 3 (Singapore)", "url": "https://www.livesoccertv.com/channels/223-hub-premier-3/", "logo": "https://api.letitgooooo.org/images/png/sg-hubpremier03.png", "stream_url": "https://github.com/cattviptv2605/sportworld/raw/refs/heads/main/hubpremier2.m3u8"},
    {"name": "Hub Premier 4 (Singapore)", "url": "https://www.livesoccertv.com/channels/224-hub-premier-4/", "logo": "https://api.letitgooooo.org/images/png/sg-hubpremier04.png", "stream_url": "https://github.com/cattviptv2605/sportworld/raw/refs/heads/main/hubpremier4.m3u8"},
    {"name": "Sky Sport 1 (NZ)", "url": "https://www.livesoccertv.com/channels/sky-sport-1-new-zealand/", "logo": "https://api.bigwifegang.org/images/png/nz-skysport1.png", "stream_url": "https://github.com/cattviptv2605/sportworld/raw/refs/heads/main/skysport1_nz.m3u8"},
    {"name": "Sky Sport 2 (NZ)", "url": "https://www.livesoccertv.com/channels/sky-sport-2-new-zealand/", "logo": "https://api.bigwifegang.org/images/png/nz-skysport2.png", "stream_url": "https://github.com/cattviptv2605/sportworld/raw/refs/heads/main/skysport2_nz.m3u8"},
    {"name": "Sky Sport 3 (NZ)", "url": "https://www.livesoccertv.com/channels/sky-sport-3-new-zealand/", "logo": "https://api.bigwifegang.org/images/png/nz-skysport3.png", "stream_url": "https://github.com/cattviptv2605/sportworld/raw/refs/heads/main/skysport3_nz.m3u8"},
    {"name": "Sky Sport 4 (NZ)", "url": "https://www.livesoccertv.com/channels/sky-sport-4-nz/", "logo": "https://api.bigwifegang.org/images/png/nz-skysport4.png", "stream_url": "https://github.com/cattviptv2605/sportworld/raw/refs/heads/main/skysport4_nz.m3u8"},
    {"name": "Sky Sport 5 (NZ)", "url": "https://www.livesoccertv.com/channels/sky-sport-5-new-zealand/", "logo": "https://api.bigwifegang.org/images/png/nz-skysport5.png", "stream_url": "https://github.com/cattviptv2605/sportworld/raw/refs/heads/main/skysport5_nz.m3u8"},
    {"name": "Sky Sport 6 (NZ)", "url": "https://www.livesoccertv.com/channels/sky-sport-6-nz/", "logo": "https://api.bigwifegang.org/images/png/nz-skysport6.png", "stream_url": "https://github.com/cattviptv2605/sportworld/raw/refs/heads/main/skysport6_nz.m3u8"},
    {"name": "Sky Sport 7 (NZ)", "url": "https://www.livesoccertv.com/channels/sky-sport-7-nz/", "logo": "https://api.bigwifegang.org/images/png/nz-skysport7.png", "stream_url": "https://github.com/cattviptv2605/sportworld/raw/refs/heads/main/skysport7_nz.m3u8"},
    {"name": "TNT Sports 1 (UK)", "url": "https://www.livesoccertv.com/channels/bt-sport-1-uk/", "logo": "https://rentapi.blackboxsys.net/images/png/uk-btsport1hd.png", "stream_url": "https://github.com/cattviptv2605/sportworld/raw/refs/heads/main/tntsport1.m3u8"},
    {"name": "TNT Sports 2 (UK)", "url": "https://www.livesoccertv.com/channels/bt-sport-2-uk/", "logo": "https://rentapi.blackboxsys.net/images/png/uk-btsport2hd.png", "stream_url": "https://github.com/cattviptv2605/sportworld/raw/refs/heads/main/tntsport2.m3u8"},
    {"name": "TNT Sports 3 (UK)", "url": "https://www.livesoccertv.com/channels/bt-sport-europe/", "logo": "https://rentapi.blackboxsys.net/images/png/uk-btsport3hd.png", "stream_url": "https://github.com/cattviptv2605/sportworld/raw/refs/heads/main/tntsport3.m3u8"},
    {"name": "TNT Sports 4 (UK)", "url": "https://www.livesoccertv.com/channels/espn-uk/", "logo": "https://api.rentm3u8.com/images/png/uk-espn.png", "stream_url": "https://github.com/cattviptv2605/sportworld/raw/refs/heads/main/tntsport4.m3u8"},
    {"name": "Ziggo Sport 1 (Netherlands)", "url": "https://www.livesoccertv.com/channels/ziggo-sport-select-netherlands/", "logo": "https://api.bigwifegang.org/images/png/nl-ziggosport1.png", "stream_url": "https://github.com/cattviptv2605/sportworld/raw/refs/heads/main/ziggosport1.m3u8"},
    {"name": "Ziggo Sport 2 (Netherlands)", "url": "https://www.livesoccertv.com/channels/ziggo-sport-voetbal/", "logo": "https://api.bigwifegang.org/images/png/nl-ziggosport2.png", "stream_url": "https://github.com/cattviptv2605/sportworld/raw/refs/heads/main/ziggosport2.m3u8"},
    {"name": "V Sport Premier League (Norway )", "url": "https://www.livesoccertv.com/channels/v-sport-premier-league/", "logo": "https://static.wikia.nocookie.net/logopedia/images/d/db/V_Sport_Premier_League.svg/revision/latest/scale-to-width-down/300?cb=20220701201704", "stream_url": "http://fomo.re/live/t3n1BFmZ1X5d3rLH/uUB0xtNxNYFzMpyo/113250.ts"}
]

# =========================
# HELPER FUNCTIONS (คงเดิม 100%)
# =========================

def get_flag_emoji_from_class(tag):
    if not tag: return "🏆"
    classes = tag.get("class", [])
    country_name = next((c for c in classes if c != "flag"), "").lower()
    if country_name in SPECIAL_FLAGS: return SPECIAL_FLAGS[country_name]
    if len(country_name) >= 2:
        try:
            iso_code = country_name[:2]
            return "".join(chr(127397 + ord(c.upper())) for c in iso_code)
        except: return "🏆"
    return "🏆"

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
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def scrape_channel(ch):
    local_matches = []
    driver = None
    try:
        driver = create_driver()
        driver.get(ch["url"])
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.schedules")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        table = soup.find("table", class_="schedules")
        
        if table:
            rows = table.find_all("tr")
            now_th = datetime.utcnow() + timedelta(hours=7)
            year = now_th.year
            current_dt = None

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
                    time_tag = row.select_one(".timecell span")
                    match_link = row.select_one("td#match a")
                    league_tag = row.select_one(".compcell_right a") or row.select_one(".compcell_right")
                    
                    if time_tag and match_link:
                        flag = get_flag_emoji_from_class(league_tag)
                        l_name = league_tag.get_text(strip=True) if league_tag else ""
                        
                        # ✅ แก้ไข Logic เวลา: ตัด am/pm ออก และใช้รูปแบบ 24 ชม. เท่านั้น
                        raw_time_str = time_tag.get_text(strip=True).lower()
                        try:
                            # 1. จัดการข้อความเวลาให้เป็นก้อนเดียว
                            clean_time = raw_time_str.replace("am", "").replace("pm", "").strip()
                            # 2. รวมวันที่ของหัวข้อกับเวลาที่ดึงมา (มองเป็น UTC)
                            match_dt_utc = datetime.combine(current_dt.date(), datetime.strptime(clean_time, "%H:%M").time())
                            # 3. บวก 7 ชั่วโมง และบังคับแสดงผล %H:%M (24 ชั่วโมง)
                            match_dt_thai = match_dt_utc + timedelta(hours=7)
                            final_time = match_dt_thai.strftime("%H:%M")
                            final_date_obj = match_dt_thai # ใช้อันนี้จัดกลุ่มเพื่อให้วันที่เปลี่ยนตามเวลาที่บวก
                        except:
                            final_time = raw_time_str
                            final_date_obj = current_dt

                        local_matches.append({
                            "dt_obj": final_date_obj,
                            "time_str": final_time, 
                            "match_name": match_link.get_text(strip=True),
                            "league_full": f"{flag}{l_name}",
                            "channel_name": ch["name"],
                            "channel_logo": ch["logo"],
                            "stream_url": ch["stream_url"]
                        })
            print(f"✅ {ch['name']} Success")
    except Exception as e:
        print(f"❌ {ch['name']} Skip: {str(e)}")
    finally:
        if driver: driver.quit()
    return local_matches

# =========================
# MAIN EXECUTION
# =========================
if __name__ == "__main__":
    now_th = datetime.utcnow() + timedelta(hours=7)
    today_thai = convert_date_to_thai(now_th)
    
    all_raw_data = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(scrape_channel, CHANNELS))

    for res in results:
        all_raw_data.extend(res)

    if all_raw_data:
        # จัดกลุ่มโดยใช้ความแม่นยำของวันที่ไทย (หลังจากบวก 7 ชม.)
        grouped = defaultdict(lambda: defaultdict(list))
        for m in all_raw_data:
            dt_key = m["dt_obj"].date()
            time_str = m["time_str"]
            m_key = f"{time_str} | {m['match_name']} | {m['league_full']}"
            
            grouped[dt_key][m_key].append({
                "name": m_key,
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

        # เรียงลำดับวันที่ให้ถูกต้อง
        for dt_date in sorted(grouped.keys()):
            match_list = []
            # เรียงลำดับชื่อคู่ (จะเรียงตามเวลา 24 ชม. โดยอัตโนมัติ)
            for m_key in sorted(grouped[dt_date].keys()):
                match_list.append({
                    "name": m_key,
                    "image": "https://img2.pic.in.th/live-tvc2a1249d4f879b85.png",
                    "stations": grouped[dt_date][m_key]
                })
            
            final_output["groups"].append({
                "name": f"วันที่ {convert_date_to_thai(datetime.combine(dt_date, datetime.min.time()))}",
                "image": "https://img2.pic.in.th/live-tvc2a1249d4f879b85.png",
                "groups": match_list
            })

        os.makedirs(SAVE_DIR, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(final_output, f, ensure_ascii=False, indent=2)