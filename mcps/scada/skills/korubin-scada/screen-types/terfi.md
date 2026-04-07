---
name: screen-type-terfi
description: |
  Terfi istasyonu (booster/riser pump station) ekran tipi bilgisi.
  Use when: nView "terfi" iceren ekranlar, terfi tag'leri soruldugunda.
  Keywords: terfi, riser, booster, pompa, istasyon, terfi istasyonu.
version: "1.0.0"
---

# Terfi Istasyonu Ekran Tipi (Booster/Riser Station)

## nView Ornekleri
- `a-terfi-envest` - Envest standart terfi ekrani
- `a-terfi-envestdalgic` - Dalgic pompali terfi
- `a-terfi-envest-musabeyli` - Ozel kurulum
- `a-terfi-2p-envest`, `a-terfi-2p-envest-y` - 2 pompali terfi
- `a-terfi-3p-envest-gbk` - 3 pompali (genel basak kontrol)
- `a-terfi-4p-envest-gbk`, `a-terfi-4p-envest-gdk` - 4 pompali
- `a-terfi-10p-dinamik` - 10 pompali dinamik
- `a-terfi-p`, `a-terfi-p-v2`, `a-terfi-p-v3`, `a-terfi-p-v4` - Farkli panel versiyonlari
- `a-terfi-CP110`, `a-terfi-OCP110` - Farkli cihaz modelleri
- `a-terfi-CP110-p2`, `a-terfi-OCP110-p2` - 2 pompali CP/OCP modelleri
- `a-aqua-cnt-terfi`, `a-aqua-cnt-terfi-v2` - AQUA CNT tabanli terfi
- `a-aqua-mini-terfi-v1.0` - AQUA Mini terfi
- `a-korubin-riser-om` - Korubin riser operations management

**Process adapter**: `riser` (nView icinde "terfi"/"riser" gecen)

## Menu Sayfalari

| Sayfa | Aciklama |
|-------|----------|
| `tahsis` | Tahsis |
| `maliyetdetay` | Maliyet detay |
| `pompaverim` | Pompa verimi |
| `calismamod` | Sabitleme / calisma modu |
| `sistem` | Sistem ayarlari |
| `pid` | PID kontrolcu |
| `sensor` | Sensor ayarlari |
| `klor_sensor` | Klor sensor |
| `debimetre` / `debimetre2` | Debimetre ayarlari |
| `dozaj_ayar` | Dozaj ayarlari |
| `programtablo` | Programli calisma |
| `emniyet` | Emniyet ayarlari |
| `emniyet_reset_ayar` | Emniyet reset |
| `maliyet` | Maliyet |
| `seviye_kontrol` | Samandira ayar |
| `depo_ayar` | Giris depo ayarlari |
| `depo` / `depo2` | Cikis depo ayarlari |
| `depo_doldurma` | Depo doldurma |
| `hidrofor_mod_ayar` | Hidrofor mod ayarlari |
| `haberlesme` | Haberlesme |
| `surucu` | Surucu (inverter) |
| `analog1_ayar` / `analog2_ayar` | Analog giris |
| `act_ayar` | Aktuator |
| `antiblokaj` | Anti-blokaj |

## Tipik Taglar

### Anlik Izleme
- `Debimetre` / `Debimetre1` - Debi (m3/h)
- `BasincSensoru` - Giris/cikis basinci (bar)
- `BasincSensoru2` - Hat basinci (bar)
- `An_Guc` - Motor gucu (kW)
- `An_SebFrekans` - Sebeke frekansi (Hz)
- `An_OrtVoltaj` / `An_OrtAkim` - Voltaj / Akim
- `ToplamHm` - Toplam basma yuksekligi

### Pompa Durumu (cok pompali)
- `P1_Durum`, `P2_Durum`, `P3_Durum`... - Her pompa durumu
- `P1_Calisiyor`, `P2_Calisiyor`... - Calisma durumu

## Kuyu vs Terfi Farklari

| Ozellik | Kuyu | Terfi |
|---------|------|-------|
| Process adapter | `well` | `riser` |
| Seviye | Dinamik/Statik su seviyesi | Genelde yok (depo varsa depo seviyesi) |
| Debi birimi oncelik | Lt/sn oncelikli | m3/h oncelikli |
| Basinc | Kuyu cikis + hat | Giris + cikis |
| Pompa sayisi | Genelde 1 | 1-10+ arasi |

## Veri Sorgulama
- `get_device_data(deviceId=nodeId)` - Tum canli tag degerleri
- `compare_log_metrics(nodeId, primaryTagHint="debi", secondaryTagHint="guc")` - Debi vs guc
- `get_pump_catalog_for_node(nodeId)` - Pompa bilgisi
- `analyze_pump_performance(nodeId)` - Pompa performans analizi
