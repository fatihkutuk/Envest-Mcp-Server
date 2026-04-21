---
name: nview-a-depo-p-b
description: |
  nView 'a-depo-p-b' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-depo-p-b" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: Debimetre, a-depo-p-b.
version: "1.0.0"
generated: true
source: //10.10.10.72/public/dev.korubin/app/views/point/display/common/a-depo-p-b/GENEL.phtml
---

# nView: a-depo-p-b

Aile bağlamı: **depo.md (depo izleme)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 2 | measurement |  |
| `BakiyeKlorBilgisi` |  | mg/L | 2 | unknown |  |
| `BakiyeKlorBilgisiGiris` | [langt:Hat Giriş Bakiye Klor] | mg/L | 2 | unknown | (div) |
| `Debimetre2` | Debi ölçümü 2 | m³/h | 2 | measurement |  |
| `Depo1Seviye` |  | m | 2 | unknown |  |
| `Depo2Seviye` |  | m | 2 | unknown |  |
| `DepoSicaklik` | [langt:Depo Sıcaklığı] | ℃ | 2 | unknown | (div) |
| `eDepoAmount` | [langt:Su Miktarı] | m³ |  | unknown | (div) |
| `eDepoBlank` | [langt:Boş] | m³ |  | unknown | (div) |
| `eDepoCap` | [langt:Depo Kapasitesi] | m³ |  | unknown | (div) |
| `GirisDebi` |  | m³/h | 2 | unknown |  |
| `SuSicaklik` | Su sıcaklığı | ℃ | 2 | measurement | langt=Su Sıcaklığı; (div) |
| `XD_Depo1Yukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **dimension_setting**: `XD_Depo1Boy`, `XD_Depo1En`, `XD_Depo2Boy`, `XD_Depo2En`
- **unknown**: `DepoSeviye`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `sensor` | [langt:Sensör] | [langt:Sensör Ayarları] | `XS_DepoSeviyeMax`, `XS_Depo2SeviyeMax`, `XS_BakiyeKlorMax` |
| `debimetre` | [langt:Debimetre] | [langt:Debimetre Ayarları] | `XS_GirisDebiMax`, `XS_DebiMax` |
| `fonksiyonlar` | [langt:Fonksiyonlar] | [langt:Fonksiyon] | `F_AOWr` |
| `hmikullanici` | [langt:HMI Güvenlik] | [langt:HMI Güvenlik Ayarları] | `XH_HMISifre`, `XH_SensorAyarSifr` |
| `vana_ayar` | [langt:Vana Ayarları] | [langt:Vana Ayarları] | `XD_Depo1KritikAlt`, `XD_Depo1KritikUst`, `XD_Depo2KritikAlt`, `XD_Depo2KritikUst` |
| `depo_ayar?no=1` | [langt:Depo 1 Ayar] |  | — |
| `depo_ayar?no=2` | [langt:Depo 2 Ayar] |  | — |

## Birim Özeti

- **Debi**: `Debimetre`, `Debimetre2`, `GirisDebi`
- **Seviye / uzunluk (m/cm)**: `Depo1Seviye`, `Depo2Seviye`, `XD_Depo1Yukseklik`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
