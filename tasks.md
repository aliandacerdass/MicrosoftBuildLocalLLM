# Görevler

Durum: `[ ]` yapılacak · `[~]` devam ediyor · `[x]` bitti

## Faz 0 — Ortam

- [x] Repoyu klonla, `.venv` kur, bağımlılıkları yükle
- [x] Foundry Local smoke testi: katalog listesi + gerçek chat + gerçek embedding
- [x] `.gitignore`, `requirements.txt`, `rules.md`, `PROJECT_MEMORY.md`, `COMMON_ERRORS.md`

## Faz 1 — Bilgi tabanı

- [x] `data/docs/` altına 7 markdown dosya (kendi özetlerimiz + kaynak linkleri)

## Faz 2 — Çekirdek pipeline

- [x] `config.py` — model aliasları, top_k, eşik, yollar (env ile ezilebilir)
- [x] `backends.py` — `FoundryBackend` + `StubBackend`
- [x] `chunking.py` — markdown başlık-duyarlı bölme, örtüşmeli
- [x] `store.py` — SQLite şema, embedding float32 BLOB, içerik hash'i ile idempotent
- [x] `ingest.py` — docs → chunk → batch embed → SQLite
- [x] `retrieve.py` — numpy cosine top-k
- [x] Birim testler (model gerekmeden yeşil)

## Faz 3 — RAG + arayüz

- [x] `rag.py` — system prompt, numaralı bağlam, atıf, düşük skorda reddetme
- [x] `cli.py` — REPL, `--show-context`
- [x] `ui.py` — Streamlit, streaming cevap, kaynak paneli

## Faz 4 — Değerlendirme

- [x] `tests/eval/questions.yaml` — 22 soru (17 cevaplanabilir + 5 cevaplanamaz)
- [x] Aday chat modellerini karşılaştır (kalite / hız) → ürün modelini seç
- [x] hit@3, reddetme doğruluğu, latency ölç → `top_k`, chunk boyutu, `MIN_SCORE` ayarla
- [x] `docs/EVALUATION.md` — gerçek sayılarla

## Faz 5 — Dökümantasyon

- [x] `README.md` (EN) — kurulum, çalıştırma, mimari, ekran görüntüsü, sınırlamalar
- [x] Mimari dökümanı — `data/docs/07-project-architecture.md` (bilgi tabanının parçası, asistan kendini anlatabiliyor)
- [x] `docs/LEARNING_NOTES.md` (TR)
- [x] `docs/VIDEO_SCRIPT.md` (TR, 3 dk, sahne sahne)

## Faz 6 — Teslim

- [~] Offline doğrulama — `lsof` ile ölçüldü (üretim sırasında bağlantı yok, katalog çözümünde var). Wi-Fi kapalı testi Ali'de
- [x] Çapraz model kod incelemesi
- [x] Türkçe commitler, `main`'e push
- [ ] Video çekimi (Ali) → link README'ye
