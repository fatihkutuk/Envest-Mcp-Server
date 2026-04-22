---
name: tag-naming
description: |
  SCADA tag adlandirma kurallari ve onek anlamlari.
  Use when: tag isimlerini yorumlamak, tag aramak, yeni tag anlamak, veya ayar/sensor/sayac tag'lerini ayirt etmek gerektiginde.
  Keywords: tag, onek, prefix, xe_, xa_, xc_, xd_, xs_, xv_, al_, t_, an_, x_, debimetre, basinc, sayac.
version: "2.0.0"
---

# Korubin SCADA Tag Adlandirma Kurallari

## Onek (Prefix) Kurallari — Detayli

| Onek | Anlam | Aciklama | Ornek |
|------|-------|----------|-------|
| `al_` | Cihaz alarmi | Cihazin urettigi alarm bitleri | `al_Termik`, `al_KuruCalisma`, `al_FazKaybi` |
| `XE_` | **Emniyet ayari** | Frekans/voltaj/akim/basinc limitleri, sure ve eylem | `XE_FrekansAlt`, `XE_VoltajUst`, `XE_AkimSure`, `XE_BasincEylem` |
| `XD_` | **Depo ayari** | Depo seviye limitleri, doldurma/bosaltma parametreleri | `XD_DepoMin`, `XD_DepoMax`, `XD_BasmaYukseklik` |
| `XA_` | **Analog giris ayari** | Analog giris 4-20mA/0-10V kalibrasyonu | `XA_Analog1Min`, `XA_Analog1Max`, `XA_BasincSensoruAkim` |
| `XC_` | **Kontrol ayari** | Calisma modu, PID, otomasyon kurallari | `XC_CalismaMod`, `XC_PidKp`, `XC_HedefBasinc` |
| `XS_` | **Sensor ayari** | Sensor tipi, range, kalibre, offset | `XS_BasincSensoruMax`, `XS_SeviyeKalibre`, `XS_DebimetreRange` |
| `XV_` | **Vana/Aktuator** | Vana aktiflik, aktuator pozisyon limiti | `XV_VanaAktif`, `XV_AkutatorMax` |
| `T_` | **Sayac (counter)** | Toplam/kumulatif sayici | `T_ToplamDebi`, `T_CalismaSuresi` |
| `T_...S` | **Sunucu sayaci** | T_ ile baslayip S ile biten: sunucu tarafinda sayiyor | `T_ToplamDebiS`, `T_GuncS` |
| `T_...` (S yok) | **Cihaz sayaci** | Cihazdan direkt okunan sayaci | `T_ToplamDebi`, `T_Enerji` |
| `An_` | Analizor anlik deger | Enerji/frekans analizoru | `An_Guc`, `An_SebFrekans`, `An_OrtVoltaj`, `An_OrtAkim` |
| `x_` (genel) | Ayar/setpoint | Tum X ile baslayanlar konfigurasyon | Yukaridaki alt onekler |

### KRITIK: X ile baslayan = AYAR (canli deger DEGIL!)
- `XS_DebimetreMax` → debinin gercek degeri degil, **sensorun max degeri** (yani sensorun olcebilecegi tavan)
- `XD_BasmaYukseklik` → gercek basma degeri degil, **sabit ayar** (pompa kataloguna girilmis)
- `XC_CalismaMod` → calisma mod **secimi** (otomatik/elle/kapali), durumu degil

### KRITIK: T_ ile baslayan = KUMULATIF SAYAC
- `T_ToplamDebi` veya `T_ToplamDebimetre` → toplam gecen su (m3)
- Iki tarih arasindaki farki al: `son_endeks - ilk_endeks` = o tarih aralindaki uretim
- Sonunda `S` varsa sunucu sayiyor (daha guvenilir), yoksa cihaz sayiyor (reset/sifirlanma riski)

## Ekran Tipine Gore Degiskenlik

Ayni islev farkli ekranlarda farkli tag ismiyle olabilir:

| Ekran Tipi | Debi Max Tag | Kalibre Tag |
|-----------|-------------|-------------|
| `a-kuyu-envest` | `XS_DebimetreMax` | `XS_DebimetreKalibre` |
| `a-kuyu-envest-v2` | `XS_DebimetreRange` | `XS_DebimetreKal` |
| `a-aqua-cnt-kuyu-v2` | `XS_Debi_Max` | `XS_Debi_Kalibre` |

