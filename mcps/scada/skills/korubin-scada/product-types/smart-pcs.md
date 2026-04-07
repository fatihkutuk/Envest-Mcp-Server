---
name: product-smart-pcs
description: |
  SMART PCS kompakt tip basinc yonetim alani (BKV) kontrol sistemi.
  Use when: SMART PCS, BKV, basinc yonetim, basinc kirici vana, DMA basinc soruldugunda.
  Keywords: SMART, PCS, BKV, basinc yonetim, vana, aktuator, DMA, basinc kirici.
version: "1.0.0"
---

# SMART PCS - Kompakt Tip Basinc Yonetim Alani (BKV) Kontrol Sistemi

## Genel Bilgi

SMART PCS, basinc yonetim alanlarinin otomatik olarak isletilmesini saglayan tumlesik bir kontrol unitesidir. Adaptif olarak sebeke basincini duzenleyerek su kayip-kacaklarini azaltir.

## Sistem Bilesenleri
1. **Oransal aktuator pilot kontrollu Basinc Kirici Vana (BKV)**
2. **AQUA CNT 100S** kompakt tip kontrol cihazi
3. **Elektromanyetik debimetre** - duz boru mesafesi gerektirmeyen (%0.2 hassasiyet)
4. **Kompakt tip pislik tutucu (filtre)**
5. **3 adet basinc sensoru**:
   - Sistem giris basinci
   - Filtre cikis basinci
   - Sistem cikis basinci
6. **Lityum pil veya kursun-karbon (CGD) aku**, gunes paneli ve sarj regulatoru

## Mekanik Boyut
DN150 cap icin genisligi 110cm - menhollerde kullanilabilir.

## Yetenekler

### Manuel Mod
- Vana acikligi kullanici tarafindan set edilebilir

### Otomatik Isletim
- 12 adet saat diliminin her biri icin kullanicinin set ettigi basinca gore PID kontrolcu ile sebeke basinci otomatik ayarlanir
- Vana cikis basincina veya uc nokta link basincina gore calisabilir

### Alarm / Acil Durum
- Debi ve sistem giris basincinin ust ve alt limitleri tanimlanabilir
- Limit asildiginda cihaz alarmlarini tetikleyecek acil durum senaryolari uretilebilir (orn: BKV ac/kapat)

### Guc Secenekleri
- Elektrik enerjisi olan menhol odalarinda: DC UPS ve SMPS guc kaynagi
- Enerjisiz menhollerde: lityum pil + gunes paneli

## Opsiyonel Elemanlar (Envest Urun Katalogu)
- Ultrasonik debimetre (4-20mA + MODBUS 485)
- Basinc sensoru (0-60 bar, 4-20mA)
- Guc kaynagi (2x 24V DC cikis)
- Enerji analizoru (3 faz, MODBUS 485)
- Elektromanyetik debimetre (+/- 0.5%)
- Hidrostatik seviye sensoru (0-500m, 4-20mA)
- Guc panolari (0.37-200kW)
- Gunes paneli (20-500W)
- Lityum iyon pil paketleri (LS11, LS33, LU11)

## Ilgili nView Ekranlari
- `a-aqua-cnt-dma` - DMA ekrani (SMART PCS ile birlikte kullanilir)
- `a-aqua-cnt-bkv`, `a-aqua-cnt-bkv-c` - BKV ekranlari
