---
name: aqua-cnt-100
description: |
  AQUA CNT 100 kompakt tip pompa kontrol ve su izleme cihazı (100S, 100F, 100FP, 100SL).
  Donanım özellikleri, montaj, kablo bağlantıları, tuş takımı, LED göstergeleri, ayarlar, alarm kodları.
  Use when: AQUA CNT kurulum, montaj, kablo bağlantısı, LED anlamı, membran tuş, MODBUS, GSM ayarı, alarm kodu sorularında.
  Keywords: AQUA CNT, 100S, 100F, 100FP, 100SL, kompakt, pompa kontrol, kablo, LED, membran, MODBUS, GSM.
version: "1.0.0"
source_pdf: "AQUA CNT Kullanım Kılavuzu Türkçe (2022) Rev 1.2.1"
---

# AQUA CNT 100 — Kullanım Kılavuzu

## Genel Bilgi

AQUA CNT, kompakt tip pompa kontrol ve su izleme cihazıdır. Kullanım alanları:

- Su üretim sondaj kuyuları
- Su terfi pompa istasyonları
- İçme suyu su depoları
- İzole alt bölge ölçüm istasyonları (DMA)

Sahadan debi, basınç, su seviyesi, pompa gerilimi ve akım verilerini toplar; pompa kontrolü sağlar. Dört model olarak sunulur: **100S**, **100F**, **100FP**, **100SL**.

## Donanım Özellikleri

- Düşük güç tüketimli mikro denetleyici
- Dahili ultrasonik debimetre, en az %1 hassasiyet, DN50–DN700 ölçüm aralığı (yalnızca **100F** modelinde)
- 64x128 Grafik LCD ekran ve membran tuş takımı
- GSM/GPRS modem + 5 dBi harici anten
- Batarya yönetim birimi, dahili DC UPS ve şarj regülatörü
- 14.8V 12.800 mAh Li-Po batarya
- 8 MB kalıcı dahili hafıza
- 3 adet 16-bit analog giriş, 1 adet 12-bit analog çıkış (4–20 mA)
- 4 adet dijital giriş (24V DC opto-kuplör) ve 2 adet röle (NO kontak) dijital çıkış
- Atanabilir I/O giriş-çıkış tablosu
- GSM üzerinden RTC (gerçek zaman saati) güncelleme
- IP 65 koruma sınıfı
- RS-485 portu (harici debimetre / enerji analizörü haberleşmesi)

### Elektriksel Değerler

| Parametre | Değer |
|---|---|
| Besleme voltajı | 24V DC, min 2.5A |
| Pil şarj min. gerilim | 21V DC |
| Pil şarj sıcaklık aralığı | 0–45 °C |
| Pil şarj min. akımı | >1A |
| Çıkış klemens gücü | 24V DC / 500 mA |
| Analog girişler | 3 × 16-bit, 4–20 mA (24V DC voltaj ve yüksek akım korumalı) |
| Analog çıkış | 1 × 12-bit, 4–20 mA |
| Dijital girişler | 4 × 24V DC opto-kuplör |
| Dijital çıkışlar | 2 × röle NO |

## Montaj

1. **Kulakların takılması:** Cihaz üzerinde bulunan kulakları ters takarak AQUA'yı bir yere sabitleyin.
2. **Rekor yerleşimi:** Cihazın altındaki deliklere kablo rekorlarını yerleştirin (kablolar bu noktalardan içeri girer).
3. **Anten:** MODEM antenini cihazın yan tarafındaki anten girişine takın.

### Montaj Uyarıları

- Pano girişine **izolasyon trafosu** tavsiye edilir.
- AQUA'nın **enerji topraklaması kesinlikle yapılmalıdır.**
- Motor sürücü besleme/çıkış kabloları ile sensör besleme ve sinyal kabloları **aynı kablo kanalından gitmemelidir.**
- Haberleşme kablosu **burgulu ve koruma kılıflı (STP)** olmalıdır.

## Kurulum ve Kullanım

### Kablo Bağlantı Şeması

Klemens bilgileri cihaz üzerindeki etikette (Şekil 2.1) gösterilmiştir. Temel bağlantı grupları:

