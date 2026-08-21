"""
BIST hisse fiyatlarini ucretsiz olarak Yahoo Finance uzerinden ceker.
Yahoo Finance'te BIST hisseleri ".IS" uzantisiyla islem gorur (orn: THYAO.IS).
Veri ~15-20 dk gecikmeli olabilir ama tamamen ucretsizdir, API key gerekmez.

Kurulum: pip install yfinance pandas
"""
import json
import time
from datetime import datetime, timezone

import yfinance as yf

# Takip edilecek hisseler - istediğin gibi genişletebilirsin
TICKERS = [
    "THYAO", "GARAN", "AKBNK", "ISCTR", "ASELS", "KCHOL", "SASA",
    "EREGL", "BIMAS", "TUPRS", "SISE", "PGSUS", "FROTO", "TCELL",
    "YKBNK", "VAKBN", "HALKB", "PETKM", "TOASO", "KOZAL",
]

OUT_PATH = "docs/data/prices.json"


def fetch_all(tickers):
    results = []
    # yfinance .IS tickerlarini toplu cekebiliyor, ama tekil cekmek
    # rate-limit acisindan daha guvenli (ucretsiz kullanimda).
    for code in tickers:
        symbol = f"{code}.IS"
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="5d", interval="1d")
            info_fast = t.fast_info  # daha hafif/hizli endpoint

            if hist.empty:
                continue

            last_close = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last_close
            change = last_close - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0.0

            results.append({
                "symbol": code,
                "price": round(last_close, 2),
                "prevClose": round(prev_close, 2),
                "change": round(change, 2),
                "changePercent": round(change_pct, 2),
                "dayHigh": round(float(hist["High"].iloc[-1]), 2),
                "dayLow": round(float(hist["Low"].iloc[-1]), 2),
                "volume": int(hist["Volume"].iloc[-1]),
                "history": [
                    {
                        "date": idx.strftime("%Y-%m-%d"),
                        "open": round(float(row["Open"]), 2),
                        "high": round(float(row["High"]), 2),
                        "low": round(float(row["Low"]), 2),
                        "close": round(float(row["Close"]), 2),
                    }
                    for idx, row in hist.iterrows()
                ],
            })
        except Exception as e:
            print(f"[UYARI] {code} cekilemedi: {e}")
        time.sleep(0.3)  # nazik ol, rate limit yeme

    return results


def main():
    data = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "stocks": fetch_all(TICKERS),
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"{len(data['stocks'])} hisse yazildi -> {OUT_PATH}")


if __name__ == "__main__":
    main()
