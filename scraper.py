#!/usr/bin/env python3
"""
Türkiye Balık Radarı - Gelişmiş Marmara Scraper v3
Kaynaklar: Google News, RSS, Telegram, Instagram, Facebook, Forumlar
Bölge: İstanbul (Galata Köprüsü, Eminönü, Karaköy dahil), Kocaeli, Yalova, Bursa, Tekirdağ, Edirne, Balıkesir
"""

import requests
from bs4 import BeautifulSoup
import json, os, time, hashlib, random
from datetime import datetime, timezone
from urllib.parse import quote_plus

OUTPUT_FILE = "data/reports.json"
MAX_REPORTS = 300

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}

# ══════════════════════════════════════════════════════════════════
# KOORDİNATLAR — Google Maps doğrulanmış
# ══════════════════════════════════════════════════════════════════
LOCATIONS = {
    # İSTANBUL — ÜNLÜ BALIK TUTMA YERLERİ
    "galata köprüsü":       (41.0164, 28.9740),
    "galata köprüsü altı":  (41.0164, 28.9740),
    "galata":               (41.0255, 28.9741),
    "karaköy":              (41.0232, 28.9745),
    "eminönü":              (41.0168, 28.9700),
    "eminönü iskelesi":     (41.0168, 28.9700),
    "unkapanı":             (41.0200, 28.9520),
    "haliç":                (41.0300, 28.9400),
    "sirkeci":              (41.0133, 28.9780),
    "sarayburnu":           (41.0133, 28.9820),
    # İSTANBUL — BOĞAZ
    "bebek":                (41.0780, 29.0440),
    "arnavutköy":           (41.0730, 29.0390),
    "ortaköy":              (41.0530, 29.0270),
    "beşiktaş":             (41.0430, 29.0070),
    "kabataş":              (41.0340, 29.0040),
    "dolmabahçe":           (41.0390, 29.0000),
    "çengelköy":            (41.0620, 29.0600),
    "anadolu hisarı":       (41.0830, 29.0730),
    "kanlıca":              (41.1000, 29.0800),
    "paşabahçe":            (41.1400, 29.0900),
    "beykoz":               (41.1220, 29.1050),
    "anadolu kavağı":       (41.1980, 29.0760),
    "rumeli kavağı":        (41.2020, 29.0600),
    "sarıyer":              (41.1670, 29.0500),
    "yeniköy":              (41.1100, 29.0600),
    "tarabya":              (41.1300, 29.0600),
    "büyükdere":            (41.1500, 29.0600),
    "boğaz":                (41.0800, 29.0500),
    "boğaziçi":             (41.0800, 29.0500),
    "istanbul boğazı":      (41.0800, 29.0500),
    # İSTANBUL — ANADOLU YAKASI
    "üsküdar":              (41.0230, 29.0140),
    "kadıköy":              (40.9900, 29.0230),
    "haydarpaşa":           (41.0010, 29.0140),
    "moda":                 (40.9800, 29.0290),
    "bostancı":             (40.9600, 29.0900),
    "maltepe":              (40.9300, 29.1300),
    "kartal":               (40.9100, 29.1900),
    "pendik":               (40.8700, 29.2300),
    "tuzla":                (40.8200, 29.2900),
    "darıca":               (40.7700, 29.3700),
    # İSTANBUL — AVRUPA YAKASI SAHİL
    "kumkapı":              (41.0050, 28.9580),
    "yenikapı":             (41.0020, 28.9510),
    "bakırköy":             (40.9800, 28.8700),
    "florya":               (40.9700, 28.8000),
    "yeşilköy":             (40.9700, 28.8200),
    "avcılar":              (40.9800, 28.7200),
    "küçükçekmece":         (41.0100, 28.7700),
    "büyükçekmece":         (41.1500, 28.8000),
    "silivri":              (41.0700, 28.2500),
    "çatalca":              (41.1430, 28.4610),
    # İSTANBUL — ADALAR
    "adalar":               (40.8700, 29.1100),
    "büyükada":             (40.8720, 29.1250),
    "heybeliada":           (40.8800, 29.0900),
    "burgazada":            (40.8800, 29.0600),
    "kınalıada":            (40.9000, 29.0200),
    # İSTANBUL — KARADENİZ
    "kilyos":               (41.2520, 29.0200),
    "şile":                 (41.1800, 29.6100),
    "ağva":                 (41.0970, 30.0000),
    "karaburun":            (41.3500, 28.6900),
    # KOCAELİ
    "izmit":                (40.7630, 29.9190),
    "izmit körfezi":        (40.7200, 29.7000),
    "kocaeli":              (40.7630, 29.9190),
    "gebze":                (40.8030, 29.4310),
    "hereke":               (40.7900, 29.6200),
    "körfez":               (40.7700, 29.7700),
    "karamürsel":           (40.6920, 29.6100),
    "gölcük":               (40.6520, 29.8330),
    "derince":              (40.7480, 29.8410),
    "kandıra":              (41.0730, 30.1570),
    # YALOVA
    "yalova":               (40.6550, 29.2770),
    "yalova iskelesi":      (40.6580, 29.2750),
    "çınarcık":             (40.6390, 29.1210),
    "armutlu":              (40.5280, 28.8310),
    "altınova":             (40.5990, 29.5180),
    # BURSA
    "bursa":                (40.1830, 29.0610),
    "mudanya":              (40.3760, 28.8840),
    "mudanya iskelesi":     (40.3760, 28.8840),
    "gemlik":               (40.4330, 29.1630),
    "gemlik körfezi":       (40.4000, 29.1500),
    "orhangazi":            (40.4910, 29.3150),
    "iznik":                (40.4320, 29.7200),
    "iznik gölü":           (40.4000, 29.5500),
    "uluabat gölü":         (40.1700, 28.6200),
    "apolyont":             (40.1700, 28.6200),
    "uluabat":              (40.1700, 28.6200),
    # TEKİRDAĞ
    "tekirdağ":             (40.9780, 27.5150),
    "tekirdağ sahili":      (40.9780, 27.5150),
    "marmara ereğlisi":     (40.9680, 27.9590),
    "şarköy":               (40.6100, 27.1120),
    "mürefte":              (40.6700, 27.2580),
    "barbaros":             (40.8220, 27.4520),
    "çorlu":                (41.1590, 27.8010),
    "hayrabolu":            (41.2230, 27.1060),
    # EDİRNE
    "edirne":               (41.6770, 26.5560),
    "meriç":                (41.1800, 26.4000),
    "meriç nehri":          (41.1800, 26.4000),
    "tunca":                (41.7000, 26.5550),
    "tunca nehri":          (41.7000, 26.5550),
    "ergene":               (41.6200, 26.7200),
    "ergene nehri":         (41.6200, 26.7200),
    "enez":                 (40.7290, 26.0810),
    "keşan":                (40.8520, 26.6380),
    "ipsala":               (40.9230, 26.3800),
    "uzunköprü":            (41.2700, 26.6900),
    # BALIKESİR
    "balıkesir":            (39.6490, 27.8830),
    "erdek":                (40.4030, 27.7980),
    "erdek körfezi":        (40.3800, 27.8200),
    "bandırma":             (40.3510, 27.9760),
    "bandırma körfezi":     (40.3300, 27.9500),
    "gönen":                (40.0970, 27.6510),
    "edincik":              (40.3530, 27.8690),
    "marmara adası":        (40.5980, 27.5800),
    "avşa":                 (40.5230, 27.5880),
    "manyas gölü":          (40.2020, 27.9720),
    "kuş gölü":             (40.2020, 27.9720),
    "kapıdağ":              (40.4200, 27.7000),
    # GENEL
    "marmara denizi":       (40.6500, 27.9000),
    "marmara":              (40.6500, 27.9000),
    "istanbul":             (41.0082, 28.9784),
    "sapanca":              (40.6960, 30.2690),
    "sapanca gölü":         (40.6960, 30.2690),
}

