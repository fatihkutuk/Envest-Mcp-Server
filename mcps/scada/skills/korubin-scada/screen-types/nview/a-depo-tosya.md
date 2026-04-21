---
name: nview-a-depo-tosya
description: |
  nView 'a-depo-tosya' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-depo-tosya" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: a-depo-tosya.
version: "1.0.0"
generated: true
source: //10.10.10.72/public/dev.korubin/app/views/point/display/common/a-depo-tosya/GENEL.phtml
---

# nView: a-depo-tosya

Aile bağlamı: **depo.md (depo izleme)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `actdurum1` |  |  | 2 | unknown |  |
| `actdurum2` |  |  | 2 | unknown |  |
| `BasincSensoru3` |  |  | 2 | unknown |  |
| `Bulaniklik` | Bulanıklık (NTU) | NTU | 2 | measurement | langt=Bulanıklık; (div) |
| `DebiLitre_D1` | [langt:Giriş Debi] | lt/sn | 2 | unknown | (div) |
| `DebiLitre_D2` | Çıkış Debimetre | lt/sn | 2 | unknown |  |
| `GirisBasinc` | [langt:Basınç] | Bar | 2 | unknown | (div) |
| `OV1Oran` | Tosya Çıkış Vanası | % | 2 | unknown |  |
| `OV2Oran` | Yumuş. Tosya Çıkış | % | 2 | unknown |  |
| `OV3Oran` | Yumuş. Giriş Vanası | % | 2 | unknown |  |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **unknown**: `actdurum`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `analogayar` | [langt:Analog Ayarı-1] | [langt:Analog Ayarları] | `XS_Analog1Min`, `XS_Analog1Max`, `XS_Analog1Kalibre`, `XS_Analog2Min`, `XS_Analog2Max`, `XS_Analog2Kalibre`, `XS_Analog3Min`, `XS_Analog3Max` …+4 |
| `analogayar2` | [langt:Analog Ayarı-2] | [langt:Analog Ayarları] | `XS_Analog5Min`, `XS_Analog5Max`, `XS_Analog5Kalibre`, `XS_Analog6Min`, `XS_Analog6Max`, `XS_Analog6Kalibre`, `XS_Analog7Min`, `XS_Analog7Max` …+4 |
| `log` | [langt:Cihaz Log] |  | — |
| `actAyarlar` | [langt:ACT Ayarları] | [langt:Act 1 Ayarları] | `XACT_AcilmaZamanAct`, `XACT_AcilmaSeviyeAct`, `XACT_KapanmaZamanAct`, `XACT_KapanmaSeviyeAct`, `XACT_AcilmaZamanAct2`, `XACT_AcilmaSeviyeAct2`, `XACT_KapanmaZamanAct2`, `XACT_KapanmaSeviyeAct2` |
| `oransalVana` | [langt:Oransal Vana] | [langt:Oransal Vana Ayarları] | `XOV_OV1Oran`, `XOV_OV2Oran`, `XOV_OV3Oran` |

## Birim Özeti

- **Basınç (bar)**: `GirisBasinc`
- **Debi**: `DebiLitre_D1`, `DebiLitre_D2`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
