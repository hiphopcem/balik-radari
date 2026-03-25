#!/usr/bin/env python3
"""
Sihirli Zoka Radar - Scraper v13
Kaynaklar: Gemini AI (15 sorgu), Google News (40+), Balıkçı Forumları, YouTube, Twitter/X
Rapor limiti: Sınırsız — sadece son 12 saat
"""

import os, json, time, hashlib, random, requests, re
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

OUTPUT_FILE   = "data/reports.json"
MAX_AGE_HOURS = 12   # Sadece son 12 saat — eski raporlar balıkçıya yaramaz
GEMINI_KEY    = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL    = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9",
}

SOURCE_NAME = "Sihirli Zoka Radar"

YOK_WORDS = ["yok", "bilgi yok", "bilgi bulunamadı", "belirsiz", "belirtilmemiş",
             "bulunamadı", "mevcut değil", "-", "—", "yok.", "yok,", "tutulmadı",
             "aktif değil", "sessiz", "boş"]

def normalize(s):
    s = str(s).lower()
    for k, v in {"ı":"i","ğ":"g","ü":"u","ş":"s","ö":"o","ç":"c",
                 "İ":"i","Ğ":"g","Ü":"u","Ş":"s","Ö":"o","Ç":"c"}.items():
        s = s.replace(k, v)
    return s

def clean_gemini(s):
    s = re.sub(r'\*+', '', s)
    s = re.sub(r'\([^)]*\)', '', s)
    return s.strip()

LOCATIONS = {
    # İSTANBUL
    "galata köprüsü avrupa": (41.01600, 28.97150),
    "galata köprüsü asya":   (41.01640, 28.97700),
    "galata köprüsü":        (41.01620, 28.97420),
    "eminönü":               (41.01650, 28.97300),
    "karaköy":               (41.02250, 28.97400),
    "sarayburnu":            (41.01330, 28.98170),
    "sirkeci":               (41.01300, 28.97800),
    "haliç":                 (41.03200, 28.95000),
    "fener":                 (41.03100, 28.95100),
    "ayvansaray":            (41.03700, 28.94300),
    "eyüp":                  (41.04900, 28.93300),
    "yenikapı sahili":       (41.00500, 28.94900),
    "yenikapı":              (41.00500, 28.94900),
    "kumkapı":               (41.00400, 28.96400),
    "yedikule":              (40.99800, 28.92700),
    "florya":                (40.97130, 28.79860),
    "yeşilköy":              (40.97280, 28.81660),
    "bakırköy":              (40.97920, 28.87010),
    "avcılar sahili":        (40.97930, 28.72190),
    "avcılar":               (40.97930, 28.72190),
    "büyükçekmece gölü":     (41.06000, 28.59000),
    "büyükçekmece":          (41.01970, 28.57730),
    "küçükçekmece gölü":     (41.02000, 28.76000),
    "küçükçekmece":          (41.01300, 28.77670),
    "silivri":               (41.07260, 28.24840),
    "kilyos":                (41.24970, 29.01570),
    "riva":                  (41.18500, 29.31000),
    "şile":                  (41.17780, 29.61030),
    "ağva":                  (41.09800, 29.99940),
    "garipçe":               (41.21000, 29.08000),
    "rumeli feneri":         (41.22500, 29.10750),
    "rumeli kavağı":         (41.19870, 29.06220),
    "büyükdere":             (41.14800, 29.05670),
    "sarıyer":               (41.16650, 29.05300),
    "tarabya":               (41.12680, 29.05690),
    "yeniköy":               (41.11100, 29.05780),
    "bebek":                 (41.07850, 29.04360),
    "rumeli hisarı":         (41.08500, 29.05400),
    "arnavutköy":            (41.06720, 29.03680),
    "ortaköy":               (41.05330, 29.02690),
    "beşiktaş":              (41.04300, 29.00600),
    "kabataş":               (41.03470, 29.00450),
    "anadolu feneri":        (41.21940, 29.15900),
    "anadolu kavağı":        (41.19300, 29.08200),
    "poyrazköy":             (41.20800, 29.13300),
    "beykoz":                (41.12180, 29.10140),
    "paşabahçe":             (41.13830, 29.09300),
    "kanlıca":               (41.10000, 29.08200),
    "anadolu hisarı":        (41.08330, 29.07360),
    "çengelköy":             (41.06200, 29.05900),
    "üsküdar":               (41.02270, 29.01510),
    "kadıköy":               (40.99020, 29.02320),
    "moda":                  (40.98400, 29.02800),
    "fenerbahçe":            (40.96800, 29.05400),
    "bostancı":              (40.96070, 29.09000),
    "maltepe":               (40.93410, 29.13500),
    "kartal":                (40.90750, 29.18580),
    "pendik":                (40.87620, 29.23300),
    "tuzla":                 (40.81480, 29.29600),
    "gebze":                 (40.80240, 29.43000),
    "büyükada":              (40.87170, 29.12400),
    "heybeliada":            (40.88300, 29.09400),
    "burgazada":             (40.87700, 29.06400),
    "kınalıada":             (40.90000, 29.03100),
    "adalar çevresi":        (40.87170, 29.10920),
    "adalar":                (40.87170, 29.10920),
    "istanbul boğazı":       (41.08000, 29.05000),
    "boğaz girişi":          (41.08000, 29.05000),
    "boğaziçi":              (41.08000, 29.05000),
    "boğaz":                 (41.08000, 29.05000),
    "istanbul":              (41.00820, 28.97840),
    # KOCAELİ
    "izmit körfezi":         (40.74000, 29.85000),
    "karamürsel":            (40.69440, 29.60750),
    "gölcük":                (40.65220, 29.83040),
    "hereke":                (40.79300, 29.62300),
    "diliskelesi":           (40.77500, 29.55800),
    "darıca":                (40.76600, 29.37400),
    "izmit":                 (40.76540, 29.94080),
    "kocaeli":               (40.76540, 29.94080),
    # YALOVA
    "çınarcık":              (40.64150, 29.12250),
    "armutlu":               (40.52780, 28.83200),
    "yalova":                (40.65490, 29.27470),
    # BURSA
    "uluabat gölü":          (40.16680, 28.62000),
    "iznik gölü":            (40.43300, 29.55000),
    "iznik":                 (40.42700, 29.72000),
    "gemlik":                (40.43150, 29.16250),
    "mudanya":               (40.37660, 28.88240),
    "orhangazi":             (40.49200, 29.31100),
    "bursa":                 (40.18260, 29.06650),
    # TEKİRDAĞ
    "marmara ereğlisi":      (40.96800, 27.95900),
    "şarköy":                (40.61210, 27.11030),
    "mürefte":               (40.67400, 27.25600),
    "hoşköy":                (40.74400, 27.17300),
    "tekirdağ":              (40.97810, 27.51170),
    "barbaros":              (40.82000, 27.45000),
    "saros körfezi":         (40.55000, 26.60000),
    "erikli":                (40.62000, 26.75000),
    # EDİRNE
    "meriç nehri":           (41.18000, 26.40000),
    "tunca nehri":           (41.70000, 26.55000),
    "ergene nehri":          (41.62000, 26.72000),
    "uzunköprü":             (41.26900, 26.68950),
    "enez":                  (40.72820, 26.08110),
    "keşan":                 (40.85600, 26.63950),
    "edirne":                (41.67710, 26.55570),
    "ipsala":                (40.91790, 26.38450),
    "enez sahili":           (40.72500, 26.09000),
    "gala gölü":             (40.79000, 26.18000),
    # ÇANAKKALE
    "çanakkale boğazı":      (40.15000, 26.40000),
    "çanakkale":             (40.15460, 26.40860),
    "gelibolu":              (40.41660, 26.67580),
    "lapseki":               (40.34600, 26.68500),
    "eceabat":               (40.18600, 26.35700),
    "kilitbahir":            (40.14500, 26.38600),
    "kepez":                 (40.09000, 26.39000),
    "ayvacık":               (39.59700, 26.40600),
    "küçükkuyu":             (39.54600, 26.61700),
    "assos":                 (39.48900, 26.33700),
    "babakale":              (39.48000, 26.05000),
    "geyikli":               (39.84000, 26.16000),
    "ezine":                 (39.78600, 26.34200),
    "bozcaada":              (39.83200, 26.06400),
    "gökçeada":              (40.17800, 25.90000),
    "tavşan adaları":        (39.95000, 26.05000),
    "biga":                  (40.22900, 27.24200),
    "karabiga":              (40.38900, 27.30600),
    # BALIKESİR
    "manyas gölü":           (40.20000, 27.97000),
    "marmara adası":         (40.60000, 27.57900),
    "avşa adası":            (40.51940, 27.59170),
    "ekinlik adası":         (40.54700, 27.53500),
    "erdek":                 (40.39750, 27.79580),
    "bandırma":              (40.35000, 27.97700),
    "gönen":                 (40.10060, 27.65020),
    "edincik":               (40.34640, 27.87200),
    "ayvalık":               (39.31760, 26.69630),
    "alibey adası":          (39.34000, 26.65000),
    "cunda adası":           (39.34000, 26.65000),
    "burhaniye":             (39.50130, 26.97650),
    "ören":                  (39.47000, 27.04000),
    "edremit körfezi":       (39.48000, 26.80000),
    "edremit":               (39.59430, 27.02380),
    "akçay":                 (39.57000, 26.92000),
    "altınoluk":             (39.56000, 26.74000),
    "gömeç":                 (39.45600, 26.84000),
    "balıkesir":             (39.64840, 27.88260),
    # SAPANCA
    "sapanca gölü":          (40.72000, 30.20000),
    "sapanca":               (40.69320, 30.27050),
    # MARMARA & EGE
    "marmara denizi":        (40.65000, 27.90000),
    "marmara":               (40.65000, 27.90000),
    "ege denizi":            (39.50000, 25.50000),
    "kuzey ege":             (40.00000, 26.00000),
}

