---
name: nview-a-atik
description: |
  nView 'a-atik' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-atik" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: BasincSensoru, Debimetre, a-atik.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-atik

Aile bağlamı: **system.md (genel)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `BasincSensoru` | Çıkış basıncı | bar | 2 | measurement | langt=Basınç; (div) |
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 2 | measurement | langt=Debi; (div) |
| `An_Gorunen` | Anlık elektrik/motor ölçümü | KVA | 1 | instant_electrical | langt=Görünen; (div) |
| `An_Guc` | Anlık elektrik/motor ölçümü | kW | 2 | instant_electrical | langt=Güç; (div) |
| `An_L1Akim` | L1A | A | 2 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L1Voltaj` | L1V | V | 2 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L2Akim` | L2A | A | 2 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L2Voltaj` | L2V | V | 2 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L3Akim` | L3A | A | 2 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L3Voltaj` | L3V | V | 2 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_Reaktif` | Anlık elektrik/motor ölçümü | KVAR | 1 | instant_electrical | langt=Reaktif; (div) |
| `An_SebFrekans` | Anlık elektrik/motor ölçümü | Hz | 2 | instant_electrical | langt=Giriş Frekansı; (div) |
| `T_ElektrikSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | kWh |  | counter | langt=P1 Elektrik Sayacı; (div) |
| `T_ElektrikSayac2` | Toplam sayaç (su, elektrik, çalışma, şalt) | kWh |  | counter | langt=P2 Elektrik Sayacı; (div) |
| `T_ElektrikSayac3` | Toplam sayaç (su, elektrik, çalışma, şalt) | kWh |  | counter | langt=P3 Elektrik Sayacı; (div) |
| `T_ElektrikSayacToplam` | Toplam sayaç (su, elektrik, çalışma, şalt) | kWh |  | counter | langt=Elektrik Sayaçları Toplamı; (div) |
| `T_JenCalismaSure` | Toplam sayaç (su, elektrik, çalışma, şalt) |  |  | counter | langt=Jeneratör Çalışma; (div) |
| `T_P1CalismaSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) |  |  | counter | langt=P1 Çalışma Saati; (div) |
| `T_P2CalismaSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) |  |  | counter | langt=P2 Çalışma Saati; (div) |
| `T_P3CalismaSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) |  |  | counter | langt=P3 Çalışma Saati; (div) |
| `T_SuSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ |  | counter | langt=Su Sayacı; (div) |
| `An2_Gorunen` | [langt:Görünen] | KVA | 1 | unknown | (div) |
| `An2_Guc` | [langt:Güç] | kW | 2 | unknown | (div) |
| `An2_L1Akim` | L1A | A | 2 | unknown | (div) |
| `An2_L1Voltaj` | L1V | V | 2 | unknown | (div) |
| `An2_L2Akim` | L2A | A | 2 | unknown | (div) |
| `An2_L2Voltaj` | L2V | V | 2 | unknown | (div) |
| `An2_L3Akim` | L3A | A | 2 | unknown | (div) |
| `An2_L3Voltaj` | L3V | V | 2 | unknown | (div) |
| `An2_Reaktif` | [langt:Reaktif] | KVAR | 1 | unknown | (div) |
| `An2_SebFrekans` | [langt:Giriş Frekansı] | Hz | 2 | unknown | (div) |
| `An3_Gorunen` | [langt:Görünen] | KVA | 1 | unknown | (div) |
| `An3_Guc` | [langt:Güç] | kW | 2 | unknown | (div) |
| `An3_L1Akim` | L1A | A | 2 | unknown | (div) |
| `An3_L1Voltaj` | L1V | V | 2 | unknown | (div) |
| `An3_L2Akim` | L2A | A | 2 | unknown | (div) |
| `An3_L2Voltaj` | L2V | V | 2 | unknown | (div) |
| `An3_L3Akim` | L3A | A | 2 | unknown | (div) |
| `An3_L3Voltaj` | L3V | V | 2 | unknown | (div) |
| `An3_Reaktif` | [langt:Reaktif] | KVAR | 1 | unknown | (div) |
| `An3_SebFrekans` | [langt:Giriş Frekansı] | Hz | 2 | unknown | (div) |
| `DepoSeviye` |  |  | 2 | unknown |  |
| `PanoSicaklik` | Pano sıcaklığı | °C | 2 | measurement | langt=Pano Sıcaklığı; (div) |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **dimension_setting**: `XD_Depo1Yukseklik`
- **measurement**: `Pompa1StartStopDurumu`
- **sensor_setpoint**: `XS_BasincMax`
- **status**: `Pompa2StartStopDurumu`, `Pompa3StartStopDurumu`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `maliyetdetay` | [langt:Maliyet Detay] |  | — |
| `sensor` | [langt:Sensör] |  | — |
| `debimetre` | [langt:Debimetre] |  | — |
| `emniyet_sensor` | [langt:Sensör Emniyet] | [langt:Emniyet Ayarları] | `XE_SeviyeAlt`, `XE_SeviyeUst`, `XE_SeviyeSure`, `XE_DebiAlt`, `XE_DebiUst`, `XE_DebiSure`, `XE_BasincAlt`, `XE_BasincUst` …+4 |
| `emniyet_pump?pump=1` | P1 |  | — |
| `emniyet_pump?pump=2` | P2 |  | — |
| `emniyet_pump?pump=3` | P3 |  | — |
| `depo_ayar` | [langt:Depo Ayarları] | [langt:Depo Ayarları ] | `XD_Seviye1Stop`, `XD_Seviye1Start`, `XD_Seviye2Stop`, `XD_Seviye2Start`, `XD_Seviye3Stop`, `XD_Seviye3Start`, `XD_Depo1Yukseklik`, `XD_Depo1En` …+1 |

## Birim Özeti

- **Basınç (bar)**: `BasincSensoru`
- **Debi**: `Debimetre`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
