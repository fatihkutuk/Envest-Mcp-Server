---
name: leak-detection
description: |
  Hat/boru patlağı ve kaçak tespiti — log verisi üzerinden akıllı analiz.
  Pompa durduğunda hat basıncı logu incelenir: basınç düşüp bir seviyede sabitleniyorsa
  orası kaçak/patlak noktasıdır (basınç dengelenmesi). Ayrıca:
  kuyu_çıkış vs hat basınç farkı → çekvalf/borulama tanısı,
  debi-basınç uyumsuzluğu → sızıntı tespiti, gece debisi → kaçak oranı.
  Use when: "hatta patlak var mı", "basınç düşüyor", "kaçak nerede", "çekvalf sorunlu mu",
  "boru tıkanıklığı", "şebeke analizi", "su kaybı", "sızıntı".
  Keywords: patlak, kaçak, sızıntı, hat basıncı, çekvalf, cekvalf, HatBasincSensoru,
  BasincSensoru2, gece debisi, şebeke, boru, NRW, DMA kaçak.
version: "1.0.0"
---

# Hat Patlağı & Kaçak Tespiti — Akıllı Şebeke Analizi

## 1. Temel Prensip — Basınç Dengelenmesi

**Pompa durduğunda** hat basıncı **statik denge noktasına** gelir:
- Tam kapalı sistem → pompa seviyesi + yükseklik farkı = basınç sabit
- **Kaçak/patlak var** → basınç kaçak noktasının **seviyesine** düşer ve orada **sabitlenir**

### Nasıl tespit edilir?

1. Pompa durma anından 10-30 dk sonra `HatBasincSensoru` log'u al
2. Basınç eğrisi:
   - **Sağlam hat:** basınç çok yavaş düşer veya sabit
   - **Patlak/kaçak:** basınç hızla düşer, bir değerde **sabitlenir** (plateau)
3. Plateau seviyesi → kaçak noktasının kotunu verir:
   ```
   Kaçak kotu ≈ Pompa kotu + Plateau_basinc_m - Pompa_çıkış_kotu_farki
   ```

### Log sorgusu (SQL)

```sql
-- Pompanın durduğu son ani bul
SELECT logTime FROM noktalog.log_{nid} l
JOIN kbindb.logparameters lp ON l.logPId=lp.id
WHERE lp.tagPath IN ('Pompa1StartStopDurumu','PompaCalismaDurumu')
  AND l.tagValue < 0.5
  AND l.logTime >= NOW() - INTERVAL 48 HOUR
ORDER BY l.logTime DESC
LIMIT 1;

-- Durmadan sonraki 30 dk hat basinci
SELECT l.logTime, l.tagValue
FROM noktalog.log_{nid} l
JOIN kbindb.logparameters lp ON l.logPId=lp.id
WHERE lp.tagPath IN ('HatBasincSensoru','BasincSensoru2')
  AND l.logTime BETWEEN <durma_ani> AND DATE_ADD(<durma_ani>, INTERVAL 30 MINUTE)
ORDER BY l.logTime ASC;
```

**MCP tool:**
```
<prefix>_get_node_log_data(nodeId=X, startDate='YYYY-MM-DD HH:MM', endDate='...',
                           logParamIds='<HatBasincSensoru_id>')
```

### Yorum

