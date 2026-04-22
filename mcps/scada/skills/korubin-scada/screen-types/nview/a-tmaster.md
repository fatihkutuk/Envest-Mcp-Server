---
name: nview-a-tmaster
description: |
  nView 'a-tmaster' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-tmaster" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: Debimetre, a-tmaster.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-tmaster

Aile bağlamı: **system.md (genel)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 2 | measurement | (div) |
| `BakiyeKlorBilgisi` |  | mg/L | 2 | unknown | (div) |
| `BasincCollector` |  | bar | 2 | unknown | (div) |
| `Depo1Seviye` |  |  | 2 | unknown |  |
| `Depo2Seviye` |  |  | 2 | unknown |  |
| `eDepoAmount` |  | m³ |  | unknown | (div) |
| `eDepoBlank` |  | m³ |  | unknown | (div) |
| `eDepoCap` |  | m³ |  | unknown | (div) |
| `GirisDebi` |  | m³/h | 2 | unknown | (div) |
| `KlorDozajDebi` |  | m³/h | 2 | unknown | (div) |
| `KlorDozajSetKlor` |  | ml/h | 2 | unknown | (div) |
| `PhOlcumBilgisi` |  | pH | 2 | unknown | (div) |
| `vanaWrap` |  |  |  | unknown | (div) |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **dimension_setting**: `XD_Depo1Boy`, `XD_Depo1En`, `XD_Depo1Yukseklik`, `XD_Depo2Boy`, `XD_Depo2En`, `XD_Depo2Yukseklik`
- **sensor_setpoint**: `XS_Depo2SeviyeMax`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `dozajklor` | [langt:Dozaj Klor] | [langt:Klor Dozaj Ayarları] | `XS_KlorDozajMax`, `XC_KlorDozajDebiSet`, `XC_KlorDozajKlorSet`, `XS_KlorDebiMax` |

## Birim Özeti

- **Basınç (bar)**: `BasincCollector`
- **Debi**: `Debimetre`, `GirisDebi`, `KlorDozajDebi`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
