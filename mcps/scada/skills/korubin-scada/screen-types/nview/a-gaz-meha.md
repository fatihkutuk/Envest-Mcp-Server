---
name: nview-a-gaz-meha
description: |
  nView 'a-gaz-meha' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-gaz-meha" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: Debimetre, StatikSeviye, a-gaz-meha.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-gaz-meha

Aile bağlamı: **system.md (genel)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `Debimetre` | Debi ölçümü (m³/h) | m3/h | 2 | measurement |  |
| `StatikSeviye` | St.Sv. | m | 2 | measurement | Statik su seviyesi |
| `An_Guc_P1` | Anlık elektrik/motor ölçümü | kw | 1 | instant_electrical | langt=Güç; (col) |
| `An_Guc_P2` | Anlık elektrik/motor ölçümü | kw | 1 | instant_electrical | langt=Güç; (col) |
| `An_Guc_P3` | Anlık elektrik/motor ölçümü | kw | 1 | instant_electrical | langt=Güç; (col) |
| `An_GucFaktoru_P1` | Anlık elektrik/motor ölçümü |  | 1 | instant_electrical | langt=Cos Q; (col) |
| `An_GucFaktoru_P2` | Anlık elektrik/motor ölçümü |  | 1 | instant_electrical | langt=Cos Q; (col) |
| `An_GucFaktoru_P3` | Anlık elektrik/motor ölçümü |  | 1 | instant_electrical | langt=Cos Q; (col) |
| `An_L1Akim_P1` | L1 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L1Akim_P2` | L1 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L1Akim_P3` | L1 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L1Voltaj_P1` | L1 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L1Voltaj_P2` | L1 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L1Voltaj_P3` | L1 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Akim_P1` | L2 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Akim_P2` | L2 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Akim_P3` | L2 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Voltaj_P1` | L2 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Voltaj_P2` | L2 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Voltaj_P3` | L2 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Akim_P1` | L3 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Akim_P2` | L3 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Akim_P3` | L3 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Voltaj_P1` | L3 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Voltaj_P2` | L3 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Voltaj_P3` | L3 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_SebFrekans_P1` | Anlık elektrik/motor ölçümü | hz | 1 | instant_electrical | langt=Şebeke Frek.; (col) |
| `An_SebFrekans_P2` | Anlık elektrik/motor ölçümü | hz | 1 | instant_electrical | langt=Şebeke Frek.; (col) |
| `An_SebFrekans_P3` | Anlık elektrik/motor ölçümü | hz | 1 | instant_electrical | langt=Şebeke Frek.; (col) |
| `AktifEnerji_P1` | Elektrik Sayaç | kwh | 1 | unknown | (col) |
| `AktifEnerji_P2` | Elektrik Sayaç | kwh | 1 | unknown | (col) |
| `AktifEnerji_P3` | Elektrik Sayaç | kwh | 1 | unknown | (col) |
| `bilgi1` | L1 | V |  | unknown | (div) |
| `bilgi2` | L1 | V |  | unknown | (div) |
| `bilgi3` | L1 | V |  | unknown | (div) |
| `CikisBasincSensoru` |  | bar | 2 | unknown |  |
| `CikisKollektorBasinc` |  | bar | 2 | unknown |  |
| `DalgicFrekansBilgi` | [langt:Çıkış Frek.] | hz | 1 | unknown | (col) |
| `DinamikSeviye` | Dn.Sv. | m | 2 | measurement | Dinamik seviye |
| `DozajlamaBilgi` |  |  | 2 | unknown | (div) |
| `DozajPompaStartStopDurumu` | Durum / mod göstergesi |  | 2 | status | langt=Dozaj Durum; (div) |
| `DozajTablo` | Dozaj Çalışma Durum |  |  | unknown | (div) |
| `esanjorbasinc` |  | bar | 2 | unknown |  |
| `esanjorsicaklik` |  | °C | 2 | unknown |  |
| `GirisKollektorBasinc` |  | bar | 2 | unknown |  |
| `HidrolikVerim_P1` | [langt:hydraulic-efficiency] | % | 2 | unknown | (col) |
| `HidrolikVerim_P2` | [langt:hydraulic-efficiency] | % | 2 | unknown | (col) |
| `HidrolikVerim_P3` | [langt:hydraulic-efficiency] | % | 2 | unknown | (col) |
| `Kalorimetre` |  |  | 2 | unknown | (div) |
| `KollektorSicaklik` |  | °C | 2 | unknown |  |
| `KuyuCikisSicaklik` |  | °C | 2 | unknown |  |
| `m3Maliyet_P1` | [langt:unit-cost] | ₺/m³ | 2 | unknown | (col) |
| `m3Maliyet_P2` | [langt:unit-cost] | ₺/m³ | 2 | unknown | (col) |
| `m3Maliyet_P3` | [langt:unit-cost] | ₺/m³ | 2 | unknown | (col) |
| `OrtamSicaklik` | [langt:Dış Ortam Sıcaklığı] | °C | 2 | unknown | (div) |
| `P1_Guc_P1` | P1 | kWh | 2 | pump_measurement | Pompa bazlı ölçüm; langt=Güç; (col) |
| `P1_Guc_P2` | P1 | kWh | 2 | pump_measurement | Pompa bazlı ölçüm; langt=Güç; (col) |
| `P1_Guc_P3` | P1 | kWh | 2 | pump_measurement | Pompa bazlı ölçüm; langt=Güç; (col) |
| `Pano2Sicakllik` | [langt:Pano-2 Sıcaklığı] | °C | 2 | unknown | (div) |
| `Pano3Sicakllik` | [langt:Pano-3 Sıcaklığı] | °C | 2 | unknown | (div) |
| `PompaNPSH` | [langt:NPSH] | m | 2 | unknown |  |
| `reenjeksiyondinamik` | Dn.Sv. | m | 2 | unknown |  |
| `reenjeksiyonstatik` | St.Sv. | m | 2 | unknown |  |
| `SeperatorAltBasinc` |  | bar | 2 | unknown |  |
| `SeperatorCikisSicaklik` |  | C° | 2 | unknown |  |
| `SeperatorSeviye` |  | m | 2 | unknown |  |
| `SeperatorUstBasinc` |  | bar | 2 | unknown |  |
| `SicaklikTablo` | [langt:Pano-1 Sıcaklığı] | °C |  | unknown | (div) |
| `sistemVerim_P1` | [langt:system-efficiency] | % | 2 | unknown | (col) |
| `sistemVerim_P2` | [langt:system-efficiency] | % | 2 | unknown | (col) |
| `sistemVerim_P3` | [langt:system-efficiency] | % | 2 | unknown | (col) |
| `TerfiP1CikisBasinc` |  | bar | 2 | unknown |  |
| `TerfiP1FrekansBilgi` | [langt:Çıkış Frek.] | hz | 1 | unknown | (col) |
| `TerfiP1GirisBasinc` |  | bar | 2 | unknown |  |
| `TerfiP1Sicaklik` | Terfi-1 Sıcaklık | °C | 1 | unknown | (col) |
| `TerfiP2CikisBasinc` |  | bar | 2 | unknown |  |
| `TerfiP2FrekansBilgi` | [langt:Çıkış Frek.] | hz | 1 | unknown | (col) |
| `TerfiP2GirisBasinc` |  | bar | 2 | unknown |  |
| `TerfiP2Sicaklik` | Terfi-2 Sıcaklık | °C | 1 | unknown | (col) |
| `toplamHm_P1` | [langt:total-hm] | m | 2 | unknown | (col) |
| `toplamHm_P2` | [langt:total-hm] | m | 2 | unknown | (col) |
| `toplamHm_P3` | [langt:total-hm] | m | 2 | unknown | (col) |
| `xGunMaliyet_P1` | [langt:total-cost] | TL | 2 | unknown | (col) |
| `xGunMaliyet_P2` | [langt:total-cost] | TL | 2 | unknown | (col) |
| `xGunMaliyet_P3` | [langt:total-cost] | TL | 2 | unknown | (col) |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **alarm**: `Al_DalgicAriza`, `Al_InlineP1Ariza`, `Al_InlineP2Ariza`
- **status**: `DalgicStartStopDurumu`, `Inline1StartStopDurumu`, `Inline2StartStopDurumu`
- **unknown**: `Inline2startstopdurumu`, `P1BakimModu`, `P2BakimModu`, `P3BakimModu`, `actdurum1`, `actdurum2`, `pompa1`, `pompa2`, `pompa_3_`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `sensor` | [langt:Sensör Ayarlar] | [langt:Sensör Ayarları] | `XS_YeraltiSeviyeSensorMontaj`, `XS_YeraltiSeviyePompaMontaj` |
| `analogayar1` | [langt:Analog 1 Ayar] | [langt:Analog Ayarları] | `XS_AIMin01`, `XS_AIMax01`, `XS_AIOffset01`, `XS_AIMin02`, `XS_AIMax02`, `XS_AIOffset02`, `XS_AIMin03`, `XS_AIMax03` …+4 |
| `analogayar2` | [langt:Analog 2 Ayar] | [langt:Analog Ayarları] | `XS_AIMin05`, `XS_AIMax05`, `XS_AIOffset05`, `XS_AIMin06`, `XS_AIMax06`, `XS_AIOffset06`, `XS_AIMin07`, `XS_AIMax07` …+4 |
| `analogayar3` | [langt:Analog 3 Ayar] | [langt:Analog Ayarları] | `XS_AIMin09`, `XS_AIMax09`, `XS_AIOffset09`, `XS_AIMin10`, `XS_AIMax10`, `XS_AIOffset10`, `XS_AIMin11`, `XS_AIMax11` …+4 |
| `analogayar4` | [langt:Analog 4 Ayar] | [langt:Analog Ayarları] | `XS_AIMin13`, `XS_AIMax13`, `XS_AIOffset13`, `XS_AIMin14`, `XS_AIMax14`, `XS_AIOffset14`, `XS_AIMin15`, `XS_AIMax15` …+4 |
| `sicaklik` | [langt:Sıcaklık] | [langt:Sıcaklık-1 Ayarları] | — |
| `dalgic_emniyet` | [langt:Dalgıç Emnniyet] | [langt:Dalgıç Pompa Emniyet Ayarları] | `XE_DalgicVoltajAltLim`, `XE_DalgicVoltajUstLim`, `XE_DalgicVoltajTimeout`, `XE_DalgicAkimAltLim`, `XE_DalgicAkimUstLim`, `XE_DalgicAkimTimeout`, `XE_DalgicGucAltLim`, `XE_DalgicGucUstLim` …+16 |
| `terfip1_emniyet` | [langt:Terfi P1 Emnniyet] | [langt:Terfi P-1 Emniyet Ayarları] | `XE_Inline1VoltajAltLim`, `XE_Inline1VoltajUstLim`, `XE_Inline1VoltajTimeout`, `XE_Inline1AkimAltLim`, `XE_Inline1AkimUstLim`, `XE_Inline1AkimTimeout`, `XE_Inline1GucAltLim`, `XE_Inline1GucUstLim` …+16 |
| `terfip2_emniyet` | [langt:Terfi P2 Emnniyet] | [langt:Terfi P-2 Emniyet Ayarları] | `XE_Inline2VoltajAltLim`, `XE_Inline2VoltajUstLim`, `XE_Inline2VoltajTimeout`, `XE_Inline2AkimAltLim`, `XE_Inline2AkimUstLim`, `XE_Inline2AkimTimeout`, `XE_Inline2GucAltLim`, `XE_Inline2GucUstLim` …+16 |
| `pompa_ayar` | [langt:Çalışma Ayarları] | [langt:Dalgıç Pompa Ayraları ] | `XP_P1SamandiraDurmaSev`, `XP_P1SamandiraCalismaSev`, `XC_SabitModFrekans_P1`, `XP_P2SamandiraDurmaSev`, `XP_P2SamandiraCalismaSev`, `XC_SabitModFrekans_P2`, `XC_SabitSeperatorSeviye_P2`, `XPID_KP_D2` …+13 |
| `surucu` | [langt:Sürücü] | [langt:Dalgıç Sürücü Ayarları] | `XINV_D1SoftMin`, `XINV_D1SoftMax`, `XINV_D1HardMin`, `XINV_D1HardMax`, `XINV_D2SoftMin`, `XINV_D2SoftMax`, `XINV_D2HardMin`, `XINV_D2HardMax` …+4 |
| `calisma_ayar` | [langt:Çalışma] | [langt:Depo Ayarları ] | `XD_Seviye1Stop`, `XD_Seviye1Start`, `XD_Seviye2Stop`, `XD_Seviye2Start`, `XD_Seviye3Stop`, `XD_Seviye3Start`, `XD_Depo1Yukseklik`, `XD_Depo1En` …+1 |
| `verim` | [langt:Pompa Verim] | [langt:Kuyu Verimi] | `XV_BoruPuruzKatsayi_P1`, `XV_BoruUzunluk_P1`, `XV_BoruIcCap_P1`, `XV_SurucuKaybi_P1`, `XV_KabloKaybi_P1`, `XV_SurtunmeKatsayisi_P1`, `XV_MotorVerim_P1`, `P1Guc_P1` …+18 |
| `maliyet` | [langt:Maliyet Ayar] | [langt:Kuyu Maliyet Hesap Ayarları] | `XM_T1Fiyat_P1`, `XM_T1GunlukSaat_P1`, `XM_T1YillikGun_P1`, `XM_T2Fiyat_P1`, `XM_T2GunlukSaat_P1`, `XM_T2YillikGun_P1`, `XM_T3Fiyat_P1`, `XM_T3GunlukSaat_P1` …+19 |
| `maliyetdetay` | [langt:Maliyet Detay] | [langt:Kuyu Maliyet Hesapları] | — |
| `pump` | [langt:pump-data] | Pompa Bilgileri | — |
| `yeralti` | [langt:Yeraltı Sensör] | Yeraltı Seviye Sensörü <span style="color:rgb(153, 0, 0);" id="kanal1Toggle"> </span> | `XS_YeraltiSeviyeSensorMontaj`, `XS_YeraltiSeviyePompaMontaj`, `XS_StatikSeviyeGuncellemeTimeout`, `XS_DinamikSeviyeGuncellemeTimeout` |
| `inhibitor` | [langt:İnhibitör] | [langt:Sensör Ayarları] | `XK_ManuelDozaj`, `XK_Birm3Dozlama`, `InhibitorRange` |
| `kalibreayarlari` | [langt:Sıcaklık Kalibre] | Kalibre Ayarları <span style="color:rgb(153, 0, 0);" id="kanal1Toggle"> </span> | `Sic01Offset`, `Sic02Offset`, `Sic03Offset`, `Sic04Offset`, `Sic05Offset`, `Sic06Offset`, `Sic07Offset`, `Sic08Offset` …+4 |
| `bakimayar` | [langt:Bakım Ayarları] | BAKIM MODU | — |

## Birim Özeti

- **Basınç (bar)**: `CikisBasincSensoru`, `CikisKollektorBasinc`, `GirisKollektorBasinc`, `SeperatorAltBasinc`, `SeperatorUstBasinc`, `TerfiP1CikisBasinc`, `TerfiP1GirisBasinc`, `TerfiP2CikisBasinc`, `TerfiP2GirisBasinc`, `esanjorbasinc`
- **Debi**: `Debimetre`
- **Seviye / uzunluk (m/cm)**: `DinamikSeviye`, `PompaNPSH`, `SeperatorSeviye`, `StatikSeviye`, `reenjeksiyondinamik`, `reenjeksiyonstatik`, `toplamHm_P1`, `toplamHm_P2`, `toplamHm_P3`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
