---
name: calisma-modlari
description: |
  Korubin SCADA kuyu/terfi/depo/dma node'larının ÇALIŞMA MODLARI INDEX.
  XC_CalismaModu mapping'i nView'a göre DEĞİŞİR — bu index'ten doğru alt dosyayı seç.
  Use when: "çalışma modu ne", "sabit basınç/debi/seviye/güç/frekans modu", "depo doldurma",
  "hidrofor modu", "terfi master/slave", "kuyu modu", "XC_CalismaModu", "XC_SabitMod*".
  Keywords: çalışma modu, sabit mod, depo doldurma, hidrofor, serbest kuyu, terfi master slave,
  XC_CalismaModu, XC_SabitModBasinc, XC_SabitModDebi, XC_SabitModSeviye, XC_SabitModGuc,
  XC_SabitModFrekans, XC_SabitModSecim, XC_KuyuModu, XC_TerfiMasterModu, XC_TerfiSlaveModu,
  calismamod, operating mode.
version: "2.0.0"
---

# Korubin SCADA — Çalışma Modları (INDEX)

**KRİTİK:** `XC_CalismaModu` değerinin anlamı **her nView için FARKLIDIR**. Yanlış mapping kullanmak kullanıcıya yanlış cevap verdirir.

## nView → Alt Dosya Routing

