# Proje Hafızası

Kararlar, gerekçeleri ve kaldığımız yer. Kod okunarak anlaşılamayacak şeyler burada.

## Proje nedir

Microsoft summer internship programı 2026 projesi: **Foundry Local ile tamamen offline
çalışan doküman Q&A asistanı**. RAG pattern — embedding ile arama, SQLite'ta vektör
deposu, cihaz üstü LLM ile kaynağa dayalı cevap üretimi.

Teslimat: bu public repo + 3 dakikalık anlatım videosu.

## Doğrulanmış teknik gerçekler (12 Ağustos 2026, Mac M4 / arm64)

| Konu | Değer |
|---|---|
| SDK | `foundry-local-sdk==1.2.4`, saf python wheel, `>=3.11` |
| Python | 3.13 (`.venv` içinde) |
| Katalogdaki model sayısı | 47 |
| Embedding modeli | `qwen3-embedding-0.6b` → **1024 boyut**, 3 metin ≈ 0.9 sn |
| İlk smoke chat modeli | `qwen2.5-0.5b` → yükleme 1.6 sn, üretim 1.2 sn |
| Model indirme süresi | ~290 sn/model (bu bağlantıda) |
| Execution provider | Sadece `WebGpuExecutionProvider` görünüyor, **kayıtlı değil** → çıkarım CPU üzerinde |

### API akışı (1.2.4)

```python
FoundryLocalManager.initialize(Configuration(app_name="..."))
mgr = FoundryLocalManager.instance
model = mgr.catalog.get_model(alias)   # alias, örn. "qwen3-embedding-0.6b"
model.download(cb); model.load()
model.get_chat_client().complete_streaming_chat(messages)
model.get_embedding_client().generate_embeddings([...])  # resp.data[i].embedding
model.unload()
```

**Tuzak 1:** `model.is_cached` bir *property*, metot değil. `is_cached()` çağırmak
`TypeError: 'bool' object is not callable` verir.

**Tuzak 2 (önemli):** Model cache'i `app_name` başına ayrışıyor. `mslocalrag_smoke` adıyla
indirilen model, uygulama `microsoft-build-local-llm` adıyla açıldığında yok sayıldı ve
baştan indi (ölçüldü: 498 sn). Bayt paylaşımı yok. Bu yüzden app adı tek yerde,
`config.APP_NAME`'de tutuluyor ve her giriş noktası onu kullanıyor.

**Tuzak 3:** Aynı anda iki Foundry Local süreci çalışırsa ikisi de yavaşlıyor. 46 chunk'lık
ingest, arka planda model indirmesi varken 677 sn sürdü.

## Kararlar ve gerekçeleri

- **Neden 0.5B model ürün için seçilmedi:** `qwen2.5-0.5b` smoke testte "RAG" kısaltmasını
  "Retributionary Amplification Game" diye uydurdu. Hızlı ama kalitesiz. Ürün modeli
  aday karşılaştırmasıyla seçildi (bkz. `docs/EVALUATION.md`).
- **Neden SQLite + numpy, vektör DB değil:** birkaç yüz chunk için brute-force cosine
  milisaniye sürüyor; ekstra bağımlılık taşımanın karşılığı yok. Program dökümanının
  istediği de bu.
- **Neden `backends.py` seam:** testlerin model indirmeden çalışabilmesi için
  (`StubBackend`). Ürün yolu her zaman `FoundryBackend`.
- **Neden benzerlik eşiği (`MIN_SCORE`):** en iyi chunk bile alakasızsa LLM'e hiç gitmeden
  reddediyoruz. Hem halüsinasyonu kesiyor hem cevabı hızlandırıyor.
- **Bilgi tabanı içeriği:** Foundry Local / RAG / embedding / SQLite konuları. Asistan
  kendi teknolojisini anlatıyor — demoda etkileyici ve public repoda paylaşımı güvenli.

## Ölçülen sonuçlar (12 Ağustos 2026)

- Index: 55 pasaj, 7 doküman, 1024 boyut
- Retrieval hit@3: 17/17 · cevap doğruluğu: 17/17 · kapsam dışı reddetme: 5/5
- Benzerlik ayrımı: cevaplanabilir min 0.624, kapsam dışı max 0.552 → eşik 0.60
- Model seçimi: qwen2.5-1.5b (medyan 3-6 sn). phi-3.5-mini aynı kalite, ~5 kat yavaş (16 sn)
- Testler: 41 birim (modelsiz) + 4 entegrasyon (gerçek model)
- Ağ: `lsof` ile ölçüldü — cevap üretilirken dış bağlantı YOK; SDK modeli katalogda
  çözerken 2, yüklerken 1 HTTPS bağlantısı açıyor

## Kaldığımız yer

- [x] Ortam kurulumu + Foundry Local smoke testi (GEÇTİ)
- [x] Repo iskeleti + kural dosyaları
- [x] Bilgi tabanı dökümanları (7 dosya)
- [x] Çekirdek pipeline (chunking / store / ingest / retrieve)
- [x] RAG katmanı + CLI + Streamlit
- [x] Değerlendirme ve ayar → `docs/EVALUATION.md`
- [x] Dökümantasyon + video scripti
- [x] Çapraz model incelemesi (Gemini) → 3 gerçek hata bulundu ve düzeltildi
- [x] Wi-Fi kapalı offline testi — GEÇTİ: soğuk süreç 10.1 sn'de cevapladı, katalog çözümü ağsız da çalışıyor
- [ ] Video çekimi (Ali) → linki README'ye

Güncel görev listesi: `tasks.md`
