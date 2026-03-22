#!/usr/bin/env python3
"""
Türkiye Balık Radarı - Scraper v8
- Türkçe karakter toleranslı lokasyon eşleştirme
- Gemini 2.0 Flash ile akıllı tarama
- Sadece son 48 saat, bölge dışı haberler yok
- 7 il: İstanbul, Tekirdağ, Edirne, Kocaeli, Yalova, Bursa, Balıkesir
"""

import os, json, time, hashlib, random, requests
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

OUTPUT_FILE  = "data/reports.json"
MAX_REPORTS  = 200
MAX_AGE_HOURS = 48
GEMINI_KEY   = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL   = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9",
}

def normalize(s):
    s = str(s).lower()
    for k, v in {"ı":"i","ğ":"g","ü":"u","ş":"s","ö":"o","ç":"c",
                 "İ":"i","Ğ":"g","Ü":"u","Ş":"s","Ö":"o","Ç":"c"}.items():
        s = s.replace(k, v)
    return s

LOCATIONS = {
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
    "yenikapı":              (41.00500, 28.94900),
    "kumkapı":               (41.00400, 28.96400),
    "yedikule":              (40.99800, 28.92700),
    "florya":                (40.97130, 28.79860),
    "yeşilköy":              (40.97280, 28.81660),
    "bakırköy":              (40.97920, 28.87010),
    "avcılar":               (40.97930, 28.72190),
    "büyükçekmece gölü":     (41.06000, 28.59000),
    "büyükçekmece":          (41.01970, 28.57730),
    "küçükçekmece gölü":     (41.02000, 28.76000),
    "küçükçekmece":          (41.01300, 28.77670),
    "silivri":               (41.07260, 28.24840),
    "kilyos":                (41.24970, 29.01570),
    "şile":                  (41.17780, 29.61030),
    "ağva":                  (41.09800, 29.99940),
    "rumeli feneri":         (41.22500, 29.10750),
    "rumeli kavağı":         (41.19870, 29.06220),
    "büyükdere":             (41.14800, 29.05670),
    "sarıyer":               (41.16650, 29.05300),
    "tarabya":               (41.12680, 29.05690),
    "bebek":                 (41.07850, 29.04360),
    "arnavutköy":            (41.06720, 29.03680),
    "ortaköy":               (41.05330, 29.02690),
    "beşiktaş":              (41.04300, 29.00600),
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
    "adalar":                (40.87170, 29.10920),
    "istanbul boğazı":       (41.08000, 29.05000),"rumeli hisarı":         (41.08500, 29.05400), "garipçe":               (41.21000, 29.08000), "karadeniz boğaz":       (41.21000, 29.09000),
    "boğaziçi":              (41.08000, 29.05000),
    "istanbul":              (41.00820, 28.97840),
    "izmit körfezi":         (40.74000, 29.85000),
    "karamürsel":            (40.69440, 29.60750),
    "gölcük":                (40.65220, 29.83040),
    "hereke":                (40.79300, 29.62300),
    "diliskelesi":           (40.77500, 29.55800),
    "darıca":                (40.76600, 29.37400),
    "izmit":                 (40.76540, 29.94080),
    "kocaeli":               (40.76540, 29.94080),
    "çınarcık":              (40.64150, 29.12250),
    "armutlu":               (40.52780, 28.83200),
    "yalova":                (40.65490, 29.27470),
    "uluabat gölü":          (40.16680, 28.62000),
    "iznik gölü":            (40.43300, 29.55000),
    "iznik":                 (40.42700, 29.72000),
    "gemlik":                (40.43150, 29.16250),
    "mudanya":               (40.37660, 28.88240),
    "orhangazi":             (40.49200, 29.31100),
    "bursa":                 (40.18260, 29.06650),
    "marmara ereğlisi":      (40.96800, 27.95900),
    "şarköy":                (40.61210, 27.11030),
    "mürefte":               (40.67400, 27.25600),
    "hoşköy":                (40.74400, 27.17300),
    "tekirdağ":              (40.97810, 27.51170),
    "meriç nehri":           (41.18000, 26.40000),
    "tunca nehri":           (41.70000, 26.55000),
    "ergene nehri":          (41.62000, 26.72000),
    "uzunköprü":             (41.26900, 26.68950),
    "enez":                  (40.72820, 26.08110),
    "keşan":                 (40.85600, 26.63950),
    "edirne":                (41.67710, 26.55570),
    "manyas gölü":           (40.20000, 27.97000),
    "marmara adası":         (40.60000, 27.57900),
    "avşa adası":            (40.51940, 27.59170),
    "erdek":                 (40.39750, 27.79580),
    "bandırma":              (40.35000, 27.97700),
    "balıkesir":             (39.64840, 27.88260),
    "sapanca gölü":          (40.72000, 30.20000),
    "sapanca":               (40.69320, 30.27050),
    "marmara denizi":        (40.65000, 27.90000),
    "marmara":               (40.65000, 27.90000),
}

