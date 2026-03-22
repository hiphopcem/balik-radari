#!/usr/bin/env python3
"""
Türkiye Balık Radarı - Claude API + Web Search Scraper v4
Bölge: İstanbul, Tekirdağ, Edirne, Kocaeli, Yalova, Bursa, Balıkesir
Her 3 saatte bir GitHub Actions tarafından çalıştırılır.

Kurulum:
  GitHub Secrets'a ANTHROPIC_API_KEY ekle
"""

import os, json, time, hashlib, random, requests
from datetime import datetime, timezone
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

OUTPUT_FILE  = "data/reports.json"
MAX_REPORTS  = 300
API_KEY      = os.environ.get("ANTHROPIC_API_KEY", "")
API_URL      = "https://api.anthropic.com/v1/messages"
MODEL        = "claude-opus-4-5"

HEADERS_HTTP = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9",
}

# ════════════════════════════════════════════════════════════════════
# HASSAS KOORDİNATLAR
# ════════════════════════════════════════════════════════════════════
LOCATIONS = {
    # İSTANBUL — Tarihi Yarımada & Haliç
    "galata köprüsü":       (41.01620, 28.97420),
    "galata köprüsü avrupa":(41.01620, 28.97200),
    "galata köprüsü asya":  (41.01620, 28.97600),
    "galata":               (41.02550, 28.97420),
    "karaköy":              (41.02250, 28.97400),
    "eminönü":              (41.01650, 28.97300),
    "sirkeci":              (41.01300, 28.97800),
    "sarayburnu":           (41.01330, 28.98170),
    "haliç":                (41.03200, 28.95000),
    "fener":                (41.03200, 28.95200),
    "balat":                (41.03000, 28.94900),
    "ayvansaray":           (41.03700, 28.94300),
    "eyüp":                 (41.04900, 28.93300),
    "hasköy":               (41.03800, 28.94700),
    "yenikapı":             (41.00500, 28.94900),
    "kumkapı":              (41.00400, 28.96400),
    "yedikule":             (40.99800, 28.92700),
    # İSTANBUL — Avrupa Sahili
    "bakırköy":             (40.97920, 28.87010),
    "florya":               (40.97130, 28.79860),
    "yeşilköy":             (40.97280, 28.81660),
    "ataköy":               (40.98200, 28.84300),
    "avcılar":              (40.97930, 28.72190),
    "büyükçekmece":         (41.01970, 28.57730),
    "büyükçekmece gölü":    (41.06000, 28.59000),
    "küçükçekmece":         (41.01300, 28.77670),
    "küçükçekmece gölü":    (41.02000, 28.76000),
    "karaburun":            (41.34840, 28.68970),
    "kilyos":               (41.24970, 29.01570),
    "şile":                 (41.17780, 29.61030),
    "ağva":                 (41.09800, 29.99940),
    "silivri":              (41.07260, 28.24840),
    # İSTANBUL — Boğaz Avrupa
    "bebek":                (41.07850, 29.04360),
    "arnavutköy":           (41.06720, 29.03680),
    "ortaköy":              (41.05330, 29.02690),
    "beşiktaş":             (41.04300, 29.00600),
    "kabataş":              (41.03470, 29.00450),
    "dolmabahçe":           (41.03900, 29.00000),
    "kuruçeşme":            (41.06300, 29.03100),
    "tarabya":              (41.12680, 29.05690),
    "yeniköy":              (41.11100, 29.05780),
    "büyükdere":            (41.14800, 29.05670),
    "sarıyer":              (41.16650, 29.05300),
    "rumeli kavağı":        (41.19870, 29.06220),
    "rumeli feneri":        (41.22500, 29.10750),
    # İSTANBUL — Boğaz Anadolu
    "üsküdar":              (41.02270, 29.01510),
    "çengelköy":            (41.06200, 29.05900),
    "kandilli":             (41.07400, 29.06700),
    "anadolu hisarı":       (41.08330, 29.07360),
    "kanlıca":              (41.10000, 29.08200),
    "paşabahçe":            (41.13830, 29.09300),
    "beykoz":               (41.12180, 29.10140),
    "anadolu kavağı":       (41.19300, 29.08200),
    "anadolu feneri":       (41.21940, 29.15900),
    "poyrazköy":            (41.20800, 29.13300),
    # İSTANBUL — Anadolu Sahili
    "kadıköy":              (40.99020, 29.02320),
    "moda":                 (40.98400, 29.02800),
    "fenerbahçe":           (40.96800, 29.05400),
    "bostancı":             (40.96070, 29.09000),
    "suadiye":              (40.95300, 29.10000),
    "caddebostan":          (40.96200, 29.06800),
    "maltepe":              (40.93410, 29.13500),
    "kartal":               (40.90750, 29.18580),
    "pendik":               (40.87620, 29.23300),
    "tuzla":                (40.81480, 29.29600),
    "gebze":                (40.80240, 29.43000),
    # İSTANBUL — Adalar
    "adalar":               (40.87170, 29.10920),
    "büyükada":             (40.87170, 29.12400),
    "heybeliada":           (40.88300, 29.09400),
    "burgazada":            (40.87700, 29.06400),
    "kınalıada":            (40.90000, 29.03100),
    # KOCAELİ
    "izmit":                (40.76540, 29.94080),
    "kocaeli":              (40.76540, 29.94080),
    "izmit körfezi":        (40.74000, 29.85000),
    "körfez":               (40.77000, 29.77000),
    "karamürsel":           (40.69440, 29.60750),
    "gölcük":               (40.65220, 29.83040),
    "darıca":               (40.76600, 29.37400),
    "hereke":               (40.79300, 29.62300),
    "diliskelesi":          (40.77500, 29.55800),
    "tavşancıl":            (40.78700, 29.51200),
    # YALOVA
    "yalova":               (40.65490, 29.27470),
    "çınarcık":             (40.64150, 29.12250),
    "armutlu":              (40.52780, 28.83200),
    "altınova":             (40.60900, 29.49500),
    # BURSA
    "bursa":                (40.18260, 29.06650),
    "mudanya":              (40.37660, 28.88240),
    "gemlik":               (40.43150, 29.16250),
    "orhangazi":            (40.49200, 29.31100),
    "zeytinbağı":           (40.39800, 28.98200),
    "trilye":               (40.35800, 28.83100),
    "iznik":                (40.42700, 29.72000),
    "iznik gölü":           (40.43300, 29.55000),
    "uluabat gölü":         (40.16680, 28.62000),
    "apolyont":             (40.16680, 28.62000),
    # TEKİRDAĞ
    "tekirdağ":             (40.97810, 27.51170),
    "marmara ereğlisi":     (40.96800, 27.95900),
    "şarköy":               (40.61210, 27.11030),
    "mürefte":              (40.67400, 27.25600),
    "hoşköy":               (40.74400, 27.17300),
    "barbaros":             (40.82000, 27.45000),
    "marmara denizi":       (40.65000, 27.90000),
    # EDİRNE
    "edirne":               (41.67710, 26.55570),
    "keşan":                (40.85600, 26.63950),
    "enez":                 (40.72820, 26.08110),
    "ergene":               (41.62000, 26.72000),
    "tunca":                (41.70000, 26.55000),
    "meriç":                (41.18000, 26.40000),
    "uzunköprü":            (41.26900, 26.68950),
    "ipsala":               (40.91790, 26.38450),
    # BALIKESİR
    "balıkesir":            (39.64840, 27.88260),
    "erdek":                (40.39750, 27.79580),
    "bandırma":             (40.35000, 27.97700),
    "gönen":                (40.10060, 27.65020),
    "edincik":              (40.34640, 27.87200),
    "marmara adası":        (40.60000, 27.57900),
    "avşa":                 (40.51940, 27.59170),
    "manyas gölü":          (40.20000, 27.97000),
    "kuş gölü":             (40.20000, 27.97000),
    "ayvalık":              (39.31760, 26.69630),
    # SAPANCA / ADAPAZARI
    "sapanca":              (40.69320, 30.27050),
    "sapanca gölü":         (40.72000, 30.20000),
    "adapazarı":            (40.77310, 30.39560),
    # GENEL
    "istanbul":             (41.00820, 28.97840),
    "marmara":              (40.65000, 27.90000),
    "boğaz":                (41.08000, 29.05000),
    "boğaziçi":             (41.08000, 29.05000),
    "haliç girişi":         (41.02800, 28.96000),
}

