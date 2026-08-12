# Görevler

Durum: `[ ]` yapılacak · `[~]` devam ediyor · `[x]` bitti

## Faz 0 — Ortam

- [x] Repoyu klonla, `.venv` kur, bağımlılıkları yükle
- [x] Foundry Local smoke testi: katalog listesi + gerçek chat + gerçek embedding
- [x] `.gitignore`, `requirements.txt`, `rules.md`, `PROJECT_MEMORY.md`, `COMMON_ERRORS.md`

## Faz 1 — Bilgi tabanı

- [ ] `data/docs/` altına 6–8 markdown dosya (kendi özetlerimiz + kaynak linkleri)

## Faz 2 — Çekirdek pipeline

- [ ] `config.py` — model aliasları, top_k, eşik, yollar (env ile ezilebilir)
- [ ] `backends.py` — `FoundryBackend` + `StubBackend`
- [ ] `chunking.py` — markdown başlık-duyarlı bölme, örtüşmeli
- [ ] `store.py` — SQLite şema, embedding float32 BLOB, içerik hash'i ile idempotent
- [ ] `ingest.py` — docs → chunk → batch embed → SQLite
- [ ] `retrieve.py` — numpy cosine top-k
- [ ] Birim testler (model gerekmeden yeşil)

## Faz 3 — RAG + arayüz

- [ ] `rag.py` — system prompt, numaralı bağlam, atıf, düşük skorda reddetme
- [ ] `cli.py` — REPL, `--show-context`
- [ ] `ui.py` — Streamlit, streaming cevap, kaynak paneli

## Faz 4 — Değerlendirme

- [ ] `tests/eval/questions.yaml` — ~15 soru (cevaplanabilir + cevaplanamaz)
- [ ] Aday chat modellerini karşılaştır (kalite / hız) → ürün modelini seç
- [ ] hit@3, reddetme doğruluğu, latency ölç → `top_k`, chunk boyutu, `MIN_SCORE` ayarla
- [ ] `docs/EVALUATION.md` — gerçek sayılarla

## Faz 5 — Dökümantasyon

- [ ] `README.md` (EN) — kurulum, çalıştırma, mimari, ekran görüntüsü, sınırlamalar
- [ ] `docs/ARCHITECTURE.md` (EN, mermaid diyagram)
- [ ] `docs/LEARNING_NOTES.md` (TR)
- [ ] `docs/VIDEO_SCRIPT.md` (TR, 3 dk, sahne sahne)

## Faz 6 — Teslim

- [ ] Wi-Fi kapalıyken offline doğrulama
- [ ] Çapraz model kod incelemesi
- [ ] Türkçe commitler, `main`'e push
- [ ] Video çekimi (Ali) → link README'ye