VALID_REGIONS = [
    "istanbul","tekirdağ","edirne","kocaeli","yalova","bursa","balıkesir",
    "sapanca","izmit","gebze","gemlik","mudanya","erdek","bandırma",
    "şarköy","marmara","boğaz","boğaziçi","haliç","galata","eminönü",
    "karaköy","sarıyer","beykoz","bostancı","kadıköy","büyükçekmece",
    "küçükçekmece","silivri","şile","kilyos","ağva","adalar","büyükada",
    "çınarcık","armutlu","iznik","uluabat","orhangazi",
    "meriç","ergene","tunca","uzunköprü","enez","keşan",
    "karamürsel","gölcük","hereke","darıca",
    "mürefte","hoşköy","marmara ereğlisi",
    "manyas","marmara adası","avşa",
    # Eksik olanlar eklendi
    "sarayburnu","rumeli","bebek","tarabya","büyükdere","paşabahçe",
    "anadolu","hisarı","kavağı","feneri","beşiktaş","ortaköy",
    "arnavutköy","kabataş","üsküdar","çengelköy","kanlıca",
    "pendik","kartal","maltepe","tuzla","heybeliada","burgazada",
    "kınalıada","florya","yeşilköy","bakırköy","avcılar","tekirdağ",
    "sirkeci","fener","ayvansaray","eyüp","yenikapı","kumkapı",
    "yedikule","gebze","darıca","diliskelesi","hereke",
]

FISHING_WORDS = [
    "balık tut","olta","lüfer","palamut","hamsi","sazan","levrek","çipura",
    "kefal","istavrit","kolyoz","barbun","kalkan","alabalık","yayın",
    "sudak","turna","karagöz","spin","lrf","surf","feeder","jigging",
    "balıkçı","avlandı","tutuldu","tuttu","oltaya","mepps","rapala",
    "kaşık","silikon","jig","wobbler","popper","fishing","av raporu","balık avı",
]

NOISE_WORDS = [
    "balık fiyat","fabrika","teknesi battı","toplu balık ölü",
    "su kirliliği","deprem","yangın","trafik","seçim","ekonomi",
    "döviz","borsa","futbol","müzik","dizi","film","magazin",
]

