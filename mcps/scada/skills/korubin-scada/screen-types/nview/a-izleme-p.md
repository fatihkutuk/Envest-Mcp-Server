---
name: nview-a-izleme-p
description: |
  nView 'a-izleme-p' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-izleme-p" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, Debimetre, a-izleme-p.
version: "1.0.0"
generated: true
source: //10.10.10.72/public/dev.korubin/app/views/point/display/common/a-izleme-p/GENEL.phtml
---

# nView: a-izleme-p

Aile bağlamı: **system.md (genel)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `BasincSensoru` | Çıkış basıncı | bar | 2 | measurement |  |
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 2 | measurement |  |
| `Hat_Cikis` |  |  | 1 | unknown |  |
| `Hat_Giris` |  |  | 1 | unknown |  |

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `sensor` | [langt:Sensör] | [langt:Sensör Ayarları] | `XS_DepoSeviyeMax`, `XS_Depo2SeviyeMax`, `XS_BakiyeKlorMax` |
| `debimetre` | [langt:Debimetre] | [langt:Debimetre Ayarları] | `XS_GirisDebiMax`, `XS_DebiMax` |
| `hmikullanici` | [langt:HMI Güvenlik] | [langt:HMI Güvenlik Ayarları] | `XH_HMISifre`, `XH_SensorAyarSifr` |
| `vana_ayar` | [langt:Vana Ayarları] | [langt:Vana Ayarları] | `XD_Depo1KritikAlt`, `XD_Depo1KritikUst`, `XD_Depo2KritikAlt`, `XD_Depo2KritikUst` |
| `depo_ayar?no=1` | [langt:Depo 1 Ayar] |  | — |
| `depo_ayar?no=2` | [langt:Depo 2 Ayar] |  | — |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoru`
- **Debi**: `Debimetre`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
