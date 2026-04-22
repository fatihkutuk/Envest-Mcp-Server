---
name: nview-a-depo-OCS110
description: |
  nView 'a-depo-OCS110' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-depo-OCS110" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: a-depo-OCS110.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-depo-OCS110

Aile bağlamı: **depo.md (depo izleme)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `T_SuSayac_D1` | Toplam sayaç (su, elektrik, çalışma, şalt) | m | 2 | counter | langt=Sayaç 1; (div) |
| `T_SuSayac_D2` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Sayaç 2; (div) |
| `T_SuSayac_D3` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Sayaç 3; (div) |
| `T_SuSayac_D4` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Sayaç 4; (div) |
| `BakiyeKlor` | Bakiye klor | mg/L | 2 | measurement | langt=Bakiye Klor; (div) |
| `Debimetre1` | Debi ölçümü 1 | m³/h | 2 | measurement |  |
| `Debimetre2` | Debi ölçümü 2 | m³/h | 2 | measurement | langt=Debimetre 2; (div) |
| `Debimetre3` | [langt:Debimetre 3] | m³/h | 2 | unknown | (div) |
| `Debimetre4` | [langt:Debimetre 4] | m³/h | 2 | unknown | (div) |
| `Depo1Bos` | [langt:Depo 1 Boş] | m³ | 2 | unknown | (div) |
| `Depo1Dolu` | [langt:Depo 1 Dolu] | m³ | 2 | unknown | (div) |
| `Depo1Kapasite` | [langt:Depo 1 Kapasite] | m³ | 2 | unknown | (div) |
| `Depo1Seviye` |  | m | 2 | unknown |  |
| `Depo2Bos` | [langt:Depo 2 Boş] | m³ | 2 | unknown | (div) |
| `Depo2Dolu` | [langt:Depo 2 Dolu] | m³ | 2 | unknown | (div) |
| `Depo2Kapasite` | [langt:Depo 2 Kapasite] | m³ | 2 | unknown | (div) |
| `Depo2Seviye` |  | m | 2 | unknown |  |
| `GirisToplamDebi` | Giriş toplam debi | m³/h | 2 | measurement |  |
| `Sicaklik1` | [langt:Sıcaklık - 1] | °C | 2 | unknown | (div) |
| `Sicaklik2` | [langt:Sıcaklık - 2] | °C | 2 | unknown | (div) |
| `Sicaklik3` | [langt:Sıcaklık - 3] | °C | 2 | unknown | (div) |
| `Sicaklik4` | [langt:Sıcaklık - 4] | °C | 2 | unknown | (div) |
| `XD_Depo1Yukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |
| `XD_Depo2Yukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting | langt=Depo 2 Yükseklik; (div) |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **dimension_setting**: `XD_Depo1Boy`, `XD_Depo1En`, `XD_Depo2Boy`, `XD_Depo2En`
- **unknown**: `DepoSeviye`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `panocalismamod` | [langt:Pano Çalş. Mod] | [langt:Pano Çalışma Mod Ayarları] | — |
| `debimetre` | [langt:Debimetre] | [langt:Debimetre Ayarları] | `Deb1_VolumeFlowm3h`, `Deb1_CoilTemperature`, `Deb1_Conductivity`, `Deb1_Cnt1`, `Deb1_Cnt2`, `Debimetre1`, `Deb2_VolumeFlowm3h`, `Deb2_CoilTemperature` …+16 |
| `depo_ayar` | Depo Ayarları | Depo Ayarları | `XD_Depo1Yukseklik`, `XD_Depo1En`, `XD_Depo1Boy`, `XD_Depo2Yukseklik`, `XD_Depo2En`, `XD_Depo2Boy` |
| `analog_ayar` | [langt:Analog Ayar] | [langt:Analog Kanal 1-4 Ayarları] | `XS_Analog1Min`, `XS_Analog1Max`, `XS_Analog1Kalibre`, `XS_Analog2Min`, `XS_Analog2Max`, `XS_Analog2Kalibre`, `XS_Analog3Min`, `XS_Analog3Max` …+10 |
| `klor_ayar` | [langt:Klor Ayar] | Klor Ayarları | `XK_KlorPompaRange`, `XK_KlorOran1m3`, `XK_KlorOranManuel` |
| `modem` | [langt:Modem Reset] | [langt:Modem Ayarları] | `XMOD_ModemResetTimeOut` |
| `act?act=` | ' + ActTitle + ' |  | — |

## Birim Özeti

- **Debi**: `Debimetre1`, `Debimetre2`, `Debimetre3`, `Debimetre4`, `GirisToplamDebi`
- **Seviye / uzunluk (m/cm)**: `Depo1Seviye`, `Depo2Seviye`, `T_SuSayac_D1`, `XD_Depo1Yukseklik`, `XD_Depo2Yukseklik`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
