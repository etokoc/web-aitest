"""
Haber basliklarini pozitif / negatif / notr olarak etiketler.

Iki katmanli calisir:
1) Once HuggingFace'teki hazir Turkce BERT sentiment modelini (ucretsiz,
   acik kaynak) yuklemeyi dener: savasy/bert-base-turkish-sentiment-cased
2) Model indirilemezse (internet yok, ilk kurulum, vb.) basit bir
   Turkce kelime sozlugune (lexicon) dusup calismaya devam eder,
   boylece script hicbir zaman patlamaz.

Kurulum (tam model icin, opsiyonel ama onerilir):
    pip install transformers torch --index-url https://download.pytorch.org/whl/cpu
"""

_pipeline = None
_MODEL_NAME = "savasy/bert-base-turkish-sentiment-cased"

# Fallback: basit Turkce duygu sozlugu (model yuklenemezse kullanilir)
POSITIVE_WORDS = [
    "artış", "artis", "yükseldi", "yukseldi", "rekor", "kazanç", "kazanc",
    "büyüme", "buyume", "ihracat", "anlaşma", "anlasma", "iyileşme",
    "iyilesme", "başarı", "basari", "olumlu", "güçlü", "guclu", "yatırım",
    "yatirim", "kâr", "kar", "yükseliş", "yukselis", "onay", "genişleme",
    "genisleme", "ödül", "odul", "prim", "temettü", "temettu", "zirve",
]
NEGATIVE_WORDS = [
    "düşüş", "dusus", "düştü", "dustu", "zarar", "kriz", "iflas",
    "gerileme", "kayıp", "kayip", "ceza", "soruşturma", "sorusturma",
    "olumsuz", "risk", "daralma", "durgunluk", "iptal", "grev",
    "kesinti", "temerrüt", "temerrut", "dava", "skandal", "resesyon",
    "enflasyon", "faiz artışı", "faiz artisi",
]


def _lexicon_sentiment(text):
    t = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in t)
    neg = sum(1 for w in NEGATIVE_WORDS if w in t)
    if pos == 0 and neg == 0:
        return {"label": "nötr", "score": 0.0, "engine": "lexicon"}
    net = pos - neg
    total = pos + neg
    score = round(net / total, 2)
    if score > 0.15:
        label = "pozitif"
    elif score < -0.15:
        label = "negatif"
    else:
        label = "nötr"
    return {"label": label, "score": score, "engine": "lexicon"}


def _get_pipeline():
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    try:
        from transformers import pipeline
        _pipeline = pipeline(
            "sentiment-analysis",
            model=_MODEL_NAME,
            tokenizer=_MODEL_NAME,
        )
    except Exception as e:
        print(f"[UYARI] Sentiment modeli yüklenemedi, lexicon'a düşülüyor: {e}")
        _pipeline = False  # bir daha denemesin
    return _pipeline


def analyze_sentiment(text):
    """Tek bir metin icin {'label': 'pozitif'|'negatif'|'nötr', 'score': float, 'engine': str} dondurur."""
    if not text or not text.strip():
        return {"label": "nötr", "score": 0.0, "engine": "none"}

    pipe = _get_pipeline()
    if pipe:
        try:
            result = pipe(text[:512])[0]
            raw_label = result["label"].lower()
            score = round(float(result["score"]), 2)
            if "pos" in raw_label or raw_label == "label_1":
                label = "pozitif"
            elif "neg" in raw_label or raw_label == "label_0":
                label = "negatif"
            else:
                label = "nötr"
            # negatifse skoru eksi yap, boylece -1..1 araliginda tek bir eksen olsun
            signed_score = score if label == "pozitif" else (-score if label == "negatif" else 0.0)
            return {"label": label, "score": round(signed_score, 2), "engine": "bert"}
        except Exception as e:
            print(f"[UYARI] Model ile analiz basarisiz, lexicon'a düşülüyor: {e}")

    return _lexicon_sentiment(text)


def analyze_batch(texts):
    return [analyze_sentiment(t) for t in texts]
