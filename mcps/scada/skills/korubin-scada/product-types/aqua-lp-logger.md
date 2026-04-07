---
name: product-aqua-lp-logger
description: |
  AQUA LP pilli veri toplama ve kaydetme cihazi (Logger).
  Use when: logger, pilli cihaz, veri toplama, rasat kuyusu, AQUA LP soruldugunda.
  Keywords: AQUA, LP, logger, pilli, veri toplama, rasat, low power.
version: "1.0.0"
---

# AQUA LP - Pilli Veri Toplama ve Kaydetme Cihazi (Logger)

## Genel Bilgi

AQUA LP, extreme low power tasarimli, dahili lityum pil ile 5 yila kadar enerjisiz kullanim saglayan pilli veri toplama cihazidir.

## Kullanim Alanlari
- Su sebekelerinde basinc, debi, katodik koruma izleme
- Rasat kuyularinda seviye izleme
- Ortam sicakligi ve nem izleme

## Teknik Ozellikler

- **Guc**: Dusuk guc tuketimi (Extreme Low Power)
- **Pil**: Dahili lityum pil ile 5 yil enerjisiz kullanim*
- **Veri Toplama**: Saatlik ve haftalik veri toplama ve gonderme
- **Uyanma Periyotlari**: 1dk, 10dk, 1saat ayarlanabilir
- **Haberlesme**: Moduler birim - 2G, 4G veya LoRa
- **Analog Giris**: 3 adet (2 adet 4-20mA + 1 adet 0-2V)
- **Sicaklik/Nem**: One-wire sicaklik ve nem sensoru baglanabilir
- **I2C**: I2C sensor girisi
- **Dijital Giris**: 2 adet (sensor ve switch'lerden veri alma ve alarm olusturma)
- **Alarm**: Analog ve dijital girislere alarm tanimlanabilir
- **Haberlesme Protokolu**: HTTPS REST API ile JSON formatinda (web tabanli) konfigurasyon
- **Koruma**: IP65, ABS polimer dis muhafaza
- **Sicaklik**: -30C ile +60C arasi
- **Hafiza**: 8 MB kalici LOG hafiza
- **Sensor Besleme**: 3.6V ve 24V sensor besleme cikisi
- **Besleme**: 3.6V pil veya USB guc beslemesi
- **USB**: USB uzerinden konfigurasyon ayarlari ve offline/modemsiz veri aktarimi
- **LED**: 2 adet durum LED'i (GSM ve islemci)

*Gunde bir kez veri alma ve haftada bir veri gonderimi halinde.

## Ozel Ozellikler
- Uyandirma ve veri gonderme butonu
- USB haberlesme portu uzerinden offline veri aktarimi
- Moduler haberlesme birimi degistirilebilir

## Ilgili Ekranlar
Logger cihazlari genellikle izleme odakli ekranlarda gorunur:
- `a-gozlem-m`, `a-gozlem-v2` - Gozlem ekranlari
- `a-debi-izleme` - Debi izleme
- `a-pressure` - Basinc izleme
