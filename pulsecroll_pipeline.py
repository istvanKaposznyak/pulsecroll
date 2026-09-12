import os
import json
import re
from datetime import datetime
from google import genai
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
genai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def clean_html(raw_html):
    if not raw_html:
        return ""
    text = re.sub(r'<(script|style|header|footer|nav)[^>]*>.*?</\1>', ' ', str(raw_html), flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def main():
    if not genai_client or not supabase:
        print("---> [HIBA] Hiányzó API kulcsok vagy adatbázis beállítások.")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"---> PulseScroll automatikus adatgyűjtés indítása: {today_str}")

    prompt = f"""
    Te egy debreceni kulturális újságíró AI vagy.
    Generálj 3 aktuális, valósághű debreceni programajánlót a mai napra ({today_str}) JSON tömb formátumban.

    KÖTELEZŐ MEZŐK:
    1. "cim": Az esemény neve.
    2. "datum": YYYY-MM-DD formátum (pl. "{today_str}").
    3. "kezdet_ido": YYYY-MM-DD HH:MM:SS formátum (pl. "{today_str} 19:00:00").
    4. "helyszin": Konkrét debreceni helyszín (pl. "Csokonai Nemzeti Színház", "Kölcsey Központ", "Nagyerdei Víztorony").
    5. "kategoria": "Színház", "Koncert", "Fesztivál", "Gasztro", "Családi" vagy "Előadás".
    6. "ajanlo": 2-3 mondatos hangulatos kedvcsináló.
    7. "url": "https://debrecen.hu"
    8. "leiras": Rövid leírás.
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

        events = json.loads(text_resp)
        print(f"---> {len(events)} esemény sikeresen feldolgozva a Gemini AI által.")

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
            supabase.table("esemenyek").insert(payload).execute()
            print(f" [SIKER] Mentve az adatbázisba: {payload['cim']}")

    except Exception as e:
        print(f"---> [HIBA] A folyamat során hiba történt: {e}")

if __name__ == "__main__":
    main()
