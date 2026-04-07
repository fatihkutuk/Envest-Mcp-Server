---
name: product-aqua-cnt-100
description: |
  AQUA CNT 100 kompakt tip pompa kontrol ve su izleme cihazi.
  Use when: AQUA CNT 100, pompa kontrol cihazi, Envest cihaz, Koru1000 soruldugunda.
  Keywords: AQUA, CNT, 100, pompa kontrol, kompakt, 100F, 100S, Envest.
version: "1.0.0"
---

# AQUA CNT 100 - Kompakt Tip Pompa Kontrol ve Su Izleme Cihazi

## Genel Bilgi

AQUA CNT 100, icme suyu temin ve dagitimi icin tasarlanmis kompakt tip saha kontrol cihazidir. Derin kuyu dalgic pompa kontrolu, terfi istasyonu pompa kontrolu, su dagitim deposu izleme ve izole alt olcum bolgesi (DMA) basinc/debi izleme amaciyla kullanilir.

## Model Varyantlari

| Model | Ozellik |
|-------|---------|
| AQUA CNT 100S | Harici debimetre baglanabilir (standart) |
| AQUA CNT 100F | Dahili ultrasonik debimetre modulu ve clamp-on problar |

## Teknik Ozellikler

- **Islemci**: Dusuk guc tuketimli mikrodenetleyici
- **Ekran**: LCD (64x128 grafik) + membran tus takimi
- **Haberlesme**: GSM/GPRS modem + harici anten
- **Batarya**: 14.8V 11.2A lityum pil (DC UPS + sarj yonetimi)
- **Hafiza**: 8 MB dahili kalici hafiza
- **Analog Giris**: 3 adet (16-bit) - 4-20mA
- **Analog Cikis**: 1 adet (12-bit)
- **Dijital Giris**: 4 adet
- **Dijital Cikis**: 2 adet (roleli)
- **MODBUS**: TCP Master ve Slave (ayni anda en fazla 5 baglanti)
- **IP Filtreleme**: Internet IP filtreleme ve APN destegi
- **Koruma**: IP65, ABS polimer dis muhafaza
- **Sicaklik**: -20C ile +60C arasi
- **Gunes Paneli**: Dahili regulator ile 100W, 15V-24V cikisli panellerle calisabilir
- **CE**: TS EN 61000-6-1 ve TS EN 61000-6-3 uygunluk sertifikasi

## Opsiyonel Ozellikler
- RTC (gercek zaman saati) GSM uzerinden guncelleme

## I/O Tablosu
Dahili atanabilir I/O (giris/cikis) tablosu vardir. Sensor ve dijital girislerden veri alma ve alarm olusturma desteklenir.

## Kullanim Alanlari
- Icme suyu temini: derin kuyu dalgic pompa kontrolu
- Terfi istasyonu pompa kontrolu
- Su dagitim deposu izleme
- Izole alt olcum bolgesi (DMA) basinc ve debi izleme
- Tarimsal sulama

## Ilgili nView Ekranlari
- `a-aqua-cnt-kuyu` - AQUA CNT kuyu ekrani
- `a-aqua-cnt-terfi` - AQUA CNT terfi ekrani
- `a-aqua-cnt-depo` - AQUA CNT depo ekrani
- `a-aqua-cnt-dma` - AQUA CNT DMA ekrani
- `a-aqua-cnt-kuyu-v2`, `a-aqua-cnt-terfi-v2`, `a-aqua-cnt-depo-v2` - V2 versiyonlari

## MCP Araclari
Urun detaylari icin cihaz/saha tag aramalari degil, urun dokuman araclari kullanilir:
- `get_product_specs` - Urun teknik ozellikleri
- `search_product_manual` - Kilavuzda arama
- `get_product_settings` - Urun ayarlari
- `get_product_troubleshoot` - Ariza giderme
- `get_product_sensor_info` - Sensor bilgisi
