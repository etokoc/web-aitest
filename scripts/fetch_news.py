"""
Ucretsiz RSS kaynaklarindan borsa/finans haberlerini ceker ve
basit anahtar kelime eslesmesiyle hangi hisseyle ilgili olabilecegini etiketler.

Kurulum: pip install feedparser
"""
import json
import re
from datetime import datetime, timezone

import feedparser

from sentiment import analyze_sentiment

# Ucretsiz, herkese acik RSS kaynaklari (istedigin kadar ekleyebilirsin)
RSS_FEEDS = [
    "https://www.bloomberght.com/rss",
    "https://www.dunya.com/rss?sectionId=finans",
    "https://www.aa.com.tr/tr/rss/default?cat=ekonomi",
]

# Hisse kodu -> haberde gecebilecek anahtar kelimeler
TICKER_KEYWORDS = {
    "THYAO": ["THY", "Türk Hava Yolları", "Turkish Airlines"],
    "GARAN": ["Garanti BBVA", "Garanti Bankası"],
    "AKBNK": ["Akbank"],
    "ISCTR": ["İş Bankası", "Isbank"],
    "ASELS": ["Aselsan"],
    "KCHOL": ["Koç Holding"],
    "SASA": ["Sasa Polyester"],
    "EREGL": ["Erdemir"],
    "BIMAS": ["BİM", "Bim Mağazalar"],
    "TUPRS": ["Tüpraş"],
    "SISE": ["Şişecam"],
    "PGSUS": ["Pegasus"],
    "FROTO": ["Ford Otosan"],
    "TCELL": ["Turkcell"],
    "YKBNK": ["Yapı Kredi"],
    "VAKBN": ["VakıfBank"],
    "HALKB": ["Halkbank"],
    "PETKM": ["Petkim"],
    "TOASO": ["Tofaş"],
    "KOZAL": ["Koza Altın"],
}

OUT_PATH = "docs/data/news.json"
MAX_ITEMS = 80


def tag_tickers(text):
    tagged = []
    for code, keywords in TICKER_KEYWORDS.items():
        if any(re.search(re.escape(kw), text, re.IGNORECASE) for kw in keywords):
            tagged.append(code)
    return tagged


def fetch_all():
    items = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:40]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                full_text = f"{title} {summary}"
                sentiment = analyze_sentiment(full_text)
                items.append({
                    "title": title,
                    "summary": summary[:300],
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "source": feed.feed.get("title", url),
                    "tickers": tag_tickers(full_text),
                    "sentiment": sentiment["label"],
                    "sentimentScore": sentiment["score"],
                })
        except Exception as e:
            print(f"[UYARI] {url} okunamadi: {e}")

    # en yeni haberleri one al (RSS siralamasi genelde zaten yeniden eskiye)
    return items[:MAX_ITEMS]


def main():
    data = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "items": fetch_all(),
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"{len(data['items'])} haber yazildi -> {OUT_PATH}")


if __name__ == "__main__":
    main()
