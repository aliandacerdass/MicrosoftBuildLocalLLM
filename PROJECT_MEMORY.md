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

**Tuzak:** `model.is_cached` bir *property*, metot değil. `is_cached()` çağırmak
`TypeError: 'bool' object is not callable` verir.

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

## Kaldığımız yer

- [x] Ortam kurulumu + Foundry Local smoke testi (GEÇTİ)
- [x] Repo iskeleti + kural dosyaları
- [ ] Bilgi tabanı dökümanları
- [ ] Çekirdek pipeline (chunking / store / ingest / retrieve)
- [ ] RAG katmanı + CLI + Streamlit
- [ ] Değerlendirme ve ayar
- [ ] Dökümantasyon + video scripti
- [ ] Video çekimi (Ali) → linki README'ye

Güncel görev listesi: `tasks.md`
