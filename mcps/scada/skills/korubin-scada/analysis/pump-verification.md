---
name: pump-verification
description: |
  Pompa secimi oncesi veri dogrulama ve pompa calisiyor mu kontrolu.
  Use when: pompa seciminden once verileri dogrulamak, pompa durumu kontrol etmek,
  veya eksik veriyi hesaplamakla (debi/Hm/guc birinden digerini tahmin) gerektiginde.
  Keywords: pompa, dogrulama, verify, cross-check, Hm, debi, guc, formul, tahmin.
version: "1.0.0"
---

# Pompa Seciminde Veri Dogrulama

Pompa secimi yaparken **yanlis veri ile yanlis pompa** secmemek icin agir kontroller gereklidir.

## Kural 1: Debi Birimi Her Zaman m3/h Varsayilir

**Varsayilan:** Tag adinda aksi belirtilmedikce debi = m3/h
- `Debimetre=160` → 160 m3/h (lt/sn DEGIL!)
- `DebimetreLtSn=44` → 44 lt/sn = 158.4 m3/h (x3.6 ile cevir)

**Cevirme kontrol:** Eger debi gercekten lt/sn ise ve `DebimetreLtSn` degil `Debimetre` tag'i ise → tag isminde `LtSn`, `Ltsn`, `LT_SN`, `Qltsn` gibi bir sey YOK. O zaman m3/h.

## Kural 2: Pompa Calisiyor mu Kontrolu

**Pompa durmussa, Hm ve debi YANLISTIR:**
- Hm: pompa dururken genelde 0 veya statik basinc (uretim basinci degil)
- Debi: pompa dururken 0

**Pompa durumu tag'leri (ekran tipine gore):**
| Ekran Tipi | Durum Tag'i |
|-----------|-------------|
| `a-aqua-cnt-kuyu-v2` | `Pompa1StartStopDurumu` |
| `a-aqua-cnt-kuyu-tank` | `Pompa1StartStopDurumu` |
| `a-kuyu-envest` / `-v2` | `P1_Durum` veya `PompaStartStopDurumu` |
| `a-terfi-*` | `P1_Durum`, `P2_Durum`, ..., `PompaCalismaDurumu` |
| Genel fallback | `PompaCalismaDurumu`, `Pompa1Calisiyor` |

**Is akisi:**
```
1. get_node(nodeId) → nView ogren
2. get_device_tag_values(deviceId=nodeId, tagNames=["Pompa1StartStopDurumu", "P1_Durum", "PompaCalismaDurumu"])
3. En az biri 1 donerse → pompa calisiyor, canli Hm/Debi kullanilabilir
4. Hepsi 0 veya bulunamadi → pompa DURUYOR, canli degerler yanlis
```

## Kural 3: Pompa Duruyorsa Loglardan Dogrula

Eger pompa su an duruyorsa, son calisma donemindeki loglardan gercek Hm ve debi'yi al:

```
1. Son 7 gunluk log al: get_node_log_data(nodeId, tagName="Pompa1StartStopDurumu", days=7)
2. Pompa=1 oldugu periodu bul
3. O periodda: get_node_log_data(nodeId, tagName="ToplamHm", start=..., end=...)
4. O periodda: get_node_log_data(nodeId, tagName="Debimetre", start=..., end=...)
5. Ortalama (veya medyan) al → gercek calisma degerleri
```

## Kural 4: Degerleri Yuvarlama

Pompa seciminde degerler AYNEN kullanilmali:
- `ToplamHm=131.45` → `head_m=131.45` (131 DEGIL)
- `Debimetre=157.82` → `flow_m3h=157.82` (160 DEGIL)
- Yuvarlama sadece kullaniciya gosterirken yapilir

## Kural 5: Cross-Check — Formullerle Dogrulama

Ikisinden digerini tahmin et, tutarlilik kontrolu yap.

### Hidrolik Guc Formulu
```
Ph (hidrolik) = ρ × g × Q × H / 3600  [Watt]
  ρ = 998.2 kg/m³ (su yogunlugu)
  g = 9.80665 m/s²
  Q = debi m3/h
  H = basma yuksekligi metre

P2 (saft) = Ph / eta_pompa  [Watt]
P1 (sebeke) = P2 / eta_motor  [Watt]
```

**Pratik formul (kW cinsinden):**
```
P_hidrolik_kW = (Q_m3h × H_m) / 367

Eger pompa verimi ~%70 → P2 = P_hidrolik / 0.70
Eger motor verimi ~%92 → P1 = P2 / 0.92

Sonuc: P1 ≈ (Q × H) / 367 / 0.70 / 0.92 ≈ (Q × H) / 236
```

