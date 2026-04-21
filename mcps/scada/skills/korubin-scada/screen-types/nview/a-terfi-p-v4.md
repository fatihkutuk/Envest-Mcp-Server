---
name: nview-a-terfi-p-v4
description: |
  nView 'a-terfi-p-v4' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-terfi-p-v4" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, Debimetre, a-terfi-p-v4.
version: "1.0.0"
generated: true
source: //10.10.10.72/public/dev.korubin/app/views/point/display/common/a-terfi-p-v4/GENEL.phtml
---

# nView: a-terfi-p-v4

Aile bağlamı: **terfi.md (terfi istasyonu)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `BasincSensoru` | Çıkış basıncı | bar | 2 | measurement |  |
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 1 | measurement |  |
| `An_Guc` | Anlık elektrik/motor ölçümü | kW | 2 | instant_electrical | langt=Sistem Güç; (col) |
| `An_InvFrekans` | Anlık elektrik/motor ölçümü | Hz | 1 | instant_electrical | langt=Çıkış; (col) |
| `An_L1Akim` | L1 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L1Voltaj` | L1 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Akim` | L2 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Voltaj` | L2 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Akim` | L3 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Voltaj` | L3 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_SebFrekans` | Anlık elektrik/motor ölçümü | Hz | 1 | instant_electrical | langt=Giriş Fr.; (col) |
| `T_CalismaSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | h |  | counter | langt=Çalışma Sayacı; (col) |
| `T_ElektrikSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | kW/h |  | counter | langt=Elektrik Sayacı; (col) |
| `T_SuSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ |  | counter | langt=Su Sayacı; (col) |
| `-Link1_DepoSeviye` |  | m | 2 | unknown |  |
| `DisOrtamSicaklik` | Dış ortam sıcaklığı | °C | 1 | measurement | langt=Dış Or.; (col) |
| `eNetGuc` | [langt:P1 Güç] | kW | 2 | unknown | (col) |
| `GirisBasincSensoru` |  | bar | 2 | unknown |  |
| `GirisDebi` | [langt:Giriş Debisi] | m³/h | 2 | unknown |  |
| `GirisDepoCikisDebi` | [langt:Çıkış Debisi] | m³/h | 2 | unknown |  |
| `GirisDepoSeviye` |  | m | 2 | unknown |  |
| `hidrolikVerim` | [langt:Hidrolik Verim] | % | 2 | unknown | (div) |
| `m3Maliyet` | [langt:Birim Maliyet] | ₺/m³ | 2 | unknown | (div) |
| `MotorSicaklik` | Motor sıcaklığı | °C | 1 | measurement | langt=Motor; (col) |
| `PanoSicaklik` | Pano sıcaklığı | °C | 1 | measurement | langt=Pano; (col) |
| `sistemVerim` | [langt:Sistem Verim] | % | 2 | unknown | (div) |
| `storeAmount` |  | m³ | 2 | unknown |  |
| `SuSicaklik` | Su sıcaklığı | °C | 1 | measurement | langt=Su; (col) |
| `toplamHm` | Toplam basma yüksekliği (alias) | m | 2 | measurement | langt=Toplam hm; (div) |
| `txt_CikisDepo` |  |  | 2 | unknown |  |
| `xGunMaliyet` | [langt:Top. Maliyet] |  | 2 | unknown | (div) |
| `XD_CikisDepoYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |
| `XD_GirisDepoYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **alarm**: `Al_Surucu`
- **dimension_setting**: `XD_GirisDepoBoy`, `XD_GirisDepoEn`
- **install_constant**: `XV_KabloKayip`, `XV_Nmotor`, `XV_Nsurtunme`, `XV_SurucuKayip`
- **measurement**: `Pompa1StartStopDurumu`
- **status**: `ACT_1_Durum`
- **unknown**: `XVN_ACTAktif`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `tahsis` | [langt:allocation] | [langt:Tahsis Ayarları] | `T_SuKalan`, `T_ElektrikKalan` |
| `maliyetdetay` | [langt:Maliyet Detay] | [langt:Maliyet Hesap Detayları] | — |
| `pompaverim` | [langt:Pompa Verimi] | [langt:Pompa Verimi] | `XV_Nsurtunme`, `XV_Nmotor`, `XV_SurucuKayip`, `XV_KabloKayip` |
| `calismamod` | [langt:Çalışma Mod] | [langt:Çalışma Ayarları] | `XC_SabitModBasinc`, `XC_SabitModDebi`, `XC_SabitModSeviye`, `XC_SabitModGuc`, `XC_SabitModFrekans` |
| `pid` | PID | [langt:PID Ayarları] | `XC_BasincPIDKP`, `XC_BasincPIDKI`, `XC_BasincPIDKT`, `XC_DebiPIDKP`, `XC_DebiPIDKI`, `XC_DebiPIDKT`, `XC_GucPIDKP`, `XC_GucPIDKI` …+1 |
| `sensor` | [langt:Sensör] | [langt:Sensör Ayarları] | `XS_GirisBasincMax`, `XS_BasincMax`, `XS_MontajSev`, `XS_CikisDepoSeviyeMax`, `XS_PanoSicKalibre`, `XS_PanoFanCalisSicaklik`, `XS_MotorSicKalibre`, `XS_SuSicKalibre` …+1 |
| `debimetre` | [langt:Debimetre] | [langt:Debimetre] | `XS_DebiMax`, `XS_DebiKalibre` |
| `programtablo` | [langt:Prog.Çalışma] | [langt:Program Tablo] | — |
| `emniyet` | [langt:Emniyet] | [langt:Emniyet Ayarları] | `XE_FrekansAlt`, `XE_FrekansUst`, `XE_FrekansSure`, `XE_VoltajAlt`, `XE_VoltajUst`, `XE_VoltajSure`, `XE_AkimAlt`, `XE_AkimUst` …+28 |
| `blokaj_modu` | [langt:Antiblokaj] | [langt:Antiblokaj Mod] | `XC_AntiBlokajBekleme`, `XC_AntiBlokajCalisma` |
| `maliyet` | [langt:Maliyet] | [langt:Maliyet Hesap Ayarları] | `XM_T1Fiyat`, `XM_T1GunlukSaat`, `XM_T1YillikGun`, `XM_T2Fiyat`, `XM_T2GunlukSaat`, `XM_T2YillikGun`, `XM_T3Fiyat`, `XM_T3GunlukSaat` …+1 |
| `hmikullanici` | [langt:HMI Güvenlik] |  | — |
| `depo?sel=Giris&sel2=Giriş` | [langt:Giriş Depo Ayr.] |  | — |
| `depo?sel=Cikis&sel2=Çıkış` | [langt:Çıkış Depo Ayr.] |  | — |
| `depo_doldurma` | [langt:Depo Doldurma] | [langt:Depo Doldurma Ayarları] | `XD_CikisDepoYukseklik`, `XD_CikisDepoAlt`, `XD_CikisDepoUst`, `XD_CikisDepoKritikAlt`, `XD_CikisDepoKritikUst` |
| `hidrofor_mod_ayar` | [langt:Hid. Mod Ayr.] | [langt:Hidrofor Modu Ayarları] | `XHID_BasincAlt`, `XHID_BasincUst`, `XHID_DebiMin`, `XHID_DebiKontrolSuresi`, `XHID_FrekansMin`, `XHID_FrekansKontrolSuresi` |
| `haberlesme` | [langt:Haberleşme] | [langt:Sunucu Haberleşmesi Yokken Çalışma Ayarları] | `XH_HabYokCalisma`, `XH_HabYokDurma`, `XH_SunucuHabTimeOut`, `XH_Link1HabTimeOut`, `XH_MasterPLCHabTimeOut` |
| `surucu` | [langt:Sürücü] | [langt:Sürücü Ayarları] | `XINV_HardMaxLimit`, `XINV_SoftMinLimit`, `XINV_SoftMaxLimit` |
| `act_settings` | [langt:Act Ayar] | [langt:Actuator Vana Ayarları] | `XVN_ACTAcmaKontrolSure`, `XVN_ACTKapatmaKontrolSure` |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoru`, `GirisBasincSensoru`
- **Debi**: `Debimetre`, `GirisDebi`, `GirisDepoCikisDebi`
- **Seviye / uzunluk (m/cm)**: `-Link1_DepoSeviye`, `GirisDepoSeviye`, `XD_CikisDepoYukseklik`, `XD_GirisDepoYukseklik`, `toplamHm`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
