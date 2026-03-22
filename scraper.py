#!/usr/bin/env python3
"""
Türkiye Balık Radarı - Gemini API Destekli Scraper v6
Bölge: İstanbul, Tekirdağ, Edirne, Kocaeli, Yalova, Bursa, Balıkesir
Her 3 saatte bir GitHub Actions tarafından çalıştırılır.
"""

import os, json, time, hashlib, random, requests
from datetime import datetime, timezone
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

OUTPUT_FILE  = "data/reports.json"
MAX_REPORTS  = 300
GEMINI_KEY   = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL   = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9",
}

# ════════════════════════════════════════════════════════════════════
# HASSAS KOORDİNATLAR — 7 İL
# ════════════════════════════════════════════════════════════════════
LOCATIONS = {
    "galata köprüsü":        (41.01620, 28.97420),
    "galata köprüsü avrupa": (41.01600, 28.97150),
    "galata köprüsü asya":   (41.01640, 28.97700),
    "eminönü":               (41.01650, 28.97300),
    "karaköy":               (41.02250, 28.97400),
    "sarayburnu":            (41.01330, 28.98170),
    "sirkeci":               (41.01300, 28.97800),
    "haliç":                 (41.03200, 28.95000),
    "fener balat":           (41.03100, 28.95100),
    "ayvansaray":            (41.03700, 28.94300),
    "eyüp":                  (41.04900, 28.93300),
    "yenikapı":              (41.00500, 28.94900),
    "kumkapı":               (41.00400, 28.96400),
    "yedikule":              (40.99800, 28.92700),
    "florya":                (40.97130, 28.79860),
    "yeşilköy":              (40.97280, 28.81660),
    "bakırköy":              (40.97920, 28.87010),
    "ataköy":                (40.98200, 28.84300),
    "avcılar":               (40.97930, 28.72190),
    "büyükçekmece gölü":     (41.06000, 28.59000),
    "büyükçekmece":          (41.01970, 28.57730),
    "küçükçekmece gölü":     (41.02000, 28.76000),
    "küçükçekmece":          (41.01300, 28.77670),
    "silivri":               (41.07260, 28.24840),
    "karaburun istanbul":    (41.34840, 28.68970),
    "kilyos":                (41.24970, 29.01570),
    "şile":                  (41.17780, 29.61030),
    "ağva":                  (41.09800, 29.99940),
    "rumeli feneri":         (41.22500, 29.10750),
    "rumeli kavağı":         (41.19870, 29.06220),
    "büyükdere":             (41.14800, 29.05670),
    "sarıyer":               (41.16650, 29.05300),
    "yeniköy boğaz":         (41.11100, 29.05780),
    "tarabya":               (41.12680, 29.05690),
    "kuruçeşme":             (41.06300, 29.03100),
    "bebek":                 (41.07850, 29.04360),
    "arnavutköy":            (41.06720, 29.03680),
    "ortaköy":               (41.05330, 29.02690),
    "beşiktaş":              (41.04300, 29.00600),
    "kabataş":               (41.03470, 29.00450),
    "dolmabahçe":            (41.03900, 29.00000),
    "anadolu feneri":        (41.21940, 29.15900),
    "anadolu kavağı":        (41.19300, 29.08200),
    "poyrazköy":             (41.20800, 29.13300),
    "beykoz":                (41.12180, 29.10140),
    "paşabahçe":             (41.13830, 29.09300),
    "kanlıca":               (41.10000, 29.08200),
    "anadolu hisarı":        (41.08330, 29.07360),
    "kandilli":              (41.07400, 29.06700),
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
    "istanbul boğazı":       (41.08000, 29.05000),
    "boğaziçi":              (41.08000, 29.05000),
    "istanbul":              (41.00820, 28.97840),
    "izmit körfezi":         (40.74000, 29.85000),
    "karamürsel":            (40.69440, 29.60750),
    "gölcük":                (40.65220, 29.83040),
    "hereke":                (40.79300, 29.62300),
    "diliskelesi":           (40.77500, 29.55800),
    "darıca":                (40.76600, 29.37400),
    "körfez kocaeli":        (40.77000, 29.77000),
    "izmit":                 (40.76540, 29.94080),
    "kocaeli":               (40.76540, 29.94080),
    "çınarcık":              (40.64150, 29.12250),
    "armutlu":               (40.52780, 28.83200),
    "altınova yalova":       (40.60900, 29.49500),
    "yalova":                (40.65490, 29.27470),
    "uluabat gölü":          (40.16680, 28.62000),
    "apolyont gölü":         (40.16680, 28.62000),
    "iznik gölü":            (40.43300, 29.55000),
    "iznik":                 (40.42700, 29.72000),
    "gemlik":                (40.43150, 29.16250),
    "mudanya":               (40.37660, 28.88240),
    "orhangazi":             (40.49200, 29.31100),
    "trilye":                (40.35800, 28.83100),
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
    "kuş gölü":              (40.20000, 27.97000),
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
    "çınarcık","armutlu","iznik","uluabat","orhangazi","trilye",
    "meriç","ergene","tunca","uzunköprü","enez","keşan","ipsala",
    "karamürsel","gölcük","hereke","darıca","izmit körfezi",
    "mürefte","hoşköy","marmara ereğlisi","manyas","kuş gölü",
    "marmara adası","avşa","erdek","bandırma",
]