VALID_REGIONS = [
    "istanbul","boğaz","boğaziçi","haliç","galata","eminönü","karaköy",
    "sarıyer","beykoz","bostancı","kadıköy","büyükçekmece","küçükçekmece",
    "silivri","şile","kilyos","ağva","adalar","büyükada","sarayburnu",
    "rumeli","bebek","tarabya","büyükdere","paşabahçe","anadolu",
    "beşiktaş","ortaköy","arnavutköy","kabataş","üsküdar","çengelköy",
    "kanlıca","pendik","kartal","maltepe","tuzla","heybeliada","burgazada",
    "kınalıada","florya","yeşilköy","bakırköy","avcılar","sirkeci","fener",
    "ayvansaray","eyüp","yenikapı","kumkapı","yedikule","diliskelesi",
    "garipçe","poyrazköy","fenerbahçe","moda","riva","gebze","darıca",
    "kocaeli","izmit","karamürsel","gölcük","hereke",
    "yalova","çınarcık","armutlu",
    "bursa","gemlik","mudanya","iznik","uluabat","orhangazi",
    "tekirdağ","şarköy","mürefte","hoşköy","marmara ereğlisi","barbaros",
    "saros","erikli",
    "edirne","meriç","ergene","tunca","uzunköprü","enez","keşan","ipsala","gala",
    "çanakkale","gelibolu","lapseki","eceabat","kilitbahir","kepez",
    "ayvacık","küçükkuyu","assos","babakale","geyikli","ezine",
    "bozcaada","gökçeada","tavşan","biga","karabiga",
    "balıkesir","erdek","bandırma","manyas","marmara adası","avşa",
    "ekinlik","gönen","edincik","ayvalık","alibey","cunda","burhaniye",
    "ören","edremit","akçay","altınoluk","gömeç",
    "sapanca","marmara","ege",
]

FISHING_WORDS = [
    "balık tut","olta","lüfer","palamut","hamsi","sazan","levrek","çipura",
    "kefal","istavrit","kolyoz","barbun","kalkan","alabalık","yayın",
    "sudak","turna","karagöz","spin","lrf","surf","feeder","jigging",
    "balıkçı","avlandı","tutuldu","tuttu","oltaya","mepps","rapala",
    "kaşık","silikon","jig","wobbler","popper","fishing","av raporu","balık avı",
    "çinekop","torik","palamut girişi","lüfer girişi","kolyoz sürüsü",
    "trolling","bolentino","zıpkın","fly fishing","sahil oltası",
]

