import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from pulsecroll_pipeline import process_and_save_event_list

TARGET_URLS = [
    "https://www.programturizmus.hu/ajanlat-debreceni-programok-fesztivalok-rendezvenyek-esemenyek.html",
    "https://visitdebrecen.com/hu/hot-now/",
    "https://debreceniprogramok.com/hu"
]

def scrape_url(url: str):
    print(f"\n==================================================")
    print(f" Böngészős adatgyűjtés: {url}")
    print(f"==================================================\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, timeout=45000, wait_until="networkidle")
            time.sleep(3)
            html_content = page.content()
        except Exception as e:
            print(f"[HIBA] Nem sikerült betölteni az oldalt ({url}): {e}")
            browser.close()
            return
            
        browser.close()

    soup = BeautifulSoup(html_content, "html.parser")
    
    # Felesleges elemek eltávolítása a szövegből
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    clean_text = soup.get_text(separator="\n", strip=True)
    
    # Az egész oldal szövege (max 15.000 karakter) egyben megy az AI-nak
    truncated_text = clean_text[:15000]
    
    print("A teljes oldal feldolgozása egyetlen AI kéréssel...")
    try:
        total_saved = process_and_save_event_list(raw_text=truncated_text, source_url=url)
        print(f"=== Befejezve: {url} | Új mentett események: {total_saved} ===")
    except Exception as e:
        print(f"[HIBA] A feldolgozás nem sikerült: {e}")

if __name__ == "__main__":
    for url in TARGET_URLS:
        scrape_url(url)
        print("Szünet a következő oldal előtt...")
        time.sleep(10)