---
name: nview-a-aqua-cnt-terfi-v2-3b
description: |
  nView 'a-aqua-cnt-terfi-v2-3b' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-aqua-cnt-terfi-v2-3b" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, Debimetre, a-aqua-cnt-terfi-v2-3b.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-aqua-cnt-terfi-v2-3b

Aile bağlamı: **terfi.md (terfi istasyonu)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `BasincSensoru` | Çıkış basıncı | bar | 2 | measurement |  |
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 1 | measurement |  |
| `An_Guc` | Anlık elektrik/motor ölçümü | kWh | 1 | instant_electrical | langt=Sistem Güç; (col) |
| `An_GucFaktoru` | Anlık elektrik/motor ölçümü | % | 3 | instant_electrical | langt=Güç Faktörü; (col) |
| `An_L1Akim` | L1 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L1Voltaj` | L1 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Akim` | L2 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Voltaj` | L2 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Akim` | L3 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Voltaj` | L3 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_OrtAkim` | Ort. Akım | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_SebFrekans` | Anlık elektrik/motor ölçümü | Hz | 1 | instant_electrical | langt=Giriş; (col) |
| `T_ElektrikReakInduSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | kVAR | 2 | counter | langt=Reaktif; (div) |
| `T_ElektrikSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | kW/h | 2 | counter | langt=Elektrik Sayacı; (div) |
| `T_SuSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Su Sayacı; (div) |
| `BeslemeVoltaj` | <ico class="battery"></ico> | V | 2 | unknown | langt=Besleme Voltajı; (div) |
| `CikisDepoSeviye` | Çıkış deposu seviyesi | m | 2 | measurement |  |
| `DepoSeviye` |  | m | 2 | unknown |  |
| `emisyukseklik` |  | m | 2 | unknown |  |
| `eNetGuc` | [langt:P1 Güç] | kW | 2 | unknown | (col) |
| `EstimatedFlow` | Tahmini Debimetre | m³/h | 1 | unknown |  |
| `fonks1` |  |  | 2 | unknown |  |
| `GirisBasincSensoru` |  | bar | 2 | unknown |  |
| `HatBasincSensoru` | Hat basıncı | bar | 2 | measurement |  |
| `hidrolikVerim` | [langt:Hidrolik Verim] | % | 2 | unknown | (div) |
| `m3Maliyet` | [langt:Birim Maliyeti] | ₺/m³ | 2 | unknown | (div) |
| `P1_Verim` | Pompa bazlı ölçüm | kWh | 2 | pump_measurement | langt=P1 Verim; (div) |
| `PilSeviye` | <ico class="battery"></ico> | % | 2 | unknown | langt=Pil Durumu; (div) |
| `PilSicaklik` | <ico class="battery"></ico> | °C | 2 | unknown | langt=Pil Sıcaklık; (div) |
| `sistemVerim` | [langt:Sistem Verim] | % | 2 | unknown | (div) |
| `storeAmount` |  | m³ | 2 | unknown |  |
| `toplamHm` | Toplam basma yüksekliği (alias) | m | 2 | measurement | langt=Toplam hm; (div) |
| `txt_CikisDepo` |  |  | 2 | unknown |  |
| `xGunMaliyet` | [langt:Toplam Maliyet] | TL<b></b> | 2 | unknown | (div) |
| `XD_BasmaYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |
| `XD_CikisDepoYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |
| `XD_GirisDepoYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |
| `XC_AnalogCikisTwo` | Çalışma modu / mod seçim | Hz | 2 | operating_mode | langt=Analog Çıkış; (col) |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **alarm**: `Al_DozajPompasiAriza`, `Al_Surucu`
- **dimension_setting**: `XD_GirisDepoBoy`, `XD_GirisDepoEn`
- **install_constant**: `XV_KabloKayip`, `XV_SurucuKayip`
- **measurement**: `Pompa1StartStopDurumu`, `ToplamHm`
- **operating_mode**: `XC_AnalogCikis`
- **status**: `ACT_1_Durum`
- **unknown**: `XINV_HardMaxLimit`, `XVN_ACTAktif`, `YaklasikHidrolikVerim`, `length`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `analogCikis` | [langt:Analog Çıkış] | [langt:analog-output] | `XC_AnalogCikis`, `XINV_HardMaxLimit` |
| `dijitalGirisCikis` | [langt:Dijital Giriş Çıkış] | [langt:Dijital Giriş] | — |
| `sensor` | [langt:Sensör] | <span style="color:rgb(153, 0, 0);" id="montajToggle"><ico id="montajIkon" class="down"></ico></span> | `XS_MontajSev`, `XS_MontajDerinlik`, `NPSHSeviye`, `DepoSeviye`, `DinamikSeviye`, `XS_GirisBasincMax`, `GirisBasincSensoru`, `XS_BasincSensoruMax` …+12 |
| `calismaMod` | [langt:Çalışma Modu] | [langt:automatic-operation-mode-settings] | `XD_MinSuBasinc`, `XD_MaxSuBasinc`, `XC_BasincPiSet`, `XZ_BasincPiSn` |
| `pompaverim` | [langt:Pompa Verimi] | [langt:pump-selection] | — |
| `pump` | [langt:Pompa Bilgileri] | [langt:Pump Data] | — |
| `motor` | [langt:Motor Ayarları] | [langt:motor-output-relay-selection] | — |
| `depoDoldurma` | [langt:Depo Doldurma] | <a href="javascript:void(0)" id="ip1Toggle"> <ico id="ip1Ikon" class="down"></ico> </a> | `XD_HedefDepoIPOktet1`, `XD_HedefDepoIPOktet2`, `XD_HedefDepoIPOktet3`, `XD_HedefDepoIPOktet4`, `XD_HedefDepoModbusAdres`, `XD_HedefDepoModbusId`, `XD_HedefDepoModbusPort`, `XD_HedefMinimumSuSeviye` …+5 |
| `hidrofor` | [langt:Hidrofor Ayarları] | [langt:Basınç Parametreleri ] | `XHID_BasincCalismaP1`, `XHID_BasincCalismaP2`, `XHID_BasincCalismaP3`, `XHID_BasincDurma` |
| `emniyet` | [langt:Emniyet Ayarları] | <a href="javascript:void(0)" id="seviyeToggle"> <ico id="seviyeIkon" class="down"></ico> </a> | `XE_SeviyeAlt`, `XE_SeviyeUst`, `XE_SuSeviyeZaman`, `XE_AkimAlt`, `XE_AkimUst`, `XE_AkimZaman`, `XE_VoltajAlt`, `XE_VoltajUst` …+9 |
| `log` | [langt:Cihaz Log] | [langt:log-settings] | `XL_LogAlmaPeryoduDk`, `LogBlokSayisi`, `LogSayfaSayisi`, `LogSayfaGoster` |
| `cihaz_uyari` | [langt:Cihaz Uyarı] | [langt:device-warning] | — |
| `terfiAyar` | [langt:Terfi Ayar] | [langt:Terfi Ayarları] | — |
| `maliyet` | [langt:Maliyet] | [langt:cost-settings] | — |
| `maliyetdetay` | [langt:Maliyet Detay] | [langt:cost-details] | — |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoru`, `GirisBasincSensoru`, `HatBasincSensoru`
- **Debi**: `Debimetre`, `EstimatedFlow`
- **Seviye / uzunluk (m/cm)**: `CikisDepoSeviye`, `DepoSeviye`, `XD_BasmaYukseklik`, `XD_CikisDepoYukseklik`, `XD_GirisDepoYukseklik`, `emisyukseklik`, `toplamHm`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
