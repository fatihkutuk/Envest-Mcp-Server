---
name: nview-a-gozlem-m
description: |
  nView 'a-gozlem-m' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-gozlem-m" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: a-gozlem-m.
version: "1.0.0"
generated: true
source: //10.10.10.72/public/dev.korubin/app/views/point/display/common/a-gozlem-m/GENEL.phtml
---

# nView: a-gozlem-m

Aile bağlamı: **system.md (genel)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `IletkenlikSensoru` |  | μS | 3 | unknown | (div) |
| `kuyu` |  | m |  | unknown | (div) |
| `OksijenSensoru` |  | mg/L | 2 | unknown | (div) |
| `pHSensoru` |  | pH | 2 | unknown | (div) |
| `yeryuzu` |  | &#8451; |  | unknown | (div) |

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `sensor` | [langt:Sensör] | [langt:Sensör Ayarları] | `XS_SeviyeMax`, `XS_MontajSev`, `XS_SuSicKalibre`, `XS_DisOrtamSicKalibre` |

## Birim Özeti

- **Seviye / uzunluk (m/cm)**: `kuyu`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
