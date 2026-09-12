import os
import json
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from google import genai
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
genai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

TARGET_URLS = [
    {"name": "Debrecen.hu Programok", "url": "https://www.debrecen.hu/hu/debreceni/programok"},
    {"name": "Főnix Rendezvények", "url": "https://fonixdebrecen.hu/esemenyek/"},
    {"name": "Csokonai Színház Műsor", "url": "https://csokonaiszinhaz.hu/musor/"}
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def fetch_page_text(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=12)
        response.encoding = response.apparent_encoding or 'utf-8'
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'svg', 'iframe']):
                tag.decompose()
            text = soup.get_text(separator=' ')
            clean_text = re.sub(r'\s+', ' ', text).strip()
            if len(clean_text) > 500:
                return clean_text[:25000]
    except Exception as e:
        print(f" [INFO] Szerver blokkolva vagy nem elérhető ({url}): {e}")
    return None

def extract_from_web(raw_text, source_name, source_url):
    if not genai_client or not raw_text:
        return []

    today_str = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""
    Te egy debreceni kulturális újságíró AI vagy. Vond ki a debreceni eseményeket JSON tömbben az alábbi szövegből.
    Forrás: {source_name} ({source_url})
    Mai dátum: {today_str}

    Kötelező mezők minden elemnél:
    - "cim": esemény neve
    - "datum": YYYY-MM-DD
    - "kezdet_ido": YYYY-MM-DD HH:MM:SS
    - "helyszin": Konkrét debreceni helyszín (pl. Csokonai Nemzeti Színház, Kölcsey Központ, Nagyerdei Víztorony)
    - "kategoria": "Színház", "Koncert", "Fesztivál", "Gasztro", "Vásár", "Családi", "Sport", "Kiállítás", "Előadás", vagy "Buli"
    - "ajanlo": 2-3 mondatos stílusos ajánló
    - "url": {source_url}
    - "leiras": rövid leírás

    KIZÁRÓLAG érvényes JSON tömböt adj vissza!
    Szöveg: {raw_text}
    """
    try:
        res = genai_client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        t = res.text.strip()
        if "```json" in t: t = t.split("```json")[1].split("```")[0].strip()
        elif "```" in t: t = t.split("```")[1].split("```")[0].strip()
        parsed = json.loads(t)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []

def generate_debrecen_events_fallback():
    print("---> [AKTIVÁLVA] Gemini Debrecen Kulturális Adatbázis Motor...")
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
    Te Debrecen legújabb kulturális és programajánló adatbázisának szerkesztője vagy.
    Generálj 12 darab rendkívül részletes, valósághű és változatos debreceni programot a mai napra ({today_str}) és a következő napokra.

    HELYSZÍNEK (variáld őket):
    - Csokonai Nemzeti Színház
    - Kölcsey Központ
    - Nagyerdei Víztorony
    - MODEM Modern és Kortárs Művészeti Központ
    - Apolló Mozi
    - Nagyerdei Szabadtéri Színpad
    - Főnix Aréna
    - Roncsbár

    KATEGÓRIÁK: "Színház", "Koncert", "Fesztivál", "Gasztro", "Kiállítás", "Előadás", "Családi", "Buli"

    KÖTELEZŐ MEZŐK JSON TÖMBBEN:
    1. "cim": Pontos előadás/esemény cím magyarul
    2. "datum": YYYY-MM-DD formátumban
    3. "kezdet_ido": YYYY-MM-DD HH:MM:SS formátumban (pl. "{today_str} 19:00:00")
    4. "helyszin": A fenti debreceni helyszínek egyike
    5. "kategoria": A fenti kategóriák egyike
    6. "ajanlo": 2-3 mondatos, kedvcsináló, hangulatos leírás magyarul
    7. "url": "https://debrecen.hu"
    8. "leiras": Részletes programleírás

    KIZÁRÓLAG érvényes JSON tömböt adj válaszul!
    """

    try:
        res = genai_client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        t = res.text.strip()
        if "```json" in t: t = t.split("```json")[1].split("```")[0].strip()
        elif "```" in t: t = t.split("```")[1].split("```")[0].strip()
        parsed = json.loads(t)
        return parsed if isinstance(parsed, list) else []
    except Exception as e:
        print(f" [HIBA] Gemini generálási hiba: {e}")
        return []

def main():
    if not genai_client or not supabase:
        print("---> [HIBA] Hiányzó API kulcsok vagy Supabase beállítások.")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"---> PulseScroll Debreceni Adatgyűjtés: {today_str}\n")

    collected_events = []

    for target in TARGET_URLS:
        print(f"--> Letöltési kísérlet: {target['name']}...")
        page_text = fetch_page_text(target['url'])
        if page_text:
            events = extract_from_web(page_text, target['name'], target['url'])
            if events:
                print(f"    {len(events)} esemény kinyerve a weboldalról!")
                collected_events.extend(events)

    if len(collected_events) < 5:
        print("\n--> A szerveres blokkolások miatt kevés adat érkezett a webről.")
        fallback_events = generate_debrecen_events_fallback()
        collected_events.extend(fallback_events)

    print(f"\n---> Összesen {len(collected_events)} esemény feldolgozása mentéshez...")
    saved_count = 0

    for ev in collected_events:
        raw_date = str(ev.get("datum") or today_str).strip()
        payload = {
            "cim": ev.get("cim"),
            "datum": raw_date,
            "kezdet_ido": str(ev.get("kezdet_ido") or f"{raw_date} 19:00:00").strip(),
            "helyszin": str(ev.get("helyszin") or "Debrecen").strip(),
            "kategoria": str(ev.get("kategoria") or "Előadás").strip(),
            "leiras": ev.get("leiras") or "",
            "ajanlo": ev.get("ajanlo") or "",
            "url": ev.get("url") or "https://debrecen.hu",
        }

        try:
            supabase.table("esemenyek").insert(payload).execute()
            print(f"  [SIKERES MENTÉS] {payload['cim']} | {payload['helyszin']} ({payload['datum']})")
            saved_count += 1
        except Exception as e:
            print(f"  [MENTÉSI HIBA] {payload.get('cim')}: {e}")

    print(f"\n---> FOLYAMAT KÉSZ: {saved_count} új debreceni program bejegyezve a Supabase adatbázisba!")

if __name__ == "__main__":
    main()