NOISE_WORDS = [
    "balık fiyat","fabrika","teknesi battı","toplu balık ölü",
    "su kirliliği","deprem","yangın","trafik","seçim","ekonomi",
    "döviz","borsa","futbol","müzik","dizi","film","magazin",
    "balık restoranı","balık market","ton balığı konserve",
]

FISH_KW = [
    "sazan","levrek","çipura","lüfer","palamut","hamsi","istavrit","kalkan",
    "barbun","kefal","alabalık","yayın","sudak","turna","karagöz","sargoz",
    "kolyoz","uskumru","orkinos","mercan","isparoz","kızılkanat","tekir",
    "izmarit","çinekop","torik","tirsi","sardalya","minekop","mezgit",
    "lahos","grida","fangri","sinarit","lagos","dil balığı","melanur",
    "akya","lüfer","palamut","karagöz",
]

ROD_MAP = {
    "Spin":["spin","spinning","mepps","kastmaster","kaşık","lure","rapala","wobbler","popper","crankbait"],
    "LRF":["lrf","light rock","micro","ajing","finesse","gulp","berkley"],
    "Surf":["surf","surfcasting","sahil oltası","uzak mesafe","plumb"],
    "Feeder":["feeder","method","pellet","boilie","karpçılık"],
    "Fly":["sinek olta","fly fishing","yapay sinek","elk hair","nymph"],
    "Jigging":["jigging","jig","silikon","vertical","dikey","twister"],
    "Trolling":["trolling","trol","tekneden"],
    "Bolentino":["bolentino","dip olta","paternos"],
    "Zıpkın":["zıpkın","dalış","spearfishing"],
    "Olta":["olta","iğne","misina","el oltası"],
}

BAIT_KW = [
    "mepps","rapala","kastmaster","kaşık","solucan","ekmek","mısır",
    "boilie","pellet","gulp","micro jig","silikon","twister","wobbler",
    "popper","jig","olta balığı","canlı balık","canlı yem",
    "deniz kurdu","kalamar","midye","karides","hamsi yemi",
]

# ── ALARM KELİMELERİ — yoğun balık aktivitesini işaret eder ──────
ALARM_L3 = [  # Seviye 3 — ACİL ALARM (kırmızı, hızlı yanıp söner)
    "kaynıyor","patladı","coşmuş","çıldırmış","manyak balık","efsane balık",
    "deli gibi balık","canavar gibi","ortalık yıkılıyor","av kopuyor",
    "su resmen kaynıyor","balık resmen akın","her yer kıpır","tut tut bitmiyor",
    "çek çek bitmiyor","aklın durur","yok böyle","böyle gün zor gelir",
    "tam patlak","ortalık yanıyor","sürü girmiş","sürü oturmuş",
    "akın etmiş","kıyıdan geçilmiyor","peş peşe","arka arkaya",
    "fışkırıyor","taşmış","fena açmış","deli gibi alıyor",
]
ALARM_L2 = [  # Seviye 2 — YÜKSEK AKTİVİTE (turuncu, yavaş yanıp söner)
    "çok iyi yapıyor","güzel yapıyor","iyi yapıyor","bereketli","verimli",
    "aktif","hareketli","canlı","sürü var","sürü geçmiş","geçiş var",
    "akın var","kıyıladı","yüzeye çıktı","basıyor","sardı","çöktü",
    "girdi","toplandı","vuruyor","sert vuruyor","yapıştırıyor",
    "biniyor","yeme biniyor","sahteye biniyor","at çekte","seri geliyor",
    "takır takır","çatır çatır","kova doluyor","sepet doluyor",
    "boş dönmüyor","gelen alıyor","oltayı atan alıyor",
]
ALARM_L1 = [  # Seviye 1 — NORMAL AKTİF (sarı, statik)
    "balık var","av iyi","balık alıyor","iyi alıyor","güzel alıyor",
    "tutuldu","tuttu","avlandı","çalışıyor","verdi","av veriyor",
    "fena değil","lumanda var","mendirekte var","taşlıkta var",
]

def calc_alarm(text):
    """Metinden alarm seviyesi hesapla: 0=normal, 1=aktif, 2=yüksek, 3=alarm"""
    tn = normalize(text)
    for w in ALARM_L3:
        if normalize(w) in tn: return 3
    for w in ALARM_L2:
        if normalize(w) in tn: return 2
    for w in ALARM_L1:
        if normalize(w) in tn: return 1
    return 0

def safe_get(url, timeout=20):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        return r
    except Exception as e:
        print(f"  ⚠ {url[:60]}: {e}")
        return None

def make_id(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:14]

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def parse_date(date_str):
    if not date_str: return None
    for fmt in ["%a, %d %b %Y %H:%M:%S %z","%a, %d %b %Y %H:%M:%S %Z","%Y-%m-%dT%H:%M:%S%z"]:
        try: return datetime.strptime(date_str.strip(), fmt)
        except: continue
    return None

def is_recent(date_str, max_hours=MAX_AGE_HOURS):
    dt = parse_date(date_str)
    if not dt: return True
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
    return (now - dt).total_seconds() < max_hours * 3600

def time_ago_str(dt_str):
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z","+00:00"))
        diff = int((datetime.now(timezone.utc)-dt).total_seconds())
        if diff < 60: return "Az önce"
        if diff < 3600: return f"{diff//60}dk önce"
        if diff < 86400: return f"{diff//3600}sa önce"
        return f"{diff//86400}g önce"
    except: return "Bilinmiyor"

def is_valid(text):
    tn = normalize(text)
    if any(normalize(n) in tn for n in NOISE_WORDS): return False
    if not any(normalize(f) in tn for f in FISHING_WORDS): return False
    if not any(normalize(r) in tn for r in VALID_REGIONS): return False
    return True

def extract_fish(text):
    tn = normalize(text)
    found = list(dict.fromkeys([f.title() for f in FISH_KW if normalize(f) in tn]))
    return found[:5] if found else ["Belirtilmemiş"]

