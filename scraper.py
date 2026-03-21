#!/usr/bin/env python3
"""
Türkiye Balık Radarı - Marmara Bölgesi Scraper
Öncelikli bölgeler: İstanbul, Tekirdağ, Edirne, Kocaeli, Yalova, Bursa, Balıkesir
Her 3 saatte bir GitHub Actions tarafından çalıştırılır.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
import hashlib
from datetime import datetime, timezone
from urllib.parse import quote_plus

OUTPUT_FILE = "data/reports.json"
MAX_REPORTS = 150

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}

# ── MARMARA BÖLGESİ KOORDİNATLARI ─────────────────────────────────────────
LOCATIONS = {
    # İSTANBUL - Avrupa Yakası
    "büyükçekmece":    (41.1500, 28.8000),
    "küçükçekmece":    (41.0100, 28.7700),
    "avcılar":         (40.9800, 28.7200),
    "bakırköy":        (40.9800, 28.8700),
    "yeşilköy":        (40.9700, 28.8200),
    "florya":          (40.9700, 28.8000),
    "kumkapı":         (41.0050, 28.9600),
    "yenikapı":        (41.0050, 28.9500),
    "sarayburnu":      (41.0130, 28.9800),
    "eminönü":         (41.0160, 28.9740),
    "galata":          (41.0230, 28.9740),
    "haliç":           (41.0300, 28.9400),
    "sarıyer":         (41.1670, 29.0500),
    "rumeli kavağı":   (41.2000, 29.0600),
    "anadolu kavağı":  (41.1900, 29.0800),
    "boğaziçi":        (41.0800, 29.0500),
    "boğaz":           (41.0800, 29.0500),
    "bebek":           (41.0780, 29.0440),
    "arnavutköy":      (41.0700, 29.0400),
    "ortaköy":         (41.0530, 29.0270),
    "beşiktaş":        (41.0430, 29.0070),
    "kabataş":         (41.0340, 29.0040),
    "şile":            (41.1800, 29.6100),
    "ağva":            (41.1000, 30.0000),
    "kilyos":          (41.2500, 29.0200),
    "karaburun":       (41.3500, 28.6900),
    # İSTANBUL - Anadolu Yakası
    "bostancı":        (40.9600, 29.0900),
    "kadıköy":         (40.9900, 29.0230),
    "üsküdar":         (41.0230, 29.0140),
    "beykoz":          (41.1200, 29.1000),
    "paşabahçe":       (41.1400, 29.0900),
    "çengelköy":       (41.0620, 29.0600),
    "anadolu hisarı":  (41.0830, 29.0730),
    "kanlıca":         (41.1000, 29.0800),
    "adalar":          (40.8700, 29.1100),
    "büyükada":        (40.8700, 29.1200),
    "heybeliada":      (40.8800, 29.0900),
    "tuzla":           (40.8200, 29.2900),
    "pendik":          (40.8700, 29.2300),
    "maltepe":         (40.9300, 29.1300),
    "kartal":          (40.9100, 29.1900),
    # KOCAELİ / İZMİT
    "izmit":           (40.7600, 29.9200),
    "kocaeli":         (40.7600, 29.9200),
    "gebze":           (40.8000, 29.4300),
    "körfez":          (40.7700, 29.7700),
    "karamürsel":      (40.6900, 29.6100),
    "gölcük":          (40.6500, 29.8300),
    "darıca":          (40.7700, 29.3700),
    "hereke":          (40.7900, 29.6200),
    # YALOVA
    "yalova":          (40.6500, 29.2700),
    "çınarcık":        (40.6400, 29.1200),
    "armutlu":         (40.5300, 28.8300),
    "termal":          (40.5900, 29.2000),
    # BURSA
    "bursa":           (40.1800, 29.0600),
    "mudanya":         (40.3800, 28.8800),
    "gemlik":          (40.4300, 29.1600),
    "orhangazi":       (40.4900, 29.3100),
    "İznik":           (40.4300, 29.7200),
    "iznik":           (40.4300, 29.7200),
    "iznik gölü":      (40.4000, 29.5500),
    "uluabat":         (40.1700, 28.6200),
    "uluabat gölü":    (40.1700, 28.6200),
    "apolyont":        (40.1700, 28.6200),
    # TEKİRDAĞ
    "tekirdağ":        (40.9700, 27.5100),
    "marmara ereğlisi":(40.9700, 27.9600),
    "şarköy":          (40.6100, 27.1100),
    "mürefte":         (40.6700, 27.2600),
    "barbaros":        (40.8200, 27.4500),
    "hayrabolu":       (41.2200, 27.1000),
    "çorlu":           (41.1600, 27.8000),
    "marmara denizi":  (40.6500, 27.9000),
    # EDİRNE
    "edirne":          (41.6800, 26.5600),
    "keşan":           (40.8500, 26.6400),
    "enez":            (40.7300, 26.0800),
    "ergene":          (41.6200, 26.7200),
    "tunca":           (41.7000, 26.5500),
    "meriç":           (41.1800, 26.4000),
    "uzunköprü":       (41.2700, 26.6900),
    "ipsala":          (40.9200, 26.3800),
    # BALIKESİR
    "balıkesir":       (39.6500, 27.8800),
    "erdek":           (40.4000, 27.8000),
    "bandırma":        (40.3500, 27.9700),
    "gönen":           (40.1000, 27.6500),
    "edincik":         (40.3500, 27.8700),
    "marmara adası":   (40.6000, 27.5800),
    "avşa":            (40.5200, 27.5900),
    "manyas gölü":     (40.2000, 27.9700),
    "kuş gölü":        (40.2000, 27.9700),
    # GENEL MARMARA
    "marmara":         (40.6500, 27.9000),
    "istanbul":        (41.0100, 28.9600),
    "sapanca":         (40.6500, 30.4000),
    "sapanca gölü":    (40.6500, 30.2500),
}

FISH_KEYWORDS = [
    "sazan","levrek","çipura","lüfer","palamut","hamsi","istavrit","kalkan",
    "barbun","kefal","alabalık","yayın","sudak","turna","karagöz","sargoz",
    "kolyoz","uskumru","orkinos","mercan","isparoz","kızılkanat","tekir",
    "izmarit","lahos","fangri","dil balığı","kırlangıç","lagos","grida",
    "çinekop","torik","tirsi","sardalya","aterina","iğne balığı",
]

ROD_KEYWORDS = {
    "spin": ["spin", "spinning", "mepps", "kaşık", "rapala", "lure", "yem balığı"],
    "lrf":  ["lrf", "light rock", "micro", "ajing", "finesse", "gulp"],
    "surf": ["surf", "surfcasting", "sahil oltası", "uzak mesafe", "plumb"],
    "feeder": ["feeder", "method", "pellet", "boilie", "karpçılık"],
    "fly":  ["sinek olta", "fly", "yapay sinek", "elk hair", "adams"],
    "jigging": ["jigging", "jig", "silikon", "vertical", "dikey"],
    "trolling": ["trolling", "trol", "tekneden"],
    "bolentino": ["bolentino", "dip olta", "deniz oltası"],
    "olta": ["olta", "iğne", "misina", "avlanma"],
}

def safe_get(url, timeout=20):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        return r
    except Exception as e:
        print(f"  ⚠ {url[:70]}: {e}")
        return None

def make_id(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:14]

def time_ago(dt_str):
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        diff = int((datetime.now(timezone.utc) - dt).total_seconds())
        if diff < 60:    return "Az önce"
        if diff < 3600:  return f"{diff//60}dk önce"
        if diff < 86400: return f"{diff//3600}s önce"
        return f"{diff//86400}g önce"
    except:
        return "Bilinmiyor"

def extract_fish(text):
    tl = text.lower()
    found = [f.title() for f in FISH_KEYWORDS if f in tl]
    return list(dict.fromkeys(found))[:4] or ["Belirtilmemiş"]

def extract_rod(text):
    tl = text.lower()
    for rod, kws in ROD_KEYWORDS.items():
        if any(kw in tl for kw in kws):
            return rod.title()
    return ""

def find_location(text):
    tl = text.lower()
    best, best_coords = None, None
    for name, coords in LOCATIONS.items():
        if name in tl:
            if best is None or len(name) > len(best):
                best, best_coords = name, coords
    return best, best_coords

def classify_type(text, loc):
    tl = (text + " " + (loc or "")).lower()
    if any(w in tl for w in ["baraj","nehir","irmak","dere","çay"]): return "nehir"
    if any(w in tl for w in ["göl","lake"]): return "göl"
    return "deniz"

def build_report(title, body, source, url=""):
    text = title + " " + body
    fish = extract_fish(text)
    if fish == ["Belirtilmemiş"]: return None
    loc, coords = find_location(text)
    if not coords: return None
    rod = extract_rod(text)
    now = datetime.now(timezone.utc).isoformat()
    # Koordinata küçük rastgelelik ekle (üst üste binmesin)
    import random
    lat = coords[0] + random.uniform(-0.02, 0.02)
    lng = coords[1] + random.uniform(-0.02, 0.02)
    return {
        "id":        make_id(title),
        "lat":       round(lat, 5),
        "lng":       round(lng, 5),
        "loc":       loc.title(),
        "fish":      fish,
        "rod":       rod,
        "bait":      "",
        "note":      title[:150],
        "heat":      min(5, len(fish) + 1),
        "type":      classify_type(text, loc),
        "time":      time_ago(now),
        "timestamp": now,
        "source":    source,
        "url":       url,
        "hot":       len(fish) >= 2,
    }

# ── SCRAPER 1: Google News RSS ──────────────────────────────────────────────
def scrape_google_news():
    print("📰 Google News RSS taranıyor...")
    results = []

    queries = [
        # Marmara + balık
        "İstanbul balık tutma",
        "İstanbul lüfer palamut",
        "Marmara denizi balıkçılık",
        "Tekirdağ balık",
        "Kocaeli İzmit balık",
        "Yalova balıkçılık",
        "Bursa Gemlik Mudanya balık",
        "Balıkesir Erdek Bandırma balık",
        "Edirne Meriç balık",
        "Sapanca gölü balık",
        "Büyükçekmece balık",
        "Boğaz lüfer kolyoz",
        "Çanakkale palamut lüfer",
        # Genel Türkiye balıkçılık haberleri
        "balıkçılık raporu Türkiye",
        "balık avı tutuldu",
        "lüfer sezonu Türkiye",
        "palamut göçü",
        "hamsi sezonu Karadeniz",
    ]

    seen = set()
    for q in queries:
        url = (
            f"https://news.google.com/rss/search"
            f"?q={quote_plus(q)}&hl=tr&gl=TR&ceid=TR:tr"
        )
        r = safe_get(url)
        if not r:
            time.sleep(1)
            continue

        try:
            soup = BeautifulSoup(r.content, "xml")
        except Exception:
            soup = BeautifulSoup(r.content, "lxml-xml")

        items = soup.find_all("item")
        print(f"  '{q}' → {len(items)} sonuç")

        for item in items[:8]:
            title_el = item.find("title")
            desc_el  = item.find("description")
            link_el  = item.find("link")
            if not title_el: continue

            title = title_el.get_text(strip=True)
            if title in seen: continue
            seen.add(title)

            desc = desc_el.get_text(strip=True) if desc_el else ""
            link = link_el.get_text(strip=True) if link_el else ""

            rep = build_report(title, desc, "Google Haberler", link)
            if rep:
                results.append(rep)

        time.sleep(1.5)

    print(f"  ✓ {len(results)} rapor elde edildi")
    return results

# ── SCRAPER 2: Türk Haber Siteleri RSS ─────────────────────────────────────
def scrape_news_rss():
    print("📡 Haber RSS taranıyor...")
    results = []

    feeds = [
        ("https://www.hurriyet.com.tr/rss/gundem",        "Hürriyet"),
        ("https://www.sabah.com.tr/rss/yasam.xml",        "Sabah"),
        ("https://www.milliyet.com.tr/rss/rssNew/gundemRss.xml", "Milliyet"),
        ("https://www.sozcu.com.tr/rss.xml",              "Sözcü"),
        ("https://www.haberturk.com/rss",                 "Habertürk"),
        ("https://www.trthaber.com/trthaber.rss",         "TRT Haber"),
    ]

    balik_words = ["balık","balıkçı","olta","avı","lüfer","palamut","hamsi","sazan"]

    for feed_url, src in feeds:
        r = safe_get(feed_url)
        if not r: continue
        try:
            soup = BeautifulSoup(r.content, "xml")
        except:
            soup = BeautifulSoup(r.content, "lxml-xml")

        for item in soup.find_all("item")[:30]:
            title_el = item.find("title")
            desc_el  = item.find("description")
            if not title_el: continue
            title = title_el.get_text(strip=True)
            desc  = desc_el.get_text(strip=True) if desc_el else ""
            text  = (title + " " + desc).lower()
            if not any(w in text for w in balik_words): continue
            rep = build_report(title, desc, src)
            if rep:
                results.append(rep)
        time.sleep(0.8)

    print(f"  ✓ {len(results)} rapor elde edildi")
    return results

# ── SCRAPER 3: Bölgesel Haber Siteleri ─────────────────────────────────────
def scrape_regional_news():
    print("🗺️  Bölgesel haber siteleri taranıyor...")
    results = []

    sites = [
        ("https://www.istanbulgazetesi.com.tr/rss.xml",  "İstanbul Gazetesi"),
        ("https://www.kocaeligazetesi.com.tr/rss.xml",   "Kocaeli Gazetesi"),
        ("https://www.bursagazetesi.com.tr/rss.xml",     "Bursa Gazetesi"),
        ("https://www.tekirdaghaber.com/rss.xml",        "Tekirdağ Haber"),
        ("https://www.edirnehaberleri.com/rss.xml",      "Edirne Haberleri"),
        ("https://www.yalovahaber.com/rss.xml",          "Yalova Haber"),
        ("https://www.balikesirolay.com/rss.xml",        "Balıkesir Olay"),
    ]

    for url, src in sites:
        r = safe_get(url)
        if not r: continue
        try:
            soup = BeautifulSoup(r.content, "xml")
        except:
            soup = BeautifulSoup(r.content, "lxml-xml")
        for item in soup.find_all("item")[:20]:
            title_el = item.find("title")
            desc_el  = item.find("description")
            if not title_el: continue
            title = title_el.get_text(strip=True)
            desc  = desc_el.get_text(strip=True) if desc_el else ""
            text  = (title + " " + desc).lower()
            if not any(w in text for w in ["balık","olta","lüfer","sazan","palamut"]): continue
            rep = build_report(title, desc, src)
            if rep:
                results.append(rep)
        time.sleep(0.8)

    print(f"  ✓ {len(results)} rapor elde edildi")
    return results

# ── SCRAPER 4: balıkavı.com ─────────────────────────────────────────────────
def scrape_balikavi():
    print("🎣 balikavi.com taranıyor...")
    results = []
    pages = [
        "https://www.balikavi.com/haberler/",
        "https://www.balikavi.com/av-raporlari/",
    ]
    for url in pages:
        r = safe_get(url)
        if not r: continue
        soup = BeautifulSoup(r.text, "html.parser")
        for el in soup.select("h2 a, h3 a, .entry-title a, .post-title a")[:15]:
            title = el.get_text(strip=True)
            if len(title) < 10: continue
            rep = build_report(title, "", "balikavi.com", el.get("href",""))
            if rep:
                results.append(rep)
        time.sleep(1)
    print(f"  ✓ {len(results)} rapor elde edildi")
    return results

# ── SCRAPER 5: Özel Google News sorguları (lokasyon bazlı) ──────────────────
def scrape_location_specific():
    print("📍 Lokasyon bazlı Google News taranıyor...")
    results = []

    location_queries = [
        ("büyükçekmece balık",        "büyükçekmece"),
        ("sapanca gölü balık",        "sapanca gölü"),
        ("İzmit körfezi balık",       "izmit"),
        ("boğaz lüfer kolyoz",        "boğaz"),
        ("sarıyer balık",             "sarıyer"),
        ("beykoz balık",              "beykoz"),
        ("bostancı sahil balık",      "bostancı"),
        ("erdek bandırma balık",      "erdek"),
        ("gemlik mudanya balık",      "gemlik"),
        ("marmara adası balık",       "marmara adası"),
        ("tekirdağ şarköy balık",     "tekirdağ"),
        ("edirne meriç balık",        "edirne"),
        ("yalova çınarcık balık",     "yalova"),
        ("iznik gölü balık",          "iznik gölü"),
    ]

    seen = set()
    for q, loc_hint in location_queries:
        url = (
            f"https://news.google.com/rss/search"
            f"?q={quote_plus(q)}&hl=tr&gl=TR&ceid=TR:tr"
        )
        r = safe_get(url)
        if not r:
            time.sleep(1)
            continue

        try:
            soup = BeautifulSoup(r.content, "xml")
        except:
            soup = BeautifulSoup(r.content, "lxml-xml")

        for item in soup.find_all("item")[:6]:
            title_el = item.find("title")
            if not title_el: continue
            title = title_el.get_text(strip=True)
            if title in seen: continue
            seen.add(title)

            desc_el = item.find("description")
            desc = desc_el.get_text(strip=True) if desc_el else ""

            # Lokasyon bulunamazsa hint'i text'e ekle
            text_with_hint = title + " " + desc + " " + loc_hint
            rep = build_report(text_with_hint, "", "Google Haberler")
            if rep:
                results.append(rep)

        time.sleep(1.5)

    print(f"  ✓ {len(results)} rapor elde edildi")
    return results

# ── DEMO VERİ (hiç bulunamazsa kullanılır) ─────────────────────────────────
FALLBACK = [
    {"id":"fb01","lat":41.150,"lng":28.800,"loc":"Büyükçekmece Gölü","fish":["Sazan","Turna"],"rod":"Feeder","bait":"Mısır, solucan","note":"Demo: Sabah erken harika avlanma.","heat":5,"type":"göl","hot":True,"source":"Demo"},
    {"id":"fb02","lat":40.960,"lng":29.090,"loc":"Bostancı Sahili","fish":["Lüfer","İstavrit"],"rod":"Spin","bait":"Mepps No:3","note":"Demo: Lüfer girişi başladı.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"fb03","lat":41.080,"lng":29.050,"loc":"Boğaziçi","fish":["Lüfer","Kolyoz","Palamut"],"rod":"Trolling","bait":"Çukur kaşık","note":"Demo: Göç dönemi, palamut aktif.","heat":5,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"fb04","lat":41.170,"lng":29.050,"loc":"Sarıyer","fish":["Lüfer","Kefal"],"rod":"Spin","bait":"Kaşık, rapala","note":"Demo: Akşam üstü lüfer çıkıyor.","heat":4,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"fb05","lat":40.760,"lng":29.920,"loc":"İzmit Körfezi","fish":["Çipura","Levrek"],"rod":"LRF","bait":"Micro jig, Gulp","note":"Demo: Çipura ve levrek aktif.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"fb06","lat":40.650,"lng":29.270,"loc":"Yalova","fish":["Kefal","Levrek"],"rod":"Olta","bait":"Solucan","note":"Demo: İskele başında kefal.","heat":3,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"fb07","lat":40.430,"lng":29.160,"loc":"Gemlik","fish":["Çipura","Levrek","Karagöz"],"rod":"LRF","bait":"Silikon, micro jig","note":"Demo: Sabah çipura bol.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"fb08","lat":40.380,"lng":28.880,"loc":"Mudanya","fish":["Kefal","Levrek"],"rod":"Feeder","bait":"Ekmek, deniz kurdu","note":"Demo: Mudanya iskelesi aktif.","heat":3,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"fb09","lat":40.400,"lng":27.800,"loc":"Erdek","fish":["Çipura","Karagöz","Sargoz"],"rod":"LRF","bait":"Micro jig","note":"Demo: Erdek açıkları çok iyi.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"fb10","lat":40.350,"lng":27.970,"loc":"Bandırma","fish":["Kefal","Çipura"],"rod":"Olta","bait":"Solucan, ekmek","note":"Demo: Bandırma limanı.","heat":3,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"fb11","lat":40.970,"lng":27.510,"loc":"Tekirdağ","fish":["Lüfer","Palamut","Kolyoz"],"rod":"Surf","bait":"Çoklu iğne, olta balığı","note":"Demo: Tekirdağ sahili aktif.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"fb12","lat":40.610,"lng":27.110,"loc":"Şarköy","fish":["Çipura","Levrek","Barbun"],"rod":"LRF","bait":"Berkley Gulp","note":"Demo: Şarköy açıkları harika.","heat":4,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"fb13","lat":41.680,"lng":26.560,"loc":"Edirne - Meriç Nehri","fish":["Sazan","Yayın","Turna"],"rod":"Feeder","bait":"Boilie, canlı balık","note":"Demo: Meriç nehri yayın aktif.","heat":4,"type":"nehir","hot":True,"source":"Demo"},
    {"id":"fb14","lat":40.650,"lng":30.250,"loc":"Sapanca Gölü","fish":["Alabalık","Sazan","Yayın"],"rod":"Spin","bait":"Rapala, solucan","note":"Demo: Sabah 6-9 alabalık harika.","heat":5,"type":"göl","hot":True,"source":"Demo"},
    {"id":"fb15","lat":40.430,"lng":29.720,"loc":"İznik Gölü","fish":["Sazan","Levrek","Sudak"],"rod":"Feeder","bait":"Pellet, mısır","note":"Demo: İznik gölü sazan sezonu.","heat":4,"type":"göl","hot":False,"source":"Demo"},
]

# ── ANA FONKSİYON ───────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print(f"🎣 Balık Radarı Scraper — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("   Bölge: İstanbul, Kocaeli, Yalova, Bursa, Tekirdağ, Edirne, Balıkesir")
    print("=" * 60)

    # Mevcut veriyi yükle
    existing = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f).get("reports", [])
            print(f"📂 Mevcut: {len(existing)} rapor")
        except Exception as e:
            print(f"⚠ Yükleme hatası: {e}")

    # Tüm kaynakları tara
    new_reports = []
    new_reports += scrape_google_news()
    new_reports += scrape_news_rss()
    new_reports += scrape_regional_news()
    new_reports += scrape_balikavi()
    new_reports += scrape_location_specific()

    print(f"\n📊 Toplam yeni: {len(new_reports)}")

    # Zaman damgası güncelle
    now_iso = datetime.now(timezone.utc).isoformat()
    for r in new_reports:
        if "timestamp" not in r:
            r["timestamp"] = now_iso
        r["time"] = time_ago(r["timestamp"])

    # Yeterli veri yoksa fallback ekle
    if len(new_reports) < 5:
        print("⚠ Yeterli veri yok, demo veri ekleniyor...")
        for r in FALLBACK:
            r["timestamp"] = now_iso
            r["time"] = "Az önce"
        new_reports = FALLBACK + new_reports

    # Mevcut + yeni birleştir (ID'ye göre tekrar engelle)
    all_map = {r["id"]: r for r in existing}
    added = 0
    for r in new_reports:
        if r["id"] not in all_map:
            all_map[r["id"]] = r
            added += 1

    # Tarihe göre sırala, MAX_REPORTS tut
    sorted_reports = sorted(
        all_map.values(),
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )[:MAX_REPORTS]

    # Kaydet
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "last_updated": now_iso,
            "total":        len(sorted_reports),
            "reports":      sorted_reports,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Tamamlandı!")
    print(f"   Yeni eklenen : {added}")
    print(f"   Toplam rapor : {len(sorted_reports)}")
    print(f"   Dosya        : {OUTPUT_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    main()
