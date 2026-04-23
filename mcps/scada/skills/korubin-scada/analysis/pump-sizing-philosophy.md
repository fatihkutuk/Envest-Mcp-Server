---
name: pump-sizing-philosophy
description: |
  Pompa seçimi / değişim önerisi için RİSK-ODAKLI karar felsefesi.
  Enerji verimi TEK kriter DEĞİLDİR — işletme zarfı (H/Q aralığı), kademe sayısı buffer'ı,
  VFD frekans esnekliği, duty point varyasyonu hepsi hesaba katılmalıdır.
  Mevcut pompa ZATEN çalışıyorsa → değiştirme için güçlü 3 kanıt lazım.
  Use when: pompa seçimi, pompa değişimi önerisi, alternatif pompa karşılaştırması,
  "daha verimli pompa var mı", "sürücülü esnek çözüm", "kademeli dönüşüm" soruları.
  Keywords: pompa seçimi, kademe, buffer, esneklik, isletme zarfi, robust, BEP, duty,
  VFD, frekans esnekligi, alternatif.
version: "1.0.0"
---

# Pompa Seçim Felsefesi — Enerji DEĞİL, Risk-Odaklı

## 1. Temel İlke: Robustness > Anlık Enerji

SCADA sistemlerinde pompa seçimi **tek bir duty point**'e göre yapılmaz. Gerçek tesiste:

- Kuyu **dinamik seviyesi** mevsimsel ve kullanım yoğunluğuna göre değişir (±5-15 m)
- Boru **sürtünmesi** yıllar içinde artar (mineral birikim, biyofilm)
- Hedef depo **seviyesi** farklı H gerektirir
- Debi ihtiyacı **kullanım** ile değişir (yaz/kış, sabah/akşam)

Bu nedenle pompa, sabit bir (Q, H) noktası değil **bir işletme zarfı** için seçilir:
```
Q_min ≤ Q ≤ Q_max
H_min ≤ H ≤ H_max
```

## 2. Kademe Sayısı = H Buffer'ı

Aynı seri pompada kademe sayısı H'ı belirler:

| Pompa | Kademe | Nominal H | Shut-off H (max) |
|-------|--------|-----------|------------------|
| SP 215-2 | 2 | ~50 m | ~55 m |
| SP 215-3 | 3 | ~73 m | ~85 m |
| SP 215-4 | 4 | ~97 m | ~110 m |

**Kritik fark:**
- 2 kademeli pompa → **max H sınırlı** (~55 m)
- 3 kademeli pompa → H'ı VFD ile istenen noktaya *düşürebilirsin*, ama gerektiğinde *yukarı* çıkabilirsin

### Örnek Senaryo (Serbest Bölge Kuyu)

Duty: Q=176 m³/h, H=49.7 m

**Seçenek A: SP 215-3 (mevcut)** + VFD @ 42 Hz
- Normal çalışma: Q=176, H=49.7, verim ~70%
- Kuyu seviyesi düşerse (H=60 gerek) → frekans 45 Hz'e çıkar → Q=180, H=60 → hala verimli
- **Güvende.** Dinamik koşullara dayanır.

**Seçenek B: SP 215-2** @ 50 Hz
- Normal çalışma: Q=219, H=50, verim ~82% (kağıt üzerinde harika)
- Kuyu seviyesi düşerse (H=60 gerek) → **pompa H=60 veremez** (max ~55 m)
- Sistem çöker, pompa cavitation riski, motor yüklenir.
- **Kırılgan.** Tek bir koşul değişiminde iflas eder.

Enerji farkı (A→B): ~2-3 puan verim. Risk farkı: **sonsuz** (B çöker).

## 3. Karar Kuralları — Risk Tabloları

### Mevcut Pompa Tutulur (DEĞİŞİM ÖNERMEME)

Tüm şu koşullar sağlanıyorsa:
- Duty Q, nominal Q'nun %60-120'si aralığında
- Pompa VFD ile çalışma bandında kalıyor (30-50 Hz ideal)
- Mevcut verim ≥ %60 (kabul edilebilir)
- Kuyu/sistem H aralığı pompanın VFD ile erişebildiği bölgede

→ **Mevcut pompa en doğru seçim.** Tek öneri: VFD frekans ince ayarı, bakım.

### Aynı Seride Az Kademeli (DİKKATLİ ÖNER)