def extract_rod(text):
    tn = normalize(text)
    rods = []
    for rod, kws in ROD_MAP.items():
        if any(normalize(kw) in tn for kw in kws): rods.append(rod)
    return ", ".join(rods[:2]) if rods else ""

def extract_bait(text):
    tn = normalize(text)
    found = [b.title() for b in BAIT_KW if normalize(b) in tn]
    return ", ".join(found[:3])

def find_location(text):
    text = clean_gemini(text)
    tn = normalize(text)
    best, best_coords, best_len = None, None, 0
    for name, coords in LOCATIONS.items():
        nn = normalize(name)
        if nn in tn and len(name) > best_len:
            best, best_coords, best_len = name, coords, len(name)
    return best, best_coords

def classify_type(text, loc):
    tn = normalize(text + " " + (loc or ""))
    if any(w in tn for w in ["nehir","irmak","dere","meric","ergene","tunca"]): return "nehir"
    if any(w in tn for w in ["gol","golu"]): return "göl"
    return "deniz"

def build_report(title, body, source, url="", hint="", pub_date=None):
    if pub_date and not is_recent(pub_date): return None
    text = " ".join([title, body, hint])
    if not is_valid(text): return None
    fish = extract_fish(text)
    if fish == ["Belirtilmemiş"]: return None
    loc, coords = find_location(text)
    if not coords and hint: loc, coords = find_location(hint)
    if not coords: return None
    if pub_date:
        dt = parse_date(pub_date)
        ts = dt.astimezone(timezone.utc).isoformat() if dt else now_iso()
    else:
        ts = now_iso()
    lat = round(coords[0] + random.uniform(-0.002, 0.002), 6)
    lng = round(coords[1] + random.uniform(-0.002, 0.002), 6)
    alarm = calc_alarm(text)
    return {
        "id":        make_id(title+(loc or "")),
        "lat":       lat, "lng": lng,
        "loc":       loc.title(),
        "fish":      fish,
        "rod":       extract_rod(text),
        "bait":      extract_bait(text),
        "note":      title[:200],
        "heat":      min(5, len(fish)+1),
        "type":      classify_type(text, loc),
        "time":      time_ago_str(ts),
        "timestamp": ts,
        "source":    SOURCE_NAME,
        "url":       url,
        "hot":       len(fish) >= 2,
        "alarm":     alarm,
    }

def ask_gemini(prompt):
    if not GEMINI_KEY: return ""
    try:
        url = f"{GEMINI_URL}?key={GEMINI_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 4096},
        }
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"  ⚠ Gemini: {e}")
        return ""

def parse_gemini_lines(response, source_label=""):
    """Gemini yanıtından LOKASYON satırlarını parse et"""
    results = []
    lines = [l.strip() for l in response.split("\n") if "LOKASYON:" in l and "BALIK:" in l]
    for line in lines:
        try:
            parts = {}
            for p in line.split("|"):
                if ":" in p:
                    k, v = p.split(":", 1)
                    parts[k.strip()] = v.strip()
            loc_hint = clean_gemini(parts.get("LOKASYON","")).strip()
            fish_str = clean_gemini(parts.get("BALIK","")).strip()
            rod_str  = clean_gemini(parts.get("OLTA","")).strip()
            bait_str = clean_gemini(parts.get("YEM","")).strip()
            note_str = clean_gemini(parts.get("NOT","")).strip()
            if not loc_hint or not fish_str: continue
            if normalize(fish_str) in [normalize(w) for w in YOK_WORDS]:
                continue
            alarm_str = clean_gemini(parts.get("ALARM","")).strip()
            full_text = f"{loc_hint} {fish_str} {rod_str} {bait_str} {note_str} {alarm_str}"
            loc, coords = find_location(full_text)
            if not coords: loc, coords = find_location(loc_hint)
            if not coords: continue
            if not any(normalize(r) in normalize(loc_hint) for r in VALID_REGIONS): continue
            fish = [f.strip().title() for f in fish_str.split(",") if f.strip()]
            if not fish: continue
            # Alarm skoru — hem Gemini'nin verdiği hem de metinden hesaplanan
            alarm = calc_alarm(full_text)
            if alarm_str:
                try:
                    a = int(alarm_str[0])
                    if a in [1,2,3]: alarm = max(alarm, a)
                except: pass
            ts = now_iso()
            lat = round(coords[0] + random.uniform(-0.003, 0.003), 6)
            lng = round(coords[1] + random.uniform(-0.003, 0.003), 6)
            results.append({
                "id":        make_id(line+source_label),
                "lat": lat, "lng": lng,
                "loc":       loc.title(),
                "fish":      fish[:5],
                "rod":       rod_str or extract_rod(full_text),
                "bait":      bait_str or extract_bait(full_text),
                "note":      note_str[:200] if note_str else f"{loc_hint} — {fish_str}",
                "heat":      min(5, len(fish)+1),
                "type":      classify_type(full_text, loc),
                "time":      "Az önce",
                "timestamp": ts,
                "source":    SOURCE_NAME,
                "url":       "",
                "hot":       len(fish) >= 2,
                "alarm":     alarm,
            })
            print(f"    ✓ {loc_hint} → {fish_str}")
        except Exception as e:
            continue
    return results

FORMAT = """LOKASYON: [tam yer adı] | BALIK: [balık türleri virgülle] | OLTA: [olta türü] | YEM: [yem] | NOT: [kısa profesyonel yorum] | ALARM: [0/1/2/3]

ALARM seviyeleri:
0 = Normal (balık var ama sakin)
1 = Aktif (balık alıyor, iyi gidiyor)
2 = Yüksek (çok aktif, sürü var, bereketli)
3 = ACİL (patlak gün, kaynıyor, efsane aktivite)

Örnek:
LOKASYON: Galata Köprüsü | BALIK: Lüfer, Kolyoz | OLTA: Olta | YEM: Hamsi | NOT: Akşam saatlerinde yoğun tutulma, sürü kıyıya yanaşmış | ALARM: 2
LOKASYON: Bozcaada | BALIK: Çipura, Levrek, Sargoz | OLTA: LRF | YEM: Micro jig | NOT: Berrak suda aktif | ALARM: 1
LOKASYON: Sarıyer | BALIK: Palamut, Lüfer, Torik | OLTA: Trolling | YEM: Rapala | NOT: Sürü patladı, her atışta vuruş var, efsane gün | ALARM: 3"""

