---
name: user-audit
description: |
  Kullanicilarin yaptigi tag yazma islemlerinin denetim kaydi (audit log).
  log_tagyaz_user_log tablosundan kim, ne zaman, hangi tag'i, ne degere degistirmis analizi.
  Use when: "degiskenlikler neden oldu", "bu tag kim tarafindan degistirildi", "ayar degisikligi"
  gibi sorularda. Anomalilerin kullanici kaynaklı olup olmadigini kontrol etmek icin.
  Keywords: audit, kullanici, user, kim, ne zaman, degisiklik, log_tagyaz_user_log, ayar.
version: "1.0.0"
---

# Kullanici Tag Yazma Audit Log'u

Bir kullanici panelden tag yazdiginda `log_tagyaz_user_log` tablosuna kayit gider.
Bu audit log'u anomalilerin kaynagini bulmada cok kullanisli.

## Tablo Yapisi

`kbindb.log_tagyaz_user_log`:

| Kolon | Aciklama |
|-------|----------|
| `id` | Birincil anahtar |
| `uid` | Kullanici ID'si (users tablosu FK) |
| `ip` | IP adresi |
| `_session` | Session bilgisi (serialize user data) |
| `devId` | Tag'in yazildigi node ID (FK to node.id) |
| `tagName` | Yazılan tag adi (orn. `Pompa1OtoWr`, `XC_CalismaMod`) |
| `tagValue` | Yazılan deger |
| `createdTime` | Islem zamani |

## Ornek Kayit

```
INSERT INTO log_tagyaz_user_log
(id, uid, ip, _session, devId, tagName, tagValue, createdTime)
VALUES
(1206589, 280, '176.55.161.217',
 '280;58;Ömer Kılıç;Ömer;Kılıç;1;30;...;Kayseri;1;1;/panel/module/dash/',
 23215, 'Pompa1OtoWr', 1, '2026-04-22 09:00:00');
```

Bu kayit: **Kullanici 280 (Ömer Kılıç), 22 Nisan 2026 09:00'da, node 23215'in `Pompa1OtoWr` tag'ini 1'e set etmis (pompayı otomatik moda almis)**.

## Kullanim Senaryolari

### 1. "Bu tag'i kim degistirmis?"
```sql
SELECT
  l.createdTime,
  l.uid,
  u.uFirstName, u.uLastName,
  l.tagName, l.tagValue, l.ip
FROM log_tagyaz_user_log l
LEFT JOIN users u ON u.id = l.uid
WHERE l.devId = X AND l.tagName = 'Pompa1OtoWr'
ORDER BY l.createdTime DESC
LIMIT 20
```

### 2. "Son 7 gunde bu node'ta yapilan tum degisiklikler"
```sql
SELECT
  l.createdTime,
  CONCAT(u.uFirstName, ' ', u.uLastName) AS kullanici,
  l.tagName, l.tagValue
FROM log_tagyaz_user_log l
LEFT JOIN users u ON u.id = l.uid
WHERE l.devId = X
  AND l.createdTime >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY l.createdTime DESC
```

### 3. "Bu tarihte bu tag'e dokunulmus mu?"
```sql
SELECT COUNT(*) as dokunma_sayisi, MAX(createdTime) as son_yazma
FROM log_tagyaz_user_log
WHERE devId = X
  AND tagName = 'Y'
  AND createdTime BETWEEN '2026-04-01' AND '2026-04-30'
```

### 4. Anomali kaynak tespiti — "Bu sensor degeri neden ani degisti?"

Bir sensor degeri aniden sapti. Sebebini bulalim:

**Adim 1: Sapmanin oldugu zamani bul**
```sql
-- analiz skill'inden anomali tespit
```

