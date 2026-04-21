---
name: nview-a-kuyu-cp110gm
description: |
  nView 'a-kuyu-cp110gm' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-kuyu-cp110gm" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, Debimetre, StatikSeviye, SuSeviye, a-kuyu-cp110gm.
version: "1.0.0"
generated: true
source: //10.10.10.72/public/dev.korubin/app/views/point/display/common/a-kuyu-cp110gm/GENEL.phtml
---

# nView: a-kuyu-cp110gm

Aile bağlamı: **kuyu.md (canlı tag + SP serisi dalgıç pompa)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `BasincSensoru` | Çıkış basıncı | bar | 2 | measurement |  |
| `BasincSensoru2` | Hat basıncı | bar | 2 | measurement |  |
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 1 | measurement |  |
| `StatikSeviye` | Statik su seviyesi | m | 2 | measurement |  |
| `SuSeviye` | Dinamik su seviyesi | m | 2 | measurement |  |
| `An_Guc` | Anlık elektrik/motor ölçümü | kWh | 1 | instant_electrical | langt=Sistem Güç; (col) |
| `An_GucFaktoru` | Anlık elektrik/motor ölçümü | % | 3 | instant_electrical | langt=Güç Faktörü; (col) |
| `An_InvFrekans` | Anlık elektrik/motor ölçümü | Hz | 1 | instant_electrical | langt=Çıkış; (col) |
| `An_L1Akim` | L1 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L1Voltaj` | L1 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Akim` | L2 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Voltaj` | L2 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Akim` | L3 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Voltaj` | L3 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_OrtAkim` | Ort. Akım | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_OrtVoltaj` | Ort. Voltaj | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_SebFrekans` | Anlık elektrik/motor ölçümü | Hz | 1 | instant_electrical | langt=Giriş; (col) |
| `T_CalismaSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | h | 2 | counter | langt=Çalışma Sayacı; (div) |
| `T_ElektrikKalan` | Toplam sayaç (su, elektrik, çalışma, şalt) | kW/h | 2 | counter | langt=Kalan Elektrik Miktarı; (div) |
| `T_ElektrikReakInduSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | kVAR | 2 | counter | langt=Reaktif; (div) |
| `T_ElektrikSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | kW/h | 2 | counter | langt=Elektrik Sayacı; (div) |
| `T_PompSaltSayisi` | Toplam sayaç (su, elektrik, çalışma, şalt) | adet | 0 | counter | langt=Şalt Sayısı; (div) |
| `T_SuKalan` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Kalan Su Miktarı; (div) |
| `T_SuSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Su Sayacı; (div) |
| `CikisDepoSeviye` | Çıkış deposu seviyesi | m | 2 | measurement |  |
| `eNetGuc` | [langt:P1 Güç] | kW | 2 | unknown | (col) |
| `hidrolikVerim` | [langt:Hidrolik Verim] | % | 2 | unknown | (div) |
| `m3Maliyet` | [langt:Birim Maliyeti] | ₺/m³ | 2 | unknown | (div) |
| `NPSHSeviye` | NPSH seviye | m | 2 | measurement | langt=NPSH Seviye |
| `P1_Verim` | Pompa bazlı ölçüm | kWh | 2 | pump_measurement | langt=P1 Verim; (div) |
| `sistemVerim` | [langt:Sistem Verim] | % | 2 | unknown | (div) |
| `toplamHm` | Toplam basma yüksekliği (alias) | m | 2 | measurement | langt=Toplam hm; (div) |
| `txt_CikisDepo` |  |  | 2 | unknown |  |
| `xGunMaliyet` | [langt:Toplam Maliyet] | TL | 2 | unknown | (div) |
| `XD_BasmaYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 1 | dimension_setting |  |
| `XD_CikisDepoYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **alarm**: `Al_Surucu`
- **install_constant**: `XV_BoruIcCap`, `XV_BoruUzunluk`, `XV_KabloKayip`, `XV_Nmotor`, `XV_Nsurtunme`, `XV_PipeRoughness`, `XV_SurucuKayip`
- **measurement**: `Pompa1StartStopDurumu`, `SuSicaklik`, `ToplamHm`
- **operating_mode**: `XC_CalismaModu`
- **sensor_setpoint**: `XS_MontajSev`
- **status**: `ACT_1_Durum`, `ACT_Durum`, `AntiBlokajDurum`
- **unknown**: `LocalMod`, `ScadaMod`, `ServisMod`, `XVN_ACTAktif`, `YaklasikHidrolikVerim`, `length`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `tahsis` | [langt:allocation] | [langt:Tahsis Ayarları] | `SuTahsis`, `ElektrikTahsis` |
| `maliyetdetay` | [langt:Maliyet Detay] |  | — |
| `pompaverim` | [langt:Pompa Verimi] |  | — |
| `pump` | [langt:Pompa Bilgileri] | Pompa Bilgileri | — |
| `calismamod` | [langt:Sabitleme] | [langt:Çalışma Ayarları] | `XC_SabitModBasinc`, `XC_SabitModDebi`, `XC_SabitModSeviye`, `XC_SabitModGuc`, `XC_SabitModFrekans` |
| `sistem` | [langt:Sistem] | [langt:Sistem Ayarları] | `XS_StatikSevGuncSure`, `XD_BasmaYukseklik` |
| `pid` | [langt:PID] | [langt:PID Ayarları] | `XC_BasincPIDKP`, `XC_BasincPIDKI`, `XC_BasincPIDKD`, `XC_BasincPIDKT`, `XC_DebiPIDKP`, `XC_DebiPIDKI`, `XC_DebiPIDKD`, `XC_DebiPIDKT` …+8 |
| `sensor` | [langt:Sensör] | [langt:Sensör Ayarları] | `XS_BasincSensoruMax`, `XS_BasincSensoruKalibre`, `BasincSensoru`, `XS_HatBasincMax`, `XS_HatBasincKalibre`, `BasincSensoru2`, `XS_SeviyeMax`, `XS_SeviyeKalibre` …+14 |
| `klor_sensor` | [langt:Klor Sensör] | [langt:Klor Sensör Ayarları] | `XS_KlorSeviyeMax`, `XS_KlorSeviyeKalibre`, `KlorSeviyeSensoru`, `XS_BulaniklikMax`, `XS_BulaniklikKalibre`, `Bulaniklik`, `XS_IletkenlikKalibre`, `IletkenlikDeger` …+6 |
| `debimetre` | [langt:Debimetre] | [langt:Debimetre 1 Ayarları] | `XS_DebimetreMax`, `XS_DebimetreKalibre`, `Debimetre`, `XS_PulseDebiMiktar` |
| `debimetre2` | [langt:Debimetre 2] | [langt:Debimetre 2 Ayarları] | `XS_Debimetre2Max`, `XS_Debimetre2Kalibre`, `Debimetre2`, `XS_PulseDebi2Miktar` |
| `dozaj_ayar` | [langt:Dozaj Ayar] | [langt:Dozaj Pompası Ayarları] | `XS_1m3DozajMiktari`, `DozajlamaMiktari`, `XS_DozajPompRange`, `XS_SbtDozajMiktari`, `DozajlamaMiktari` |
| `programtablo` | [langt:Prog.Çalışma] | [langt:Program Tablo] | — |
| `emniyet` | [langt:Emniyet] | [langt:Emniyet Ayarları] | `XE_FrekansAlt`, `XE_FrekansUst`, `XE_FrekansSure`, `XE_VoltajAlt`, `XE_VoltajUst`, `XE_VoltajSure`, `XE_AkimAlt`, `XE_AkimUst` …+49 |
| `emniyet_reset_ayar` | [langt:Emniyet Reset] | [langt:Emniyet Reset Ayarları] | `XE_OtoAlarmResetSayac`, `XE_OtoAlarmResetSet`, `XE_OtoAlarmResetBeklemeSn`, `XE_OtoAlarmSayacResetlemeSn` |
| `maliyet` | [langt:Maliyet] | [langt:Maliyet Hesap Ayarları] | `XM_T1Fiyat`, `XM_T1GunlukSaat`, `XM_T1YillikGun`, `XM_T2Fiyat`, `XM_T2GunlukSaat`, `XM_T2YillikGun`, `XM_T3Fiyat`, `XM_T3GunlukSaat` …+1 |
| `seviye_kontrol` | [langt:Şamandıra Ayar] | [langt:Şamandıra Kontrol] | `XC_SevKontStart`, `XC_SevKontStartBekleme`, `XC_SevKontStop`, `XC_SevKontStopBekleme` |
| `depo` | [langt:Çıkış Depo Ayr.] | [langt:Çıkış Depo Ayarları] | `XD_CikisDepoEn`, `XD_CikisDepoBoy`, `XD_CikisDepoYukseklik`, `CikisDepoSeviye`, `XS_CikisDepoSeviyeMax`, `XS_CikisDepoSeviyeKalibre`, `CikisDepoSeviye` |
| `depo2` | [langt:Çıkış Depo 2 Ayr.] | [langt:Çıkış Depo 2 Ayarları] | `XD_CikisDepoEn2`, `XD_CikisDepoBoy2`, `XD_CikisDepoYukseklik2`, `CikisDepoSeviye2`, `XS_CikisDepoSeviyeMax2`, `XS_CikisDepoSeviyeKalibre2`, `CikisDepoSeviye2` |
| `depo_doldurma` | [langt:Depo Doldurma] | [langt:Depo Doldurma Ayarları] | `XD_CikisDepo1GunduzAlt`, `XD_CikisDepo1GunduzUst`, `XD_CikisDepo1PuantAlt`, `XD_CikisDepo1PuantUst`, `XD_CikisDepo1GeceAlt`, `XD_CikisDepo1GeceUst`, `XD_CikisDepo2GunduzAlt`, `XD_CikisDepo2GunduzUst` …+10 |
| `hidrofor_mod_ayar` | [langt:Hid. Mod Ayr.] | [langt:Hidrofor Modu Ayarları] | `XHID_BasincCalisma`, `XHID_BasincDurma`, `XHID_ZamanCalisma`, `XHID_ZamanDurma`, `XHID_DebiMin`, `XHID_DebiKontrolSuresi`, `XHID_FrekansMin`, `XHID_FrekansKontrolSuresi` |
| `haberlesme` | [langt:Haberleşme] | [langt:Sunucu Haberleşmesi Yokken Çalışma Ayarları] | `XH_HabYokCalisma`, `XH_HabYokDurma`, `XH_SunucuHabTimeOut`, `XH_Link1HabTimeOut` |
| `surucu` | [langt:Sürücü] | [langt:Sürücü Ayarları] | `XINV_SoftMinLimit`, `XINV_SoftMaxLimit`, `XINV_HardMaxLimit` |
| `analog1_ayar` | [langt:Analog 1 Ayar] | [langt:Analog 1 Ayarları] | — |
| `analog2_ayar` | [langt:Analog 2 Ayar] | [langt:Analog 2 Ayarları] | — |
| `act_ayar` | [langt:Act Ayar] | [langt:ACT Ayarları] | `ACT_AcilmaZamani`, `ACT_KapanmaZamani`, `OransalVana1Pozisyon`, `OransalVana2Pozisyon`, `OransalVana3Pozisyon` |
| `antiblokaj` | [langt:Antiblokaj] | [langt:Antiblokaj Mod] | `XC_AntiBlokajBekleme`, `XC_AntiBlokajCalisma`, `XC_AntiBlokajDevreyeGirmeSicaklik` |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoru`, `BasincSensoru2`
- **Debi**: `Debimetre`
- **Seviye / uzunluk (m/cm)**: `CikisDepoSeviye`, `NPSHSeviye`, `StatikSeviye`, `SuSeviye`, `XD_BasmaYukseklik`, `XD_CikisDepoYukseklik`, `toplamHm`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