FISHING_REQUIRED = [
    "balık tut","balık avla","olta","lüfer","palamut","hamsi","sazan",
    "levrek","çipura","kefal","istavrit","kolyoz","barbun","kalkan",
    "alabalık","yayın","sudak","turna","karagöz","spin","lrf","surf",
    "feeder","jigging","balıkçı","av raporu","avlandı","tutuldu",
    "tuttu","çıktı","vurdu","oltaya geldi","mepps","rapala","kaşık",
    "silikon","jig","wobbler","popper","fishing",
]

NOISE_WORDS = [
    "balık fiyat","ton balığı fabrika","balıkçı teknesi battı",
    "toplu balık ölü","su kirliliği","deprem","yangın","trafik",
    "seçim","siyasi","ekonomi","döviz","borsa","futbol","dizi",
]

FISH_KW = [
    "sazan","levrek","çipura","lüfer","palamut","hamsi","istavrit","kalkan",
    "barbun","kefal","alabalık","yayın","sudak","turna","karagöz","sargoz",
    "kolyoz","uskumru","orkinos","mercan","isparoz","kızılkanat","tekir",
    "izmarit","çinekop","torik","tirsi","sardalya","minekop","mezgit",
]

ROD_MAP = {
    "Spin":      ["spin","spinning","mepps","kastmaster","kaşık","lure","rapala","wobbler","popper","crankbait"],
    "LRF":       ["lrf","light rock","micro","ajing","finesse","gulp","berkley"],
    "Surf":      ["surf","surfcasting","sahil oltası","uzak mesafe","plumb"],
    "Feeder":    ["feeder","method","pellet","boilie","karpçılık"],
    "Fly":       ["sinek olta","fly fishing","yapay sinek","elk hair","nymph"],
    "Jigging":   ["jigging","jig","silikon","vertical","dikey","twister"],
    "Trolling":  ["trolling","trol","tekneden"],
    "Bolentino": ["bolentino","dip olta","paternos"],
    "Zıpkın":   ["zıpkın","dalış","spearfishing"],
    "Olta":      ["olta","iğne","misina","el oltası"],
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
    tl = text.lower()
    if any(n in tl for n in NOISE_WORDS): return False
    if not any(f in tl for f in FISHING_REQUIRED): return False
    if not any(r in tl for r in VALID_REGIONS): return False
    return True

def extract_fish(text):
    tl = text.lower()
    return list(dict.fromkeys([f.title() for f in FISH_KW if f in tl]))[:4] or ["Belirtilmemiş"]

def extract_rod(text):
    tl = text.lower()
    for rod, kws in ROD_MAP.items():
        if any(kw in tl for kw in kws): return rod
    return ""

def extract_bait(text):
    tl = text.lower()
    return ", ".join([b.title() for b in BAIT_KW if b in tl][:2])

def find_location(text):
    tl = text.lower()
    best, best_coords, best_len = None, None, 0
    for name, coords in LOCATIONS.items():
        if name in tl and len(name) > best_len:
            best, best_coords, best_len = name, coords, len(name)
    return best, best_coords

def classify_type(text, loc):
    tl = (text+" "+(loc or "")).lower()
    if any(w in tl for w in ["nehir","irmak","dere","çay","meriç","ergene","tunca"]): return "nehir"
    if any(w in tl for w in ["göl","gölü"]): return "göl"
    return "deniz"

def build_report(title, body, source, url="", hint=""):
    text = " ".join([title, body, hint])
    if not is_valid(text): return None
    fish = extract_fish(text)
    if fish == ["Belirtilmemiş"]: return None
    loc, coords = find_location(text)
    if not coords and hint: loc, coords = find_location(hint)
    if not coords: return None
    lat = round(coords[0] + random.uniform(-0.003, 0.003), 6)
    lng = round(coords[1] + random.uniform(-0.003, 0.003), 6)
    ts = now_iso()
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

# ════════════════════════════════════════════════════════════════════
# GEMİNİ API — Web'i tarayarak balık raporu üretir
# ════════════════════════════════════════════════════════════════════
def ask_gemini(prompt):
    if not GEMINI_KEY:
        print("  ⚠ GEMINI_API_KEY yok")
        return ""
    try:
        url = f"{GEMINI_URL}?key={GEMINI_KEY}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 3000,
            }
        }
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"  ⚠ Gemini API hatası: {e}")
        return ""

