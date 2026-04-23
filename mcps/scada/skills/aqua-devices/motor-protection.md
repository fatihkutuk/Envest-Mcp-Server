# AQUA CNT — Motor Koruma Ayarları

> **Kaynak:** AQUA CNT Kullanım Kılavuzu, Bölüm 4 "Motor Koruma Ayarları
> Ekranı" (s24–28).

Motor Koruma alt menüsü, analog / sensör ölçümleri tanımlı limitleri
aştığında motoru durdurur ve alarm üretir. Her koruma için **eşik değeri**
+ **tahammül süresi** vardır.

> **Alarm olduğunda ne olur?** Motor durur, kırmızı LED yanıp söner. 15 dk
> sonra tekrar başlar. 3 defa art arda olursa manuel reset ister.
> Detay: `alarms-and-warnings.md`.

---

## 1. Koruma Eşikleri (register 68–75) + Set Değerleri (76–81)

| Ayar | Register | Birim | Giriş çarpanı | Not |
|---|---|---|---|---|
| **Min Su Seviye Koruma** | 68 | cm | – | Seviye-1 < bu değer → alarm |
| **Max Su Seviye Koruma** | 69 | cm | – | Seviye-1 > bu değer → alarm |
| **Min Akım Koruma** | 70 | A | **x10** (10.5 A → 105) | Analizör aktifse. Kuru çalışma tespiti |
| **Max Akım Koruma** | 71 | A | **x10** (50.2 A → 502) | Aşırı akım (tıkanma / mekanik yük) |
| **Min Basınç Koruma** | 72 | bar | **x100** (3.48 bar → 348) | Hat basıncı düşüşü |
| **Max Basınç Koruma** | 73 | bar | **x100** (6.54 bar → 654) | Hat patlak / vana kapalı |
| **Min Debi Koruma** | 74 | m³/h | **x10** (10.5 → 105) | Kuru çalışma / tıkanma |
| **Max Debi Koruma** | 75 | m³/h | **x10** (20.5 → 205) | Hat açık kaldı / patlak |
| **Min Voltaj Koruma** | 51 | V | **x10** (280 V → 2800) | Analizör aktifse |
| **Max Voltaj Koruma** | 52 | V | **x10** (382 V → 3820) | Analizör aktifse |

> Bir koruma tanımlı **DEĞİLSE** (eşik = 0 veya giriş tanımsız) o limitten
> alarm üretilmez.

---

## 2. Koruma Zamanları (register 45–49)

Ölçüm aralık dışına çıktığında, alarm **hemen değil**, bu süre kadar
aralığın dışında kalırsa üretilir. Ani geçici dalgalanmalarda gereksiz
alarm üretilmemesi için tahammül süresi.

| Zaman | Register | Birim | Tipik |
|---|---|---|---|
| Su Seviye Koruma Zaman | 45 | sn | 20 |
| Akım Koruma Zaman | 46 | sn | 5–30 |
| Voltaj Koruma Zaman | 47 | sn | 5 |
| Basınç Koruma Zaman | 48 | sn | 5–10 |
| Debi Koruma Zaman | 49 | sn | 10–30 |

---

## 3. Set Değerleri (Sensör Max Skala — register 76–81)

Sensör 4-20 mA'de okuyor, 20 mA değerinin neye karşılık geldiğini
tanımlamak için "Set" değeri gerek.

| Set | Register | Birim | Örnek |
|---|---|---|---|
| Debi-1 Set | 76 | m³/h | 200 |
| Debi-2 Set | 77 | m³/h | 200 |
| Basınç-1 Set | 78 | bar | 10 |
| Basınç-2 Set | 79 | bar | 10 |
| Seviye-1 Set | 80 | cm | 500 |
| Seviye-2 Set | 81 | cm | 15000 |

> **Önemli kavram:** Seviye sensörü tanımlanırken:
> - **Statik Seviye** = motor DURURKEN ölçülen seviye (kuyu statik su
>   seviyesi). Sensör montaj derinliği – sensör su sütunu farkıdır.
> - **Dinamik Seviye** = motor ÇALIŞIRKEN ölçülen seviye. Pompa çektikçe
>   düşer, sabitlenir.
>
> İkisi arasındaki fark = **pompa tarafından indirilen su sütunu**
> (akifer verimi / pompa debisi göstergesi).

---

## 4. Tipik Koruma Şablonları

### Derin Kuyu / Su Çekimi
```
Min Su Seviye      : 100 cm  (pompa emişi üstünde)
Max Su Seviye      : 2000 cm (sensör hata kontrol)
Min Akım           : 30% × nominal akım
Max Akım           : 120% × nominal akım
Akım Koruma Zaman  : 10 sn
Voltaj Koruma      : 180 V – 250 V (tek faz) / 360 V – 420 V (üç faz)
```

### Hidrofor Hattı
```
Min Basınç         : setpoint – 1.5 bar
Max Basınç         : setpoint + 1.5 bar
Basınç Koruma Zaman: 5 sn
Min Debi           : 0 (serbest)
Max Debi           : nominal debi × 1.3
```

### Terfi Merkezi / Depo Doldurma
```
Min Su Seviye      : pompa emiş üstü
Max Su Seviye      : tanım dışı (sensör testi)
Min/Max Akım + Voltaj: analizör tanımlıysa
```

---

## 5. "SurucuElModCalisiyor" Özel Uyarısı

Bu bir koruma değil, **koruma mantığının tespit ettiği anomalidir**:
- AQUA "Motor Çalış Çıkışı" **vermediği halde** "Motor Çalışıyor Girişi"
  gelirse uyarı üretir.
- **Sebep:** Sürücü ya da kontaktör paneli **el (manuel) moda** alınmış.
- **Çözüm:** Sürücü / pano önündeki EL / OTO anahtarını **OTO'ya** al.

---

## 6. Koruma Alarmlarının Modbus Karşılığı

| Koruma | Alarm Word 1 biti |
|---|---|
| Akım | bit 3 |
| Basınç | bit 5 |
| Debi | bit 4 |
| Su Seviye | bit 2 |
| Voltaj | bit 10 |
| Giriş Voltaj Yüksek | bit 9 |
| Motor Çalışma Hatası | bit 0 |
| Motor Termik | bit 1 |

---

## 7. Alarm Reset Yolları

1. **Ekrandan:** Alarm ve Uyarılar menüsüne gir → OK
2. **Modbus:** Control Word 1 (register 38) bit 0 = 1 (tek atış)
3. **Kendi kendine:** 15 dk sonra otomatik (max 3 kez)
