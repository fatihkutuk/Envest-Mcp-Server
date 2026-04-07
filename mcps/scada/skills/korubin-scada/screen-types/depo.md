---
name: screen-type-depo
description: |
  Su deposu ekran tipi bilgisi.
  Use when: nView "depo" iceren ekranlar, depo tag'leri soruldugunda.
  Keywords: depo, tank, store, seviye, dolum, bosaltma, debimetre, giris, cikis.
version: "1.0.0"
---

# Depo Ekran Tipi (Water Storage Tank)

## nView Ornekleri
- `a-depo-envest` - Envest standart depo ekrani
- `a-depo-envest-bakiyeklor` - Bakiye klorlu depo
- `a-depo-envest-brm`, `a-depo-envest-brm-v2` - BRM versiyonlari
- `a-depo-envest-mimarsinanosb` - Ozel kurulum
- `a-depo-p`, `a-depo-p-v3`, `a-depo-p-b` - Farkli panel versiyonlari
- `a-depo-m`, `a-depo-m-v3` - M serisi
- `a-depo-s` - S serisi
- `a-depo-v5` - V5 versiyonu
- `a-depo-cs100`, `a-depo-CS110`, `a-depo-OCS110` - Farkli cihaz modelleri
- `a-aqua-cnt-depo`, `a-aqua-cnt-depo-v2` - AQUA CNT tabanli
- `a-aqua-cnt-depo-klor` - Klorlamali depo
- `a-aqua-cnt-depo-2outflow` - 2 cikisli depo
- `a-aqua-cnt-depo-3debi` - 3 debimetreli depo
- `a-aqua-cnt-3debi-depo`, `a-aqua-cnt-3debi-depo-v2` - 3 debi depo varyantlari
- `a-aqua-mini-depo-v1.0` - AQUA Mini depo
- `a-korubin-depo-om` - Korubin depo operations management

**Process adapter**: `tank` (nView icinde "depo"/"tank"/"store" gecen)

## Menu Sayfalari (a-depo-envest)

| Sayfa | Aciklama |
|-------|----------|
| `sensor` | Sensor ayarlari |
| `sicaklik_secim` | Sicaklik secim |
| `giris_debimetre` | Giris debimetre ayarlari |
| `cikis_debimetre` | Cikis debimetre ayarlari |
| `debimetre3` - `debimetre7` | Ek debimetreler (3-7) |
| `klor_sensor` | Klor sensor |
| `emniyet_sensor` | Sensor emniyet |
| `emniyet_klor` | Klor emniyet |
| `dozaj_ayar` | Dozaj ayarlari |
| `pompa_debi_link` | Pompa-debi baglantisi |
| `pompa_start_stop_link` | Pompa start/stop baglantisi |
| `act_ayar` | ACT ayarlari |
| `oran_act_1_ayar` - `oran_act_4_ayar` | Oransal aktuator ayarlari (1-4) |
| `tekfazvana` | Tek faz vana (XV_VanaAktif aktifse gorunur) |
| `depo_ayar` | Depo ayarlari |
| `analog1_ayar` / `analog2_ayar` | Analog giris |

## Tipik Taglar

### Seviye
- `DepoSeviye` - Depo su seviyesi (metre veya %)
- `SuSeviye` - Alternatif seviye tag'i

### Debi
- `GirisToplamDebi` - Giris toplam debi
- `CikisToplamDebimetre` - Cikis toplam debi
- `CikisAnlikDebi` - Cikis anlik debi
- `Debimetre`, `Debimetre1`...`Debimetre7` - Birden fazla debimetre

### Klor
- `BakiyeKlor` / `KlorSensoru` - Bakiye klor degeri

### Vana
- `VanaDurum` - Vana durumu (0=acik/yesil, 1=kapali/kahverengi)
- `XV_VanaAktif` - Vana aktiflik kontrolu

## Depo Ozel Ozellikleri
- Depo ekranlarinda genellikle giris ve cikis debimetreleri ayri izlenir
- 7'ye kadar debimetre destegi vardir
- Oransal aktuator (1-4) ile vana kontrol
- Pompa-debi baglantisi: hangi pompanin hangi debimetreye baglandigi
- Pompa start/stop link: uzak pompa istasyonu start/stop komutu
