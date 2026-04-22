---
name: aqua-cnt-80
description: |
  AQUA CNT 80 LORA ve GSM destekli Pompa-Depo Kontrol Cihazı. Dalgıç/inline pompa kontrolü, su deposu izleme, şebeke basınç ve debi izleme için kullanılır. Dahili Wi-Fi, MODBUS TCP, LoRa (opsiyonel) ve güneş paneli desteği sunar.
  Use when: kullanıcı AQUA CNT 80, pompa-depo kontrolü, LoRa haberleşmeli pompa kontrolü, Wi-Fi üzerinden konfigürasyon veya hidrofor modu gibi konular hakkında soru sorduğunda.
  Keywords: AQUA CNT 80, pompa kontrol, depo kontrol, LoRa, GSM, Wi-Fi, MODBUS TCP, hidrofor modu, depo doldurma, 868 MHz, güneş paneli, dalgıç pompa, terfi
version: "1.0.0"
source_pdf: "AQUA Ürün Kataloğu 2026"
---

# AQUA CNT 80 LORA ve GSM Destekli Pompa-Depo Kontrol Cihazı

AQUA CNT 80, dalgıç veya inline pompaların kontrol edilmesi, su depolarının seviye izlenmesi ve şebeke basınç/debi takibi için tasarlanmış kompakt bir kontrol cihazıdır. Dahili Wi-Fi ile sahada mobil uygulama üzerinden konfigüre edilebilir; opsiyonel LoRa modülü sayesinde pompa ile depo arasında kablosuz haberleşme sağlar.

## Kullanım Alanları
- Dalgıç ve inline pompa kontrolü
- Su deposu seviye izleme
- Su şebekelerinde basınç ve debi izleme
- Rasat kuyularında seviye izleme
- Depo doldurma senaryoları
- Hidrofor modu ile basınçlı su temini

## Teknik Özellikler
- Dahili Wi-Fi haberleşme birimi (saha konfigürasyonu için)
- MODBUS TCP Master ve Slave haberleşme (aynı anda en fazla 5 bağlantı)
- 2 adet Analog Giriş (12-bit, 4-20 mA)
- 3 adet Dijital Giriş, 2 adet Dijital Çıkış (transistörlü)
- Dahili atanabilir I/O (giriş/çıkış) tablosu
- Çalışma sıcaklığı: -30°C ile +60°C arası
- 24 VDC giriş beslemesi
- 24 VDC 200 mA sensör besleme çıkışı
- Dahili regülatör ile 50W, 15V-24V çıkışlı güneş panelleriyle doğrudan çalışabilme
- Batarya Yönetim Birimi (DC UPS + Şarj)
- İnternet IP filtreleme ve APN desteği (güvenlik)
- IP65 koruma sınıfında ABS polimer dış muhafaza kutusu
- Wi-Fi üzerinden mobil uygulama ile konfigürasyon
- 5 adet durum LED'i
- Analog ve dijital girişlere alarm tanımlayabilme
- Depo doldurma ve hidrofor modu işletme senaryoları

## Opsiyonel Özellikler
- 868 MHz LoRa desteği: Pompa ile depo arası haberleşme, açık alanda 10 km menzil
- 11.2V 5.6A Lityum Pil (enerji kesintisi için yedek)
- Modüler haberleşme birimi seçenekleri: 2G, 4G veya Ethernet

## Uygulama Örnekleri / Hangi Senaryoda Kullanılır
- **Depo-pompa otomasyonu:** Uzak bir su deposunun seviyesine göre pompa istasyonundaki dalgıç pompanın LoRa üzerinden otomatik çalıştırılması. Kablo çekmenin maliyetli veya imkânsız olduğu kırsal uygulamalar için idealdir.
- **Hidrofor modu:** Basınç sensörü ile birlikte kullanılarak şebeke basıncını sabit tutacak şekilde pompa çalıştırma/durdurma kontrolü.
- **Saha konfigürasyonu:** Teknisyenin panele erişim gerektirmeden, dahili Wi-Fi üzerinden telefondaki mobil uygulama ile ayar yapması.
- **Şebekesiz noktalar:** 50W güneş paneli + Lityum pil ile elektrik şebekesi olmayan lokasyonlarda kesintisiz çalışma.
- **SCADA entegrasyonu:** MODBUS TCP Master olarak sahadaki sensörlerden veri toplama; aynı anda Slave olarak 5 farklı SCADA/ölçüm sistemine veri sunma.
- **Rasat kuyusu takibi:** 4-20 mA hidrostatik seviye sensörü bağlanarak yeraltı suyu seviyesinin uzaktan izlenmesi.

## Kullanıcı Sorularına Hızlı Yanıt İpuçları
- "Wi-Fi ile nasıl bağlanırım?" → Dahili Wi-Fi + mobil uygulama ile konfigürasyon
- "Kablo çekmeden pompa kontrol edebilir miyim?" → 868 MHz LoRa opsiyonu, 10 km açık alan
- "Kaç SCADA bağlanabilir?" → MODBUS TCP Slave olarak aynı anda 5 bağlantı
- "Güneş enerjisi ile çalışır mı?" → Dahili regülatör ile 50W panel doğrudan bağlanabilir
- "Güç kesilirse?" → 11.2V 5.6A Lityum pil opsiyonu + DC UPS
