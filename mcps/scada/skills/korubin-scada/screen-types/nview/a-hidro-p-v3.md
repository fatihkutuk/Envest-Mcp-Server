---
name: nview-a-hidro-p-v3
description: |
  nView 'a-hidro-p-v3' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-hidro-p-v3" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, Debimetre, a-hidro-p-v3.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-hidro-p-v3

Aile bağlamı: **system.md (genel)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `BasincSensoru` | Çıkış basıncı | bar | 2 | measurement |  |
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 2 | measurement |  |
| `An_Guc` | Anlık elektrik/motor ölçümü | kW | 2 | instant_electrical | (div) |
| `An_InvFrekans` | Anlık elektrik/motor ölçümü | Hz | 2 | instant_electrical | (div) |
| `An_L1Voltaj` | Anlık elektrik/motor ölçümü | V | 2 | instant_electrical | (div) |
| `An_L2Akim` | Anlık elektrik/motor ölçümü | A | 2 | instant_electrical | (div) |
| `An_L2Voltaj` | Anlık elektrik/motor ölçümü | V | 2 | instant_electrical | (div) |
| `An_L3Akim` | Anlık elektrik/motor ölçümü | A | 2 | instant_electrical | (div) |
| `An_L3Voltaj` | Anlık elektrik/motor ölçümü | V | 2 | instant_electrical | (div) |
| `An_SebFrekans` | Anlık elektrik/motor ölçümü | Hz | 2 | instant_electrical | (div) |
| `T_CalismaSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) |  |  | counter | (div) |
| `T_SuSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³/h |  | counter | (div) |
| `CikisSicaklik` |  | &#8451; | 2 | unknown |  |
| `depoBilgi` |  | m³ |  | unknown | (div) |
| `DepoSeviye` |  |  | 2 | unknown |  |
| `durum` |  | bar |  | unknown | (div) |
| `DurumSag` | Durum / mod göstergesi |  |  | status | (div) |
| `eDepoAmount` |  | m³ |  | unknown | (div) |
| `eDepoBlank` |  | m³ |  | unknown | (div) |
| `enHidrolik` |  | % |  | unknown | (div) |
| `enSistem` |  | % |  | unknown | (div) |
| `GirisBasincSensoru` |  | bar | 2 | unknown |  |
| `ortadurum` |  | A |  | unknown | (div) |
| `PanoSicaklik` | Pano sıcaklığı | &#8451; | 2 | measurement | (div) |
| `sayaclargr` |  | kWh |  | unknown | (div) |
| `sicaklikInfo` |  | &#8451; |  | unknown | (div) |
| `SuSicaklik` | Su sıcaklığı | &#8451; | 2 | measurement |  |
| `terfiSarici` | [langt:Yükseklik] | m |  | unknown | (div) |
| `verimBilgi` |  | m |  | unknown | (div) |
| `XGunMaliyet` |  |  |  | unknown | (div) |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **dimension_setting**: `XD_Depo1Yukseklik`, `XD_DepoBoy`, `XD_DepoEn`, `XD_DepoUst`
- **install_constant**: `XV_KabloKayip`, `XV_Nmotor`, `XV_Nsurtunme`, `XV_SurucuKayip`
- **unknown**: `DepoUstSeviyeBilgisi`, `Link1_DepoSeviye`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `sayaclar` | [langt:Sayaçlar] |  | — |
| `maliyetdetay` | [langt:Maliyet Detay] |  | — |
| `pompaverim` | [langt:Pompa Verimi] |  | — |
| `calismamod` | [langt:Çalışma Mod] |  | — |
| `sistem` | [langt:Sistem] |  | — |
| `pid` | PID |  | — |
| `sensor` | [langt:Sensör] |  | — |
| `debimetre` | [langt:Debimetre] |  | — |
| `progcalisma` | [langt:Prog.Çalışma] |  | — |
| `emniyet` | [langt:Emniyet] | [langt:Emniyet Ayarları] | `XE_FrekansAlt`, `XE_FrekansUst`, `XE_FrekansSure`, `XE_VoltajAlt`, `XE_VoltajUst`, `XE_VoltajSure`, `XE_AkimAlt`, `XE_AkimUst` …+27 |
| `maliyet` | [langt:Maliyet] |  | — |
| `hmikullanici` | [langt:HMI Güvenlik] |  | — |
| `depo_ayar` | [langt:Giriş Depo Ayr.] |  | — |
| `depo_doldurma` | [langt:Depo Doldurma] |  | — |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoru`, `GirisBasincSensoru`, `durum`
- **Debi**: `Debimetre`, `T_SuSayac`
- **Seviye / uzunluk (m/cm)**: `terfiSarici`, `verimBilgi`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