- **Besleme girişi:** 24V DC, min 2.5A (24V DC kaynak veya güneş paneli)
- **Sensör beslemesi:** Çıkış klemensinden 24V DC / max 500 mA
- **3 × Analog giriş (AI1–AI3):** 4–20 mA (basınç, seviye, debimetre — atanabilir)
- **4 × Dijital giriş (DI1–DI4):** 24V DC opto (motor termik, motor çalışıyor, SSR, pulse debimetre)
- **2 × Röle çıkış (DO1–DO2):** NO kontak (motor çalıştırma)
- **1 × Analog çıkış (AO):** 4–20 mA (motor sürücü referansı)
- **RS-485:** Harici debimetre + enerji analizörü
- **GSM Anten:** Yan taraftaki SMA girişi

> Analog çıkışta motor çalışmazken 4 mA üretilir. Motor başladığında "motor sürücü çıkış" referansına göre oran üretilir.

### Tuş Takımı ve LED Göstergeleri

Membran tuş takımı 4 tuşludur: **C**, **Yukarı**, **Aşağı**, **OK**.

| Tuş | İşlev |
|---|---|
| C | Geri, üst menüye dönüş, iptal. Değer girerken basılırsa **kaydederek geri gider** |
| Yukarı / Aşağı | Menüler arasında gezinme veya değer değiştirme |
| OK | Onay / kaydetme |

**Özel tuş kombinasyonları (açılış ekranında):**

- **Yukarı + Aşağı birlikte:** Otomatik Mod ↔ Manuel Mod geçişi
- **OK (manuel modda):** Motor çalış/dur komutu (art arda basışlar 30 sn aralıkla işletilir)
- **OK (alarm ekranında):** Mevcut alarmları sıfırlar

**LED'ler:**

| LED | Durum | Anlam |
|---|---|---|
| Yeşil | Saniyede 1 yanıp söner | GPRS bağlantısı ve SCADA haberleşmesi sağlandı |
| Kırmızı | Saniyede 1 yanıp söner | Sistemde aktif alarm var |

**Uyku modu:** Son tuşa basıldıktan 60 sn sonra ekran uyku moduna geçer; "KORU1000, Lütfen Bir Tuşa Basınız" yazısı belirir.

> Ekran ışığı yanıp veri görünmüyorsa ya da ekran kapalıyken membran ışıkları yanıyorsa **ekran kablosu kontrol edilmelidir.**

## AQUA Menüleri

Ana menü 8 başlıktan oluşur:

1. İşletme Ekranı
2. Sistem Ayarları
3. Motor Çalışma Ayarları
4. Motor Koruma Ayarları
5. Alarm ve Uyarılar
6. MODBUS RTU Ayarları
7. Hakkında
8. Cihaz Test

### 1. İşletme Ekranı

İki sayfadan oluşur, yön tuşlarıyla geçiş yapılır.

**Birincil Ekran:**

| Satır | Gösterilen veri |
|---|---|
| 1 | Saat, tarih, çekim gücü (CSQ 0–31) |
| 2 | Modem çalışma durumu |
| 3 | Debi1 / Debi2 anlık değer (tanımlı ise) |
| 4 | Basınç1 / Basınç2 anlık değer (tanımlı ise) |
| 5 | Seviye1 / Seviye2 anlık değer (tanımlı ise) |
| 6 | Hedef seviye + son haberleşme süresi. `Hedef:` = OK, `Hedef!` = haberleşme yok |
| 7 | Giriş besleme voltajı + son SCADA sorgusu süresi |
| 8 | Pil yüzdesi, şarj durumu, otomatik/manuel |
| 9 | `Pil:` = normal mod, `Pil!` = düşük güç modu |

**İkincil Ekran:**

| Satır | Gösterilen veri |
|---|---|
| 1 | L1 Voltaj + L1 Akım |
| 2 | L2 Voltaj + L2 Akım |
| 3 | L3 Voltaj + L3 Akım |
| 4 | Anlık güç + ortalama akım |
| 5 | CosΦ + şebeke frekansı (NOT: CosΦ 0–1 dışındaysa akım trafo yönleri kontrol edilmeli) |
| 6 | Sürücüye gönderilecek frekans referansı |
| 7 | Dijital giriş fiziksel durumları |
| 8 | Dijital çıkış fiziksel durumları |

### 2. Sistem Ayarları

