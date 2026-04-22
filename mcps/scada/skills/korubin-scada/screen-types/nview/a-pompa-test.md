---
name: nview-a-pompa-test
description: |
  nView 'a-pompa-test' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-pompa-test" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: Debimetre, a-pompa-test.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-pompa-test

Aile bağlamı: **system.md (genel)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 1 | measurement |  |
| `AkimOrtalamaDeger` | [langt:Aort] | A | 1 | unknown | (col) |
| `BasincSensoruDeger` |  | bar | 2 | unknown |  |
| `BirimMaliyetGuc` | [langt:BirimMalGüç] | kWh | 2 | unknown | (div) |
| `BirimMaliyetTl` | [langt:BirimMalITI] | TI | 2 | unknown | (div) |
| `CikisFrekansDeger` | [langt:Invertor Frek.] | Hz | 2 | unknown | (col) |
| `CokNoktaTestHm10` | [langt:Nokta 10] | m | 2 | unknown | (div) |
| `CokNoktaTestHm2` | [langt:Nokta 2] | m | 2 | unknown | (div) |
| `CokNoktaTestHm3` | [langt:Nokta 3] | m | 2 | unknown | (div) |
| `CokNoktaTestHm4` | [langt:Nokta 4] | m | 2 | unknown | (div) |
| `CokNoktaTestHm5` | [langt:Nokta 5] | m | 2 | unknown | (div) |
| `CokNoktaTestHm7` | [langt:Nokta 7] | m | 2 | unknown | (div) |
| `CokNoktaTestHm8` | [langt:Nokta 8] | m | 2 | unknown | (div) |
| `CokNoktaTestHm9` | [langt:Nokta 9] | m | 2 | unknown | (div) |
| `DisOrtamSicaklikDeger` | [langt:Ortam] | °C | 2 | unknown | (div) |
| `ElektrikSayacDeger` | [langt:Elek Say.] | kWh | 2 | unknown | (col) |
| `ElektrikSayacReaktifDeger` | [langt:Reak Say.] | kVARh | 2 | unknown | (col) |
| `FrekansDeger` | [langt:Şebeke Frek.] | Hz | 2 | unknown | (col) |
| `GucFaktoruDeger` | [langt:Pf] | % | 2 | unknown | (col) |
| `Hf` | [langt:Toplam Hf] | m | 2 | unknown | (div) |
| `Hm` | [langt:Toplam Hm] | m | 2 | unknown | (div) |
| `hmdiv` | [langt:Nokta 1] | m |  | unknown | (div) |
| `Hmu0130stenilenAralikta` | [langt:Hm Aralıkta] |  | 2 | unknown | (div) |
| `L1AkimDeger` | L1 | A | 1 | unknown | (col) |
| `L1VoltajDeger` | L1 | V | 1 | unknown | (col) |
| `L2AkimDeger` | L2 | A | 1 | unknown | (col) |
| `L2VoltajDeger` | L2 | V | 1 | unknown | (col) |
| `L3AkimDeger` | L3 | A | 1 | unknown | (col) |
| `L3VoltajDeger` | L3 | V | 1 | unknown | (col) |
| `MotorSicaklikDeger` | [langt:Motor] | °C | 2 | unknown | (div) |
| `P1GucDeger` | [langt:Sistem Güç] | kW | 2 | unknown | (col) |
| `PanoSicaklikDeger` | [langt:MCC] | °C | 2 | unknown | (div) |
| `PompaVerimDeger` | [langt:pump-efficiency] | % | 2 | unknown | (div) |
| `ScadaPanoSicaklikDeger` | [langt:Scada] | °C | 2 | unknown | (div) |
| `TestAdimDeger` | [langt:Test Adımı] |  | 2 | unknown | (div) |
| `TestEdilenHm` | [langt:Test Hm] |  | 2 | unknown | (div) |
| `VoltajOrtalamaDeger` | [langt:Vort] | V | 1 | unknown | (col) |
| `XEF_BoruBasincSiniri` | [langt:Hat Basınç Sınırı] | bar | 2 | unknown | (div) |
| `XEF_HmAltSinir` | [langt:Test Hm Alt] | m | 2 | unknown | (div) |
| `XEF_HmAralikOran` | [langt:Hm Aralık Oran] | % | 2 | unknown | (div) |
| `XEF_HmUstSinir` | [langt:Test Hm Üst] | m | 2 | unknown | (div) |
| `XEF_LogAlmaSure` | [langt:Log Alma Süre] | dk | 2 | unknown | (div) |
| `XEF_TekNoktaHm` | [langt:Test Hm] | m | 2 | unknown | (div) |
| `XEF_TestNoktaSayisi` | [langt:Test Nokta Sayısı] | Adet | 2 | unknown | (div) |
| `YillikMaliyetGuc` | [langt:YıllıkMalGüç] | kWh | 2 | unknown | (div) |
| `YillikMaliyetTl` | [langt:YıllıkMalITI] | TI | 2 | unknown | (div) |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **alarm**: `Al_Surucu`
- **dimension_setting**: `XD_CikisDepoYukseklik`
- **install_constant**: `XV_BoruIcCap`, `XV_BoruUzunluk`, `XV_KabloKayip`, `XV_Nmotor`, `XV_Nsurtunme`, `XV_PipeRoughness`, `XV_SurucuKayip`
- **instant_electrical**: `An_Guc`
- **measurement**: `BasincSensoru`, `Pompa1StartStopDurumu`, `StatikSeviye`, `SuSeviye`, `SuSicaklik`
- **operating_mode**: `XC_OtoDepoDolMod`
- **sensor_setpoint**: `XS_MontajSev`
- **status**: `ACT_1_Durum`, `AntiBlokajDurum`
- **unknown**: `BoruHatSecim`, `TestDevemEdiyor`, `XVN_ACTAktif`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `pid` | PID | [langt:PID Ayarları] | `XPID_Kp`, `XPID_Ki`, `XPID_Kd`, `XPID_Kt` |
| `surucu` | [langt:Sürücü] | [langt:Sürücü Ayarları] | `XINV_SoftMinLimit`, `XINV_HardMinLimit`, `XINV_SurucuFrekans`, `CikisFrekansDeger`, `XINV_SoftMaxLimit`, `XINV_HardMaxLimit`, `SurucuFrekansAkimDeger`, `SurucuFrekansAkimDeger` |
| `act` | [langt:Actuatör] | [langt:Oransal Aktuatör Ayarları] | `XACT_SoftMinLimit`, `XACT_HardMinLimit`, `ACTOransalReferans`, `ACTOransalPozisyon`, `ManuelVanaReferans`, `XACT_SoftMaxLimit`, `XACT_HardMaxLimit`, `ACTOransalReferansAkim` …+1 |
| `verim` | [langt:Verim] | [langt:Verim] | `XEF_BoruPuruzlulukKatsayisi`, `XEF_MotorVerim`, `XEF_SurucuKaybi`, `XEF_MekanikKayip`, `XEF_KolonBoruUzunluk`, `XEF_KolonBoruIcCap` |
| `maliyet` | [langt:Maliyet] | [langt:Maliyet Girdileri] | `T1GunlukCalismaSaat`, `T1YillikCalismaGun`, `T1EnerjiMaaliyet`, `T2GunlukCalismaSaat`, `T2YillikCalismaGun`, `T2EnerjiMaaliyet`, `T3GunlukCalismaSaat`, `T3YillikCalismaGun` …+1 |
| `sensor` | [langt:Sensör] | Sensör Ayarları | `YeralitSeviyeAkimDeger`, `XS_YeraltiSeviyeSensoruRangeMin`, `XS_YeraltiSeviyeSensoruRangeMax`, `XS_YeraltiSeviyeSensoruKalibre`, `YeralitSeviyeDeger`, `XS_SensorMontajDerinlik`, `DinamikSeviye`, `StatikSeviye` …+17 |
| `emniyet` | [langt:Emniyet] | [langt:Emniyet Ayarları] | `XE_DinamikSeviyeAlt`, `XE_DinamikSeviyeUst`, `XE_DinamikSeviyeGecikme`, `XE_NPSHAlt`, `XE_NPSHUst`, `XE_NPSHGecikme`, `XE_BasincAlt`, `XE_BasincUst` …+28 |
| `izleme` | [langt:Test İzleme] | Test İzleme | — |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoruDeger`, `XEF_BoruBasincSiniri`
- **Debi**: `Debimetre`
- **Seviye / uzunluk (m/cm)**: `CokNoktaTestHm10`, `CokNoktaTestHm2`, `CokNoktaTestHm3`, `CokNoktaTestHm4`, `CokNoktaTestHm5`, `CokNoktaTestHm7`, `CokNoktaTestHm8`, `CokNoktaTestHm9`, `Hf`, `Hm`, `XEF_HmAltSinir`, `XEF_HmUstSinir`, `XEF_TekNoktaHm`, `hmdiv`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
