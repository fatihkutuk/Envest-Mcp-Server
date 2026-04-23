---
name: hydraulic-network-analysis
description: |
  Pompa + boru + sürücü hidrolik şebeke analizi. Kullanıcı "pompa verim analizi",
  "neden bu kadar çok enerji çekiyor", "boru çapı yetersiz mi", "sürtünme ne kadar",
  "boru değiştirsek ne kazanırız", "yatırım geri döner mi" sorduğunda bu skill
  okunmalı. Darcy-Weisbach + Colebrook-White ile sürtünme, statik vs sürtünme payı
  ayrımı, boru büyütme senaryosu ve geri ödeme (payback) hesabı.
  Use when: pompa verim raporu, boru çapı sorgusu, sürtünme kaybı, yatırım analizi.
  Keywords: verim analizi, sürtünme, boru çapı, Darcy, Colebrook, Reynolds, yatırım, geri ödeme, LCC.
version: "1.0.0"
---

# Hidrolik Şebeke & Pompa Verim Analizi — Akışkanlar Mekaniği Uzman Katmanı

> **AMAÇ:** Pompa verim raporunu "katalog karşılaştırma" seviyesinden çıkarıp, **iletim borusundaki enerjiyi nereye harcadığımızı ayrıştıran** bir uzman analizine taşımak.
>
> **İlke:** `ToplamHm` tek bir sayı değildir — birkaç ayrı fiziksel bileşenin toplamıdır. Ayırmazsak yanlış öneri üretiriz (örn. sürtünme payı %4 iken "boru değiştir" önermek).

---

## 1. ToplamHm'i Bileşenlerine Ayırma

Ölçülmüş / hesaplanmış canlı denklem (korubin `calc.helper.js` ile bire bir uyumlu):

```
ToplamHm  =  (BasincSensoru × 10.197)   [= yüzey basıncı / karşı basınç, mSS]
           + SuSeviye                    [= dinamik kuyu seviyesi düşümü, m]
           + well_lift                   [= KUYU POMPASI: pompa_montaj_derinlik − statik_su_seviyesi]
           + h_sürtünme_boru              [= Darcy-Weisbach ile hesaplanır]
           + h_yerel (XV_Nsurtunme)       [= vana/dirsek/çek valf ek kayıpları, doğrudan m]
```

**Well-lift bileşeni (kuyu pompası için kritik):**
Dalgıç pompa kuyu tabanında yer alır. Pompa, üzerindeki **tüm su kolonunu** yukarı itmek zorundadır. Bu sütunun yüksekliği:

```
well_lift = max(0, nPMontaj − StatikSuSeviye)
```

`nPMontaj` = pompa montaj derinliği (yerden aşağı, m). `StatikSuSeviye` = duruşta yerden suyun üstüne kadar olan mesafe (m). Arasındaki fark = pompanın statik olarak kaldırmak zorunda olduğu su kolonu.

Örnek: Serbest Bölge Kuyu — pompa 51 m derinde, statik seviye 6 m → well_lift = 45 m. Bu tek başına `ToplamHm`'in ~%55'i olabilir; sürtünmeyle karıştırmak yanlış sonuç verir.

Bu ayrıştırma olmadan LLM'in söyleyeceği "verim düşük, pompa değiştir" önerisi yanıltıcı olur.

---

## 2. Kullanılan Tag'ler — Birim Dönüşümleri ÖNEMLİ

| Tag | DB birimi | Hesapta kullanım birimi | Dönüşüm |
|-----|-----------|-------------------------|---------|
| `XV_BoruIcCap` | mm | metre | `÷ 1000` |
| `XV_BoruUzunluk` | m | metre | `× 1` |
| `XV_PipeRoughness` | nanometre (nm) | metre | `÷ 1 000 000 000` |
| `XV_Nsurtunme` | m (mSS) | metre (doğrudan yerel kayıp) | `× 1` |
| `XV_Nmotor` | % | oran (me/100) | `× 0.01` |
| `XV_KabloKayip` | % | oran | `× 0.01` |
| `XV_SurucuKayip` | % | oran | `× 0.01` |
| `SuSicaklik` | °C | viskozite tablosundan ν | tablo interpolasyonu |
| `SuSeviye` | m | metre (dinamik kuyu) | `× 1` |
| `BasincSensoru` | bar | metre (×10.197) | `× 10.197` |

