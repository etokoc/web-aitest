# BIST Pano — Tamamen Ücretsiz Hisse Takip Projesi

Backend sunucusu YOK. Veri, GitHub Actions ile periyodik olarak çekilip
statik JSON dosyası olarak repoya yazılıyor; site de bu JSON'ları okuyan
saf HTML/JS. Bu sayede tamamen ücretsiz kalıyor (sunucu uyuma/soğuma
problemi yaşayan Render/Railway gibi servislere ihtiyaç yok).

## Nasıl çalışıyor
```
GitHub Actions (15 dk'da bir, cron)
   -> scripts/fetch_prices.py   (Yahoo Finance, ücretsiz, .IS tickerları)
   -> scripts/fetch_news.py     (ücretsiz RSS kaynakları + Türkçe sentiment analizi)
   -> scripts/analyze.py        (RSI/SMA + haber yoğunluğu + ortalama duygu skoru)
   -> docs/data/*.json dosyalarını commit'ler
GitHub Pages
   -> docs/ klasörünü doğrudan yayınlar (index.html bu JSON'ları fetch eder)
```

## Kurulum adımları

1. Bu klasörü yeni bir **public** GitHub reposuna push et:
   ```bash
   cd bist-panel
   git init
   git add .
   git commit -m "ilk kurulum"
   git branch -M main
   git remote add origin https://github.com/KULLANICI_ADIN/bist-panel.git
   git push -u origin main
   ```
   > Repo public olmalı — public repolarda GitHub Actions dakikaları sınırsız/ücretsiz.

2. **GitHub Pages'i aç:** Repo → Settings → Pages → "Build and deployment" →
   Source: *Deploy from a branch* → Branch: `main` → Klasör: `/docs` → Save.
   Birkaç dakika sonra siten `https://KULLANICI_ADIN.github.io/bist-panel/` adresinde yayında olur.

3. **Actions izinlerini kontrol et:** Repo → Settings → Actions → General →
   "Workflow permissions" → *Read and write permissions* seçili olsun
   (workflow'un JSON dosyalarını commit'leyebilmesi için gerekli).

4. **İlk veri çekimini elle tetikle:** Repo → Actions sekmesi →
   "BIST verilerini güncelle" → *Run workflow*. Bu, `docs/data/*.json`
   dosyalarını doldurur; ondan sonra cron otomatik devam eder.

## Yerelde test etmek istersen
```bash
pip install yfinance pandas feedparser
# Sentiment modeli icin (opsiyonel ama onerilir, ~450MB indirir):
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers

cd scripts
python fetch_prices.py
python fetch_news.py
python analyze.py
cd ../docs && python -m http.server 8000
# http://localhost:8000 adresini aç
```

## Sentiment (duygu) analizi nasıl çalışıyor?
`scripts/sentiment.py`, her haberi **pozitif / negatif / nötr** olarak etiketler:
- **Öncelikli yöntem:** HuggingFace üzerindeki ücretsiz, açık kaynak
  `savasy/bert-base-turkish-sentiment-cased` modeli (Türkçe BERT).
- **Yedek yöntem:** `transformers`/`torch` kurulu değilse veya model
  indirilemiyorsa (örn. ilk kurulumda internet yoksa), basit bir Türkçe
  kelime sözlüğüne otomatik düşer — script asla hata vermez.

Üretilen `sentiment` etiketi hem haber kartlarında rozet olarak gösterilir,
hem de `analyze.py` içinde ilgili hissenin "sinyal" skoruna dahil edilir
(haberlerin ortalama duygu tonu pozitifse skor +1, negatifse -1 etkiler).
GitHub Actions workflow'u modeli her çalıştırmada yeniden indirmemesi için
`actions/cache` ile önbelleğe alır.

## Genişletme fikirleri
- `TICKERS` listesine (scripts/fetch_prices.py) ve `TICKER_KEYWORDS`
  sözlüğüne (scripts/fetch_news.py) istediğin kadar hisse ekle.
- `analyze.py` içindeki kural tabanlı skoru zamanla gerçek bir
  scikit-learn/XGBoost modeliyle değiştirebilirsin.
- Bildirim istersen: GitHub Actions'a bir adım ekleyip, belirli bir
  sinyal oluştuğunda ücretsiz bir Telegram bot API'siyle mesaj attırabilirsin.

## Önemli not
Buradaki "sinyal" ve "AI önerisi" etiketleri kural tabanlı, basit bir
ön-analizdir; **yatırım tavsiyesi değildir**. Yahoo Finance verisi
gecikmeli olabilir; gerçek zamanlı/lisanslı veri için ücretli bir
sağlayıcıya (Foreks, Matriks vb.) geçmen gerekir.
