---
name: nview-a-dma-p
description: |
  nView 'a-dma-p' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-dma-p" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, Debimetre, a-dma-p.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-dma-p

Aile bağlamı: **dma.md (debi bölge K-Means + basınç ölçekleme)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `BasincSensoru` | Çıkış Basınç | bar | 2 | measurement | Çıkış basıncı |
| `Debimetre` | Debimetre | m³/h | 2 | measurement | Debi ölçümü (m³/h) |
| `barucapi` | Boru Çapı | inç |  | unknown |  |
| `Debimetre4` | BKV Basınç | bar | 2 | unknown |  |
| `debimetreLt` |  | lt/sn | 2 | unknown |  |
| `GirisBasinc` | Giriş Basınç | bar | 2 | unknown |  |
| `ili1` |  |  | 1 | unknown |  |
| `ili2` |  |  | 1 | unknown |  |
| `ili3` |  |  | 1 | unknown |  |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **analog_instant**: `XA_Analog4Secim`
- **unknown**: `js`, `length`

## Alt Menü Sayfaları (MENU.phtml)

| Sayfa (phtml) | Etiket |
|---|---|
| `genel_ayar` | [langt:Genel Ayarlar] |
| `map2` | [langt:Harita Ayarları (Yeni)] |
| `map` | [langt:Harita Ayarları] |
| `dma` | [langt:DMA Ayarları] |
| `iwa` | [langt:IWA Ayarları] |
| `sensor` | [langt:Sensör] |
| `giris_debimetre` | [langt:Giriş Debimetre] |
| `cikis_debimetre` | [langt:Çıkış Debimetre] |
| `debimetre3` | [langt:Debimetre 3] |
| `debimetre4` | [langt:Debimetre 4] |
| `debimetre5` | [langt:Debimetre 5] |
| `debimetre6` | [langt:Debimetre 6] |
| `debimetre7` | [langt:Debimetre 7] |
| `klor_sensor` | [langt:Klor Sensör] |
| `emniyet_sensor` | [langt:Sensör Emniyet] |
| `emniyet_klor` | [langt:Klor Emniyet] |
| `dozaj_ayar` | [langt:Dozaj Ayar] |
| `pompa_debi_link` | [langt:Pom. Debi Li.] |
| `pompa_start_stop_link` | [langt:Pom. Start Li.] |
| `act_ayar` | [langt:ACT Ayar] |
| `oran_act_1_ayar` | [langt:Oransal ACT 1 Ayar] |
| `oran_act_2_ayar` | [langt:Oransal ACT 2 Ayar] |
| `oran_act_3_ayar` | [langt:Oransal ACT 3 Ayar] |
| `oran_act_4_ayar` | [langt:Oransal ACT 4 Ayar] |
| `depo_ayar` | [langt:Depo Ayar] |
| `analog1_ayar` | [langt:Analog 1 Ayar] |
| `analog2_ayar` | [langt:Analog 2 Ayar] |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoru`, `Debimetre4`, `GirisBasinc`
- **Debi**: `Debimetre`, `debimetreLt`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