def scrape_with_gemini():
    print("🤖 Gemini API ile akıllı tarama başlıyor...")

    # Her sorgu belirli bir bölgeye odaklanıyor
    prompts = [
        """Bugün veya dün İstanbul'da şu noktalarda balık tutma raporları var mı?
        Galata Köprüsü, Eminönü, Karaköy, Sarayburnu, Haliç, Boğaziçi.
        İnternette, Türkçe forumlarda, sosyal medyada, haber sitelerinde ara.
        
        Bulduğun her rapor için şu formatta yaz (her rapor ayrı satır):
        LOKASYON: [yer adı] | BALIK: [balık türleri] | OLTA: [olta türü] | YEM: [yem] | NOT: [kısa bilgi]
        
        Sadece gerçek bulduğun bilgileri yaz, uydurma.""",

        """Bugün veya dün İstanbul Boğazı'nda şu noktalarda balık var mı?
        Sarıyer, Rumeli Kavağı, Rumeli Feneri, Büyükdere, Tarabya, 
        Bebek, Beykoz, Anadolu Kavağı, Paşabahçe, Kanlıca.
        İnternette ara, Türkçe forumlarda ve sosyal medyada bak.
        
        Bulduğun her rapor için:
        LOKASYON: [yer] | BALIK: [türler] | OLTA: [olta] | YEM: [yem] | NOT: [bilgi]""",

        """İstanbul Anadolu yakası ve adalarda bugün balık raporu:
        Bostancı, Kadıköy, Fenerbahçe, Maltepe, Kartal, Pendik, Tuzla,
        Büyükada, Heybeliada, Büyükçekmece, Küçükçekmece, Şile, Kilyos.
        İnternette Türkçe kaynaklarda ara.
        
        Format: LOKASYON: [yer] | BALIK: [türler] | OLTA: [olta] | YEM: [yem] | NOT: [bilgi]""",

        """Kocaeli (İzmit Körfezi, Karamürsel, Gölcük, Gebze), 
        Yalova (Çınarcık, Armutlu), Bursa (Gemlik, Mudanya, Orhangazi, İznik Gölü, Uluabat Gölü)
        bölgelerinde bugün balık tutma haberleri veya raporları var mı?
        İnternette Türkçe kaynaklarda ara.
        
        Format: LOKASYON: [yer] | BALIK: [türler] | OLTA: [olta] | YEM: [yem] | NOT: [bilgi]""",

        """Tekirdağ (Şarköy, Mürefte, Marmara Ereğlisi), 
        Balıkesir (Erdek, Bandırma, Marmara Adası, Avşa Adası, Manyas Gölü),
        Edirne (Meriç Nehri, Ergene, Tunca) bölgelerinde bugün balık raporu var mı?
        İnternette Türkçe kaynaklarda ara.
        
        Format: LOKASYON: [yer] | BALIK: [türler] | OLTA: [olta] | YEM: [yem] | NOT: [bilgi]""",

        """Marmara Denizi ve İstanbul çevresinde şu an hangi balıklar aktif?
        Lüfer, palamut, kolyoz, çipura, levrek, hamsi, istavrit hakkında
        güncel bilgi ve raporlar neler? Hangi noktalarda yoğunluk var?
        Türkçe forumlarda, Instagram'da, Facebook gruplarında, haberlerde ara.
        
        Format: LOKASYON: [yer] | BALIK: [türler] | OLTA: [olta] | YEM: [yem] | NOT: [bilgi]""",

        """Sapanca Gölü ve çevresinde bugün balık tutma haberleri var mı?
        Ayrıca İstanbul'daki spin, LRF, surf balıkçılığı ile ilgili 
        bugünkü veya dünkü raporlar neler?
        Türkçe kaynaklarda ara.
        
        Format: LOKASYON: [yer] | BALIK: [türler] | OLTA: [olta] | YEM: [yem] | NOT: [bilgi]""",
    ]

    all_reports = []
    for i, prompt in enumerate(prompts):
        print(f"  Gemini sorgu {i+1}/{len(prompts)}...")
        response = ask_gemini(prompt)
        if not response:
            time.sleep(2)
            continue

        # Gemini cevabını satır satır işle
        lines = [l.strip() for l in response.split("\n") if "LOKASYON:" in l]
        print(f"    → {len(lines)} rapor satırı bulundu")

        for line in lines:
            try:
                # LOKASYON: X | BALIK: Y | OLTA: Z | YEM: W | NOT: V
                parts = {p.split(":")[0].strip(): ":".join(p.split(":")[1:]).strip()
                         for p in line.split("|") if ":" in p}
                loc_hint = parts.get("LOKASYON","")
                fish_str = parts.get("BALIK","")
                rod_str  = parts.get("OLTA","")
                bait_str = parts.get("YEM","")
                note_str = parts.get("NOT","")

                full_text = f"{loc_hint} {fish_str} {rod_str} {bait_str} {note_str}"

                loc, coords = find_location(full_text)
                if not coords:
                    loc, coords = find_location(loc_hint.lower())
                if not coords:
                    continue

                fish = [f.strip().title() for f in fish_str.split(",") if f.strip()]
                if not fish: fish = extract_fish(full_text)
                if fish == ["Belirtilmemiş"]: continue

                rod  = rod_str.strip() or extract_rod(full_text)
                bait = bait_str.strip() or extract_bait(full_text)
                note = note_str.strip() or f"{loc_hint} bölgesinde balık raporu."

                lat = round(coords[0] + random.uniform(-0.003, 0.003), 6)
                lng = round(coords[1] + random.uniform(-0.003, 0.003), 6)
                ts  = now_iso()

                all_reports.append({
                    "id":        make_id(line),
                    "lat":       lat, "lng": lng,
                    "loc":       loc.title(),
                    "fish":      fish[:4],
                    "rod":       rod,
                    "bait":      bait,
                    "note":      note[:160],
                    "heat":      min(5, len(fish)+1),
                    "type":      classify_type(full_text, loc),
                    "time":      time_ago(ts),
                    "timestamp": ts,
                    "source":    "Gemini AI + Web Tarama",
                    "url":       "",
                    "hot":       len(fish) >= 2,
                })
            except Exception as e:
                print(f"    ⚠ Satır işleme hatası: {e}")
                continue

        time.sleep(4)  # Gemini rate limit

    print(f"  ✓ Gemini toplam {len(all_reports)} rapor üretti")
    return all_reports