def scrape_gemini():
    print("🤖 Gemini ile kapsamlı tarama (15 sorgu)...")
    today = datetime.now().strftime("%d %B %Y")
    now_hour = (datetime.now(timezone.utc).hour + 3) % 24
    time_str = f"saat {now_hour}:00 civarı"

    prompts = [
        # 1 - İstanbul Boğazı detaylı
        f"""Bugün {today} {time_str} İstanbul Boğazı'nda aktif balık tutma noktaları:
Galata Köprüsü, Eminönü, Karaköy, Sarayburnu, Kumkapı, Yenikapı, Haliç, Rumeli Hisarı,
Bebek, Ortaköy, Beşiktaş, Kabataş, Üsküdar, Çengelköy, Anadolu Hisarı.
Sadece aktif noktaları yaz. Markdown kullanma.
{FORMAT}""",

        # 2 - Boğaz kuzey
        f"""Bugün {today} {time_str} İstanbul Boğazı kuzey bölümünde aktif noktalar:
Sarıyer, Büyükdere, Tarabya, Yeniköy, Rumeli Kavağı, Rumeli Feneri, Garipçe,
Beykoz, Paşabahçe, Kanlıca, Anadolu Kavağı, Anadolu Feneri, Poyrazköy.
Sadece aktif noktaları yaz. Markdown kullanma.
{FORMAT}""",

        # 3 - İstanbul Anadolu ve adalar
        f"""Bugün {today} {time_str} İstanbul Anadolu sahili ve adalarda aktif noktalar:
Kadıköy, Moda, Fenerbahçe, Bostancı, Maltepe, Kartal, Pendik, Tuzla, Gebze,
Büyükada, Heybeliada, Burgazada, Kınalıada.
Sadece aktif noktaları yaz. Markdown kullanma.
{FORMAT}""",

        # 4 - İstanbul Avrupa sahili ve göller
        f"""Bugün {today} {time_str} İstanbul Avrupa sahili ve göllerde aktif noktalar:
Florya, Yeşilköy, Bakırköy, Avcılar, Küçükçekmece Gölü, Büyükçekmece Gölü,
Silivri, Kilyos, Şile, Riva, Ağva.
Sadece aktif noktaları yaz. Markdown kullanma.
{FORMAT}""",

        # 5 - Marmara denizi genel
        f"""Bugün {today} {time_str} Marmara Denizi'nde aktif balık noktaları:
Tekirdağ, Şarköy, Mürefte, Hoşköy, Marmara Ereğlisi, Barbaros,
Erdek, Bandırma, Marmara Adası, Avşa Adası, Ekinlik Adası, Edincik.
Sadece aktif noktaları yaz. Markdown kullanma.
{FORMAT}""",

        # 6 - Kocaeli ve Yalova
        f"""Bugün {today} {time_str} Kocaeli ve Yalova'da aktif balık noktaları:
İzmit Körfezi, Karamürsel, Gölcük, Hereke, Diliskelesi, Darıca, Gebze,
Çınarcık, Armutlu, Yalova.
Sadece aktif noktaları yaz. Markdown kullanma.
{FORMAT}""",

        # 7 - Bursa
        f"""Bugün {today} {time_str} Bursa bölgesinde aktif balık noktaları:
Gemlik, Mudanya, Orhangazi, İznik Gölü, Uluabat Gölü.
Sadece aktif noktaları yaz. Markdown kullanma.
{FORMAT}""",

        # 8 - Çanakkale Boğazı
        f"""Bugün {today} {time_str} Çanakkale Boğazı'nda aktif balık noktaları:
Gelibolu, Lapseki, Eceabat, Kilitbahir, Kepez, Çanakkale merkez.
Lüfer, palamut, kolyoz göçü var mı? Sadece aktif noktaları yaz. Markdown kullanma.
{FORMAT}""",

        # 9 - Kuzey Ege adalar
        f"""Bugün {today} {time_str} Kuzey Ege adaları ve kıyılarında aktif balık noktaları:
Bozcaada, Gökçeada, Tavşan Adaları, Babakale, Assos, Küçükkuyu, Ayvacık, Ezine.
Çipura, levrek, sargoz, lahos durumu? Sadece aktif noktaları yaz. Markdown kullanma.
{FORMAT}""",

        # 10 - Balıkesir Ege
        f"""Bugün {today} {time_str} Balıkesir Ege kıyılarında aktif balık noktaları:
Ayvalık, Cunda Adası, Alibey Adası, Burhaniye, Ören, Edremit Körfezi,
Akçay, Altınoluk, Gömeç.
Sadece aktif noktaları yaz. Markdown kullanma.
{FORMAT}""",

        # 11 - Edirne ve Saros
        f"""Bugün {today} {time_str} Edirne ve Saros bölgesinde aktif balık noktaları:
Meriç Nehri, Tunca Nehri, Ergene Nehri, Enez, Enez Sahili, Gala Gölü,
Saros Körfezi, Erikli, Keşan.
Sazan, yayın, çipura, levrek durumu? Sadece aktif noktaları yaz. Markdown kullanma.
{FORMAT}""",

        # 12 - Sapanca ve iç göller
        f"""Bugün {today} {time_str} Sapanca Gölü ve çevre noktalarda aktif balık durumu:
Sapanca Gölü, Sapanca, Manyas Gölü, İznik Gölü, Uluabat Gölü,
Büyükçekmece Gölü, Küçükçekmece Gölü, Gala Gölü.
Alabalık, sazan, yayın, sudak durumu? Sadece aktif noktaları yaz. Markdown kullanma.
{FORMAT}""",

        # 13 - Mevsimsel balık hareketleri
        f"""Bugün {today} {time_str} Marmara ve Kuzey Ege'de mevsimsel balık hareketleri:
Bu saatlerde hangi balıklar hangi bölgelerde aktif?
Lüfer, palamut, kolyoz, çipura, levrek, kefal, hamsi, istavrit, kalkan, barbun.
Spin, LRF, Surf, Trolling için en iyi noktalar? Markdown kullanma.
{FORMAT}""",

        # 14 - Teknik tavsiye + lokasyon
        f"""Sen deneyimli bir Türk balıkçısısın. Bugün {today} {time_str}:
Marmara ve Ege'de hangi tekniklerin işe yarayacağı noktaları söyle.
Özellikle LRF, Spin, Surf, Jigging için aktif noktalar.
Yem ve teknik tavsiyeleri de ekle. Markdown kullanma.
{FORMAT}""",

        # 15 - Son 12 saatte tutulan balıklar
        f"""Türkiye'de son 12 saat içinde sosyal medya, forum ve haberlerde
İstanbul, Marmara, Ege, Çanakkale bölgelerinde balık tutulduğuna dair paylaşımlar var mı?
Hangi lokasyonlarda ne tutuldu? Sadece son 12 saate ait bilgi ver.
Markdown kullanma.
{FORMAT}""",
    ]

    all_reports = []
    for i, prompt in enumerate(prompts):
        print(f"  Sorgu {i+1}/{len(prompts)}...")
        response = ask_gemini(prompt)
        if response:
            results = parse_gemini_lines(response, f"_g{i}")
            all_reports.extend(results)
            print(f"    → {len(results)} rapor")
        time.sleep(3)

    print(f"  ✓ Gemini toplam: {len(all_reports)} rapor")
    return all_reports

