---
name: pump-frequency-projection
description: |
  Bir pompanın farklı frekansta ne Q/H/P vereceğini doğru hesaplamak.
  Affinity Laws naif uygulamak YANLIŞTIR — sistem direnci göz ardı edilmiş olur.
  ToplamHm canlı ölçüm = sistem + pompa iş noktası. Projeksiyon: mevcut noktadan başla.
  Use when: kullanıcı "bu pompayı X Hz'de çalıştırsam ne olur", "en verimli frekans nedir",
  "frekans düşürürsem debi ne olur" gibi sorular sorduğunda.
  Keywords: frekans, Hz, vfd, surucu, affinity, calisma noktasi, annex a, sistem direnci.
version: "1.0.0"
---

# Pompa Frekans Projeksiyonu — Doğru Yöntem

## Neden Basit Affinity Laws Yanlış?

Grundfos affinity yasaları (sabit sistem için):
```
Q2 = Q1 × (f2/f1)
H2 = H1 × (f2/f1)²
P2 = P1 × (f2/f1)³
```

**TUZAK:** Bu formüller sadece **pompa** için geçerli. Sistem direnci (boru, vana, yükseklik farkı) hesaba katılmamış olur.

### ToplamHm Zaten Sistem Direncini İçeriyor

`ToplamHm` canlı SCADA tag'i = pompanın **şu anki iş noktasında** gerçekten verdiği H. Bu değer:
- Dinamik kuyu seviyesi
- Boru sürtünme kaybı (tüm bağlantılar dahil)
- Yükseklik farkı (statik H)
- Depo/sisteme bağlı karşı basınç

hepsini içeriyor. Yani `ToplamHm = sistem_H` (sistem eğrisi üzerindeki gerçek nokta).

### Pompa ve Sistem Eğrisi Kesişimi

Her pompa bir Q-H eğrisi, her sistem bir direnç eğrisi sunar. **İş noktası = bu iki eğrinin kesişimi.** Frekans değiştiğinde:
- Pompa eğrisi **yukarı/aşağı** kayar (yeni Q-H eğrisi)
- Sistem eğrisi **aynı** kalır (boru/vana değişmedi)
- Yeni iş noktası = yeni pompa eğrisi ∩ mevcut sistem eğrisi

Bu kesişim Affinity Laws ile değil, **hem pompa hem sistem modeliyle** bulunur.

## Doğru Projeksiyon Adımları

### 1. Mevcut Noktayı Belirle (Canlı ölçüm)
```
prepare_pump_selection(nodeId) → canlı ölçümler
- Q1 = Debimetre (m3/h)
- H1 = ToplamHm (m) ← sistem + pompa iş noktası
- P1_actual = An_Guc (kW)
- η_actual = YaklasikHidrolikVerim (%)
- f1 = P1_Frekans veya PompaFrekans (Hz) — varsa canlı, yoksa 50 Hz varsay
```

### 2. Sistem Eğrisini Modelle
Sistem eğrisi: `H_sys(Q) = H_static + k × Q²`

`H_static` = kuyu dinamik seviyesi + yükseklik farkı (statik bileşen)
`k` = tüm dinamik kayıpların birleşik katsayısı

**Kalibrasyon:** Tek ölçüm noktasından `k` çıkar:
```
H1 = H_static + k × Q1²
→ k = (H1 - H_static) / Q1²
```

`H_static` bilinmiyorsa: birkaç frekansta log'dan (Q, H) çifti al → regresyonla `H_static` + `k`.

Yaklaşım yöntemi: `H_static ≈ XD_BasmaYukseklik` (ayar) veya `SuSeviye_dinamik` (canlı kuyu seviyesi). Yoksa `H_static ≈ 0.3 × H1` ile başlanabilir (yaygın çalışma aralığında statik payı %20-40).

### 3. Pompa Eğrisini Modelle
Katalogdan (nodepar `np_*` veya KoruCAPS DB):
```
H_pump(Q, f) = a(f)·Q² + b(f)·Q + c(f)
```
Frekans ölçeklemesi Affinity ile: pompa eğrisi katsayıları `f²` ile çarpılır.

