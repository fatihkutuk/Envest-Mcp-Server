---
name: calisma-modlari-depo-dma
description: |
  Korubin SCADA DEPO (tank) ve DMA (District Metered Area) nView node'larının
  çalışma modu ve ayar etiketleri. Bu node'lar `calismamod.phtml` DOSYASINA SAHIP
  DEGILDIR — pompa kuyu/terfi panellerinin aksine burada tek bir XC_CalismaModu
  ana switchi yoktur. Mod kavramı klorlama ve ACT (oransal vana) alt panellerinde
  yer alır; DMA node'ları genelde pasif izleme (debi/basınç ölçüm) yapar ve
  çalışma modu ayarı bulundurmaz.
  Use when: "depo çalışma modu", "DMA çalışma modu", "depo-envest mod", "aqua-cnt-depo mod",
  "klor çalışma modu", "klorlama modu", "dozaj pompası modu", "DMA izleme mi kontrol mü",
  "a-depo-envest calismamod", "a-aqua-cnt-depo-klor klorayar", "XC_CalismaMod klor",
  "XACT*_CalismaModDepoSeviye", "XACT*_CalismaModLinkSeviye".
  Keywords: depo, DMA, klor, klorlama, dozajlama, izleme, oransal act, aqua-cnt,
  a-depo-envest, a-aqua-cnt-depo-v2, a-aqua-cnt-depo-klor, a-dma-p-v3,
  a-aqua-cnt-dma-v1.2, XC_CalismaMod, XK_DozajPompasiGirisSecim, XK_BakiyeKlorPid,
  XACT_CalismaModDepoSeviye, XACT_CalismaModLinkSeviye, XOranACT_CalismaMod.
version: "1.0.0"
---

# Depo ve DMA Çalışma Modları

## Özet: `calismamod.phtml` Yok

Aşağıdaki 5 nView dizini incelendi. Hiçbirinde `calismamod.phtml`
(veya `Calismamod.phtml` / `calisma.phtml` / `calisma_mod.phtml`) dosyası
bulunmamaktadır:

| nView                           | calismamod.phtml | Not                                                                 |
| ------------------------------- | ---------------- | ------------------------------------------------------------------- |
| `a-depo-envest`                 | YOK              | Mod mantığı `act_ayar.phtml` + `oran_act_*_ayar.phtml` içinde       |
| `a-aqua-cnt-depo-v2`            | YOK              | Basit depo; sadece depo ölçüleri + klor linki                        |
| `a-aqua-cnt-depo-klor`          | YOK              | Tam klorlama modu `klorayar.phtml` içinde (XC_CalismaMod)           |
| `a-dma-p-v3`                    | YOK              | Pasif izleme; sadece debimetre/sensör/analog ayar                    |
| `a-aqua-cnt-dma-v1.2`           | YOK              | Pasif DMA/IWA node; ili/iwa/map panelleri — kontrol yok              |

Alternatif isimler (`Calismamod.phtml`, `calisma.phtml`, `calisma_mod.phtml`)
da taranmış, hiçbirinde mevcut değildir.

## Sonuç: Depo ve DMA için `XC_CalismaModu` Yoktur

Kuyu/terfi node'larındaki tek-noktalı `XC_CalismaModu` (1=Sabit Basınç,
2=Sabit Debi, ...) switch'i BU node'larda **bulunmaz**. Bunun yerine:

- **Depo node'ları** → her ACT (motorize vana) için ayrı ayrı "Depo Seviye /
  Link Seviye" modu (per-actuator checkbox)
- **Klor node'ları** → ayrı bir `XC_CalismaMod` (klorlama türü, 4 değerli)
- **DMA node'ları** → çalışma modu kavramı yok, yalnızca pasif izleme

---

## 1. `a-depo-envest` — ACT (Motorize Vana) Başına Mod

Kaynak: `act_ayar.phtml` + `oran_act_{1..4}_ayar.phtml`

### Per-ACT Çalışma Modu (ACT 1..6)

Her ACT için iki seviye kaynağı arasından **checkbox** ile mod seçilir:

| Tag                                 | Anlam                                              |
| ----------------------------------- | -------------------------------------------------- |
| `XACT1_CalismaModDepoSeviye`        | ACT 1 kendi depo seviyesine göre açıp/kapanır      |
| `XACT1_CalismaModLinkSeviye`        | ACT 1 link (uzak) depo seviyesine göre çalışır     |
| `XACT2_CalismaModDepoSeviye` / `XACT2_CalismaModLinkSeviye` | ACT 2 …         |
| `XACT3_CalismaModDepoSeviye` / `XACT3_CalismaModLinkSeviye` | ACT 3 …         |
| `XACT4_CalismaModDepoSeviye` / `XACT4_CalismaModLinkSeviye` | ACT 4 …         |
| `XACT5_CalismaModDepoSeviye` / `XACT5_CalismaModLinkSeviye` | ACT 5 …         |
| `XACT6_CalismaModDepoSeviye` / `XACT6_CalismaModLinkSeviye` | ACT 6 …         |

### Per-ACT Vana Yönü

| Tag                              | Anlam                                    |
| -------------------------------- | ---------------------------------------- |
| `XACT{N}_VanaAyarGirisCikis`     | 1 = Giriş vanası, 0 = Çıkış vanası (N=1..6) |
| `XACT{N}_AcmaSeviye` (m)         | Vana açma eşik seviyesi                  |
| `XACT{N}_KapatmaSeviye` (m)      | Vana kapatma eşik seviyesi               |

### ACT Genel Ayarları (per-N)

| Tag                              | Açıklama                       |
| -------------------------------- | ------------------------------ |
| `XVN_ACT{N}_AcilmaZamani` (sn)   | Vana tam açılma süresi         |
| `XVN_ACT{N}_KapanmaZamani` (sn)  | Vana tam kapanma süresi        |
| `XVN_ACT{N}_AktifPasif`          | ACT aktif/pasif                |
| `ACT{N}_Resetle`                 | Reset butonu                   |
| `nACT{N}_Ad`                     | Vana adı (text)                |

### Oransal ACT (`oran_act_{1..4}_ayar.phtml`)

Oransal (analog) vanalar için aynı iki mod + 6 seviye kontrol kademesi:

| Tag                                       | Anlam                                 |
| ----------------------------------------- | ------------------------------------- |
| `XOranACT{N}_CalismaModDepoSeviye`        | Kendi depo seviyesine göre oranlama   |
| `XOranACT{N}_CalismaModLinkSeviye`        | Link (uzak nokta) seviyesine göre     |
| `OranACT{N}_OtoMan`                       | Oto/Manuel seçim (checkbox)           |
| `XOranACT{N}_VanaAyarGirisCikis`          | Giriş/Çıkış seçimi                    |
| `XOranACT{N}_PosManuelOran` (%)           | Manuel çalışmada vana açıklık oranı   |
| `XOranACT{N}_Sev{1..6}AltSeviye` (m)      | Kademe alt seviyesi                   |
| `XOranACT{N}_Sev{1..6}Oran` (%)           | O kademedeki vana açıklık oranı       |
| `XOranACT{N}_Sev{1..6}UstSeviye` (m)      | Kademe üst seviyesi                   |
| `nOransalACT{N}_id`                       | Bağlı link nokta id                   |
| `nOranACT{N}_DepoYukseklik` (m)           | Link depo yüksekliği                  |

### Depo Ölçüleri (`depo_ayar.phtml`)

| Tag                    | Birim |
| ---------------------- | ----- |
| `XD_Depo1Yukseklik`    | m     |
| `XD_Depo1En`           | m     |
| `XD_Depo1Boy`          | m     |
| `XD_Depo2Yukseklik`    | m     |
| `XD_Depo2En`           | m     |
| `XD_Depo2Boy`          | m     |
| `XD_KlorDepoYukseklik` | m     |
| `XD_KlorDepoCap`       | m     |

---

## 2. `a-aqua-cnt-depo-v2` — Sadece İzleme + Klor Linki

Dizinde yalnızca şu panel dosyaları var:
`GENEL.phtml`, `MAIN.phtml`, `MENU.phtml`, `arayuz.phtml`,
`depoAyar.phtml`, `klorLink.phtml`.

**Çalışma modu/switch yok.** Sadece depo geometrisi + düşük güç modu ayarı:

| Tag                         | Anlam                                        |
| --------------------------- | -------------------------------------------- |
| `XD_Depo1Yukseklik/En/Boy`  | Depo ölçüleri (m)                            |
| `DepoTekSeviye`             | 1=Aktif / 0=Pasif (tek depo tekil seviye)    |
| `XE_DusukGucModu`           | Düşük güç modu (aqua-cnt bataryalı cihaz)    |
| `ui_deposeviyepercentaktif` | UI: seviye yüzde gösterimi aç/kapa           |

Klor kontrolü bu node'da **yok**; ayrı bir node'a (`klorLink.phtml`
üzerinden `a-aqua-cnt-depo-klor`) link edilir.

---

## 3. `a-aqua-cnt-depo-klor` — Klorlama Çalışma Modu (XC_CalismaMod)

Kaynak: `klorayar.phtml`

Burada `XC_CalismaMod` kuyu/terfideki gibi **mod switch**'tir, ama anlamı
klorlama türüdür (vv=value):

| vv | XC_CalismaMod Anlamı         |
| -- | ----------------------------- |
| 1  | Link Debi Oransal Klorlama    |
| 2  | Motor Kontrol Klorlama        |
| 3  | Dahili Klorlama               |
| 4  | Link Bakiye Klorlama          |

UI multi-checkbox ile tek bir değer set edilir:
`setname="XC_CalismaMod" setvalue="1|2|3|4" class='ch-multi-akpas set'`.

### Manuel / Otomatik Kontrol

| Tag                          | Açıklama                                  |
| ---------------------------- | ----------------------------------------- |
| `XC_ManuelKlorAc`            | Manuel klor aç (checkbox)                 |
| `XK_ManuelKlorlamaSure`      | Manuel klor verme süresi                  |
| `XC_ManuelAnalogRefVer`      | Manuel analog referans ver                |
| `XC_SistemOtomatikMan`       | Sistem Otomatik/Manuel                    |
| `XC_AnalogMaxRangeCikisSet`  | Analog max range çıkış set                |
| `XC_AnalogManRefCikis`       | Analog manuel referans çıkışı             |

### Dozaj Pompası Giriş/Çıkış Seçimi

Multi-select checkbox grubu (her biri 1 set değeri):

| Tag                           | Değer 1..N        |
| ----------------------------- | ----------------- |
| `XK_DozajPompasiGirisSecim`   | 1..4 (DI1..DI4)   |
| `XK_DozajPompasiCikisSecim`   | 1..2 (DO1..DO2)   |

### Klor PID (Bakiye Klor)

| Tag                              | Açıklama                           |
| -------------------------------- | ---------------------------------- |
| `XK_KlorCalismaAltLimitSet`      | Klor çalışma alt limit             |
| `XK_KlorCalismaUstLimitSet`      | Klor çalışma üst limit             |
| `XK_PidTmrDakikaSet`             | PID Timer (dakika)                 |
| `XK_BakiyeKlorPidSet`            | Bakiye Klor PID hedef              |
| `XK_KlorMinPidCikis`             | Klor min PID çıkış (%)             |
| `XK_KlorMaxPidCikis`             | Klor max PID çıkış (%)             |
| `XK_BakiyeKlorPidYuzde0_5Set`    | Bakiye klor 0-5 aralık PID %       |
| `XK_BakiyeKlorPidYuzde5_15Set`   | 5-15 aralık                        |
| `XK_BakiyeKlorPidYuzde15_35Set`  | 15-35 aralık                       |
| `XK_BakiyeKlorPidYuzde35_70Set`  | 35-70 aralık                       |
| `XK_BakiyeKlorPidYuzde70_100Set` | 70-100 aralık                      |

### Link Debi Oransal Klorlama Parametreleri

| Tag                                      | Açıklama                          |
| ---------------------------------------- | --------------------------------- |
| `XC_AnalogMaxRangeCikisSet`              | Max dozajlama range çıkış         |
| `XK_1m3IcinDozajMiktari`                 | 1 m³ için dozaj miktarı           |
| `XK_DozajlamaToplamDebiSecimLinkDebi{1..8}` | Link debi seçimleri (8 adet)    |
| `XK_DozajlamaToplamDebiSecimDebiG{1..4}` | Lokal giriş debi seçimleri        |
| `XK_DozajlamaToplamDebiSecimDebiC{1..4}` | Lokal çıkış debi seçimleri        |

