# AQUA CNT — Donanım Referansı

> **Kaynak:** AQUA CNT Kullanım Kılavuzu, Donanımsal Özellikler + Montaj
> (s2–4) + Donanım bölümü (s37–38) + Ek1/Ek2 sensör modülleri (s38–40).

---

## 1. Model Karşılaştırma

| Özellik | 100S | 100F | 100FP | 100SL |
|---|---|---|---|---|
| Dahili Ultrasonik Debimetre | – | ✓ | ✓ | – |
| Dahili Basınç Sensörü | – | – | ✓ | – |
| Dahili Seviye Sensörü | – | – | – | ✓ |
| Harici Anten | ✓ | ✓ | ✓ | ✓ |

---

## 2. Donanımsal Özellikler (Genel)

- Düşük güç tüketimli mikro denetleyici
- **Dahili ultrasonik debimetre** — min ±%1 hassasiyet, DN50–DN700 ölçüm aralığı (100F modeli)
- **64×128 grafik LCD** + membran tuş takımı
- **GSM/GPRS modem** + 5 dBi harici anten
- Batarya yönetimi birimi, dahili DC UPS ve şarj regülatörü
- **14.8 V, 12 800 mAh Li-Po pil**
- **8 MB** kalıcı dahili hafıza
- **3 adet 16-bit** analog giriş (4-20 mA)
- **1 adet 12-bit** analog çıkış (4-20 mA)
- **4 adet** dijital giriş (24 VDC opto-coupler)
- **2 adet** dijital çıkış (röle NO kontak)
- Dahili I/O giriş-çıkış tablosu
- GSM üzerinden **RTC** (gerçek zaman saati) senkronizasyonu (UNIX ts)
- **IP65** koruma sınıfı

---

## 3. Besleme ve Çıkış

### Besleme
- **24 VDC** (min **2.5 A**)
- 24 VDC güç kaynağı **veya güneş paneli** ile besleme yapılabilir
- Dahili pilin tam kapasite şarj olması için **≥ 21 VDC** besleme gerekir
- Pano içi **izolasyon trafosu** tavsiye edilir; toprak bağlantısı zorunlu

### Çıkış
- 24 VDC, **500 mA** max
- Çıkış yoksa: dahili **cam sigorta** kontrolü
- Motor sürücü beslemesi / çıkış güç kabloları ile sensör sinyal kabloları
  **aynı kablo kanalından** gitmemelidir
- Analizör haberleşme kablosu **burgulu ve koruma kılıflı** olmalı

### Pil (14.8 V Li-Po)
- Pil anahtarı **sağ** konuma getirilmeden cihaz pil enerjisini kullanamaz
- Pil enerjisi tükendiğinde "koruma moduna" geçer; harici güç kaynağı
  veya güneş paneliyle akım > 1 A ve voltaj > 21 VDC geldiğinde otomatik
  çıkar
- Şarj olması için **pil sıcaklığı 0–45 °C** arasında olmalı — NTC sensörü
  bu aralığı kontrol eder (ek sıcaklık sensörü gerekli değil, dahili)
- "Pil bağlantı yapıldı ama boş gözüküyor" → pil anahtarı, pil + klemensi
  kontrol et

---

## 4. I/O Listesi

| Giriş / Çıkış | Sayı | Tip |
|---|---|---|
| Analog Giriş | 3 | 16-bit, 4-20 mA, 24 V opto + akım koruma |
| Analog Çıkış | 1 | 12-bit, 4-20 mA |
| Dijital Giriş | 4 | 24 VDC opto-coupler |
| Dijital Çıkış | 2 | Röle NO kontak |
| RS-485 | 1 | Debimetre + Analizör için (9600/8/N) |

### Dijital Giriş Atamaları (tipik)
- Motor Termik Giriş → register 88 (1–4, dijital giriş no)
- Motor Çalışıyor Giriş → register 89 (1–4)
- SSR Giriş → register 93 (1–4)

### Dijital Çıkış Atamaları
- Motor Çalış Çıkışı → register 44 (0=yok, 1=DO1, 2=DO2)

---

## 5. Kablo Bağlantı Şeması

