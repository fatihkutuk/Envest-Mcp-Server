# AQUA CNT — Modem Durumu, LED, GSM ve Haberleşme

> **Kaynak:** AQUA CNT Kullanım Kılavuzu, Tablo 1.1 + Şekil 1.1 (s7–8) +
> APN ve Hedef IP ayarları (s16–12).

Bu dosya, işletme ekranının 2. satırında gösterilen **"Modem: X"** değerinin
anlamını, çözüm yollarını, çekim gücü (CSQ) kademelerini ve GSM haberleşme
ayarlarının TAM referansını içerir.

---

## 1. Tablo 1.1 — Modem Çalışma Durumu (KRİTİK)

İşletme ekranının 2. satırında `Modem: X` şeklinde gösterilir. LED'lerle
birlikte yorumlanır.

| Modem Durum | LED | Ne anlama gelir? | Tipik sebep / aksiyon |
|---|---|---|---|
| **0** | LED **yanmıyor** | Modeme enerji yok | Modem regülatörü arızalı **veya** modem power-on transistörü arızalı. Donanım servisi gerekir. |
| **0** | **Yanıp sönüyor** | Modem enerjili ama haberleşme **hiç** kurulamıyor | Modem 150 sn boyunca 0'dan kurtulamazsa cihaz kendini resetler. Bekle; süreklileşirse anten/SIM kontrol. |
| **1** | – | SIM kart sorgulanıyor | Uzun süre 1'de kalıyorsa: SIM kartta **PIN kodu tanımlı** olabilir (kilitli), **SIM yuvası bozuk** olabilir ya da **SIM yok**. |
| **2** | – | GSM network'üne bağlanmaya çalışıyor | Bir sonraki adıma geçmiyorsa: **GSM şebeke bağlanma problemi** var. **Anten takılı değil** veya **çekim gücü zayıf** olabilir. |
| **15** | – | GSM bağlantısı kuruldu; cihaz port **502'den Modbus TCP sorgusu bekler** | Sorguya ulaşabilmek için **APN Network** ayarlarının doğru yapılması gerekir. Varsayılan: Turkcell statik IP için `mgbs`. |
| **102** | – | Cihaz **hedef IP**'ye (başka AQUA / SCADA) bağlanmayı deniyor | Hedef IP / Port / Modbus ID / RegAdres ayarlarını kontrol et (aşağıda detay). |

> **Özet kural:**  
> `Modem: 0` → enerji / donanım  
> `Modem: 1` → SIM  
> `Modem: 2` → GSM kapsama / anten  
> `Modem: 15` → hat kuruldu, **APN veya sunucu-tarafı** problem  
> `Modem: 102` → hedef IP'ye giden **dış bağlantı** problemi

---

## 2. LED Göstergeleri

