---
name: device-pressure-sensor
description: |
  Basinc sensoru bilgisi.
  Use when: basinc olcumu, hat basinci, kuyu cikis basinci soruldugunda.
  Keywords: basinc, pressure, sensor, bar, hat, kuyu cikis, BasincSensoru.
version: "1.0.0"
---

# Basinc Sensoru (Pressure Sensor)

## Sensor Tipi

### Basinc Sensoru
- Olcum araligi: 0-60 bar'a kadar
- Hassasiyet: %0.3
- Cikis: 4-20mA analog

## Basinc Tag Turleri

### Kuyu Cikis Basinci (Birincil)
Kuyu cikisindaki basinc, pompa performansinin ana gostergesi.
- Tag: `BasincSensoru`, `basıncsensoru`, `BasincSensoru`, `kuyucikis`
- Birim: bar

### Hat Basinci (Ikincil)
Dagitim hattindaki basinc, sebekeye verilen basinc.
- Tag: `BasincSensoru2`, `HatBasincSensoru`, `hatbasincsensoru`, `hatbasıncsensoru`
- Birim: bar

### Giris/Cikis Basinci (Terfi/Depo)
- `GirisBasincSensoru`, `GirisBasinc` - Giris basinci
- `CikisBasincSensoru`, `CikisBasinc` - Cikis basinci
- `T_Basinc` - Hesaplanmis basinc

## Arama Stratejisi

Kullanici "basinc" dediginde:
- "hat" kelimesi varsa: hat basinc tagleri oncelikli
- "kuyu" + "cikis" varsa: kuyu cikis basinc tagleri
- Belirtilmemisse: hem kuyu cikis hem hat basinc tagleri aranir

## Sensor Ayarlari (sensor.phtml)

### Kuyu Cikis Basinc Sensoru
| Tag | Aciklama | Birim |
|-----|----------|-------|
| `XS_BasincSensoruMax` | 20mA degeri (tam skala) | bar |
| `XS_BasincSensoruKalibre` | Kalibrasyon offset (+/-) | bar |
| `XA_BasincSensoruAkim` | Anlik 4-20mA degeri | mA |
| `BasincSensoru` | Anlik basinc degeri | bar |

### Hat Basinc Sensoru
| Tag | Aciklama | Birim |
|-----|----------|-------|
| `XS_HatBasincMax` | 20mA degeri (tam skala) | bar |
| `XS_HatBasincKalibre` | Kalibrasyon offset (+/-) | bar |
| `XA_HatBasincSensoruAkim` | Anlik 4-20mA degeri | mA |
| `BasincSensoru2` | Anlik hat basinci | bar |

## Basinc -> Basma Yuksekligi Donusumu

Hm (basma yuksekligi) tag'i yoksa basinc'tan hesaplanir:
```
Hm (metre) = Basinc (bar) x 10.197
```

## SMART PCS (Basinc Yonetim Alani)

SMART PCS urununde 3 adet basinc sensoru bulunur:
1. Sistem giris basinci
2. Filtre cikis basinci
3. Sistem cikis basinci

PID kontrolcu ile vana acikligi otomatik ayarlanarak sebeke basinci optimize edilir.

## Emniyet Limitleri

Basinc emniyet parametreleri (emniyet.phtml):
- `XE_BasincAlt` - Basinc alt siniri (bar)
- `XE_BasincUst` - Basinc ust siniri (bar)
- `XE_BasincSure` - Gecikme suresi (sn)
- `XE_BasincEylem` - Sinir asildiginda pompa dursun mu
