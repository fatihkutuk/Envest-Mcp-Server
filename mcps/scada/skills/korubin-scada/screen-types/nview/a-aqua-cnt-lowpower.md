---
name: nview-a-aqua-cnt-lowpower
description: |
  nView 'a-aqua-cnt-lowpower' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-aqua-cnt-lowpower" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, Debimetre, a-aqua-cnt-lowpower.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-aqua-cnt-lowpower

Aile bağlamı: **system.md (genel)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `BasincSensoru` | Basinc | bar | 2 | measurement | Çıkış basıncı |
| `Debimetre` | Debimetre | m³/h | 2 | measurement | Debi ölçümü (m³/h) |
| `Katotik` | <ico class="battery"></ico>Katotik |  | 2 | unknown | (div) |
| `Nem` | <ico class="battery"></ico>Nem | % | 2 | unknown | (div) |
| `PilBesleme` | <ico class="battery"></ico>GSM PilSeviye | % | 2 | unknown | (div) |
| `Seviye` | Seviye | m | 2 | unknown |  |
| `Sicaklik` | <ico class="battery"></ico>Sicaklik | °C | 2 | unknown | (div) |

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `settings` | [langt:Sensör Ayarları] | [langt:Basınç Ayarları] | `XS_BasincSet`, `XS_BasincGiris`, `XS_BasincAlarmUst`, `XS_BasincAlarmAlt`, `XS_DebiSet`, `XS_DebiGiris`, `XS_DebiAlarmUst`, `XS_DebiAlarmAlt` …+14 |
| `uyanmasaat` | [langt:Uyanma Saatleri] | Uyanma Saatleri | — |
| `verisaat` | [langt:Veri Saatleri] | Uyanma Saatleri | — |
| `verigun` | [langt:Veri Gönderme Günü] | Veri Günleri | — |
| `arsiv` | [langt:Arşiv] | Cihazdan Gelen Veriler | — |
| `arayuz` | [langt:Arayüz Ayarları] | Ekran Görünümü | — |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoru`
- **Debi**: `Debimetre`
- **Seviye / uzunluk (m/cm)**: `Seviye`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