Tam katalog yoksa **3 nokta (Q, H)** çifti yeterli — Q-H polinomu fit edilir.

### 4. Yeni Frekansta Kesişim
```
H_pump(Q, f2) = H_sys(Q)
```
Bu denklemin kökü → (Q2, H2) yeni iş noktası.

### 5. Yeni Güç & Verim
```
P_hidrolik_2 = (Q2 × H2) / 367
η2 ≈ pompa kataloğundan veya interpolasyonla
P1_2 = P_hidrolik_2 / η2
```

## Yanlış vs Doğru Örneği

**Senaryo:** Mevcut: 42 Hz, Q1=175 m³/h, H1=49.66 m, P1=42.5 kW, η=%70

**YANLIS (naif Affinity):**
```
40 Hz'e düşersek:
Q2 = 175 × (40/42) = 166.6 m³/h
H2 = 49.66 × (40/42)² = 45.0 m
"176 m³/h debi devam eder"  ← YANLIŞ! Sistem eğrisi göz ardı edildi
```

**DOGRU:**
1. Sistem eğrisi kalibrasyonu: diyelim `H_static = 15 m`, `k = (49.66-15)/175² = 1.13e-3`
2. 40 Hz'de pompa eğrisi yukarıdan aşağı kayar, yeni eğri sistem eğrisini daha küçük Q'da keser
3. Yeni nokta: Q2 ≈ 148-155 m³/h, H2 ≈ 40-42 m (sistem eğrisi üzerinde)
4. Kullanıcının gözlemiyle uyuşur: "40 Hz'de debi 150'ye düştü" ✓

## Operational Rule (LLM için)

**Frekans projeksiyonu sorulduğunda:**

1. `prepare_pump_selection(nodeId)` çağır → canlı Q, H, P, η al
2. `An_Guc` + formül (P_hid = Q×H/367) → çalışma noktasının tutarlılığını doğrula
3. Sistem eğrisi için ya:
   - Önceki log'lardan (f, Q, H) çiftleri ile kalibrasyon, veya
   - Statik tahminle yaklaşık model
4. Affinity ile **pompa** eğrisini f2'ye ölçekle
5. Sistem ∩ yeni pompa eğrisi kesişimi = yeni (Q2, H2)
6. Kullanıcıya verirken **belirsizliği** açıkça söyle:
   - "Sistem statik komponenti tam bilinmiyorsa tahmin ±%10-15"
   - "Gerçek değer log'larla doğrulanmalı"

**YASAK:** Pompa katalog Q-H değerlerini sabit bir çalışma noktası gibi sunmak. Her Q için bir H vardır, ama gerçekte **sistem eğrisi** hangi Q'ya düşeceğini belirler.

## Katalog Verisi Nereden Alınır

KoruCAPS'te:
```
korucaps_get_pump_specs(pump_name="SP 215-3")
→ q_h_curve (nominal 50 Hz), np_* parametreleri, BEP
```

SCADA instance'ında (node'un kataloglu pompası varsa):
```
get_node(nodeId) → parametreler listesi içinde np_PompaDebi, np_PompaHm, np_PompaGuc,
                   np_PompaVerim (nominal/etiket değerleri)
```

Bunlar **nominal** (etiket) değerlerdir — gerçek iş noktası yaygınca farklıdır.

## Özet

- **ToplamHm = gerçek iş noktası H**, pompa eğrisinin o Q'daki H'i DEĞİL
- **Frekans değişince** yeni nokta = yeni pompa eğrisi ∩ sistem eğrisi
- **Affinity Laws** sadece pompa tarafı için geçerli, sistem direnci ayrıca modellenmelidir
- Katalog/etiket verimi canlı verimle tutmayabilir — **canlı ölçüm birincil**
- Projeksiyonun belirsizliği kullanıcıya açıkça söylenmeli