### Dogrulama Ornekleri

**Ornek 1: Debi ve Hm var, guc yok**
```
Q = 160 m3/h, H = 130 m
Tahmini P1 = 160 × 130 / 236 = 88 kW

Eger olculen An_Guc = 85-95 kW arasi → TUTARLI
Eger olculen An_Guc = 150 kW → TUTARSIZ (H veya Q yanlis olabilir)
Eger olculen An_Guc = 30 kW → TUTARSIZ (pompa arizali veya degerler yanlis)
```

**Ornek 2: Hm ve guc var, debi yok**
```
H = 130 m, P1 = 90 kW
Tahmini Q = 90 × 236 / 130 = 163 m3/h

Eger olculen Debimetre = 160 m3/h → TUTARLI (2% fark normal)
Eger olculen Debimetre = 44 m3/h → TUTARSIZ! Tag muhtemelen Lt/sn, 44*3.6=158 m3/h uygun
```

**Ornek 3: Debi ve guc var, Hm yok**
```
Q = 160 m3/h, P1 = 90 kW
Tahmini H = 90 × 236 / 160 = 133 m

Eger olculen ToplamHm = 130 m → TUTARLI
```

### Tutarsizlik Varsa Ne Yap

Tutarsizlik tespit edildiginde:
1. Kullaniciya bildir: "Olculen Q=160 m3/h ve H=130m ile beklenen guc ~88kW, ama An_Guc=150kW. Degerlerden biri yanlis olabilir."
2. Loglardan kontrol et (pompa gercekten calistigi anlari)
3. Sensorlerin saglik durumuna bak (sensor-analysis skill'i)
4. Kullaniciya sor: "Hangi degere guveniyorsunuz?"

## Kural 6: Eksik Degeri Tahmin

Kullanici tek veri verdiyse, diger iki degeri tahmin edip pompa ara:

**Kullanici: "Bu pompa 90kW cekiyorsa ne kadar basiyor olabilir?"**
- Pompa seri (SP/CR?) bildiyse → pompa curve'unden tahmin
- Hm ~130m varsayilabilir (tipik kuyu)
- Q = 90 × 236 / 130 = 163 m3/h

**Kullanici: "Kuyu 100m, pompa kaliteli olmali ne onerirsin?"**
- Debi ve guc yok
- Ortalama kuyu: 100-200 m3/h arasi
- Kullaniciya sor: "Mevcut debi bilgisi var mi? Ya da beklenen debi?"

## Ornek Tam Is Akisi

```
Kullanici: "Selafur Kuyu 4 icin pompa sec"

1. find_nodes_by_keywords("selafur kuyu 4") → nodeId
2. get_node(nodeId) → nView=a-aqua-cnt-kuyu-v2 ogren
3. get_device_tag_values(deviceId=nodeId, tagNames=[
     "Pompa1StartStopDurumu", "Debimetre", "ToplamHm", "An_Guc", "BasincSensoru"
   ])
4. Pompa1StartStopDurumu=1 → CALISIYOR, canli degerler saglikli

5. Degerleri al:
   Debimetre=160 (m3/h — lt/sn gecmiyor tag isminde)
   ToplamHm=131.45
   An_Guc=88

6. Cross-check:
   Beklenen P1 = 160 × 131.45 / 236 = 89 kW
   Olculen 88 kW → TUTARLI (%1 fark, normal)

7. search_pumps(
     flow_m3h=160, head_m=131.45,
     application="groundwater", sub_application="WELLINS"
   )

8. Sonucu kullaniciya sun, mevcut pompa ile karsilastir
```

## Pompa Duruyorsa Alternatif Akis

```
1-4 aynı

5. Pompa1StartStopDurumu=0 → DURUYOR

6. Son calisma donemini bul:
   get_node_log_data(nodeId, tagName="Pompa1StartStopDurumu",
                      days=7, min_value=0.5)
   → Son calistigi tarih araligi

7. O araliktan gercek degerleri al:
   get_node_log_data(nodeId, tagName="ToplamHm",
                      start=..., end=...) → ortalama veya medyan
   get_node_log_data(nodeId, tagName="Debimetre",
                      start=..., end=...) → ortalama veya medyan

8. Bu degerleri kullanarak 5-8 adimlarini isle

9. Kullaniciya bildir: "Pompa su an duruyor, son calisma donemi (X-Y tarihleri)
   ortalamalari kullanildi: Q=158 m3/h, H=130m"
```