**Tipik değerler (doğrulama için):**
- `XV_PipeRoughness ≈ 100000 nm = 0.1 mm` → normal çelik boru (galvaniz/çelik ε ≈ 0.05–0.3 mm)
- `XV_BoruIcCap ≈ 100–200 mm` kuyu dalgıç için (DN100–DN200)
- `XV_Nmotor ≈ 82–94 %` (küçük motor düşük, büyük motor yüksek)
- `XV_SurucuKayip ≈ 2 %` (VFD varsa), `XV_KabloKayip ≈ 0.3–1 %`

---

## 3. Darcy-Weisbach Sürtünme Hesabı (sistemin tam formülü)

```python
# Giriş
d = XV_BoruIcCap / 1000           # m
L = XV_BoruUzunluk                 # m
ε = XV_PipeRoughness / 1e9         # m (nanometreden)
Q = Debimetre                      # m³/h
T = SuSicaklik                     # °C

# Hız
A = pi * d**2 / 4                  # m²
u = (Q / 3600) / A                 # m/s

# Kinematik viskozite ν(T) — calc.helper.js tablosu × 1e-6
ν = interpolate_nu(T) / 1e6        # m²/s

# Reynolds
Re = u * d / ν

# Darcy sürtünme katsayısı (Colebrook-White iteratif)
# 1/√λ = -2·log10( 2.51/(Re·√λ) + ε/(d·3.72) )
λ = solve_colebrook(Re, ε/d)

# Sürtünme yükü (Türkiye pratiği g = 9.7905, WELL kabulü)
h_f = λ * L * u**2 / (d * 2 * 9.7905)   # m

# Toplam sürtünme (boru + yerel)
h_friction_total = h_f + XV_Nsurtunme
```

**Akış rejimi:**
- `Re < 2300` → laminer (nadir, çok küçük debi)
- `2300 ≤ Re ≤ 4000` → geçiş (türbülans-laminer arası)
- `Re > 4000` → türbülanslı (tipik)

---

## 4. Güç Akışı ve Verim Ağacı

```
P1 (şebekeden çekilen, An_Guc)
  ↓ sürücü kaybı (XV_SurucuKayip %)
  ↓ kablo kaybı (XV_KabloKayip %)
P_motor_giriş
  ↓ motor verimi (XV_Nmotor %)
P_şaft
  ↓ pompa verimi (η_p)
P_hidrolik = ρ·g·Q·H/3600 × 10⁻³  [kW]
```

**korubin formülü (birebir):**
```
guc_eff     = An_Guc × (1 − XV_SurucuKayip/100 − XV_KabloKayip/100)
η_hidrolik  = (Hm × Q) / (367.2 × guc_eff × XV_Nmotor/100) × 100   [%]  → POMPA verimi
η_sistem    = η_hidrolik × XV_Nmotor / 100                         [%]  → TOPLAM verim
```

- `η_hidrolik` katalogdaki pompa Q-H-η eğrisinin o noktaya denk düşen değeridir
- `η_sistem` motor+pompa birleşik wire-to-water verimidir

---

## 5. Tanı Mantığı — Sürtünme Baskın mı, Statik mi?

Hesabın çıktılarını al:
```
H_statik   = (BasincSensoru × 10.197) + SuSeviye
H_friction = h_f + XV_Nsurtunme
friction_share = H_friction / ToplamHm
```

| friction_share | Yorum | Öneri |
|---|---|---|
| `< 10 %` | Statik baskın (derin kuyu veya yüksek basma hattı) | Boru değişimi **anlamsız**. Pompa seçimi odaklanılmalı. |
| `10 – 25 %` | Dengeli | Boru büyütme marjinal kazanç; yalnız enerji fiyatı çok yüksekse |
| `25 – 40 %` | Sürtünme yüksek | Boru çapı yetersiz olabilir; bir kademe büyük (DN150→DN200) senaryosu çalıştır |
| `> 40 %` | Sürtünme hakim | Ciddi sorun — boru çapı yanlış seçilmiş, acil senaryo analizi |

---

## 6. Boru Büyütme Senaryosu — Geri Ödeme

Kullanıcı "boru değiştirsek ne kazanır" dediğinde veya friction_share > %25 ise:

1. `analyze_pipe_upgrade_economics(nodeId, alternative_inner_diameter_mm=200)` çağır
2. Tool şunları döner:
   - Yeni `h_f` (aynı Q, yeni d)
   - ΔH tasarrufu
   - Yıllık kWh tasarrufu = `ΔH × Q × 9.81 / 3600 / η_toplam × saat_yıl`
   - Yıllık TL tasarrufu = kWh × fiyat (XM_T1Fiyat tarifelerinden)
   - Yatırım = L × fiyat/m × montaj_faktörü
   - Basit geri ödeme (simple payback) = yatırım / yıllık tasarruf
   - 20 yıllık NPV (iskonto oranı parametresi ile)