FISH_KW = [
    "sazan","levrek","çipura","lüfer","palamut","hamsi","istavrit","kalkan",
    "barbun","kefal","alabalık","yayın","sudak","turna","karagöz","sargoz",
    "kolyoz","uskumru","orkinos","mercan","isparoz","kızılkanat","tekir",
    "izmarit","çinekop","torik","tirsi","sardalya","minekop","mezgit",
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

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def parse_rss_date(date_str):
    if not date_str: return None
    for fmt in ["%a, %d %b %Y %H:%M:%S %z","%a, %d %b %Y %H:%M:%S %Z","%Y-%m-%dT%H:%M:%S%z"]:
        try: return datetime.strptime(date_str.strip(), fmt)
        except: continue
    return None

def is_recent(date_str, max_hours=MAX_AGE_HOURS):
    dt = parse_rss_date(date_str)
    if not dt: return True
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
    return (now - dt).total_seconds() < max_hours * 3600

def time_ago(dt_str):
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z","+00:00"))
        diff = int((datetime.now(timezone.utc)-dt).total_seconds())
        if diff < 60:    return "Az önce"
        if diff < 3600:  return f"{diff//60}dk önce"
        if diff < 86400: return f"{diff//3600}s önce"
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
    return list(dict.fromkeys([f.title() for f in FISH_KW if normalize(f) in tn]))[:4] or ["Belirtilmemiş"]

def extract_rod(text):
    tn = normalize(text)
    for rod, kws in ROD_MAP.items():
        if any(normalize(kw) in tn for kw in kws): return rod
    return ""

def extract_bait(text):
    tn = normalize(text)
    return ", ".join([b.title() for b in BAIT_KW if normalize(b) in tn][:2])

def find_location(text):
    # Markdown yıldızları ve parantez içindeki açıklamaları temizle
    import re
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'\([^)]*\)', '', text)
    text = text.strip()
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
        dt = parse_rss_date(pub_date)
        ts = dt.astimezone(timezone.utc).isoformat() if dt else now_iso()
    else:
        ts = now_iso()
    lat = round(coords[0] + random.uniform(-0.002, 0.002), 6)
    lng = round(coords[1] + random.uniform(-0.002, 0.002), 6)
    return {
        "id":        make_id(title+(loc or "")),
        "lat":       lat, "lng": lng,
        "loc":       loc.title(),
        "fish":      fish,
        "rod":       extract_rod(text),
        "bait":      extract_bait(text),
        "note":      title[:160],
        "heat":      min(5, len(fish)+1),
        "type":      classify_type(text, loc),
        "time":      time_ago(ts),
        "timestamp": ts,
        "source":    source,
        "url":       url,
        "hot":       len(fish) >= 2,
    }

def ask_gemini(prompt):
    if not GEMINI_KEY: return ""
    try:
        url = f"{GEMINI_URL}?key={GEMINI_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 4000},
        }
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"  ⚠ Gemini hatası: {e}")
        return ""