FISH_KEYWORDS = [
    "sazan","levrek","çipura","lüfer","palamut","hamsi","istavrit","kalkan",
    "barbun","kefal","alabalık","yayın","sudak","turna","karagöz","sargoz",
    "kolyoz","uskumru","tekir","izmarit","çinekop","torik","tirsi","sardalya",
    "aterina","iğne balığı","dil balığı","kırlangıç","lagos","grida","lahos",
    "fangri","isparoz","mercan","kızılkanat","orkinos",
]

ROD_KEYWORDS = {
    "Spin":      ["spin","spinning","mepps","kaşık","rapala","lure","wobbler","popper","jerkbait"],
    "LRF":       ["lrf","light rock","micro jig","ajing","finesse","gulp","berkley","micro"],
    "Surf":      ["surf","surfcasting","sahil oltası","uzak mesafe","plumb","darak"],
    "Feeder":    ["feeder","method feeder","pellet","boilie","karpçılık","pva"],
    "Fly":       ["sinek olta","fly fishing","yapay sinek","elk hair","adams","streamer"],
    "Jigging":   ["jigging","jig","silikon","vertical jigging","dikey","twister"],
    "Trolling":  ["trolling","trol","tekneden","rapala cd"],
    "Bolentino": ["bolentino","dip olta","deniz oltası","paragat"],
    "Zıpkın":   ["zıpkın","spearfishing","dalış"],
    "Olta":      ["olta","iğne","misina","avlandı","tutuldu"],
}