FISH_KW = [
    "sazan","levrek","çipura","lüfer","palamut","hamsi","istavrit","kalkan",
    "barbun","kefal","alabalık","yayın","sudak","turna","karagöz","sargoz",
    "kolyoz","uskumru","orkinos","mercan","isparoz","kızılkanat","tekir",
    "izmarit","lahos","fangri","dil balığı","kırlangıç","lagos","grida",
    "çinekop","torik","tirsi","sardalya","aterina","minekop","mezgit",
]

ROD_MAP = {
    "Spin":      ["spin","spinning","mepps","kastmaster","kaşık","lure","rapala","wobbler","popper","crankbait"],
    "LRF":       ["lrf","light rock","micro","ajing","finesse","gulp","berkley","light game"],
    "Surf":      ["surf","surfcasting","sahil oltası","uzak mesafe","beach","plumb"],
    "Feeder":    ["feeder","method","pellet","boilie","karpçılık","groundbait"],
    "Fly":       ["sinek olta","fly fishing","yapay sinek","elk hair","adams","nymph"],
    "Jigging":   ["jigging","jig","silikon","vertical","dikey","softbait","twister"],
    "Trolling":  ["trolling","trol","tekneden"],
    "Bolentino": ["bolentino","dip olta","paternos"],
    "Zıpkın":   ["zıpkın","dalış","spearfishing","sualtı"],
    "Olta":      ["olta","iğne","misina","el oltası"],
}

