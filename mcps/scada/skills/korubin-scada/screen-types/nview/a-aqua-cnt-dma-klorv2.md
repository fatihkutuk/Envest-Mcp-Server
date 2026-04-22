---
name: nview-a-aqua-cnt-dma-klorv2
description: |
  nView 'a-aqua-cnt-dma-klorv2' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-aqua-cnt-dma-klorv2" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, a-aqua-cnt-dma-klorv2.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-aqua-cnt-dma-klorv2

Aile bağlamı: **dma.md (debi bölge K-Means + basınç ölçekleme)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `BasincSensoru` | Basınç | bar | 2 | measurement | Çıkış basıncı |
| `T_SuSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Su Sayaç (Cihaz); (div) |
| `T_SuSayacS` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Su Sayaç (Sunucu); (div) |
| `AtimOranitx` | Atım oranı | % | 2 | unknown |  |
| `bakiyeklortx` | Bakiye Klor | ppm | 2 | unknown |  |
| `bulanikliktx` | Bulanıklık | ntu | 2 | unknown |  |
| `debimetreLt` | Debimetre | lt/sn | 2 | unknown |  |
| `Debimetrem3` | Debimetre | m³/h | 2 | unknown |  |
| `deposeviyetx` | Depo Seviye | m | 2 | unknown |  |
| `depoyuksekliktx` | Depo Yükseklik | m | 2 | unknown |  |
| `depoyuzde` |  | % | 2 | unknown |  |
| `linkbakiyeklor` | Link Bakiye Klor | ppm | 2 | unknown |  |
| `linkdebiklor` | Link Debi Klor | ppm | 2 | unknown |  |
| `phtx` | PH |  | 2 | unknown |  |
| `PilSeviye` | <ico class="battery"></ico> | % | 2 | unknown | langt=Pil Durumu; (div) |
| `PilSicaklik` | <ico class="battery"></ico> | °C | 2 | unknown | langt=Pil Sıcaklık; (div) |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **measurement**: `BakiyeKlor`, `Bulaniklik`, `Debimetre`
- **operating_mode**: `XC_AnalogCikis`, `XC_CalismaMod`
- **unknown**: `DepoSeviye`, `LinkBakiyeKlor`, `LinkToplamDebimetre`, `PhSensoru`, `_NoError`

## Arayüz Ayarları (uisettings.phtml)

Bu nView'da bazı tag'ler **node konfigürasyonuna göre** aktif olur. Node parametre (`np`) üzerinde şu bayraklar kontrol edilir; bir DMA noktasında hangi basınç/debi sensörünün gerçekten kullanıldığını anlamak için bu tabloya bakın:

| np anahtarı | Etiket | Aktifse görünür tag'ler |
|---|---|---|
| `ui_depo` | [langt:Depo] | — |
| `ui_girisdozaj` | [langt:Giriş Dozajlama Aktif] | — |
| `ui_klorlama` | [langt:Klor Dozlama] | — |
| `ui_bulaniklik` | [langt:Bulanıklık] | — |
| `ui_ph` | [langt:Ph] | — |
| `ui_bakiyeklor` | [langt:Bakiye Klor] | — |
| `ui_debimetre1` | [langt:Debimetre] | — |
| `ui_basinc` | [langt:Basınç] | — |

> **DMA basınç bölgeleme analizi için ipucu:** `ui_cikisbasinc=1` ise node'da çıkış basınç sensörü (genelde `BasincSensoru`) aktif; `ui_girisbasinc=1` ise giriş basınç (`GirisBasincSensoru` veya `GirisBasinc`) aktif. Tool `analyze_dma_seasonal_demand` bu tag'lerin log'undan min/max türeterek PRV bandını otomatik belirler.

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `uisettings` | [langt:Arayüz Ayarları] | [langt:Arayüz Ayarları] | — |
| `analogayar` | [langt:Analog Ayar] | [langt:Analog Ayarları] | `XS_Analog1Min`, `XS_Analog1Max`, `XS_Analog1Kalibre`, `XS_Analog2Min`, `XS_Analog2Max`, `XS_Analog2Kalibre`, `XS_Analog3Min`, `XS_Analog3Max` …+1 |
| `klorayar` | [langt:Klor Ayar] | [langt:Çalışma Modu] | `XK_ManuelKlorlamaSure`, `XC_AnalogMaxRangeCikisSet`, `XC_AnalogManRefCikis`, `XK_KlorCalismaAltLimitSet`, `XK_KlorCalismaUstLimitSet`, `XK_PidTmrDakikaSet`, `XK_BakiyeKlorPidSet`, `XK_KlorMinPidCikis` …+8 |
| `klorlink` | [langt:Klor Link] | <a href="javascript:void(0)" id="ip1Toggle"> <ico id="ip1Ikon" class="down"></ico> </a> | `XD_HedefBeslemeIp1`, `XD_HedefBeslemeIp2`, `XD_HedefBeslemeIp3`, `XD_HedefBeslemeIp4`, `XD_HedefBeslemeModbusAdres`, `XD_HedefBeslemeModbusID`, `XD_HedefBeslemeModbusPort` |
| `dijitalGirisCikis` | [langt:Dijital Giriş Çıkış] | [langt:Dijital Giriş] | — |
| `log` | [langt:Cihaz Log] | [langt:Log Alma Ayarları ] | `XL_LogAlmaPeryoduDk`, `LogBlokSayisi`, `LogSayfaSayisi`, `LogSayfaGoster` |
| `cihaz_uyari` | [langt:Cihaz Uyarı] | [langt:Cihaz Uyarıları] | — |
| `depoAyar` | [langt:Depo Ayar] | [langt:Depo Ayarları] | — |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoru`
- **Debi**: `Debimetrem3`, `debimetreLt`
- **Seviye / uzunluk (m/cm)**: `deposeviyetx`, `depoyuksekliktx`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
