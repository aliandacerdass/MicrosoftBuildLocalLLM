# Öğrenme Notları

Bu projeyi yaparken öğrendiklerim, kendi cümlelerimle. Program dökümanındaki Faz 1
konularının hepsi burada — ama ezber tanım olarak değil, uygulayınca ne anladığım olarak.

## 1. RAG aslında modelin işini değiştiriyor

Başta RAG'i "modele ekstra bilgi vermek" sanıyordum. Asıl olan şu: modelden istediğin
görevi değiştiriyorsun.

- RAG'siz görev: **hatırla**. Model eğitim verisinden bir şeyler çıkarmaya çalışıyor.
- RAG'li görev: **oku ve cevapla**. Bilgi zaten promptun içinde.

Okuma-anlama, hatırlamaktan çok daha kolay bir iş. Küçük modellerin RAG ile belirgin
şekilde iyileşmesinin sebebi bu.

Bunu somut gördüm: smoke testte `qwen2.5-0.5b`'ye düz "RAG nedir?" diye sordum,
"Retributionary Amplification Game" diye bir şey uydurdu. Kelimenin ne olduğunu bilmiyordu
ama bilmediğini de söylemedi. Halüsinasyonun tehlikeli tarafı bu — çıktının hiçbir yerinde
"bundan emin değilim" sinyali yok.

## 2. Embedding = anlamın koordinatı

Embedding, metnin anlamını sayı listesine çeviriyor. Bizim modelde (`qwen3-embedding-0.6b`)
her metin **1024 boyutlu** bir vektör oluyor.

Tek tek boyutların anlamı yok — 47. sayı "kibarlık ekseni" değil. Önemli olan geometri:
benzer anlamlı metinlerin vektörleri aynı yöne bakıyor.

Benzerliği **kosinüs** ile ölçüyoruz, yani aradaki açının kosinüsü. Uzaklık yerine açı
kullanmamızın sebebi: aynı konudaki uzun bir paragraf ile kısa bir cümle yine eşleşsin
istiyoruz, uzunluk farkı bizi yanıltmasın.

Öğrendiğim püf nokta: vektörleri **birim uzunluğa normalize edersen** kosinüs benzerliği
düpedüz nokta çarpımına iniyor. Bir kere ingest sırasında normalize et, sonra her arama
tek bir matris çarpımı. `store.load_index()` bu yüzden normalize edilmiş matris döndürüyor.

## 3. Vektör veritabanına gerek yok (bu ölçekte)

İlk refleksim "vektör DB lazım" oldu. Doğru cevap: hayır.

Birkaç yüz chunk, 1024 boyut → tüm index birkaç MB. numpy'da `matrix @ query` tek BLAS
çağrısı, sonuç anında geliyor. Yaklaşık komşuluk indeksi (HNSW/FAISS) on binlerce
kayıttan sonra anlamlı. Ölçmeden ekleyeceğim her bağımlılık, kazandırdığından fazlasını
karmaşıklık olarak geri alıyor.

SQLite tarafında öğrendiğim: vektör tipi yok, ben `float32` ham byte olarak saklıyorum
(`np.tobytes()` / `np.frombuffer()`). JSON'a göre ~10 kat küçük ve okurken parse yok.
1024 boyut × 4 byte = **4096 byte** per chunk.

İki tuzak: dtype'ı yazarken de okurken de sabitlemek zorundasın, yoksa çöp okuyorsun. Ve
boyutu ayrı bir kolonda saklamak lazım — embedding modelini değiştirdiğinde kod sessizce
saçmalamak yerine yüksek sesle patlıyor.

## 4. Chunking, sistemin en sessiz ama en kritik parçası

Beklemediğim şey: RAG'de sonuç kötü olduğunda sorunun çoğu zaman modelde değil,
**retrieval'da** olması.

Doküman tek parça embed edilirse tek bir vektör bütün konuların ortalaması oluyor ve hiçbir
şeye tam benzemiyor. Tek cümlelik chunk'lar da işe yaramıyor, çünkü cümle bağlamından
koparıldığında cevabı taşımıyor.

Ben karakter sayısına göre değil, **markdown başlıklarına göre** bölüyorum. Yazar zaten
`## Execution providers` yazarken "burada konu değişiyor" demiş — bedava bilgi. Karakter
limiti sadece çok uzun bölümler için devreye giriyor, ~800 karakter hedefiyle ve ~100
karakter örtüşmeyle.

En çok işe yarayan küçük numara: **başlığı chunk metninin başına ekleyip öyle embed etmek.**
İçinde "Foundry Local" geçmeyen bir paragraf, başına "Foundry Local - Execution providers"
eklendiğinde Foundry Local sorularına çok daha iyi eşleşiyor.

## 5. Prompt: modele "bilmiyorum" deme izni vermek

System prompt'ta dört kural işin çoğunu görüyor: sadece verilen bağlamı kullan, bağlamda
yoksa bilmediğini söyle, kullandığın pasajları `[1]` şeklinde göster, kısa yaz.

İkincisi ilk bakışta gereksiz duruyor ama değil. Model varsayılan olarak "yardımcı olmaya"
çalışıyor, o yüzden ona açıkça **başarısız olma izni** vermen gerekiyor.

Ama asıl öğrendiğim şey şu: promptla verilen kural bir *rica*, garanti değil. Küçük model
onu görmezden gelebiliyor. Daha sağlam savunma pipeline'ın daha erkeninde:

> En iyi chunk bile benzerlik eşiğinin altındaysa, modeli hiç çağırmadan reddet.

Bu deterministik — konuşmayla aşılamıyor — ve bedava, çünkü üretim hiç başlamıyor.
Eşiği tahminle değil, elimdeki soru setinin gerçek skorlarına bakarak seçtim
(`docs/EVALUATION.md`).

## 6. Local çalışmanın gerçek maliyeti hız

Bulut modeliyle çalışırken düşünmediğim şey: her prompt token'ı CPU'da zaman demek. Bu
yüzden "3 chunk getir" ile "20 chunk getir" arasındaki fark cevap kalitesi değil, saniye
farkı.

Ölçtüklerim (Apple M4, CPU):

- Model indirme: model başına ~5–9 dakika (tek seferlik)
- Cache'ten yükleme: 1.6–3.3 saniye
- 3 kısa metnin embedding'i: ~0.9 saniye
- `qwen2.5-0.5b` ile kısa cevap: ~1.2 saniye

Execution provider listesinde sadece `WebGpuExecutionProvider` göründü ve kayıtlı değildi,
yani çıkarım CPU'da koştu. Desteklenen bir yapılandırma; sadece beklentiyi doğru kurmak
gerekiyor.

## 7. Bu projede en çok işime yarayan alışkanlık

`--show-context` bayrağı. Cevap kötü geldiğinde ilk soru "model mi kötü?" değil,
**"doğru pasaj geldi mi?"** olmalı. Bu ikisini ayırmadan yapılan her düzeltme tahmin.

Aynı mantık testlerde de var: `StubBackend` sayesinde chunking, depolama, retrieval ve
prompt kurulumu model indirmeden test ediliyor. Ama bunu kendime karşı dürüst tutmam
gerekti — **yeşil test ürünün çalıştığını kanıtlamıyor**, o yüzden her teslimattan önce
gerçek modelle uçtan uca demo şart.