BAIT_KW = [
    "mepps","rapala","kastmaster","kaşık","solucan","ekmek","mısır",
    "boilie","pellet","gulp","micro jig","silikon","twister","wobbler",
    "popper","crankbait","jig","olta balığı","canlı balık","canlı yem",
    "deniz kurdu","kalamar","midye","karides","hamsi yemi","suni yem",
]

def safe_get(url, timeout=20):
    try:
        r = requests.get(url, headers=HEADERS_HTTP, timeout=timeout)
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
    return list(dict.fromkeys([f.title() for f in FISH_KW if f in tl]))[:4] or ["Belirtilmemiş"]

def extract_rod(text):
    tl = text.lower()
    for rod, kws in ROD_MAP.items():
        if any(kw in tl for kw in kws): return rod
    return ""

def extract_bait(text):
    tl = text.lower()
    found = [b.title() for b in BAIT_KW if b in tl]
    return ", ".join(found[:2])

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
    if any(w in tl for w in ["baraj","nehir","irmak","dere","çay","meriç","ergene","tunca","sakarya"]): return "nehir"
    if any(w in tl for w in ["göl","gölü","lake"]): return "göl"
    return "deniz"

def build_report(title, body, source, url="", hint=""):
    text = " ".join([title, body, hint])
    fish = extract_fish(text)
    if fish == ["Belirtilmemiş"]: return None
    loc, coords = find_location(text)
    if not coords and hint:
        loc, coords = find_location(hint)
    if not coords: return None
    lat = round(coords[0] + random.uniform(-0.003, 0.003), 6)
    lng = round(coords[1] + random.uniform(-0.003, 0.003), 6)
    ts = now_iso()
    return {
        "id":        make_id(title + (loc or "")),
        "lat":       lat, "lng": lng,
        "loc":       loc.title(),
        "fish":      fish,
        "rod":       extract_rod(text),
        "bait":      extract_bait(text),
        "note":      title[:160],
        "heat":      min(5, len(fish) + 1),
        "type":      classify_type(text, loc),
        "time":      time_ago(ts),
        "timestamp": ts,
        "source":    source,
        "url":       url,
        "hot":       len(fish) >= 2,
    }

