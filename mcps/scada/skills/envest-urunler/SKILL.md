---
name: envest-urunler
description: |
  Envest firmasının RESMİ ÜRÜN KATALOĞU ve teknik dökümanları.
  AQUA CNT 100 (S/F/FP/SL), AQUA CNT 80 (LoRa/GSM), AQUA LP Logger (pilli veri toplama),
  AQUA SMART PCS (BKV/basınç yönetim), PLC/RTU ailesi (CP100-GM, CP110-GM, CP120-GM, CP130-GM,
  CP140-GM, CS100/101/110/111/120/121/130/140/141/150-GM, CC100/110/120-GM, OCP110), güç panoları
  (M100 kontaktör, M200 soft starter, M300-DF frekans konvertörü), sensörler (basınç, seviye,
  ultrasonik/elektromanyetik debimetre, enerji analizörü, güneş paneli, lityum pil).
  Use when: kullanıcı ÜRÜN tanıtımı, ürün kataloğu, hangi ürünler, ürün portföyü, hangi modeller,
  ürün seçimi, teknik özellikler, modbus haritası, kablo bağlantısı, LED, alarm kodu,
  montaj, kılavuz, BKV, pompa kontrol cihazı gibi ürün-seviyesi sorularında. SCADA canlı veri
  DEĞİL, cihaz/ürün sorusu için bu skill kullanılır.
  Keywords: ürün, ürünler, ürün tanıtımı, ürün kataloğu, ürün portföyü, envest ürün,
  hangi ürünler, hangi modeller, ürün listesi, cihaz, katalog, broşür, kılavuz, manual,
  AQUA, AQUA CNT, 100S, 100F, 100FP, 100SL, AQUA CNT 80, LP Logger, SMART PCS, BKV,
  basınç yönetim alanı, CP100GM, CP110GM, CP120GM, CP130GM, CP140GM, CS100GM, CS110GM,
  CS120GM, CC100GM, CC110GM, CC120GM, OCP110, M100, M200, M300, M300-DF, kontaktör,
  soft starter, frekans konvertörü, VFD, ultrasonik debimetre, elektromanyetik debimetre,
  enerji analizörü, basınç sensörü, hidrostatik seviye, güneş paneli, lityum pil,
  MODBUS, TCP, RTU, LoRa, GSM, GPRS, APN, CSQ, LED, alarm kodu, modem status, register,
  kablo bağlantı, montaj, IP65, teknik özellik, firma tanıtımı.
version: "1.1.0"
---

# Envest Ürün Dokümanları

> **Bu skill Envest'in gerçek ürün kataloğudur** — SCADA DB'deki iç `node_product_type` tablosu DEĞİL.
> Kullanıcı "hangi ürünler var", "ürün tanıtımı", "katalog" gibi sorduğunda **buradan yanıtla**.
> `list_product_types` SCADA tool'u SCADA'ya kayıtlı node tiplerini listeler, gerçek ürün ailesi değil.

## İçerik — Ürün Aileleri

### 1. AQUA CNT Kompakt Kontrol Cihazları

| Dosya | Ürün | Özet |
|-------|------|------|
| [products/aqua-cnt-100.md](products/aqua-cnt-100.md) | **AQUA CNT 100** (S / F / FP / SL) | Kompakt pompa kontrol + su izleme. Derin kuyu, terfi, DMA, içme suyu depoları. 4 alt model. 39KB detaylı kılavuz. |
| [products/aqua-cnt-100-ozet.md](products/aqua-cnt-100-ozet.md) | AQUA CNT 100 özet | Katalog özet — 100F vs 100S farkı |
| [products/aqua-cnt-80.md](products/aqua-cnt-80.md) | **AQUA CNT 80** | LoRa + GSM destekli pompa-depo kontrol. Pompa-depo arası 10 km açık alan haberleşme. |

### 2. Veri Toplama & Alan Ölçümü