- **IP Filtreleme:** 2 adet IP adresi filtreleme tanımlanabilir (IP1-1…IP2-4 oktetleri)
- **Hedef Besleme IP:** Hedef cihazdan seviye okunacaksa hedefin IP'si
- **Hedef MODBUS Register Adres:** Float (Real) değerlerde gerçek adres **+10000** olarak girilir
- **Hedef MODBUS ID:** Hedef cihaz başka bir AQUA ise **ID = 3** olmalıdır
- **Hedef Sorgu Port:** Hedef AQUA ise **port = 502**
- **Debi 1/2 Set (m³/h):** Debimetre maksimum skala (tam sayı)
- **Basınç 1/2 Set (bar):** Basınç sensörü maksimum skala (tam sayı)
- **Seviye 1/2 Set (cm):** Seviye sensörü maksimum skala (tam sayı)
- **Debi / Basınç / Seviye / Motor Termik / Motor Çalışıyor / SSR Giriş:** Fiziksel bağlantı noktası seçimi (AI1…AI3, DI1…DI4)
- **Debimetre Pulse Çarpanı:** Dijital girişteyse 1 m³ başına kaç puls
- **Motor Çalış Çıkışı:** DO1 veya DO2 seçimi
- **Log tutma süresi:** 1–1000 dk arasında; haberleşme yokken analog değerler + güç + status word kaydedilir
- **APN Network:** Ön tanımlı `mgbs` (Turkcell sabit IP). Boş bırakılırsa `mgbs` atanır.
  - Turkcell: `mgbs`
  - Vodafone: `internetstatik`
  - Türk Telekom: `statikip`
- **Motor Referans Çıkış:** Sürücüye gönderilen referans frekansın 10 katı (örn. 45.5 Hz → **455**). Minimum çalışma değeri 30 Hz'de sabittir.
- **Motor Referans Set:** Maksimum motor referans değeri (varsayılan 50 Hz)
- **Düşük Güç Modu Aktif:** Güneş panelli sistemlerde pil %40'ın altına düşerse haberleşmeyi kapatır (Donanım v1.2 için geçerli)
- **Debimetre Tip Seçimi:** Haberleşmeli debimetrelerden seçim
- **Enerji Analizörünü Aktif Etme + Model Seçimi:**
  - `0` = Klemsan KLEA220P
  - `1` = Entes MPR32S
  - `2` = Schneider PM2100

### 3. Motor Çalışma Ayarları

**Çalışma Modları (özet):**

| Mod | Açıklama |
|---|---|
| 1 | Depo Doldurma (hedef seviye ile) |
| 2 | Hidrofor Modu (basınç set noktaları ile) |
| Basınç PI | PI kontrol ile sabit basınç |

- **Hedef Min/Max Su Seviye (cm):** Depo doldurma modunda pompa çalışma/durma seviyeleri
- **Hidrofor Min/Max Basınç:** x100 olarak girilir. Örn. 4.55 bar → **455**, 6.55 bar → **655**
- **Basınç PI Set:** Hedef basınç × 100
- **Basınç PI Zaman:** PI çevrim süresi (ms)
- **Acil Senaryo Aktif:** Depo doldurma modunda hedefle haberleşme yoksa, geçmiş en yakın haberleşmeli günün motor davranışını **15 dk örnekleme** ile taklit eder
- **Acil Durum Bekleme Süresi (dk):** 10–300 dk (haberleşme yoksa motor bekleme süresi)
- **Acil Durum Çalışma Süresi (dk):** 10–300 dk (haberleşme yoksa motor çalışma süresi)
- **SCADA Linkleme Aktif:** Depo doldurma modunda hedef seviye SCADA tarafından link edilir. 10 dk içinde link kurulmazsa cihaz hedefi kendi okur.
- **Basınç 2'ye göre çalışma:** Hidrofor modunda referans basınç olarak 2. basınç sensörünü kullanır
- **Log Hafızası Temizleme:** Kayıtları siler
- **Antiblokaj Modu:** Soğuk havada donmayı önlemek için otomatik modda **her 90 dk'da 5 dk çalışır**

### 4. Motor Koruma Ayarları

Koruma değerleri alt/üst limitler olarak tanımlanır. Limitlerin **sıfırdan büyük** olması gerekir.

