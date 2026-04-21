---
name: nview-a-kuyu-p-v4.1
description: |
  nView 'a-kuyu-p-v4.1' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-kuyu-p-v4.1" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, Debimetre, StatikSeviye, SuSeviye, a-kuyu-p-v4.1.
version: "1.0.0"
generated: true
source: //10.10.10.72/public/dev.korubin/app/views/point/display/common/a-kuyu-p-v4.1/GENEL.phtml
---

# nView: a-kuyu-p-v4.1

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
| `An_InvFrekans` | Anlık elektrik/motor ölçümü | Hz | 1 | instant_electrical | langt=Çıkış; (col) |
| `An_L1Akim` | L1 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L1Voltaj` | L1 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Akim` | L2 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Voltaj` | L2 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Akim` | L3 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Voltaj` | L3 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_SebFrekans` | Anlık elektrik/motor ölçümü | Hz | 1 | instant_electrical | langt=Giriş; (col) |
| `T_CalismaSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | h | 2 | counter | langt=Çalışma Sayacı; (div) |
| `T_ElektrikKalan` | Toplam sayaç (su, elektrik, çalışma, şalt) | kW/h | 2 | counter | langt=Kalan Elektrik Miktarı; (div) |
| `T_ElektrikSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | kW/h | 2 | counter | langt=Elektrik Sayacı; (div) |
| `T_SuKalan` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Kalan Su Miktarı; (div) |
| `T_SuSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Su Sayacı; (div) |
| `-Link1_DepoSeviye` |  | m | 2 | unknown |  |
| `DisOrtamSicaklik` | Dış ortam sıcaklığı | °C | 2 | measurement | langt=Dış Ortam; (div) |
| `eNetGuc` | [langt:P1 Güç] | kW | 2 | unknown | (col) |
| `hidrolikVerim` | [langt:Hidrolik Verim] | % | 2 | unknown | (div) |
| `m3Maliyet` | [langt:Birim Maliyeti] | ₺/m³ | 2 | unknown | (div) |
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
| `tahsis` | [langt:allocation] |  | — |
| `maliyetdetay` | [langt:Maliyet Detay] |  | — |
| `pompaverim` | [langt:Pompa Verimi] |  | — |
| `calismamod` | [langt:Sabitleme] |  | — |
| `sistem` | [langt:Sistem] |  | — |
| `pid` | [langt:PID] |  | — |
| `sensor` | [langt:Sensör] |  | — |
| `blokaj_modu` | [langt:Antiblokaj] |  | — |
| `debimetre` | [langt:Debimetre] |  | — |
| `programtablo` | [langt:Prog.Çalışma] | [langt:Program Tablo] | — |
| `emniyet` | [langt:Emniyet] |  | — |
| `emniyet_reset_ayar` | [langt:Emniyet Reset] | [langt:Emniyet Reset Ayarları] | `XE_OtoAlarmResetSayac`, `XE_OtoAlarmResetSet`, `XE_OtoAlarmResetBeklemeSn`, `XE_OtoAlarmSayacResetlemeSn` |
| `maliyet` | [langt:Maliyet] |  | — |
| `hmikullanici` | [langt:HMI Güvenlik] |  | — |
| `seviye_kontrol` | [langt:Seviye Kontrol] |  | — |
| `depo?sel=Cikis` | [langt:Çıkış Depo Ayr.] |  | — |
| `depo_doldurma` | [langt:Depo Doldurma] | [langt:Depo Doldurma Ayarları] | `XD_CikisDepoYukseklik`, `XD_CikisDepoAlt`, `XD_CikisDepoUst`, `XD_CikisDepoKritikAlt`, `XD_CikisDepoKritikUst` |
| `hidrofor_mod_ayar` | [langt:Hid. Mod Ayr.] | [langt:Hidrofor Modu Ayarları] | `XHID_BasincAlt`, `XHID_BasincUst`, `XHID_DebiMin`, `XHID_DebiKontrolSuresi`, `XHID_FrekansMin`, `XHID_FrekansKontrolSuresi` |
| `haberlesme` | [langt:Haberleşme] | [langt:Sunucu Haberleşmesi Yokken Çalışma Ayarları] | `XH_HabYokCalisma`, `XH_HabYokDurma`, `XH_SunucuHabTimeOut`, `XH_Link1HabTimeOut`, `XH_MasterPLCHabTimeOut` |
| `surucu` | [langt:Sürücü] | [langt:Sürücü Ayarları] | `XINV_HardMaxLimit`, `XINV_SoftMinLimit`, `XINV_SoftMaxLimit` |
| `act_settings` | [langt:Act Ayar] | [langt:Actuator Vana Ayarları] | `XVN_ACTAcmaKontrolSure`, `XVN_ACTKapatmaKontrolSure` |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoru`, `BasincSensoru2`
- **Debi**: `Debimetre`
- **Seviye / uzunluk (m/cm)**: `-Link1_DepoSeviye`, `StatikSeviye`, `SuSeviye`, `XD_BasmaYukseklik`, `XD_CikisDepoYukseklik`, `toplamHm`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
