---
name: water-production
description: |
  Tarih araligindaki su uretimi/tuketimi hesabi. Sayaci (T_ tag'i) bulup endeks farkindan uretim
  hesaplar. Log tablolari optimize sorgulamasi.
  Use when: "bu kuyuda X tarihten Y tarihe ne kadar su uretilmis", "sayac farki", "toplam debi",
  "enerji tuketim" gibi kumulatif olculer sorulduktan.
  Keywords: uretim, tuketim, sayac, toplam, endeks, T_, fark, delta.
version: "1.0.0"
---

# Su Uretimi ve Sayaç Hesaplamalari

Sayaç tag'leri (`T_` ile baslayanlar) kumulatif toplam degerlerdir. Iki tarih arasinda uretim
hesaplamak icin **son_endeks - ilk_endeks** yeterlidir.

## Adim 1: Sayaç Tag'ini Bul

```
search_tags(deviceId=nodeId, pattern="T_*")
```

**Yaygin sayaç tag'leri:**
- `T_ToplamDebi` - Toplam gecen su (m3)
- `T_ToplamDebimetre` - Alternatif ad
- `T_ToplamDebiS` - Sunucu sayiyor (S ile biten)
- `T_Enerji` - Toplam enerji tuketimi (kWh)
- `T_CalismaSuresi` - Toplam calisma suresi (saat)

**Onemli:** `T_...S` (sunucu sayiyor) tercih edilir - cihaz resetlense bile bozulmaz.

## Adim 2: Ilk ve Son Endeks

Iki tarih arasinda:

### SQL ile (en verimli)
```sql
-- Ilk endeks (baslangic tarihindeki)
SELECT tagValue, readTime FROM noktalog.logdata
WHERE devId=X AND tagName='T_ToplamDebi'
  AND readTime >= '2026-01-01 00:00:00'
ORDER BY readTime ASC LIMIT 1

-- Son endeks (bitis tarihindeki)
SELECT tagValue, readTime FROM noktalog.logdata
WHERE devId=X AND tagName='T_ToplamDebi'
  AND readTime <= '2026-03-31 23:59:59'
ORDER BY readTime DESC LIMIT 1

-- Tek sorguda:
SELECT
  MIN(CASE WHEN rn_asc=1 THEN tagValue END) ilk_endeks,
  MIN(CASE WHEN rn_asc=1 THEN readTime END) ilk_tarih,
  MIN(CASE WHEN rn_desc=1 THEN tagValue END) son_endeks,
  MIN(CASE WHEN rn_desc=1 THEN readTime END) son_tarih
FROM (
  SELECT tagValue, readTime,
    ROW_NUMBER() OVER (ORDER BY readTime ASC) rn_asc,
    ROW_NUMBER() OVER (ORDER BY readTime DESC) rn_desc
  FROM noktalog.logdata
  WHERE devId=X AND tagName='T_ToplamDebi'
    AND readTime BETWEEN '...' AND '...'
) t
WHERE rn_asc=1 OR rn_desc=1
```

### Tool ile
```
get_node_log_data(nodeId, tagName="T_ToplamDebi",
                  start="2026-01-01", end="2026-01-01", limit=1)
→ ilk_endeks

get_node_log_data(nodeId, tagName="T_ToplamDebi",
                  start="2026-03-31", end="2026-03-31", limit=1)
→ son_endeks
```

## Adim 3: Uretim = Son - Ilk

```
uretim = son_endeks - ilk_endeks
```

**Kontrol:**
- Eger negatif → sayaç resetlenmis (adim 4'e bak)
- Eger cok buyuk (gunde 10000+ m3) → anormal
- Eger 0 → pompa calismamis veya sayaç donmus

## Adim 4: Reset Tespiti

Sayaç bir donemde resetlenmisse (cihaz degisimi, firmware guncellemesi):

```sql
-- Ardarda azalisi olan noktalar
SELECT t1.readTime, t1.tagValue as yeni, t2.tagValue as onceki
FROM noktalog.logdata t1
JOIN noktalog.logdata t2 ON t1.devId=t2.devId AND t1.tagName=t2.tagName
WHERE t1.devId=X AND t1.tagName='T_ToplamDebi'
  AND t1.readTime BETWEEN '...' AND '...'
  AND t2.readTime < t1.readTime
  AND t1.tagValue < t2.tagValue
ORDER BY t1.readTime
```

**Reset varsa:**
```
uretim = (reset_oncesi_son_endeks - baslangic_endeks) + (son_endeks - reset_sonrasi_ilk_endeks)
```

Bu karisik, en basiti:
```
Gunluk farkleri topla:
SELECT SUM(
  CASE WHEN tagValue >= prev THEN tagValue - prev ELSE tagValue END
) as toplam_uretim
FROM (
  SELECT tagValue,
    LAG(tagValue) OVER (ORDER BY readTime) AS prev
  FROM noktalog.logdata
  WHERE devId=X AND tagName='T_ToplamDebi'
    AND readTime BETWEEN '...' AND '...'
) t
WHERE prev IS NOT NULL
```

## Adim 5: Debi'den Hesaplama (Sayaç Yoksa)

Eger sayaç tag'i yoksa veya guvenilmezse, anlik debi ile integre edebilirsin:

```
uretim (m3) ≈ Σ (Debimetre_okuma × okuma_araligi_saat)
```

Ama bu yanlistir - pompa duran zamanlarda 0 alinmali.

```sql
-- Pompa calisirken debi integre
SELECT SUM(
  CASE WHEN pompa_durumu > 0
       THEN debimetre * (interval_seconds / 3600.0)
       ELSE 0 END
) as toplam_uretim_m3
FROM ...
```

## Ornek Kullanim

```
Kullanici: "Selafur Kuyu 4'te Mart ayinda ne kadar su uretilmis?"

1. find_nodes_by_keywords("selafur kuyu 4") → nodeId
2. search_tags(deviceId=nodeId, pattern="T_*") → ["T_ToplamDebi","T_Enerji"]
3. SQL ile tek sorgu:
   SELECT
     (SELECT tagValue FROM noktalog.logdata WHERE devId=X AND tagName='T_ToplamDebi'
        AND readTime >= '2026-03-01' ORDER BY readTime ASC LIMIT 1) AS ilk,
     (SELECT tagValue FROM noktalog.logdata WHERE devId=X AND tagName='T_ToplamDebi'
        AND readTime <= '2026-03-31 23:59:59' ORDER BY readTime DESC LIMIT 1) AS son

4. Sonuc: ilk=125430, son=342150
5. uretim = 342150 - 125430 = 216,720 m3
6. Kullaniciya sun: "Mart 2026'da Selafur Kuyu 4'te toplam 216,720 m3 su uretilmistir."
```

## Enerji Tuketimi (Benzer Mantik)

```
T_Enerji (kWh) veya T_ToplamEnerji tag'i varsa ayni formul:
enerji_tuketim = son_endeks - ilk_endeks  [kWh]

Eger yoksa:
enerji ≈ Σ (An_Guc_okuma × okuma_araligi_saat)  [kWh]
```