| Dosya | Ürün | Özet |
|-------|------|------|
| [products/aqua-lp-logger.md](products/aqua-lp-logger.md) | **AQUA LP Logger** | Pilli veri toplama (Extreme Low Power). Dahili lityum pil ile 5 yıl enerjisiz. Basınç, debi, katodik koruma, rasat kuyusu izleme. 2G/4G/LoRa modüler. |
| [products/smart-pcs.md](products/smart-pcs.md) | **AQUA SMART PCS** | Kompakt tip Basınç Yönetim Alanı (BKV) kontrol sistemi. Oransal BKV + AQUA CNT 100S + debimetre + basınç sensörleri. 12 saat dilimli PID. |

### 3. PLC / RTU Ürün Ailesi (Koru1000 Serisi)

| Dosya | Kapsam |
|-------|--------|
| [products/plc-katalogu.md](products/plc-katalogu.md) | **18 PLC + 3 güç panosu + 5 sensör** |

Detay:
- **CP Serisi (Kuyu & Terfi):** CP100-GM, CP110-GM, CP120-GM, CP130-GM, CP140-GM
- **CS Serisi (Depo & Gözlem):** CS100-GM, CS101-GM, CS110-GM, CS111-GM, CS120-GM, CS121-GM, CS130-GM, CS140-GM, CS141-GM, CS150-GM
- **CC Serisi (Atıksu Terfi):** CC100-GM, CC110-GM, CC120-GM
- **M Serisi (Güç Panoları):** M100 (kontaktör), M200 (soft starter), M300-DF (frekans konvertörü — Tip 1/2/3)
- **Sensörler:** TR-11 sıcaklık, BT-214-G1 basınç, PTL-110 hidrostatik seviye, ultrasonik & elektromanyetik debimetre

### 4. Firma Bilgisi

| Dosya | Özet |
|-------|------|
| [company-intro.md](company-intro.md) | Envest firma tanıtımı, faaliyet alanları, sektörel referanslar |

---

## Kullanım Rehberi

### "Hangi ürünler var" / "ürün tanıtımı" / "katalog"
→ **Bu SKILL.md** dosyasını kullanıcıya sun. Yukarıdaki 4 kategoriyi kısaca anlat.
Detay isteniyorsa alt dosyayı oku.

### "AQUA CNT nedir" / spesifik model sorusu
→ `get_skill('envest-urunler', 'products/<dosya>.md')` ile ilgili ürün dosyasını oku.

### "CP110-GM kaç dijital giriş var" / PLC teknik detay
→ `get_skill('envest-urunler', 'products/plc-katalogu.md')` + aranan modele bak.

### "Modem status 2 ne demek" / AQUA CNT cihaz-içi konu
→ Bu skill yerine `aqua-devices` skill'ini kullan (daha detaylı tag/register bilgisi).

---

## ÖNEMLI — Hangi skill vs tool ne zaman?

| Soru | Doğru yer |
|------|-----------|
| "Envest'in hangi ürünleri var" | **envest-urunler/SKILL.md** (bu dosya) |
| "AQUA CNT 100 nasıl montaj edilir" | **envest-urunler/products/aqua-cnt-100.md** |
| "AQUA modem status 2" | **aqua-devices/modem-status.md** |
| "Şu anda kaç aktif alarm var" | `<prefix>_get_active_alarms` (SCADA tool) |
| "Serbest Bölge Kuyu hangi pompa" | `<prefix>_get_installed_pump_info` (SCADA tool) |
| "SCADA'da kaç farklı node tipi kayıtlı" | `<prefix>_list_product_types` (SCADA tool) — iç kayıt, gerçek ürün portföyü DEĞİL |

---

## Notlar
- **OCR gerekli:** `AQUA CNT CE Uygunluk Sertifikası 2022` ve `AQUA SMART PCS Broşür 2022` PDF'leri taranmış görsel — metin çıkarılamadı. İçerik eklenmesi istenirse manuel paylaşılabilir.
- Kaynak PDF'ler Envest web sitesinde: `https://envest.com.tr/tr/76-dokumanlar/`