# ════════════════════════════════════════════════════════════════════
# GOOGLE NEWS RSS
# ════════════════════════════════════════════════════════════════════
def scrape_google_news():
    print("📰 Google News taranıyor...")
    queries = [
        "galata köprüsü balık tutma",
        "eminönü karaköy balık",
        "boğaz lüfer palamut kolyoz",
        "sarıyer rumeli kavağı balık",
        "beykoz anadolu kavağı balık",
        "bostancı kadıköy sahil balık",
        "büyükçekmece şile kilyos balık",
        "istanbul lüfer sezonu",
        "istanbul balıkçılık raporu",
        "kocaeli izmit körfezi balık",
        "yalova gemlik mudanya balık",
        "tekirdağ şarköy marmara balık",
        "edirne meriç ergene balık",
        "balıkesir erdek bandırma balık",
        "sapanca gölü balık",
        "iznik gölü uluabat balık",
        "marmara denizi çipura levrek",
        "lüfer palamut marmara",
        "spin lrf surf istanbul",
    ]
    results, seen = [], set()
    for q in queries:
        url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=tr&gl=TR&ceid=TR:tr"
        r = safe_get(url)
        if not r: time.sleep(1); continue
        try:    soup = BeautifulSoup(r.content, "xml")
        except: soup = BeautifulSoup(r.content, "lxml-xml")
        items = soup.find_all("item")
        print(f"  '{q}' → {len(items)} sonuç")
        for item in items[:8]:
            t = item.find("title"); d = item.find("description"); l = item.find("link")
            if not t: continue
            title = t.get_text(strip=True)
            if title in seen: continue
            seen.add(title)
            desc = d.get_text(strip=True) if d else ""
            link = l.get_text(strip=True) if l else ""
            rep = build_report(title, desc, "Google Haberler", link, q)
            if rep: results.append(rep)
        time.sleep(1.2)
    print(f"  ✓ {len(results)} geçerli rapor")
    return results

