# Video Konuşma Metni — 3 Dakika

Kelime kelime okunacak metin. Sahne yönergeleri (`▸ EKRAN`) okunmaz, sadece o anda ekranda
ne olması gerektiğini söyler. Sahne sıralaması ve çekim hazırlığı için: `VIDEO_SCRIPT.md`.

**Konuşulan metin 380 kelime.** Sakin tempoda (dakikada ~125 kelime) 3 dakika 2 saniye,
normal tempoda (~140) 2 dakika 43 saniye. Yani sakin oku — demo beklemeleriyle birlikte tam
3 dakikaya oturuyor. Aceleye getirirsen 2:30'a düşer ve dolu olması gereken video seyrek
görünür.

---

## 1 — Problem (0:00 – 0:25)

▸ EKRAN: Terminal. Küçük bir modele RAG'siz soru soruluyor, uydurma cevap veriyor.

> Bir dil modeline eğitim verisinde olmayan bir şey sorarsanız, çoğu zaman bilmediğini
> söylemez — emin bir tonda uydurur.
>
> Ben bunu projenin ilk günü yaşadım. Küçük bir modele "RAG nedir" diye sordum, bana
> "Retributionary Amplification Game" diye bir şey uydurdu. Böyle bir şey yok.
>
> Yaz projemde bu problemi çözen bir asistan yaptım: sorulara sadece kendi dökümanlarımdan
> cevap veren, tamamen kendi bilgisayarımda çalışan bir soru-cevap sistemi.

---

## 2 — Nasıl çalışıyor (0:25 – 1:05)

▸ EKRAN: README'deki mimari diyagramı. Anlatırken kutuları sırayla göster.

> Kullandığım desen RAG — Retrieval Augmented Generation. Yani getir, ekle, üret.
>
> Önce dökümanlarımı parçalara bölüyorum, her parçayı bir embedding modeliyle bin yirmi dört
> boyutlu bir vektöre çevirip SQLite'a yazıyorum.
>
> Soru geldiğinde soruyu da aynı şekilde vektöre çeviriyorum, kosinüs benzerliğiyle en yakın
> üç pasajı buluyorum, ve bu pasajları sorunun yanına koyup Microsoft Foundry Local ile cihaz
> üstünde çalışan modele veriyorum.
>
> İşin özü şu: modelden hatırlamasını değil, okuyup cevaplamasını istiyorum. Okuma-anlama,
> hatırlamaktan çok daha kolay bir görev. Küçük modellerin RAG ile bu kadar iyileşmesinin
> sebebi bu.

---

## 3 — Canlı demo (1:05 – 2:05)

▸ EKRAN: Streamlit arayüzü. Üç soru sırayla. Cevap gelirken konuşmaya devam etme, bekle.

> İlk soru: "What is an execution provider?"

▸ Cevabı bekle, sonra **Sources** panelini aç.

> Cevabı veriyor — ve altında hangi dosyanın hangi bölümünden aldığını gösteriyor. Yani ben
> cevabı doğrulayabiliyorum. Kontrol edemediğim bir cevap, edebildiğimden çok daha az değerli.
>
> Şimdi bilgi tabanında olmayan bir şey soruyorum: 2018 Dünya Kupası'nı kim kazandı?

▸ Reddetme cevabını bekle.

> "Bu bilgi bilgi tabanımda yok" diyor. Burada iki savunmam var. Biri sistem promptunda
> "bilmiyorsan söyle" talimatı. Diğeri ve daha sağlamı: en iyi pasaj bile benzerlik eşiğinin
> altındaysa modeli hiç çağırmadan reddediyorum. Bu deterministik, modelin görmezden gelmesi
> mümkün değil.
>
> Ve şimdi Wi-Fi'ı kapatıyorum.

▸ Wi-Fi'ı kapat, ilk soruyu tekrar sor.

> Aynı soru, aynı cevap, on saniyede. Model de, embedding de, arama da bu makinede çalışıyor.

---

## 4 — Öğrendiklerim (2:05 – 3:00)

▸ EKRAN: `docs/EVALUATION.md` sonuç tablosu.

> Üç şey öğrendim.
>
> Birincisi: RAG'de kötü cevapların çoğu modelin değil, aramanın hatası. O yüzden arayüze
> getirilen pasajları gösteren bir panel koydum. "Model mi kötü" diye sormadan önce "doğru
> pasaj geldi mi" diye bakıyorum.
>
> İkincisi: ölçmeden ayar yapılmıyor. Yirmi beş soruluk bir değerlendirme seti hazırladım.
> Doğru pasajı bulma oranı yirmide yirmi, kapsam dışı soruları reddetme beşte beş.
>
> Üçüncüsü, ve benim için en değerlisi: kendi yazdığın testle kendini kandırabilirsin.
> Reddetme eşiğini kendi sorularımla ayarlamıştım, sıfır nokta altmışa. Sonra biri projeyi
> kendi doğal cümlesiyle sordu ve asistan reddetti. Oysa doğru pasajı bulmuştu — sadece skoru
> düşük kalmıştı. Çünkü ben sorularımı dökümanların kendi kelimeleriyle yazmıştım.
>
> Eşiği sıfır nokta kırk beşe indirdim ve tekrar ölçtüm: kapsam dışı sorular hâlâ beşte beş
> reddediliyor, ama artık gerçek sorular geçiyor.
>
> Yani asıl öğrendiğim şey şu: kendi yazmadığın girdilerle ölçmen gerekiyor.

---

## Süre taşarsa

Sahne 4'ün son iki paragrafı yerine tek cümle:

> Üçüncüsü: eşiği kendi sorularımla ayarlamıştım ve gerçek bir kullanıcının sorusunu yanlışlıkla
> reddetti. Kendi yazdığın testle kendini kandırabiliyorsun — kendi yazmadığın girdilerle ölçmek
> gerekiyor.

Bu ~20 saniye kazandırır.

## Süre kalırsa

Sahne 4'ten sonra ekleyebileceğin bir cümle:

> Bir de iki modeli karşılaştırdım: program dökümanının önerdiği phi-3.5-mini ile qwen2.5-1.5b
> aynı doğrulukta çıktı, ama phi beş kat yavaştı — medyan on altı saniyeye karşı üç saniye. O
> yüzden küçük olanı seçtim. Bu da ölçmenin karşılığı.

## Okuma notları

- **Sayıları yavaş söyle.** "Bin yirmi dört", "sıfır nokta kırk beş" — rakam okunurken hızlanmak
  en sık yapılan hata.
- **Demo beklerken susma paniği yapma.** Model cevap üretirken 3–8 saniye geçiyor; o boşluk
  videoda normal duruyor, doldurmaya çalışırsan aceleci görünür.
- **Sahne 3'te Wi-Fi anı** videonun en güçlü yeri. Kapatma hareketini ekranda göster, sonra
  bir saniye bekle, sonra soruyu sor.
- İngilizce anlatım gerekiyorsa bu metnin çevirisi hazırlanabilir; teknik terimler zaten
  İngilizce (execution provider, embedding, retrieval), o yüzden geçiş kolay.