def scrape_google_news():
    print("📰 Google News taranıyor (40+ sorgu)...")

    # Her lokasyon için özel sorgular
    queries = [
        # İstanbul genel
        "galata köprüsü balık tutma bugün","eminönü karaköy balık avı",
        "istanbul boğazı lüfer palamut","sarıyer rumeli kavağı balık",
        "beykoz anadolu kavağı balık tutma","bostancı kadıköy balık avı",
        "büyükçekmece şile kilyos balık","istanbul balıkçılık raporu",
        "boğazda lüfer girişi","istanbul palamut sezonu",
        "boğaz kolyoz çinekop","istanbul spin lrf balık",
        # Marmara
        "tekirdağ şarköy balık tutma","marmara ereğlisi hoşköy balık",
        "erdek bandırma marmara adası balık","avşa adası balık avı",
        "marmara denizi lüfer palamut","saros körfezi çipura levrek",
        # Kocaeli Yalova Bursa
        "izmit körfezi kocaeli balık","karamürsel gölcük balık tutma",
        "yalova çınarcık balık avı","gemlik mudanya balık tutma",
        "iznik gölü sazan alabalık","uluabat gölü balık avı",
        # Çanakkale Ege
        "çanakkale boğazı balık tutma","gelibolu lapseki balık avı",
        "bozcaada çipura levrek","gökçeada balık avı",
        "küçükkuyu assos balık tutma","ayvalık cunda balık avı",
        "edremit körfezi balık tutma","altınoluk akçay balık",
        # Edirne
        "meriç nehri sazan yayın","enez saros balık avı",
        "edirne balıkçılık raporu",
        # Göller
        "sapanca gölü alabalık sazan","iznik gölü balık avı bugün",
        "büyükçekmece gölü sazan turna",
        # Teknik
        "istanbul lrf spin balık avı","marmara surf casting balık",
        "ege trolling jigging balık","çanakkale bolentino balık",
        # Genel güncel
        "türkiye balık avı raporu","marmara ege balık hareketleri",
        "lüfer palamut kolyoz nerede","çipura levrek aktif",
    ]

    results, seen = [], set()
    for q in queries:
        url = f"https://news.google.com/rss/search?q={quote_plus(q)}+when:1d&hl=tr&gl=TR&ceid=TR:tr"
        r = safe_get(url)
        if not r: time.sleep(0.5); continue
        try: soup = BeautifulSoup(r.content, "xml")
        except: soup = BeautifulSoup(r.content, "lxml-xml")
        fresh = 0
        for item in soup.find_all("item")[:8]:
            t = item.find("title")
            d = item.find("description")
            l = item.find("link")
            pub = item.find("pubDate")
            if not t: continue
            title = t.get_text(strip=True)
            if title in seen: continue
            seen.add(title)
            pub_date = pub.get_text(strip=True) if pub else None
            if pub_date and not is_recent(pub_date, MAX_AGE_HOURS): continue
            desc = d.get_text(strip=True) if d else ""
            link = l.get_text(strip=True) if l else ""
            rep = build_report(title, desc, SOURCE_NAME, link, q, pub_date)
            if rep: results.append(rep); fresh += 1
        if fresh > 0: print(f"  ✓ '{q[:40]}' → {fresh}")
        time.sleep(0.8)

    print(f"  ✓ Google News toplam: {len(results)} rapor")
    return results

def scrape_forums():
    print("🎣 Balıkçı forumları taranıyor...")
    results = []

    forums = [
        # Balıkçı forumları
        ("https://www.balıkçıyız.net/son-av-raporları", "Forum"),
        ("https://www.balıkçıyız.com/forum/av-raporlari", "Forum"),
        ("https://www.spinforum.net/forum/av-raporlari", "SpinForum"),
        ("https://www.lrfturkiye.com/forum", "LRF Türkiye"),
        ("https://www.karpcilar.com/forum/av-raporlari", "Karpçılar"),
    ]

    # Google ile forum aramalarını yap
    forum_queries = [
        "site:balikcilar.net av raporu istanbul",
        "site:spinforum.net istanbul boğaz",
        "balıkçı forum istanbul av raporu bugün",
        "balık av raporu forum marmara ege",
        "lrf spin istanbul boğaz av raporu forum",
    ]

    for q in forum_queries:
        url = f"https://news.google.com/rss/search?q={quote_plus(q)}+when:1d&hl=tr&gl=TR&ceid=TR:tr"
        r = safe_get(url)
        if not r: time.sleep(0.5); continue
        try: soup = BeautifulSoup(r.content, "xml")
        except: soup = BeautifulSoup(r.content, "lxml-xml")
        for item in soup.find_all("item")[:5]:
            t = item.find("title")
            d = item.find("description")
            l = item.find("link")
            pub = item.find("pubDate")
            if not t: continue
            title = t.get_text(strip=True)
            pub_date = pub.get_text(strip=True) if pub else None
            if pub_date and not is_recent(pub_date, MAX_AGE_HOURS): continue
            desc = d.get_text(strip=True) if d else ""
            link = l.get_text(strip=True) if l else ""
            rep = build_report(title, desc, SOURCE_NAME, link, q, pub_date)
            if rep: results.append(rep)
        time.sleep(0.8)

    print(f"  ✓ Forumlar toplam: {len(results)} rapor")
    return results

