# AQUA CNT — Çalışma Modları ve Senaryolar

> **Kaynak:** AQUA CNT Kullanım Kılavuzu, Bölüm 3 "Motor Çalışma Ayarları
> Ekranı" (s20–26).

Motor Çalışma Ayarları menüsünden **Çalışma Mod** değeri seçilir. Toplam
4 mod vardır ve her mod kendi alt parametrelerine sahiptir.

---

## 1. Çalışma Mod (register 43)

| Değer | Mod | Özet |
|---|---|---|
| 0 | **Serbest Mod** | AQUA sadece izleme yapar, motor kontrolü yapmaz |
| 1 | **Depo Doldurma** | Hedefle haberleşerek / taklit ederek depo seviyesini aralığa getirir |
| 2 | **Hidrofor Mod** | Basınç sensöründen okuduğu değere göre hat basıncını aralığa getirir |
| 3 | **Basınç PI** | Sabit basınç setpoint'ine göre sürücü frekansı ile motor çalıştırır |

---

## 2. Depo Doldurma (Mod = 1)

**Kontrol mantığı:** Hedefte (başka bir AQUA veya SCADA) okunan depo seviyesi
**min altında ise** motor çalışır, **max üstüne** çıkarsa durur.

| Ayar | Menü | Birim | Not |
|---|---|---|---|
| Hedef Minimum Su Seviye | Motor Calisma Ayar → Hedef Min Su Seviye | cm | Pompa **çalışma** seviyesi |
| Hedef Maksimum Su Seviye | Motor Calisma Ayar → Hedef Max Su Seviye | cm | Pompa **durma** seviyesi |
| Acil Senaryo Aktif | Acil Senaryo Aktif | 0/1 | Hedefle hab. yoksa son 15 dk örneklemiyle geçmişi taklit et |
| Acil Durum Bekleme Süresi | Acil Durum Bekle | dk (10–300) | Acil senaryo **pasif** ise, hedef yoksa motor bu süre durur |
| Acil Durum Çalışma Süresi | Acil Durum Çalış | dk (10–300) | Acil senaryo **pasif** ise, hedef yoksa motor bu süre çalışır |
| SCADA Linkleme Aktif | SCADA Linkleme | 0/1 | Hedef seviyeyi Modbus üzerinden **SCADA yazacak**; 10 dk boyunca link yoksa cihaz hedefe kendisi sorar |

> **Acil senaryo aktif iken:** Cihaz, hedef cihazdan 15 dk örnekleme ile
> topladığı geçmiş verideki motor çalışma/durma kalıplarını (aynı gün,
> benzer saat aralığı) taklit eder. Bu, kuyular + depolu sistemlerde
> haberleşme koptuğunda pompanın bir süre sağlıklı çalışmasını sağlar.

---

## 3. Hidrofor Mod (Mod = 2)

**Kontrol mantığı:** Hat basıncı `Hidrofor Min Basınç` altına düştüğünde
motor **çalışır**, `Hidrofor Max Basınç` üstüne çıktığında **durur**.

| Ayar | Menü | Birim | Giriş Formatı |
|---|---|---|---|
| Hidrofor Minimum Basınç | Motor Calisma Ayar → Hidrofor Min Basınç | bar | **x100 olarak gir**. Örn 4.55 bar → `455` |
| Hidrofor Maksimum Basınç | Hidrofor Max Basınç | bar | **x100**. Örn 6.55 → `655` |
| Basınç 2'ye göre çalış | Basınç 2 ile Çalış | 0/1 | 1 seçildiğinde referans Basınç Sensörü **2** olur |

---

## 4. Basınç PI Mod (Mod = 3)

**Kontrol mantığı:** Motor sürücüyle çalışır, sürücü frekansını **PI
algoritması** ile ayarlar ve basıncı sabit tutar.

| Ayar | Menü | Birim | Giriş Formatı |
|---|---|---|---|
| Basınç PI Set | Motor Calisma Ayar → Basınç PI Set | bar | **x100**. Örn 5.5 bar → `550` |
| Basınç PI Zaman | Basınç PI Zaman | ms | PI çevrim süresi (örn 5000 = 5 sn) |

> Sürücüye gönderilen referans **Motor Ref Çıkış** (register 40, x10 değer).
> Motor referansı **minimum 30 Hz** altına inemez (sabit).

---

## 5. Antiblokaj (soğuk hava önlemi)

- **Amaç:** Soğuk havalarda hattaki suyun donmaması için pompayı düzenli
  aralıkla kısa süreli çalıştırmak.
- **Koşul:** Sistem **Otomatik modda** olmalı ve Antiblokaj Aktif = 1.
- **Periyot:** **Her 90 dakikada bir 5 dakika** çalıştırır.
- **Status Word 1 bit 8** = "Motor Antiblokaj'da Çalışıyor" → çalışma
  sebebini bu bitle ayırt edebilirsin.

---

## 6. Düşük Güç Modu (HW v1.2+)

- **Koşul:** Güneş paneli ile beslenen noktalarda pil %40 altına düşerse.
- **Etki:** Cihaz haberleşmeyi **kapatır** (modem dışı), enerji tasarrufu
  yapar.
- Aktif olduğunda **Uyarı: Pil!** (ekran) ve **AlarmWord-1 bit 9** yükselir.
- Control Word 2 bit 3 = "Düşük Güç Modu Aktif" (kalıcı ayar).

---

## 7. SCADA Linkleme (Depo Doldurma modunda)

- **Amaç:** Uzaktaki depo seviyesini SCADA okuyup AQUA'ya yazmak
  (hedef cihaz Modbus değil, SCADA aracısı varsa).
- **Aktifse:** AQUA, hedef seviye bilgisini SCADA'nın register 33'e
  yazmasını bekler. 10 dk boyunca SCADA yazmazsa AQUA kendi başına
  hedef IP'den sorgulamaya geçer.
- Control Word 2 bit 1 = "Hedef Depo Seviyeyi SCADA Yazacak".

---

## 8. Motor Referans Ayarları (Sürücülü çalışma)

| Ayar | Menü | Not |
|---|---|---|
| Motor Referans Çıkış | Motor Ref Çıkış | Anlık sürücü referansı (x10). 45.5 Hz → `455` |
| Motor Referans Set | Motor Ref Set | Max. sürücü referansı (varsayılan 50 Hz) |

> **Motor referansı pompa çalışırken minimum 30 Hz olacak şekilde
> sabitlenmiştir.** Bu altta çalıştırılamaz.

---

## 9. Mod Seçim Karar Ağacı

```
Bu nokta ne tür?
├─ Uzaktaki bir depoya su veriyor mu? ── EVET ─▶ Mod 1 (Depo Doldurma)
│   └─ Hedefle kalıcı link güvenilir mi?
│       ├─ EVET → Acil Senaryo = 0
│       └─ HAYIR → Acil Senaryo = 1 (taklit et)
├─ Hat basıncını tutması mı gerekiyor?
│   ├─ Basit on/off ─▶ Mod 2 (Hidrofor)
│   └─ Sabit basınç + sürücü ─▶ Mod 3 (Basınç PI)
└─ Sadece izliyor muyuz? ─▶ Mod 0 (Serbest)
```