def safe_get(url, timeout=20):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        return r
    except Exception as e:
        print(f"  ⚠ {url[:65]}: {e}")
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
            return rod
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

def build_report(title, body, source, url="", force_loc=None, force_coords=None):
    text = title + " " + body
    fish = extract_fish(text)
    if fish == ["Belirtilmemiş"]: return None
    if force_loc and force_coords:
        loc, coords = force_loc, force_coords
    else:
        loc, coords = find_location(text)
    if not coords: return None
    rod = extract_rod(text)
    now = datetime.now(timezone.utc).isoformat()
    lat = coords[0] + random.uniform(-0.008, 0.008)
    lng = coords[1] + random.uniform(-0.008, 0.008)
    return {
        "id":        make_id(title + source),
        "lat":       round(lat, 6),
        "lng":       round(lng, 6),
        "loc":       loc.title(),
        "fish":      fish,
        "rod":       rod,
        "bait":      "",
        "note":      title[:160],
        "heat":      min(5, len(fish) + 1),
        "type":      classify_type(text, loc),
        "time":      time_ago(now),
        "timestamp": now,
        "source":    source,
        "url":       url,
        "hot":       len(fish) >= 2,
    }

def scrape_google_news_general():
    print("📰 Google News (genel) taranıyor...")
    results = []
    queries = [
        "İstanbul balık tutma raporu", "İstanbul lüfer palamut kolyoz",
        "Marmara denizi balıkçılık", "Boğaz balık tutma",
        "Galata köprüsü balık", "Tekirdağ Kocaeli balıkçılık",
        "Yalova Bursa deniz balık", "Edirne Meriç balık avı",
        "Balıkesir Erdek Bandırma balık", "Sapanca gölü balık tutma",
        "lüfer sezonu Marmara", "palamut göçü İstanbul",
        "hamsi kolyoz istavrit tutuldu", "çipura levrek tutuldu Marmara",
        "sazan yayın sudak tutuldu", "spin lrf surf balık İstanbul",
        "olta balık avı Kocaeli Yalova", "balık haberleri Bursa Mudanya",
        "Gemlik körfezi balık", "İzmit körfezi çipura levrek",
    ]
    seen = set()
    for q in queries:
        url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=tr&gl=TR&ceid=TR:tr"
        r = safe_get(url)
        if not r: time.sleep(1); continue
        try: soup = BeautifulSoup(r.content, "xml")
        except: soup = BeautifulSoup(r.content, "lxml-xml")
        items = soup.find_all("item")
        print(f"  '{q[:38]}' → {len(items)}")
        for item in items[:8]:
            t = item.find("title"); d = item.find("description"); l = item.find("link")
            if not t: continue
            title = t.get_text(strip=True)
            if title in seen: continue
            seen.add(title)
            desc = d.get_text(strip=True) if d else ""
            link = l.get_text(strip=True) if l else ""
            rep = build_report(title, desc, "Google Haberler", link)
            if rep: results.append(rep)
        time.sleep(1.2)
    print(f"  ✓ {len(results)} rapor")
    return results

