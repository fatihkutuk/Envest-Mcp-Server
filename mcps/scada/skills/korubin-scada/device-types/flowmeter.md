---
name: device-flowmeter
description: |
  Debimetre (akis olcer) bilgisi.
  Use when: debimetre ayarlari, debi olcumu, akis hizi soruldugunda.
  Keywords: debimetre, flowmeter, debi, akis, flow, m3/h, Lt/sn, ultrasonik, elektromanyetik.
version: "1.0.0"
---

# Debimetre (Flowmeter)

## Debimetre Tipleri

### Ultrasonik Debimetre
- Olcum araligi: -12...+12 m/s
- Hassasiyet: +/- 1%
- Cikislar: 4-20mA analog + MODBUS 485
- Clamp-on problar (AQUA CNT 100F modelinde dahili modul)

### Elektromanyetik Debimetre
- Olcum araligi: -12...+12 m/s
- Hassasiyet: +/- 0.5% (daha hassas)
- Cikislar: 4-20mA analog + MODBUS 485
- Duz boru mesafesi gerektirmez (SMART PCS'de kullanilir)

## Tag Isimleri

### m3/h Biriminde Taglar
- `Debimetre` - Birincil debimetre
- `Debimetre1`, `Debimetre2`, ... `Debimetre7` - Numarali debimetreler
- `T_Debi` - Hesaplanmis toplam debi
- `GirisToplamDebi` - Giris toplam (depo/DMA)
- `CikisToplamDebimetre` - Cikis toplam (depo/DMA)
- `CikisAnlikDebi` - Cikis anlik debi
- `DebiM3h`, `Debi_m3h`, `AnlikDebiM3h`, `Qm3h` - m3/h acik yazilmis

### Lt/sn Biriminde Taglar
- `T_DebiLtSn`, `DebimetreLtSn`, `LtSn`, `LT_SN` - Lt/sn
- `DebiLtSn`, `AnlikDebiLtSn`, `DebiLs`, `Debi_ls` - Alternatif yazimlar
- `QltSn`, `QLtsn`, `LitreSn`, `Litre_Sn`, `DebimetreLt` - Diger varyantlar

**Donusum**: 1 Lt/sn = 3.6 m3/h

## Debimetre Ayarlari (debimetre.phtml)

Tipik ayar parametreleri:
- `XS_DebimetreMax` - Debimetre 20mA degeri (m3/h veya Lt/sn)
- `XS_DebimetreKalibre` - Kalibrasyon offset
- `XA_DebimetreAkim` - Anlik 4-20mA degeri (mA)

## Arama Stratejisi

Kullanici "debi" dediginde asagidaki parcalar aranir:
```
debimetre, debimetre1, debimetre2, demimetre, deminetre, debi, akis, akis, flow
```

Yaygin yazim hatalari da dahil edilir: `demimetre`, `deminetre`

## Depo/DMA Ekranlarinda Coklu Debimetre

Depo ve DMA ekranlarinda 7'ye kadar debimetre destegi vardir:
- `giris_debimetre` - Giris debimetre ayari
- `cikis_debimetre` - Cikis debimetre ayari
- `debimetre3` ... `debimetre7` - Ek debimetreler
- `pompa_debi_link` - Hangi pompanin hangi debimetreye bagli oldugu

## Veri Sorgulama
- `get_device_tag_values(deviceId, tagNames=["Debimetre"])` - Anlik deger
- `get_chart_data(nodeId, logParamId, start, end)` - Tarihsel debi grafigi
- `analyze_dma_seasonal_demand(nodeId)` - DMA debi K-Means profili
- `compare_log_metrics(nodeId, primaryTagHint="debi", secondaryTagHint="basinc")` - Debi-basinc karsilastirma
