---
name: nview-a-kuyu-m
description: |
  nView 'a-kuyu-m' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-kuyu-m" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: a-kuyu-m.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-kuyu-m

Aile bağlamı: **kuyu.md (canlı tag + SP serisi dalgıç pompa)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `T_SuKalan` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ |  | counter | (div) |
| `-Link1_DepoSeviye` |  |  | 2 | unknown |  |
| `BirOncekiYilSuSayac` |  | m³ |  | unknown | (div) |
| `kuyuDetay` |  | m³/h |  | unknown | (div) |
| `kuyuDurumSag` | Durum / mod göstergesi | m³ |  | status | (div) |
| `SaltSayKalan` |  | salt/h |  | unknown | (div) |
| `YilBasiSuSayac` |  | m³ |  | unknown | (div) |
| `XD_Depo1Yukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting | (div) |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **alarm**: `Al_Motor`
- **counter**: `T_SuSayac`
- **measurement**: `Debimetre`, `Pompa1StartStopDurumu`
- **operating_mode**: `XC_OtoDepoDolMod`
- **status**: `AntiBlokajDurum`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `tahsis` | [langt:allocation] |  | — |
| `debimetre` | [langt:Debimetre] |  | — |
| `debimetre_kalibre` | [langt:Debi Kalibre] | [langt:Debimetre Kalibre] | `XS_X1Analog`, `XS_X2Analog`, `XS_Y1Debi`, `XS_Y2Debi`, `XS_YCutOff` |
| `progcalisma` | [langt:Prog.Çalışma] |  | — |
| `depo_doldurma` | [langt:Depo Doldurma] |  | — |

## Birim Özeti

- **Debi**: `kuyuDetay`
- **Seviye / uzunluk (m/cm)**: `XD_Depo1Yukseklik`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