def scrape_with_gemini():
    print("🤖 Gemini ile akıllı tarama...")
    today = datetime.now().strftime("%d %B %Y")

    prompts = [
        f"""Sen bir balıkçılık asistanısın. Bugün {today} tarihinde İstanbul'da şu noktalarda balık tutuldu mu?
Galata Köprüsü, Eminönü, Karaköy, Sarayburnu, Haliç, İstanbul Boğazı, Sarıyer, Rumeli Kavağı, Rumeli Feneri, Büyükdere, Tarabya, Bebek, Beykoz, Anadolu Kavağı, Paşabahçe, Bostancı, Kadıköy, Büyükçekmece, Şile, Kilyos, Adalar.

İnternette Türkçe forumlarda, sosyal medyada, haberlerde bugünkü veya dünkü bilgileri bul.

Her bulgu için SADECE şu formatı kullan, başka hiçbir şey yazma:
LOKASYON: [tam yer adı] | BALIK: [balık türleri virgülle] | OLTA: [olta türü] | YEM: [yem adı] | NOT: [kısa bilgi]

Örnek:
LOKASYON: Galata Köprüsü | BALIK: Lüfer, Kolyoz | OLTA: Olta | YEM: Hamsi | NOT: Akşam saatlerinde yoğun tutulma

Her satır bir lokasyon olsun. Uydurma yapma, sadece gerçek bilgi yaz.""",

        f"""Sen bir balıkçılık asistanısın. Bugün {today} tarihinde şu bölgelerde balık durumu nedir?
Kocaeli (İzmit Körfezi, Karamürsel, Gölcük, Gebze, Darıca),
Yalova (Çınarcık, Armutlu),
Bursa (Gemlik, Mudanya, Orhangazi, İznik Gölü, Uluabat Gölü),
Tekirdağ (Şarköy, Mürefte, Marmara Ereğlisi, Hoşköy),
Balıkesir (Erdek, Bandırma, Marmara Adası, Avşa Adası, Manyas Gölü),
Edirne (Meriç Nehri, Ergene Nehri, Tunca Nehri),
Sapanca Gölü.

Her bulgu için SADECE şu formatı kullan:
LOKASYON: [tam yer adı] | BALIK: [türler] | OLTA: [olta] | YEM: [yem] | NOT: [bilgi]

Her lokasyon için ayrı satır. Uydurma yapma.""",

        f"""Sen bir balıkçılık asistanısın. Marmara Denizi ve İstanbul çevresinde şu an hangi balıklar aktif?
Lüfer, palamut, kolyoz, çipura, levrek, kefal, hamsi, istavrit, kalkan, barbun hangi noktalarda tutuluyor?
Spin, LRF, Surf, Feeder, Jigging teknikleri için güncel bilgi ver.

Her bulgu için SADECE şu formatı kullan:
LOKASYON: [tam yer adı] | BALIK: [türler] | OLTA: [olta] | YEM: [yem] | NOT: [bilgi]

Her satır ayrı lokasyon. Uydurma yapma.""",
    ]

    all_reports = []
    for i, prompt in enumerate(prompts):
        print(f"  Gemini sorgu {i+1}/{len(prompts)}...")
        response = ask_gemini(prompt)
        if not response:
            time.sleep(3); continue

        lines = [l.strip() for l in response.split("\n") if "LOKASYON:" in l and "BALIK:" in l]
        print(f"    → {len(lines)} rapor satırı bulundu")

        for line in lines:
            try:
                parts = {}
                for p in line.split("|"):
                    if ":" in p:
                        k, v = p.split(":", 1)
                        parts[k.strip()] = v.strip()

                loc_hint = parts.get("LOKASYON","").strip()
                fish_str = parts.get("BALIK","").strip()
                rod_str  = parts.get("OLTA","").strip()
                bait_str = parts.get("YEM","").strip()
                note_str = parts.get("NOT","").strip()

                if not loc_hint or not fish_str: continue

                full_text = f"{loc_hint} {fish_str} {rod_str} {bait_str} {note_str}"
                loc, coords = find_location(full_text)
                if not coords:
                    loc, coords = find_location(loc_hint)
                if not coords:
                    print(f"    ⚠ Lokasyon bulunamadı: {loc_hint}")
                    continue

                if not any(normalize(r) in normalize(loc_hint) for r in VALID_REGIONS):
                    print(f"    ⚠ Bölge dışı: {loc_hint}")
                    continue

                fish = [f.strip().title() for f in fish_str.split(",") if f.strip()]
                # "Yok" veya boş balık bilgisi olanları atla
if not fish_str or fish_str.strip().lower() in ["yok","bilgi yok","—","-","belirtilmemiş"]:
    continue
                if not fish: continue

                ts  = now_iso()
                lat = round(coords[0] + random.uniform(-0.002, 0.002), 6)
                lng = round(coords[1] + random.uniform(-0.002, 0.002), 6)

                all_reports.append({
                    "id":        make_id(line),
                    "lat":       lat, "lng": lng,
                    "loc":       loc.title(),
                    "fish":      fish[:4],
                    "rod":       rod_str or extract_rod(full_text),
                    "bait":      bait_str or extract_bait(full_text),
                    "note":      note_str[:160] if note_str else f"{loc_hint} bölgesi raporu.",
                    "heat":      min(5, len(fish)+1),
                    "type":      classify_type(full_text, loc),
                    "time":      "Az önce",
                    "timestamp": ts,
                    "source":    "Gemini AI",
                    "url":       "",
                    "hot":       len(fish) >= 2,
                })
                print(f"    ✓ {loc_hint} → {fish_str}")
            except Exception as e:
                print(f"    ⚠ Satır hatası: {e}")
                continue

        time.sleep(4)

    print(f"  ✓ Gemini: {len(all_reports)} rapor")
    return all_reports

