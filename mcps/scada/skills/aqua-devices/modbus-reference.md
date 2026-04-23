# AQUA CNT — Modbus TCP / RTU Referansı

> **Kaynak:** AQUA CNT Kullanım Kılavuzu, Bölüm 7 "MODBUS TCP Haberleşme
> Tablosu" (s31–36).

Bu dosya: Modbus TCP bağlantı kuralları + register 0-94 + Status Word 1 +
Control Word 1 + Control Word 2 + Uyarı/Alarm Word bit haritası.

> **Uyarı/Alarm Word bit tanımları için** ayrıca `alarms-and-warnings.md`
> dosyasına da bak (orada alarm bazlı çözüm rehberi var).

---

## 1. Bağlantı Kuralları

| Madde | Değer |
|---|---|
| Protokol | Modbus TCP |
| Port | **502** |
| Modem | Dahili GSM 2G |
| Max eş zamanlı sorgu | **5** |
| Min sorgu aralığı (tek SCADA) | 1 sn |
| Min sorgu aralığı (hem SCADA hem hedef depo) | **15 sn** |
| Min sorgu aralığı (birden fazla SCADA) | **30 sn** |
| Tek sorguda max word | **64** |
| Desteklenen FC | FC3, FC6, FC16, FC22 |
| Float register | Adres + **10000** (örn. adres 100 float ise `10100` iste) |
| Control Word 2 + sonrası | **Kalıcı hafıza** (güç kesse bile korunur) |

**Modbus RTU (RS-485) — Debimetre / Analizör hattı:**
- Baud: **9600**, 8 bit, N (no parity), 1 stop
- Debimetre ID: **1** (sabit)
- Analizör ID: **2** (sabit)

---

## 2. Register Tablosu (0 – 94)

