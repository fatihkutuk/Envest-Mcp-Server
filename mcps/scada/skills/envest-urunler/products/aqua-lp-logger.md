---
name: aqua-lp-logger
description: |
  AQUA LP Logger, ekstra düşük güç tüketimli pilli veri toplama ve kaydetme cihazıdır. Su şebekelerinde basınç/debi/katodik koruma izleme, rasat kuyularında seviye izleme ve ortam sıcaklık/nem takibi için kullanılır. Dahili lityum pil ile 5 yıla kadar enerjisiz çalışabilir.
  Use when: kullanıcı AQUA LP Logger, pilli data logger, uzun ömürlü batarya ile saha ölçümü, katodik koruma izleme, LoRa/2G/4G modüler haberleşmeli veri kaydedici konularında soru sorduğunda.
  Keywords: AQUA LP Logger, data logger, pilli logger, extreme low power, lityum pil 5 yıl, katodik koruma, rasat kuyu, LoRa, 2G, 4G, HTTPS REST API, JSON, I2C, one-wire, IP65
version: "1.0.0"
source_pdf: "AQUA Ürün Kataloğu 2026"
---

# AQUA LP Logger Pilli Veri Toplama ve Kaydetme Cihazı

AQUA LP Logger, elektrik şebekesinin bulunmadığı veya güç tüketiminin kritik olduğu sahalarda uzun süreli veri toplamak amacıyla tasarlanmış, çok düşük güç tüketimli (Extreme Low Power) bir data logger'dır. Modüler haberleşme birimi sayesinde uygulamaya göre 2G, 4G veya LoRa yapı taşı seçilebilir.

## Kullanım Alanları
- Su şebekelerinde basınç, debi ve katodik koruma izleme
- Rasat kuyularında seviye izleme
- Ortam sıcaklığı ve nem izleme
- Uzak sahalarda uzun süreli (yıllık) veri toplama noktaları
- Elektrik olmayan noktalarda modemsiz USB ile offline veri toplama

## Teknik Özellikler
- Düşük güç tüketimi (Extreme Low Power mimarisi)
- Dahili lityum pil ile 5 yıl enerjisiz kullanım* (*Günde bir kez veri alma ve haftada bir veri gönderimi halinde)
- Saatlik ve haftalık veri toplama/gönderme
- 1 dakika, 10 dakika, 1 saatlik uyanma periyotları ayarlanabilir
- Modüler haberleşme birimi: 2G, 4G veya LoRa
- 3 adet analog giriş (2 adet 4-20 mA + 1 adet 0-2V)
- One-wire sıcaklık ve nem sensörü bağlanabilme
- I2C sensör girişi
- 2 adet dijital giriş (sensör ve switch'lerden veri alma, alarm oluşturma)
- Analog ve dijital girişlere alarm tanımlayabilme
- HTTPS REST API ile JSON formatında haberleşme (web tabanlı konfigürasyon)
- IP65 koruma sınıfında ABS polimer dış muhafaza kutusu
- Çalışma sıcaklığı: -30°C ile +60°C arası
- Uyandırma ve veri gönderme butonu
- 2 adet durum LED'i (GSM ve işlemci)
- 8 MB kalıcı LOG hafıza
- 3.6V ve 24V sensör besleme çıkışı
- 3.6V pil veya USB güç beslemesi ile çalışabilme
- USB üzerinden konfigürasyon ayarları yapabilme
- USB haberleşme portu üzerinden offline / modemsiz veri aktarımı

## Opsiyonel Özellikler
- Haberleşme modülü seçimi: 2G / 4G / LoRa (proje ihtiyaçlarına göre)
- One-wire sıcaklık-nem sensörü entegrasyonu
- I2C tabanlı sensör eklentileri
- 3.6V uzun ömürlü Lityum pil paketi (tek pil ile 5 yıl çalışma)

## Uygulama Örnekleri / Hangi Senaryoda Kullanılır
- **Katodik koruma izleme:** Boru hattı boyunca onlarca kilometre uzanan katodik koruma istasyonlarında, elektrik olmadan yıllarca veri toplama. LoRa veya 4G ile merkeze iletim.
- **Şehir içi basınç loglama:** Su dağıtım şebekesinde farklı noktalara konularak gün/saat bazlı basınç profili çıkarma. DMA analizleri için temel veri kaynağıdır.
- **Rasat kuyusu seviyesi:** Yeraltı suyu gözlem kuyularında hidrostatik seviye sensörü ile çok yıllık seviye trendi kaydı.
- **Şantiye ortam takibi:** Bir araç/kabinet içinde sıcaklık-nem izleme; eşik aşılırsa alarm üretimi.
- **Modemsiz saha:** Kapsamanın olmadığı sahalarda cihaz, 8 MB hafızasında veri biriktirir; teknisyen USB ile yerinde veri indirir.
- **Bulut entegrasyonu:** HTTPS REST API + JSON formatıyla mevcut web sistemine doğrudan entegre edilir, aracı sunucu gerekmez.

## Kullanıcı Sorularına Hızlı Yanıt İpuçları
- "Pil ne kadar dayanır?" → Dahili lityum pil ile günde 1 okuma + haftalık gönderim senaryosunda 5 yıl
- "Hangi sensörler bağlanır?" → 4-20 mA, 0-2V analog, one-wire sıcaklık/nem, I2C sensörler, dijital switch'ler
- "Nasıl haberleşir?" → Modüler: 2G / 4G / LoRa seçilebilir; HTTPS REST API JSON
- "İnternet yoksa?" → 8 MB kalıcı hafıza + USB ile offline veri aktarımı
- "Dışarıda duracak, sorun olur mu?" → IP65 ABS kutu, -30°C ile +60°C çalışma aralığı