**Suphede ne yap?**
1. Panelde o sayfaya bak: `https://<panel_base_url>/panel/point/<node_id>/<menu>` (orn: `/emniyet`, `/sensor`, `/debimetre`). Detay icin `conventions/panel-routing.md` skill'ine bak
2. Veya `search_tags(deviceId=nodeId, pattern="*Debi*")` ile dinamik tara
3. Veya `get_device_data(deviceId=nodeId)` ile tum tag'leri listele

## Yaygin Tag Isimleri

### CANLI Izleme (ayar degil, olcum!)
- `Debimetre`, `Debimetre1`, `Debimetre2` - **m3/h** cinsinden anlik akis (default birim)
- `DebimetreLtSn`, `LtSn`, `Qltsn` - **Lt/sn** (eger adinda belirtilmisse). Lt/sn → m3/h icin x3.6
- `SuSeviye` / `dinamikseviye` - Dinamik su seviyesi
- `StatikSuSeviye` / `statikseviye` - Statik seviye (pompa dururken)
- `BasincSensoru` - Birincil basinc (bar) - kuyu cikisi
- `BasincSensoru2` / `HatBasincSensoru` - Hat basinci (bar)
- `ToplamHm` - Toplam basma yuksekligi (metre) **← pompa secimi icin bunu kullan!**
- `An_Guc` / `P1_Guc` - Motor gucu (kW)
- `KlorSensoru` / `BakiyeKlor` - Bakiye klor

### KRITIK: DEBI BIRIMI
**Varsayilan birim m3/h'tir. Aksi belirtilmedikce (tag adinda LtSn/Ltsn/LT_SN gecmedikce) debi m3/h kabul edilir.**

### Pompa Durumu (CANLI)
- `Pompa1StartStopDurumu`, `Pompa2StartStopDurumu` - Pompa start/stop durumu (1=acik, 0=kapali)
- `PompaStartStopDurumu` - Tek pompa durumu
- `PompaCalismaDurumu`, `Pompa1Calisiyor` - Calisiyor mu durumu
- `P1_Durum`, `P2_Durum` - Eski ekranlarda pompa durumu

**Ekran tipine gore degisir:**
- `a-aqua-cnt-kuyu-v2` → `Pompa1StartStopDurumu`
- `a-kuyu-envest` → `P1_Durum` veya `PompaStartStopDurumu`

## Birim Donusumleri

| Kaynak birim | Hedef birim | Carpan |
|-------------|-------------|--------|
| Lt/sn | m3/h | × 3.6 |
| bar | mSS (metre su sutunu / Hm) | × 10.197 |
| kPa | bar | ÷ 100 |
| mbar | bar | ÷ 1000 |

## Degeri Yuvarlamama Kurali

**Sensor/tag degerleri AYNEN kullanilmali.**
- `ToplamHm=131.45` → pompa seciminde `131.45` gonder, `131` degil
- `Debimetre=157.82` → `157.82` gonder, `160` degil
- Yuvarlama yalnizca **kullaniciya gosterirken** yapilir, islem/sorgulamalarda ham deger kullanilir

## Panel Referansi

Tag tanimlari panel sayfalarinda (emniyet, sensor, debimetre vb.) gorunur. Kullaniciya panel URL'si ile yonlendir:

```
https://<panel_base_url>/panel/point/<node_id>/<menu>
```

Ornekler:
- `/emniyet` → XE_ tag'leri (emniyet limitleri)
- `/sensor` → XS_ tag'leri (sensor kalibre/max)
- `/depo` → XD_ tag'leri (depo ayarlari)
- `/pid` veya `/calismamod` → XC_ tag'leri (kontrol/mod)
- `/debimetre` → Debimetre ayarlari

Detay icin `conventions/panel-routing.md` skill'ine bak. Iç dosya yolu veya IP KULLANMA.

## Onemli Not
- Gercek tag yollari projeye gore degisir
- Suphede `search_tags` veya `get_device_data` ile dogrulayin
- Ekran tipine ozel sabit tanimli degilse yukaridaki varsayilanlar gecerlidir
- `X` ile baslayan = AYAR (setpoint), canli olcum DEGIL
- `T_` ile baslayan = SAYAC (kumulatif toplam)
