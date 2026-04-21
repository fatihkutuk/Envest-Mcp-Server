---
name: nview-a-depo-envest-brm
description: |
  nView 'a-depo-envest-brm' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-depo-envest-brm" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: Debimetre, a-depo-envest-brm.
version: "1.0.0"
generated: true
source: //10.10.10.72/public/dev.korubin/app/views/point/display/common/a-depo-envest-brm/GENEL.phtml
---

# nView: a-depo-envest-brm

Aile bağlamı: **depo.md (depo izleme)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 2 | measurement | langt=Debi; (div) |
| `actAcKapa` |  |  |  | unknown | (div) |
| `OranACT1_PosVanaPozisyon` | [langt:Vana Pozisyon] | % | 1 | unknown | (div) |
| `OrtamSicaklikDeger` | [langt:İç Ortam] | °C | 2 | unknown | (div) |
| `SuSicaklikDeger` | [langt:Su] | °C | 2 | unknown | (div) |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **counter**: `T_Su2SayacS`
- **unknown**: `GirisDebi`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `ayar_yedek` | [langt:Ayar Yedekleri] |  | — |
| `saat_ayar` | [langt:Saat Ayarları] |  | — |
| `sensor` | [langt:Sensör] | [langt:Sensör Ayarları] | `XS_Seviye1SensorRange`, `XS_Seviye1SensorKalibre`, `XS_Seviye2SensorRange`, `XS_Seviye2SensorKalibre`, `XS_PanoSicaklikKalibre`, `XS_OrtamSicaklikKalibre`, `XS_SuSicaklikKalibre`, `XS_DisOrtamSicaklikKalibre` |
| `giris_debimetre` | [langt:Giriş Debimetre] | [langt:Giriş Debimetre Ayarları] | `XF_GirisDebimetreRange`, `XF_GirisDebimetreKalibre`, `GirisDebi`, `XS_PulseGirisDebiMiktar` |
| `klor_sensor` | [langt:Klor Sensör] | [langt:Klor Sensör Ayarları] | `XCH_GirisBakiyeKlorRange`, `XCH_GirisBakiyeKlorKalibre`, `XCH_CikisBakiyeKlorRange`, `XCH_CikisBakiyeKlorKalibre`, `XCH_KlorSeviyeRange`, `XCH_KlorSeviyeKalibre`, `XCH_PhRange`, `XCH_PhKalibre` …+2 |
| `emniyet_sensor` | [langt:Sensör Emniyet] | [langt:Sensör Emniyet Ayarları] | `XE_Seviye1GozAltLimit`, `XE_Seviye1GozUstLimit`, `XE_Seviye1GozDenetimZamani`, `XE_Seviye2GozAltLimit`, `XE_Seviye2GozUstLimit`, `XE_Seviye2GozDenetimZamani`, `XE_GirisDebimetreAltDeger`, `XE_GirisDebimetreUstDeger` …+22 |
| `emniyet_klor` | [langt:Klor Emniyet] | [langt:Klor Emniyet Ayarları] | `XE_GirisBakiyeKlorAltDeger`, `XE_GirisBakiyeKlorUstDeger`, `XE_GirisBakiyeKlorDenetimZamani`, `XE_CikisBakiyeKlorAltDeger`, `XE_CikisBakiyeKlorUstDeger`, `XE_CikisBakiyeKlorDenetimZamani`, `XE_PhAltDeger`, `XE_PhUstDeger` …+7 |
| `dozaj_ayar` | [langt:Dozaj Ayar] | [langt:Dozaj Pompası Ayarları] | `XDP_KlorBirimHacimDozajlamaMiktari`, `KlorDozajlamaMiktariBilgi`, `XDP_KlorDozajPompasiRange`, `XDP_KlorManuelDozajlamaMiktari` |
| `act_ayar` | [langt:ACT Ayar] | [langt:ACT Ayarları] | `XVN_ACT1_AcilmaZamani`, `XVN_ACT1_KapanmaZamani`, `XACT1_AcmaSeviye`, `XACT1_KapatmaSeviye`, `XVN_ACT2_AcilmaZamani`, `XVN_ACT2_KapanmaZamani`, `XACT2_AcmaSeviye`, `XACT2_KapatmaSeviye` …+16 |
| `oran_act_1_ayar` | [langt:Oransal ACT 1 Ayar] | [langt:Oransal ACT 1 Ayarları] | `XC_SabitModDebi`, `XC_DebiPIDKT`, `XC_DebiPIDKD`, `XC_DebiPIDKI`, `XC_DebiPIDKP`, `XOranACT1_PosManuelOran`, `OranACT1_PosVanaPozisyon`, `OranACT1_LinkSeviye` |
| `analog1_ayar` | [langt:Analog 1 Ayar] | [langt:Analog 1 Ayarları] | — |
| `analog2_ayar` | [langt:Analog 2 Ayar] | [langt:Analog 2 Ayarları] | — |

## Birim Özeti

- **Debi**: `Debimetre`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
