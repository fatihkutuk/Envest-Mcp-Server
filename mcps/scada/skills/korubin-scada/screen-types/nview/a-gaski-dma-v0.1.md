---
name: nview-a-gaski-dma-v0.1
description: |
  nView 'a-gaski-dma-v0.1' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-gaski-dma-v0.1" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, Debimetre, a-gaski-dma-v0.1.
version: "1.0.0"
generated: true
source: //10.10.10.72/public/dev.korubin/app/views/point/display/common/a-gaski-dma-v0.1/GENEL.phtml
---

# nView: a-gaski-dma-v0.1

Aile bağlamı: **dma.md (debi bölge K-Means + basınç ölçekleme)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `BasincSensoru` | Çıkış basıncı | bar | 1 | measurement |  |
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 1 | measurement |  |
| `Debimetre2` | Debi ölçümü 2 | m³/h | 1 | measurement |  |
| `Hat_Cikis` |  |  | 1 | unknown |  |
| `Hat_Giris` |  |  | 1 | unknown |  |
| `ili2` |  |  | 1 | unknown |  |
| `ili3` |  |  | 1 | unknown |  |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **unknown**: `js`, `length`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `map` | [langt:Harita Ayarları] | [langt:Harita Ayarları] | — |
| `dma` | [langt:DMA Ayarları] | [langt:DMA Ayarları] | — |
| `iwa` | [langt:IWA Ayarları] | [langt:IWA Tabloları] | — |
| `ozellestirme` | [langt:Özelleştrme Ayarları] | [langt:Özelleştirme Ayarları] | — |
| `debimetre` | [langt:Debimetre] | [langt:Debimetre Ayarları] | `Deb1_VolumeFlowm3h`, `Deb1_CoilTemperature`, `Deb1_Conductivity`, `Deb1_Cnt1`, `Deb1_Cnt2`, `Debimetre1`, `Deb2_VolumeFlowm3h`, `Deb2_CoilTemperature` …+16 |
| `analog_ayar` | [langt:Analog Ayar] | [langt:Analog Ayarları] | `XS_Analog1Min`, `XS_Analog1Max`, `XS_Analog1Kalibre`, `XS_Analog2Min`, `XS_Analog2Max`, `XS_Analog2Kalibre`, `XS_Analog3Min`, `XS_Analog3Max` …+4 |
| `modem` | [langt:Modem Reset] | [langt:Modem Ayarları] | `XMOD_ModemResetTimeOut` |
| `fonksiyonel` | [langt:Fonksiyonel] | [langt:Dijital Çıkış] | — |
| `act?act=` | ' + ActTitle + ' |  | — |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoru`
- **Debi**: `Debimetre`, `Debimetre2`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
