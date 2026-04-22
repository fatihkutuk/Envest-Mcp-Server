---
name: nview-a-aqua-cnt-kuyu-v2
description: |
  nView 'a-aqua-cnt-kuyu-v2' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-aqua-cnt-kuyu-v2" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, Debimetre, StatikSeviye, SuSeviye, a-aqua-cnt-kuyu-v2.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-aqua-cnt-kuyu-v2

Aile bağlamı: **kuyu.md (canlı tag + SP serisi dalgıç pompa)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `BasincSensoru` | Çıkış basıncı | bar | 2 | measurement |  |
| `BasincSensoru2` | Hat basıncı | bar | 2 | measurement |  |
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 1 | measurement |  |
| `StatikSeviye` | Statik Seviye | m | 2 | measurement | Statik su seviyesi |
| `SuSeviye` | Dinamik Seviye | m | 2 | measurement | Dinamik su seviyesi |
| `An_Guc` | Anlık elektrik/motor ölçümü | kWh | 1 | instant_electrical | langt=system-power; (col) |
| `An_GucFaktoru` | Anlık elektrik/motor ölçümü | % | 3 | instant_electrical | langt=power-factor; (col) |
| `An_L1Akim` | L1 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L1Voltaj` | L1 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Akim` | L2 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L2Voltaj` | L2 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Akim` | L3 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_L3Voltaj` | L3 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_OrtAkim` | Anlık elektrik/motor ölçümü | A | 1 | instant_electrical | langt=average-current; (col) |
| `An_OrtVoltaj` | Ort. Voltaj | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (col) |
| `An_SebFrekans` | Anlık elektrik/motor ölçümü | Hz | 1 | instant_electrical | langt=input; (col) |
| `T_ElektrikReakInduSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | kVAR | 2 | counter | langt=reactive; (div) |
| `T_ElektrikSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | kW/h | 2 | counter | langt=electricity-meter; (div) |
| `T_SuSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=water-meter; (div) |
| `BeslemeVoltaj` | <ico class="battery"></ico> | V | 2 | unknown | langt=supply-voltage; (div) |
| `CikisDepoSeviye` | Çıkış deposu seviyesi | m | 2 | measurement |  |
| `CikisDepoSeviyePercent` |  | % | 2 | unknown |  |
| `Debimetre2` | Debi ölçümü 2 | m³/h | 1 | measurement |  |
| `depokot` | Depo Kotu | m | 0 | measurement | Depo kotu (altitude) |
| `eNetGuc` | [langt:p1-power] | kW | 2 | unknown | (col) |
| `hidrolikVerim` | [langt:hydraulic-efficiency] | % | 2 | unknown | (div) |
| `kuyukot` | Kuyu Kotu | m | 0 | measurement | Kuyu kotu (altitude) |
| `m3Maliyet` | [langt:unit-cost] | ₺/m³ | 2 | unknown | (div) |
| `NPSHSeviye` | NPSH seviye | m | 2 | measurement | langt=NPSH Seviye |
| `P1_Verim` | P1 | kWh | 2 | pump_measurement | Pompa bazlı ölçüm; langt=efficiency; (div) |
| `PilSeviye` | <ico class="battery"></ico> | % | 2 | unknown | langt=battery-status; (div) |
| `PilSicaklik` | <ico class="battery"></ico> | °C | 2 | unknown | langt=battery-temperature; (div) |
| `sistemVerim` | [langt:system-efficiency] | % | 2 | unknown | (div) |
| `toplamHmjs` | [langt:total-hm] | m | 2 | unknown | (div) |
| `txt_CikisDepo` |  |  | 2 | unknown |  |
| `xGunMaliyet` | [langt:total-cost] | TL<b></b> | 2 | unknown | (div) |
| `XD_BasmaYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 1 | dimension_setting |  |
| `XD_CikisDepoYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |
| `XC_AnalogCikisTwo` | Çalışma modu / mod seçim | Hz | 2 | operating_mode | langt=analog-output; (col) |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **alarm**: `Al_DozajPompasiAriza`, `Al_Surucu`
- **measurement**: `Pompa1StartStopDurumu`, `ToplamHm`
- **operating_mode**: `XC_AnalogCikis`, `XC_CalismaModu`
- **sensor_setpoint**: `XS_Basinc2GirisSecim`, `XS_Debimetre2GirisSecim`, `XS_MontajSev`
- **status**: `ACT_1_Durum`, `ACT_Durum`, `AntiBlokajDurum`
- **unknown**: `XINV_HardMaxLimit`, `XM_T1Fiyat`, `XM_T1GunlukSaat`, `XM_T1YillikGun`, `XM_T2Fiyat`, `XM_T2GunlukSaat`, `XM_T2YillikGun`, `XM_T3Fiyat`, `XM_T3GunlukSaat`, `XM_T3YillikGun`, `XVN_ACTAktif`, `YaklasikHidrolikVerim`, `length`, `pVal`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `analogCikis` | [langt:analog-output] |  | — |
| `dijitalGirisCikis` | [langt:digital-in-out] |  | — |
| `sensor` | [langt:sensor] |  | — |
| `calismaMod` | [langt:operation-mode] | [langt:automatic-operation-mode-settings] | `XD_MinSuBasinc`, `XD_MaxSuBasinc`, `XC_BasincPiSet`, `XZ_BasincPiSn`, `XC_BasincPiSet`, `XZ_BasincPiSn` |
| `arayuz` | [langt:Arayüz] | [langt:Tank] | — |
| `pompaverim` | [langt:pump-efficiency] | [langt:Akıllı Pompa Seçimi] | — |
| `pump` | [langt:pump-data] |  | — |
| `motor` | [langt:motor-settings] |  | — |
| `depoDoldurma` | [langt:reservoir-filling-mode] |  | — |
| `emniyet` | [langt:safety-settings] |  | — |
| `sayac` | [langt:counter-settings] |  | — |
| `log` | [langt:device-log] |  | — |
| `cihaz_uyari` | [langt:device-warning] |  | — |
| `depoAyar` | [langt:reservoir-settings] | [langt:well-settings] | — |
| `maliyet` | [langt:cost] |  | — |
| `maliyetdetay` | [langt:cost-details] |  | — |
| `pumpclustring` | [langt:Pump-clustering] |  | — |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoru`, `BasincSensoru2`
- **Debi**: `Debimetre`, `Debimetre2`
- **Seviye / uzunluk (m/cm)**: `CikisDepoSeviye`, `NPSHSeviye`, `StatikSeviye`, `SuSeviye`, `XD_BasmaYukseklik`, `XD_CikisDepoYukseklik`, `depokot`, `kuyukot`, `toplamHmjs`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