# ════════════════════════════════════════════════════════════════════
# RSS FEEDLER
# ════════════════════════════════════════════════════════════════════
def scrape_rss():
    print("📡 RSS feedler taranıyor...")
    feeds = [
        ("https://www.hurriyet.com.tr/rss/gundem",               "Hürriyet"),
        ("https://www.sabah.com.tr/rss/yasam.xml",               "Sabah"),
        ("https://www.milliyet.com.tr/rss/rssNew/gundemRss.xml", "Milliyet"),
        ("https://www.trthaber.com/trthaber.rss",                "TRT Haber"),
        ("https://www.aa.com.tr/tr/rss/default?cat=yasam",       "AA"),
    ]
    results = []
    for url, src in feeds:
        r = safe_get(url)
        if not r: continue
        try:    soup = BeautifulSoup(r.content, "xml")
        except: soup = BeautifulSoup(r.content, "lxml-xml")
        for item in soup.find_all("item")[:30]:
            t = item.find("title"); d = item.find("description")
            if not t: continue
            title = t.get_text(strip=True)
            desc  = d.get_text(strip=True) if d else ""
            rep = build_report(title, desc, src)
            if rep: results.append(rep)
        time.sleep(0.8)
    print(f"  ✓ {len(results)} geçerli rapor")
    return results

# ════════════════════════════════════════════════════════════════════
# TELEGRAM PUBLIC
# ════════════════════════════════════════════════════════════════════
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
        for msg in msgs[:20]:
            text = msg.get_text(strip=True)
            if len(text) < 20: continue
            rep = build_report(text[:200], "", src)
            if rep: results.append(rep)
        time.sleep(1.5)
    print(f"  ✓ {len(results)} geçerli rapor")
    return results