| Koruma | Birim | Giriş Formatı | Örnek |
|---|---|---|---|
| Min/Max Su Seviye | cm | tam sayı | 150 |
| Min/Max Akım | A × 10 | tam sayı | 10.5A → 105 |
| Min/Max Basınç | bar × 100 | tam sayı | 3.48 bar → 348 |
| Min/Max Debi | m³/h × 10 | tam sayı | 10.5 m³/h → 105 |
| Min/Max Voltaj | V × 10 | tam sayı | 280V → 2800 |

- **Maksimum Su Seviyesi Koruması:** Min seviye alarmı aktifken, seviye bu değere ulaşınca alarm resetlenir ve motor çalışır.
- **Koruma Zaman parametreleri** (Su Seviye / Akım / Basınç / Debi / Voltaj): Sn cinsinden tahammül süresi. Değer limit dışına çıkıp bu süre geçerse alarm verilir.
- Alarmlar **3 kez 15 dk aralıkla otomatik resetlenir**. Ard arda 3'ten fazla oluşursa **kalıcı alarm** olur ve **manuel reset** gerekir.

## Model Farkları (100S / 100F / 100FP / 100SL)

| Model | Dahili Debimetre | Dahili Basınç Sensörü | Dahili Seviye Sensörü | Tipik Kullanım |
|---|---|---|---|---|
| **100S** | — | — | — | Standart pompa kontrol, harici sensörlerle |
| **100F** | Ultrasonik (DN50–DN700, %1) | — | — | Debi ölçüm + pompa kontrol |
| **100FP** | Ultrasonik | Var | — | Debi + basınç (hidrofor / pompa kontrol) |
| **100SL** | — | — | Var | Su dağıtım depoları, seviye takibi |

Dahili basınç/seviye sensörleri 3 analog girişten birine bağlanıp menüden tanımlanır. **100F/100FP içindeki ultrasonik debimetre modülü cihazdan ayrı olarak (haricen) kullanılamaz.**

### Dahili Ultrasonik Debimetre — Kurulum Adımları

1. MENU 10 veya 11: Boru **dış çevresi** ya da **çapı**
2. MENU 12: Boru kalınlığı
3. MENU 14: Boru malzemesi
4. MENU 16: Kaplama malzemesi (yoksa 0)
5. MENU 18: Kaplama kalınlığı (varsa)
6. MENU 20: Sıvı tipi
7. MENU 23: Transdüser tipi
8. MENU 24: Transdüser bağlantı modu
9. MENU 25: Transdüserler arası boşluk
10. MENU 90: Sinyal kalitesini ölç
11. MENU 08: Çalışma durumunun `R` olduğunu doğrula
12. MENU 01: Verileri doğrula
13. MENU 26: Ayarları kalıcı hafızaya kaydet

### Transdüser Yerleştirme Yöntemleri

| Metod | Boru İç Çapı |
|---|---|
| **W** | 32–50 mm |
| **V** | 15–200 mm |
| **Z** | > 200 mm |

**Yerleştirme ipuçları:**

- Borunun en uzun düz bölgesine yerleştirin.
- Oda sıcaklığına yakın bir ortam seçin (transdüser ısı limitlerine dikkat).
- Temiz ve plastik kaplamasız boru tercih edin; pas/kir için zımparalayın.
- Uygun kuplör ile boşluk bırakmadan uygulayın.
- Transdüserleri borunun **yan tarafına yatay** uygulayın.

## MODBUS Haberleşme

### MODBUS RTU (RS-485) Ayarları

Harici debimetre ve enerji analizörü için:

- Haberleşme parametreleri: **9600 / 8 / N / 1**
- Debimetre MODBUS ID: **1**
- Analizör MODBUS ID: **2**

### MODBUS TCP (GSM 2G üzerinden)

- Port: **502** (standart)
- Desteklenen Function Code'lar: **FC3, FC6, FC16, FC22**
- Aynı anda maksimum **5 sorgu** kabul edilir
- Tek sorguda maksimum **64 word register** okunabilir
- Tek sorgu varsa aralık **≥ 1 sn**
- SCADA + hedef depo sorgusu yapan noktalarda aralık **≥ 15 sn**
- Birden fazla SCADA haberleşmesi varsa aralık **≥ 30 sn**
- Önerilen timeout: **3 sn**, önerilen sorgu sıklığı: **min 15 sn**
- **Control Word2 ve sonrası register'ları kalıcı hafızada tutulur.**
- Float (Real) değerleri için hedef register adresi **+10000** offset ile tanımlanır.