| Basınç Profili (pompa durdu → 30 dk) | Tanı |
|--------------------------------------|------|
| %<5 düşüş, kayda değer değişim yok | ✅ Sağlam hat |
| Yavaş doğrusal düşüş (dk 20'de %10-30 kayıp) | ⚠️ Küçük sızıntı / vana seal'i |
| Hızlı başlangıç düşüşü, sonra **plateau** | 🚨 Patlak/kaçak, plateau kotu kaçak noktası |
| Sürekli serbest düşüş, sıfıra kadar | 🚨 Büyük patlak (hat tamamen atmosferik) |

---

## 2. BasincSensoru vs HatBasincSensoru Farkı → Çekvalf/Borulama Tanısı

Bu iki tag farklı ölçümler:
- **`BasincSensoru`** (kuyu nView'larında): **pompa çıkış** basıncı (pompa-boru aralığı, çekvalfin BUKAK tarafı)
- **`HatBasincSensoru`** veya **`BasincSensoru2`**: **hat/şebeke** basıncı (çekvalfin SONRASI, hat tarafı)

Normal durumda `BasincSensoru > HatBasincSensoru` (çekvalf + vana + boru kaybı kadar fark).

### Fark tanı tablosu

| Fark (bar) | Durum | Olası Sebep |
|------------|-------|-------------|
| **< -0.2** | ❌ Ölçüm hatası | Sensör kalibrasyon hatası, etiketler ters takılmış, veri hattı bozuk |
| **-0.2 … 0.3** | ⚠️ Çok yakın sıfır | Çekvalf sızdırıyor olabilir (geri akış), sensör uzaklığı düşük |
| **0.3 … 1.5** | ✅ Normal | Vana + boru + çekvalf direnci |
| **> 1.5** | 🚨 Aşırı direnç | Çekvalf yarım kapalı, vana kısılmış, manifold tıkanmış, çekvalf klapası yapışmış |

### Diagnose formülü

```
H_direnç (m) = (BasincSensoru − HatBasincSensoru) × 10.197
Q = Debimetre (canlı)
→ Sürtünme k = H_direnç / Q²
```

Bu k katsayısı zaman içinde:
- **Artıyorsa** → tıkanma/çökelme birikiyor
- **Sabit** → normal
- **Azalıyorsa** → çekvalf aşınıyor (sızdırma artıyor)

---

## 3. Gece Debisi Analizi (DMA / Zone Kaçak Oranı)

Gece saatlerinde (02:00-05:00) kullanım minimum. Bu saatteki debi ≈ **hattaki kaçak**.

### SQL
```sql
SELECT HOUR(logTime) AS saat, AVG(tagValue) AS avg_debi, COUNT(*) AS n
FROM noktalog.log_{nid} l
JOIN kbindb.logparameters lp ON l.logPId=lp.id
WHERE lp.tagPath='Debimetre'
  AND HOUR(logTime) BETWEEN 2 AND 5
  AND logTime >= NOW() - INTERVAL 30 DAY
GROUP BY HOUR(logTime);
```

### Yorum
- Gece debisi **gündüz ortalamasının >%10-15'i** → kaçak büyük
- Gece debisi **sürekli yüksek** → sistematik kayıp (birden fazla kaçak noktası)
- Gece debisinde **ani artış** → son bir patlak oluşmuş

---

## 4. Debi-Basınç Uyumsuzluğu

Normal hat için: `basinc × debi ≈ sabit` (belirli çalışma noktasında).

- **Basınç düşüyor ama debi artıyor** → pompa güç harcaması aynı, ama su başka yere gidiyor → kaçak
- **Debi sabit, güç artıyor** → pompa aşınıyor veya hat tıkanması
- **Basınç ani düştü, debi ani arttı** → patlak

---

## 5. Adım-Adım Analiz Akışı

Kullanıcı "hatta patlak var mı" veya benzer sorduğunda:

1. **Canlı durum:** `prepare_pump_selection(nodeId)` → `pompa_cikis_vs_hat_basinc` alanı otomatik gelir. `durum` field'ına bak: `cekvalf_veya_borulama_sorunu` / `olcum_hatasi` / `cok_yakin_sifir` / `normal`.
2. **Pompa durdu mu?** Durduysa son 30 dk `HatBasincSensoru` log'unu al:
   ```
   <prefix>_get_node_log_data(nodeId, startDate='<durma-30dk>', endDate='<durma+30dk>',
                              logParamIds='<HatBasincSensoru_id>')
   ```
3. **Basınç profili:** plateau var mı → plateau seviyesi kaçak kotunu verir
4. **Gece debisi:** `analyze_log_trend` veya `run_safe_query` ile saat 02-05 debi ortalaması
5. **Kuyu-depo yükseklik dengesi:**
   - Beklenen statik H = XD_BasmaYukseklik + (StatikSeviye - dinamik_seviye)
   - Log'daki gerçek pompa-durma H'i ile karşılaştır, sistematik fark varsa sensör kalibrasyon sorunu

## 6. Tag Referansı

| Tag | Ne Ölçer | Birim |
|-----|----------|-------|
| `BasincSensoru` (kuyu) | Pompa çıkış basıncı (çekvalf ÖNCESİ) | bar |
| `BasincSensoru2`, `HatBasincSensoru` | Hat / şebeke basıncı (çekvalf SONRASI) | bar |
| `GirisBasinc` | Sisteme giriş basıncı (DMA'da) | bar |
| `XD_BasmaYukseklik` | Kuyu-depo kot farkı (statik H) | m |
| `XD_CikisDepoYukseklik` | Çıkış deposu yüksekliği | m |
| `StatikSeviye`, `SuSeviye`, `DinamikSeviye` | Kuyu su seviyesi | m |
| `kuyukot`, `depokot` | Deniz seviyesinden kot | m |

## 7. Kritik — "BasincSensoru kullanıyorum, doğru değer mi?"

**Kural:** Hat basıncı analizi veya kaçak tespiti için **HİÇBİR ZAMAN sadece `BasincSensoru`** kullanma — o pompa çıkışıdır. Her zaman `HatBasincSensoru` veya `BasincSensoru2` tercih et. Yoksa iki sensörü birlikte analiz et (fark = çekvalf tanısı).

ToplamHm hesabı için de hat basıncı doğrudur (şebekeye basılan H, pompa çıkışı değil).
