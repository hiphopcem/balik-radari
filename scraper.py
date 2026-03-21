#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import os
import re
import time
import hashlib
from datetime import datetime, timezone
from urllib.parse import urljoin, quote_plus

OUTPUT_FILE = "data/reports.json"
MAX_REPORTS = 200
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

FISH_KEYWORDS = [
    "sazan","levrek","çipura","lüfer","palamut","hamsi","istavrit","kalkan",
    "barbun","kefal","alabalık","yayın","sudak","turna","karagöz","sargoz",
    "kolyoz","uskumru","orkinos","mercan","isparoz","kızılkanat"
]

LOCATION_COORDS = {
    "büyükçekmece":(41.15,28.80),"küçükçekmece":(41.01,28.77),
    "bostancı":(40.96,29.09),"beykoz":(41.12,29.10),
    "kumkapı":(41.00,28.96),"boğaz":(41.08,29.05),
    "istanbul":(41.01,28.96),"şile":(41.18,29.61),
    "sapanca":(40.65,30.40),"izmit":(40.76,29.92),
    "bursa":(40.18,29.06),"çanakkale":(40.15,26.40),
    "tekirdağ":(40.97,27.51),"edirne":(41.68,26.56),
    "izmir":(38.42,27.14),"urla":(38.32,26.76),
    "çeşme":(38.32,26.30),"kuşadası":(37.86,27.26),
    "bodrum":(37.03,27.43),"marmaris":(36.85,28.27),
    "fethiye":(36.65,29.12),"ayvalık":(39.32,26.70),
    "antalya":(36.89,30.70),"alanya":(36.54,32.00),
    "mersin":(36.80,34.64),"adana":(37.00,35.32),
    "trabzon":(41.00,39.73),"samsun":(41.28,36.34),
    "rize":(41.02,40.52),"sinop":(42.02,35.15),
    "ordu":(40.98,37.88),"giresun":(40.91,38.39),
    "mogan":(39.79,32.76),"eymir":(39.93,32.85),
    "atatürk barajı":(37.48,38.30),"keban":(38.70,39.50),
    "abant":(40.60,31.27),"tortum":(40.30,41.55),
    "ergene":(41.62,26.72),"seyhan":(37.20,35.45),
    "beyşehir":(37.68,31.73),"eğirdir":(37.87,30.85),
    "van":(38.65,42.87),
}

def safe_get(url, timeout=15):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        return r
    except Exception as e:
        print(f"  Hata ({url[:60]}): {e}")
        return None

def extract_fish(text):
    text_lower = text.lower()
    found = []
    for fish in FISH_KEYWORDS:
        if fish in text_lower and fish not in found:
            found.append(fish.title())
    return found if found else ["Belirtilmemiş"]

def find_location_coords(text):
    text_lower = text.lower()
    best_loc = None
    best_coords = None
    for loc_name, coords in LOCATION_COORDS.items():
        if loc_name in text_lower:
            if best_loc is None or len(loc_name) > len(best_loc):
                best_loc = loc_name
                best_coords = coords
    return best_loc, best_coords

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:12]

def time_ago(dt_str):
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = int((now - dt).total_seconds())
        if diff < 60: return "Az önce"
        if diff < 3600: return f"{diff//60}dk önce"
        if diff < 86400: return f"{diff//3600}s önce"
        return f"{diff//86400}g önce"
    except:
        return "Bilinmiyor"

def classify_type(text, loc):
    t = (text + " " + (loc or "")).lower()
    if any(w in t for w in ["baraj","nehir","irmak","dere"]): return "nehir"
    if any(w in t for w in ["göl"]): return "göl"
    return "deniz"

def scrape_google_news():
    print("Google News taranıyor...")
    reports = []
    queries = [
        "balık tutma raporu Türkiye",
        "balıkçılık haberleri bugün",
        "lüfer palamut hamsi sezonu",
        "sazan yayın alabalık tutuldu",
    ]
    for query in queries:
        url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=tr&gl=TR&ceid=TR:tr"
        r = safe_get(url)
        if not r:
            continue
        soup = BeautifulSoup(r.content, "xml")
        for item in soup.find_all("item")[:5]:
            title = item.find("title")
            desc = item.find("description")
            if not title: continue
            text = title.get_text() + " " + (desc.get_text() if desc else "")
            fish = extract_fish(text)
            if fish == ["Belirtilmemiş"]: continue
            loc_name, coords = find_location_coords(text)
            if not coords: continue
            now = datetime.now(timezone.utc).isoformat()
            reports.append({
                "id": make_id(title.get_text()),
                "lat": coords[0], "lng": coords[1],
                "loc": loc_name.title(),
                "fish": fish[:3],
                "note": title.get_text()[:120],
                "heat": min(5, len(fish) + 2),
                "type": classify_type(text, loc_name),
                "time": time_ago(now),
                "timestamp": now,
                "source": "Google Haberler",
                "url": "",
                "hot": len(fish) >= 2,
            })
        time.sleep(1)
    print(f"  {len(reports)} haber bulundu")
    return reports