```
AQUA CNT Ekran
├── KORU 1000 AQUA CNT (kompakt tip pompa kontrol ve su izleme)
Debimetre Ekran
├── DEBİMETRE PROB GİRİŞLER: UP+, UP-, GND, DN+, DN-, GND
Maks: 500 mA çıkış
Röle 1NO, Röle 2NO, AI1 (4-20 mA), AI2 (4-20 mA), AI3 (4-20 mA), AI4 (4-20 mA)
BATARYA, GİRİŞ GÜCÜ, 24V+ 24V-, GND, D.GİRİŞ GİRİŞLERİ, ÇIKIŞ GİRİŞLERİ, ANALOG GİRİŞLER, ANALOG ÇIKIŞLAR
```

(Detay şekil: kılavuz s4, Şekil 2.1)

---

## 6. Ek1 — Basınç Sensörü (100FP Dahili)

AQUA 100FP içinde gelir, **pompa kontrol noktalarında** kullanıma uygun.

| Özellik | Değer |
|---|---|
| Ölçüm prensibi | Piezo rezistif ölçüm hücresi |
| Ölçüm değişkenler | Görece ve mutlak basınç |
| Ölçüm aralığı | Max **600 bar** |
| Çıkış | **4–20 mA** |
| Hassasiyet | ± %0.07 (lineerlik + histerisis + tekrar) |
| Sıfır noktası | ± 0.2 mV/V |
| İşletme sıcaklığı | -40 °C ~ 135 °C |
| Ortam sıcaklığı | -25 °C ~ 85 °C |
| Koruma sınıfı | IP67 |
| Besleme | 8–42 VDC |
| Sensör gövde | Paslanmaz 316L, Seramik |
| O-ring | Viton |
| Erkek bağlantı | 1/2" diş / 1/4" diş |
| Ağırlık | ~ 1 kg |
| Boyut | Ø 27 × 80 mm |

> **Not:** AQUA analog çıkışında motor çalışmaz iken **4 mA** değer üretilir.
> Motor çalışmaya başladığında "motor sürücü çıkış" referansına orantılı
> çıkış verir.

---

## 7. Ek2 — Seviye Sensörü (100SL Dahili)

AQUA 100SL içinde gelir, **su dağıtım depoları** için uygun.

| Özellik | Değer |
|---|---|
| Diyafram | Paslanmaz 316L, Seramik |
| Madde | Sıvılar |
| Sıvı sıcaklığı | 0–70 °C |
| Ölçüm aralığı | Min **0–300 mm**, Max **0–150 000 mm** (150 m) |
| Doğrusallık | ± %0.2 tam skalanın |
| Hassasiyet | ± %0.3 tam skalanın |
| Bağlantı | Polipropen |
| Koruma sınıfı | **IP68** (sürekli suda) |
| Besleme | 10–36 VDC |
| Çıkış | 4–20 mA |
| Gövde | Paslanmaz çelik 316 |

---

## 8. Ek3 — Dahili Ultrasonik Debimetre (100F / 100FP)

Debimetre modülü AQUA CNT'den **hariç olarak kullanılamaz** (sadece 100F
ve 100FP modellerinde dahili).

- Menüleri **M00–M92** arası kodlanmıştır.
- Boru iç çapı 15–200 mm → **V metodu**
- Boru çapı 32–50 mm → **W metodu**
- Boru çapı > 200 mm → **Z metodu**
- Tüm M menüleri için: `ultrasonic-flowmeter.md`

---

## 9. Montaj Notları

- AQUA kulaklarını **ters takarak** bir yere sabitlenebilir.
- Kablo geçişleri için rekorlar cihazın **alt** tarafından yapılır.
- Anten **yan taraftaki SMA girişine** takılır.
- Metal pano içinde → **anten dışarıya uzatılmalı** (kapsama zayıf).
- **Motor güç hattı + sensör sinyal hattı ayrı kanallardan** geçmelidir
  (EMI sebebi).

---

## 10. Hakkında / Seri No

Hakkında ekranında:
- `www.koru1000.com`
- Envest Enerji LTD ŞTİ (Tel: 444 51 29, E-posta: satis@envest.com.tr)
- HW: (donanım versiyonu, v1.2+ ise Düşük Güç Modu aktif)
- SW: (yazılım versiyonu)
- IP: Statik IP
- IMEI: Modem IMEI
- Seri No: Cihaz seri numarası
