---
name: nview-a-depo-p
description: |
  nView 'a-depo-p' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-depo-p" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: Debimetre, a-depo-p.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-depo-p

Aile bağlamı: **depo.md (depo izleme)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 2 | measurement | (div) |
| `BakiyeKlorBilgisi` |  | mg/L | 2 | unknown | (div) |
| `BakiyeKlorBilgisiGiris` |  | mg/L | 2 | unknown | (div) |
| `Debimetre2` | Debi ölçümü 2 | m³/h | 2 | measurement | (div) |
| `Depo1Seviye` |  |  | 2 | unknown |  |
| `Depo2Seviye` |  |  | 2 | unknown |  |
| `DepoSicaklik` |  | ℃ | 2 | unknown | (div) |
| `eDepoAmount` |  | m³ |  | unknown | (div) |
| `eDepoBlank` |  | m³ |  | unknown | (div) |
| `eDepoCap` |  | m³ |  | unknown | (div) |
| `GirisDebi` |  | m³/h | 2 | unknown | (div) |
| `SuSicaklik` | Su sıcaklığı | ℃ | 2 | measurement | (div) |
| `vanaWrap` |  |  |  | unknown | (div) |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **dimension_setting**: `XD_Depo1Boy`, `XD_Depo1En`, `XD_Depo1Yukseklik`, `XD_Depo2Boy`, `XD_Depo2En`, `XD_Depo2Yukseklik`
- **sensor_setpoint**: `XS_Depo2SeviyeMax`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `sensor` | [langt:Sensör] | [langt:Sensör Ayarları] | `XS_DepoSeviyeMax`, `XS_Depo2SeviyeMax`, `XS_BakiyeKlorMax`, `XS_BakiyeKlorGirisMax` |
| `debimetre` | [langt:Debimetre] | [langt:Debimetre Ayarları] | `XS_GirisDebiMax`, `XS_DebiMax` |
| `hmikullanici` | [langt:HMI Güvenlik] | [langt:HMI Güvenlik Ayarları] | `XH_HMISifre`, `XH_SensorAyarSifr` |
| `vana_ayar` | [langt:Vana Ayarları] | [langt:Vana Ayarları] | `XD_Depo1KritikAlt`, `XD_Depo1KritikUst`, `XD_Depo2KritikAlt`, `XD_Depo2KritikUst` |
| `depo_ayar?no=1` | [langt:Depo 1 Ayar] |  | — |
| `depo_ayar?no=2` | [langt:Depo 2 Ayar] |  | — |

## Birim Özeti

- **Debi**: `Debimetre`, `Debimetre2`, `GirisDebi`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
