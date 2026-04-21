---
name: nview-a-aqua-mini-kuyu-v1.0
description: |
  nView 'a-aqua-mini-kuyu-v1.0' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-aqua-mini-kuyu-v1.0" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, Debimetre, SuSeviye, a-aqua-mini-kuyu-v1.0.
version: "1.0.0"
generated: true
source: //10.10.10.72/public/dev.korubin/app/views/point/display/common/a-aqua-mini-kuyu-v1.0/GENEL.phtml
---

# nView: a-aqua-mini-kuyu-v1.0

Aile bağlamı: **kuyu.md (canlı tag + SP serisi dalgıç pompa)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `BasincSensoru` | Çıkış basıncı | bar | 2 | measurement |  |
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 1 | measurement |  |
| `SuSeviye` | Dinamik su seviyesi | m | 2 | measurement |  |
| `T_SuSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Su Sayacı; (div) |
| `T_SuSayacLORA` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Su Sayacı; (div) |
| `BeslemeVoltaj` | <ico class="battery"></ico> | V | 2 | unknown | langt=Besleme Voltajı; (div) |
| `DepoSeviye` |  | m | 2 | unknown |  |
| `GirisBasincSensoru` |  | bar | 2 | unknown |  |
| `GSMCekimGucu` | [langt:GSM Çekim Gücü] |  | 2 | unknown | (div) |
| `LORAAin1` | [langt:LORAAin1] |  | 2 | unknown | (div) |
| `LORAAin2` | [langt:LORAAin2] |  | 2 | unknown | (div) |
| `LORABasincSensoru` | [langt:Basınç] | bar | 2 | unknown | (div) |
| `LORABeslemeVoltaji` | <ico class="battery"></ico> | V | 2 | unknown | langt=(Lora) Besleme Voltajı; (div) |
| `LORACekimGucu` | [langt:Lora Çekim Gücü] | % | 2 | unknown | (div) |
| `LORADebimetre` | [langt:Debimetre] | m³ | 2 | unknown | (div) |
| `LORAPilSeviye` | <ico class="battery"></ico> | % | 2 | unknown | langt=(Lora) Pil Durumu; (div) |
| `LORAPilSicaklik` | <ico class="battery"></ico> | °C | 2 | unknown | langt= (LoraPil) Sıcaklık; (div) |
| `LORASuSeviye` | [langt:Su Seviye] | m | 2 | unknown | (div) |
| `PilSeviye` | <ico class="battery"></ico> | % | 2 | unknown | langt=Pil Durumu; (div) |
| `PilSicaklik` | <ico class="battery"></ico> | °C | 2 | unknown | langt=Pil Sıcaklık; (div) |
| `storeAmount` |  | m³ | 2 | unknown |  |
| `txt_CikisDepo` |  |  | 2 | unknown |  |
| `XD_BasmaYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |
| `XD_CikisDepoYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **dimension_setting**: `XD_GirisDepoBoy`, `XD_GirisDepoEn`, `XD_GirisDepoYukseklik`
- **install_constant**: `XV_KabloKayip`, `XV_SurucuKayip`
- **instant_electrical**: `An_Guc`
- **measurement**: `Pompa1StartStopDurumu`, `ToplamHm`
- **status**: `ACT_1_Durum`
- **unknown**: `XVN_ACTAktif`, `YaklasikHidrolikVerim`, `emisyukseklik`, `length`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `dijitalGirisCikis` | [langt:Dijital Giriş Çıkış] | [langt:Dijital Giriş] | — |
| `sensor` | [langt:Sensör] | <a href="javascript:void(0)" id="basincToggle"><ico id="basincIkon" class="down"></ico></a> | `XS_BasincSet`, `BasincSensoru`, `XS_SeviyeSet`, `SuSeviye`, `XS_DebiSet`, `Debimetre`, `Ain1`, `Ain2` |
| `calismaMod` | [langt:Çalışma Modu] | [langt:Otomatik Çalışma Modu Ayarları] | `XS_MinSuBasinc`, `XS_MaxSuBasinc`, `AntiblokajDurmaSure`, `AntiblokajCalismaSure` |
| `pompaverim` | [langt:Pompa Verimi] | [langt:Pompa Seçimi] | — |
| `pump` | [langt:Pompa Bilgileri] | Pompa Bilgileri | — |
| `motor` | [langt:Motor Ayarları] | [langt:Motor Çıkış Seçimi (Mutlaka Seçiniz)] | — |
| `depoDoldurma` | [langt:Depo Doldurma] | <a href="javascript:void(0)" id="parametreToggle"> <ico id="parametreIkon" class="down"></ico> </a> | `XH_HedefBeslemeMinSuSeviye`, `XH_HedefBeslemeMaxSuSeviye` |
| `hidrofor` | [langt:Hidrofor Ayarları] | [langt:Basınç Parametreleri ] | `XHID_BasincCalismaP1`, `XHID_BasincCalismaP2`, `XHID_BasincCalismaP3`, `XHID_BasincDurma` |
| `emniyet` | [langt:Emniyet Ayarları] | <a href="javascript:void(0)" id="seviyeToggle"> <ico id="seviyeIkon" class="down"></ico> </a> | `XE_MotorKorumaSuSeviyeMin`, `XE_MotorKorumaSuSeviyeMax`, `XE_MotorKorumaSuSeviyeZaman`, `XE_MotorKorumaBasincMin`, `XE_MotorKorumaBasincMax`, `XE_MotorKorumaBasincZaman`, `XE_MotorKorumaDebiMin`, `XE_MotorKorumaDebiMax` …+3 |
| `cihaz_uyari` | [langt:Cihaz Uyarı] | [langt:Cihaz Uyarıları] | — |
| `terfiAyar` | [langt:Terfi Ayar] | [langt:Terfi Ayarları] | — |
| `maliyet` | [langt:Maliyet] | [langt:Maliyet Hesap Ayarları] | — |
| `maliyetdetay` | [langt:Maliyet Detay] | [langt:Maliyet Hesap Detayları] | — |
| `dijitalGirisCikislora` | [langt:Dijital Giriş Çıkış] | [langt:Dijital Giriş] | — |
| `sensorlora` | [langt:Sensör] | <a href="javascript:void(0)" id="basincToggle"><ico id="basincIkon" class="down"></ico></a> | `XR_LORABasincSet`, `LORABasincSensoru`, `XR_LORASeviyeSet`, `LORASuSeviye`, `XR_LORADebiSet`, `LORADebimetre` |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoru`, `GirisBasincSensoru`, `LORABasincSensoru`
- **Debi**: `Debimetre`
- **Seviye / uzunluk (m/cm)**: `DepoSeviye`, `LORASuSeviye`, `SuSeviye`, `XD_BasmaYukseklik`, `XD_CikisDepoYukseklik`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
