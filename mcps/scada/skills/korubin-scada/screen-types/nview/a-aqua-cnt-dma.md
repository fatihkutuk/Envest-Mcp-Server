---
name: nview-a-aqua-cnt-dma
description: |
  nView 'a-aqua-cnt-dma' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-aqua-cnt-dma" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, Debimetre, a-aqua-cnt-dma.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-aqua-cnt-dma

Aile bağlamı: **dma.md (debi bölge K-Means + basınç ölçekleme)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `BasincSensoru` | Basınç | bar | 2 | measurement | Çıkış basıncı |
| `Debimetre` | Debimetre | m³/h | 2 | measurement | Debi ölçümü (m³/h) |
| `T_SuSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Su Sayaç (Cihaz); (div) |
| `T_SuSayacS` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Su Sayaç (Sunucu); (div) |
| `Debimetre2` | Debimetre2 | m³/h | 2 | measurement | Debi ölçümü 2 |
| `debimetre2Lt` |  | lt/sn | 2 | unknown |  |
| `debimetreLt` |  | lt/sn | 2 | unknown |  |
| `GirisBasincSensoru` | Giriş Basınç | bar | 2 | unknown |  |
| `ili1` |  |  | 1 | unknown |  |
| `ili2` |  |  | 1 | unknown |  |
| `ili3` |  |  | 1 | unknown |  |
| `PilSeviye` | <ico class="battery"></ico> | % | 2 | unknown | langt=Pil Durumu; (div) |
| `PilSicaklik2` | <ico class="battery"></ico> | °C | 2 | unknown | langt=Pil Sıcaklık; (div) |
| `XC_AnalogCikisTwo` | Çalışma modu / mod seçim | Hz | 2 | operating_mode | langt=Analog Çıkış; (div) |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **analog_instant**: `XA_Analog4Secim`
- **operating_mode**: `XC_AnalogCikis`
- **unknown**: `Debimetre4`, `GirisBasinc`, `PilSicaklik`, `XINV_HardMaxLimit`, `_NoError`, `js`, `length`

## Arayüz Ayarları (uisettings.phtml)

Bu nView'da bazı tag'ler **node konfigürasyonuna göre** aktif olur. Node parametre (`np`) üzerinde şu bayraklar kontrol edilir; bir DMA noktasında hangi basınç/debi sensörünün gerçekten kullanıldığını anlamak için bu tabloya bakın:

| np anahtarı | Etiket | Aktifse görünür tag'ler |
|---|---|---|
| `ui_girisbasinc` | [langt:Giriş Basınç Sensörü] | — |
| `ui_cikisbasinc` | [langt:Çıkış Basınç Sensörü] | — |
| `ui_debimetre1` | [langt:Debimetre 1] | — |
| `ui_debimetre2` | [langt:Debimetre 2] | — |

> **DMA basınç bölgeleme analizi için ipucu:** `ui_cikisbasinc=1` ise node'da çıkış basınç sensörü (genelde `BasincSensoru`) aktif; `ui_girisbasinc=1` ise giriş basınç (`GirisBasincSensoru` veya `GirisBasinc`) aktif. Tool `analyze_dma_seasonal_demand` bu tag'lerin log'undan min/max türeterek PRV bandını otomatik belirler.

## Alt Menü Sayfaları (MENU.phtml)

| Sayfa (phtml) | Etiket |
|---|---|
| `uisettings` | [langt:Arayüz Ayarları] |
| `map` | [langt:Harita Ayarları] |
| `dma` | [langt:BYA/BÖA Ayarları] |
| `iwa` | [langt:IWA Ayarları] |
| `analogCikis` | [langt:Analog Çıkış] |
| `dijitalGirisCikis` | [langt:Dijital Giriş Çıkış] |
| `sensor` | [langt:Sensör] |
| `log` | [langt:Cihaz Log] |
| `cihaz_uyari` | [langt:Cihaz Uyarı] |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoru`, `GirisBasincSensoru`
- **Debi**: `Debimetre`, `Debimetre2`, `debimetre2Lt`, `debimetreLt`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
