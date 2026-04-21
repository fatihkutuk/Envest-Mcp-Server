---
name: nview-a-gaski-dma
description: |
  nView 'a-gaski-dma' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-gaski-dma" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, Debimetre, a-gaski-dma.
version: "1.0.0"
generated: true
source: //10.10.10.72/public/dev.korubin/app/views/point/display/common/a-gaski-dma/GENEL.phtml
---

# nView: a-gaski-dma

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
| `sensor` | [langt:Sensör] | [langt:Sensör Ayarları] | `XS_BasincSensoruMax`, `XS_BasincSensoruKalibre`, `BasincSensoru` |
| `debimetre` | [langt:Debimetre] | [langt:Debimetre Ayarları] | `XF_CikisDebimetreRange`, `XF_CikisDebimetreKalibre`, `Debimetre` |
| `ozellestirme` | [langt:Özelleştrme Ayarları] | [langt:Özelleştirme Ayarları] | — |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoru`
- **Debi**: `Debimetre`, `Debimetre2`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