# ════════════════════════════════════════════════════════════════════
# CLAUDE API — Web Search ile akıllı tarama
# ════════════════════════════════════════════════════════════════════
def ask_claude(prompt):
    """Claude API'ye web_search tool ile soru sorar."""
    if not API_KEY:
        print("  ⚠ ANTHROPIC_API_KEY yok, Claude atlanıyor")
        return ""
    try:
        headers = {
            "x-api-key":         API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type":      "application/json",
            "anthropic-beta":    "tools-2024-04-04",
        }
        payload = {
            "model":      MODEL,
            "max_tokens": 4000,
            "tools": [{
                "type": "web_search_20250305",
                "name": "web_search",
            }],
            "messages": [{"role": "user", "content": prompt}],
        }
        r = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        # Tüm text bloklarını birleştir
        return " ".join(
            b.get("text", "") for b in data.get("content", [])
            if b.get("type") == "text"
        )
    except Exception as e:
        print(f"  ⚠ Claude API hatası: {e}")
        return ""

def scrape_with_claude():
    """Claude'a web search yaptırarak Marmara bölgesi balık raporları topla."""
    print("🤖 Claude API + Web Search ile taranıyor...")

    prompts = [
        # Her prompt için lokasyon ve konu belirli
        """Galata Köprüsü, Eminönü ve Karaköy'de son 24 saat içinde balık tutma raporları, 
        hangi balıklar tutuldu, ne tür olta ve yem kullanıldı? 
        Türkçe forum, sosyal medya ve haber sitelerinde ara. 
        Buldukların hakkında kısa kısa, her biri ayrı paragraf olacak şekilde yaz. 
        Her raporda: lokasyon, balık türü, olta türü, yem, kısa not olsun.""",

        """İstanbul Boğazı'nda (Sarıyer, Rumeli Kavağı, Beykoz, Anadolu Kavağı, 
        Paşabahçe, Bebek) bugün veya dün balık avı raporları neler? 
        Lüfer, palamut, kolyoz, levrek tutuldu mu? 
        Türkçe kaynaklarda ara ve her lokasyon için ayrı rapor yaz.""",

        """Büyükçekmece, Küçükçekmece, Şile, Kilyos, Ağva bölgelerinde 
        son balık tutma haberleri ve raporları neler? 
        Hangi balıklar, hangi olta, hangi yem kullanılıyor?
        Her yer için ayrı paragraf yaz.""",

        """İzmit Körfezi, Kocaeli, Karamürsel, Yalova, Çınarcık bölgelerinde 
        son balıkçılık raporları neler? Çipura, levrek, kefal var mı?
        Türkçe forumlarda ve haberlerde ara, her lokasyon için kısa rapor yaz.""",

        """Bursa (Gemlik, Mudanya, Orhangazi), İznik Gölü, Uluabat Gölü 
        bölgelerinde son balık avı haberleri ve raporları neler?
        Her lokasyon için ayrı rapor yaz, olta ve yem bilgisi varsa ekle.""",

        """Tekirdağ (Şarköy, Mürefte, Marmara Ereğlisi), Marmara Denizi ve 
        Erdek, Bandırma (Balıkesir) bölgelerinde son balıkçılık raporları neler?
        Her lokasyon için ayrı rapor, balık türü ve olta bilgisiyle yaz.""",

        """Edirne Meriç Nehri, Ergene, Tunca nehirlerinde son balık avı raporları.
        Sapanca Gölü ve Adapazarı bölgesinde son balık tutma haberleri.
        Her lokasyon için kısa rapor yaz.""",

        """Türkiye'de lüfer sezonu, palamut göçü, hamsi sezonu hakkında 
        bugünkü son haberler neler? Marmara'da hangi noktalarda aktif?
        Kısa kısa her bilgiyi ayrı paragrafta yaz.""",
    ]

    all_reports = []
    for i, prompt in enumerate(prompts):
        print(f"  Sorgu {i+1}/{len(prompts)}: {prompt[:60]}...")
        response = ask_claude(prompt)
        if not response:
            time.sleep(2)
            continue

        # Claude'un cevabını paragraflara böl ve her birinden rapor çıkar
        paragraphs = [p.strip() for p in response.split("\n") if len(p.strip()) > 30]
        for para in paragraphs:
            rep = build_report(para[:200], "", "Claude AI + Web Search")
            if rep:
                all_reports.append(rep)

        print(f"    → {len(paragraphs)} paragraf, {len([r for r in all_reports])} toplam rapor")
        time.sleep(3)  # Rate limit

    print(f"  ✓ Claude toplam {len(all_reports)} rapor üretti")
    return all_reports