def scrape_google_news():
    print("📰 Google News taranıyor...")
    queries = [
        "galata köprüsü balık","eminönü karaköy balık",
        "boğaz lüfer palamut","sarıyer beykoz balık",
        "bostancı kadıköy balık","büyükçekmece şile balık",
        "istanbul balıkçılık","kocaeli izmit körfezi balık",
        "yalova gemlik mudanya balık","tekirdağ şarköy balık",
        "edirne meriç balık","balıkesir erdek bandırma balık",
        "sapanca gölü balık","marmara denizi lüfer çipura",
    ]
    results, seen = [], set()
    for q in queries:
        url = f"https://news.google.com/rss/search?q={quote_plus(q)}+when:2d&hl=tr&gl=TR&ceid=TR:tr"
        r = safe_get(url)
        if not r: time.sleep(1); continue
        try:    soup = BeautifulSoup(r.content, "xml")
        except: soup = BeautifulSoup(r.content, "lxml-xml")
        fresh = 0
        for item in soup.find_all("item")[:10]:
            t   = item.find("title")
            d   = item.find("description")
            l   = item.find("link")
            pub = item.find("pubDate")
            if not t: continue
            title = t.get_text(strip=True)
            if title in seen: continue
            seen.add(title)
            pub_date = pub.get_text(strip=True) if pub else None
            if pub_date and not is_recent(pub_date, 48): continue
            desc = d.get_text(strip=True) if d else ""
            link = l.get_text(strip=True) if l else ""
            rep = build_report(title, desc, "Google Haberler", link, q, pub_date)
            if rep: results.append(rep); fresh += 1
        if fresh > 0: print(f"  ✓ '{q[:35]}' → {fresh} rapor")
        time.sleep(1.2)
    print(f"  ✓ Google News toplam: {len(results)} rapor")
    return results

def scrape_rss():
    print("📡 RSS feedler taranıyor...")
    feeds = [
        ("https://www.hurriyet.com.tr/rss/gundem",               "Hürriyet"),
        ("https://www.sabah.com.tr/rss/yasam.xml",               "Sabah"),
        ("https://www.milliyet.com.tr/rss/rssNew/gundemRss.xml", "Milliyet"),
        ("https://www.aa.com.tr/tr/rss/default?cat=yasam",       "AA"),
    ]
    results = []
    for url, src in feeds:
        r = safe_get(url)
        if not r: continue
        try:    soup = BeautifulSoup(r.content, "xml")
        except: soup = BeautifulSoup(r.content, "lxml-xml")
        for item in soup.find_all("item")[:30]:
            t   = item.find("title")
            d   = item.find("description")
            pub = item.find("pubDate")
            if not t: continue
            title    = t.get_text(strip=True)
            desc     = d.get_text(strip=True) if d else ""
            pub_date = pub.get_text(strip=True) if pub else None
            rep = build_report(title, desc, src, "", "", pub_date)
            if rep: results.append(rep)
        time.sleep(0.8)
    print(f"  ✓ RSS: {len(results)} rapor")
    return results

def scrape_telegram():
    print("📲 Telegram kanalları taranıyor...")
    channels = [
        ("balikcilar_istanbul",  "Telegram: Balıkçılar İstanbul"),
        ("marmara_balik",        "Telegram: Marmara Balık"),
        ("bogaz_balik",          "Telegram: Boğaz Balık"),
        ("lufer_palamut",        "Telegram: Lüfer Palamut"),
        ("galata_koprusu_balik", "Telegram: Galata Köprüsü"),
        ("spin_lrf_istanbul",    "Telegram: Spin LRF İstanbul"),
        ("istanbul_fishing",     "Telegram: İstanbul Fishing"),
    ]
    results = []
    for ch, src in channels:
        r = safe_get(f"https://t.me/s/{ch}")
        if not r: continue
        soup = BeautifulSoup(r.text, "html.parser")
        msgs = soup.select(".tgme_widget_message_text")
        found = 0
        for msg in msgs[:20]:
            text = msg.get_text(strip=True)
            if len(text) < 20: continue
            rep = build_report(text[:200], "", src)
            if rep: results.append(rep); found += 1
        if found > 0: print(f"  ✓ {ch}: {found} rapor")
        time.sleep(1.5)
    print(f"  ✓ Telegram toplam: {len(results)} rapor")
    return results