> Detaylı MODBUS register adres tablosu kılavuzun sayfa 30–35 arasındadır (Rev 1.2.1). MCP içinde adres listesi sorulduğunda güncel kılavuz PDF'ine yönlendirin.

## Alarm Kodları

Alarm ekranı aktif alarmları listeler. Her alarm 3 kez 15 dk ara ile otomatik reset dener; 3'ten fazla tekrar ederse **kalıcı alarm** olur ve **OK tuşu ile manuel reset** gerekir.

| Alarm | Anlamı | Olası Sebep / Çözüm |
|---|---|---|
| Min Su Seviye | Seviye alt limitin altında | Kuyu/depo boş; min seviye set değerini ve sensörü kontrol edin |
| Max Su Seviye | Seviye üst limiti aştı | Max seviye koruma değerini ve sensör skalasını kontrol edin |
| Min Akım | Motor akımı alt limit altında | Kuru çalışma / rotor kopması; analizör bağlantısını ve motoru kontrol edin |
| Max Akım | Motor akımı üst limit üstünde | Motor sıkışması / aşırı yük; mekanik kontrol |
| Min Basınç | Basınç alt limit altında | Emiş sorunu, kaçak; hidrofor modu set değerlerini kontrol edin |
| Max Basınç | Basınç üst limit üstünde | Çıkış vanası kapalı, set çok düşük; koruma set değerini kontrol edin |
| Min Debi | Debi alt limit altında | Vana kapalı, pompa boşa dönüyor; debimetre kalibrasyonu |
| Max Debi | Debi üst limit üstünde | Patlak hat / aşırı tüketim; set değerini gözden geçirin |
| Min Voltaj | Şebeke voltajı alt limitin altında | Şebeke zayıf; min voltaj set değerini kontrol edin |
| Max Voltaj | Şebeke voltajı üst limitin üstünde | Şebeke yüksek; trafo/sigorta kontrolü |
| Motor Termik | Termik rölesi atmış | Motoru soğutun, termik rölesini resetleyin, DI bağlantısını kontrol edin |
| SSR (Sıvı Seviye Rölesi) | Elektrod/SSR tetikledi | Elektrod seviyesini ve DI girişini kontrol edin |
| Hedef Haberleşme Hata | Hedef cihaza MODBUS TCP yok | IP / Port / MODBUS ID / GSM sinyali kontrolü; Acil Senaryo devreye girer |
| Pil Düşük / CutOFF | Pil tükendi veya koruma modunda | Anahtar konumu, şarj voltajı (≥21V DC) ve pil sıcaklığı (0–45 °C) kontrolü |
| Düşük Sıcaklık Uyarısı | Pil sıcaklık sensörü yok / düşük | Pil sıcaklık sensörünün takılı olduğunu doğrulayın |

## Donanım Detayları (Özet)

### Pil

- **14.8V 12.800 mAh Li-Po**, dahili şarjlı.
- Aktivasyon: Pil anahtarını sağ konuma getirin.
- **Şarj koşulu:** Pil sıcaklığı 0–45 °C, besleme ≥ 21V DC, akım ≥ 1A.
- Pil tükendiğinde **koruma moduna** geçer; yeterli şarj gelince otomatik çıkar.
- Anahtar kapalıyken bile sıcaklık okunur; CutOFF varsayılarak 30 sn aralıkla uyandırma denemesi yapılır.

**SSS — Pil neden bir dolu bir boş gösterir?**

- Pil anahtarı kapalı olabilir,
- Pil koruma moduna geçmiş olabilir,
- Pil `+` ucu klemensten çıkmış olabilir.

### Besleme ve Çıkışlar

- **Besleme:** 24V DC, min 2.5A (adaptör veya güneş paneli)
- **Çıkış klemensi:** 24V DC / 500 mA (dahili cam sigorta korumalı — çıkış yoksa sigortayı kontrol edin)

### Kavram Tanımları

- **Statik Seviye:** Motor çalışmazken su seviyesinin zemine olan uzaklığı. Sensörün montaj derinliği − su yükü.
- **Dinamik Seviye:** Motor çalışırken su seviyesinin zemine olan uzaklığı. Aynı formül, çalışır durumda.

## Sık Sorulan Sorular