# ════════════════════════════════════════════════════════════════════
# KLASIK SCRAPERLAR (Claude olmadan da çalışsın)
# ════════════════════════════════════════════════════════════════════
def scrape_google_news():
    print("📰 Google News RSS taranıyor...")
    queries = [
        "galata köprüsü balık tutma","eminönü balık","karaköy balık",
        "boğaz lüfer palamut","sarıyer balık","beykoz balık",
        "bostancı sahil balık","büyükçekmece balık","şile balık",
        "İstanbul lüfer sezonu","İstanbul balıkçılık",
        "Marmara denizi balık","Kocaeli İzmit balık",
        "Yalova çınarcık balık","Bursa gemlik balık",
        "Tekirdağ şarköy balık","Edirne meriç balık",
        "Sapanca gölü balık","İznik gölü balık",
        "lüfer sezonu Türkiye","palamut göçü",
        "balık avı raporu bugün","balıkçılık haberleri",
    ]
    results, seen = [], set()
    for q in queries:
        url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=tr&gl=TR&ceid=TR:tr"
        r = safe_get(url)
        if not r:
            time.sleep(1); continue
        try:    soup = BeautifulSoup(r.content, "xml")
        except: soup = BeautifulSoup(r.content, "lxml-xml")
        for item in soup.find_all("item")[:8]:
            t = item.find("title")
            d = item.find("description")
            l = item.find("link")
            if not t: continue
            title = t.get_text(strip=True)
            if title in seen: continue
            seen.add(title)
            desc = d.get_text(strip=True) if d else ""
            link = l.get_text(strip=True) if l else ""
            rep = build_report(title, desc, "Google Haberler", link, q)
            if rep: results.append(rep)
        time.sleep(1.2)
    print(f"  ✓ {len(results)} rapor")
    return results

def scrape_rss_feeds():
    print("📡 Haber RSS taranıyor...")
    feeds = [
        ("https://www.hurriyet.com.tr/rss/gundem",               "Hürriyet"),
        ("https://www.sabah.com.tr/rss/yasam.xml",               "Sabah"),
        ("https://www.milliyet.com.tr/rss/rssNew/gundemRss.xml", "Milliyet"),
        ("https://www.sozcu.com.tr/rss.xml",                     "Sözcü"),
        ("https://www.trthaber.com/trthaber.rss",                "TRT Haber"),
        ("https://www.aa.com.tr/tr/rss/default?cat=yasam",       "AA"),
    ]
    bw = ["balık","balıkçı","olta","lüfer","palamut","hamsi","sazan","çipura","levrek"]
    results = []
    for url, src in feeds:
        r = safe_get(url)
        if not r: continue
        try:    soup = BeautifulSoup(r.content, "xml")
        except: soup = BeautifulSoup(r.content, "lxml-xml")
        for item in soup.find_all("item")[:30]:
            t = item.find("title"); d = item.find("description")
            if not t: continue
            title = t.get_text(strip=True); desc = d.get_text(strip=True) if d else ""
            if not any(w in (title+desc).lower() for w in bw): continue
            rep = build_report(title, desc, src)
            if rep: results.append(rep)
        time.sleep(0.8)
    print(f"  ✓ {len(results)} rapor")
    return results