def scrape_youtube():
    print("📺 YouTube başlıkları taranıyor...")
    results = []

    yt_queries = [
        "istanbul balık avı bugün","boğaz lüfer palamut av",
        "marmara balık tutma","çanakkale balık avı",
        "bozcaada gökçeada balık","ayvalık edremit balık avı",
        "spin lrf istanbul","surf casting marmara",
        "sapanca gölü balık avı","şile kilyos balık",
    ]

    for q in yt_queries:
        # YouTube RSS ile ara
        url = f"https://news.google.com/rss/search?q={quote_plus(q+' youtube')}+when:1d&hl=tr&gl=TR&ceid=TR:tr"
        r = safe_get(url)
        if not r: time.sleep(0.5); continue
        try: soup = BeautifulSoup(r.content, "xml")
        except: soup = BeautifulSoup(r.content, "lxml-xml")
        for item in soup.find_all("item")[:5]:
            t = item.find("title")
            d = item.find("description")
            l = item.find("link")
            pub = item.find("pubDate")
            if not t: continue
            title = t.get_text(strip=True)
            pub_date = pub.get_text(strip=True) if pub else None
            if pub_date and not is_recent(pub_date, MAX_AGE_HOURS): continue
            # YouTube başlığından balık bilgisi çıkar
            if not any(normalize(f) in normalize(title) for f in FISH_KW+["balık","olta","lrf","spin","surf"]): continue
            desc = d.get_text(strip=True) if d else ""
            link = l.get_text(strip=True) if l else ""
            rep = build_report(title, desc, SOURCE_NAME, link, q, pub_date)
            if rep: results.append(rep)
        time.sleep(0.8)

    print(f"  ✓ YouTube toplam: {len(results)} rapor")
    return results

def scrape_twitter():
    print("🐦 Twitter/X arama...")
    results = []

    # Twitter/X public arama (Nitter üzerinden)
    nitter_instances = [
        "nitter.net",
        "nitter.privacydev.net",
        "nitter.poast.org",
    ]

    twitter_queries = [
        "istanbul boğaz lüfer","marmara palamut kolyoz",
        "galata köprüsü balık","çanakkale balık avı",
        "bozcaada çipura","lrf spin istanbul",
        "sapanca gölü alabalık","marmara balık tutma",
    ]

    for nitter in nitter_instances:
        for q in twitter_queries[:4]:  # Her instance için 4 sorgu
            url = f"https://{nitter}/search/rss?q={quote_plus(q)}&f=tweets"
            r = safe_get(url, timeout=10)
            if not r: continue
            try: soup = BeautifulSoup(r.content, "xml")
            except: soup = BeautifulSoup(r.content, "lxml-xml")
            for item in soup.find_all("item")[:5]:
                t = item.find("title")
                d = item.find("description")
                pub = item.find("pubDate")
                if not t: continue
                title = t.get_text(strip=True)[:200]
                pub_date = pub.get_text(strip=True) if pub else None
                if pub_date and not is_recent(pub_date, MAX_AGE_HOURS): continue
                desc = d.get_text(strip=True) if d else ""
                rep = build_report(title, desc, SOURCE_NAME, "", q, pub_date)
                if rep: results.append(rep)
            time.sleep(1)
        if results: break  # Bir instance çalıştı, yeter

    print(f"  ✓ Twitter/X toplam: {len(results)} rapor")
    return results

def scrape_rss():
    print("📡 RSS kaynakları taranıyor...")
    feeds = [
        ("https://www.hurriyet.com.tr/rss/gundem", SOURCE_NAME),
        ("https://www.sabah.com.tr/rss/yasam.xml", SOURCE_NAME),
        ("https://www.milliyet.com.tr/rss/rssNew/gundemRss.xml", SOURCE_NAME),
        ("https://www.aa.com.tr/tr/rss/default?cat=yasam", SOURCE_NAME),
        ("https://www.sozcu.com.tr/rss.xml", SOURCE_NAME),
        ("https://www.haberturk.com/rss", SOURCE_NAME),
    ]
    results = []
    for url, src in feeds:
        r = safe_get(url)
        if not r: continue
        try: soup = BeautifulSoup(r.content, "xml")
        except: soup = BeautifulSoup(r.content, "lxml-xml")
        for item in soup.find_all("item")[:20]:
            t = item.find("title")
            d = item.find("description")
            pub = item.find("pubDate")
            if not t: continue
            title = t.get_text(strip=True)
            desc = d.get_text(strip=True) if d else ""
            pub_date = pub.get_text(strip=True) if pub else None
            rep = build_report(title, desc, src, "", "", pub_date)
            if rep: results.append(rep)
        time.sleep(0.5)
    print(f"  ✓ RSS toplam: {len(results)} rapor")
    return results

def scrape_telegram():
    print("📲 Telegram taranıyor...")
    channels = [
        "balikcilar_istanbul","marmara_balik","bogaz_balik",
        "lufer_palamut","galata_koprusu_balik","spin_lrf_istanbul",
        "istanbul_fishing","turkiye_balik","marmara_fishing",
        "canakkale_balik","ege_balik","bozcaada_fishing",
    ]
    results = []
    for ch in channels:
        r = safe_get(f"https://t.me/s/{ch}", timeout=10)
        if not r: continue
        soup = BeautifulSoup(r.text, "html.parser")
        msgs = soup.select(".tgme_widget_message_text")
        for msg in msgs[:15]:
            text = msg.get_text(strip=True)
            if len(text) < 20: continue
            rep = build_report(text[:200], "", SOURCE_NAME)
            if rep: results.append(rep)
        time.sleep(1)
    print(f"  ✓ Telegram toplam: {len(results)} rapor")
    return results

