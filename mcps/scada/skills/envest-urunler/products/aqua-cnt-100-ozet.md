---
name: aqua-cnt-100-ozet
description: |
  AQUA CNT 100 kompakt tip Pompa Kontrol ve Su İzleme cihazının katalog özeti. Derin kuyu dalgıç pompa, terfi istasyonu pompa kontrolü, dağıtım deposu izleme ve DMA (izole alt ölçüm bölgesi) basınç-debi izleme için kullanılır. 100F modelinde dahili ultrasonik debimetre bulunur, 100S harici debimetre bağlanabilen versiyondur. Detaylı referans için aqua-cnt-100.md dosyasına bakılır.
  Use when: kullanıcı AQUA CNT 100 hakkında genel/özet bilgi sorduğunda veya 100F ile 100S farkını merak ettiğinde. Derin teknik sorular için aqua-cnt-100.md skill dosyası kullanılmalıdır.
  Keywords: AQUA CNT 100, AQUA CNT 100F, AQUA CNT 100S, pompa kontrol, su izleme, derin kuyu, terfi istasyonu, DMA, izole alt ölçüm bölgesi, tarımsal sulama, clamp-on ultrasonik, özet
version: "1.0.0"
source_pdf: "AQUA Ürün Kataloğu 2026"
---

# AQUA CNT 100 Kompakt Tip Pompa Kontrol ve Su İzleme Cihazı (Katalog Özeti)

> Bu dosya kataloğdaki özet bölümüdür. Daha kapsamlı teknik bilgi, parametre tabloları ve SCADA entegrasyon detayları için `aqua-cnt-100.md` skill dosyasına bakın.

## Kullanım Alanları
- İçme suyu temin ve dağıtımı için derin kuyu dalgıç pompa kontrolü
- Terfi istasyonu pompa kontrolü
- Su dağıtım deposu izleme
- İzole alt ölçüm bölgesi (DMA) basınç ve debi izleme
- Tarımsal sulama uygulamaları

## Teknik Özellikler
- Düşük güç tüketimli mikrodenetleyici
- LCD ekran (64x128 grafik) ve membran tuş takımı
- GSM/GPRS modem + harici anten
- Batarya Yönetim Birimi (DC UPS + Şarj)
- 14.8V 11.2A Lityum pil
- 8 MB dahili kalıcı hafıza
- 3 Analog Giriş (16-bit), 1 Analog Çıkış (12-bit)
- 4 Dijital Giriş, 2 Dijital Çıkış (röleli)
- Dahili atanabilir I/O (giriş/çıkış) tablosu
- MODBUS TCP Master ve Slave haberleşme (aynı anda en fazla 5 bağlantı)
- İnternet IP filtreleme ve APN desteği
- 24 VDC giriş beslemesi
- Dahili regülatör ile 100W ve 15V-24V çıkışlı güneş panelleriyle çalışabilme
- Korozyona karşı ABS polimer dış koruma
- Çalışma sıcaklığı: -20°C ile +60°C arası
- Güvenlik: internet IP filtreleme ve APN desteği
- TS EN 61000-6-1 ve TS EN 61000-6-3 ile CE uygunluk sertifikası
- GSM üzerinden RTC (gerçek-zaman saat) güncelleme
- IP65 koruma sınıfı

## Opsiyonel Özellikler
- **AQUA CNT 100F modeli:** Dahili ultrasonik debimetre modülü ve clamp-on probları bulunur (harici debimetre gerektirmez).
- **AQUA CNT 100S modeli:** Harici debimetre bağlanabilen versiyondur (SMART PCS sisteminde de bu model kullanılır).

## Uygulama Örnekleri / Hangi Senaryoda Kullanılır
- **Derin kuyu pompası:** İçme suyu kuyusunda dalgıç pompanın kontrolü; seviye/basınç sensörlerine göre çalışma-durma mantığı.
- **DMA izleme:** İzole alt ölçüm bölgesine giriş/çıkışta basınç ve debi kaydı, gece minimum akışı analizi.
- **Depo takibi:** Dağıtım deposunda seviye, sıcaklık ve klor ölçümleri için analog girişlerin kullanımı.
- **Tarımsal sulama:** Pompa + vana kombinasyonu ile program destekli sulama; röleli dijital çıkışlarla vana kontrolü.
- **Clamp-on debi ölçümü:** 100F modelinde boruyu kesmeden ultrasonik clamp-on prob ile debi ölçümü — mevcut boruya hızlı montaj.
- **SCADA entegrasyonu:** MODBUS TCP Master ile saha sensörlerinden veri toplama; Slave olarak merkez SCADA'ya 5 eş zamanlı bağlantıya kadar servis.

## 100F vs 100S Farkı (Hızlı Özet)
| Özellik | 100F | 100S |
|---|---|---|
| Dahili ultrasonik debimetre | Var | Yok |
| Clamp-on probları | Var | - |
| Harici debimetre desteği | - | Var |
| Tipik kullanım | Standalone noktalar | SMART PCS ve DMA giriş panelleri |

## Kullanıcı Sorularına Hızlı Yanıt İpuçları
- "100F mi 100S mi alayım?" → Boruyu kesmeden debi ölçmek istiyorsan 100F, kendi debimetren varsa 100S
- "Kaç pompa kontrol eder?" → 2 röleli dijital çıkış (standart) ile 2 pompa / vana; atanabilir I/O ile özelleştirme
- "Hafıza?" → 8 MB dahili kalıcı + lityum pil destekli DC UPS
- "Sertifika?" → CE (TS EN 61000-6-1 ve 6-3)
- "Detay istiyorum" → aqua-cnt-100.md skill dosyasını yükle
