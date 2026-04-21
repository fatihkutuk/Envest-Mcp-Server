---
name: nview-a-dma-p-v3
description: |
  nView 'a-dma-p-v3' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-dma-p-v3" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, Debimetre, a-dma-p-v3.
version: "1.0.0"
generated: true
source: //10.10.10.72/public/dev.korubin/app/views/point/display/common/a-dma-p-v3/GENEL.phtml
---

# nView: a-dma-p-v3

Aile bağlamı: **dma.md (debi bölge K-Means + basınç ölçekleme)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `BasincSensoru` | Çıkış Basınç | bar | 2 | measurement | Çıkış basıncı |
| `Debimetre` | Debimetre | m³/h | 2 | measurement | Debi ölçümü (m³/h) |
| `BasincLink2` |  | bar | 2 | unknown | (div) |
| `BasincLink3` |  | bar | 2 | unknown | (div) |
| `BasincLink4` |  | bar | 2 | unknown | (div) |
| `DaireKapi` |  |  |  | unknown |  |
| `Debi2AkisHizi` | Akış Hızı | m/sn | 2 | unknown |  |
| `DebiLink1` |  | m³/h | 2 | unknown | (div) |
| `DebiLink2` |  | m³/h | 2 | unknown | (div) |
| `DebiLink3` |  | m³/h | 2 | unknown | (div) |
| `DebiLink4` |  | m³/h | 2 | unknown | (div) |
| `debimetreLt` |  | lt/sn | 2 | unknown |  |
| `FarkBasinc` | Fark Basınç | bar | 2 | unknown |  |
| `GirisBasinc` | Giriş Basınç | bar | 2 | unknown |  |
| `HatBasinc` | BKV Basınç | bar | 2 | unknown |  |
| `ili1` |  |  | 1 | unknown |  |
| `ili2` |  |  | 1 | unknown |  |
| `ili3` |  |  | 1 | unknown |  |
| `Pressure1` | 1. | bar | 2 | unknown |  |
| `Pressure2` | 2. | bar | 2 | unknown |  |
| `Pressure3` | 3. | bar | 2 | unknown |  |
| `Pressure4` | 4. | bar | 2 | unknown |  |
| `SuTaskin` |  |  |  | unknown |  |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **alarm**: `Al_KapakAcildi`, `Al_SuBaskini`
- **analog_instant**: `XA_Analog4Secim`
- **sensor_setpoint**: `XS_CikisDebiHabMod`, `XS_ModbusDebi2Secim`
- **unknown**: `js`, `length`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `hwmdata` | [langt:HWM Verileri] | [langt:Hwm Değerleri] | `Hwm_BasincDeger`, `Hwm_DebiDeger` |
| `map` | [langt:Harita Ayarları] |  | — |
| `dma` | [langt:DMA Ayarları] |  | — |
| `iwa` | [langt:IWA Ayarları] |  | — |
| `sensor` | [langt:Sensör] | [langt:Sensör Ayarları] | `XS_GirisBasincMax`, `XS_GirisBasincMin`, `XS_GirisBasincKalibre`, `XS_CikisBasincMax`, `XS_CikisBasincMin`, `XS_CikisBasincKalibre`, `XS_HatBasincMax`, `XS_HatBasincMin` …+4 |
| `cikis_debimetre` | [langt:Çıkış Debimetre] | [langt:Çıkış Debimetre Ayarları] | `XF_CikisDebimetreRange`, `XF_CikisDebimetreMin`, `XF_CikisDebimetreKalibre`, `Debimetre`, `XS_PulseCikisDebiMiktar` |
| `emniyet_sensor` | [langt:Sensör Emniyet] | [langt:Sensör Emniyet Ayarları] | `XE_GirisDebimetreAltDeger`, `XE_GirisDebimetreUstDeger`, `XE_GirisDebimetreDenetimZamani`, `XE_CikisDebimetreAltDeger`, `XE_CikisDebimetreUstDeger`, `XE_CikisDebimetreDenetimZamani`, `XE_Debimetre3AltDeger`, `XE_Debimetre3UstDeger` …+10 |
| `analog1_ayar` | [langt:Analog 1 Ayar] | [langt:Analog 1 Ayarları] | — |
| `saha_link` | [langt:Saha Link] | [langt:Saha Link Noktaları] | — |

## Birim Özeti

- **Basınç (bar)**: `BasincLink2`, `BasincLink3`, `BasincLink4`, `BasincSensoru`, `FarkBasinc`, `GirisBasinc`, `HatBasinc`, `Pressure1`, `Pressure2`, `Pressure3`, `Pressure4`
- **Debi**: `DebiLink1`, `DebiLink2`, `DebiLink3`, `DebiLink4`, `Debimetre`, `debimetreLt`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