Diğer klor yardımcı panelleri: `actayar.phtml`, `analogayar.phtml`,
`arayuzayar.phtml`, `cihaz_uyari.phtml`, `depoAyar.phtml`,
`dijitalGirisCikis.phtml`, `klorlink.phtml`, `log.phtml`,
`uisettings.phtml`.

---

## 4. `a-dma-p-v3` — DMA (Pasif İzleme, Mod Yok)

Dizindeki paneller:
`GENEL.phtml`, `MAIN.phtml`, `MENU.phtml`, `analog1_ayar.phtml`,
`cikis_debimetre.phtml`, `debiatama.phtml`, `emniyet_sensor.phtml`,
`giris_debimetre.phtml`, `hwmdata.phtml`, `saha_link.phtml`, `sensor.phtml`.

- **`calismamod.phtml` YOK** — `XC_CalismaModu` veya klor tarzı `XC_CalismaMod`
  switch'i bu node'da **yer almaz**.
- DMA Tez P-versiyonu: giriş/çıkış debimetre, basınç sensörü,
  analog ayar, emniyet sensörü üzerinden **pasif izleme + debi atama** yapar.
- Aktif kontrol (vana açma, pompa komut verme) yoktur. `saha_link.phtml`
  üzerinden komşu noktalara referans verebilir ama lokal kontrol switch'i yok.
- `hwmdata.phtml` HWM (Hydrosave/Halma) logger verisi için.

---

## 5. `a-aqua-cnt-dma-v1.2` — DMA (AquaCnt, Pasif İzleme + IWA)

Dizindeki paneller:
`GENEL.phtml` (+ `GENEL copy.phtml`, `GENELeski.phtml`), `MAIN.phtml`,
`MENU.phtml`, `dma.phtml`, `dma_add.phtml`, `dma_edit.phtml`, `ili.phtml`,
`iwa.phtml`, `iwa_add.phtml`, `iwa_edit.phtml`, `map.phtml`,
`uisettings.phtml`.

- **`calismamod.phtml` YOK.** Tüm UI konfigürasyon + IWA (International Water
  Association) kaçak/MNF göstergeleri + ILI (Infrastructure Leakage Index)
  hesabı etrafında kurgulanmış. Kontrol switch'i, mod seçimi **yoktur**.
- `dma_add.phtml` / `dma_edit.phtml` DMA tanım kayıtları (nokta-bölge
  ilişkisi), çalışma modu değildir.
- Node tamamen **pasif analiz** amaçlıdır.

---

## Araştırma Özeti

| nView                  | calismamod.phtml | Mod switch          | Klor mod      | DMA tip           |
| ---------------------- | ---------------- | ------------------- | ------------- | ----------------- |
| a-depo-envest          | yok              | per-ACT (Depo/Link) | (dozaj ayrı) | —                 |
| a-aqua-cnt-depo-v2     | yok              | —                   | link         | —                 |
| a-aqua-cnt-depo-klor   | yok              | —                   | XC_CalismaMod 1-4 | —            |
| a-dma-p-v3             | yok              | —                   | —             | pasif izleme      |
| a-aqua-cnt-dma-v1.2    | yok              | —                   | —             | pasif izleme+IWA  |

**Kural:** Bu 5 node'da "çalışma modu ne?" sorusu kuyu/terfi
mantığıyla yanıtlanamaz. Doğru yanıt için:

- `a-depo-envest` → hangi ACT için soruluyor, onun `XACT{N}_CalismaMod*`
  checkbox'ları okunur.
- `a-aqua-cnt-depo-klor` → `XC_CalismaMod` (1..4) + Oto/Manuel
  (`XC_SistemOtomatikMan`) birlikte okunur.
- `a-aqua-cnt-depo-v2` → çalışma modu yok, yalnızca `XE_DusukGucModu`.
- `a-dma-p-v3` / `a-aqua-cnt-dma-v1.2` → "DMA pasif izleme node'udur,
  çalışma modu tanımı bulunmaz" cevabı verilmelidir.
