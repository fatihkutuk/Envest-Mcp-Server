---
name: aqua-devices
description: |
  AQUA CNT 100S / 100F / 100FP / 100SL kompakt pompa kontrol ve su izleme
  cihazının TAM donanım ve yazılım referansı. Modem/GSM/LED durumu
  (Tablo 1.1), hedef çalışma durumu kodları (Tablo 1.2: 10/11/100/101/
  120/121/200/201/30/31), alarm ve uyarı listesi (Tablo 4.1), Modbus TCP
  register haritası (0-94), Uyarı/Alarm/Status/Control Word bit tanımları,
  motor koruma eşikleri, çalışma modları (Serbest/Depo Doldurma/Hidrofor/
  Basınç PI), SCADA linkleme, antiblokaj, acil senaryo, APN/IP ayarları,
  dahili basınç (100FP) / seviye (100SL) sensörleri, dahili ultrasonik
  debimetre (100F/100FP) menüleri M00-M92 ve R/I/J/H/F/G/K hata kodları.
  Use when: kullanıcı "modem status X", "LED yanıp sönüyor", "hedef X koduna
  düştü motor çalışmıyor/çalışıyor", "alarm kodu", "modbus register X ne",
  "debimetre hata I/J/H/F/G/K", "APN Turkcell/Vodafone", "kontrol/status
  word bit X", "çekim gücü", "SSR hata", "pil kapalı", "antiblokaj",
  "SCADA linkleme", "düşük güç modu", "AQUA CNT kurulumu", "hedef IP
  tanımlama", "basınç PI set", "min/max akım koruma", "Statik/Dinamik
  seviye", "analizör Klemsan/Entes/Schneider", "transdüser V/Z/W metodu"
  gibi bir AQUA CNT donanım/yazılım referans sorusu sordu.
  Keywords: AQUA, AQUA CNT, 100S, 100F, 100FP, 100SL, modem, status, LED,
  GSM, GPRS, APN, SIM, anten, çekim, CSQ, kademe, hedef, Tablo 1.2,
  register, modbus, TCP, 502, control word, status word, alarm, uyarı,
  word 1, word 2, bit, pil, NTC, koru1000, KORU 1000, SCADA link, linkleme,
  antiblokaj, acil senaryo, taklit, debimetre, ultrasonik, transdüser,
  Longrun, Krohne, ENELSAN, IFC50, IFC300, basınç sensörü, seviye sensörü,
  Klemsan, Entes, Schneider, PM2100, MPR32S, KLEA220P, statik seviye,
  dinamik seviye, NPSH, M00, M23, M91, V metodu, Z metodu, W metodu,
  Çalışma Mod, Serbest, Depo Doldurma, Hidrofor, Basınç PI, SSR, mgbs,
  internetstatik, statikip, Turkcell, Vodafone, Türk Telekom.
version: "1.0.0"
---

# AQUA CNT 100S / 100F / 100FP / 100SL — Cihaz Referansı

> **KAYNAK:** AQUA CNT Kullanım Kılavuzu Türkçe (2022, Rev 1.2.1).
> Bu skill, kılavuzun tüm kritik tablolarını ve referanslarını markdown olarak
> içerir. PDF silindi (çıkarma tamamlandı); yeniden çıkarma gerekirse orijinal
> PDF `envest-web` assets klasöründen alınabilir.

---

## 🧭 Hangi soru → hangi dosya (LLM için routing tablosu)

Kullanıcı sorusu geldiğinde `get_skill('aqua-devices', '<dosya>')` çağır:

| Kullanıcı soruyu nasıl soruyor? | Hangi dosya? |
|---|---|
| "Modem status 2" / "modemim 15'te takılı" / "LED kırmızı yanıp sönüyor" / "GSM çekim gücü" / "APN ne olmalı" / "anten zayıf" / "SIM kart" | `modem-status.md` |
| "Hedef 11 var, motor çalışmıyor" / "ekranda hedef!100 yazıyor" / "Tablo 1.2" / "sistem otomatikte mi" / "201 manuelde çalışıyor" / "taklit et acil" | `hedef-status.md` |
| "Alarm listesi" / "motor termik hata" / "SurucuElModCalisiyor" / "Pil Sıcaklık Yüksek" / "Giriş Voltaj Yüksek" / "Akım Alarm" | `alarms-and-warnings.md` |
| "Register X" / "Control Word bit 3" / "Status Word nedir" / "modbus 28 adresi" / "FC3 FC16" / "tek sorguda kaç word" | `modbus-reference.md` |
| "İşletme ekranı" / "ana menü" / "tuş takımı" / "LCD ekran 60 sn uyku" / "COSQ L1 L2 L3" | `display-and-menus.md` |
| "Çalışma modu" / "Depo Doldurma" / "Hidrofor" / "Basınç PI" / "SCADA linkleme" / "antiblokaj 90dk 5dk" / "acil senaryo" | `operating-modes.md` |
| "Min akım koruma" / "max basınç" / "koruma zamanı" / "voltaj koruma" / "alarm 3 defa reset" | `motor-protection.md` |
| "24V besleme" / "2.5A" / "4-20mA giriş" / "röle çıkış" / "opto coupler" / "100F dahili debimetre" / "100FP sensör" / "100SL seviye" / "IP65" / "14.8V Li-Po" | `hardware-reference.md` |
| "Debimetre M00-M92" / "V metodu Z metodu" / "transdüser yerleştirme" / "hata kodu I J H F G K" / "boş boru" / "sinyal yok" / "kalibrasyon" | `ultrasonic-flowmeter.md` |

