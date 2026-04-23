# AQUA CNT — İşletme Ekranları ve Menüler

> **Kaynak:** AQUA CNT Kullanım Kılavuzu, Bölüm 1 "İşletme Ekranı" (s7–9) +
> Şekil 2.3 ana menü ağacı.

---

## 1. Ana Menü (8 Başlık)

LCD 64×128 grafik ekran + 4 tuş membran (C / Yukarı / Aşağı / OK).

```
> İşletme
  Sistem Ayar
  Motor Calisma Ayar
  Motor Koruma Ayar
  Alarm ve Uyarılar
  Modbus RTU Ayar
  Hakkında
  Cihaz Test
```

| Menü | Ne içerir? |
|---|---|
| **İşletme** | 2 sayfa canlı veri (aşağıda §2–3) |
| **Sistem Ayar** | IP, APN, debimetre/basınç/seviye giriş tanımlamaları, analizör, log süresi |
| **Motor Calisma Ayar** | Çalışma modu, hedef min/max seviye, hidrofor min/max basınç, PI, acil senaryo, SCADA linkleme, antiblokaj |
| **Motor Koruma Ayar** | Koruma eşikleri + koruma zamanları |
| **Alarm ve Uyarılar** | Aktif alarmları görüntüle / manuel reset |
| **Modbus RTU Ayar** | RS-485 debimetre/analizör ID + baud |
| **Hakkında** | koru1000.com, HW/SW versiyon, Statik IP, IMEI, Seri No |
| **Cihaz Test** | Fabrika test (şifreli, servis için) |

---

## 2. İşletme Ekranı — 1. Sayfa

```
22:23:58  1: 1: 0  0
Modem: 1       Calis:200
D1:0.0   D2:0.0
B1:0.0   B2:0.0
S1:0     S2:0
Hedef!0  HdfHab:0
GrsV:0.0 Scada:31
Pil:96.6 Manuel
```

Satır bazında:

| Satır | İçerik |
|---|---|
| 1 | Saat + Tarih + **Çekim gücü (CSQ 0–31)** |
| 2 | **Modem: X** (Tablo 1.1) + **Calis: Y** (Tablo 1.2 → `hedef-status.md`) |
| 3 | Debi-1 / Debi-2 (m³/h) |
| 4 | Basınç-1 / Basınç-2 (bar) |
| 5 | Seviye-1 / Seviye-2 (cm) |
| 6 | **Hedef seviye + son hedef haberleşmesinden bu yana (sn)** — `Hedef: X` (hab. var) / `Hedef! X` (hab. yok) |
| 7 | Giriş Besleme Voltaj + SCADA'dan son sorgu kaç sn önce geldi |
| 8 | **Pil: yüzde + şarj durumu + oto/manuel** (`Pil:` normal mod, `Pil!` düşük güç modu) |

### Çekim gücü (CSQ) kademeleri

| CSQ | Kademe |
|---|---|
| 0–16 | 1. Kademe |
| 16–22 | 2. Kademe |
| 22–26 | 3. Kademe |
| 27–31 | 4. Kademe |

### Hedef Bildirim Notasyonu

- `Hedef:X` (iki nokta) → hedefle haberleşme **VAR**
- `Hedef!X` (ünlem) → hedefle haberleşme **YOK** — `hedef-status.md` §1

---

## 3. İşletme Ekranı — 2. Sayfa

```
L1:0.0V   L1:0.0A
L2:0.0V   L2:0.0A
L3:0.0V   L3:0.0A
P:0.0     OA:0.0A
COSQ:0.00 F:0.0Hz
SFrq:30.0
D.Girisler: 0 0 0 0
D.Cikislar: 0 0
```

| Satır | İçerik |
|---|---|
| 1–3 | L1/L2/L3 faz voltajları ve akımları |
| 4 | **P** = anlık toplam güç, **OA** = ortalama akım |
| 5 | **COSΦ** + **F** = şebeke frekansı. *COSΦ 0–1 dışında ise akım trafosu yönleri ters* |
| 6 | **SFrq** = sürücü çıkış frekansı (sürücülü motorda) |
| 7 | Dijital giriş 1–4 fiziksel durumları |
| 8 | Dijital çıkış 1–2 fiziksel durumları |

---

## 4. Hakkında Ekranı Şablonu

```
---HAKKINDA---
www.koru1000.com
Envest Enerji LTD STI
Tel: 444 51 29
HW: V1.1    SW: V1.05
IP:
IMEI:
SeriNO: 17105985
```

- **HW V1.2+** için "Düşük Güç Modu" ve "Çıkış Enerjisini Kes"
  (Control Word 1 bit 5) özellikleri geçerlidir.
- Soruda "HW versiyonu nedir" veya "eski cihaz mı" geçiyorsa buradan bak.

---

## 5. Ekran Uyku Modu

- 60 sn hiçbir tuşa basılmazsa ekran uyku → `"KORU1000, Lütfen Bir Tuşa Basınız"`
- Herhangi bir tuş → uyku çıkar.
- **Ekran ışığı yanıyor ama veri yok** veya **ekran kapalı iken membran
  ışıkları yanıyor** → membran–LCD kablo kontrolü gerek.

---

## 6. Tuş İşlevleri (Özet)

| Tuş | Normal menü | Açılış / alarm ekranı |
|---|---|---|
| **C** | Geri / üst menü / iptal | – |
| **Yukarı** | Üst menü / değer ↑ | (+Aşağı birlikte) Oto ↔ Manuel |
| **Aşağı** | Alt menü / değer ↓ | (+Yukarı birlikte) Oto ↔ Manuel |
| **OK** | Onayla / kaydet | **Alarm ekranı**: alarm reset; **Açılış**: 30 sn arayla 2 kez → Çalış/Dur komutu |
