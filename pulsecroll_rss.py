import feedparser
from pulsecroll_pipeline import process_and_save_event

# Debreceni RSS csatornák listája
RSS_FEEDS = [
    "https://dehir.hu/rss",  # Dehir hír- és programcsatorna
]

def process_rss_feeds():
    print("=== RSS Adatgyűjtés indítása ===\n")
    
    for feed_url in RSS_FEEDS:
        print(f"Csatorna beolvasása: {feed_url}")
        feed = feedparser.parse(feed_url)
        
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "") or entry.get("description", "")
            link = entry.get("link", "")
            
            raw_text = f"Cím: {title}\nLeírás: {summary}"
            
            # Szűrés debreceni programkulcsszavakra
            lower_text = raw_text.lower()
            if any(keyword in lower_text for keyword in ["program", "koncert", "fesztivál", "kiállítás", "színház", "előadás"]):
                print(f"Továbbítás az AI-nak: {title}")
                try:
                    process_and_save_event(raw_text=raw_text, source_url=link)
                except Exception as e:
                    print(f"[HIBA] {e}")
                print("-" * 40)

if __name__ == "__main__":
    process_rss_feeds()