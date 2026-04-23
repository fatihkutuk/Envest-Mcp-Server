# AQUA CNT — Dahili Ultrasonik Debimetre (100F / 100FP)

> **Kaynak:** AQUA CNT Kullanım Kılavuzu, Ek3 Dahili Debimetre (s41–50) +
> M00-M92 menü tablosu + Hata kodları.

Bu dosya sadece **100F / 100FP** modellerinde bulunan dahili ultrasonik
debimetre modülünün kurulum, kalibrasyon ve hata referansıdır.

---

## 1. Transdüser Yerleştirme — Metot Seçimi

| Boru İç Çapı | Metot |
|---|---|
| 15 mm – 200 mm | **V Metodu** (transdüserler aynı tarafta, sinyal 1 yansıma) |
| 200 mm – büyük | **Z Metodu** (transdüserler karşılıklı, sinyal düz) |
| 32 mm – 50 mm | **W Metodu** (sinyal 2 yansıma) |

### Boru Konfigürasyonu ve Pozisyon

Transdüser yerleşimi için **yukarı akış (L_up)** ve **aşağı akış (L_dn)**
düz boru mesafeleri:

| Geometri öncesi | L_up | L_dn |
|---|---|---|
| Dirsek / T bağlantı | 10D | 5D |
| Redüksiyon (konik) | 10D | 5D |
| Genişleme (konik) | 10D | 5D |
| Vana (küresel / kelebek) | 12D | 5D |
| Pompa | 20D | 5D |
| Açık konik vana | 20D | 5D |
| Düzensiz akış üreten | 30D | 5D |

> **D**: Boru dış çapı. Yukarı akışta kadar düz boru olmalıdır.

---

## 2. Optimum Lokasyon Kuralları

1. Transdüserleri borunun **en uzun düz** bölümüne yerleştirin.
2. Ortam sıcaklığı transdüsere yakın olmalı (çok sıcak / soğuk ortam hassasiyeti bozar).
3. Kirli borular önerilmez; mümkünse **yeni boru** kullan.
4. **Plastik kaplı** boruda plastik üzerine yapıştırma **sakıncalı** olabilir.
5. Boru yüzeyindeki kir ve pas temizlenmeli → **zımparalanması** tavsiye edilir.
6. Kuplör jeli ile boşluksuz yapıştırılır.
7. Transdüserler borunun **yan tarafına** yatay olarak yerleştirilmelidir (dikey yüzde tortulaşma).

---

## 3. Kurulum Adımları (Menü Sırası)

1. MENU 10 veya 11 → **boru dış çevresi** ya da **çap** gir
2. MENU 12 → **boru kalınlığı**
3. MENU 14 → **boru malzemesi** (0-9: Karbon, Paslanmaz, Döküm, Duktil, Bakır, PVC, Alüminyum, Asbest, Fiberglass, Diğer)
4. MENU 16 → **kaplama malzemesi** (yoksa 0)
5. MENU 18 → kaplama malzeme **kalınlığı**
6. MENU 20 → **sıvı tipi** (0-15: Su, Deniz, Kerosen, Benzin, Fuel Oil, Ham Petrol, Propan, Bütan, Diğer, Dizel, Hint Yağı, Fıstık, Benzin 90, 93, Alkol, Sıcak su 125°)
7. MENU 23 → **transdüser tipi** (0-21 standart/eklentili/clamp-on modeller)
8. MENU 24 → **transdüser bağlama yöntemi** (0-V, 1-Z, 2-N, 3-W)
9. MENU 25 → transdüserler arası **boşluk** kontrolü
10. MENU 90 → **sinyal kalitesi** ölç
11. MENU 08 → **hata kodu** kontrolü (**R** olmalı — Sistem Normal)
12. MENU 01 → verileri canlı izle
13. MENU 26 → **ayarları kalıcı hafızaya kaydet**

---

## 4. Kritik Menü Kodları

