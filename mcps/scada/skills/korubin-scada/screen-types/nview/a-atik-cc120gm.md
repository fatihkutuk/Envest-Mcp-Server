---
name: nview-a-atik-cc120gm
description: |
  nView 'a-atik-cc120gm' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-atik-cc120gm" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: Debimetre, a-atik-cc120gm.
version: "1.0.0"
generated: true
source: //10.10.10.72/public/dev.korubin/app/views/point/display/common/a-atik-cc120gm/GENEL.phtml
---

# nView: a-atik-cc120gm

Aile bağlamı: **system.md (genel)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 2 | measurement |  |
| `analizor3` |  | A |  | unknown | (div) |
| `BasincSensoruDeger` |  | bar | 2 | unknown |  |
| `DepoSeviye` |  |  | 2 | unknown |  |
| `JeneratorCalismaSaati` |  |  |  | unknown |  |
| `kuyuDurumSag` | Durum / mod göstergesi | A |  | status | (div) |
| `OrtamSicaklikDeger` |  | °C | 2 | unknown |  |
| `PanoSicaklikDeger` |  | °C | 2 | unknown |  |
| `Pompa1AkimOrtalamaDeger` |  | A | 2 | unknown | (div) |
| `Pompa1CalismaSaati` |  | saat | 2 | unknown | (div) |
| `Pompa1CikisFrekansDeger` |  | Hz | 2 | unknown | (div) |
| `Pompa1ElektrikSayacDeger` |  | kWh | 2 | unknown | (div) |
| `Pompa1ElektrikSayacReaktifDeger` |  | kVARh | 3 | unknown | (div) |
| `Pompa1FrekansDeger` |  | Hz | 2 | unknown | (div) |
| `Pompa1GucDeger` |  | kW | 2 | unknown | (div) |
| `Pompa1L1VoltajDeger` |  | V | 2 | unknown | (div) |
| `Pompa1L2AkimDeger` |  | A | 2 | unknown | (div) |
| `Pompa1L2VoltajDeger` |  | V | 2 | unknown | (div) |
| `Pompa1L3AkimDeger` |  | A | 2 | unknown | (div) |
| `Pompa1L3VoltajDeger` |  | V | 2 | unknown | (div) |
| `Pompa1VoltajOrtalamaDeger` |  | V | 2 | unknown | (div) |
| `Pompa2AkimOrtalamaDeger` |  | A | 2 | unknown | (div) |
| `Pompa2CalismaSaati` |  | saat | 2 | unknown | (div) |
| `Pompa2CikisFrekansDeger` |  | Hz | 2 | unknown | (div) |
| `Pompa2ElektrikSayacDeger` |  | kWh | 2 | unknown | (div) |
| `Pompa2ElektrikSayacReaktifDeger` |  | kVARh | 3 | unknown | (div) |
| `Pompa2FrekansDeger` |  | Hz | 2 | unknown | (div) |
| `Pompa2GucDeger` |  | kW | 2 | unknown | (div) |
| `Pompa2L1AkimDeger` |  | A | 2 | unknown | (div) |
| `Pompa2L1VoltajDeger` |  | V | 2 | unknown | (div) |
| `Pompa2L2AkimDeger` |  | A | 2 | unknown | (div) |
| `Pompa2L2VoltajDeger` |  | V | 2 | unknown | (div) |
| `Pompa2L3AkimDeger` |  | A | 2 | unknown | (div) |
| `Pompa2L3VoltajDeger` |  | V | 2 | unknown | (div) |
| `Pompa2SicaklikDeger` |  | °C | 2 | unknown | (div) |
| `Pompa2VoltajOrtalamaDeger` |  | V | 2 | unknown | (div) |
| `Pompa3AkimOrtalamaDeger` |  | A | 2 | unknown | (div) |
| `Pompa3CalismaSaati` |  | saat | 2 | unknown | (div) |
| `Pompa3CikisFrekansDeger` |  | Hz | 2 | unknown | (div) |
| `Pompa3ElektrikSayacDeger` |  | kWh | 2 | unknown | (div) |
| `Pompa3ElektrikSayacReaktifDeger` |  | kVARh | 3 | unknown | (div) |
| `Pompa3FrekansDeger` |  | Hz | 2 | unknown | (div) |
| `Pompa3GucDeger` |  | kW | 2 | unknown | (div) |
| `Pompa3L1VoltajDeger` |  | V | 2 | unknown | (div) |
| `Pompa3L2AkimDeger` |  | A | 2 | unknown | (div) |
| `Pompa3L2VoltajDeger` |  | V | 2 | unknown | (div) |
| `Pompa3L3AkimDeger` |  | A | 2 | unknown | (div) |
| `Pompa3L3VoltajDeger` |  | V | 2 | unknown | (div) |
| `Pompa3SicaklikDeger` |  | °C | 2 | unknown | (div) |
| `Pompa3VoltajOrtalamaDeger` |  | V | 2 | unknown | (div) |
| `sicaklik` |  | °C |  | unknown | (div) |
| `XD_Depo1Yukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **measurement**: `BasincSensoru`, `Pompa1StartStopDurumu`
- **status**: `Pompa2StartStopDurumu`, `Pompa3StartStopDurumu`
- **unknown**: `BasincSensoruRange`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `sensor` | [langt:Sensör] | [langt:Sensör Ayarları] | `XS_BasincSensoruRange`, `XS_BasincSensoruKalibre`, `XS_SeviyeSensoruRange`, `XS_SeviyeSensoruKalibre`, `XS_FanCalismaSicaklik`, `XS_PanoSicaklikKalibre`, `XS_OrtamSicaklikKalibre`, `XS_Pompa1SicaklikKalibre` …+2 |
| `debimetre` | [langt:Debimetre] | [langt:Debimetre Ayarları] | `XF_DebimetreRange`, `XF_DebimetreKalibre`, `Debimetre` |
| `calisma` | [langt:Seviye&Pompa] | [langt:Seviye ve Pompa Kontrol Ayarları] | `XLP_Seviye1DurmaSeviye`, `XLP_Seviye1CalismaSeviye`, `XLP_Seviye2DurmaSeviye`, `XLP_Seviye2CalismaSeviye`, `XLP_Seviye3DurmaSeviye`, `XLP_Seviye3CalismaSeviye` |
| `emniyet_sensor` | [langt:Sensör Emniyet] | [langt:Sensör Emniyet Ayarları] | `XE_EmniyetSeviyeAltDeger`, `XE_EmniyetSeviyeUstDeger`, `XE_EmniyetSeviyeGecikme`, `XE_EmniyetBasincAltDeger`, `XE_EmniyetBasincUstDeger`, `XE_EmniyetBasincGecikme`, `XE_EmniyetDebimetreAltDeger`, `XE_EmniyetDebimetreUstDeger` …+4 |
| `emniyet_pump?pump=1` | P1 |  | — |
| `emniyet_pump?pump=2` | P2 |  | — |
| `emniyet_pump?pump=3` | P3 |  | — |
| `emniyet_reset_ayar` | [langt:Emniyet Reset] | [langt:Emniyet Reset Ayarları] | `XE_OtoAlarmResetDk` |
| `surucu` | [langt:Sürücü] | [langt:Sürücü Ayarları] | `XINV_Surucu1Frekans`, `Pompa1CikisFrekansDeger`, `XINV_Surucu1SoftMinLimit`, `XINV_Surucu1SoftMaxLimit`, `XINV_Surucu1HardMaxLimit`, `XINV_Surucu2Frekans`, `Pompa2CikisFrekansDeger`, `XINV_Surucu2SoftMinLimit` …+7 |
| `depo` | [langt:Depo] | [langt:Depo Ayarları] | `XD_DepoEn`, `XD_DepoBoy`, `XD_Depo1Yukseklik` |
| `act_ayar` | [langt:Act Ayar] | [langt:ACT Ayarları] | `ACT1_AcilmaZamani`, `ACT1_KapanmaZamani`, `ACT2_AcilmaZamani`, `ACT2_KapanmaZamani`, `ACT3_AcilmaZamani`, `ACT3_KapanmaZamani` |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoruDeger`
- **Debi**: `Debimetre`
- **Seviye / uzunluk (m/cm)**: `XD_Depo1Yukseklik`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
