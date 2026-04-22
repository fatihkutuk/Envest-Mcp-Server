---
name: plc-katalogu
description: |
  Envest / Koru1000 PLC Ürün Kataloğu (2019) — CP serisi kuyu & terfi pompa kontrol cihazları,
  CS serisi depo kontrol ve gözlem cihazları, CC serisi atıksu terfi kontrol cihazları, M serisi
  güç panoları (kontaktör / yumuşak yolverici / frekans konvertörü) ve çevre birimleri.
  Her modelin: DI/DO/AI/AO sayıları, haberleşme (3G + Modbus TCP/RTU + Ethernet + WiFi), güç
  kaynağı, UPS, HMI, sıcaklık modülü, uygulama alanları ve tipik istasyon senaryoları.
  Use when: kullanıcı "CPxxx / CSxxx / CCxxx / Mxxx özellikleri", "giriş/çıkış sayısı",
  "hangi model hidrofor / klor dozajlama / güneş enerjisi / sıcaklık destekler", "karşılaştırma",
  "kuyu veya terfi için hangi pano seçilmeli", "pano ağırlığı/ebadı", "HMI var mı",
  "enerji analizörü var mı" gibi sorular sorduğunda.
  Keywords: PLC, RTU, CP100-GM, CP110-GM, CP120-GM, CP130-GM, CP140-GM, CS100-GM, CS101-GM,
  CS110-GM, CS111-GM, CS120-GM, CS121-GM, CS130-GM, CS140-GM, CS141-GM, CS150-GM, CC100-GM,
  CC110-GM, CC120-GM, M100, M200, M300-DF, Koru1000, dijital giriş, analog çıkış, röle,
  modbus, 3G, HMI, sürücü, frekans konvertörü, UPS, güneş paneli, klor dozajlama, hidrofor,
  debimetre, basınç sensörü, hidrostatik seviye, ultrasonik debimetre, elektromanyetik
  debimetre, PT-100, termokupl.
version: "1.0.0"
source_pdf: "Koru1000 / Envest PLC Ürün Kataloğu 2019"
---

# Envest / Koru1000 PLC & RTU Ürün Kataloğu (2019)

Bu belge, sahada çalışan Envest / Koru1000 su yönetim donanımlarının özet spesifikasyonlarını
içerir. Tüm cihazlar endüstriyel PLC tabanlıdır, Modbus TCP/RTU destekler ve Koru1000 bulut
SCADA sistemine 3G üzerinden entegre olur.

## Ürün Aileleri

| Seri | Amaç | Model Sayısı |
|------|------|--------------|
| **CP** | Kuyu ve terfi pompa kontrol cihazları | CP100-GM ... CP140-GM (5 model) |
| **CS** | Depo kontrol ve gözlem cihazları | CS100-GM ... CS150-GM (10 model) |
| **CC** | Atıksu terfi kontrol cihazları | CC100-GM, CC110-GM, CC120-GM |
| **M** | Güç panoları (motor sürüş) | M100 (kontaktör), M200 (soft starter), M300-DF (sürücü) |
| **Çevre** | Sensörler | TR-11 sıcaklık, BT-214-G1 basınç, PTL-110 seviye, ultrasonik & elektromanyetik debimetre |

---

## Tüm CP/CS/CC Cihazlarında Ortak Ana PLC Kontrolör Özellikleri

Aşağıdaki özellikler CP100-GM, CP110-GM, CP120-GM, CP130-GM, CP140-GM, CS100-GM, CS101-GM,
CS110-GM, CS111-GM, CS120-GM, CS121-GM, CS130-GM, CS140-GM, CS141-GM, CS150-GM, CC100-GM,
CC110-GM ve CC120-GM'in **ana PLC modülünde** aynıdır:

- **9 kanal 24VDC PNP/NPN dijital giriş**
- **6 kanal 230VAC 5A röle çıkışı**
- **1 kanal 0-10VDC / 0-20mADC seçilebilir analog giriş** (12 bit)
- **1 kanal 0-20mADC analog çıkış** (14 bit)
- Modüler yapı — maksimum **16 genişleme modülü**
- 100 Mbit Ethernet, **MODBUS TCP**
- RS232 + RS485, **MODBUS RTU**
- 12 ns komut işleme hızı, RTC, ondalıklı işlem
- 24 VDC besleme, güç tüketimi < 3 W
- 0°C … +50°C çalışma sıcaklığı
- Grafiksel Ladder editörü ile programlanabilme

Toplam DI/DO/AI/AO sayıları, eklenen **dijital/analog/sıcaklık genişleme modülleri** ile artar
(aşağıdaki karşılaştırma tablolarına bakınız).

### Ortak GSM Haberleşme (Teltonika tipi 3G Router)

- 3G 14.4 Mbps / 2G 236.8 Kbps
- IEEE 802.11b/g/n WiFi AP / istasyon
- 2 × Ethernet portu
- VPN, APN, DHCP, QoS, güvenlik duvarı, DDOS/port tarama önleme, WPA-2Ent
- RutOS (Linux), 1 DI / 1 DO, 9-30 VDC besleme, < 5 W
- -40°C … +75°C çalışma sıcaklığı

### Ortak Güç Kaynağı Tipleri

| Tip | Cihazlarda | Özellik |
|-----|-----------|---------|
| **60 W SMPS** (2.5 A) | CP100, CP110, CS100, CS110, CS120, CS130, CC100, CC110 | 24 VDC çıkış, 100-240 VAC / 90-350 VDC giriş, %88 verim, -25…+60°C |
| **120 W SMPS** (5 A) | CP120, CP130, CP140, CS140, CS150, CC120 | Aynı özellikler, daha yüksek akım |
| **Güneş Enerji Regülatörü** | CS101, CS111, CS121, CS141 | 20 A yük akımı, LCD ekran, ters akü / yüksek akım koruma, -20…+55°C (akü & panel **sisteme dahil değildir**) |

### Ortak Kesintisiz Güç Kaynakları

- **600 VA AC UPS** — CP100, CS100, CC100 (Line-interactive, 162-290 VAC giriş, 1×12V 7Ah akü)
- **DC UPS** — CP110, CP120, CP130, CP140, CS110, CS120, CS130, CS140, CS150, CC110, CC120 (22.5-28 V giriş → 24 V çıkış, 30 A, ≥7 Ah 12V kuru akü, -40…+70°C)

---

# CP SERİSİ — Kuyu ve Terfi Pompa Kontrol Cihazları

## CP100-GM — Temel Kuyu Pompa Kontrol Cihazı

**Hedef:** İçmesuyu, tarımsal sulama, proses sularının yönetimi — **sadece kuyu pompası**.

| Özellik | Değer |
|---------|-------|
| Toplam Analog G/Ç | 1 / 1 |
| Toplam Dijital G/Ç | 9 / 6 |
| Sıcaklık Girişi | Yok |
| Güç Kaynağı | 24 VDC 60 W SMPS |
| UPS | **AC UPS** (600 VA) |
| HMI Ekran | Yok |
| Enerji Analizörü | Yok |
| Sürücü / Hidrofor | Yok |
| Sensör Kapasitesi | **1 adet analog** (debimetre / basınç / yeraltı su seviyesi / depo seviyesi) |
| Pano | PVC 40×60×22 cm, 11.85 kg |

**Çalışma senaryoları:** Bağlanan depoya göre otomatik (Koru1000 Link), zamana göre programlı çalışma.

---

## CP110-GM — Kuyu + Terfi Pompa, Sürücü Desteği