| nView (node'un nView alanı) | İlgili dosya | Hızlı bakış |
|---|---|---|
| `a-kuyu-envest`, `a-kuyu-envest-drenaj`, `a-kuyu-envest-v2` | [calisma-modlari-kuyu.md](calisma-modlari-kuyu.md) | 1=Depo Doldurma, 2=Hidrofor, 3=Serbest Kuyu |
| `a-aqua-cnt-kuyu`, `a-aqua-cnt-kuyu-v2` | [calisma-modlari-kuyu.md](calisma-modlari-kuyu.md) | 0=FreeFlow, 3=Basınç PI, 4=Seviye Doldurma PI (FARKLI!) |
| `a-kuyu-p-v4`, `a-kuyu-p-v4.1` | [calisma-modlari-kuyu.md](calisma-modlari-kuyu.md) | 1=Serbest, 2=Hidrofor, 3=Depo, 4=Terfi (vv'ler envest'ten farklı) |
| `a-kuyu-p` | [calisma-modlari-kuyu.md](calisma-modlari-kuyu.md) | XC_CalismaModu YOK, XC_Oto{DepoDol,Hidrofor,Serbest}Mod ayrı bayraklar |
| `a-terfi-envest`, `a-terfi-envestdalgic` | [calisma-modlari-terfi.md](calisma-modlari-terfi.md) | 1=Depo, 2=Hidrofor, 3=Serbest (kanonik) |
| `a-terfi-p-v4`, `a-terfi-p-v3` | [calisma-modlari-terfi.md](calisma-modlari-terfi.md) | 1=Serbest, 2=Hidrofor, 3=Depo, 4=Terfi |
| `a-aqua-cnt-terfi-v2`, `a-aqua-cnt-terfi-v2-3b` | [calisma-modlari-terfi.md](calisma-modlari-terfi.md) | 0=FreeFlow, 1=TargetLevel, 2=TargetPressure, 3=PressurePI |
| `a-hidro-p-v3` | — | calismamod.phtml YOK, sadece GENEL/MENU/emniyet |
| `a-depo-envest` | [calisma-modlari-depo-dma.md](calisma-modlari-depo-dma.md) | calismamod YOK, actuator bazlı modlar (XACT{N}_CalismaMod*) |
| `a-aqua-cnt-depo-v2` | [calisma-modlari-depo-dma.md](calisma-modlari-depo-dma.md) | Mode YOK, düşük güç izleme |
| `a-aqua-cnt-depo-klor` | [calisma-modlari-depo-dma.md](calisma-modlari-depo-dma.md) | XC_CalismaMod (not Modu): 1=LinkDebiOransal, 2=MotorKontrol, 3=Dahili, 4=LinkBakiye Klor |
| `a-dma-p-v3`, `a-aqua-cnt-dma-v1.2` | [calisma-modlari-depo-dma.md](calisma-modlari-depo-dma.md) | Pasif izleme, mode switch YOK |

**Kullanım:** Node'un nView'ını `get_node(nodeId)` ile al → yukarıdaki tablodan uygun alt dosyayı `get_skill('korubin-scada', 'conventions/<dosya>.md')` ile oku.

**Hızlı araç:** `prepare_pump_selection(nodeId)` response'ta `calisma_modu.mapping_kaynagi_tr` alanı hangi map kullanıldığını söyler. Bilinmeyen nView ise "varsayılan kuyu mapping" denir — alt dosyadan doğrula.

---

## Ortak: XC_SabitModSecim (sabit mod seçimi)

Kuyu/terfi envest serisinde standart (nView'a göre değişebilir, bazı cnt serilerinde yok):

Panel URL: `https://<panel_base_url>/panel/point/<nodeId>/calismamod`

Bu sayfa üç bölümden oluşur:
1. **Otomatik Çalışma Mod Seçimi** (hangi değişken kontrol ediliyor)
2. **XC_CalismaModu** (ana işletme senaryosu)
3. **XC_KuyuModu / XC_TerfiMasterModu / XC_TerfiSlaveModu** (alt mod bayrakları)

---

## 1. `XC_SabitModSecim` — Otomatik Sabit Mod Seçimi

Pompa **tek bir sabit değişkeni** hedefler. Hangi değişken olacağını bu tag belirler.

| Değer | Mod | Kontrol Değişkeni | Setpoint Tag'i | Birim |
|:-----:|-----|-------------------|-----------------|-------|
| **1** | Sabit Basınç | Hat basıncı (BasincSensoru) | `XC_SabitModBasinc` | bar |
| **2** | Sabit Debi | Anlık debi (Debimetre) | `XC_SabitModDebi` | m³/h |
| **3** | Sabit Seviye | Su seviyesi (SuSeviye / DepoSeviye) | `XC_SabitModSeviye` | m |
| **4** | Sabit Güç | An_Guc motor elektrik gücü | `XC_SabitModGuc` | kW |
| **5** | Sabit Frekans | Sürücü çıkış frekansı (VFD) | `XC_SabitModFrekans` | Hz |

**Okuma:** Aktif olan satırda `XC_SabitModSecim == X`. Diğer satırlardaki setpoint'ler de
görülebilir ama aktif değildir — pompa **sadece** seçilen mod için PID/kontrol döngüsü çalıştırır.

### Hangi mod hangi duruma uygun?

- **Sabit Basınç (1):** Terfi istasyonları, hat basıncı sabit tutulacak sistemler (hidrofor benzeri)
- **Sabit Debi (2):** Tarımsal sulama, düzenli çekiş gerektiren sistemler
- **Sabit Seviye (3):** Depo doldurma senaryoları (genelde XC_CalismaModu=1 ile beraber)
- **Sabit Güç (4):** Çok nadir, motor akımını sabit tutma ihtiyacı
- **Sabit Frekans (5):** VFD'nin sabit frekansta kilitli çalıştırılması (en basit kontrol, debi/basınç
  sistem direncine göre değişebilir)

---

## 2. `XC_CalismaModu` — Ana İşletme Senaryosu

Pompa hangi **lojik senaryo** ile çalışıyor?

| Değer | Mod | Açıklama |
|:-----:|-----|----------|
| **1** | Depo Doldurma | Hedef depo seviyesine göre çalış — XC_SabitModSecim genelde 3 (Sabit Seviye). Hedef ile haberleşme + acil senaryo mantığı devreye girer. |
| **2** | Hidrofor | Kapalı devre basınçlandırma. XC_SabitModSecim=1 (Sabit Basınç) ile PID kontrol. |
| **3** | Serbest Kuyu | Kuyu kendi başına çalışır — hedef depo sorgulamaz. XC_SabitModSecim'e göre (genelde 5=Sabit Frekans veya 1=Sabit Basınç). |

### Depo Doldurma (1) özel detayları
- **Hedef IP + Modbus ID** → hedef depoyu sorgular (`aqua-devices/hedef-status.md`)
- **Acil Senaryo** (haberleşme kesilirse) — 15dk örnekleme ile geçmiş günü taklit et
- **SCADA Linkleme Aktif** → hedef seviye SCADA üzerinden linklenir (10dk içinde kurulmazsa cihaz kendi okur)

---

## 3. Alt Mod Bayrakları

Ek lojik katmanlar — aynı anda sadece biri aktif olmalı.

| Tag | Amaç |
|-----|------|
| `XC_KuyuModu` | Kuyu kontrolü (dalgıç pompa) — statik/dinamik seviye NPSH korumaları aktif |
| `XC_TerfiMasterModu` | Terfi istasyonunda master pompa — diğer slave'leri tetikler |
| `XC_TerfiSlaveModu` | Terfi istasyonunda slave pompa — master'ın yönlendirmesiyle çalışır |

---

## 4. Kullanıcı "X modunda çalışıyor mu" Sorduğunda Okuma Sırası

```
get_device_tag_values(nodeId, tagNames=[
  "XC_CalismaModu",         # ana mod (1/2/3)
  "XC_SabitModSecim",       # otomatik sabit mod (1-5)
  "XC_SabitModBasinc",      # setpoint değerleri
  "XC_SabitModDebi",
  "XC_SabitModSeviye",
  "XC_SabitModGuc",
  "XC_SabitModFrekans",
  "XC_KuyuModu",            # alt mod bayrakları
  "XC_TerfiMasterModu",
  "XC_TerfiSlaveModu"
])
```

Yorum:
1. `XC_CalismaModu = 3` (Serbest Kuyu) + `XC_SabitModSecim = 5` → **Sabit Frekans ile Serbest Kuyu**
   → Pompa `XC_SabitModFrekans` Hz'de sürekli çalışır. Debi/basınç sistem direncine göre oturur.
2. `XC_CalismaModu = 1` (Depo Doldurma) + `XC_SabitModSecim = 3` → **Hedef Seviye ile Depo**
   → `XC_SabitModSeviye` cm'ye kadar pompa çalışır, kapatır.
3. `XC_CalismaModu = 2` (Hidrofor) + `XC_SabitModSecim = 1` → **Hat Basıncı PID**
   → `XC_SabitModBasinc` bar hedefiyle PID, frekans otomatik.

---

## 5. Verim/Frekans Projeksiyonu ile İlişki

Kullanıcı "pompa verim analizi" veya "X Hz'de ne olur" dediğinde **önce çalışma modu okunmalı:**

- **Sabit Frekans modu (5) aktifse** → VFD frekansı MANUEL sabit (örn. 42 Hz). Frekans projeksiyonu tool'u bu noktadan başlamalı. Kullanıcı frekansı değiştirmek istiyorsa `XC_SabitModFrekans` set edilmeli.
- **Sabit Basınç/Debi/Seviye modu aktifse** → VFD frekansı otomatik değişiyor, mevcut frekans canlı tag'den (`An_InvFrekans`) okunur. "X Hz'de sabitlersem" sorusu için önce modu sabit frekansa çevirmek gerekir.

**Kural:** `XC_SabitModSecim != 5` iken "frekansı şu değere ayarla" önermek **yanlış** olur — sistem zaten başka bir değişkeni hedefliyor, frekans çıktı.

---

## 6. Örnek — Serbest Bölge Kuyu Okuması

Panel sayfasından alınan gerçek değerler (`node 1192`):

| Tag | Değer | Anlam |
|-----|-------|-------|
| XC_CalismaModu | 3 | **Serbest Kuyu** |
| XC_SabitModSecim | 5 | **Sabit Frekans modu aktif** |
| XC_SabitModFrekans | 42.00 Hz | Pompa 42 Hz'de kilitli |
| XC_SabitModBasinc | 0.00 bar | (pasif, kullanılmıyor) |
| XC_SabitModDebi | 190.00 m³/h | (pasif) |
| XC_SabitModSeviye | 36.00 m | (pasif) |
| XC_SabitModGuc | 60.00 kW | (pasif) |
| XC_KuyuModu | Aktif | Dalgıç kuyu korumaları aktif |

**Yorum:** Kuyu `Serbest Kuyu` modunda, VFD `42 Hz` sabit frekansta kilitli. Pompa sürekli bu frekansta çalışır, duty noktası (Q, H) tamamen sistem eğrisine bağlı.

**Verim analizi notu:** Debi/basınç değişkenliği sistem tarafından belirleniyor (boru sürtünmesi, kuyu seviyesi, depo seviyesi). Pompayı daha verimli hale getirmek için:
- XC_SabitModFrekans'ı ince ayarla (42 → 41 Hz ile ~%3.5 enerji tasarrufu)
- Veya otomatik moda geç (Sabit Basınç/Debi → PID sistem direncine karşı adapte olur)
