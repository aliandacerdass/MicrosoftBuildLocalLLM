# Proje Kuralları

Bu dosya projenin değişmez kurallarını tutar. Kod yazan herkes (insan veya AI) buna uyar.

## 1. Public repo güvenliği

Bu repo **herkese açık**. Aşağıdakiler asla commit edilmez:

- API anahtarı, token, parola, sertifika (bu proje hiçbirini kullanmıyor — tamamen local çalışır, cloud hesabı gerekmez)
- `.env` dosyaları
- Üretilen veritabanı dosyaları (`*.db`) — `data/index/` altında tutulur, `.gitignore`'da
- İndirilen model dosyaları — Foundry Local bunları kendi cache'inde tutar, repoya girmez
- Kişisel veri, özel ders notları, üçüncü kişilere ait içerik

Push öncesi zorunlu kontrol: `git diff --cached` gözden geçirilir.

## 2. Telif

`data/docs/` altındaki bilgi tabanı dosyaları **kendi özetlerimizdir**. Microsoft Learn veya
blog metinleri kelimesi kelimesine kopyalanmaz; her dosyanın başında kaynak linki verilir.

## 3. "Offline" iddiası ciddiye alınır

Projenin temel iddiası internet olmadan çalışmasıdır. Bu yüzden:

- Çalışma zamanında hiçbir bulut API'si çağrılmaz (embedding de, üretim de cihaz üstünde)
- Tek istisna: modellerin **ilk indirilmesi** internet gerektirir. Bu kurulum adımıdır,
  çalışma zamanı değil — README'de açıkça yazar
- Bu iddia her sürümde Wi-Fi kapalıyken bir soru sorularak test edilir

## 4. Kod standardı

- Python 3.11+, tip ipuçları (type hints) kullanılır
- Her modülün tek bir sorumluluğu vardır (`chunking`, `store`, `retrieve`, `rag` ayrı)
- Spekülatif soyutlama yok: istenmeyen özellik, kullanılmayan "esneklik" eklenmez
- Yorumlar *neden*'i anlatır, *ne*'yi değil
- Ayarlanabilir her şey `config.py`'de toplanır ve ortam değişkeni ile ezilebilir

## 5. Test

- `pytest` model indirmeden çalışır (`StubBackend` sayesinde) — CI dostu ve hızlı
- Gerçek modelle çalışan değerlendirme testleri `-m slow` ile işaretlenir
- **Yeşil test ürünün çalıştığını kanıtlamaz.** Her teslimattan önce gerçek modelle
  uçtan uca elle demo yapılır

## 6. Commit

- Commit mesajları **Türkçe**, emir kipi: `retrieval: cosine benzerliği numpy'a taşındı`
- Bir commit tek bir mantıksal değişiklik içerir
- `main` dalına push edilir

## 7. Dil

- `README.md` ve `docs/ARCHITECTURE.md` → İngilizce (program değerlendiricisi için)
- `rules.md`, `PROJECT_MEMORY.md`, `tasks.md`, `COMMON_ERRORS.md`,
  `docs/LEARNING_NOTES.md`, `docs/VIDEO_SCRIPT.md` → Türkçe (çalışma dosyaları)
- Kod içi isimler ve docstring'ler → İngilizce
