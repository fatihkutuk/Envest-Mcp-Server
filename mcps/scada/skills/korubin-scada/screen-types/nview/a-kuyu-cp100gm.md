---
name: nview-a-kuyu-cp100gm
description: |
  nView 'a-kuyu-cp100gm' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-kuyu-cp100gm" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, Debimetre, StatikSeviye, SuSeviye, a-kuyu-cp100gm.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-kuyu-cp100gm

Aile bağlamı: **kuyu.md (canlı tag + SP serisi dalgıç pompa)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `BasincSensoru` | Çıkış basıncı | bar | 2 | measurement |  |
| `BasincSensoru2` | Hat basıncı | bar | 2 | measurement |  |
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 1 | measurement |  |
| `StatikSeviye` | Statik su seviyesi | m | 2 | measurement |  |
| `SuSeviye` | Dinamik su seviyesi | m | 2 | measurement |  |
| `T_CalismaSayac` | Çalışma Sayacı <z>(h)</z> | (h) |  | counter | Toplam sayaç (su, elektrik, çalışma, şalt); (div) |
| `T_PompSaltSayisi` | Şalt Sayısı <z>(adet)</z> | (adet) |  | counter | Toplam sayaç (su, elektrik, çalışma, şalt); (div) |
| `T_SuSayac` | Su Sayacı <z>(m³)</z> | (m³) |  | counter | Toplam sayaç (su, elektrik, çalışma, şalt); (div) |
| `-Link1_DepoSeviye` |  | m | 2 | unknown |  |
| `NPSHSeviye` | NPSH Seviye <z></z> |  |  | measurement | NPSH seviye; (div) |
| `txt_CikisDepo` |  |  | 2 | unknown |  |
| `XD_BasmaYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 1 | dimension_setting |  |
| `XD_CikisDepoYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **alarm**: `Al_Surucu`
- **analog_instant**: `XA_Analog0Secim`
- **install_constant**: `XV_BoruIcCap`, `XV_BoruUzunluk`, `XV_KabloKayip`, `XV_Nmotor`, `XV_Nsurtunme`, `XV_PipeRoughness`, `XV_SurucuKayip`
- **instant_electrical**: `An_Guc`
- **measurement**: `Pompa1StartStopDurumu`, `SuSicaklik`
- **operating_mode**: `XC_CalismaModu`
- **sensor_setpoint**: `XS_MontajSev`
- **status**: `ACT_1_Durum`, `AntiBlokajDurum`
- **unknown**: `CalismaModu`, `XVN_ACTAktif`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `tahsis` | [langt:allocation] | [langt:Tahsis Ayarları] | `SuTahsis` |
| `calismamod` | [langt:Çalışma Mod] | [langt:Çalışma Ayarları] | — |
| `sistem` | [langt:Sistem] | [langt:Sistem Ayarları] | `XS_StatikSevGuncSure` |
| `sensor` | [langt:Sensör] | [langt:Sensör Ayarları] | `XS_BasincSensoruMax`, `XS_BasincSensoruKalibre`, `BasincSensoru`, `XS_HatBasincMax`, `XS_HatBasincKalibre`, `BasincSensoru2`, `XS_SeviyeMax`, `XS_SeviyeKalibre` …+8 |
| `analog_ayar` | [langt:Analog Ayar] | [langt:Analog Ayarları] | — |
| `debimetre` | [langt:Debimetre] | [langt:Debimetre Ayarları] | `XS_DebimetreMax`, `XS_DebimetreKalibre`, `Debimetre`, `XS_PulseDebiMiktar` |
| `programtablo` | [langt:Prog.Çalışma] | [langt:Program Tablo] | — |
| `emniyet` | [langt:Emniyet] | [langt:Emniyet Ayarları] | `XE_DebiAlt`, `XE_DebiUst`, `XE_DebiSure`, `XE_BasincAlt`, `XE_BasincUst`, `XE_BasincSure`, `XE_HatBasincAlt`, `XE_HatBasincUst` …+10 |
| `depo` | [langt:Çıkış Depo Ayr.] | [langt:Çıkış Depo Ayarları] | `XD_CikisDepoEn`, `XD_CikisDepoBoy`, `XD_CikisDepoYukseklik`, `CikisDepoSeviye`, `XS_CikisDepoSeviyeMax`, `XS_CikisDepoSeviyeKalibre`, `CikisDepoSeviye` |
| `depo_doldurma` | [langt:Depo Doldurma] | [langt:Depo Doldurma Ayarları] | `XD_CikisDepoSeviyeAlt`, `XD_CikisDepoSeviyeUst` |
| `haberlesme` | [langt:Haberleşme] | [langt:Sunucu Haberleşmesi Yokken Çalışma Ayarları] | `XH_HabYokCalisma`, `XH_HabYokDurma`, `XH_SunucuHabTimeOut`, `XH_Link1HabTimeOut` |
| `blokaj_modu` | [langt:Antiblokaj] |  | — |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoru`, `BasincSensoru2`
- **Debi**: `Debimetre`
- **Seviye / uzunluk (m/cm)**: `-Link1_DepoSeviye`, `StatikSeviye`, `SuSeviye`, `XD_BasmaYukseklik`, `XD_CikisDepoYukseklik`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
