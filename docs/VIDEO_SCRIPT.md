# Video Scripti — 3 Dakika

Program "neler öğrendim ve ne yaptım" videosu istiyor. Hedef: 3 dakika, 4 sahne.
Aşağıda her sahnede **ne söyleyeceğin** ve **ekranda ne olacağı** ayrı ayrı yazılı.

Çekim öncesi kontrol listesi en altta.

---

## Sahne 1 — Problem (0:00–0:30)

**Ekranda:** Terminal, sadece Foundry Local ile küçük bir modele düz soru soruluyor.
Model uydurma cevap veriyor. (Smoke testte `qwen2.5-0.5b`'nin "RAG" için ürettiği
"Retributionary Amplification Game" cevabının ekran görüntüsü ya da canlı tekrarı.)

**Söylenecek:**

> "Bir dil modeline eğitim verisinde olmayan bir şey sorduğunuzda üç şey olabilir:
> bilmediğini söyler, doğru bilir, ya da emin bir tonda uydurur. Tehlikeli olan üçüncüsü —
> çıktının hiçbir yerinde 'bundan emin değilim' sinyali yok. Bu projede o problemi
> çözen bir asistan yaptım: kendi dökümanlarımdan cevap veren, tamamen kendi
> bilgisayarımda çalışan bir soru-cevap sistemi."

---

## Sahne 2 — Nasıl çalışıyor (0:30–1:15)

**Ekranda:** README'deki mimari diyagramı. Konuşurken kutuları sırayla göster.

**Söylenecek:**

> "Kullandığım desen RAG — Retrieval Augmented Generation. Üç adım:
>
> **Retrieve:** Soruyu bir embedding modeliyle 1024 boyutlu vektöre çeviriyorum ve
> SQLite'ta sakladığım doküman parçalarının vektörleriyle kosinüs benzerliğine göre
> karşılaştırıp en yakın 3 pasajı buluyorum.
>
> **Augment:** Bu pasajları numaralandırıp promptun içine koyuyorum, üstüne de kuralı:
> sadece bu pasajlardan cevapla, yoksa bilmediğini söyle, kaynağı göster.
>
> **Generate:** Cevabı Microsoft Foundry Local ile cihaz üstünde çalışan bir model
> yazıyor. Buradaki kritik nokta şu: modelden 'hatırlamasını' değil, 'okuyup cevaplamasını'
> istiyorum. Okuma-anlama çok daha kolay bir görev — küçük modellerin RAG ile bu kadar
> iyileşmesinin sebebi bu."

---

## Sahne 3 — Canlı demo (1:15–2:30)

**Ekranda:** Streamlit arayüzü. Üç soru, bu sırayla:

1. **Cevaplanan soru** — örn. "What is an execution provider?"
   Cevap gelirken kaynaklar panelini aç, `[1]` atıfının hangi dosyanın hangi bölümünden
   geldiğini göster.

2. **Reddedilen soru** — örn. "Who won the 2018 FIFA World Cup?"
   Asistan "I don't have that information in my knowledge base." diyor.

3. **Offline kanıtı** — Wi-Fi'ı kapat, birinci soruyu tekrar sor, aynı şekilde cevaplasın.

**Söylenecek:**

> "İlk soru bilgi tabanında var — cevabı veriyor ve hangi pasajdan aldığını gösteriyor,
> yani doğrulayabiliyorum.
>
> İkinci soru bilgi tabanında yok. Burada iki savunmam var: sistem promptunda 'bilmiyorsan
> söyle' talimatı, ve ondan daha sağlamı — en iyi pasaj bile benzerlik eşiğinin altındaysa
> modeli hiç çağırmadan reddediyorum. Bu deterministik, modelin görmezden gelmesi mümkün
> değil. Eşiği tahminle değil ölçerek seçtim: cevaplanabilir sorular 0.62 ve üstü,
> kapsam dışı sorular 0.58 ve altı skor alıyordu, eşiği aradaki 0.60'a koydum.
>
> Ve şimdi Wi-Fi'ı kapatıyorum... aynı soru, aynı cevap. Hiçbir bulut çağrısı yok —
> model de, embedding de bu makinede çalışıyor."

---

## Sahne 4 — Öğrendiklerim (2:30–3:00)

**Ekranda:** `docs/EVALUATION.md`'deki sonuç tablosu.

**Söylenecek:**

> "Üç şey öğrendim.
>
> Birincisi: RAG'de kötü cevapların çoğu modelin değil, **retrieval'ın** hatası. O yüzden
> CLI'a retrieve edilen pasajları basan bir bayrak koydum — 'model mi kötü' diye sormadan
> önce 'doğru pasaj geldi mi' diye bakıyorum.
>
> İkincisi: **chunking** sistemin en sessiz ama en kritik parçası. Karakter sayısına göre
> değil, markdown başlıklarına göre bölüyorum, çünkü yazar zaten konunun nerede değiştiğini
> söylemiş. Başlığı chunk metninin başına ekleyip embed etmek de eşleşmeyi belirgin
> şekilde iyileştirdi.
>
> Üçüncüsü: **ölçmeden ayar yapılmıyor.** 22 soruluk bir değerlendirme seti hazırladım;
> doğru pasajı bulma oranı %100, kapsam dışı soruları reddetme oranı %100 çıktı.
> Sayılar olmadan eşik seçmek tahmindi."

---

## Çekim öncesi kontrol listesi

- [ ] `python -m localrag.ingest` çalıştırılmış, index hazır (demo sırasında indirme bekleme yok)
- [ ] Streamlit açık ve bir kere ısıtılmış (ilk soru model yüklemesi yüzünden yavaş)
- [ ] Terminal yazı tipi büyütülmüş (video sıkıştırmasında okunabilirlik)
- [ ] Wi-Fi kapatma anı prova edilmiş
- [ ] Ekranda kişisel bilgi yok: masaüstü temiz, sekmeler kapalı, terminal geçmişi temiz
- [ ] Toplam süre 3:00'ı geçmiyor (prova ile ölç)

## Not

Sahne 3 videonun en güçlü anı. Wi-Fi'ı kapatıp aynı cevabı almak, "offline çalışıyor"
cümlesinin tek gerçek kanıtı — anlatmak yerine gösterilmesi gereken şey bu.
