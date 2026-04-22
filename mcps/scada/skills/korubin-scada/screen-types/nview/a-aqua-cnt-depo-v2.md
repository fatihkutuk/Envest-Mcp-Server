---
name: nview-a-aqua-cnt-depo-v2
description: |
  nView 'a-aqua-cnt-depo-v2' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-aqua-cnt-depo-v2" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: Debimetre, a-aqua-cnt-depo-v2.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-aqua-cnt-depo-v2

Aile bağlamı: **depo.md (depo izleme)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 2 | measurement |  |
| `T_CikisDebimetre2Sayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Çıkış 2 Su Sayacı; (div) |
| `T_CikisDebimetre3Sayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Çıkış 3 Su Sayacı; (div) |
| `T_CikisDebimetre4Sayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Çıkış 4 Su Sayacı; (div) |
| `T_CikisDebimetre5Sayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Çıkış 5 Su Sayacı; (div) |
| `T_CikisDebimetre6Sayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Çıkış 6 Su Sayacı; (div) |
| `T_CikisDebimetreSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Çıkış Su Sayacı; (div) |
| `T_CikisToplamSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Çıkış Toplam Su Sayacı; (div) |
| `T_GirisDebimetre2Sayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Giriş 2 Su Sayacı; (div) |
| `T_GirisDebimetre3Sayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Giriş 3 Su Sayacı; (div) |
| `T_GirisDebimetre4Sayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Giriş 4 Su Sayacı; (div) |
| `T_GirisDebimetre5Sayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Giriş 5 Su Sayacı; (div) |
| `T_GirisDebimetre6Sayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Giriş 6 Su Sayacı; (div) |
| `T_GirisDebimetreSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Giriş Su Sayacı; (div) |
| `T_GirisToplamSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ | 2 | counter | langt=Giriş Toplam Su Sayacı; (div) |
| `CikisDebimetre2` | [langt:Çıkış 2 Debimetre] | m³ | 2 | unknown | (div) |
| `CikisDebimetre3` | [langt:Çıkış 3 Debimetre] | m³ | 2 | unknown | (div) |
| `CikisDebimetre4` | [langt:Çıkış 4 Debimetre] | m³ | 2 | unknown | (div) |
| `CikisDebimetre5` | [langt:Çıkış 5 Debimetre] | m³ | 2 | unknown | (div) |
| `CikisDebimetre6` | [langt:Çıkış 6 Debimetre] | m³ | 2 | unknown | (div) |
| `Debimetre2` | Debi ölçümü 2 | m³/h | 2 | measurement |  |
| `Depo2Seviye` |  | m | 2 | unknown |  |
| `DepoBos` | [langt:Top. Boş] | m³ | 2 | unknown | (div) |
| `DepoKapasite` | [langt:Top. Kapasite] | m³ | 2 | unknown | (div) |
| `DepoSeviye` |  | m | 2 | unknown |  |
| `DepoSuMiktari` | [langt:Top. Su Miktarı] | m³ | 2 | unknown | (div) |
| `GirisDebi` | [langt:Giriş Debimetre] | m³ | 2 | unknown | (div) |
| `GirisDebi2` | [langt:Giriş 2 Debimetre] | m³ | 2 | unknown | (div) |
| `GirisDebi3` | [langt:Giriş 3 Debimetre] | m³ | 2 | unknown | (div) |
| `GirisDebi4` | [langt:Giriş 4 Debimetre] | m³ | 2 | unknown | (div) |
| `GirisDebi5` | [langt:Giriş 5 Debimetre] | m³ | 2 | unknown | (div) |
| `GirisDebi6` | [langt:Giriş 6 Debimetre] | m³ | 2 | unknown | (div) |
| `PilSeviye` | <ico class="battery"></ico> | % | 2 | unknown | langt=battery-status; (div) |
| `PilSicaklik` | <ico class="battery"></ico> | °C | 2 | unknown | langt=battery-temperature; (div) |
| `XD_Depo1Yukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |
| `XD_Depo2Yukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting | langt=Depo 2 Yükseklik; (div) |
| `XC_KapasiteBilgi` | Çalışma modu / mod seçim | m³ | 2 | operating_mode | langt=capacity; (div) |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **dimension_setting**: `XD_Depo1Boy`, `XD_Depo1En`
- **unknown**: `DepoTekSeviye`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `analogCikis` | [langt:analog-output] |  | — |
| `dijitalGirisCikis` | [langt:digital-in-out] |  | — |
| `sensor` | [langt:sensor] |  | — |
| `log` | [langt:device-log] |  | — |
| `cihaz_uyari` | [langt:device-warning] |  | — |
| `depoAyar` | [langt:reservoir-settings] | [langt:reservoir-settings] | `XE_DusukGucModu` |
| `arayuz` | [langt:energy] | [langt:reservoir-settings] | — |

## Birim Özeti

- **Debi**: `Debimetre`, `Debimetre2`
- **Seviye / uzunluk (m/cm)**: `Depo2Seviye`, `DepoSeviye`, `XD_Depo1Yukseklik`, `XD_Depo2Yukseklik`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