def merge_locations(reports):
    """
    Aynı lokasyondaki raporları tek noktada birleştir.
    Gemini tüm raporları okuyup profesyonel özet yorum yazar.
    """
    # Lokasyona göre grupla
    groups = {}
    for r in reports:
        loc = r.get("loc","").strip().lower()
        if not loc: continue
        if loc not in groups:
            groups[loc] = []
        groups[loc].append(r)

    merged = []
    for loc_key, reps in groups.items():
        if not reps: continue

        # En yeni raporu temel al
        reps_sorted = sorted(reps, key=lambda x: x.get("timestamp",""), reverse=True)
        base = reps_sorted[0].copy()

        # Tüm balık türlerini birleştir
        all_fish = []
        for r in reps_sorted:
            for f in r.get("fish",[]):
                if f not in all_fish:
                    all_fish.append(f)
        base["fish"] = all_fish[:6]

        # En yüksek alarm seviyesini al
        base["alarm"] = max(r.get("alarm",0) for r in reps_sorted)
        base["hot"] = any(r.get("hot",False) for r in reps_sorted)
        base["heat"] = max(r.get("heat",0) for r in reps_sorted)

        # Tüm notları birleştir
        notes = []
        for r in reps_sorted:
            note = r.get("note","").strip()
            t = r.get("time","")
            if note and note not in notes:
                notes.append(f"[{t}] {note}")

        # Birden fazla rapor varsa Gemini ile özet yorum yaptır
        if len(reps_sorted) > 1 and GEMINI_KEY:
            summary = gemini_summarize(base["loc"], reps_sorted)
            if summary:
                base["note"] = summary
            else:
                base["note"] = " | ".join(notes[:3])
        else:
            base["note"] = notes[0] if notes else base.get("note","")

        # Tüm sub-raporları sakla (popup'ta detay için)
        base["reports"] = [
            {
                "time": r.get("time",""),
                "fish": r.get("fish",[]),
                "note": r.get("note",""),
                "rod":  r.get("rod",""),
                "bait": r.get("bait",""),
            }
            for r in reps_sorted[:5]  # max 5 detay
        ]
        base["report_count"] = len(reps_sorted)

        merged.append(base)

    return merged


def gemini_summarize(loc, reports):
    """Bir konumdaki birden fazla raporu Gemini ile özetlet"""
    if not GEMINI_KEY or len(reports) < 2:
        return None

    # Rapor özetlerini hazırla
    rep_lines = []
    for r in reports[:5]:
        t = r.get("time","")
        fish = ", ".join(r.get("fish",[]))
        note = r.get("note","")
        rod  = r.get("rod","")
        rep_lines.append(f"- {t}: {fish} tutuldu. {note} {rod}")

    prompt = f"""Sen deneyimli bir balıkçılık uzmanısın.
{loc} konumunda son 12 saatte şu raporlar geldi:

{chr(10).join(rep_lines)}

Bu raporları tek bir profesyonel özet yoruma dönüştür.
- Balık hareketlerini analiz et
- Trend varsa belirt (artıyor mu, azalıyor mu)
- En iyi zaman dilimini belirt
- Teknik tavsiye ver
- Maksimum 2 cümle, Türkçe, professional ton
- Sadece özeti yaz, başka hiçbir şey ekleme"""

    response = ask_gemini(prompt)
    return response.strip() if response else None


def main():
    print("="*65)
    print(f"🎣 Sihirli Zoka Radar v13 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   AI Tarama: {'✓' if GEMINI_KEY else '✗'} | Max yaş: {MAX_AGE_HOURS} saat")
    print("="*65)

    # Mevcut veriyi yükle
    existing = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE,"r",encoding="utf-8") as f:
                existing = json.load(f).get("reports",[])
            print(f"📂 Mevcut: {len(existing)} rapor")
        except Exception as e:
            print(f"⚠ {e}")

    # Son 12 saat dışındakileri temizle
    cutoff = datetime.now(timezone.utc) - timedelta(hours=MAX_AGE_HOURS)
    fresh = []
    for r in existing:
        try:
            if r.get("source","") == "Demo": continue
            ts = r.get("timestamp","")
            if not ts: continue
            dt = datetime.fromisoformat(ts.replace("Z","+00:00"))
            if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
            if dt > cutoff: fresh.append(r)
        except: pass

    print(f"🧹 Temizlik: {len(fresh)} rapor kaldı ({len(existing)-len(fresh)} silindi)")

    # Tüm kaynakları tara
    new_reports = []

    if GEMINI_KEY:
        new_reports += scrape_gemini()

    new_reports += scrape_google_news()
    new_reports += scrape_forums()
    new_reports += scrape_youtube()
    new_reports += scrape_twitter()
    new_reports += scrape_rss()
    new_reports += scrape_telegram()

    print(f"\n📊 Ham rapor: {len(new_reports)}")

    ts = now_iso()
    for r in new_reports:
        if "timestamp" not in r: r["timestamp"] = ts
        r["time"] = time_ago_str(r["timestamp"])

    # Birleştir — yinelenen ID'leri atla
    all_map = {r["id"]: r for r in fresh}
    added = 0
    for r in new_reports:
        if r["id"] not in all_map:
            all_map[r["id"]] = r
            added += 1

    all_reports = list(all_map.values())

    # ── KONUM BİRLEŞTİRME ────────────────────────────────────────
    # Aynı lokasyondaki raporları tek noktada birleştir
    print(f"\n🔀 Konum birleştirme...")
    merged = merge_locations(all_reports)
    print(f"   {len(all_reports)} rapor → {len(merged)} birleşik konum")

    # Son 12 saate göre sırala — en yeni başta
    sorted_reports = sorted(
        merged,
        key=lambda x: x.get("timestamp",""),
        reverse=True
    )

    print(f"\n✅ Tamamlandı!")
    print(f"   Yeni eklenen : {added}")
    print(f"   Toplam konum : {len(sorted_reports)}")

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE,"w",encoding="utf-8") as f:
        json.dump({
            "last_updated": ts,
            "total":        len(sorted_reports),
            "reports":      sorted_reports,
        }, f, ensure_ascii=False, indent=2)

    print("="*65)

if __name__ == "__main__":
    main()
