---
name: device-pump
description: |
  Pompa izleme, verimlilik hesaplama ve performans analizi.
  Use when: pompa verimi, Hm, debi-guc iliskisi, pompa performansi soruldugunda.
  Keywords: pompa, pump, verim, efficiency, Hm, basma yuksekligi, performans.
version: "1.0.0"
---

# Pompa Izleme ve Verimlilik

## Pompa Snapshot Degerleri

Bir pompa noktasindan okunan temel degerler:

| Parametre | Tag Adaylari | Birim | Aciklama |
|-----------|-------------|-------|----------|
| Debi (flow_m3h) | Debimetre, T_Debi, Debimetre1, GirisToplamDebi, CikisAnlikDebi, DebiM3h, Qm3h | m3/h | Anlik akis hizi |
| Debi (Lt/sn) | T_DebiLtSn, DebimetreLtSn, LtSn, DebiLtSn, AnlikDebiLtSn, QltSn, LitreSn | Lt/sn | x3.6 = m3/h |
| Basinc | BasincSensoru, T_Basinc, CikisBasincSensoru, GirisBasincSensoru | bar | Pompa cikis basinci |
| Guc | An_Guc, T_Guc | kW | Motor aktif gucu |
| Frekans | An_SebFrekans, T_Frekans, Frekans | Hz | Sebeke/motor frekansi |
| Basma yuksekligi | ToplamHm, TotalHm, PompaHm, BasmaYuksekligi, GercekHm, Hm | metre | Direkt Hm olcumu |

## Basma Yuksekligi (Hm) Hesaplama

Oncelik sirasi:
1. **Direkt Hm tag'i**: ToplamHm, TotalHm, PompaHm, BasmaYuksekligi, GercekHm, Hm
2. **Basinc'tan donusum**: Hm tag'i yoksa, `BasincSensoru * 10.197` metre

## Verimlilik Hesaplama

### Hidrolik Verim
```
Hidrolik Guc (kW) = (Q * Hm * 9.81) / 3600
   Q = debi (m3/h)
   Hm = basma yuksekligi (metre)

Verim (%) = (Hidrolik Guc / Motor Gucu) * 100
```

### Sistem Verimi
GENEL.phtml'de canli hesaplanir: debi, Hm, guc ve pompa sayisini kullanarak.

## Process Adapter Siniflandirmasi

| nView icerigi | Adapter | Debi onceligi |
|--------------|---------|---------------|
| "kuyu" / "well" | well | Lt/sn oncelikli |
| "terfi" / "riser" | riser | m3/h oncelikli |
| "depo" / "tank" / "store" | tank | m3/h oncelikli |
| Diger | generic | m3/h oncelikli |

## Cok Pompali Sistemler

Terfi istasyonlarinda birden fazla pompa olabilir:
- `P1_Durum`, `P2_Durum`, ... `P10_Durum` - Pompa durumlari
- `P1_Calisiyor`, `P2_Calisiyor` - Calisma durumu
- Her pompa icin ayri frekans, akim, guc degerleri olabilir

## MCP Araclari

| Arac | Kullanim |
|------|----------|
| `get_pump_catalog_for_node(nodeId)` | Node icin pompa katalog bilgisi |
| `get_well_hydraulic_profile(nodeId)` | Kuyu hidrolik profili |
| `analyze_pump_performance(nodeId)` | Pompa performans analizi |
| `search_pump_alternatives(nodeId)` | Alternatif pompa onerisi |
| `calculate_hydraulic_metrics(nodeId)` | Hidrolik metrik hesaplama |
| `compare_log_metrics(nodeId, "debi", "guc")` | Debi-guc karsilastirma grafigi |

## Pompa Ariza Isaretleri
- Debi dusuk + guc yuksek: Pompa performans kaybetmis olabilir
- Hm dusuk + debi dusuk: Kuyu seviyesi dusmus olabilir
- Frekans degisken + debi sabit degil: VFD (inverter) sorunu
- Guc = 0 ama pompa durumu = calisiyor: Sensor veya iletisim hatasi
