---
name: nview-a-terfi-p-v3
description: |
  nView 'a-terfi-p-v3' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-terfi-p-v3" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, Debimetre, a-terfi-p-v3.
version: "1.0.0"
generated: true
source: //10.10.10.72/public/dev.korubin/app/views/point/display/common/a-terfi-p-v3/GENEL.phtml
---

# nView: a-terfi-p-v3

Aile bağlamı: **terfi.md (terfi istasyonu)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `BasincSensoru` | Çıkış basıncı | bar | 2 | measurement | (div) |
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 2 | measurement | (div) |
| `An_Guc` | Anlık elektrik/motor ölçümü | kW | 2 | instant_electrical | (div) |
| `An_InvFrekans` | Anlık elektrik/motor ölçümü | Hz | 2 | instant_electrical | (div) |
| `An_L1Voltaj` | Anlık elektrik/motor ölçümü | V | 2 | instant_electrical | (div) |
| `An_L2Akim` | Anlık elektrik/motor ölçümü | A | 2 | instant_electrical | (div) |
| `An_L2Voltaj` | Anlık elektrik/motor ölçümü | V | 2 | instant_electrical | (div) |
| `An_L3Akim` | Anlık elektrik/motor ölçümü | A | 2 | instant_electrical | (div) |
| `An_L3Voltaj` | Anlık elektrik/motor ölçümü | V | 2 | instant_electrical | (div) |
| `An_SebFrekans` | Anlık elektrik/motor ölçümü | Hz | 2 | instant_electrical | (div) |
| `T_SuSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³/h |  | counter | (div) |
| `-Link1_DepoSeviye` |  |  | 2 | unknown |  |
| `depoBilgi` |  | m³ |  | unknown | (div) |
| `DepoSeviye` |  |  | 2 | unknown |  |
| `DisOrtamSicaklik` | Dış ortam sıcaklığı | &#8451; | 2 | measurement | (div) |
| `durum` |  | bar |  | unknown | (div) |
| `DurumSag` | Durum / mod göstergesi |  |  | status | (div) |
| `eDepoAmount` |  | m³ |  | unknown | (div) |
| `eDepoBlank` |  | m³ |  | unknown | (div) |
| `eNetGuc` |  | kW |  | unknown | (div) |
| `enHidrolik` |  | % |  | unknown | (div) |
| `enSistem` |  | % |  | unknown | (div) |
| `ortadurum` |  | A |  | unknown | (div) |
| `PanoSicaklik` | Pano sıcaklığı | &#8451; | 2 | measurement | (div) |
| `sayaclargr` |  | kWh |  | unknown | (div) |
| `sicaklikInfo` |  | &#8451; |  | unknown | (div) |
| `suSeviyeInfo` |  | m |  | unknown | (div) |
| `SuSicaklik` | Su sıcaklığı | &#8451; | 2 | measurement | (div) |
| `verimBilgi` |  | m |  | unknown | (div) |
| `XGunMaliyet` |  |  |  | unknown | (div) |
| `XD_Depo1Yukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting | (div) |
| `XD_DepoXYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting | (div) |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **dimension_setting**: `XD_DepoBoy`, `XD_DepoEn`
- **install_constant**: `XV_KabloKayip`, `XV_Nmotor`, `XV_Nsurtunme`, `XV_SurucuKayip`
- **unknown**: `DepoUstSeviyeBilgisi`, `GirisBasincSensoru`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `sayaclar` | [langt:Sayaçlar] | [langt:Sayaçlar] | — |
| `maliyetdetay` | [langt:Maliyet Detay] | [langt:Maliyet Hesap Detayları] | — |
| `pompaverim` | [langt:Pompa Verimi] | [langt:Pompa Verimi] | `XV_Nsurtunme`, `XV_Nmotor`, `XV_SurucuKayip`, `XV_KabloKayip` |
| `calismamod` | [langt:Çalışma Mod] | [langt:Çalışma Ayarları] | `XC_SabitModBasinc`, `XC_SabitModDebi`, `XC_SabitModSeviye`, `XC_SabitModGuc`, `XC_SabitModFrekans` |
| `sistem` | [langt:Sistem] | [langt:Sistem Ayarları] | `XD_BasmaYukseklik`, `XZ_Saat`, `XZ_Dk`, `XZ_Sn`, `XZ_Gun`, `XZ_Ay`, `XZ_Yil` |
| `pid` | PID | [langt:PID Ayarları] | `XC_BasincPIDKP`, `XC_BasincPIDKI`, `XC_BasincPIDKD`, `XC_DebiPIDKP`, `XC_DebiPIDKI`, `XC_DebiPIDKD`, `XC_GucPIDKP`, `XC_GucPIDKI` …+4 |
| `sensor` | [langt:Sensör] | [langt:Sensör Ayarları] | `XS_BasincMax`, `XS_CikisDepoSeviyeMax`, `XS_GirisBasincMax`, `XS_GirisBasincMin`, `XS_GirisBasincKalibre`, `XE_FanCalisSic`, `XE_IsiticiCalisSic`, `XS_SuSicKalibre` …+5 |
| `debimetre` | [langt:Debimetre] | [langt:Debimetre Ayarları] | `XS_DebiMax` |
| `progcalisma` | [langt:Prog.Çalışma] | [langt:Programlı Çalışma Ayarları] | `XP_1BasSaat`, `XP_1BasDk`, `XP_1BitSaat`, `XP_1BitDk`, `XP_2BasSaat`, `XP_2BasDk`, `XP_2BitSaat`, `XP_2BitDk` |
| `emniyet` | [langt:Emniyet] | [langt:Emniyet Ayarları] | `XE_FrekansAlt`, `XE_FrekansUst`, `XE_FrekansSure`, `XE_VoltajAlt`, `XE_VoltajUst`, `XE_VoltajSure`, `XE_AkimAlt`, `XE_AkimUst` …+27 |
| `maliyet` | [langt:Maliyet] | [langt:Maliyet Hesap Ayarları] | `XM_T1Fiyat`, `XM_T1GunlukSaat`, `XM_T1YillikGun`, `XM_T2Fiyat`, `XM_T2GunlukSaat`, `XM_T2YillikGun`, `XM_T3Fiyat`, `XM_T3GunlukSaat` …+1 |
| `hmikullanici` | [langt:HMI Güvenlik] |  | — |
| `depo_ayar` | [langt:Giriş Depo Ayr.] | [langt:Depo Ayarları] | `XD_Depo1Yukseklik`, `XD_DepoEn`, `XD_DepoBoy` |
| `depo_doldurma` | [langt:Depo Doldurma] | [langt:Depo Doldurma Ayarları] | `XD_DepoXYukseklik`, `XD_DepoAlt`, `XD_DepoUst`, `XD_DepoKritikAlt`, `XD_DepoKritikUst` |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoru`, `durum`
- **Debi**: `Debimetre`, `T_SuSayac`
- **Seviye / uzunluk (m/cm)**: `XD_Depo1Yukseklik`, `XD_DepoXYukseklik`, `suSeviyeInfo`, `verimBilgi`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