def scrape_google_news_locations():
    print("📍 Google News (lokasyon bazlı) taranıyor...")
    results = []
    lq = [
        ("galata köprüsü balık olta",       "galata köprüsü",   LOCATIONS["galata köprüsü"]),
        ("eminönü balık tutma",              "eminönü",          LOCATIONS["eminönü"]),
        ("karaköy iskelesi balık",           "karaköy",          LOCATIONS["karaköy"]),
        ("unkapanı balık olta",              "unkapanı",         LOCATIONS["unkapanı"]),
        ("haliç balık avı",                  "haliç",            LOCATIONS["haliç"]),
        ("sarıyer balık tutma",              "sarıyer",          LOCATIONS["sarıyer"]),
        ("beykoz balık",                     "beykoz",           LOCATIONS["beykoz"]),
        ("bebek arnavutköy balık",           "bebek",            LOCATIONS["bebek"]),
        ("anadolu kavağı balık",             "anadolu kavağı",   LOCATIONS["anadolu kavağı"]),
        ("rumeli kavağı balık",              "rumeli kavağı",    LOCATIONS["rumeli kavağı"]),
        ("bostancı sahili lüfer",            "bostancı",         LOCATIONS["bostancı"]),
        ("kadıköy moda balık",               "kadıköy",          LOCATIONS["kadıköy"]),
        ("büyükçekmece gölü balık",          "büyükçekmece",     LOCATIONS["büyükçekmece"]),
        ("kilyos sahil balık",               "kilyos",           LOCATIONS["kilyos"]),
        ("şile ağva balık",                  "şile",             LOCATIONS["şile"]),
        ("İzmit körfezi balık çipura",       "izmit körfezi",    LOCATIONS["izmit körfezi"]),
        ("karamürsel gölcük balık",          "karamürsel",       LOCATIONS["karamürsel"]),
        ("yalova balık iskelesi",            "yalova iskelesi",  LOCATIONS["yalova iskelesi"]),
        ("çınarcık armutlu balık",           "çınarcık",         LOCATIONS["çınarcık"]),
        ("mudanya iskelesi balık",           "mudanya iskelesi", LOCATIONS["mudanya iskelesi"]),
        ("gemlik körfezi çipura levrek",     "gemlik körfezi",   LOCATIONS["gemlik körfezi"]),
        ("iznik gölü balık tutma",           "iznik gölü",       LOCATIONS["iznik gölü"]),
        ("uluabat gölü balık",               "uluabat gölü",     LOCATIONS["uluabat gölü"]),
        ("tekirdağ sahili balık",            "tekirdağ sahili",  LOCATIONS["tekirdağ sahili"]),
        ("şarköy mürefte balık",             "şarköy",           LOCATIONS["şarköy"]),
        ("marmara ereğlisi balık",           "marmara ereğlisi", LOCATIONS["marmara ereğlisi"]),
        ("meriç nehri balık sazan",          "meriç nehri",      LOCATIONS["meriç nehri"]),
        ("tunca nehri balık",                "tunca nehri",      LOCATIONS["tunca nehri"]),
        ("ergene nehri balık",               "ergene nehri",     LOCATIONS["ergene nehri"]),
        ("erdek körfezi balık çipura",       "erdek körfezi",    LOCATIONS["erdek körfezi"]),
        ("bandırma körfezi balık",           "bandırma körfezi", LOCATIONS["bandırma körfezi"]),
        ("marmara adası avşa balık",         "marmara adası",    LOCATIONS["marmara adası"]),
        ("manyas kuş gölü balık",            "manyas gölü",      LOCATIONS["manyas gölü"]),
        ("sapanca gölü balık alabalık",      "sapanca gölü",     LOCATIONS["sapanca gölü"]),
    ]
    seen = set()
    for q, loc_name, coords in lq:
        url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=tr&gl=TR&ceid=TR:tr"
        r = safe_get(url)
        if not r: time.sleep(1); continue
        try: soup = BeautifulSoup(r.content, "xml")
        except: soup = BeautifulSoup(r.content, "lxml-xml")
        for item in soup.find_all("item")[:6]:
            t = item.find("title")
            if not t: continue
            title = t.get_text(strip=True)
            if title in seen: continue
            seen.add(title)
            d = item.find("description")
            desc = d.get_text(strip=True) if d else ""
            rep = build_report(title, desc, "Google Haberler",
                               force_loc=loc_name, force_coords=coords)
            if rep: results.append(rep)
        time.sleep(1.0)
    print(f"  ✓ {len(results)} rapor")
    return results

