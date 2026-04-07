---
name: tag-naming
description: |
  SCADA tag adlandirma kurallari ve onek anlamlari.
  Use when: tag isimlerini yorumlamak, tag aramak, veya yeni tag anlamak gerektiginde.
  Keywords: tag, onek, prefix, xe_, al_, xd_, x_, debimetre, SuSeviye, basinc.
version: "1.0.0"
---

# Korubin SCADA Tag Adlandirma Kurallari

## Onek (Prefix) Kurallari

| Onek | Anlam | Aciklama |
|------|-------|----------|
| `al_` | Cihaz alarmi | Alarm parametresi (orn. `al_Termik`, `al_KuruCalisma`) |
| `xe` veya `XE_` | Emniyet alarmi | Emniyet sinir degerleri (orn. `XE_VoltajAlt`, `XE_FrekansUst`, `XE_BasincAlt`) |
| `xd` veya `XD_` | Depo alarmi (genelde) | Depo seviye alarmlari veya depo ile ilgili parametreler |
| `x` ile baslayan (genel) | Ayar / setpoint parametresi | Kullanicinin degistirebilecegi yapilandirma degerleri |
| `XS_` | Sensor ayari | Sensor kalibrasyon/max degerleri (orn. `XS_BasincSensoruMax`, `XS_BasincSensoruKalibre`) |
| `XA_` | Analog gosterge | Anlik analog deger gostergesi (orn. `XA_BasincSensoruAkim`) |
| `XV_` | Vana/Actuator aktiflik | Vana veya aktuator aktiflik durumu (orn. `XV_VanaAktif`) |
| `An_` | Analizor / anlik deger | Enerji analizoru okumalari (orn. `An_Guc`, `An_SebFrekans`, `An_OrtVoltaj`, `An_OrtAkim`) |
| `T_` | Toplam / hesaplanmis | Hesaplanmis veya toplam deger (orn. `T_Debi`, `T_Guc`, `T_ToplamHm`) |

## Yaygin Tag Isimleri

### Debi (Akis) Tagleri
- `Debimetre`, `Debimetre1`, `Debimetre2` - m3/h cinsinden akis olcumu
- `Demimetre` - yaygin yazim hatasi, debimetre ile ayni
- `T_Debi`, `T_DebiLtSn` - Hesaplanmis debi degerleri
- `GirisToplamDebi`, `CikisToplamDebimetre`, `CikisAnlikDebi` - Giris/cikis debileri (depo ekranlarinda)
- `DebiM3h`, `Debi_m3h`, `AnlikDebiM3h`, `Qm3h` - m3/h biriminde debi
- `DebimetreLtSn`, `LtSn`, `LT_SN`, `DebiLtSn`, `AnlikDebiLtSn` - Lt/sn biriminde debi (x3.6 = m3/h)

### Guc / Enerji Tagleri
- `An_Guc`, `P1_Guc` - Anlik guc (kW)
- `MotorAktifGuc` - Motor aktif gucu
- `An_SebFrekans` - Sebeke frekansi (Hz)
- `An_OrtVoltaj` - Ortalama voltaj (V)
- `An_OrtAkim` - Ortalama akim (A)

### Seviye Tagleri
- `SuSeviye`, `suseviye` - Dinamik su seviyesi (kuyu icinde)
- `StatikSuSeviye`, `statikseviye` - Statik su seviyesi (pompa dururken)
- `DepoSeviye` - Depo su seviyesi
- `dinamikseviye` - Dinamik seviye alternatif yazim

### Basinc Tagleri
- `BasincSensoru` - Birincil basinc sensoru (bar) - genelde kuyu cikis basinci
- `BasincSensoru2` - Ikincil basinc sensoru - genelde hat basinci
- `HatBasincSensoru`, `hatbasincsensoru` - Hat basinci
- `CikisBasincSensoru`, `GirisBasincSensoru` - Giris/cikis basinclari (terfi/depo)

### Basma Yuksekligi (Hm) Tagleri
- `ToplamHm`, `TotalHm`, `TOPHAMHM` - Toplam basma yuksekligi (metre)
- `PompaHm`, `Pompa_Hm` - Pompa basma yuksekligi
- `BasmaYuksekligi` - Basma yuksekligi
- `GercekHm` - Gercek basma yuksekligi
- `Hm` - Genel kisa ad (yanlis eslesme riski)

### Pompa Tagleri
- `P1_Durum`, `P2_Durum` - Pompa durumu (1=calisiyor, 0=durdu)
- `P1_Calisiyor`, `P2_Calisiyor` - Pompa calisma durumu

### Klor Tagleri
- `KlorSensoru` - Bakiye klor olcumu
- `BakiyeKlor` - Bakiye klor degeri

## Birim Donusumleri

| Kaynak birim | Hedef birim | Carpan |
|-------------|-------------|--------|
| Lt/sn (LtSn) | m3/h | x 3.6 |
| bar (Basinc) | mSS (metre su sutunu) | x 10.197 |

## Onemli Not
- Gercek tag yollari projeye gore degisir
- Suphede `search_tags` veya `get_device_data` ile dogrulayin
- Ekran tipine ozel sabit tanimli degilse yukaridaki varsayilanlar gecerlidir
