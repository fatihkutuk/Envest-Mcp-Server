---
name: calisma-modlari-terfi
description: |
  Korubin SCADA terfi (booster/hidrofor) nView'lerinin ÇALIŞMA MODLARI — her nView'in
  kendi calismamod.phtml dosyasındaki XC_CalismaModu vv mapping'leri, XC_SabitModSecim
  seçenekleri, setpoint tag'leri ve Master/Slave alt mod bayrakları. nView'ler arasında
  aynı vv değerinin farklı anlama gelebileceğine dikkat (özellikle a-terfi-p-v4).
  Use when: "terfi çalışma modu", "booster mode", "hidrofor modu", "master slave terfi",
  "a-terfi-envest modu", "a-terfi-p-v4 modu", "a-aqua-cnt-terfi-v2 modu",
  "pressure PI target basınç PI".
  Keywords: terfi, booster, hidrofor, master, slave, XC_CalismaModu, XC_SabitModSecim,
  XC_TerfiMasterModu, XC_TerfiSlaveModu, XC_BasincPiSet, XE_Basinc2yeGoreCalis,
  XC_AntiBlokajAktif, a-terfi-envest, a-aqua-cnt-terfi-v2, a-terfi-p-v4, a-hidro-p-v3,
  calismamod, operating mode nView.
version: "1.0.0"
---

# Korubin SCADA — Terfi/Booster nView Çalışma Modları

Her nView `calismamod.phtml` sayfasında farklı bir mod haritası kullanabilir. Bu dosya
4 terfi-ailesi nView'ini karşılaştırır. **`XC_CalismaModu` vv değerleri nView'e göre
farklı anlamlar taşıdığı için yorumlamadan önce hangi nView olduğuna bakılmalıdır.**

Kaynak tarama:
- `//10.10.10.72/public/dev.korubin/app/views/point/display/common/<nview>/calismamod.phtml`

---

## 1. `a-terfi-envest`

**XC_SabitModSecim** (Otomatik Sabit Mod Seçimi):

| vv | Mod | Setpoint Tag | Birim |
|:--:|-----|--------------|-------|
| 1 | Sabit Basınç | `XC_SabitModBasinc` | bar |
| 2 | Sabit Debi | `XC_SabitModDebi` | m³/h |
| 3 | Sabit Seviye | `XC_SabitModSeviye` | m |
| 4 | Sabit Güç | `XC_SabitModGuc` | kW |
| 5 | Sabit Frekans | `XC_SabitModFrekans` | hz |

**XC_CalismaModu** (Ana İşletme Senaryosu):

| vv | Mod |
|:--:|-----|
| 1 | Depo Doldurma |
| 2 | Hidrofor |
| 3 | Serbest Kuyu |

**Alt Mod Bayrakları** (ch-akpas):
- `XC_KuyuModu`
- `XC_TerfiMasterModu`
- `XC_TerfiSlaveModu`

nView-ekstra: yok. Standart/kanonik terfi şablonu.

---

## 2. `a-aqua-cnt-terfi-v2`

Bu nView **sabit-mod tablosu içermez**. Sadece `XC_CalismaModu` + hedef basınç/PI ayarları
ve anti-blokaj bulunur.

**XC_CalismaModu**:

| vv | Mod | Açıklama |
|:--:|-----|----------|
| 0 | Free Flow (serbest akış) | free-flow-mode |
| 1 | Target Level | Rezervuar (depo) doldurma — reservoir-filling-mode |
| 2 | Target Pressure | Booster/hidrofor modu — booster-mode |
| 3 | Activate Pressure PI | Basınç PI döngüsü aktif |

**Setpoint / ayar tag'leri**:

| Tag | Anlam | Birim |
|-----|-------|-------|
| `XD_MinSuBasinc` | Min su basıncı | bar |
| `XD_MaxSuBasinc` | Max su basıncı | bar |
| `XC_BasincPiSet` | Basınç PI setpoint | bar |
| `XZ_BasincPiSn` | Basınç PI zaman sabiti | sn |
| `XE_Basinc2yeGoreCalis` | Basınç sensörü 2'yi referans al (vv=1) | flag |
| `XC_AntiBlokajAktif` | Anti-blokaj aktif/pasif | flag (ch-akpas) |

nView-ekstra: **Pressure PI tuning** (set + time sabit), **ikinci basınç sensörü referansı**,
**anti-blocking**. Master/Slave bayrakları **YOK**.

---

## 3. `a-terfi-p-v4`

**XC_SabitModSecim**:

