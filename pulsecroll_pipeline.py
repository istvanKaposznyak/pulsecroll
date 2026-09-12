import os
import json
import re
from datetime import datetime, timedelta
from google import genai
from supabase import create_client, Client

# ==============================================================================
# 1. BEÁLLÍTÁSOK ÉS KÖRNYEZETI VÁLTOZÓK (LOKÁLIS + GITHUB ACTIONS)
# ==============================================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lhoozpsyhwmoqtmgxipe.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxob296cHN5aHdtb3F0bWd4aXBlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg3MDAwNjUsImV4cCI6MjEwNDI3NjA2NX0.sWap7Ka6igDGHK6nzyC1C46TTRIhDHA7298ME1hKq8o")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def clean_html(raw_html):
    if not raw_html:
        return ""
    text = re.sub(r'<(script|style|header|footer|nav)[^>]*>.*?</\1>', ' ', str(raw_html), flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def process_and_save_event_list(raw_data=None, raw_text=None, **kwargs):
    if not genai_client:
        print("---> [INFO] Nincs GEMINI_API_KEY környezeti változó beállítva.")
        return

    content = raw_text if raw_text is not None else raw_data
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")

    events = []

    if content:
        clean_content = clean_html(content)
        prompt = f"""
        Te egy debreceni kulturális újságíró AI vagy. 
        A kapott weboldal-tartalomból vond ki a debreceni eseményeket JSON tömb formátumban.

        Mai dátum referenciának: {today_str}

        KÖTELEZŐ MEZŐK:
        1. "cim": Az esemény pontos neve.
        2. "datum": YYYY-MM-DD formátumú dátum (pl. "{today_str}").
        3. "kezdet_ido": YYYY-MM-DD HH:MM:SS formátumban (pl. "{today_str} 19:00:00").
        4. "helyszin": A konkrét debreceni intézmény neve (pl. "Csokonai Nemzeti Színház", "Kölcsey Központ", "Nagyerdei Víztorony", "DEAC Sportcampus"). SOHASE csak "Debrecen"!
        5. "kategoria": Szigorúan a következők egyike: "Színház", "Koncert", "Fesztivál", "Gasztro", "Vásár", "Családi", "Sport", "Kiállítás", "Előadás", "Buli".
        6. "ajanlo": 2-3 mondatos egyedi, stílusos kedvcsináló magyarul.
        7. "url": Az esemény linkje.
        8. "leiras": Tömör összefoglaló.

        Tartalom:
        {clean_content[:25000]}
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
                text_resp = text_resp.split("```")[1].split("```")[0].strip()

            parsed = json.loads(text_resp)
            if isinstance(parsed, list):
                events = parsed
            elif isinstance(parsed, dict) and "events" in parsed:
                events = parsed["events"]
        except Exception as e:
            print(f"Gemini AI feldolgozás értesítés: {e}")

    if not events:
        print("---> Weboldal tartalom hiányában a mintaprogramok maradnak az adatbázisban.")
        return

    print(f"\n---> {len(events)} élő esemény mentése a Supabase adatbázisba...")

    for event in events:
        raw_date = str(event.get("datum") or today_str).strip()
        payload = {
            "cim": event.get("cim"),
            "datum": raw_date,
            "kezdet_ido": str(event.get("kezdet_ido") or f"{raw_date} 19:00:00").strip(),
            "helyszin": str(event.get("helyszin") or "Csokonai Nemzeti Színház").strip(),
            "kategoria": str(event.get("kategoria") or "Színház").strip(),
            "leiras": event.get("leiras") or "",
            "ajanlo": event.get("ajanlo") or "",
            "url": event.get("url") or "",
        }

        try:
            supabase.table("esemenyek").insert(payload).execute()
            print(f" [SIKER] Betöltve: {payload['cim']} | {payload['kategoria']} | Dátum: {payload['datum']}")
        except Exception as e:
            print(f" [HIBA] {payload['cim']}: {e}")