| Menü | Fonksiyon |
|---|---|
| **M00** | NET Totalizör |
| **M01** | Debi + akış hızı |
| **M02** | POS Totalizör (pozitif yön) |
| **M03** | NEG Totalizör (negatif yön) |
| **M04** | Tarih / saat |
| **M05** | Anlık + toplam enerji |
| **M06** | Sıcaklık |
| **M07** | AI3 / AI4 analog (°C, bar vb. sinyale karşılık değer) |
| **M08** | **Hata kodları** (ana teşhis menüsü!) |
| **M09** | Gün net debisi |
| M10–M18 | Boru & kaplama tanımı |
| M20–M22 | Sıvı tipi + ses hızı + viskozite |
| M23–M25 | Transdüser tipi, metot, aralık |
| M26 | Ayarları kaydet |
| M29 | **Boş boru kontrolü** — sıvı yoksa totalizör saymaz |
| M30–M39 | Birim sistemi, totalizör reset, fabrika ayar, dil |
| M40 | Damping (0–999, default 10) |
| M41 | Düşük debi eliminasyonu |
| M42–M44 | Sıfır noktası kalibrasyonu, debi farkı |
| M45 | Debi skala faktörü (default 1) |
| M46 | Modbus Network adres |
| M47 | Sistem kilit (LOCKO komutu / register 49-50 üzerinden) |
| M54 | Pulse genişliği (6–1000 ms) |
| M55 | Analog çıkış seçimi (4-20 mA modları) |
| M62 | RS232/RS485 baud/parite/stop |
| M63 | Protokol (MODBUS ASCII, MODBUS RTU, METER-BUS, Fuji Ext.) |
| M68 | Min. ölçülen debi |
| M69 | Max. ölçülen debi |
| M70 | LCD arka ışık süresi (> 5000 = sürekli açık) |
| M71 | Ekran kontrast |
| M90 | **Sinyal kalitesi** (kurulumda kontrol!) |
| M92 | Gerçek ses hızı vs beklenen ses hızı karşılaştırma |

---

## 5. Hata Kodları (M08'de görünür)

| Kod | Mesaj | Sebepler | Çözümler |
|---|---|---|---|
| **R** | Sistem Normal | – | Hata yok, her şey iyi |
| **I** | Sinyal yok | Sinyal tespit edilmedi / transdüser düzgün monte değil / çok fazla kir / kaplama çok kalın / transdüser kabloları düzgün bağlanmamış | Ölçüm noktası değiştir, noktayı temizle, kabloları kontrol et |
| **J** | Donanım hatası | Donanımsal problem | Üretici ile iletişime geç |
| **H** | Zayıf sinyal tespit edildi | Zayıf sinyal / transdüser düzgün monte değil / çok fazla kir / kaplama çok kalın / kablolar | Ölçüm yerini değiştir, temizle, kuplör kontrol |
| **F** | Sistem RAM hatası / Tarih / CPU / Rom parity | Geçici RAM/RTC sorunu veya kalıcı donanım | Enerjiyi kesip tekrar ver; devam ediyorsa üretici |
| **G** | Kazanç ayarlanıyor | Cihaz kazancı ayarlanıyor (geçici) | Bekle |
| **K** | Boş boru | M29'de ayar yapın / boruda sıvı yok | M29'ı **0** gir veya boruyu doldur |

---

## 6. Modbus RTU Özellikleri

- Debimetre kendi Modbus ID'si: **1** (sabit, değiştirilmez)
- Baud: **9600 / 8 / N / 1**
- AQUA ana ünitesi bu hattan debimetreyi okur; SCADA'ya kendi
  register'larından (17, 18 = Debi-1, Debi-2) ulaştırır.

---

## 7. Birim Seçimi (M31)

Debi birimi:

| Değer | Birim |
|---|---|
| 0 | m³ |
| 1 | litre |
| 2 | USA Galon |
| 3 | Emperyal Galon |
| 4 | Milyon USA Galon |
| 5 | Kübik Fit |
| 6 | USA Sıvı Varil |
| 7 | Yağ Varil |

Zaman birimi: /gün, /saat, /dakika, /saniye (toplam 32 farklı opsiyon).

---

## 8. Damping (M40)

- Değer 0–999 arası
- Default **10**
- Yüksek değer → daha stabil ama daha gecikmeli okuma
- **0** → damping kapalı (çok dalgalı okuma)

---

## 9. Hata Giderme Hızlı Kart

| Semptom | İlk kontrol |
|---|---|
| M08 = I (sinyal yok) | Transdüser kuplör jeli, boşluk, kablo |
| M08 = H (zayıf sinyal) | Boru yüzeyi kir/pas, transdüser metot (V → Z?) |
| M08 = K (boş boru) | M29 ayarı, sıvı var mı? |
| Toplam debi sayıyor ama anlık 0 | Debi < min debi eliminasyonu (M41 aşırı yüksek) |
| Ters yön sayıyor | Transdüser "UP" / "DN" sırasını değiştir |
| Ses hızı anormal | M20 sıvı tipi yanlış seçilmiş; M92'den kontrol |
| Ayar kaybolmuş | M26'dan kaydetmedin |