def scrape_telegram():
    print("📱 Telegram kanalları taranıyor...")
    results = []
    channels = [
        ("https://t.me/s/balikcilar",          "Telegram: Balıkçılar"),
        ("https://t.me/s/istanbulbalikcilar",   "Telegram: İstanbul Balıkçılar"),
        ("https://t.me/s/marmara_balik",        "Telegram: Marmara Balık"),
        ("https://t.me/s/lufer_palamut",        "Telegram: Lüfer Palamut"),
        ("https://t.me/s/balikcirapor",         "Telegram: Balıkçı Rapor"),
        ("https://t.me/s/istanbulolta",         "Telegram: İstanbul Olta"),
        ("https://t.me/s/spin_lrf_tr",          "Telegram: Spin LRF TR"),
        ("https://t.me/s/turkiyebalikcilar",    "Telegram: Türkiye Balıkçılar"),
        ("https://t.me/s/bogazbalik",           "Telegram: Boğaz Balık"),
        ("https://t.me/s/galatabalik",          "Telegram: Galata Balık"),
        ("https://t.me/s/kocaelibalikcilar",    "Telegram: Kocaeli Balıkçılar"),
        ("https://t.me/s/bursabalik",           "Telegram: Bursa Balık"),
        ("https://t.me/s/tekirdagbalik",        "Telegram: Tekirdağ Balık"),
        ("https://t.me/s/balikciliktr",         "Telegram: Balıkçılık TR"),
        ("https://t.me/s/oltacilar",            "Telegram: Oltacılar"),
        ("https://t.me/s/spinningturkiye",      "Telegram: Spinning Türkiye"),
        ("https://t.me/s/lrfturkiye",           "Telegram: LRF Türkiye"),
        ("https://t.me/s/surfcastingtr",        "Telegram: Surf Casting TR"),
        ("https://t.me/s/eminonubalik",         "Telegram: Eminönü Balık"),
        ("https://t.me/s/galatakorpusu",        "Telegram: Galata Köprüsü"),
    ]
    for url, src in channels:
        r = safe_get(url)
        if not r: time.sleep(0.5); continue
        soup = BeautifulSoup(r.text, "html.parser")
        for msg in soup.select(".tgme_widget_message_text, .js-message_text, .text")[:10]:
            text = msg.get_text(strip=True)
            if len(text) < 20: continue
            rep = build_report(text[:200], "", src)
            if rep: results.append(rep)
        time.sleep(1.0)
    print(f"  ✓ {len(results)} rapor")
    return results

def scrape_instagram():
    print("📸 Instagram taranıyor...")
    results = []
    hashtags = [
        ("istanbulbalik",    "Instagram: #istanbulbalık"),
        ("galatakorpusu",    "Instagram: #galataköprüsü"),
        ("eminonubalik",     "Instagram: #eminönübalık"),
        ("marmarabalik",     "Instagram: #marmarabalık"),
        ("luferbaligi",      "Instagram: #lüferbalığı"),
        ("palamutbaligi",    "Instagram: #palamutbalığı"),
        ("oltacilar",        "Instagram: #oltacılar"),
        ("spinbalik",        "Instagram: #spinbalık"),
        ("lrfturkiye",       "Instagram: #lrfturkiye"),
        ("surfcasting",      "Instagram: #surfcasting"),
        ("balikcilik",       "Instagram: #balıkçılık"),
        ("baliktutma",       "Instagram: #balıktutma"),
        ("sazan",            "Instagram: #sazan"),
        ("levrek",           "Instagram: #levrek"),
        ("cipura",           "Instagram: #çipura"),
        ("bursabalik",       "Instagram: #bursabalık"),
        ("tekirdagbalik",    "Instagram: #tekirdağbalık"),
        ("izmitbalik",       "Instagram: #izmitbalık"),
        ("yalovabalik",      "Instagram: #yalovabalık"),
        ("edirnebalik",      "Instagram: #edirnebalık"),
    ]
    for tag, src in hashtags:
        url = f"https://www.instagram.com/explore/tags/{tag}/"
        r = safe_get(url)
        if not r: time.sleep(1.5); continue
        soup = BeautifulSoup(r.text, "html.parser")
        for meta in soup.find_all("meta", {"property": "og:description"}):
            content = meta.get("content", "")
            if any(w in content.lower() for w in ["balık","lüfer","sazan","levrek","palamut","olta"]):
                rep = build_report(content[:200], "", src)
                if rep: results.append(rep)
        time.sleep(1.5)
    print(f"  ✓ {len(results)} rapor")
    return results