def scrape_telegram_public():
    print("📲 Telegram public kanalları taranıyor...")
    channels = [
        ("balikcilar_istanbul",  "Telegram: Balıkçılar İstanbul"),
        ("marmara_balik",        "Telegram: Marmara Balık"),
        ("istanbul_balikcilik",  "Telegram: İstanbul Balıkçılık"),
        ("bogaz_balik",          "Telegram: Boğaz Balık"),
        ("lufer_palamut",        "Telegram: Lüfer Palamut"),
        ("turkiye_balikcilar",   "Telegram: Türkiye Balıkçılar"),
        ("galata_koprusu_balik", "Telegram: Galata Köprüsü"),
        ("spin_lrf_istanbul",    "Telegram: Spin LRF İstanbul"),
        ("istanbul_fishing",     "Telegram: İstanbul Fishing"),
        ("marmara_fishing",      "Telegram: Marmara Fishing"),
    ]
    results = []
    for ch, src in channels:
        r = safe_get(f"https://t.me/s/{ch}")
        if not r: continue
        soup = BeautifulSoup(r.text, "html.parser")
        msgs = soup.select(".tgme_widget_message_text")
        print(f"  {ch}: {len(msgs)} mesaj")
        for msg in msgs[:20]:
            text = msg.get_text(strip=True)
            if len(text) < 15: continue
            bw = ["balık","lüfer","palamut","sazan","çipura","levrek","hamsi","olta","spin","lrf"]
            if not any(w in text.lower() for w in bw): continue
            rep = build_report(text[:200], "", src)
            if rep: results.append(rep)
        time.sleep(1.5)
    print(f"  ✓ {len(results)} rapor")
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
    {"id":"f07","lat":41.19870,"lng":29.06220,"loc":"Rumeli Kavağı","fish":["Palamut","Lüfer","Torik"],"rod":"Trolling","bait":"CD-11 Rapala","note":"Rumeli Kavağı. Torik ve palamut.","heat":5,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f08","lat":41.12180,"lng":29.10140,"loc":"Beykoz","fish":["Kalkan","Barbun"],"rod":"Olta","bait":"Deniz kurdu","note":"Beykoz sahili. Dip olta ile barbun.","heat":4,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"f09","lat":40.96070,"lng":29.09000,"loc":"Bostancı","fish":["Lüfer","İstavrit"],"rod":"Spin","bait":"Kaşık","note":"Bostancı sahili akşam lüfer girişi.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f10","lat":41.06000,"lng":28.59000,"loc":"Büyükçekmece Gölü","fish":["Sazan","Turna","Kefal"],"rod":"Feeder","bait":"Mısır, solucan","note":"Büyükçekmece Gölü sazan sezonu açık.","heat":5,"type":"göl","hot":True,"source":"Demo"},
    {"id":"f11","lat":40.76540,"lng":29.94080,"loc":"İzmit Körfezi","fish":["Çipura","Levrek"],"rod":"LRF","bait":"Gulp, micro jig","note":"İzmit körfezi çipura aktif.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f12","lat":40.65490,"lng":29.27470,"loc":"Yalova","fish":["Kefal","Levrek"],"rod":"Olta","bait":"Solucan","note":"Yalova iskelesi. Kefal bol.","heat":3,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"f13","lat":40.43150,"lng":29.16250,"loc":"Gemlik","fish":["Çipura","Levrek","Karagöz"],"rod":"LRF","bait":"Silikon, micro jig","note":"Gemlik limanı sabah çipura harika.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f14","lat":40.37660,"lng":28.88240,"loc":"Mudanya","fish":["Kefal","Levrek"],"rod":"Feeder","bait":"Ekmek, deniz kurdu","note":"Mudanya iskelesi aktif.","heat":3,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"f15","lat":40.97810,"lng":27.51170,"loc":"Tekirdağ","fish":["Lüfer","Palamut","Kolyoz"],"rod":"Surf","bait":"Çoklu iğne takımı","note":"Tekirdağ sahili. Palamut geçişi var.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
    {"id":"f16","lat":40.61210,"lng":27.11030,"loc":"Şarköy","fish":["Çipura","Levrek","Barbun"],"rod":"LRF","bait":"Berkley Gulp","note":"Şarköy açıkları çok aktif.","heat":4,"type":"deniz","hot":False,"source":"Demo"},
    {"id":"f17","lat":41.67710,"lng":26.55570,"loc":"Edirne - Meriç","fish":["Sazan","Yayın","Turna"],"rod":"Feeder","bait":"Boilie, canlı balık","note":"Meriç nehrinde yayın sezonu.","heat":4,"type":"nehir","hot":True,"source":"Demo"},
    {"id":"f18","lat":40.72000,"lng":30.20000,"loc":"Sapanca Gölü","fish":["Alabalık","Sazan","Yayın"],"rod":"Spin","bait":"Rapala, solucan","note":"Sapanca sabah alabalık harika.","heat":5,"type":"göl","hot":True,"source":"Demo"},
    {"id":"f19","lat":40.43300,"lng":29.55000,"loc":"İznik Gölü","fish":["Sazan","Levrek","Sudak"],"rod":"Feeder","bait":"Pellet, mısır","note":"İznik gölü sazan sezonu.","heat":4,"type":"göl","hot":False,"source":"Demo"},
    {"id":"f20","lat":40.39750,"lng":27.79580,"loc":"Erdek","fish":["Çipura","Karagöz","Sargoz"],"rod":"LRF","bait":"Micro jig","note":"Erdek açıkları mükemmel.","heat":4,"type":"deniz","hot":True,"source":"Demo"},
]

# ════════════════════════════════════════════════════════════════════
# ANA FONKSİYON
# ════════════════════════════════════════════════════════════════════
def main():
    print("=" * 65)
    print(f"🎣  Balık Radarı Scraper v4 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"    Claude API: {'✓ Aktif' if API_KEY else '✗ Yok (sadece RSS/scrape)'}")
    print("=" * 65)

    existing = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f).get("reports", [])
            print(f"📂 Mevcut: {len(existing)} rapor")
        except Exception as e:
            print(f"⚠ {e}")

    new_reports = []

    # 1. Claude API (en zengin kaynak)
    if API_KEY:
        new_reports += scrape_with_claude()

    # 2. Klasik scraperlar
    new_reports += scrape_google_news()
    new_reports += scrape_rss_feeds()
    new_reports += scrape_telegram_public()

    print(f"\n📊 Ham yeni: {len(new_reports)}")

    ts = now_iso()
    for r in new_reports:
        if "timestamp" not in r: r["timestamp"] = ts
        r["time"] = time_ago(r["timestamp"])

    # Yeterli veri yoksa fallback
    if len(new_reports) < 5:
        print("⚠ Yeterli veri yok — demo veri ekleniyor...")
        for r in FALLBACK:
            r["timestamp"] = ts
            r["time"] = "Az önce"
        new_reports = FALLBACK + new_reports

    # Birleştir ve kaydet
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
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "last_updated": ts,
            "total":        len(sorted_reports),
            "reports":      sorted_reports,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Tamamlandı!")
    print(f"   Yeni eklenen : {added}")
    print(f"   Toplam rapor : {len(sorted_reports)}")
    print("=" * 65)

if __name__ == "__main__":
    main()
