---
name: product-aqua-cnt-80
description: |
  AQUA CNT 80 LoRa ve GSM destekli pompa-depo kontrol cihazi.
  Use when: AQUA CNT 80, LoRa, WiFi cihaz, pompa-depo haberlesme soruldugunda.
  Keywords: AQUA, CNT, 80, LoRa, WiFi, pompa, depo, kontrol.
version: "1.0.0"
---

# AQUA CNT 80 - LoRa ve GSM Destekli Pompa-Depo Kontrol Cihazi

## Genel Bilgi

AQUA CNT 80, dalgic ve inline pompa kontrolu ile su deposu izleme icin tasarlanmis, WiFi ve LoRa haberlesme destekli kontrol cihazidir.

## Kullanim Alanlari
- Dalgic ve inline pompa kontrolu
- Su deposu izleme
- Su sebekelerinde basinc ve debi izleme
- Rasat kuyularinda seviye izleme

## Teknik Ozellikler

- **Haberlesme**: Dahili WiFi birim
- **MODBUS**: TCP Master ve Slave (ayni anda en fazla 5 baglanti)
- **Analog Giris**: 2 adet (12-bit) 4-20mA
- **Dijital Giris**: 3 adet
- **Dijital Cikis**: 2 adet (transistorlu)
- **I/O Tablosu**: Dahili atanabilir giris/cikis tablosu
- **Sicaklik**: -30C ile +60C arasi
- **Besleme**: 24 VDC giris beslemesi
- **Sensor Cikis**: 24 VDC 200mA sensor besleme cikisi
- **Gunes Paneli**: Dahili regulator ile 50W, 15V-24V cikisli panellerle dogrudan calisabilir
- **Batarya**: Batarya yonetim birimi (DC UPS + sarj)
- **IP Filtreleme**: Internet IP filtreleme ve APN destegi
- **Koruma**: IP65, ABS polimer dis muhafaza
- **WiFi Konfigürasyon**: WiFi uzerinden mobil uygulama ile konfigurasyon
- **LED**: 5 adet durum LED'i
- **Alarm**: Analog ve dijital girislere alarm tanimlanabilir

## Isletme Senaryolari
- Depo doldurma modu
- Hidrofor modu

## Opsiyonel Ozellikler
- **LoRa**: 868 MHz LoRa destegi - pompa-depo arasi haberlesme (acik alan 10 km)
- **Batarya**: 11.2V 5.6A lityum pil
- **Moduler haberlesme**: 2G, 4G veya Ethernet secenekleri

## Ilgili nView Ekranlari
- `a-aqua-cnt-kuyu` - AQUA CNT kuyu (dusuk guclu versiyon)
- `a-aqua-cnt-depo` - AQUA CNT depo
- `a-aqua-cnt-lowpower` - Dusuk guc modu