**Farklar (CP100'e göre):** Sürücü desteği, 4 analog sensör, DC UPS, oransal aktuatörlü vana kontrolü, enerji analizörü.

| Özellik | Değer |
|---------|-------|
| Toplam Analog G/Ç | 5 / 3 (PLC + 4AI/2AO genişleme modülü) |
| Toplam Dijital G/Ç | 9 / 6 |
| Güç Kaynağı | 24 VDC 60 W SMPS |
| UPS | **DC UPS** |
| Enerji Analizörü | **Var** (3V, 3I, frekans, W, Var, VA, kWh, kVarh, Cos φ, RS485 Modbus RTU, %0.5) |
| HMI | Yok |
| Sürücü (frekans konvertörü) | **Destekli** — basınç / debi / seviye / güce göre adaptif sabitleme |
| Oransal aktuatörlü vana | 1 adet |
| Sensör Kapasitesi | **4 analog** (debimetre, giriş/çıkış/hat basıncı, yeraltı/depo seviyesi, bakiye klor, bulanıklık) |
| Pano | PVC 40×60×22 cm, 10.25 kg |

**Uygulama:** Kuyu + terfi pompa kontrolü, hidrofor modu (basınca göre), enerji verimliliği.

---

## CP120-GM — HMI'lı, Sıcaklık Modüllü Gelişmiş Kontrol

**Farklar (CP110'a göre):** 7" dokunmatik HMI, 4 kanal sıcaklık modülü, 120 W SMPS, aktuatörlü vana (1 adet, 3 fazlı), pompa verimi hesaplama.

| Özellik | Değer |
|---------|-------|
| Toplam Analog G/Ç | 5 / 3 |
| Toplam Dijital G/Ç | 9 / 6 |
| Sıcaklık Girişi | **4 kanal** (PT-100/1000, termokupl B/C/E/J/K/N/R/S/T, NTC, mVDC) |
| Güç Kaynağı | 24 VDC **120 W** SMPS |
| UPS | DC UPS |
| Enerji Analizörü | Var |
| HMI | **7" TFT 800×480 dokunmatik**, 32-bit 800 MHz, 128 MB Flash, VNC, Modbus TCP |
| Sürücü | Var (adaptif sabitleme) |
| Aktuatörlü vana | 1 adet, 3 fazlı |
| Oransal vana | 1 adet |
| Sensör Kapasitesi | **4 analog** + 4 sıcaklık (pano, motor, ortam, su) |
| Pano | PVC 50×70×25 cm, 15.60 kg |

**Kullanım:** İçmesuyu, tarımsal sulama, proses. Pompa verimi hesaplama yapar.

---

## CP130-GM — Klor Dozajlama + Genişletilmiş DI/DO

**Farklar (CP120'ye göre):** **8 DI + 8 röle çıkışlı dijital genişleme modülü**, klor dozaj pompası kontrolü (3 adet), fonksiyonel G/Ç'lar. Bakiye Klor sensörü desteği eklendi.

| Özellik | Değer |
|---------|-------|
| Toplam Analog G/Ç | 5 / 3 |
| Toplam Dijital G/Ç | **17 / 14** (9/6 + 8/8 genişleme) |
| Sıcaklık Girişi | 4 kanal |
| HMI | 7" TFT dokunmatik |
| Sürücü | Var |
| Klor dozaj pompası | **3 adet** |
| Aktuatörlü vana | 1 adet, 3 fazlı |
| Sensör Kapasitesi | 4 analog (debimetre, basınçlar, seviyeler, bakiye klor, bulanıklık) |
| Pano | PVC 50×70×25 cm, 15.90 kg |

---

## CP140-GM — Maksimum Sensör Kapasiteli Kuyu/Terfi

**Farklar (CP130'a göre):** Analog genişleme modülü **8AI / 4AO**'ya yükseltildi, 8 adet analog sensör bağlanabilir (Klor Seviyesi de eklendi).

| Özellik | Değer |
|---------|-------|
| Toplam Analog G/Ç | **9 / 5** (1/1 PLC + 8/4 genişleme) |
| Toplam Dijital G/Ç | 17 / 14 |
| Sıcaklık Girişi | 4 kanal |
| HMI | 7" TFT dokunmatik |
| Sensör Kapasitesi | **8 adet analog** |
| Pano | PVC 50×70×25 cm, 16.20 kg |

---

# CS SERİSİ — Depo Kontrol ve Gözlem Cihazları

**Ortak uygulama alanları:** İçmesuyu, proses suları, gözlem istasyonları, su depoları, rasat kuyuları,
kayıp-kaçak yönetimi (basınç & debi gözlem odaları).

CS serisinde **"-0" sonlu** modeller şebeke elektriği ile, **"-1" sonlu** modeller güneş enerjisi
regülatörü ile çalışır (CS101, CS111, CS121, CS141).

## CS100-GM vs CS101-GM — Temel Depo Gözlem

| Özellik | CS100-GM | CS101-GM |
|---------|----------|----------|
| Analog G/Ç | 1/1 | 1/1 |
| Dijital G/Ç | 9/6 | 9/6 |
| Sıcaklık | Yok | Yok |
| Güç | 60 W SMPS | **Güneş enerji regülatörü (20 A)** |
| UPS | AC UPS | Yok (panel + akü sisteme dahil değil) |
| Sensör | 1 analog (debimetre / basınç / seviye) | Aynı |
| Pano | PVC 40×60×22, 11.00 kg | PVC 40×60×22, 7.10 kg |

---

## CS110-GM vs CS111-GM — Klor Dozajlama + Oransal Vana

| Özellik | Değer |
|---------|-------|
| Analog G/Ç | **5 / 3** (1/1 PLC + 4/2 genişleme) |
| Dijital G/Ç | 9 / 6 |
| Sıcaklık | Yok |
| Klor dozaj pompası | **2 adet** |
| Oransal vana | Var (oransal/sabit) |
| Sensör Kapasitesi | 4 analog |
| CS110 Güç | 60 W SMPS + DC UPS |
| CS111 Güç | Güneş enerji regülatörü |
| Pano | 40×60×22 — CS110: 8.00 kg / CS111: 7.20 kg |

**Ek uygulama:** Klorlama, sıvı klor dozajlama.

---

## CS120-GM vs CS121-GM — Sıcaklık Ölçümlü

**CS110/111'in üzerine 2 kanallı sıcaklık modülü eklenir.** (pano, ortam, su sıcaklığı).

| Özellik | CS120-GM | CS121-GM |
|---------|----------|----------|
| Analog G/Ç | 5/3 | 5/3 |
| Dijital G/Ç | 9/6 | 9/6 |
| **Sıcaklık** | **2 kanal** | **2 kanal** |
| Güç | 60 W SMPS + DC UPS | Güneş regülatörü |
| Pano | 40×60×22, 8.60 kg | 40×60×22, 8.20 kg |

---

## CS130-GM — 17/14 DI/DO ile Depo Kontrol

PLC + Dijital genişleme (8DI/8RO) içerir.

| Özellik | Değer |
|---------|-------|
| Analog G/Ç | 5 / 3 |
| Dijital G/Ç | **17 / 14** |
| Sıcaklık | Yok |
| Güç | 60 W SMPS + DC UPS |
| Klor/Oransal vana | Var |

---

## CS140-GM vs CS141-GM — Yüksek Analog Kapasiteli

**Analog modülü 8AI/4AO'ya yükseltilmiş**, 8 analog sensör desteği, 120 W SMPS.

| Özellik | Değer |
|---------|-------|
| Analog G/Ç | **9 / 5** |
| Dijital G/Ç | 9 / 6 |
| Sıcaklık | Yok |
| Klor dozaj | 4 adet |
| CS140 güç | 120 W SMPS + DC UPS |
| CS141 güç | Güneş enerji regülatörü |
| Pano | 40×60×22, 8.30 kg |

---

## CS150-GM — **Basınç Kontrol Vana Odası Amiral Modeli**

Depo + basınç kontrol odası için en yüksek donanımlı model. Dijital + analog + sıcaklık
genişleme modüllerinin hepsine sahiptir.

| Özellik | Değer |
|---------|-------|
| Analog G/Ç | **9 / 5** (1/1 + 8/4) |
| Dijital G/Ç | **17 / 14** (9/6 + 8/8) |
| Sıcaklık | **2 kanal** |
| Güç | 120 W SMPS + DC UPS |
| Klor dozaj pompası | 4 adet |
| Aktuatörlü vana | 2 adet, 3 fazlı |
| Oransal vana | Oransal/Sabit |
| Sensör Kapasitesi | 8 analog |
| Uygulama | **Şebekelerde basınç kontrolü**, sıvı klor dozajlama, depo, rasat, kayıp-kaçak |
| Pano | PVC 50×70×25 cm, 15.35 kg |

---

# CC SERİSİ — Atıksu Terfi Kontrol Cihazları

**Ortak uygulama:** Kanal atıksu pompalarının kontrolü (seviyeye göre kaskad çalışma).

## CC100-GM — Temel Atıksu Terfi

| Özellik | Değer |
|---------|-------|
| Analog G/Ç | 1 / 1 |
| Dijital G/Ç | 9 / 6 |
| Sıcaklık | Yok |
| Güç | 60 W SMPS + **AC UPS** |
| HMI | Yok |
| Enerji Analizörü | Yok |
| Pompa Sayısı | 1 veya 2 pompalı |
| Sensör | 1 analog (rezervuar seviyesi) |
| Pano | PVC 40×60×22, 11.85 kg |

---

## CC110-GM — HMI'lı, Sıcaklık Modüllü Atıksu

| Özellik | Değer |
|---------|-------|
| Analog G/Ç | 1 / 1 |
| Dijital G/Ç | **17 / 14** (8DI/8RO genişleme ile) |
| Sıcaklık | **4 kanal** |
| Güç | 60 W SMPS + DC UPS |
| Enerji Analizörü | **Var** |
| HMI | **7" TFT dokunmatik** |
| Pompa Sayısı | 1, 2 veya 3 |
| Sensör | 1 analog + 4 sıcaklık |
| Pano | PVC 50×70×25, 16.8 kg |

---

## CC120-GM — **Amiral Atıksu Modeli** — Sürücü + On/Off Aktuatör

| Özellik | Değer |
|---------|-------|
| Analog G/Ç | **5 / 3** |
| Dijital G/Ç | **25 / 22** (9/6 PLC + 16DI/16RO genişleme) |
| Sıcaklık | 4 kanal |
| Güç | **120 W SMPS** + DC UPS |
| Enerji Analizörü | Var |
| HMI | 7" TFT dokunmatik |
| Sürücü (frekans konvertörü) | **Destekli** (3 adet, 3 fazlı) |
| On/Off Aktuatörlü vana | 3 adet |
| Sensör | 2 analog (debimetre + basınç + rezervuar seviyesi) + 4 sıcaklık |
| Pompa Sayısı | 1, 2 veya 3 |
| Pano | **Sac 220×120×60 cm** (büyük endüstriyel) |

---

# M SERİSİ — Güç Panoları (Motor Sürüş)

## M100 — Kontaktörlü Güç Panosu

- **Güç aralığı:** 4 – 300 kW
- 380-400 V 3 faz motor kontaktörü, dahili voltaj bastırıcı
- Direkt yol verme — en basit ve ekonomik başlangıç
- Pano: Fırınlanmış Sac 40×60×20 cm (45 kW ve üzeri için bilgi alınız)
- **Avantaj:** Sabit şebekelerde, mekanik olarak sağlam sistemler için.
- Parafudr / kompanzasyon: opsiyonel

## M200 — Yumuşak Yol Vericili (Soft Starter) Güç Panosu

- **Güç seçenekleri:** 4, 5.5, 7.5, 11, 15, 18.5, 22, 30, 37 kW (45+ için bilgi alınız)
- 2 faz kontrollü, ana gerilim 208-600 V, kontrol 100-240 VAC veya 24 VAC/DC
- Dahili bypass, gerilim rampası, 3 potansiyometre ile ayar
- **Avantaj:** Motor başlangıç/duruş elektriksel darbelerini ve yüksek akımları ortadan kaldırır.
- Pano: Fırınlanmış sac 60×80×35 cm

## M300-DF — Frekans Konvertörlü (Sürücü) Güç Panosu

En gelişmiş M serisi modeli — **enerji verimliliği** (basınç / debi / yeraltı su seviyesi sabitleme).

| Tip | Güç Aralığı | Pano Boyutu |
|-----|-------------|-------------|
| Tip 1 | 4, 5.5, 7.5, 11, 15, 18.5, 22 kW | 60×140×50 cm |
| Tip 2 | 30, 37, 45, 55, 75 kW | 60×190×50 cm |
| Tip 3 | 90, 110, 132, 160, 200, 250, 285 kW | 60×220×60 cm |

**Teknik:**
- Nominal giriş: 380-480 V ±10%, güç faktörü 0.98, verim %98
- THD <%48 (%80-100 yükte)
- Aşırı yük: %110 (1 dk/10 dk), ağır şartlarda %150
- 0-45°C kayıpsız çalışma, yoğuşmasız %95 nem
- IEC 61000-4-2/3/4/5 ve IEC 61800-3 uyumlu
- RFI/EMC filtre (150 m motor kablosu)
- **Dahili Modbus RTU**, Profibus / Ethernet / Profinet / Devicenet ek kart desteği
- PID otomatik ayar (autotuning), Türkçe kontrol paneli
- Vektör + skaler kontrol, sabit mıknatıslı motor sürüş
- Akım trafosu + fan güce göre seçilir; parafudr opsiyonel

---

# Çevre Birimleri (Sensörler)

## TR-11 — Sıcaklık Sensörü
- Aralık: -40 … +350°C, hassasiyet <0.5°C
- 30×6 mm, 1.4301 DIN paslanmaz, 3 telli 1 m kablo
- Kullanım: pano, ortam, motor, su sıcaklığı; pompa verim hesabı; rasat yeraltı su sıcaklığı

## BT-214-G1 — Basınç Sensörü
- 4-20 mA (2 kablo), 12-30 VDC, %0.3 hassasiyet @ +25°C
- Silikon/çelik/seramik membran, 304L paslanmaz, IP65/IP67
- Çalışma: -20 … +85°C
- Aralıklar: **0-1 / 0-6 / 0-10 / 0-16 / 0-25 / 0-40 / 0-60 bar**
- Kullanım: kuyu çıkış/hat basıncı, terfi giriş/çıkış/hat, kayıp-kaçak takibi

## PTL-110 — Hidrostatik Seviye Sensörü
- Piezorezistif, 4-20 mA, 12-30 VDC, IP68, %0.3 hassasiyet, 316L paslanmaz
- Aralıklar: **0-6 / 10 / 20 / 30 / 40 / 50 / 60 / 70 / 80 / 100 / 150 mss**
- Kullanım: kuyu yeraltı su seviyesi, depo seviyesi, atıksu rezervuar, rasat kuyusu

## Ultrasonik Debimetre
- İçmesuyu, DN32...6000, DC 8-36 V veya AC 85-264 V
- Arka aydınlatmalı 2 satır LCD, membran tuş
- **1 × 4-20 mA analog çıkış**, 1 × 4-20 mA analog giriş
- 1 × OCT pals çıkışı, 1 × röle çıkışı, **RS485**
- Mıknatıslı problar, ölçüm 0 … ±12 m/s, hassasiyet ±%1
- -20 … +60°C, IP67
- Kullanım: kuyu/terfi/depo/şebeke debisi, **DMA uygulamaları**, kayıp-kaçak, oransal klorlama

## Elektromanyetik Debimetre
- İçmesuyu **ve atıksu**, DN25...3000, iki yönlü akış
- 2 noktalı kalibrasyon, -20 … +65°C, -12 … +12 m/s
- DN50-150 PN16 / DN200-300 PN10
- **Muhafaza:** Alüminyum (standart) / paslanmaz çelik (opsiyonel), IP67 / IP68
- İç kaplama: polipropilen veya sert kauçuk / opsiyonel PTFE, poliolefin
- Elektrotlar: Hastelloy C (standart) / paslanmaz çelik, titanyum (opsiyonel)
- **Tipler:** Bütünleşik (dönüştürücü sensör üzerinde) / Ayrık tip

---

# Model Karşılaştırma Tabloları

## CP Serisi (Kuyu & Terfi Pompa)

| Özellik | CP100-GM | CP110-GM | CP120-GM | CP130-GM | CP140-GM |
|---------|----------|----------|----------|----------|----------|
| Analog G/Ç | 1/1 | 5/3 | 5/3 | 5/3 | **9/5** |
| Dijital G/Ç | 9/6 | 9/6 | 9/6 | **17/14** | 17/14 |
| Sıcaklık Giriş | — | — | 4 | 4 | 4 |
| Güç Kaynağı | 60 W SMPS | 60 W SMPS | **120 W SMPS** | 120 W SMPS | 120 W SMPS |
| UPS | AC UPS | DC UPS | DC UPS | DC UPS | DC UPS |
| Enerji Analizörü | — | Var | Var | Var | Var |
| HMI (7" TFT) | — | — | Var | Var | Var |
| Sürücü Desteği | — | Var | Var | Var | Var |
| Aktuatörlü vana | — | — | 1 (3f) | 1 (3f) | 1 (3f) |
| Klor dozajlama | — | — | — | 3 adet | 3 adet |
| Sensör (analog) | 1 | 4 | 4 | 4 | **8** |
| Pano Ağırlık | 11.85 kg | 10.25 kg | 15.60 kg | 15.90 kg | 16.20 kg |

## CS Serisi (Depo & Gözlem)

| Özellik | CS100 | CS101 | CS110 | CS111 | CS120 | CS121 | CS130 | CS140 | CS141 | CS150 |
|---------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|
| Analog G/Ç | 1/1 | 1/1 | 5/3 | 5/3 | 5/3 | 5/3 | 5/3 | **9/5** | 9/5 | 9/5 |
| Dijital G/Ç | 9/6 | 9/6 | 9/6 | 9/6 | 9/6 | 9/6 | **17/14** | 9/6 | 9/6 | **17/14** |
| Sıcaklık | — | — | — | — | **2** | **2** | — | — | — | **2** |
| Güç (SMPS) | 60W | — | 60W | — | 60W | — | 60W | **120W** | — | **120W** |
| Güneş Regülatörü | — | **20A** | — | **20A** | — | **20A** | — | — | **20A** | — |
| UPS | AC | — | DC | — | DC | — | DC | DC | — | DC |
| Klor | — | — | 2 | 2 | 2 | 2 | — | 4 | 4 | 4 |
| Bar (basınç kontrol) | — | — | — | — | — | — | — | — | — | **Var** |

> **"-1" sonlu CS modelleri güneş panelli**, akü ve panel **sisteme dahil değildir**.

## CC Serisi (Atıksu Terfi)

| Özellik | CC100-GM | CC110-GM | CC120-GM |
|---------|----------|----------|----------|
| Analog G/Ç | 1/1 | 1/1 | **5/3** |
| Dijital G/Ç | 9/6 | **17/14** | **25/22** |
| Sıcaklık | — | 4 | 4 |
| Güç Kaynağı | 60 W SMPS | 60 W SMPS | **120 W SMPS** |
| UPS | AC UPS | DC UPS | DC UPS |
| Enerji Analizörü | — | Var | Var |
| HMI (7" TFT) | — | Var | Var |
| Sürücü | — | — | **Var** |
| Maks. Pompa | 2 | 3 | 3 |

## M Serisi (Güç Panoları)

| Özellik | M100 | M200 | M300-DF |
|---------|------|------|---------|
| Kontaktör | Var | — | — |
| Yumuşak Yol Verici | — | Var | — |
| Frekans Konvertörü | — | — | **Var** |
| Güç Aralığı | 4-300 kW | 4-37 kW (45+ bilgi) | Tip 1/2/3: 4-285 kW |
| Enerji Verimliliği | — | — | Var (PID, autotuning) |

---

# Tipik İstasyon Senaryoları (Örnek Uygulamalardan)

Bu bölüm "hangi modelleri bir araya getirmeli?" sorularına yanıt için:

## İçme Suyu — 1 Kuyu + 1 Depo

| Seviye | Kuyu Pano | Depo Pano |
|--------|-----------|-----------|
| **Başlangıç** | CP100-GM + M100 / M200 | CS100-GM veya CS101-GM |
| **Standart** | CP110-GM + M300-DF | CS110-GM veya CS111-GM |
| **Profesyonel** | CP130-GM + M300-DF | CS120-GM veya CS121-GM |

## Çoklu İstasyon (Kuyular + Terfi + Depo + Basınç Kontrol)

| Başlangıç | Standart | Profesyonel |
|-----------|----------|-------------|
| 2× CP100 + 2× M100/200 (kuyu) | 2× CP120 + 2× M300-DF (kuyu) | 2× CP130 + 2× M300-DF (kuyu) |
| 2× CP110 + 3× M100/200 (terfi) | 3× CP120 + 3× M300-DF (terfi) | 1× CP130 + 2× CP120 + 3× M300-DF (terfi) |
| 1× CS100/101 (depo) | 1× CS120/121 (depo) | 1× CS140/141 (depo) |
| 1× CS130 (basınç kontrol) | 1× CS130 (basınç kontrol) | **1× CS150** (basınç kontrol) |

---

# Hızlı Seçim Rehberi (LLM için)

- **Sadece kuyu kontrolü, bütçe odaklı** → CP100-GM
- **Kuyu + terfi + sürücü + enerji analizörü** → CP110-GM
- **+ HMI ekran ve sıcaklık ölçümü istiyorsan** → CP120-GM
- **+ Klor dozajlama (3 adet) istiyorsan** → CP130-GM
- **Maksimum 8 analog sensör (bulanıklık dahil)** → CP140-GM
- **Depo gözlem, şebeke elektriği, tek sensör** → CS100-GM
- **Depo + güneş paneli (off-grid)** → CS101 / CS111 / CS121 / CS141
- **Depo + klor dozajlama + oransal vana** → CS110 (şebeke) / CS111 (güneş)
- **Depo + sıcaklık ölçümü** → CS120 / CS121
- **Büyük depo, çok DI/DO** → CS130 veya CS140
- **Basınç kontrol vana odası (şebeke hat basıncı)** → **CS150-GM**
- **Atıksu, 1-2 pompa, bütçe** → CC100-GM
- **Atıksu + HMI + 3 pompa** → CC110-GM
- **Atıksu + sürücü + çok G/Ç (25/22 DI/DO)** → **CC120-GM**
- **Basit motor yol verme** → M100
- **Yumuşak kalkış** → M200
- **Enerji verimliliği + değişken hız** → **M300-DF**

## Ultrasonik vs Elektromanyetik Debimetre

- **Ultrasonik:** sadece içmesuyu, DN32-6000, mıknatıslı probla dışarıdan ölçüm
- **Elektromanyetik:** içmesuyu **+ atıksu**, DN25-3000, hatta bağlanır, iki yönlü akış
- Atıksu için → Elektromanyetik
- Temiz su hattına girmeden ölçüm → Ultrasonik

---

# Notlar (LLM İçin İpuçları)

1. Tüm CP/CS/CC modelleri **temel PLC'de 9 DI / 6 RO / 1 AI / 1 AO**'ya sahiptir. Toplam sayılar
   eklenen **dijital genişleme (8DI/8RO veya 16DI/16RO)** ve **analog genişleme
   (4AI/2AO veya 8AI/4AO)** modüllerine göre büyür.
2. Modbus TCP + Modbus RTU **her modelde standart**.
3. 3G endüstriyel router + WiFi + VPN **her modelde standart**.
4. "-1" ile biten CS modelleri güneş enerjisi ile çalışır, akü ve panel **sistem paketine dahil değildir**.
5. HMI ekran sadece **CP120, CP130, CP140, CC110, CC120** modellerinde mevcuttur.
6. Enerji analizörü **CP110 ve üzeri**, **CC110 ve CC120**'de mevcuttur.
7. CC120-GM, tüm katalogdaki **en yüksek DI/DO sayısına (25/22)** sahip modeldir.
8. Sürücü (frekans konvertörü) desteği **CP110, CP120, CP130, CP140, CC120** modellerinde vardır
   ve bunlar M300-DF ile birlikte kullanılır.