def scrape_facebook():
    print("👥 Facebook taranıyor...")
    results = []
    fb_pages = [
        ("https://www.facebook.com/groups/istanbulbalikcilar/",  "FB: İstanbul Balıkçılar"),
        ("https://www.facebook.com/groups/marmarabalik/",        "FB: Marmara Balık"),
        ("https://www.facebook.com/groups/bogazbalikcilar/",     "FB: Boğaz Balıkçılar"),
        ("https://www.facebook.com/groups/lrfturkiye/",          "FB: LRF Türkiye"),
        ("https://www.facebook.com/groups/spinningtr/",          "FB: Spinning TR"),
        ("https://www.facebook.com/groups/surfcastingturkiye/",  "FB: Surf Casting"),
        ("https://www.facebook.com/groups/kocaelibalik/",        "FB: Kocaeli Balık"),
        ("https://www.facebook.com/groups/bursabalikcilar/",     "FB: Bursa Balıkçılar"),
        ("https://www.facebook.com/groups/tekirdagbalik/",       "FB: Tekirdağ Balık"),
        ("https://www.facebook.com/groups/balikcilikturkiye/",   "FB: Balıkçılık TR"),
        ("https://www.facebook.com/groups/oltacilartr/",         "FB: Oltacılar TR"),
        ("https://www.facebook.com/groups/galatakorpususevenler/","FB: Galata Köprüsü"),
        ("https://www.facebook.com/groups/eminonubalik/",        "FB: Eminönü Balık"),
    ]
    for url, src in fb_pages:
        r = safe_get(url)
        if not r: time.sleep(1); continue
        soup = BeautifulSoup(r.text, "html.parser")
        for meta in soup.find_all("meta", {"property": ["og:description","og:title"]}):
            content = meta.get("content", "")
            if len(content) < 15: continue
            if any(w in content.lower() for w in ["balık","lüfer","sazan","levrek","palamut","olta","avlandı","tutuldu"]):
                rep = build_report(content[:200], "", src, url)
                if rep: results.append(rep)
        time.sleep(1.5)
    print(f"  ✓ {len(results)} rapor")
    return results

def scrape_news_rss():
    print("📡 Haber RSS taranıyor...")
    results = []
    feeds = [
        ("https://www.hurriyet.com.tr/rss/gundem",               "Hürriyet"),
        ("https://www.sabah.com.tr/rss/yasam.xml",               "Sabah"),
        ("https://www.milliyet.com.tr/rss/rssNew/gundemRss.xml", "Milliyet"),
        ("https://www.sozcu.com.tr/rss.xml",                     "Sözcü"),
        ("https://www.haberturk.com/rss",                        "Habertürk"),
        ("https://www.trthaber.com/trthaber.rss",                "TRT Haber"),
        ("https://www.ntv.com.tr/feeds/rss/son-dakika",          "NTV"),
        ("https://www.istanbulgazetesi.com.tr/rss.xml",          "İstanbul Gazetesi"),
        ("https://www.kocaeligazetesi.com.tr/rss.xml",           "Kocaeli Gazetesi"),
        ("https://www.bursagazetesi.com.tr/rss.xml",             "Bursa Gazetesi"),
        ("https://www.tekirdaghaber.com/rss.xml",                "Tekirdağ Haber"),
        ("https://www.edirnehaberleri.com/rss.xml",              "Edirne Haberleri"),
        ("https://www.yalovahaber.com/rss.xml",                  "Yalova Haber"),
        ("https://www.balikesirgercek.com/rss.xml",              "Balıkesir Gerçek"),
    ]
    balik_words = ["balık","balıkçı","olta","lüfer","palamut","hamsi","sazan","levrek","çipura","avı","tutuldu"]
    for feed_url, src in feeds:
        r = safe_get(feed_url)
        if not r: continue
        try: soup = BeautifulSoup(r.content, "xml")
        except: soup = BeautifulSoup(r.content, "lxml-xml")
        for item in soup.find_all("item")[:25]:
            t = item.find("title"); d = item.find("description")
            if not t: continue
            title = t.get_text(strip=True)
            desc  = d.get_text(strip=True) if d else ""
            if not any(w in (title+desc).lower() for w in balik_words): continue
            rep = build_report(title, desc, src)
            if rep: results.append(rep)
        time.sleep(0.8)
    print(f"  ✓ {len(results)} rapor")
    return results