Duty point dar aralıkta (H sabite çok yakın) VE:
- Duty H << pompa max H'ı (pompa sürekli VFD ile çok kısılmış, %30-40 altı verimde)
- Tesis H aralığı dar (kuyu seviyesi stabil, boru durumu iyi)

→ Az kademeli **aynı seri** öner (SP 215-3 → SP 215-2).
→ **UYARI şart:** "H ihtiyacı 55 m'yi aşarsa bu pompa yetmez"
→ Kullanıcıya **seçim** sun, dayatma.

### Farklı Seri (ANCAK GERÇEKTEN UYGUNSA)

Duty point mevcut pompanın çalışma bandının dışındaysa:
- Q << nominal Q'nun %60'ı → pompa aşırı büyük, debi yetersiz
- Q >> nominal Q'nun %120'si → pompa küçük, yetersiz
- Veya teknik gereksinim değişmişse (basınç zonu, derinlik)

→ Uygun seri + kademe sayısı önerilir.
→ Alternatifler karşılaştırılır, karar kullanıcıya bırakılır.

## 4. VFD Frekans Esneklik Matrisi

Aynı pompa için farklı frekanslarda performans (affinity yasaları + %5 şebeke verim kaybı):

| Frekans | Q | H | Toplam Verim |
|---------|---|---|--------------|
| 50 Hz | Q_nom | H_nom | %100 (referans) |
| 45 Hz | 0.90 × Q_nom | 0.81 × H_nom | %98 |
| 40 Hz | 0.80 × Q_nom | 0.64 × H_nom | %94 |
| 35 Hz | 0.70 × Q_nom | 0.49 × H_nom | %88 |
| 30 Hz | 0.60 × Q_nom | 0.36 × H_nom | **%80** ⚠️ |
| < 30 Hz | ... | ... | Motor soğutma yetersiz, **KULLANMA** |

**Sonuç:** VFD ile frekans düşürmek verimi çok az etkiler (50→40 Hz: sadece %6 düşüş). Ama kademe sayısı yetersizse **hiçbir frekans seni kurtaramaz**.

## 5. Kullanıcıya Sunuş Yapısı

Pompa seçimi sorulduğunda **her zaman** şu yapıda cevap ver:

```
## Mevcut Durum
- Takılı pompa: <marka> <model>
- Duty noktası: Q, H, verim
- Değerlendirme: <uygun / bantta / uygunsuz>

## Seçenek A — Mevcut Pompayı Koru (ÖNERİLEN varsayılan)
- Avantaj: Kanıtlanmış işletme, H buffer'ı (kademe avantajı)
- İyileştirme: VFD ince ayar (X → Y Hz), mevcut verim A'dan B'ye çıkar
- Risk: Düşük

## Seçenek B — Aynı Seri Az Kademeli (<model2>)
- Avantaj: BEP'e tam oturma, %X verim artışı
- Risk: Max H sınırlı (~N m). H ihtiyacı aşarsa sistem başarısız olur.
- UYARI: Tesis H aralığı GEÇMİŞTEKİ log'larla doğrulanmalı

## Seçenek C — Farklı Seri (sadece duty gerçekten uyuyorsa)
- Gerekçe, avantaj, dezavantaj

## Öneri
[Risk-tolerans ve maliyet denklemi]:
- Konservatif/kritik tesis: A (mevcudu koru + VFD opt)
- Enerji agresif ve koşullar stabil: B (aynı seri az kademe)
- Teknik değişim zorunlu: C
```

## 6. Yasaklar

- Enerji sırasında **ilk modeli** dogmatik şekilde dayatmak
- Mevcut pompa doğru boyuttaysa "değiştir" demek
- Kademe azaltma önerirken H riski uyarısını atlamak
- VFD frekans esnekliğini küçümsemek ("4 Hz düşüşle verim kaybı ihmal edilir")
- Aynı seri varken farklı seri önerisi (SP 215 yerine SP 160 gibi)

## 7. Özet Kuralı

> **Risk = Belirsizlik × Etki.**  
> Pompa değişimi yüksek maliyetli bir karardır. Enerji tasarrufu 5 yılda geri öder ama kırılgan bir pompa seçimi **ilk zor koşulda** tüm sistemi çökertir.  
> Varsayılan: *mevcut pompanın optimizasyonu*.  
> Değiştirme önerisi ancak **gerçek veriye dayanan üç kanıt** ile sunulur.