> **Kural:** Yukarıdaki tabloya uyan bir soru geldiğinde **SCADA tool'larını
> çağırmadan önce** bu skill dosyasını oku. Cihaz içi (hardware) sorunun
> cevabı kılavuzdadır — canlı SCADA verisine ancak durum teyidi için ihtiyacın
> olabilir.

---

## Ortak Sabitler / Konvansiyonlar

| Konu | Değer |
|---|---|
| Default APN (Turkcell) | `mgbs` |
| Hedef cihaz AQUA ise Modbus ID | 3 |
| Hedef cihaz AQUA ise Modbus Port | 502 |
| Modbus TCP standard port | 502 |
| Modbus RTU hattı | 9600 / 8 / N / 1 |
| Debimetre RS485 ID (sabit) | 1 |
| Analizör RS485 ID (sabit) | 2 |
| Tek sorguda max word | 64 |
| Min sorgu aralığı | 1 sn |
| Hem SCADA hem hedef sorgusu yapılan noktada | ≥ 15 sn |
| Birden fazla SCADA eşzamanlı | ≥ 30 sn |
| Max eş zamanlı SCADA sorgusu | 5 |
| Modbus FC destekleri | FC3, FC6, FC16, FC22 |
| Modbus float register | adres + 10000 |
| Cihaz besleme | 24 VDC, min 2.5 A |
| Dahili Li-Po pil | 14.8 V, 12 800 mAh |
| Pil şarj şartları | Sıcaklık 0–45 °C, besleme > 21 VDC, akım > 1 A |
| Düşük güç modu eşiği | Pil %40 altı (HW v1.2+) |
| Modem minimum çalışma frekansı | Motor referans min **30 Hz** (sabit) |
| Koruma cihaz sınıfı | IP65 |
| LED yeşil | GPRS/SCADA bağlandı (1 Hz yanıp söner) |
| LED kırmızı | Sistemde alarm var (1 Hz yanıp söner) |
| Ekran uyku modu | 60 sn tuşa basılmazsa → "KORU1000, Lütfen Bir Tuşa Basınız" |
| Alarm otomatik reset sayısı | 3 defa × 15 dk arayla; 4. → kalıcı alarm (manuel reset) |

---

## Model Karşılaştırma Matrisi

| Özellik | 100S | 100F | 100FP | 100SL |
|---|---|---|---|---|
| Dahili Debimetre (ultrasonik) | – | ✓ | ✓ | – |
| Dahili Basınç Sensörü | – | – | ✓ | – |
| Dahili Seviye Sensörü | – | – | – | ✓ |
| Harici Anten | ✓ | ✓ | ✓ | ✓ |
| Ultrasonik Pad/Jel | – | ✓ | ✓ | – |
| Montaj Seti | ✓ | ✓ | ✓ | ✓ |
| Kelepçe | – | ✓ | ✓ | – |

- **100S**: Saf izleme/kontrol, dahili sensör yok
- **100F**: Ultrasonik debimetre dahil
- **100FP**: Debimetre + basınç sensörü (pompa kontrol noktalarında)
- **100SL**: Seviye sensörü (su dağıtım depoları)

---

## Tuş Takımı ve Temel Kontroller

- **C tuşu**: geri git / üst menü / iptal
- **Aşağı / Yukarı**: menü / değer değiştir
- **OK**: onay / kaydet
- **OK (alarm ekranında)**: alarmları resetle
- **OK (açılış ekranında)**: motor Çalış/Dur (30 sn arayla art arda)
- **Aşağı + Yukarı beraber (açılış ekranında)**: Otomatik Mod ↔ Manuel Mod geçiş

---

## Alt Dosyalar (detay içerik)

- `modem-status.md` — Tablo 1.1 modem durumları + LED + GSM + APN + Hedef IP ayarları
- `hedef-status.md` — Tablo 1.2 çalışma durumu kodları (10–201 arası, "motor çalışıyor/çalışmıyor" + "hedefle hab. var/yok")
- `display-and-menus.md` — İşletme ekranı 1 ve 2, ana menü ağacı (8 başlık)
- `operating-modes.md` — Serbest/Depo Doldurma/Hidrofor/Basınç PI + SCADA linkleme + antiblokaj + acil senaryo
- `motor-protection.md` — Koruma eşikleri ve zaman ayarları
- `alarms-and-warnings.md` — Tablo 4.1 alarm listesi + Uyarı Word + Alarm Word bit açıklamaları
- `modbus-reference.md` — Register 0-94 + Status Word 1 + Control Word 1/2 + bit tanımları
- `hardware-reference.md` — Donanım, besleme, I/O, 100FP basınç sensörü, 100SL seviye sensörü, pil
- `ultrasonic-flowmeter.md` — Dahili debimetre M00-M92 menü + V/Z/W metodu + R/I/J/H/F/G/K hata kodları
