---
name: nview-a-kuyu-p-v4
description: |
  nView 'a-kuyu-p-v4' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-kuyu-p-v4" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, Debimetre, StatikSeviye, SuSeviye, a-kuyu-p-v4.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-kuyu-p-v4

Aile bağlamı: **kuyu.md (canlı tag + SP serisi dalgıç pompa)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `BasincSensoru` | Çıkış basıncı | bar | 2 | measurement |  |
| `BasincSensoru2` | Hat basıncı | bar | 2 | measurement |  |
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 1 | measurement |  |
| `StatikSeviye` | Statik su seviyesi | m | 2 | measurement |  |
| `SuSeviye` | Dinamik su seviyesi | m | 2 | measurement |  |
| `An_Guc` | Anlık elektrik/motor ölçümü | kW | 2 | instant_electrical | langt=Sistem Güç; (col) |
| `An_InvFrekans` | Anlık elektrik/motor ölçümü | Hz | 1 | instant_electrical | langt=Çıkış; (col) |
| `An_L1Akim` | L1 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L1Voltaj` | L1 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Akim` | L2 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Voltaj` | L2 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Akim` | L3 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Voltaj` | L3 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_SebFrekans` | Anlık elektrik/motor ölçümü | Hz | 1 | instant_electrical | langt=Giriş; (col) |
| `T_CalismaSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | h |  | counter | langt=Çalışma Sayacı; (div) |
| `T_ElektrikKalan` | Toplam sayaç (su, elektrik, çalışma, şalt) | kW/h |  | counter | langt=Kalan Elektrik Miktarı; (div) |
| `T_ElektrikSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | kW/h |  | counter | langt=Elektrik Sayacı; (div) |
| `T_SuKalan` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ |  | counter | langt=Kalan Su Miktarı; (div) |
| `T_SuSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ |  | counter | langt=Su Sayacı; (div) |
| `-Link1_DepoSeviye` |  | m | 2 | unknown |  |
| `DisOrtamSicaklik` | Dış ortam sıcaklığı | °C | 2 | measurement | langt=Dış Or.; (div) |
| `eNetGuc` | [langt:P1 Güç] | kW | 2 | unknown | (col) |
| `hidrolikVerim` | [langt:Hidrolik Verim] | % | 2 | unknown | (div) |
| `m3Maliyet` | [langt:Birim Maliyet] | ₺/m³ | 2 | unknown | (div) |
| `MotorSicaklik` | Motor sıcaklığı | °C | 2 | measurement | langt=Motor; (div) |
| `PanoSicaklik` | Pano sıcaklığı | °C | 2 | measurement | langt=Pano; (div) |
| `sistemVerim` | [langt:Sistem Verim] | % | 2 | unknown | (div) |
| `SuSicaklik` | Su sıcaklığı | °C | 2 | measurement | langt=Su; (div) |
| `toplamHm` | Toplam basma yüksekliği (alias) | m | 2 | measurement | langt=Toplam hm; (div) |
| `txt_CikisDepo` |  |  | 2 | unknown |  |
| `xGunMaliyet` | [langt:Toplam Maliyet] | TL<b></b> | 2 | unknown | (div) |
| `XD_BasmaYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 1 | dimension_setting |  |
| `XD_CikisDepoYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **alarm**: `Al_Surucu`
- **install_constant**: `XV_BoruIcCap`, `XV_BoruUzunluk`, `XV_KabloKayip`, `XV_Nmotor`, `XV_Nsurtunme`, `XV_PipeRoughness`, `XV_SurucuKayip`
- **measurement**: `Pompa1StartStopDurumu`
- **operating_mode**: `XC_CalismaModu`
- **sensor_setpoint**: `XS_MontajSev`
- **status**: `ACT_1_Durum`, `AntiBlokajDurum`
- **unknown**: `XVN_ACTAktif`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `tahsis` | [langt:allocation] | [langt:Tahsis Ayarları] | `T_SuKalan`, `T_ElektrikKalan` |
| `maliyetdetay` | [langt:Maliyet Detay] | [langt:Maliyet Hesap Detayları] | — |
| `pompaverim` | [langt:Pompa Verimi] | [langt:Akıllı Pompa Seçimi] | `XV_Nsurtunme`, `XV_Nmotor`, `XV_SurucuKayip`, `XV_KabloKayip`, `XV_BoruIcCap`, `XV_BoruUzunluk`, `XV_PipeRoughness` |
| `calismamod` | [langt:Sabitleme] | [langt:Çalışma Ayarları] | `XC_SabitModBasinc`, `XC_SabitModDebi`, `XC_SabitModSeviye`, `XC_SabitModGuc`, `XC_SabitModFrekans` |
| `sistem` | [langt:Sistem] | [langt:Sistem Ayarları] | `XS_StatikSevGuncSure`, `XD_BasmaYukseklik`, `XE_EnKesTekrarCalSure` |
| `pid` | [langt:PID] | [langt:PID Ayarları] | `XC_BasincPIDKP`, `XC_BasincPIDKI`, `XC_BasincPIDKT`, `XC_DebiPIDKP`, `XC_DebiPIDKI`, `XC_DebiPIDKT`, `XC_SeviyePIDKP`, `XC_SeviyePIDKI` …+4 |
| `sensor` | [langt:Sensör] | [langt:Sensör Ayarları] | `XS_BasincMax`, `XS_SeviyeMax`, `XS_MontajSev`, `XS_PanoSicKalibre`, `XS_PanoFanCalisSicaklik`, `XS_MotorSicKalibre`, `XS_SuSicKalibre`, `XS_DisOrtamSicKalibre` |
| `blokaj_modu` | [langt:Antiblokaj] | [langt:Antiblokaj Mod] | `XC_AntiBlokajBekleme`, `XC_AntiBlokajCalisma` |
| `debimetre` | [langt:Debimetre] | [langt:Debimetre Ayarları] | `XS_DebiMax`, `XS_DebiKalibre` |
| `programtablo` | [langt:Prog.Çalışma] |  | — |
| `emniyet` | [langt:Emniyet] | [langt:Emniyet Ayarları] | `XE_FrekansAlt`, `XE_FrekansUst`, `XE_FrekansSure`, `XE_VoltajAlt`, `XE_VoltajUst`, `XE_VoltajSure`, `XE_AkimAlt`, `XE_AkimUst` …+28 |
| `maliyet` | [langt:Maliyet] | [langt:Maliyet Hesap Ayarları] | `XM_T1Fiyat`, `XM_T1GunlukSaat`, `XM_T1YillikGun`, `XM_T2Fiyat`, `XM_T2GunlukSaat`, `XM_T2YillikGun`, `XM_T3Fiyat`, `XM_T3GunlukSaat` …+1 |
| `hmikullanici` | [langt:HMI Güvenlik] |  | — |
| `seviye_kontrol` | [langt:Seviye Kontrol] | [langt:Seviye Şamandıra Kontrol] | `XC_SevKontStart`, `XC_SevKontStop`, `XC_SevKontBekleme` |
| `depo?sel=Cikis` | [langt:Çıkış Depo Ayr.] |  | — |
| `depo_doldurma` | [langt:Depo Doldurma] |  | — |
| `hidrofor_mod_ayar` | [langt:Hid. Mod Ayr.] |  | — |
| `haberlesme` | [langt:Haberleşme] |  | — |
| `surucu` | [langt:Sürücü] |  | — |
| `act_settings` | [langt:Act Ayar] |  | — |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoru`, `BasincSensoru2`
- **Debi**: `Debimetre`
- **Seviye / uzunluk (m/cm)**: `-Link1_DepoSeviye`, `StatikSeviye`, `SuSeviye`, `XD_BasmaYukseklik`, `XD_CikisDepoYukseklik`, `toplamHm`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