| Adres | İsim | Tip | Çarpan | Not |
|---|---|---|---|---|
| 0 | L1 Voltaj | WORD | /10 | V |
| 1 | L1 Akım | WORD | /10 | A |
| 2 | L2 Voltaj | WORD | /10 | V |
| 3 | L2 Akım | WORD | /10 | A |
| 4 | L3 Voltaj | WORD | /10 | V |
| 5 | L3 Akım | WORD | /10 | A |
| 6 | Anlık Ortalama Akım | WORD | /10 | A |
| 7 | CosΦ | WORD | /10 | – |
| 8 | Anlık Güç | WORD | /10 | kW |
| 9 | Şebeke Frekans | WORD | /10 | Hz |
| 10 | Toplam Debimetre | FLOAT | – | m³ |
| 12 | Toplam Aktif Güç | DWORD | – | kWh |
| 14 | Toplam Reaktif Güç | DWORD | – | kVARh |
| 16 | Dijital Girişler | WORD | – | bitmask |
| 17 | Debi-1 | WORD | /10 | m³/h |
| 18 | Debi-2 | WORD | /10 | m³/h |
| 19 | Basınç-1 | WORD | /100 | bar |
| 20 | Basınç-2 | WORD | /100 | bar |
| 21 | Seviye-1 | WORD | – | cm |
| 22 | Seviye-2 | WORD | – | cm |
| 23 | Pil Seviye % | WORD | – | % |
| 24 | RTC (Epoch Time) | DWORD | – | Unix ts (GSM üzerinden senkron) |
| 26 | **Uyarılar-1** | WORD | – | bit tablosu §5 |
| 27 | Uyarılar-2 | WORD | – | **yedek** |
| 28 | **Alarmlar-1** | WORD | – | bit tablosu §5 |
| 29 | Alarmlar-2 | WORD | – | **yedek** |
| 30 | **StatusWord-1** | WORD | – | bit tablosu §3 |
| 31 | Besleme Voltajı | WORD | /10 | V |
| 32 | NTC Pil Sıcaklık | WORD | /10 | °C |
| 33 | Hedef Besleme Seviye | WORD | – | cm (hedeften okunan) |
| 34 | Dinamik Seviye | WORD | – | cm (motor çalışırken) |
| 35 | Statik Seviye | WORD | – | cm (motor dururken) |
| 36 | NPSH | WORD | – | m |
| 37 | Dijital Çıkışlar | WORD | – | bitmask |
| 38 | **ControlWord-1** | WORD | – | bit tablosu §4 (geçici) |
| 39 | **ControlWord-2** | WORD | – | bit tablosu §4 (**kalıcı hafıza**) |
| 40 | Motor Sürücü Çıkışı | WORD | /10 | Hz |
| 41 | Sensör Montaj Derinlik | WORD | – | m |
| 42 | Pompa Montaj Derinlik | WORD | – | m |
| 43 | Çalışma Mod | WORD | – | 0=Serbest, 1=Hedef Seviye, 2=Hidrofor, 3=Basınç PI |
| 44 | Motor Çalış Çıkışı | WORD | – | 0=yok, 1=DO1, 2=DO2 |
| 45 | Su Seviye Koruma Zaman | WORD | – | sn |
| 46 | Akım Koruma Zaman | WORD | – | sn |
| 47 | Voltaj Koruma Zaman | WORD | – | sn |
| 48 | Basınç Koruma Zaman | WORD | – | sn |
| 49 | Debi Koruma Zaman | WORD | – | sn |
| 50 | PI Timer | WORD | – | ms |
| 51 | Motor Koruma Min. Voltaj | WORD | /10 | V |
| 52 | Motor Koruma Maks. Voltaj | WORD | /10 | V |
| 53 | Hedef Belirleme IP-1 | WORD | – | 1. oktet |
| 54 | Hedef Belirleme IP-2 | WORD | – | 2. oktet |
| 55 | Hedef Belirleme IP-3 | WORD | – | 3. oktet |
| 56 | Hedef Belirleme IP-4 | WORD | – | 4. oktet |
| 57 | Hedef Besleme Modbus Adres | WORD | – | **float ise +10000** |
| 58 | Hedef Besleme Modbus ID | WORD | – | hedef AQUA ise **3** |
| 59 | Hedef Besleme Modbus Port | WORD | – | hedef AQUA ise **502** |
| 60 | Hedef Minimum Su Seviye | WORD | – | cm |
| 61 | Hedef Maksimum Su Seviye | WORD | – | cm |
| 62 | Min. Su Basınç | WORD | /100 | bar |
| 63 | Max. Su Basınç | WORD | /100 | bar |
| 64 | Motor Sürücü Max Referans Set | WORD | – | Hz (50 default) |
| 65 | Acil Senaryo Bekleme Süre | WORD | – | dk (10–300) |
| 66 | Acil Senaryo Çalışma Süre | WORD | – | dk (10–300) |
| 67 | Basınç PI Set | WORD | /100 | bar |
| 68 | Motor Koruma Su Seviye Min. | WORD | – | cm |
| 69 | Motor Koruma Su Seviye Maks. | WORD | – | cm |
| 70 | Motor Koruma Akım Min. | WORD | /10 | A |
| 71 | Motor Koruma Akım Maks. | WORD | /10 | A |
| 72 | Motor Koruma Basınç Min. | WORD | /100 | bar |
| 73 | Motor Koruma Basınç Maks. | WORD | /100 | bar |
| 74 | Motor Koruma Debi Min. | WORD | /10 | m³/h |
| 75 | Motor Koruma Debi Maks. | WORD | /10 | m³/h |
| 76 | Debi-1 SET | WORD | – | m³/h (max skala) |
| 77 | Debi-2 SET | WORD | – | m³/h |
| 78 | Basınç-1 SET | WORD | – | bar (max skala) |
| 79 | Basınç-2 SET | WORD | – | bar |
| 80 | Seviye-1 SET | WORD | – | cm (max skala) |
| 81 | Seviye-2 SET | WORD | – | cm |
| 82 | Debi1 Giriş | WORD | – | bağlantı seçimi (0–8) |
| 83 | Debi2 Giriş | WORD | – | bağlantı seçimi |
| 84 | Basınç1 Giriş | WORD | – | 0=yok, 1=AI1, 2=AI2, 3=AI3 |
| 85 | Basınç2 Giriş | WORD | – | " |
| 86 | Seviye1 Giriş | WORD | – | " |
| 87 | Seviye2 Giriş | WORD | – | " |
| 88 | Motor Termik Giriş | WORD | – | 1–4 (DI) |
| 89 | Motor Çalışıyor Giriş | WORD | – | 1–4 (DI) |
| 90 | Debimetre PulsÇarpanı | WORD | – | 1m³ için pulse adedi |
| 91 | Debimetre Tip Seçim | WORD | – | 0=Longrun, 1=Krohne IFC50, 2=Krohne IFC300, 3=ENELSAN |
| 92 | Analizör Tip Seçim | WORD | – | 0=Klemsan KLEA220P, 1=Entes MPR32S, 2=Schneider PM2100 |
| 93 | SSR Giriş | WORD | – | 1–4 (DI) |
| 94 | Log Tutma Sıklığı | WORD | – | dk (1–1000) |

---