| vv | Mod | Setpoint Tag | Birim |
|:--:|-----|--------------|-------|
| 1 | Sabit Basınç | `XC_SabitModBasinc` | bar |
| 2 | Sabit Debi | `XC_SabitModDebi` | m³/h |
| *(3)* | *(Sabit Seviye — yorum satırı)* | *`XC_SabitModSeviye`* | *m* |
| 4 | Sabit Güç | `XC_SabitModGuc` | kW |
| 5 | Sabit Frekans | `XC_SabitModFrekans` | hz |

> vv=3 (Sabit Seviye) HTML içinde yorumlanmış — bu nView'de **sabit seviye kullanılmaz**.

**XC_CalismaModu** — **dikkat, vv mapping diğer terfilerden farklı**:

| vv | Mod |
|:--:|-----|
| 1 | Serbest Kuyu |
| 2 | Hidrofor |
| 3 | Depo Doldurma |
| 4 | **Terfi** |

**Alt Mod Bayrakları**: tablo **YOK** (Master/Slave bayrakları bu nView'de ayrı sayfada).

nView-ekstra: `XC_CalismaModu=4` **Terfi** değeri eklenmiş — dört-modlu şablon.

---

## 4. `a-hidro-p-v3`

**calismamod.phtml dosyası bulunmuyor.**

Dizin içeriği: `GENEL.phtml`, `MAIN.phtml`, `MENU.phtml`, `emniyet.phtml` — ayrı bir
"çalışma modu" sayfası yok. Hidrofor modu muhtemelen MAIN/GENEL üzerinden konfigüre
ediliyor ya da nView komple sabit-mod (hidrofor/basınç PI) varsayıyor. Bu nView için
mod okunması istenirse MAIN.phtml/GENEL.phtml taranmalı.

---

## Karşılaştırma — Hangi nView'in mode mapping'i farklı?

| Boyut | a-terfi-envest | a-aqua-cnt-terfi-v2 | a-terfi-p-v4 | a-hidro-p-v3 |
|-------|:--------------:|:-------------------:|:------------:|:------------:|
| Sabit-mod tablosu | Var (1..5) | Yok | Var (1,2,4,5) | Dosya yok |
| XC_CalismaModu vv | 1=Depo 2=Hidrofor 3=Serbest | 0=Free 1=Level 2=Pressure 3=PI | 1=Serbest 2=Hidrofor 3=Depo 4=Terfi | — |
| Master/Slave | Var | Yok | Yok (bu sayfada) | — |
| Pressure PI | Yok | Var (Set+Sn, 2.sensör) | Yok | — |
| Anti-blokaj | Yok | Var | Yok | — |

### Farklı mode mapping'i olanlar

- **`a-terfi-p-v4` — XC_CalismaModu mapping'i standart `a-terfi-envest` ile TERSİNE ÇEVRİLMİŞ**:
  - envest: `1=Depo, 2=Hidrofor, 3=Serbest`
  - v4:     `1=Serbest, 2=Hidrofor (aynı), 3=Depo, 4=Terfi`
  - Sadece **vv=2 (Hidrofor)** aynı kalıyor. vv=1 ve vv=3 yer değiştirmiş; vv=4 yeni eklenmiş.
  - **Bu nView'de XC_CalismaModu yorumlanırken kesinlikle bu tabloya bakılmalı.**

- **`a-aqua-cnt-terfi-v2` — tamamen farklı bir model**:
  - vv=0 geçerli (diğerlerinde yok — serbest akış)
  - vv=3 = Basınç PI aktivasyon bayrağı (diğerlerinde "mod" anlamı)
  - Sabit-mod kavramı yok; bunun yerine MinSuBasinc/MaxSuBasinc + BasincPiSet/Sn var.
  - Master/Slave yok; bunun yerine ikinci basınç sensörü seçimi + anti-blokaj var.

- **`a-terfi-envest`** — kanonik terfi şablonu (`calisma-modlari.md` referansı ile uyumlu).

- **`a-hidro-p-v3`** — calismamod.phtml yok; mode mapping karşılaştırılamaz.

---

## Okuma Sırası (nView-aware)

```
# Önce nView'i belirle
get_device_tag_values(nodeId, tagNames=["XC_CalismaModu","XC_SabitModSecim",
  "XC_SabitModBasinc","XC_SabitModDebi","XC_SabitModSeviye","XC_SabitModGuc",
  "XC_SabitModFrekans","XC_TerfiMasterModu","XC_TerfiSlaveModu","XC_KuyuModu",
  "XC_BasincPiSet","XZ_BasincPiSn","XE_Basinc2yeGoreCalis","XC_AntiBlokajAktif",
  "XD_MinSuBasinc","XD_MaxSuBasinc"])
```

Ardından node'un nView adına göre yukarıdaki ilgili tabloyu kullanarak yorumla.