FALLBACK = [
    {"id":"f01","lat":41.01620,"lng":28.97420,"loc":"Galata Köprüsü","fish":["Lüfer","Kolyoz","Kefal"],"rod":"Olta","bait":"Çoklu iğne, hamsi","note":"Galata Köprüsü'nde yoğun balıkçı. Lüfer ve kolyoz tutuldu.","heat":5,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f02","lat":41.01650,"lng":28.97300,"loc":"Eminönü","fish":["Kefal","İstavrit"],"rod":"Olta","bait":"Ekmek, solucan","note":"Eminönü rıhtımında kefal aktif.","heat":4,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"f03","lat":41.02250,"lng":28.97400,"loc":"Karaköy","fish":["Lüfer","Levrek"],"rod":"Spin","bait":"Küçük kaşık","note":"Karaköy iskelesi. Sabah lüfer çıktı.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f04","lat":41.01330,"lng":28.98170,"loc":"Sarayburnu","fish":["Kolyoz","Palamut","Lüfer"],"rod":"Trolling","bait":"Çukur kaşık","note":"Sarayburnu açıklarında palamut akını.","heat":5,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f05","lat":41.19870,"lng":29.06220,"loc":"Rumeli Kavağı","fish":["Palamut","Lüfer","Torik"],"rod":"Trolling","bait":"CD-11 Rapala","note":"Rumeli Kavağı. Torik ve palamut aktif.","heat":5,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f06","lat":41.16650,"lng":29.05300,"loc":"Sarıyer","fish":["Lüfer","Palamut"],"rod":"Spin","bait":"Mepps No:3","note":"Sarıyer açıkları. Lüfer girişi başladı.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f07","lat":41.12180,"lng":29.10140,"loc":"Beykoz","fish":["Kalkan","Barbun"],"rod":"Olta","bait":"Deniz kurdu","note":"Beykoz sahili. Dip olta ile barbun bol.","heat":4,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"f08","lat":40.96070,"lng":29.09000,"loc":"Bostancı","fish":["Lüfer","İstavrit"],"rod":"Spin","bait":"Kaşık","note":"Bostancı sahili akşam lüfer girişi.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f09","lat":41.06000,"lng":28.59000,"loc":"Büyükçekmece Gölü","fish":["Sazan","Turna","Kefal"],"rod":"Feeder","bait":"Mısır, solucan","note":"Büyükçekmece Gölü sazan sezonu açık.","heat":5,"type":"göl","hot":True,"source":"Demo"},
    {"id":"f10","lat":40.74000,"lng":29.85000,"loc":"İzmit Körfezi","fish":["Çipura","Levrek"],"rod":"LRF","bait":"Gulp, micro jig","note":"İzmit körfezi çipura aktif.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f11","lat":40.65490,"lng":29.27470,"loc":"Yalova","fish":["Kefal","Levrek"],"rod":"Olta","bait":"Solucan","note":"Yalova iskelesi. Kefal bol.","heat":3,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"f12","lat":40.43150,"lng":29.16250,"loc":"Gemlik","fish":["Çipura","Levrek","Karagöz"],"rod":"LRF","bait":"Silikon, micro jig","note":"Gemlik limanı sabah çipura harika.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f13","lat":40.97810,"lng":27.51170,"loc":"Tekirdağ","fish":["Lüfer","Palamut","Kolyoz"],"rod":"Surf","bait":"Çoklu iğne takımı","note":"Tekirdağ sahili. Palamut geçişi var.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f14","lat":40.61210,"lng":27.11030,"loc":"Şarköy","fish":["Çipura","Levrek","Barbun"],"rod":"LRF","bait":"Berkley Gulp","note":"Şarköy açıkları çok aktif.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f15","lat":41.67710,"lng":26.55570,"loc":"Edirne - Meriç","fish":["Sazan","Yayın","Turna"],"rod":"Feeder","bait":"Boilie, canlı balık","note":"Meriç nehrinde yayın sezonu.","heat":4,"type":"nehir","hot":True,"source":"Demo"},
    {"id":"f16","lat":40.72000,"lng":30.20000,"loc":"Sapanca Gölü","fish":["Alabalık","Sazan","Yayın"],"rod":"Spin","bait":"Rapala, solucan","note":"Sapanca sabah alabalık harika.","heat":5,"type":"göl","hot":True,"source":"Demo"},
    {"id":"f17","lat":40.39750,"lng":27.79580,"loc":"Erdek","fish":["Çipura","Karagöz","Sargoz"],"rod":"LRF","bait":"Micro jig","note":"Erdek açıkları mükemmel.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f18","lat":40.43300,"lng":29.55000,"loc":"İznik Gölü","fish":["Sazan","Levrek","Sudak"],"rod":"Feeder","bait":"Pellet, mısır","note":"İznik gölü sazan sezonu açık.","heat":4,"type":"göl","hot":False,"source":"Demo"},
    {"id":"f19","lat":40.96800,"lng":27.95900,"loc":"Marmara Ereğlisi","fish":["Lüfer","Kolyoz"],"rod":"Surf","bait":"Çoklu iğne","note":"Marmara Ereğlisi sahili lüfer aktif.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f20","lat":40.60000,"lng":27.57900,"loc":"Marmara Adası","fish":["Çipura","Levrek","Sargoz"],"rod":"LRF","bait":"Micro jig","note":"Marmara adası çipura bol.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
]

def main():
    print("="*65)
    print(f"🎣 Balık Radarı v8 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Gemini: {'✓' if GEMINI_KEY else '✗'} | Max yaş: {MAX_AGE_HOURS} saat")
    print("="*65)

    existing = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE,"r",encoding="utf-8") as f:
                existing = json.load(f).get("reports",[])
            print(f"📂 Mevcut: {len(existing)} rapor")
        except Exception as e:
            print(f"⚠ {e}")

    # Demo verileri ve eski raporları temizle
    cutoff = datetime.now(timezone.utc) - timedelta(hours=MAX_AGE_HOURS)
    existing_fresh = []
    for r in existing:
        try:
            if r.get("source","") == "Demo": continue
            ts = r.get("timestamp","")
            if not ts: continue
            dt = datetime.fromisoformat(ts.replace("Z","+00:00"))
            if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
            if dt > cutoff: existing_fresh.append(r)
        except: pass

    print(f"🧹 Temizlik: {len(existing_fresh)} rapor kaldı ({len(existing)-len(existing_fresh)} silindi)")

    new_reports = []
    if GEMINI_KEY:
        new_reports += scrape_with_gemini()
    new_reports += scrape_google_news()
    new_reports += scrape_rss()
    new_reports += scrape_telegram()

    print(f"\n📊 Yeni rapor: {len(new_reports)}")

    ts = now_iso()
    for r in new_reports:
        if "timestamp" not in r: r["timestamp"] = ts
        r["time"] = time_ago(r["timestamp"])

    if len(new_reports) < 5:
        print("⚠ Yeterli veri yok — demo veri ekleniyor...")
        for r in FALLBACK:
            r["timestamp"] = ts
            r["time"] = "Az önce"
        new_reports = FALLBACK + new_reports

    all_map = {r["id"]: r for r in existing_fresh}
    added = 0
    for r in new_reports:
        if r["id"] not in all_map:
            all_map[r["id"]] = r
            added += 1

    sorted_reports = sorted(
        all_map.values(),
        key=lambda x: x.get("timestamp",""),
        reverse=True
    )[:MAX_REPORTS]

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE,"w",encoding="utf-8") as f:
        json.dump({
            "last_updated": ts,
            "total":        len(sorted_reports),
            "reports":      sorted_reports,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Tamamlandı!")
    print(f"   Yeni eklenen : {added}")
    print(f"   Toplam rapor : {len(sorted_reports)}")
    print("="*65)

if __name__ == "__main__":
    main()