## 3. Status Word 1 (Register **30**) — Bit Tanımları

| Bit | İsim | 1 = |
|---|---|---|
| 0 | Besleme var | Harici 24 V besleme bağlı |
| 1 | Pil şarj oluyor | Şarj aktif |
| 2 | **Hedefle Hab. Var** | Hedef cihaz / SCADA ile sorgu başarılı |
| 3 | **Alarm Var** | En az bir alarm aktif (kırmızı LED) |
| 4 | **Sistem Otomatikte** | Manuel değil |
| 5 | **Motor Çalışıyor** | Motor çıkışı enerjili ve hedef cihazdan / sensörden teyit var |
| 6 | Pil Sıcaklık Düşük | NTC < 0 °C |
| 7 | Pil Sıcaklık Yüksek | NTC > 45 °C |
| 8 | Motor Antiblokaj'da Çalışıyor | 90 dk / 5 dk antiblokaj döngüsünde |
| 9-15 | **Yedek** | – |

> **Status Word 2** (yok / yedek).

---

## 4. Control Word 1 (Register **38**, geçici) + Control Word 2 (Register **39**, kalıcı)

### Control Word 1 — Komut bit'leri (tek atış)

| Bit | Komut | Not |
|---|---|---|
| 0 | **Alarm Reset** | Kalıcı alarmı manuel resetle |
| 1 | **Man Calis/Dur** | Manuel modda motor çalış/dur tetikle |
| 2 | Flash Log Hafıza Temizleme | Log hafızası sıfırla |
| 3 | Link No Error | Haberleşme hata sayacını sıfırla |
| 4 | **AQUA Restart** | Cihazı yeniden başlat |
| 5 | Çıkış Enerjisini Kes | HW v1.2+ — çıkış 24 V kesilir |
| 6-15 | **Yedek** | – |

### Control Word 2 — Ayar bit'leri (**kalıcı hafıza**)

| Bit | Ayar | 1 = |
|---|---|---|
| 0 | **Otomatik** | Otomatik modda |
| 1 | **Hedef Depo Seviyeyi SCADA Yazacak** | SCADA linkleme aktif |
| 2 | Acil Durum Senaryo Aktif | Depo Doldurma modunda hedef yoksa "taklit et" |
| 3 | Düşük Güç Modu Aktif | Pil %40 altı → haberleşme kapanır (HW v1.2+) |
| 4 | Analizör Bağlı | Enerji analizörü okuma aktif |
| 5 | Basınç 2'ye Göre Çalış | Hidrofor modunda referans Basınç-2 |
| 6 | Antiblokaj Aktif | Otomatik modda 90 dk arayla 5 dk çalıştır |
| 7-15 | **Yedek** | – |

> **Dikkat:** Control Word 2 güç kesilse bile korunur. Yazarken önce
> mevcut değeri oku, biti değiştir, geri yaz (read-modify-write).

---

## 5. Uyarı Word 1 / Alarm Word 1 Bit Tanımları

Tam açıklama ve çözümler için `alarms-and-warnings.md`. Kısa:

**Uyarı Word-1 (register 26):**
`0=Analizor Hab.Uyarı, 1=Debimetre Hab.Uyarı, 2=LogBirTurDöndü, 3=LcdBağlıDeğil,
4=FlashHafıza, 5=ADC1, 6=ADC2, 7=ADC3, 8=SürücüElModda, 9=PilKapalı`

**Alarm Word-1 (register 28):**
`0=MotorCalismaHata, 1=MotorTermikHata, 2=SuSeviyeAlarm, 3=Akımalarm,
4=DebiAlarm, 5=BasincAlarm, 6=AnalizorHabHata, 7=DebimetreHabHata,
8=SSRHata, 9=GirişVoltajYüksek, 10=VoltajAlarm`

---

## 6. Sık Kullanılan Okuma Senaryoları

- **Temel izleme (tek sorgu):** adres 0, 20 word → tüm elektrik + debi + basınç + seviye
- **Alarm/Status (tek sorgu):** adres 26, 5 word → Uyarı/Alarm Word 1-2 + StatusWord-1
- **Motor durumu:** register 40 (sürücü Hz) + 43 (mod) + 30 bit 5 (çalışıyor)
- **Hedef tanıtımı (okuma):** 53..59 (7 word) → IP, adres, ID, port
- **Alarm reset komutu:** FC6, adres 38, değer = `0x0001`
- **Cihaz restart:** FC6, adres 38, değer = `0x0010` (bit 4)
- **Alarm resetten sonra:** Control Word 1 otomatik temizlenir (tek atış komutları).