**Adim 2: Sapma zamanindan onceki kisa bir pencerede user audit log**
```sql
SELECT l.createdTime, l.uid, u.uName, l.tagName, l.tagValue
FROM log_tagyaz_user_log l
LEFT JOIN users u ON u.id = l.uid
WHERE l.devId = X
  AND l.createdTime BETWEEN
    DATE_SUB('2026-04-20 14:30:00', INTERVAL 1 HOUR)
    AND '2026-04-20 14:30:00'
ORDER BY l.createdTime DESC
```

**Sonuc:** Eger sapmadan once `XS_BasincSensoruKalibre` degisimi varsa → kalibre yanlis girilmis.

### 5. "Kim en cok islem yapiyor?" (tercih istatistigi)
```sql
SELECT
  CONCAT(u.uFirstName, ' ', u.uLastName) AS kullanici,
  COUNT(*) AS islem_sayisi,
  MAX(l.createdTime) AS son_islem
FROM log_tagyaz_user_log l
LEFT JOIN users u ON u.id = l.uid
WHERE l.createdTime >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY l.uid
ORDER BY islem_sayisi DESC
LIMIT 10
```

### 6. Supheli IP kontrolu
```sql
SELECT ip, COUNT(DISTINCT uid) AS kullanici_sayisi, COUNT(*) AS islem_sayisi
FROM log_tagyaz_user_log
WHERE createdTime >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY ip
HAVING kullanici_sayisi > 3
-- Ayni IP'den 3+ kullanici → supheli (paylasimli oturum?)
```

## Anomali -> Audit Log Akisi

**Senaryo:** "Selafur Kuyu 4'te basinc degeri 20 Nisan'dan itibaren 8 bar yerine 15 bar gosteriyor. Neden?"

```
1. Anomaliyi dogrula (log-anomaly-detection skill'i):
   - Son 30 gun ortalama vs son 7 gun ortalama
   - Sapmanin tam baslangici = 2026-04-20 14:35

2. Audit log sorgula (bu skill):
   SELECT * FROM log_tagyaz_user_log
   WHERE devId=X
     AND createdTime BETWEEN '2026-04-20 13:00' AND '2026-04-20 15:00'
   ORDER BY createdTime

3. Sonuc bulundu:
   2026-04-20 14:30:00 | Omer Kilic | XS_BasincSensoruMax | degeri 10 → 20 yapilmis

4. Cevap:
   "Basinc sensoru maksimum degeri 20 Nisan 14:30'da Omer Kilic tarafindan
    10'dan 20'ye cikarildi. Bu yuzden olculen deger iki katina cikti.
    Muhtemelen yanlis kalibre girildi. Duzeltmek icin XS_BasincSensoruMax'i
    eski degere (10) geri alin."
```

## Kritik Tag'ler — Ozellikle Izlenmeli

Bu tag'lerin degisimleri dogrudan olcumu etkiler:
- `XS_*Max`, `XS_*Min`, `XS_*Range` - Sensor aralik limitleri
- `XS_*Kalibre`, `XS_*Offset` - Kalibrasyon
- `XE_*Alt`, `XE_*Ust`, `XE_*Eylem` - Emniyet limitleri
- `XC_CalismaMod` - Calisma modu (otomatik/elle/kapali)
- `XD_*Min`, `XD_*Max` - Depo limitleri
- `*OtoWr`, `*ElWr` - Otomatik/elle yazim istekleri

## Eger run_safe_query Yoksa

Mevcut tool'lar arasinda audit log sorgusu yoksa, direkt SQL:
```
run_safe_query(sql="
  SELECT l.createdTime, u.uName, l.tagName, l.tagValue
  FROM log_tagyaz_user_log l
  LEFT JOIN users u ON u.id = l.uid
  WHERE l.devId = 23280
    AND l.createdTime >= DATE_SUB(NOW(), INTERVAL 30 DAY)
  ORDER BY l.createdTime DESC
  LIMIT 50
")
```

Bu tool `run_safe_query` yalnizca SELECT'e izin verir, audit log okumak icin guvenli.
