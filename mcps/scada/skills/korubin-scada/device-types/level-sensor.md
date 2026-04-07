---
name: device-level-sensor
description: |
  Seviye sensoru bilgisi.
  Use when: su seviyesi, depo seviyesi, kuyu seviyesi, statik/dinamik seviye soruldugunda.
  Keywords: seviye, level, sensor, statik, dinamik, depo, kuyu, SuSeviye, hidrostatik.
version: "1.0.0"
---

# Seviye Sensoru (Level Sensor)

## Sensor Tipi

### Hidrostatik Seviye Sensoru
- Olcum araligi: 0-500 metreye kadar
- Hassasiyet: %0.3
- Cikis: 4-20mA analog
- Kullanim: Kuyu su seviyesi, depo seviyesi

## Seviye Turleri

### Dinamik Seviye (Kuyu)
Pompa calisirken kuyu icindeki su seviyesi. Pompa calisdikca duser.
- Tag: `SuSeviye`, `suseviye`, `dinamikseviye`, `dinamik seviye`

### Statik Seviye (Kuyu)
Pompa durunca kuyu icindeki dengede su seviyesi.
- Tag: `StatikSuSeviye`, `statikseviye`, `statik`

### Depo Seviyesi
Su deposundaki su seviyesi (metre veya %).
- Tag: `DepoSeviye`, `SuSeviye` (depo baglaminda)

### Genel Seviye
Tipe bagli olmadan genel seviye olcumu.
- Tag: `suseviye`, `su seviye`, `seviye`, `level`, `SuSeviye`

## Arama Stratejisi

Kullanici "seviye" dediginde:
- "statik" kelimesi varsa: `StatikSuSeviye`, `statikseviye`, `statik`
- "dinamik" kelimesi varsa: `SuSeviye`, `suseviye`, `dinamikseviye`, `dinamik seviye`
- Belirtilmemisse (genel): `suseviye`, `su seviye`, `seviye`, `level`, `SuSeviye`

## Seviye Ayarlari (sensor.phtml)

Tipik ayar parametreleri:
- `XS_SeviyeSensoruMax` - Seviye sensoru max degeri (metre)
- `XS_SeviyeKalibre` - Kalibrasyon offset
- `XA_SeviyeAkim` - Anlik 4-20mA degeri (mA)

## Seviye Kontrol (seviye_kontrol.phtml)

Samandira ve seviye bazli kontrol:
- Depo dolu/bos seviyeleri
- Pompa baslatma/durdurma seviyeleri
- Tasmadan koruma

## Analiz Araclari

| Arac | Kullanim |
|------|----------|
| `analyze_seasonal_level_profile(nodeId, tagHint="SuSeviye")` | Mevsimsel seviye profili (saatlik ortalama + K-Means) |
| `analyze_log_trend(nodeId, tagHint="SuSeviye", mode="long_term")` | Uzun vadeli seviye trendi (yillik dusus vb.) |
| `get_chart_data(nodeId, logParamId)` | Tarihsel seviye grafigi |

## Onemli Notlar
- Kuyu dinamik seviyesi pompanin calisma durumuna bagli olarak degisir
- Statik seviye genelde gece saatlerinde (pompa duruyorken) olculur
- Mevsimsel analiz: yaz aylarinda seviye dusumu, kis aylarinda toparlanma beklenir
- Yillik dusus trendi: yeraltı su kaynaklarinin tukenme riski gostergesi
