# AQUA CNT — Hedef Çalışma Durumu Kodları (Tablo 1.2)

> **Kaynak:** AQUA CNT Kullanım Kılavuzu, Tablo 1.2 "AQUA Çalışma Durum
> Bilgileri" (s9). İşletme ekranının 2. satırında **`Hedef: X`** veya
> **`Hedef! X`** şeklinde gösterilir.

Bu kod, cihazın **hangi çalışma senaryosunda** olduğunu ve motorun o an
**çalışıp çalışmadığını** tek rakamla özetler. İki haneye dikkat:
- **İlk hane / yüzler basamağı** → senaryo tipi
- **Birler basamağı** → motor çalışıyor (1) / çalışmıyor (0)

---

## 1. Tablo 1.2 — TAM Liste

| Durum | Senaryo | Motor | Açıklama |
|---|---|---|---|
| **0** | Seçilmedi | – | Çalışma durumu seçilmedi, **Sistem otomatikte** ama mod tanımlı değil |
| **10** | Hedef **Besleme** (Depo Doldurma) | Çalışmıyor | Hedefle haberleşme **VAR**, hedef "dur" istiyor veya şartlar uygun değil |
| **11** | Hedef **Besleme** (Depo Doldurma) | **Çalışıyor** | Hedefle haberleşme **VAR**, depo doluyor |
| **100** | Hedef Besleme | Çalışmıyor | Hedefle haberleşme **YOK**, **geçmişi taklit et-acil durum AKTİF** ama şu an durma periyodunda |
| **101** | Hedef Besleme | **Çalışıyor** | Hedefle haberleşme **YOK**, **taklit et-acil aktif**, çalışma periyodunda |
| **120** | Hedef Besleme | Çalışmıyor | Hedefle haberleşme **YOK**, **taklit et-acil PASİF** → hedef kurtulana kadar "acil durum bekleme süresi"/"acil durum çalışma süresi" döngüsü |
| **121** | Hedef Besleme | **Çalışıyor** | 120 döngüsünde çalış periyoduna girdi |
| **20** | Hedef **Basınç** | Çalışmıyor | Basınç senaryosu aktif, şu an basmıyor |
| **21** | Hedef **Basınç** | **Çalışıyor** | Basınç senaryosu aktif, basıyor |
| **200** | Sistem **Manuelde** | Çalışmıyor | Operatör manuel moda almış, motor durdurulmuş |
| **201** | Sistem **Manuelde** | **Çalışıyor** | Manuel başlatılmış (30 sn arayla 2 kez OK tuşuyla da olabilir) |
| **30** | **Basınç PI** | Çalışmıyor | PI setpoint sağlanıyor / durma periyodunda |
| **31** | **Basınç PI** | **Çalışıyor** | PI aktif, motoru sürücü frekansıyla süvüyor |

---

## 2. Hızlı Teşhis Kartı

| Sorun | Ne soruyorsun? | Cevap |
|---|---|---|
| "Hedef 11 ama ben motor çalışıyor görmüyorum" | SCADA'da StatusWord bit 5 "Motor Çalışıyor" | Register 30 bit 5'i kontrol et; ekran ile StatusWord farklıysa iletişim gecikmesi olabilir |
| "Hedef 100/101/120/121 olmuş" | Hedefle haberleşme neden koptu? | `modem-status.md` dosyasına bak. Hedef IP / port / APN / anten |
| "Hedef 200 olduysa neden motor durdu?" | Operatör manuel moda almış | Ana açılış ekranında **Yukarı + Aşağı birlikte** → otomatik moda geçiş |
| "Hedef 0 yazıyor ama sistem otomatik görünüyor" | Çalışma modu seçilmemiş | Motor Çalışma Ayarları → Çalışma Mod menüsünden 1/2/3 seç |
| "30/31'deyim ama basınç oturmuyor" | PI parametreleri | `operating-modes.md` → Basınç PI Set + Basınç PI Zaman |

---

## 3. İlgili Senaryo Dosyaları

- **Senaryolar** (Hedef Besleme nasıl çalışır, Acil Durum, SCADA linkleme,
  Antiblokaj): `operating-modes.md`
- **Hedef IP/port/ID tanımlamaları**: `modem-status.md` §5
- **Status Word register bit tanımları** (Sistem Otomatikte, Hedefle Hab. Var,
  Motor Çalışıyor): `modbus-reference.md`

---

## 4. Status Word 1 ile Hedef Kodu Arasındaki İlişki

Ekranda "Hedef X" görürsün, Modbus'tan `StatusWord-1` (register 30) okursun.
İki kaynak aynı durumu farklı açıdan anlatır.

| Hedef Kodu | StatusWord-1 bit 4 (Otomatik) | bit 2 (Hedefle Hab. Var) | bit 5 (Motor Çalışıyor) |
|---|---|---|---|
| 10 | 1 | 1 | 0 |
| 11 | 1 | 1 | 1 |
| 100 | 1 | 0 | 0 |
| 101 | 1 | 0 | 1 |
| 120 | 1 | 0 | 0 |
| 121 | 1 | 0 | 1 |
| 200 | 0 | – | 0 |
| 201 | 0 | – | 1 |
| 30 | 1 | – | 0 |
| 31 | 1 | – | 1 |

> `Hedef: X` → hedefle haberleşme **var**  
> `Hedef! X` → hedefle haberleşme **yok** (ünlem işareti haberleşme
> kopukluğunun ekran notasyonudur)
