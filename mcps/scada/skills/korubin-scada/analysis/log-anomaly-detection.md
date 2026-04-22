---
name: log-anomaly-detection
description: |
  Log verisi analizi: sensor saglik kontrolu, patlak tespiti, anomali tespiti.
  Use when: sensor arizasindan supheleniyorken, hat patlagi tespit etmek, veya tag'deki
  anormal degisimleri anlamak gerektiginde. Basinc dususu, sensor kalibre bozuldu, donmus deger.
  Keywords: sensor, ariza, patlak, anomali, anomaly, kalibre, drift, basinc dususu, frozen value.
version: "1.0.0"
---

# Log Anomali ve Sensor Saglik Analizi

Log verisi SCADA sisteminin hafizasidir. Dogru okumayi ogrendiginde cok sey anlayabilirsin.

## 1. Sensor Arizasi Tespiti

Sensorun arizali oldugunu nasil anlarsin:

### Pattern 1: Donmus Deger (Frozen Value)
Sensor degeri cok uzun sure **tamamen ayni** kaliyor (virgulden sonra bile degismiyor).

**Yorum:**
- Sensor baglantisi kopuk olabilir
- Manuel deger girilmis (simulation modu)
- Sensor kalibre ekranindan sabit deger set edilmis

**Tespit:**
```
get_node_log_data(nodeId, tagName="BasincSensoru", days=7)
→ Tum degerler ayni (orn. hep 4.25 bar) → DONMUS, sensor arizali
```

### Pattern 2: Surekli Sifir
Sensor surekli 0 veriyor ama pompa calisiyor.

**Yorum:**
- Sensor baglantisi kopuk
- Analog giris karti arizasi
- Kalibre max yanlis set edilmis

**Tespit:**
```
- Pompa1StartStopDurumu=1 (pompa calisiyor)
- BasincSensoru surekli 0 (son 24 saat)
→ Sensor arizali
```

### Pattern 3: Saçma Sapan Degerler (Out of Range)
Normal 2-8 bar arasinda gezerken birden 50 bar veya -5 bar gibi degerler.

**Yorum:**
- Sensor bozulmak uzere (drift)
- Analog giris kart karisiyor
- EMI/parazit

**Tespit:**
```
get_node_log_summary(nodeId, tagName="BasincSensoru", days=30)
- min=2.1, max=8.3, mean=4.5 (30 gun once)
- son 24 saat: min=-3, max=45 → ANORMAL
```

### Pattern 4: Ani Sapma (Drift)
Uzun sure stabil iken birden farkli bir aralikta takili kaldi.

**Yorum:**
- Kalibre bozuldu
- Sensor eskidi
- Ayarlar degistirildi (user audit log kontrol!)

**Tespit:**
```
- 3 ay once: ortalama 4 bar
- 1 ay once: ortalama 4.2 bar
- Son hafta: ortalama 7.5 bar → Kalibre/ayar degismis olabilir
```

## 2. Hat Patlak Tespiti

Hat sonundaki basinc sensoru (`BasincSensoru2` / `HatBasincSensoru`) patlak yerini soyler.

### Teori: Basinç Düşüş Testi
- Pompa calisirken: hat dolu, basinc = 10 bar (örn.)
- Pompa durdu: cek valf kapanir, hat basinçli kalir
- Eger hat saglam: basinc yavas yavas 10 bar civarinda kalir
- Eger **patlak var**: basinc dusmeye baslar
- Dusmeyi durdurdugu seviye = patlagin irtifasi

**Formul:**
```
Patlak irtifasi (metre) = hat_basinc_dusus_son_deger (bar) × 10.2
```

**Ornek:**
- Pompa durdu, hat basinci 10 bar
- 5 dakika sonra: 8 bar
- 30 dakika sonra: 6 bar
- 2 saat sonra: 6 bar (degismiyor)
- Patlak yerin irtifasi: 6 × 10.2 = ~61 metre
- Pompanin bulundugu yerden 61m yukaridaki bir noktada patlak var

### Is Akisi

```
1. Pompa durumu tarihi bul:
   get_node_log_data(nodeId, tagName="Pompa1StartStopDurumu",
                     start=<1 gun once>, end=<simdi>)

2. Pompa durdugu zamanlari cikart:
   - durus_zamanlari = [t for t in log if pompa_durumu == 0 and onceki == 1]

3. Her durus icin basinc egrisini al:
   get_node_log_data(nodeId, tagName="HatBasincSensoru",
                     start=<durus_zamani>, end=<durus_zamani + 2 saat>)

4. Egri analizi:
   - Baslangic basinci (pompa calisirken): P0
   - 2 saat sonraki basinc: P_final
   - Eger P_final > P0 * 0.9 → hat SAGLAM (normal sizinti)
   - Eger P_final < P0 * 0.5 → PATLAK VAR
   - Dusup yataylastigi nokta = patlak yeri

5. Sonuc:
   Patlak yaklasik irtifa = P_final × 10.2 metre
```

