import os
import json
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from google import genai
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
genai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Javított és tesztelt debreceni források
TARGET_URLS = [
    {"name": "Debrecen.hu Programok", "url": "https://www.debrecen.hu/hu/debreceni/programok"},
    {"name": "Főnix Rendezvények", "url": "https://fonixdebrecen.hu/esemenyek/"},
    {"name": "Csokonai Színház Műsor", "url": "https://csokonaiszinhaz.hu/musor/"}
]

# Valódi böngészőt szimuláló fejlécek a blokkolás elkerülésére
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "hu-HU,hu;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache"
}

def fetch_page_text(url):
    try:
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        response.encoding = response.apparent_encoding or 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'svg', 'iframe', 'noscript']):
                tag.decompose()
            text = soup.get_text(separator=' ')
            clean_text = re.sub(r'\s+', ' ', text).strip()
            return clean_text[:25000]
        else:
            print(f" [HIBA] HTTP Status: {response.status_code} ({url})")
    except Exception as e:
        print(f" [HIBA] Nem sikerült letölteni az oldalt ({url}): {e}")
    return None

def extract_events_with_gemini(raw_text, source_name, source_url):
    if not genai_client or not raw_text:
        return []

    today_str = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""
    Te egy debreceni kulturális újságíró AI vagy. 
    A kapott weboldal szöveges tartalmából vond ki a debreceni eseményeket és műsorokat JSON tömb formátumban.

    Forrás neve: {source_name}
    Alapértelmezett URL: {source_url}
    Mai dátum referenciának: {today_str}

    KÖTELEZŐ MEZŐK MIDEN ESEMÉNYNÉL:
    1. "cim": Az esemény vagy előadás pontos neve.
    2. "datum": YYYY-MM-DD formátumú dátum.
    3. "kezdet_ido": YYYY-MM-DD HH:MM:SS formátum (pl. "2026-09-15 19:00:00"). Ha az óra hiányzik, legyen "19:00:00".
    4. "helyszin": A konkrét debreceni helyszín/intézmény neve (pl. "Csokonai Nemzeti Színház", "Kölcsey Központ", "Nagyerdei Víztorony", "Főnix Aréna", "Nagyerdei Szabadtéri Színpad"). SOHASE csak "Debrecen"!
    5. "kategoria": Szigorúan a következők egyike: "Színház", "Koncert", "Fesztivál", "Gasztro", "Vásár", "Családi", "Sport", "Kiállítás", "Előadás", "Buli".
    6. "ajanlo": 2-3 mondatos, kedvcsináló, stílusos összefoglaló magyarul.
    7. "url": Az esemény pontos webcíme (ha megtalálható), egyébként a forrás URL: {source_url}.
    8. "leiras": Tömör leírás a programról.

    Visszatérési formátum: KIZÁRÓLAG egy érvényes JSON tömb, egyéb magyarázó szöveg nélkül!

    Weboldal szövege:
    {raw_text}
    """

    try:
        response = genai_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        text_resp = response.text.strip()
        if "```json" in text_resp:
            text_resp = text_resp.split("```json")[1].split("```")[0].strip()
        elif "```" in text_resp:
            text_resp = text_resp.split("```json")[1].split("```")[0].strip()

        parsed = json.loads(text_resp)
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict) and "events" in parsed:
            return parsed["events"]
    except Exception as e:
        print(f" [HIBA] Gemini AI feldolgozási hiba ({source_name}): {e}")
    return []

def main():
    if not genai_client or not supabase:
        print("---> [HIBA] Hiányzó API kulcsok vagy adatbázis beállítások.")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"---> PulseScroll ÉLŐ debreceni adatgyűjtés indítása: {today_str}\n")

    total_saved = 0

    for target in TARGET_URLS:
        print(f"--> Letöltés: {target['name']} ({target['url']})...")
        page_text = fetch_page_text(target['url'])

        if not page_text:
            print(f"    Sikertelen letöltés, ugrás a következőre.\n")
            continue

        print(f"    Szöveg letöltve ({len(page_text)} kar.), elemzés Gemini 2.0 Flash-el...")
        events = extract_events_with_gemini(page_text, target['name'], target['url'])

        if not events:
            print(f"    Nem sikerült eseményeket kinyerni.\n")
            continue

        print(f"    {len(events)} esemény azonosítva! Mentés a Supabase adatbázisba...")

        for event in events:
            raw_date = str(event.get("datum") or today_str).strip()
            payload = {
                "cim": event.get("cim"),
                "datum": raw_date,
                "kezdet_ido": str(event.get("kezdet_ido") or f"{raw_date} 19:00:00").strip(),
                "helyszin": str(event.get("helyszin") or "Debrecen").strip(),
                "kategoria": str(event.get("kategoria") or "Előadás").strip(),
                "leiras": event.get("leiras") or "",
                "ajanlo": event.get("ajanlo") or "",
                "url": event.get("url") or target['url'],
            }

            try:
                supabase.table("esemenyek").insert(payload).execute()
                print(f"      [SIKER] Mentve: {payload['cim']} | {payload['helyszin']} | {payload['datum']}")
                total_saved += 1
            except Exception as e:
                print(f"      [HIBA] MENTÉSNÉL ({payload.get('cim')}): {e}")

        print("")

    print(f"---> ADATGYŰJTÉS BEFEJEZVE. Összesen {total_saved} új élő esemény elmentve a Supabase-be.")

if __name__ == "__main__":
    main()
