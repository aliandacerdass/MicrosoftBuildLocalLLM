# Sık Karşılaşılan Hatalar

Bu projede gerçekten karşılaştığımız hatalar ve çözümleri.

## `TypeError: 'bool' object is not callable`

**Nerede:** `model.is_cached()` çağırırken.

**Sebep:** `foundry-local-sdk` 1.2.4'te `is_cached` bir *property*. `is_loaded`,
`context_length`, `capabilities` da öyle.

**Çözüm:** Parantezsiz kullan → `if model.is_cached:`

## `ModuleNotFoundError: No module named 'foundry_local_sdk'`

**Sebep:** Paket kurulmamış ya da yanlış Python yorumlayıcısı kullanılıyor
(conda base vs. proje `.venv`'i).

**Çözüm:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
python -c "import foundry_local_sdk; print(foundry_local_sdk.__version__)"
```

## Model zaten indirilmişti ama yine indiriyor

**Sebep:** Foundry Local'ın model cache'i `Configuration(app_name=...)` değerine göre
ayrışıyor. Bir deneme scriptinde `app_name="deneme"` ile indirdiğin model, uygulama
`app_name="microsoft-build-local-llm"` ile açıldığında `is_cached == False` görünüyor ve
baştan iniyor.

Bu projede birebir yaşandı: smoke testte `mslocalrag_smoke` adıyla indirilen modeller
uygulamada görünmedi.

**Çözüm:** Tek bir app adı kullan. `localrag.backends.FoundryBackend` bunu tek yerde
tutuyor — deneme scriptleri de aynı adı kullanmalı:

```python
FoundryLocalManager.initialize(Configuration(app_name="microsoft-build-local-llm"))
```

Hangi modellerin gerçekten cache'te olduğunu görmek için:
`manager.catalog.get_cached_models()`

## İki süreç aynı anda model indirirse ikisi de yavaşlar

**Belirti:** `python -m localrag.ingest` dakikalarca hiçbir çıktı vermiyor.

**Sebep:** Aynı anda çalışan başka bir Foundry Local süreci model indiriyordu; ingest
sırasını bekledi. Ölçtüğümüz 46 chunk'lık ingest bu yüzden 677 saniye sürdü.

**Çözüm:** Aynı anda tek Foundry Local süreci çalıştır. Ayrıca uzun çıktıyı dosyaya
yönlendirirken Python stdout'u bloklu tamponluyor; anlık ilerleme görmek için
`python -u -m localrag.ingest` kullan.

## İlk çalıştırma çok yavaş

**Sebep:** Model ilk kullanımda indiriliyor. Ölçtüğümüz: model başına ~290 saniye.

**Çözüm:** Normal davranış. İndirme bir kere olur, sonra Foundry Local cache'inden
yüklenir (1–4 saniye). Kurulumu `python -m localrag.ingest` ile önden yapın, demo
sırasında beklemeyin.

## Cevap alakasız / model bilgi tabanını yok sayıyor

**Kontrol sırası:**
1. `python -m localrag.cli --show-context` ile retrieve edilen chunk'lara bak —
   sorun retrieval'da mı, üretimde mi?
2. Chunk'lar alakasızsa: `TOP_K` artır veya chunk boyutunu küçült
3. Chunk'lar doğru ama cevap uydurma ise: model çok küçük. `qwen2.5-0.5b` bu iş için
   yetersiz (smoke testte "RAG"i uydurdu) — `config.py`'deki chat modelini büyüt

## Her soruya "bilgi tabanımda yok" cevabı

**Sebep:** `MIN_SCORE` eşiği fazla yüksek.

**Çözüm:** `--show-context` ile gerçek benzerlik skorlarını gör, `config.py`'de
`MIN_SCORE`'u ona göre düşür. Eşiğin veriyle ayarlanması gerekir, tahminle değil.

## Veritabanı boş / "no chunks found"

**Sebep:** Ingest çalıştırılmamış ya da farklı bir DB yoluna yazmış.

**Çözüm:** `python -m localrag.ingest` çalıştır; `LOCALRAG_DB` ortam değişkeni
ayarlıysa CLI ve ingest'in aynı değeri gördüğünden emin ol.
