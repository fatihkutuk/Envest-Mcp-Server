---
name: nview-a-aqua-mini-depo-v1.0
description: |
  nView 'a-aqua-mini-depo-v1.0' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-aqua-mini-depo-v1.0" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: a-aqua-mini-depo-v1.0.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-aqua-mini-depo-v1.0

Aile bağlamı: **depo.md (depo izleme)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `LORABeslemeVoltaji` | <ico class="battery"></ico> | V | 2 | unknown | langt=(Lora) Besleme Voltajı; (div) |
| `LORAPilSeviye` | <ico class="battery"></ico> | % | 2 | unknown | langt=(Lora) Pil Durumu; (div) |
| `LORAPilSicaklik` | <ico class="battery"></ico> | °C | 2 | unknown | langt= (LoraPil) Sıcaklık; (div) |
| `PilSeviye` | <ico class="battery"></ico> | % | 2 | unknown | langt=Pil Durumu; (div) |
| `PilSicaklik` | <ico class="battery"></ico> | °C | 2 | unknown | langt=Pil Sıcaklık; (div) |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **dimension_setting**: `XD_Depo1Boy`, `XD_Depo1En`, `XD_Depo1Yukseklik`
- **measurement**: `CikisDepoSeviye`, `Debimetre`, `Pompa1StartStopDurumu`
- **unknown**: `DepoSeviye`, `DepoTekSeviye`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `dijitalGirisCikis` | [langt:Dijital Giriş Çıkış] | [langt:Dijital Giriş] | — |
| `sensor` | [langt:Sensör] | <a href="javascript:void(0)" id="basincToggle"><ico id="basincIkon" class="down"></ico></a> | `XS_BasincSet`, `BasincSensoru`, `XS_SeviyeSet`, `SuSeviye`, `XS_DebiSet`, `Debimetre`, `Ain1`, `Ain2` |
| `calismaMod` | [langt:Çalışma Modu] | [langt:Otomatik Çalışma Modu Ayarları] | `XS_MinSuBasinc`, `XS_MaxSuBasinc` |
| `pompaverim` | [langt:Pompa Verimi] | [langt:Pompa Seçimi] | — |
| `pump` | [langt:Pompa Bilgileri] | Pompa Bilgileri | — |
| `motor` | [langt:Motor Ayarları] | [langt:Motor Çıkış Seçimi (Mutlaka Seçiniz)] | — |
| `depoDoldurma` | [langt:Depo Doldurma] | <a href="javascript:void(0)" id="ip1Toggle"> <ico id="ip1Ikon" class="down"></ico> </a> | `XH_HedefBeslemeIp1`, `XH_HedefBeslemeIp2`, `XH_HedefBeslemeIp3`, `XH_HedefBeslemeIp4`, `XH_HedefBeslemeModbusAdres`, `XH_HedefBeslemeModbusID`, `XH_HedefBeslemeModbusPort`, `XH_HedefBeslemeMinSuSeviye` …+1 |
| `hidrofor` | [langt:Hidrofor Ayarları] | [langt:Basınç Parametreleri ] | `XHID_BasincCalismaP1`, `XHID_BasincCalismaP2`, `XHID_BasincCalismaP3`, `XHID_BasincDurma` |
| `emniyet` | [langt:Emniyet Ayarları] | <a href="javascript:void(0)" id="seviyeToggle"> <ico id="seviyeIkon" class="down"></ico> </a> | `XE_MotorKorumaSuSeviyeMin`, `XE_MotorKorumaSuSeviyeMax`, `XE_MotorKorumaSuSeviyeZaman`, `XE_MotorKorumaBasincMin`, `XE_MotorKorumaBasincMax`, `XE_MotorKorumaBasincZaman`, `XE_MotorKorumaDebiMin`, `XE_MotorKorumaDebiMax` …+3 |
| `cihaz_uyari` | [langt:Cihaz Uyarı] | [langt:Cihaz Uyarıları] | — |
| `depoAyar` | [langt:Depo Ayar] | [langt:Depo Ayarları] | `XE_DusukGucModu` |
| `maliyet` | [langt:Maliyet] | [langt:Maliyet Hesap Ayarları] | — |
| `maliyetdetay` | [langt:Maliyet Detay] | [langt:Maliyet Hesap Detayları] | — |
| `arayuz` | [langt:Arayüz Ayar] | [langt:Arayüz Ayarları] | — |
| `dijitalGirisCikislora` | [langt:Dijital Giriş Çıkış] | [langt:Dijital Giriş] | — |
| `sensorlora` | [langt:Sensör] | <a href="javascript:void(0)" id="basincToggle"><ico id="basincIkon" class="down"></ico></a> | `XR_LORABasincSet`, `LORABasincSensoru`, `XR_LORASeviyeSet`, `LORASuSeviye`, `XR_LORADebiSet`, `LORADebimetre` |

## Birim Özeti


## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
