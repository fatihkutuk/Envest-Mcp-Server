---
name: nview-a-sanko-terfi
description: |
  nView 'a-sanko-terfi' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-sanko-terfi" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: Debimetre, a-sanko-terfi.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-sanko-terfi

Aile bağlamı: **terfi.md (terfi istasyonu)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 1 | measurement |  |
| `An_L1Akim` | L1 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L1L2Volt` | L1 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L1L3Volt` | L2 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L2Akim` | L2 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L2L3Volt` | L3 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L3Akim` | L3 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `AltSet` | Alt Seviye | m | 2 | unknown | (div) |
| `BasincSet` | Basınç Set | m | 2 | unknown | (div) |
| `CikisBasincDeger` | Çıkış Basınç | bar | 2 | unknown |  |
| `GirisBasincDeger` | Giriş Basınç | bar | 2 | unknown |  |
| `P1GirisBasincDeger` | P1 G.Basınç | bar | 2 | unknown |  |
| `P2CalismaSaat` | P2 | h | 0 | unknown | (div) |
| `P2GirisBasincDeger` | P2 G.Basınç | bar | 2 | unknown |  |
| `P3CalismaSaat` | P3 | h | 0 | unknown | (div) |
| `P3GirisBasincDeger` | P3 G.Basınç | bar | 2 | unknown |  |
| `SeviyeSet` | Seviye Set | m | 2 | unknown | (div) |
| `TankSeviye` | Tank Seviye | m | 2 | unknown |  |
| `UstSet` | Üst Seviye | m | 2 | unknown | (div) |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **install_constant**: `XV_KabloKayip`, `XV_Nmotor`, `XV_Nsurtunme`, `XV_SurucuKayip`
- **instant_electrical**: `An_Guc`
- **measurement**: `BasincSensoru`, `StatikSeviye`
- **sensor_setpoint**: `XS_MontajSev`
- **unknown**: `DepoYukseklik`, `GirisBasincSensoru`, `P1Calisti`, `P1Local`, `P1Scada`, `P1Servis`, `P2Calisti`, `P2Local`, `P2Scada`, `P2Servis`, `P3Calisti`, `P3Local`, `P3Scada`, `P3Servis`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `sensor` | [langt:Sensör] | [langt:Sensör Ayarları] | `GirisBasincMaksSeviye`, `GirisBasincDeger`, `CikisBasincMaksSeviye`, `CikisBasincDeger`, `DepoYukseklik`, `TankSeviye`, `DebiAnalogMax`, `Debimetre` |
| `emniyet` | [langt:Emniyet] | [langt:Emniyet Ayarları] | `EmniyetAltL1`, `EmniyetUstL1`, `AkimDevriyeGirmeZamani`, `EmniyetAltL2`, `EmniyetUstL2`, `AkimDevriyeGirmeZamani`, `EmniyetAltL3`, `EmniyetUstL3` …+10 |

## Birim Özeti

- **Basınç (bar)**: `CikisBasincDeger`, `GirisBasincDeger`, `P1GirisBasincDeger`, `P2GirisBasincDeger`, `P3GirisBasincDeger`
- **Debi**: `Debimetre`
- **Seviye / uzunluk (m/cm)**: `AltSet`, `BasincSet`, `SeviyeSet`, `TankSeviye`, `UstSet`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
