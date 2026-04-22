---
name: nview-a-terfi-p
description: |
  nView 'a-terfi-p' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-terfi-p" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, Debimetre, a-terfi-p.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-terfi-p

Aile bağlamı: **terfi.md (terfi istasyonu)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `BasincSensoru` | Çıkış basıncı | bar | 2 | measurement | langt=Basınç; (div) |
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 2 | measurement | langt=Debi; (div) |
| `An_Guc` | Anlık elektrik/motor ölçümü | kW | 2 | instant_electrical | langt=Sistem Güç; (div) |
| `An_InvFrekans` | Anlık elektrik/motor ölçümü | Hz | 1 | instant_electrical | langt=Çıkış; (div) |
| `An_L1Akim` | L1 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L1Voltaj` | L1 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L2Akim` | L2 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L2Voltaj` | L2 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L3Akim` | L3 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L3Voltaj` | L3 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_SebFrekans` | Anlık elektrik/motor ölçümü | Hz | 1 | instant_electrical | langt=Giriş Fr.; (div) |
| `T_ElektrikSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | kWh |  | counter | langt=Elektrik Sayacı; (div) |
| `T_SuSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³/h |  | counter | langt=Su Sayacı; (div) |
| `-Link1_DepoSeviye` |  | m | 2 | unknown |  |
| `DepoSeviye` |  | m | 2 | unknown |  |
| `DisOrtamSicaklik` | Dış ortam sıcaklığı | &#8451; | 2 | measurement | langt=Dış Ortam Sıcaklığı; (div) |
| `eDepoAmount` | [langt:Su Miktarı] | m³ |  | unknown | (div) |
| `eDepoBlank` | [langt:Boş] | m³ |  | unknown | (div) |
| `eDepoCap` | [langt:Depo Kapasitesi] | m³ |  | unknown | (div) |
| `eHm` | [langt:Toplam hm] | m |  | unknown | (div) |
| `eNetGuc` | [langt:P1 Güç] | kW | 2 | unknown | (div) |
| `enHidrolik` | [langt:Hidrolik Verim] | % |  | unknown | (div) |
| `enSistem` | [langt:Sistem Verim] | % |  | unknown | (div) |
| `M3Maliyet` | (m³) |  |  | unknown | langt=Birim Maliyet; (div) |
| `MotorSicaklik` | Motor sıcaklığı | &#8451; | 2 | measurement | langt=Motor Sıcaklığı; (div) |
| `PanoSicaklik` | Pano sıcaklığı | &#8451; | 2 | measurement | langt=Pano Sıcaklığı; (div) |
| `Pompa1Vana` | 1 |  |  | unknown | langt=Pompa; (div) |
| `Pompa2Vana` | 2 |  |  | unknown | langt=Pompa; (div) |
| `Pompa3Vana` | 3 |  |  | unknown | langt=Pompa; (div) |
| `Pompa4Vana` | 4 |  |  | unknown | langt=Pompa; (div) |
| `SuSicaklik` | Su sıcaklığı | &#8451; | 2 | measurement | langt=Su Sıcaklığı; (div) |
| `XGunMaliyet` | <r></r> |  |  | unknown | langt=Günlük Toplam Maliyet; (div) |
| `XD_Depo1Yukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting | langt=Yükseklik |
| `XD_DepoXYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **dimension_setting**: `XD_DepoBoy`, `XD_DepoEn`
- **install_constant**: `XV_KabloKayip`, `XV_Nmotor`, `XV_Nsurtunme`, `XV_SurucuKayip`
- **unknown**: `DepoUstSeviyeBilgisi`, `GirisBasincSensoru`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `sayaclar` | [langt:Sayaçlar] |  | — |
| `maliyetdetay` | [langt:Maliyet Detay] |  | — |
| `pompaverim` | [langt:Pompa Verimi] |  | — |
| `sabitleme` | [langt:Sabitleme] | [langt:Çalışma Ayarları] | `XC_SabitModBasinc`, `XC_SabitModDebi`, `XC_SabitModGuc`, `XC_SabitModFrekans` |
| `sistem` | [langt:Sistem] |  | — |
| `pid` | [langt:PID] |  | — |
| `sensor` | [langt:Sensör] |  | — |
| `debimetre` | [langt:Debimetre] | [langt:Debimetre Ayarları] | `XS_DebiMax`, `XS_DMetrePuls` |
| `progcalisma` | [langt:Prog.Çalışma] |  | — |
| `emniyet` | [langt:Emniyet] | [langt:Emniyet Ayarları] | `XE_FrekansAlt`, `XE_FrekansUst`, `XE_FrekansSure`, `XE_VoltajAlt`, `XE_VoltajUst`, `XE_VoltajSure`, `XE_AkimAlt`, `XE_AkimUst` …+27 |
| `maliyet` | [langt:Maliyet] |  | — |
| `hmikullanici` | [langt:HMI Güvenlik] |  | — |
| `depo_ayar` | [langt:Giriş Depo Ayr.] |  | — |
| `depo_doldurma` | [langt:Depo Doldurma] |  | — |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoru`
- **Debi**: `Debimetre`, `T_SuSayac`
- **Seviye / uzunluk (m/cm)**: `-Link1_DepoSeviye`, `DepoSeviye`, `XD_Depo1Yukseklik`, `XD_DepoXYukseklik`, `eHm`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
