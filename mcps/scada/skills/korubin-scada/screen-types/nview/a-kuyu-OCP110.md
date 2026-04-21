---
name: nview-a-kuyu-OCP110
description: |
  nView 'a-kuyu-OCP110' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-kuyu-OCP110" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: Debimetre, StatikSeviye, a-kuyu-OCP110.
version: "1.0.0"
generated: true
source: //10.10.10.72/public/dev.korubin/app/views/point/display/common/a-kuyu-OCP110/GENEL.phtml
---

# nView: a-kuyu-OCP110

Aile bağlamı: **kuyu.md (canlı tag + SP serisi dalgıç pompa)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 2 | measurement |  |
| `StatikSeviye` | Statik su seviyesi | m | 2 | measurement |  |
| `An_Guc_P1` | Anlık elektrik/motor ölçümü | kW | 2 | instant_electrical | langt=Sistem Güç; (col) |
| `An_InverterFrekans` | Anlık elektrik/motor ölçümü | Hz | 2 | instant_electrical | langt=Çıkış Frekans; (col) |
| `An_kVarh_P1` | Anlık elektrik/motor ölçümü | kVarh |  | instant_electrical | langt=Reaktif Sayaç; (div) |
| `An_kWh_P1` | Anlık elektrik/motor ölçümü | kWh |  | instant_electrical | langt=Elektirik Sayaç; (div) |
| `An_L1Akim_P1` | L1 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L1Voltaj_P1` | L1 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Akim_P1` | L2 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Voltaj_P1` | L2 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Akim_P1` | L3 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Voltaj_P1` | L3 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_pF_P1` | Anlık elektrik/motor ölçümü |  | 2 | instant_electrical | langt=Cos Q P1; (col) |
| `An_SebFrekans_P1` | Anlık elektrik/motor ölçümü | Hz | 1 | instant_electrical | langt=Giriş; (col) |
| `T_PompaCalismaSayac_P1` | Toplam sayaç (su, elektrik, çalışma, şalt) | h |  | counter | langt=Çalışma Sayacı P1; (div) |
| `T_PompaSaltSayisi_P1` | Toplam sayaç (su, elektrik, çalışma, şalt) | adet |  | counter | langt=Şalt Sayısı P1; (div) |
| `T_SuSayac_D1` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ |  | counter | langt=Su Sayacı; (div) |
| `CikisDepoSeviye` | Çıkış deposu seviyesi | m | 2 | measurement |  |
| `DebiLitre_D1` |  | L/sn | 2 | unknown |  |
| `DinamikSeviye` | Dinamik seviye | m | 2 | measurement |  |
| `DisOrtamSicaklik` | Dış ortam sıcaklığı | °C | 2 | measurement | langt=Dış Ortam; (col) |
| `eNetGuc` | [langt:P1 Güç] | kW | 2 | unknown | (col) |
| `GirisBasinc` |  | bar | 2 | unknown |  |
| `HatBasinc` |  | bar | 2 | unknown |  |
| `hidrolikVerim` | [langt:Hidrolik Verim] | % | 2 | unknown | (div) |
| `m3Maliyet` | [langt:Birim Maliyeti] | ₺/m³ | 2 | unknown | (div) |
| `MotorSicaklik` | Motor sıcaklığı | °C | 2 | measurement | langt=Motor; (col) |
| `NPSH` | NPSH Seviye | m | 2 | unknown |  |
| `PanoSicaklik` | Pano sıcaklığı | °C | 2 | measurement | langt=Pano; (col) |
| `sistemVerim` | [langt:Sistem Verim] | % | 2 | unknown | (div) |
| `SuSicaklik` | Su sıcaklığı | °C | 2 | measurement | langt=Su; (col) |
| `toplamHm` | Toplam basma yüksekliği (alias) | m | 2 | measurement | langt=Toplam hm; (div) |
| `txt_CikisDepo` |  |  | 2 | unknown |  |
| `xGunMaliyet` | [langt:Toplam Maliyet] | TL<b></b> | 2 | unknown | (div) |
| `XD_CikisDepoYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **alarm**: `Al_Surucu`
- **install_constant**: `XV_BoruIcCap`, `XV_BoruUzunluk`, `XV_KabloKayip`, `XV_Nmotor`, `XV_Nsurtunme`, `XV_PipeRoughness`, `XV_SurucuKayip`
- **instant_electrical**: `An_Guc`
- **measurement**: `BasincSensoru`, `Pompa1StartStopDurumu`, `SuSeviye`, `ToplamHm`
- **sensor_setpoint**: `XS_MontajSev`
- **status**: `ACT_1_Durum`, `AntiBlokajDurum`
- **unknown**: `CalismaModu`, `PanoBTNStatus`, `XVN_ACTAktif`, `YaklasikHidrolikVerim`, `length`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `pompaverim` | [langt:Pompa Verimi] | [langt:Akıllı Pompa Seçimi] | `XV_Nsurtunme`, `XV_Nmotor`, `XV_SurucuKayip`, `XV_KabloKayip`, `XV_BoruIcCap`, `XV_BoruUzunluk`, `XV_PipeRoughness` |
| `maliyetdetay` | [langt:Maliyet Detay] | [langt:Maliyet Hesap Detayları] | — |
| `maliyet` | [langt:Maliyet] | [langt:Maliyet Hesap Ayarları] | `XM_T1Fiyat`, `XM_T1GunlukSaat`, `XM_T1YillikGun`, `XM_T2Fiyat`, `XM_T2GunlukSaat`, `XM_T2YillikGun`, `XM_T3Fiyat`, `XM_T3GunlukSaat` …+1 |
| `pump` | [langt:Pompa Bilgileri] | Pompa Bilgileri | — |
| `calismamod` | [langt:Çalışma Mod] | [langt:Çalışma Mod Ayarları] | `XC_SabitModBasinc`, `XC_SabitModDebi`, `XC_SabitModSeviye`, `XC_SabitModGuc`, `XC_SabitModFrekans` |
| `panocalismamod` | [langt:Pano Çalış. Mod] | [langt:Pano Çalışma Mod Ayarları] | — |
| `ssr_ayarlari` | [langt:SSR Ayarları] | [langt:SSR Ayarları] | `XSSR_SSROnTime`, `XSSR_SSROffTime` |
| `yeralti_seviye` | [langt:Yeraltı Seviye ] | [langt:Sensör Ayarları] | `XS_MontajSev`, `XS_MontajDerinlik`, `NPSH`, `DinamikSeviye`, `XS_StatikSevGuncSure`, `StatikSeviye`, `XS_DinamikSevGuncSure`, `DinamikSeviye` |
| `debimetre` | [langt:Debimetre] | [langt:Debimetre 1] | `Deb1_VolumeFlowm3h`, `Deb1_CoilTemperature`, `Deb1_Conductivity`, `Deb1_Cnt1`, `Deb1_Cnt2`, `Debimetre1`, `Deb2_VolumeFlowm3h`, `Deb2_CoilTemperature` …+16 |
| `emniyet` | [langt:Emniyet] | [langt:Pompa 1 Emniyet Ayarları] | `XE_LGerilimAlt_P1`, `XE_LGerilimUst_P1`, `XE_VoltajSure_P1`, `XE_IAkimAlt_P1`, `XE_IAkimUst_P1`, `XE_AkimSure_P1`, `XE_FrekansAlt_P1`, `XE_FrekansUst_P1` …+22 |
| `emniyet_reset_ayar` | [langt:Emniyet Reset] | [langt:Emniyet Reset Ayarları] | `XE_OtoAlarmResetSayac`, `XE_OtoAlarmResetSet`, `XE_OtoAlarmResetBeklemeSn`, `XE_OtoAlarmSayacResetlemeSn` |
| `analog_ayar` | [langt:Analog Ayar] | [langt:Analog Ayarları] | `XS_Analog1Min`, `XS_Analog1Max`, `XS_Analog1Kalibre`, `XS_Analog2Min`, `XS_Analog2Max`, `XS_Analog2Kalibre`, `XS_Analog3Min`, `XS_Analog3Max` …+4 |
| `depo?sel=Cikis` | [langt:Çıkış Depo Ayr.] |  | — |
| `girisbasincayar` | [langt:Giris Basınç Ayr.] | [langt:Giriş Basınç Ayarları] | `XD_GirisDepoAlt_P1`, `XD_GirisDepoUst_P1`, `XC_GirisBasincBaslamaGecikme`, `XC_GirisBasincDurmaGecikme` |
| `depo_doldurma` | [langt:Depo Doldurma] | [langt:Depo Doldurma Ayarları] | `XD_CikisDepoSeviyeAltLim_P1`, `XD_CikisDepoSeviyeUstLim_P1` |
| `haberlesme` | [langt:Haberleşme] | [langt:Haberleşme Ayarları] | `XH_SunucuHabTimeOut`, `XH_DepoHabTimeOut` |
| `hidrofor_mod_ayar` | [langt:Hid. Mod Ayr.] | [langt:Hidrofor Modu Ayarları] | `XHID_HidroforBasincAltLim_P1`, `XHID_HidroforBasincUstLim_P1`, `XHID_HidroforKalkisSure` |
| `dononleme` | [langt:Don Önleme] | [langt:Don Mod] | `XC_AntiBlokajBekleme`, `XC_AntiBlokajCalisma` |
| `isitici` | [langt:Isıtıcı] | [langt:Isıtıcı Ayarları] | `XS_CalismaSicaklik`, `XS_DurmaSicaklik` |
| `modem` | [langt:Modem Reset] | [langt:Modem Ayarları] | `XMOD_ModemResetTimeOut` |
| `programtablo` | [langt:Prog.Çalışma] | [langt:Programlı Çalışma] | — |
| `fonksiyonel` | [langt:Fonskiyonel] | [langt:Fonskiyonel Çıkış Ayarları] | — |
| `surucu_reset` | [langt:Sürücü Reset] | [langt:Sürücü Reset] | — |
| `surucu` | [langt:Sürücü] | [langt:Sürücü Ayarları] | `XINV_SoftMinLimit`, `XINV_SoftMaxLimit`, `XINV_HardMaxLimit` |
| `sicaklik` | [langt:Sıcaklık Kalibre] | [langt:Sıcaklık Ayarları] | `XS_DisOrtamSicaklikKalibre`, `XS_PanoSicaklikKalibre`, `XS_SuSicaklikKalibre`, `XS_MotorSicaklikKalibre` |

## Birim Özeti

- **Basınç (bar)**: `GirisBasinc`, `HatBasinc`
- **Debi**: `Debimetre`
- **Seviye / uzunluk (m/cm)**: `CikisDepoSeviye`, `DinamikSeviye`, `NPSH`, `StatikSeviye`, `XD_CikisDepoYukseklik`, `toplamHm`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
