---
name: nview-a-terfi-bilge-otomasyon
description: |
  nView 'a-terfi-bilge-otomasyon' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-terfi-bilge-otomasyon" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: Debimetre, StatikSeviye, a-terfi-bilge-otomasyon.
version: "1.0.0"
generated: true
source: //10.10.10.72/public/dev.korubin/app/views/point/display/common/a-terfi-bilge-otomasyon/GENEL.phtml
---

# nView: a-terfi-bilge-otomasyon

Aile bağlamı: **terfi.md (terfi istasyonu)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 1 | measurement |  |
| `StatikSeviye` | Statik su seviyesi | m | 2 | measurement |  |
| `An_Guc_P1` | Anlık elektrik/motor ölçümü | kW | 2 | instant_electrical | langt=Sistem Güç; (col) |
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
| `CikisBasinc` |  | bar | 2 | unknown |  |
| `CikisDepoSeviye` | Çıkış deposu seviyesi | m | 2 | measurement |  |
| `DebiLitre_D1` |  | L/sn | 1 | unknown |  |
| `DinamikSeviye` | Dinamik seviye | m | 2 | measurement |  |
| `DisOrtamSicaklik` | Dış ortam sıcaklığı | °C | 2 | measurement | langt=Dış Ortam; (col) |
| `eNetGuc` | [langt:P1 Güç] | kW | 2 | unknown | (col) |
| `HatBasinc` |  | bar | 2 | unknown |  |
| `hidrolikVerim` | [langt:Hidrolik Verim] | % | 2 | unknown | (div) |
| `m3Maliyet` | [langt:Birim Maliyeti] | ₺/m³ | 2 | unknown | (div) |
| `MotorSicaklik` | Motor sıcaklığı | °C | 2 | measurement | langt=Motor; (col) |
| `NPSH` | NPSH Seviye | m | 2 | unknown |  |
| `PanoSicaklik` | Pano sıcaklığı | °C | 2 | measurement | langt=Pano; (col) |
| `sistemVerim` | [langt:Sistem Verim] | % | 2 | unknown | (div) |
| `SurucuFrekans` | [langt:Çıkış Frekans] | Hz | 2 | unknown | (col) |
| `SuSicaklik` | Su sıcaklığı | °C | 2 | measurement | langt=Su; (col) |
| `toplamHm` | Toplam basma yüksekliği (alias) | m | 2 | measurement | langt=Toplam hm; (div) |
| `txt_CikisDepo` |  |  | 2 | unknown |  |
| `xGunMaliyet` | [langt:Toplam Maliyet] | TL<b></b> | 2 | unknown | (div) |
| `XD_BasmaYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 1 | dimension_setting |  |
| `XD_CikisDepoYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **alarm**: `Al_KlorAriza`, `Al_Surucu`, `Al_Vana1Ariza`, `Al_Vana2Ariza`, `Al_Vana3Ariza`, `Al_Vana4Ariza`
- **analog_instant**: `XA_Analog1Secim`, `XA_Analog2Secim`, `XA_Analog3Secim`, `XA_Analog4Secim`
- **dimension_setting**: `XD_CikisDepoSeviyeAltLim_P1`, `XD_CikisDepoSeviyeUstLim_P1`, `XD_Depo1KritikAlt`, `XD_Depo1KritikUst`
- **install_constant**: `XV_BoruIcCap`, `XV_BoruUzunluk`, `XV_KabloKayip`, `XV_Nmotor`, `XV_Nsurtunme`, `XV_PipeRoughness`, `XV_SurucuKayip`
- **instant_electrical**: `An_Guc`
- **measurement**: `BasincSensoru`, `Pompa1StartStopDurumu`, `SuSeviye`, `ToplamHm`
- **operating_mode**: `XC_OperasyonModu`
- **sensor_setpoint**: `XS_AnalizorSecim`, `XS_SensorMontaj`
- **status**: `ACT_1_Durum`, `AntiBlokajDurum`, `DozajPompaStartStopDurumu`
- **unknown**: `Deb1_Cnt1`, `KlorTankDolu`, `PanoBTNStatus`, `Vana1Acildi`, `Vana2Acildi`, `Vana3Acildi`, `Vana4Acildi`, `XDeb_Aktif_D1`, `XDeb_Debimetre1_An_Rs_Secim`, `XVN_ACTAktif`, `YaklasikHidrolikVerim`, `js`, `length`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `pompaverim` | [langt:Pompa Verim] | [langt:Akıllı Pompa Seçimi] | `XV_Nsurtunme`, `XV_Nmotor`, `XV_SurucuKayip`, `XV_KabloKayip`, `XV_BoruIcCap`, `XV_BoruUzunluk`, `XV_PipeRoughness` |
| `maliyetdetay` | [langt:Maliyet Detay] | [langt:Maliyet Hesap Detayları] | — |
| `maliyet` | [langt:Maliyet] | [langt:Maliyet Hesap Ayarları] | `XM_T1Fiyat`, `XM_T1GunlukSaat`, `XM_T1YillikGun`, `XM_T2Fiyat`, `XM_T2GunlukSaat`, `XM_T2YillikGun`, `XM_T3Fiyat`, `XM_T3GunlukSaat` …+1 |
| `pump` | [langt:Pompa Bilgileri] | Pompa Bilgileri | — |
| `calismamod` | [langt:Çalışma Mod] | [langt:Pano Çalışma Mod Ayarları] | — |
| `sistem` | [langt:system] | [langt:Sistem Ayarları] | `XS_StatikSevGuncSure`, `XD_BasmaYukseklik` |
| `ssr_ayarlari` | [langt:SSR Ayarları] | [langt:SSR Ayarları] | `XSSR_SSROnTime`, `XSSR_SSROffTime` |
| `yeralti_seviye` | [langt:Yeraltı Seviye ] | [langt:Sensör Ayarları] | `XS_SensorMontaj`, `XS_PompaMontaj`, `NPSH`, `DinamikSeviye`, `XS_StatikSevGuncSure`, `StatikSeviye`, `XS_DinamikSevGuncSure`, `DinamikSeviye` |
| `debimetre` | [langt:Debimetre] | [langt:Debimetre Ayarlar] | `Debimetre1`, `DebiLitre_D1`, `Deb1_Conductivity`, `T_SuSayac_D1`, `T_SuSayac2_D1`, `T_SuSayacS`, `Debimetre2`, `DebiLitre_D2` …+4 |
| `emniyet` | [langt:Emniyet] | [langt:Pompa 1 Emniyet Ayarları] | `XE_VoltajAlt_P1`, `XE_VoltajUst_P1`, `XE_VoltajSure_P1`, `XE_AkimAlt_P1`, `XE_AkimUst_P1`, `XE_AkimSure_P1`, `XE_Surucu1FrekansAltLim`, `XE_Surucu1FrekansUstLim` …+10 |
| `analog_ayar` | [langt:Analog Ayar] | [langt:Analog Ayarları] | `XS_Analog1Min`, `XS_Analog1Max`, `XS_Analog1Kalibre`, `XS_Analog2Min`, `XS_Analog2Max`, `XS_Analog2Kalibre`, `XS_Analog3Min`, `XS_Analog3Max` …+4 |
| `analog_ayar2` | [langt:Analog Ayar 2] | [langt:Analog Ayarları 2] | `XS_Analog5Min`, `XS_Analog5Max`, `XS_Analog5Kalibre`, `XS_Analog6Min`, `XS_Analog6Max`, `XS_Analog6Kalibre`, `XS_Analog7Min`, `XS_Analog7Max` …+4 |
| `depo?sel=Cikis` | [langt:Çıkış Depo Ayr.] |  | — |
| `depo_doldurma` | [langt:Depo Doldurma] | [langt:Depo Doldurma Ayarları] | `XD_CikisDepoSeviyeAltLim_P1`, `XD_CikisDepoSeviyeUstLim_P1`, `XD_Depo1KritikAlt`, `XD_Depo1KritikUst` |
| `haberlesme` | [langt:Haberleşme] | [langt:Haberleşme Ayarları] | `XH_SunucuHabTimeOut`, `XH_DepoHabTimeOut`, `XH_P2_0006_CalismaSure`, `XH_P2_0006_DurmaSure`, `XH_P2_0612_CalismaSure`, `XH_P2_0612_DurmaSure`, `XH_P2_1218_CalismaSure`, `XH_P2_1218_DurmaSure` …+2 |
| `hidrofor_mod_ayar` | [langt:Hid. Mod Ayr.] | [langt:Hidrofor Modu Ayarları] | `XHID_HidroforBasincAltLim_P1`, `XPID_HedefBasinc`, `XHID_HidroforBasincUstLim_P1`, `XHID_HidroforKalkisSure` |
| `dononleme` | [langt:Don Önleme & Isıtıcı] | [langt:Pompa 1 Don Modu Çalışma Ayarları(Yeni)] | `XDon_P1_0006_CalismaSure`, `XDon_P1_0006_DurmaSure`, `XDon_P1_0612_CalismaSure`, `XDon_P1_0612_DurmaSure`, `XDon_P1_1218_CalismaSure`, `XDon_P1_1218_DurmaSure`, `XDon_P1_1824_CalismaSure`, `XDon_P1_1824_DurmaSure` …+6 |
| `modem` | [langt:Modem Reset] | [langt:Modem Ayarları] | `XMOD_ModemResetTimeOut` |
| `seviye_kontrol` | [langt:Şamandıra Ayar] | [langt:Şamandıra Kontrol] | `XS_SamandiraBaslamaSeviye`, `XC_SevKontStartBekleme`, `XS_SamandiraDurmaSeviye`, `XC_SevKontStopBekleme` |
| `surucuariza` | [langt:Sürücü Arıza] |  | — |
| `klorLink` | [langt:Klor Link] | [langt:Klor Oto Mod] | `XK_LinkPompaSayi` |
| `surucu1` | [langt:P1 Sürücü / PID Ayarları] | [langt:Sürücü Güç Girişi] | `XD_SurucuKW`, `XD_D1Referans`, `XD_D1SoftMin`, `XD_D1SoftMax`, `XD_D1HardMin`, `XD_D1HardMax`, `XPID_HedefBasinc`, `XPID_Debi` …+2 |
| `parselayar` | [langt:Parsel Ayarları] | [langt:Parsel Ayarları] | `XP_P1PtesiBasSaat`, `XP_P1PtesiBasDk`, `XP_P1PtesiSure`, `XP_P1SaliBasSaat`, `XP_P1SaliBasDk`, `XP_P1SaliSure`, `XP_P1CarsambaBasSaat`, `XP_P1CarsambaBasDk` …+29 |
| `actmenu` | [langt:Act Buton] | [langt:Buton] | — |

## Birim Özeti

- **Basınç (bar)**: `CikisBasinc`, `HatBasinc`
- **Debi**: `Debimetre`
- **Seviye / uzunluk (m/cm)**: `CikisDepoSeviye`, `DinamikSeviye`, `NPSH`, `StatikSeviye`, `XD_BasmaYukseklik`, `XD_CikisDepoYukseklik`, `toplamHm`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