## 3. Sayaç Hatasi / Reset Tespiti

Sayaç (`T_` ile baslayan tag'ler) normalde **sadece artar**. Eger azaliyorsa sorun var.

### Pattern: Sayaç Resetlenmis
```
13:00 → T_ToplamDebi = 125,430
13:15 → T_ToplamDebi = 0 (veya 1.2 gibi cok dusuk)
```
**Yorum:** Cihaz resetlendi (elektrik kesildi, firmware guncellendi, ayarlar elle degistirildi)

### Pattern: Sayaç Geri Gidiyor
```
13:00 → T_ToplamDebi = 125,430
13:15 → T_ToplamDebi = 125,400 (azalmis!)
```
**Yorum:** Sensor arizasi veya manuel mudahale (user audit log kontrol)

### Is Akisi

```
1. Sayaç tag'ini bul: search_tags(deviceId=nodeId, pattern="T_*")
2. Son 30 gunluk log: get_node_log_data(nodeId, tagName="T_ToplamDebi", days=30)
3. Delta hesapla: her noktada (tn - t(n-1))
4. Negatif delta = reset/geri gidis anomalisi
5. Log kayitlarini kullanicaya sun
```

## 4. Akilli Sorgulama Stratejisi

Log tablolari milyonlarca satir olabilir. Sistemi patlatmadan sorgulamak icin:

### Buyuk Tablolarda
**YAPMA:**
```
SELECT * FROM noktalog.logdata WHERE devId=23280 -- TUM LOG, milyonlar
```

**YAP:**
```
SELECT * FROM noktalog.logdata
WHERE devId=23280
  AND tagName='Debimetre'                    -- tag filtre
  AND readTime BETWEEN '...' AND '...'       -- tarih filtre
ORDER BY readTime DESC
LIMIT 1000                                   -- limit
```

### Ornek Sorgu Sablonlari

**Son deger:**
```sql
SELECT tagValue, readTime FROM noktalog.logdata
WHERE devId=X AND tagName='Y'
ORDER BY readTime DESC LIMIT 1
```

**Gunluk ortalama (son 30 gun):**
```sql
SELECT DATE(readTime) AS gun, AVG(tagValue) AS ort_deger, COUNT(*) AS okumalar
FROM noktalog.logdata
WHERE devId=X AND tagName='Y'
  AND readTime >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(readTime)
ORDER BY gun
```

**Min-max-avg istatistik:**
```sql
SELECT MIN(tagValue) min_v, MAX(tagValue) max_v, AVG(tagValue) avg_v,
       STDDEV(tagValue) std_v, COUNT(*) n
FROM noktalog.logdata
WHERE devId=X AND tagName='Y'
  AND readTime BETWEEN '...' AND '...'
```

**Donmus deger tespiti:**
```sql
SELECT DISTINCT tagValue, COUNT(*) AS sayac
FROM noktalog.logdata
WHERE devId=X AND tagName='Y'
  AND readTime >= DATE_SUB(NOW(), INTERVAL 1 DAY)
GROUP BY tagValue
ORDER BY sayac DESC LIMIT 5
-- Eger tek deger tum okumalarin %90+ ise DONMUS
```

**Ani sapma tespiti (son 24 saat vs onceki 30 gun):**
```sql
SELECT
  AVG(CASE WHEN readTime >= DATE_SUB(NOW(), INTERVAL 1 DAY) THEN tagValue END) son_24h,
  AVG(CASE WHEN readTime < DATE_SUB(NOW(), INTERVAL 1 DAY) THEN tagValue END) onceki_30g
FROM noktalog.logdata
WHERE devId=X AND tagName='Y'
  AND readTime >= DATE_SUB(NOW(), INTERVAL 30 DAY)
-- Eger son_24h / onceki_30g < 0.5 veya > 2 → anomali
```

## 5. Mevcut MCP Tool'lari ile Analiz

Olan tool'lar:
- `get_node_log_data(nodeId, tagName, start, end)` - raw log
- `get_node_log_summary(nodeId, tagName, days)` - ozet istatistik
- `get_node_log_latest_values(nodeId, tagNames)` - son degerler
- `analyze_log_trend(nodeId, tagName, days)` - trend analizi
- `analyze_seasonal_level_profile(nodeId)` - mevsimsel profil
- `compare_log_metrics(nodeId, primary, secondary)` - iki metrik karsilastirma
- `run_safe_query(sql)` - guvenli SQL (sadece SELECT)

**`run_safe_query` ile kucuk istatistikler calisabilir.** Unutma: SQL'de LIMIT ekle, tarih filtresi koy.
