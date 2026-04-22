---
name: nview-a-aqua-cnt-bkv
description: |
  nView 'a-aqua-cnt-bkv' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-aqua-cnt-bkv" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: a-aqua-cnt-bkv.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-aqua-cnt-bkv

Aile bağlamı: **system.md (genel)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `T_SuSayac` | <ico class="battery"></ico> | m³ | 2 | counter | Toplam sayaç (su, elektrik, çalışma, şalt); langt=Toplam Su Sayacı; (div) |
| `021_PILSEVIYE` | <ico class="battery"></ico> | % | 2 | unknown | langt=Pil Seviyesi; (div) |
| `Debi` | Debi | m³/h | 3 | unknown |  |
| `GsmCekimGucu` | <ico class="battery"></ico> | rssi | 2 | unknown | langt=Gsm Çekim Gücü; (div) |
| `LinklemeHedefBasinc` | Link 1 Basınç | bar | 2 | unknown |  |
| `MANUELVANAORANI` | Manuel Vana Oranı | % |  | unknown | (div) |
| `PILSicaklik` | <ico class="battery"></ico> | °C | 2 | unknown | langt=Pil Sıcaklık; (div) |
| `SetEdilenBasinc` | Set Edilen Basınç | bar | 2 | unknown |  |
| `solmenu` | <ico class="battery"></ico> | % |  | unknown | langt=Akü Seviyesi; (div) |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **alarm**: `Al_KapiAcik`
- **unknown**: `AktuatorAnlikPoz`, `CikisBasinc`, `CikisBasincSet`, `FiltreCikisBasinc`, `FiltreCikisBasincSet`, `GirisBasinc`, `GirisBasincSet`

## Arayüz Ayarları (uisettings.phtml)

Bu nView'da bazı tag'ler **node konfigürasyonuna göre** aktif olur. Node parametre (`np`) üzerinde şu bayraklar kontrol edilir; bir DMA noktasında hangi basınç/debi sensörünün gerçekten kullanıldığını anlamak için bu tabloya bakın:

| np anahtarı | Etiket | Aktifse görünür tag'ler |
|---|---|---|
| `nAkisCarpan` | [langt:Debi Range (Akış Hızı İçin)] | — |
| `GunesPanelli` | [langt:Güneş Paneli Ayarı] | — |
| `nAkisColor` | [langt:Akış Rengi] | — |
| `nDoorOpenColor` | [langt:Kapak Açık Rengi] | — |
| `nEfColor` | [langt:Verimlilik Rengi] | — |
| `nNonEfColor` | [langt:Verimsizlik Rengi] | — |

> **DMA basınç bölgeleme analizi için ipucu:** `ui_cikisbasinc=1` ise node'da çıkış basınç sensörü (genelde `BasincSensoru`) aktif; `ui_girisbasinc=1` ise giriş basınç (`GirisBasincSensoru` veya `GirisBasinc`) aktif. Tool `analyze_dma_seasonal_demand` bu tag'lerin log'undan min/max türeterek PRV bandını otomatik belirler.

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `kurulumayar` | [langt:Kurulum Ayarları] | Sistem İzleme | `AktuatorAdim`, `AktuatorMaxKonum`, `XACT_AktuatorKirinimBasinc` |
| `pidayar` | [langt:PID Ayarları] | [langt:PID Ayarları ] | `PID_ZamanSaniye`, `PidOluAlanYuzde` |
| `sensor` | [langt:Sensör] | <a href="javascript:void(0)" id="basincToggle"> <ico id="basincIkon" class="down"></ico> </a> | `GirisBasincSet`, `GirisBasinc`, `FiltreCikisBasincSet`, `FiltreCikisBasinc`, `CikisBasincSet`, `CikisBasinc`, `Debi_Set`, `Debi` |
| `dijitalGiris` | [langt:Dijital Girişler] | [langt:Dijital Giriş] | — |
| `hedefBasinc` | [langt:Hedef Basınç] | <a href="javascript:void(0)" id="ip1Toggle"> <ico id="ip1Ikon" class="down"></ico> </a> | `HEDEFBESLEMEIP1`, `HEDEFBESLEMEIP2`, `HEDEFBESLEMEIP3`, `HEDEFBESLEMEIP4`, `HEDEFBESLEMEMODBUSADRES`, `HEDEFBESLEMEMODBUSID`, `HEDEFBESLEMEMODBUSPORT` |
| `link_basinc` | [langt:Saha Link] | [langt:Saha Link Noktaları] | `XC_LinkBasinc1_KritikAlt` |
| `emniyet_ayar` | [langt:Emniyet Ayar] | [langt:Emniyet Ayarları] | `HatKORUMAMIN_DEBI`, `hatKORUMAMAX_DEBI`, `HatKORUMAMIN_BASINC`, `HatKORUMAMAX_BASINC`, `AlarmDurumHaraketSaniye`, `AlarmDurumPozisyon` |
| `program` | [langt:Prog. Çalışma] | [langt:Programlı Çalışma Ayarları] | `XP_1_Set`, `XP_2_Set`, `XP_3_Set`, `XP_4_Set`, `XP_5_Set`, `XP_6_Set`, `XP_7_Set`, `XP_8_Set` …+6 |
| `uisettings` | [langt:Arayüz Ayarları] | <a href="javascript:void(0)" id="ip1Toggle"> <ico id="ip1Ikon" class="down"></ico> </a> | — |

## Birim Özeti

- **Basınç (bar)**: `LinklemeHedefBasinc`, `SetEdilenBasinc`
- **Debi**: `Debi`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