def scrape_fishing_sites():
    print("🎣 Balıkçılık siteleri taranıyor...")
    results = []
    sites = [
        ("https://www.balikavi.com/haberler/",             "balikavi.com"),
        ("https://www.balikavi.com/av-raporlari/",         "balikavi.com"),
        ("https://www.balikcilarsitesi.com/av-raporlari/", "balikcilarsitesi.com"),
        ("https://www.oltaci.net/haberler/",               "oltaci.net"),
        ("https://www.sporfishing.com/haberler/",          "sporfishing.com"),
    ]
    for url, src in sites:
        r = safe_get(url)
        if not r: time.sleep(0.5); continue
        soup = BeautifulSoup(r.text, "html.parser")
        for el in soup.select("h1 a, h2 a, h3 a, .entry-title a, .post-title a")[:15]:
            title = el.get_text(strip=True)
            if len(title) < 12: continue
            rep = build_report(title, "", src, el.get("href",""))
            if rep: results.append(rep)
        time.sleep(1.0)
    print(f"  ✓ {len(results)} rapor")
    return results

# ══════════════════════════════════════════════════════════════════
# DEMO VERİ — Doğru koordinatlı Marmara odaklı
# ══════════════════════════════════════════════════════════════════
FALLBACK = [
    {"id":"fb01","lat":41.0164,"lng":28.9740,"loc":"Galata Köprüsü","fish":["Lüfer","Kolyoz","İstavrit"],"rod":"Olta","bait":"Hamsi, istavrit iç","note":"Galata köprüsü klasik olta noktası. Akşam lüfer aktif.","heat":5,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"fb02","lat":41.0168,"lng":28.9700,"loc":"Eminönü","fish":["Kefal","Lüfer"],"rod":"Olta","bait":"Ekmek, hamsi","note":"Eminönü iskelesi. Sabah kefal, akşam lüfer.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"fb03","lat":41.0232,"lng":28.9745,"loc":"Karaköy","fish":["Lüfer","İstavrit","Kefal"],"rod":"Spin","bait":"Küçük kaşık, mepps","note":"Karaköy rıhtımı. Akşam lüfer girişi güzel.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"fb04","lat":41.0200,"lng":28.9520,"loc":"Unkapanı","fish":["Kefal","Sazan"],"rod":"Olta","bait":"Solucan, ekmek","note":"Unkapanı köprüsü altı. Kefal ve sazan aktif.","heat":3,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"fb05","lat":41.0300,"lng":28.9400,"loc":"Haliç","fish":["Kefal","Sazan","Levrek"],"rod":"Feeder","bait":"Solucan, ekmek","note":"Haliç kıyısı. Kefal sürüsü var.","heat":3,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"fb06","lat":41.1670,"lng":29.0500,"loc":"Sarıyer","fish":["Lüfer","Palamut","Kolyoz"],"rod":"Trolling","bait":"Çukur kaşık, rapala","note":"Sarıyer açıkları. Palamut göçü devam ediyor.","heat":5,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"fb07","lat":41.1980,"lng":29.0760,"loc":"Anadolu Kavağı","fish":["Lüfer","Kalkan"],"rod":"Bolentino","bait":"Hamsi, deniz kurdu","note":"Anadolu Kavağı. Kalkan dip oltayla güzel.","heat":4,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"fb08","lat":41.1220,"lng":29.1050,"loc":"Beykoz","fish":["Levrek","Kefal"],"rod":"Spin","bait":"Popper, yüzey lure","note":"Beykoz sahili. Akşam levrek aktif.","heat":4,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"fb09","lat":40.9600,"lng":29.0900,"loc":"Bostancı Sahili","fish":["Lüfer","İstavrit"],"rod":"Spin","bait":"Mepps No:3, kaşık","note":"Bostancı. Lüfer girişi başladı.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"fb10","lat":41.1500,"lng":28.8000,"loc":"Büyükçekmece","fish":["Sazan","Turna","Yayın"],"rod":"Feeder","bait":"Mısır, solucan, boilie","note":"Büyükçekmece gölü. Sabah erken harika avlanma.","heat":5,"type":"göl","hot":True,"source":"Demo"},
    {"id":"fb11","lat":40.7200,"lng":29.7000,"loc":"İzmit Körfezi","fish":["Çipura","Levrek","Karagöz"],"rod":"LRF","bait":"Micro jig, Berkley Gulp","note":"İzmit körfezi. Çipura ve levrek aktif.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"fb12","lat":40.6580,"lng":29.2750,"loc":"Yalova İskelesi","fish":["Kefal","Levrek"],"rod":"Olta","bait":"Solucan, deniz kurdu","note":"Yalova iskelesi. Sabah kefal bolca.","heat":3,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"fb13","lat":40.3760,"lng":28.8840,"loc":"Mudanya İskelesi","fish":["Çipura","Levrek","Karagöz"],"rod":"LRF","bait":"Silikon, micro jig 5g","note":"Mudanya iskelesi. LRF ile sabah çipura güzel.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"fb14","lat":40.4000,"lng":29.1500,"loc":"Gemlik Körfezi","fish":["Levrek","Çipura"],"rod":"Spin","bait":"Rapala, yüzey lure","note":"Gemlik körfezi. Sabah erken levrek aktif.","heat":4,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"fb15","lat":40.4000,"lng":29.5500,"loc":"İznik Gölü","fish":["Sazan","Levrek","Sudak"],"rod":"Feeder","bait":"Pellet, mısır","note":"İznik gölü. Sazan sezonu çok iyi.","heat":4,"type":"göl","hot":False,"source":"Demo"},
    {"id":"fb16","lat":40.9780,"lng":27.5150,"loc":"Tekirdağ Sahili","fish":["Lüfer","Palamut","Kolyoz"],"rod":"Surf","bait":"Çoklu iğne takımı","note":"Tekirdağ sahilinde palamut akını var.","heat":5,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"fb17","lat":40.6100,"lng":27.1120,"loc":"Şarköy","fish":["Çipura","Levrek","Barbun"],"rod":"LRF","bait":"Berkley Gulp, micro","note":"Şarköy açıkları. Çipura ve barbun aktif.","heat":4,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"fb18","lat":41.1800,"lng":26.4000,"loc":"Meriç Nehri","fish":["Sazan","Yayın","Turna"],"rod":"Feeder","bait":"Boilie, canlı balık","note":"Meriç nehri. Yayın ve sazan sezonu açık.","heat":4,"type":"nehir","hot":True,"source":"Demo"},
    {"id":"fb19","lat":40.3800,"lng":27.8200,"loc":"Erdek Körfezi","fish":["Çipura","Karagöz","Sargoz"],"rod":"LRF","bait":"Micro jig, silikon","note":"Erdek körfezi. Marmara'nın en iyi çipura noktası.","heat":5,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"fb20","lat":40.6960,"lng":30.2690,"loc":"Sapanca Gölü","fish":["Alabalık","Sazan","Yayın"],"rod":"Spin","bait":"Rapala wobbler, solucan","note":"Sapanca. Sabah 6-9 alabalık mükemmel.","heat":5,"type":"göl","hot":True,"source":"Demo"},
]

def main():
    print("=" * 65)
    print(f"🎣 Balık Radarı Scraper v3 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("   Galata Köprüsü + Eminönü + Karaköy + Tüm Marmara")
    print("=" * 65)

    existing = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f).get("reports", [])
            print(f"📂 Mevcut: {len(existing)} rapor")
        except Exception as e:
            print(f"⚠ Yükleme hatası: {e}")

    new_reports = []
    new_reports += scrape_google_news_general()
    new_reports += scrape_google_news_locations()
    new_reports += scrape_news_rss()
    new_reports += scrape_fishing_sites()
    new_reports += scrape_telegram()
    new_reports += scrape_instagram()
    new_reports += scrape_facebook()

    print(f"\n📊 Toplam yeni: {len(new_reports)}")

    now_iso = datetime.now(timezone.utc).isoformat()
    for r in new_reports:
        if "timestamp" not in r:
            r["timestamp"] = now_iso
        r["time"] = time_ago(r["timestamp"])

    if len(new_reports) < 5:
        print("⚠ Yeterli veri yok, demo veri kullanılıyor...")
        for r in FALLBACK:
            r["timestamp"] = now_iso
            r["time"] = "Az önce"
        new_reports = FALLBACK + new_reports

    all_map = {r["id"]: r for r in existing}
    added = 0
    for r in new_reports:
        if r["id"] not in all_map:
            all_map[r["id"]] = r
            added += 1

    sorted_reports = sorted(
        all_map.values(),
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )[:MAX_REPORTS]

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
    print("=" * 65)

if __name__ == "__main__":
    main()
