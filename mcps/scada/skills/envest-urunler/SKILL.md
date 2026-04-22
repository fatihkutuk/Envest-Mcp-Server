---
name: envest-urunler
description: |
  Envest firmasının ürün dokümanları (AQUA CNT 100/80, LP Logger, SMART PCS, PLC ailesi).
  Teknik özellikler, montaj, kablo bağlantısı, LED anlamları, MODBUS haritaları, alarm kodları.
  Use when: kullanıcı Envest ürünleri hakkında soru sorduğunda (AQUA, CNT, SMART PCS, CP100/110/120, OCP vb.).
  Keywords: AQUA CNT, SMART PCS, LP Logger, CP100GM, CP110GM, CC120GM, OCP110, MODBUS, BKV, pompa kontrol.
version: "1.0.0"
---

# Envest Ürün Dokümanları

## İçerik

### Ürün Dokümanları (`products/`)

| Dosya | İçerik |
|-------|--------|
| [aqua-cnt-100.md](products/aqua-cnt-100.md) | AQUA CNT 100 (S/F/FP/SL) detaylı kullanım kılavuzu |
| [aqua-cnt-100-ozet.md](products/aqua-cnt-100-ozet.md) | AQUA CNT 100 kataloğ özeti |
| [aqua-cnt-80.md](products/aqua-cnt-80.md) | AQUA CNT 80 LoRa/GSM pompa-depo kontrol |
| [aqua-lp-logger.md](products/aqua-lp-logger.md) | AQUA LP Logger pilli veri toplama |
| [smart-pcs.md](products/smart-pcs.md) | SMART PCS BKV kontrol sistemi |
| [plc-katalogu.md](products/plc-katalogu.md) | PLC / RTU ürün ailesi (CP100GM, CP110GM, OCP110 vb.) |

### Firma Bilgisi
- [company-intro.md](company-intro.md) — Envest firma tanıtımı

## Kullanım Rehberi

Kullanıcı bir ürün sorduğunda:
1. `list_skills` çıktısında bu skill'i gör
2. İlgili alt dosyayı `get_skill('envest-urunler', 'products/<dosya>.md')` ile oku
3. Ürün bazlı spesifik sorularda doğrudan ilgili dosyaya git

## Notlar
- **OCR gerekli**: `AQUA CNT CE Uygunluk Sertifikası 2022` ve `AQUA SMART PCS Broşür 2022` PDF'leri taranmış görsel formatta — metin çıkarılamadı. Gerekirse manuel eklenir.
- Kaynak PDF'ler `C:\Users\user\Downloads\pdfler\` dizininde.
