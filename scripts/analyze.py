"""
prices.json ve news.json dosyalarini okuyup her hisse icin basit bir
teknik + haber-yogunluk skoru uretir. Bu bir YATIRIM TAVSIYESI DEGILDIR,
sadece kural tabanli bir on-analiz katmanidir. Istersen ileride bu dosyayi
gercek bir ML modeliyle (orn. scikit-learn) degistirebilirsin.

Kurulum: pip install pandas
"""
import json
from datetime import datetime, timezone

PRICES_PATH = "docs/data/prices.json"
NEWS_PATH = "docs/data/news.json"
OUT_PATH = "docs/data/analysis.json"


def sma(values, window):
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def score_stock(stock, news_count, avg_sentiment):
    closes = [d["close"] for d in stock.get("history", [])]
    sma3 = sma(closes, 3)
    rsi_val = rsi(closes)
    change_pct = stock.get("changePercent", 0)

    score = 0
    reasons = []

    if sma3 and stock["price"] > sma3:
        score += 1
        reasons.append("Fiyat kısa vadeli ortalamanın üzerinde")
    elif sma3:
        score -= 1
        reasons.append("Fiyat kısa vadeli ortalamanın altında")

    if rsi_val is not None:
        if rsi_val < 30:
            score += 1
            reasons.append(f"RSI {rsi_val} - aşırı satım bölgesi")
        elif rsi_val > 70:
            score -= 1
            reasons.append(f"RSI {rsi_val} - aşırı alım bölgesi")

    if change_pct > 2:
        score += 1
        reasons.append("Günlük değişim güçlü pozitif")
    elif change_pct < -2:
        score -= 1
        reasons.append("Günlük değişim güçlü negatif")

    if news_count >= 3:
        reasons.append(f"Son dönemde {news_count} haberde geçiyor (yüksek gündem)")

    if avg_sentiment is not None and news_count > 0:
        if avg_sentiment > 0.2:
            score += 1
            reasons.append(f"Haber duygu tonu pozitif (ort. {avg_sentiment:+.2f})")
        elif avg_sentiment < -0.2:
            score -= 1
            reasons.append(f"Haber duygu tonu negatif (ort. {avg_sentiment:+.2f})")
        else:
            reasons.append(f"Haber duygu tonu nötr (ort. {avg_sentiment:+.2f})")

    if score >= 2:
        label = "İzlenebilir (pozitif sinyal)"
    elif score <= -2:
        label = "Dikkatli olunmalı (negatif sinyal)"
    else:
        label = "Nötr"

    return {
        "symbol": stock["symbol"],
        "label": label,
        "score": score,
        "rsi": rsi_val,
        "sma3": round(sma3, 2) if sma3 else None,
        "newsCount": news_count,
        "avgSentiment": round(avg_sentiment, 2) if avg_sentiment is not None else None,
        "reasons": reasons,
        "disclaimer": "Bu bir yatırım tavsiyesi değildir; kural tabanlı otomatik bir ön analizdir.",
    }


def main():
    with open(PRICES_PATH, encoding="utf-8") as f:
        prices = json.load(f)
    try:
        with open(NEWS_PATH, encoding="utf-8") as f:
            news = json.load(f)
    except FileNotFoundError:
        news = {"items": []}

    news_count_by_ticker = {}
    sentiment_sum_by_ticker = {}
    for item in news.get("items", []):
        sent_score = item.get("sentimentScore", 0.0) or 0.0
        for t in item.get("tickers", []):
            news_count_by_ticker[t] = news_count_by_ticker.get(t, 0) + 1
            sentiment_sum_by_ticker[t] = sentiment_sum_by_ticker.get(t, 0.0) + sent_score

    def avg_sentiment_for(symbol):
        count = news_count_by_ticker.get(symbol, 0)
        if count == 0:
            return None
        return sentiment_sum_by_ticker.get(symbol, 0.0) / count

    analysis = [
        score_stock(
            s,
            news_count_by_ticker.get(s["symbol"], 0),
            avg_sentiment_for(s["symbol"]),
        )
        for s in prices.get("stocks", [])
    ]

    out = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "analysis": analysis,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"{len(analysis)} hisse analiz edildi -> {OUT_PATH}")


if __name__ == "__main__":
    main()