| LED | Anlam |
|---|---|
| **Yeşil LED** — saniyede bir yanıp sönme | GPRS bağlantısı ve SCADA haberleşmesi **kurulu** |
| **Kırmızı LED** — saniyede bir yanıp sönme | Sistemde **alarm var** (Tablo 4.1'deki alarmlardan biri aktif) |
| Yeşil yanmıyor, Modem: 15 | APN yanlış, statik IP alınamıyor, SCADA sunucusuna ulaşılamıyor |

---

## 3. Çekim Gücü (CSQ)

İşletme ekranı 1. satırda saat/tarih ile birlikte gösterilir. Aralık 0–31.

| CSQ Aralığı | Kademe |
|---|---|
| 0 – 16 | 1. Kademe (zayıf) |
| 16 – 22 | 2. Kademe |
| 22 – 26 | 3. Kademe |
| 27 – 31 | 4. Kademe (çok iyi) |

- CSQ ≤ 16 ise **`Modem: 2`** veya uzun `Modem: 15` + kopukluk olağandır.
  Anten yönünü değiştir, harici anten uzatması kullan, kapalı pano içinden
  çıkar.
- SCADA'da `GsmCekimGucu` tag'i bu değerdir.

---

## 4. APN Network Ayarı (Sistem Ayarları → APN Network)

Varsayılan: Turkcell statik IP APN'si `mgbs`.

| Operatör | Önerilen APN |
|---|---|
| Turkcell | `mgbs` |
| Vodafone | `internetstatik` |
| Türk Telekom | `statikip` (ya da özel data / yurtdışı APN) |

Ayar ekranında metin girilirken **C tuşu** boşluk bırakır; zaman aşımında
otomatik `mgbs` atanır.

---

## 5. Hedef Sunucuya (SCADA / Başka AQUA) Bağlanma Ayarları

Kullanıcı "Modem: 102" veya "hedefe bağlanamıyor" dediğinde kontrol sırası:

| Ayar | Menü Yeri | Kural |
|---|---|---|
| İzinli IP Filtresi | Sistem Ayarları → İzinli IP 1-1 … 2-4 | 2 adet IP filtresi tanımlanabilir; boşsa `0.0.0.0` |
| Hedef Besleme IP | Sistem Ayarları → Hedef Besleme IP-1 | Hedef cihaz / sunucu IP'si (Oktet oktet girilir) |
| Hedef Modbus RegAdres | Sistem Ayarları → Hedef Modbus RegAdres | Okunacak register adresi. **Float ise +10000 ekle** |
| Hedef Modbus ID | Sistem Ayarları → Hedef Modbus ID | **Hedef AQUA ise 3 gir** |
| Hedef Sorgu Port | Sistem Ayarları → Hedef Sorgu Port | **Hedef AQUA ise 502** |

> **15 sn kuralı:** Aynı noktada hem SCADA sorgusu hem de hedef depo
> seviyesi sorgusu yapılıyorsa sorgu aralıkları **minimum 15 saniye**
> olmalıdır. Birden fazla SCADA aynı anda sorgu atıyorsa **minimum 30 sn**.
> Aynı anda max 5 sorgu aktif olabilir.

---

## 6. Modem Status 2 — Sistematik Sorun Giderme

Kullanıcı "Modem Status 2'de kalıyor" dediğinde sırayla:

1. **Fiziksel anten kontrolü**
   - Yan paneldeki SMA antenin sıkı takılı olduğunu teyit et.
   - Pano metal içindeyse anteni pano dışına uzat.
2. **Çekim gücü (CSQ) kontrolü**
   - SCADA'da `GsmCekimGucu` veya ekrandan CSQ değerine bak.
   - CSQ < 16 ise cihaz sürekli `Modem: 2` durumunda kalır.
3. **SIM kart kontrolü**
   - Kapağı aç, SIM kartın yuvasında olduğunu teyit et.
   - SIM başka bir cihaza takılıp network görmesi test edilebilir.
   - SIM PIN kodu OLMAMALI.
4. **Operatör / APN kontrolü**
   - SIM kart statik IP abonesi mi? (Turkcell "mobgus", Vodafone statik,
     Türk Telekom statikip servisi).
   - APN ayarının operatöre uygun olması (Tablo §4).
5. **Yerel / konum faktörü**
   - Bodrum, yer altı kuyu odası, metal konteyner içindeyse kapsama
     alanına çıkar.

> **SCADA tag'lerinden teyit ederken:** `GsmCekimGucu`,
> `Status_HedefleHaberlemeVar` (Status Word 1 bit 2), cihaz `IP`, `IMEI`.
> Ama önce bu skill'deki yönlendirmeyi uygula — çoğu vaka fiziksel katmanda
> çözülür.

---

## 7. İlgili Tag / Register

- Register **30 — StatusWord**: bit 2 = Hedefle Hab. Var
- "Hakkında" ekranı: HW/SW versiyon, statik IP, IMEI, Cihaz Seri No
- Kullanıcı aşağıdaki tag'leri sorguluyorsa modem-status ile alakalı:
  `GsmCekimGucu`, `Status_HedefleHaberlemeVar`, `XC_AquaRestart` (yeniden
  başlatma bitleri için `modbus-reference.md` → Control Word 1).