**Karar kuralı:**
- Geri ödeme `< 3 yıl` → **önerilir**, güçlü dil
- `3-7 yıl` → önerilebilir, faizler/enflasyonla teyit
- `> 7 yıl` → önerilmez (pompa + hat ömrü buna denk değil)
- friction_share `< 10 %` → tasarruf negatif olsa bile bile "gereksiz" diye raporla

---

## 7. LLM için Operasyonel Kural

**Pompa verim analizi istendiğinde ZORUNLU AKIŞ:**

1. `find_node_everywhere` + `get_node` → nodeId, nView
2. `prepare_pump_selection(nodeId)` → canlı Q, H, P, pompa çalışıyor mu
3. `analyze_hydraulic_network(nodeId)` → **sürtünme/statik ayrıştırması** (YENİ)
4. `get_installed_pump_info(nodeId)` → takılı pompa, annexa (gösterim için değil, iç kullanım)
5. Rapor yazarken:
   - Canlı Q, H, P, verim ver
   - **H bileşenlerini ayrı ayrı göster:** statik (kuyu + basınç), sürtünme (boru), yerel
   - friction_share yüz değer göster, %10'un altındaysa boru değişimine değinme
   - annexa sapma varsa 1 cümle ("tolerans dahilinde normal"), **yaşlanma diye yorumlama**
   - Pompa yerinde iyiyse "Mevcut pompa BEP yakın, değiştirme" de
6. Sürtünme baskınsa → `analyze_pipe_upgrade_economics` ile senaryo üret, geri ödeme + NPV sun

**YASAK:**
- XV_* tag'leri okumadan sürtünme hakkında yorum yapmak
- friction_share bakmadan boru öneri yapmak
- annexa<1 gördüğünde "pompa yaşlanmış" demek (bkz. core-rules Bölüm 5)
- Canlı güç `An_Guc` ile effektif güç (sürücü+kablo kayıpları düşülmüş) arasında karıştırmak

---

## 8. Tipik Rapor Şablonu

```
📊 Pompa Verim Raporu — {node_adı}

⚙️ İş Noktası (canlı):
  Q = {flow} m³/h, H = {Hm} m, P1 = {power} kW
  η_hidrolik = {ep}%, η_sistem = {es}% (wire-to-water)

🔬 Hidrolik Ayrıştırma:
  Statik (basınç + kuyu seviyesi):   {H_static} m   ({static_share}%)
  Boru sürtünme (Darcy-Weisbach):    {h_f} m         ({friction_share}%)
  Yerel kayıp (vana/dirsek):          {h_local} m    ({local_share}%)
  ────────────────────────────
  Toplam:                             {Hm} m

  Akış: Re={Re} ({regime}), λ={f_darcy}, v={u} m/s, ε/d={rr}

🎯 Tanı:
  {friction-based diagnosis}
  {static-based diagnosis}

💡 Öneri:
  [Eğer friction_share < %10]  Sürtünme payı düşük, boru çapı yeterli. İyileştirme önerisi yok.
  [Eğer friction_share > %25]  Sürtünme yüksek — boru çapı senaryosu analiz edilmeli (analyze_pipe_upgrade_economics).
  [Mevcut pompa BEP yakınsa]    Pompa değiştirme önerilmez; seçim zaten yerinde.

📌 Not:
  annexa={annexa} → katalog-saha sapma toleransı {annexa_pct}%. Bu normal tolerans dahilindedir.
  (SADECE sapma >%15 + trend bozulma + mekanik semptom varsa aşınma düşünülür.)
```

---

## 9. Özet

- `ToplamHm`'i **dört bileşene** ayrıştırmadan verim analizi yapma
- Sürtünme payı `friction_share` dominant değilse boru önerisi yok
- `annexa` toleranstır, yaşlanma değildir — tek başına yorum yok
- Boru değişimi önerisi **her zaman** geri ödeme ve NPV ile desteklenir
- Mevcut pompa BEP yakınsa değiştirme önerme — hata yapma

Tool'lar:
- `analyze_hydraulic_network(nodeId)` → bileşen ayrıştırması + tanı
- `analyze_pipe_upgrade_economics(nodeId, alternative_inner_diameter_mm, pipe_cost_tl_per_meter=0)` → senaryo + payback
