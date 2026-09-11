from supabase import create_client
from datetime import datetime, timedelta

SUPABASE_URL = "https://lhoozpsyhwmoqtmgxipe.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxob296cHN5aHdtb3F0bWd4aXBlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg3MDAwNjUsImV4cCI6MjEwNDI3NjA2NX0.sWap7Ka6igDGHK6nzyC1C46TTRIhDHA7298ME1hKq8o"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

today = datetime.now()
today_str = today.strftime("%Y-%m-%d")
tomorrow_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")
weekend_str = (today + timedelta(days=(5 - today.weekday() + 7) % 7)).strftime("%Y-%m-%d")

mintak = [
    {
        "cim": "Örkény István: Tóték",
        "datum": today_str,
        "kezdet_ido": f"{today_str} 19:00:00",
        "helyszin": "Csokonai Nemzeti Színház",
        "kategoria": "Színház",
        "leiras": "Örkény István legismertebb drámája a II. világháború idején játszódik, ahol a Tót család mindent megtesz a fiuk parancsnokaként érkező őrnagy kedvéért.",
        "ajanlo": "Örkény drámája lélektani mélységgel és fanyar humorral szembesít minket a Csokonai Színház felújított színpadán. Kiváló színházi élmény az igényes dráma kedvelőinek.",
        "url": "https://csokonaiszinhaz.hu"
    },
    {
        "cim": "Debreceni Bor- és Gasztrokorzó",
        "datum": tomorrow_str,
        "kezdet_ido": f"{tomorrow_str} 16:00:00",
        "helyszin": "Kossuth tér",
        "kategoria": "Gasztro",
        "leiras": "Többnapos szabadtéri gasztronómiai fesztivál borkóstolókkal, kézműves vásárral és kulturális fellépőkkel Debrecen Kossuth terén.",
        "ajanlo": "Az ország legjelesebb pincészetei és a régió elismert kézműves konyhái költöznek Debrecen főterére. Tökéletes esti kikapcsolódás élőzenével és koccintással.",
        "url": "https://www.debrecen.hu"
    },
    {
        "cim": "Nagyerdei Jazz és Akusztik Est",
        "datum": weekend_str,
        "kezdet_ido": f"{weekend_str} 20:00:00",
        "helyszin": "Nagyerdei Víztorony",
        "kategoria": "Koncert",
        "leiras": "Szabadtéri élőzenei koncert a Nagyerdei Víztorony kerthelyiségében, ahol a hazai jazz szféra kiemelkedő tehetségei lépnek színpadra.",
        "ajanlo": "A Nagyerdő lombkoronái alatt felcsendülő finom jazz és akusztikus dallamok tökéletes hétvégi hangulatot teremtenek a Víztorony kertjében.",
        "url": "https://nagyerdeiviztorony.hu"
    }
]

print("Adatbázis frissítése kategóriákkal...")
try:
    supabase.table("esemenyek").delete().neq("id", 0).execute()
except Exception as e:
    print("Ürítési infó:", e)

for elem in mintak:
    try:
        supabase.table("esemenyek").insert(elem).execute()
        print(f" [OK] Mentve: {elem['cim']} -> Kategória: {elem['kategoria']}")
    except Exception as e:
        print(f" [HIBA] {elem['cim']}: {e}")