def scrape_rss_feeds():
    print("RSS feedleri taranıyor...")
    reports = []
    feeds = [
        ("https://www.hurriyet.com.tr/rss/gundem", "Hürriyet"),
        ("https://www.sabah.com.tr/rss/yasam.xml", "Sabah"),
        ("https://www.ntv.com.tr/feeds/rss/son-dakika", "NTV"),
    ]
    for feed_url, source_name in feeds:
        r = safe_get(feed_url)
        if not r: continue
        soup = BeautifulSoup(r.content, "xml")
        for item in soup.find_all("item")[:20]:
            title = item.find("title")
            desc = item.find("description")
            if not title: continue
            text = title.get_text() + " " + (desc.get_text() if desc else "")
            if not any(w in text.lower() for w in ["balık","balıkçı","olta"]): continue
            fish = extract_fish(text)
            loc_name, coords = find_location_coords(text)
            if not coords: continue
            now = datetime.now(timezone.utc).isoformat()
            reports.append({
                "id": make_id(title.get_text()),
                "lat": coords[0], "lng": coords[1],
                "loc": loc_name.title(),
                "fish": fish[:3],
                "note": title.get_text()[:120],
                "heat": 3,
                "type": classify_type(text, loc_name),
                "time": time_ago(now),
                "timestamp": now,
                "source": source_name,
                "url": "", "hot": False,
            })
        time.sleep(0.5)
    print(f"  {len(reports)} haber bulundu")
    return reports

FALLBACK_DATA = [
    {"id":"fb01","lat":41.15,"lng":28.80,"loc":"Büyükçekmece Gölü","fish":["Sazan","Turna"],"note":"Sabah erken saatlerde harika. Sazan bolluk.","heat":5,"type":"göl","hot":True,"source":"Demo"},
    {"id":"fb02","lat":40.98,"lng":29.14,"loc":"Bostancı Sahili","fish":["Lüfer","İstavrit"],"note":"Lüfer girişi başladı, akşam üstü aktif.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"fb03","lat":40.65,"lng":30.40,"loc":"Sapanca Gölü","fish":["Alabalık","Sazan"],"note":"Sabah 6-9 arası alabalık aktif.","heat":5,"type":"göl","hot":True,"source":"Demo"},
    {"id":"fb04","lat":38.40,"lng":27.10,"loc":"İzmir Körfezi","fish":["Çipura","Levrek"],"note":"Sabah çipura iyi tuttu.","heat":5,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"fb05","lat":37.78,"lng":38.28,"loc":"Atatürk Barajı","fish":["Yayın","Sazan","Sudak"],"note":"Dev yayın sezonu açık.","heat":5,"type":"nehir","hot":True,"source":"Demo"},
    {"id":"fb06","lat":41.00,"lng":39.72,"loc":"Trabzon Sahili","fish":["Hamsi","Istavrit"],"note":"Hamsi sürüsü geldi!","heat":5,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"fb07","lat":40.20,"lng":26.40,"loc":"Çanakkale Boğazı","fish":["Palamut","Lüfer"],"note":"Palamut akını var.","heat":5,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"fb08","lat":39.80,"lng":32.70,"loc":"Mogan Gölü","fish":["Sazan","Sudak"],"note":"Sudak aktif.","heat":4,"type":"göl","hot":False,"source":"Demo"},
    {"id":"fb09","lat":38.70,"lng":39.50,"loc":"Keban Barajı","fish":["Yayın","Sudak"],"note":"Dip olta iyi.","heat":4,"type":"nehir","hot":False,"source":"Demo"},
    {"id":"fb10","lat":36.88,"lng":30.70,"loc":"Antalya Körfezi","fish":["Levrek","Kefal"],"note":"Akşam levrek aktif.","heat":4,"type":"deniz","hot":False,"source":"Demo"},
]

def main():
    print(f"Balık Radarı Scraper - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    existing = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f).get("reports", [])
            print(f"Mevcut {len(existing)} rapor yüklendi")
        except Exception as e:
            print(f"Mevcut veri okunamadı: {e}")

    new_reports = []
    new_reports += scrape_google_news()
    new_reports += scrape_rss_feeds()
    print(f"Toplam yeni: {len(new_reports)} rapor")

    now_iso = datetime.now(timezone.utc).isoformat()
    for r in new_reports:
        if "timestamp" not in r:
            r["timestamp"] = now_iso
        r["time"] = time_ago(r["timestamp"])

    if len(new_reports) < 3:
        print("Yeterli veri yok, demo veri ekleniyor...")
        for r in FALLBACK_DATA:
            r["timestamp"] = now_iso
            r["time"] = "Az önce"
        new_reports = FALLBACK_DATA + new_reports

    all_reports = {r["id"]: r for r in existing}
    for r in new_reports:
        all_reports[r["id"]] = r

    sorted_reports = sorted(
        all_reports.values(),
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )[:MAX_REPORTS]

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "last_updated": now_iso,
            "total": len(sorted_reports),
            "reports": sorted_reports,
        }, f, ensure_ascii=False, indent=2)

    print(f"Tamamlandı! {len(sorted_reports)} rapor kaydedildi.")

if __name__ == "__main__":
    main()
