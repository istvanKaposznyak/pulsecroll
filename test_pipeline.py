import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Teszt beszúrás a helyszinek táblába
def test_connection():
    res = supabase.table("helyszinek").insert({
        "nev": "Nagyerdei Víztorony",
        "cim": "Debrecen, Pallagi út 7.",
        "akadalymentes": True
    }).execute()
    print("Kapcsolódási teszt sikeres! Létrejött rekord ID-ja:", res.data[0]["id"])

if __name__ == "__main__":
    test_connection()