**Q: 100F ile 100FP arasındaki fark nedir?**
A: 100F yalnızca dahili ultrasonik debimetre içerir. 100FP hem dahili debimetre **hem de** dahili basınç sensörü içerir; hidrofor/pompa kontrol uygulamalarında tercih edilir.

**Q: 100S ile 100SL farkı?**
A: 100S standart modeldir (dahili sensör yok, hepsi harici). 100SL dahili seviye sensörü ile gelir; su dağıtım depolarında kullanılır.

**Q: Manuel moda nasıl geçerim?**
A: Açılış ekranında **Yukarı + Aşağı** tuşlarına aynı anda basın.

**Q: Manuel modda motoru nasıl çalıştırırım?**
A: Açılış ekranında **OK** tuşuna basın. Art arda çalıştır/durdur komutları 30 sn aralıkla işletilir.

**Q: Alarmı nasıl resetlerim?**
A: Alarm ekranına gidip **OK** tuşuna basın. Kalıcı alarmlar sadece manuel resetlenebilir.

**Q: Kırmızı LED sürekli yanıp sönüyor, ne yapmalıyım?**
A: Sistemde aktif alarm var. Alarm ekranını açıp listedeki alarmı ve Motor Koruma Ayarları'nı kontrol edin.

**Q: Yeşil LED yanmıyor, SCADA'ya veri gelmiyor.**
A: GSM sinyalini (CSQ), APN ayarını, SIM kartı ve anten bağlantısını kontrol edin. CSQ < 10 ise anten konumunu değiştirin.

**Q: MODBUS TCP'den float değer okumak istiyorum, adresi nasıl tanımlarım?**
A: Gerçek register adresine **+10000** ekleyin. Örn. gerçek adres 40 ise AQUA'ya **10040** girin.

**Q: Hedef cihaz başka bir AQUA ise MODBUS ID ve port ne olmalı?**
A: MODBUS ID = **3**, Port = **502**.

**Q: Motor sürücüye referans frekans nasıl girilir?**
A: Değerin **10 katı** girilir. 45.5 Hz için 455 yazın. Minimum çalışma frekansı 30 Hz'de sabittir.

**Q: Basınç set değerini nasıl girerim?**
A: Değerin **100 katı** girilir. 4.55 bar için 455 yazın.

**Q: Düşük güç modu ne işe yarar?**
A: Güneş panelli kurulumlarda pil %40 altına düşünce haberleşmeyi kapatıp enerji tasarrufu sağlar (Donanım v1.2 için geçerli).

**Q: Antiblokaj modu ne yapar?**
A: Otomatik modda her 90 dk'da 5 dk motoru çalıştırarak donmayı önler.

**Q: SCADA linkleme aktifken hedef seviye nereden okunur?**
A: İlk 10 dk SCADA link bekler; link başarılı olursa hedef seviye SCADA üzerinden okunur. 10 dk içinde link kurulmazsa (Hedef IP tanımlıysa) cihaz hedefi kendisi sorgular.

**Q: Ultrasonik transdüserleri hangi metoda göre yerleştireyim?**
A: Boru iç çapına göre: 32–50 mm → W, 15–200 mm → V, >200 mm → Z metodu.

**Q: Ekran uyku moduna geçiyor, veri görünmüyor ne yapayım?**
A: 60 sn tuş basılmadığında ekran uyur; herhangi bir tuşa basın. Işık yanıp veri gelmiyorsa ekran kablosunu kontrol edin.

**Q: CosΦ 0–1 aralığı dışında görünüyor, sebep ne?**
A: Akım trafo yönleri ters takılmıştır; trafo polaritelerini kontrol edin.

**Q: APN boş bırakılırsa ne olur?**
A: Otomatik olarak `mgbs` (Turkcell sabit IP APN) atanır.

## İletişim / Destek

- **Envest Enerji ve Su Teknolojileri Ltd. Şti.**
- Merkez: Altınoluk Mh. Fatih Sultan Mehmet Blv. No: 72/2 38050 Melikgazi / Kayseri
- Ar-Ge: Erciyes Teknopark Tekno-1 Binası No: 61/24 Melikgazi / Kayseri
- Telefon: 0 352 224 01 82
- 7/24 Destek: 0 533 205 20 38
- E-posta: satis@envest.com.tr
- Web: www.envest.com.tr