# ════════════════════════════════════════════════════════════════════
# FALLBACK VERİ
# ════════════════════════════════════════════════════════════════════
FALLBACK = [
    {"id":"f01","lat":41.01620,"lng":28.97420,"loc":"Galata Köprüsü","fish":["Lüfer","Kolyoz","Kefal"],"rod":"Olta","bait":"Çoklu iğne, hamsi","note":"Galata Köprüsü'nde yoğun balıkçı. Lüfer ve kolyoz tutuldu.","heat":5,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f02","lat":41.01650,"lng":28.97300,"loc":"Eminönü","fish":["Kefal","İstavrit"],"rod":"Olta","bait":"Ekmek, solucan","note":"Eminönü rıhtımında kefal aktif.","heat":4,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"f03","lat":41.02250,"lng":28.97400,"loc":"Karaköy","fish":["Lüfer","Levrek"],"rod":"Spin","bait":"Küçük kaşık","note":"Karaköy iskelesi. Sabah lüfer çıktı.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f04","lat":41.01330,"lng":28.98170,"loc":"Sarayburnu","fish":["Kolyoz","Palamut","Lüfer"],"rod":"Trolling","bait":"Çukur kaşık","note":"Sarayburnu açıklarında palamut akını.","heat":5,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f05","lat":41.07850,"lng":29.04360,"loc":"Bebek","fish":["Levrek","Kefal"],"rod":"LRF","bait":"Micro jig","note":"Bebek koyu. Levrek micro jig ile tutuldu.","heat":3,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"f06","lat":41.16650,"lng":29.05300,"loc":"Sarıyer","fish":["Lüfer","Palamut"],"rod":"Spin","bait":"Mepps No:3","note":"Sarıyer açıkları. Lüfer girişi başladı.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f07","lat":41.19870,"lng":29.06220,"loc":"Rumeli Kavağı","fish":["Palamut","Lüfer","Torik"],"rod":"Trolling","bait":"CD-11 Rapala","note":"Rumeli Kavağı. Torik ve palamut aktif.","heat":5,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f08","lat":41.12180,"lng":29.10140,"loc":"Beykoz","fish":["Kalkan","Barbun"],"rod":"Olta","bait":"Deniz kurdu","note":"Beykoz sahili. Dip olta ile barbun bol.","heat":4,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"f09","lat":40.96070,"lng":29.09000,"loc":"Bostancı","fish":["Lüfer","İstavrit"],"rod":"Spin","bait":"Kaşık","note":"Bostancı sahili akşam lüfer girişi.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f10","lat":41.06000,"lng":28.59000,"loc":"Büyükçekmece Gölü","fish":["Sazan","Turna","Kefal"],"rod":"Feeder","bait":"Mısır, solucan","note":"Büyükçekmece Gölü sazan sezonu açık.","heat":5,"type":"göl","hot":True,"source":"Demo"},
    {"id":"f11","lat":40.74000,"lng":29.85000,"loc":"İzmit Körfezi","fish":["Çipura","Levrek"],"rod":"LRF","bait":"Gulp, micro jig","note":"İzmit körfezi çipura aktif.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f12","lat":40.65490,"lng":29.27470,"loc":"Yalova","fish":["Kefal","Levrek"],"rod":"Olta","bait":"Solucan","note":"Yalova iskelesi. Kefal bol.","heat":3,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"f13","lat":40.43150,"lng":29.16250,"loc":"Gemlik","fish":["Çipura","Levrek","Karagöz"],"rod":"LRF","bait":"Silikon, micro jig","note":"Gemlik limanı sabah çipura harika.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f14","lat":40.37660,"lng":28.88240,"loc":"Mudanya","fish":["Kefal","Levrek"],"rod":"Feeder","bait":"Ekmek, deniz kurdu","note":"Mudanya iskelesi aktif.","heat":3,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"f15","lat":40.97810,"lng":27.51170,"loc":"Tekirdağ","fish":["Lüfer","Palamut","Kolyoz"],"rod":"Surf","bait":"Çoklu iğne takımı","note":"Tekirdağ sahili. Palamut geçişi var.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f16","lat":40.61210,"lng":27.11030,"loc":"Şarköy","fish":["Çipura","Levrek","Barbun"],"rod":"LRF","bait":"Berkley Gulp","note":"Şarköy açıkları çok aktif.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f17","lat":40.96800,"lng":27.95900,"loc":"Marmara Ereğlisi","fish":["Lüfer","Kolyoz"],"rod":"Surf","bait":"Çoklu iğne","note":"Marmara Ereğlisi sahili lüfer aktif.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f18","lat":41.67710,"lng":26.55570,"loc":"Edirne - Meriç Nehri","fish":["Sazan","Yayın","Turna"],"rod":"Feeder","bait":"Boilie, canlı balık","note":"Meriç nehrinde yayın sezonu.","heat":4,"type":"nehir","hot":True,"source":"Demo"},
    {"id":"f19","lat":40.72000,"lng":30.20000,"loc":"Sapanca Gölü","fish":["Alabalık","Sazan","Yayın"],"rod":"Spin","bait":"Rapala, solucan","note":"Sapanca sabah alabalık harika.","heat":5,"type":"göl","hot":True,"source":"Demo"},
    {"id":"f20","lat":40.43300,"lng":29.55000,"loc":"İznik Gölü","fish":["Sazan","Levrek","Sudak"],"rod":"Feeder","bait":"Pellet, mısır","note":"İznik gölü sazan sezonu açık.","heat":4,"type":"göl","hot":False,"source":"Demo"},
    {"id":"f21","lat":40.16680,"lng":28.62000,"loc":"Uluabat Gölü","fish":["Sazan","Yayın","Turna"],"rod":"Feeder","bait":"Mısır, boilie","note":"Uluabat gölü sazan bolluğu.","heat":4,"type":"göl","hot":False,"source":"Demo"},
    {"id":"f22","lat":40.39750,"lng":27.79580,"loc":"Erdek","fish":["Çipura","Karagöz","Sargoz"],"rod":"LRF","bait":"Micro jig","note":"Erdek açıkları mükemmel.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f23","lat":40.60000,"lng":27.57900,"loc":"Marmara Adası","fish":["Çipura","Levrek","Sargoz"],"rod":"LRF","bait":"Micro jig, gulp","note":"Marmara adası etrafı çipura bol.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f24","lat":41.62000,"lng":26.72000,"loc":"Ergene Nehri","fish":["Sazan","Turna"],"rod":"Feeder","bait":"Mısır, solucan","note":"Ergene sazan tutuldu.","heat":3,"type":"nehir","hot":False,"source":"Demo"},
    {"id":"f25","lat":40.35000,"lng":27.97700,"loc":"Bandırma","fish":["Kefal","Çipura"],"rod":"Olta","bait":"Solucan, ekmek","note":"Bandırma limanı kefal aktif.","heat":3,"type":"deniz","hot":False,"source":"Demo"},
]

# ════════════════════════════════════════════════════════════════════
# ANA FONKSİYON
# ════════════════════════════════════════════════════════════════════
def main():
    print("="*65)
    print(f"🎣 Balık Radarı v6 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Gemini API: {'✓ Aktif' if GEMINI_KEY else '✗ Yok'}")
    print("="*65)

    existing = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE,"r",encoding="utf-8") as f:
                existing = json.load(f).get("reports",[])
            print(f"📂 Mevcut: {len(existing)} rapor")
        except Exception as e:
            print(f"⚠ {e}")

    new_reports = []

    # Gemini (varsa) — en zengin kaynak
    if GEMINI_KEY:
        new_reports += scrape_with_gemini()

    # Klasik kaynaklar
    new_reports += scrape_google_news()
    new_reports += scrape_rss()
    new_reports += scrape_telegram()

    print(f"\n📊 Yeni (filtreden geçen): {len(new_reports)}")

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

    all_map = {r["id"]: r for r in existing}
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
