---
name: screen-type-kuyu
description: |
  Kuyu (derin kuyu / dalgic pompa) ekran tipi bilgisi.
  Use when: nView "kuyu" iceren ekranlar, kuyu tag'leri, kuyu alarmlari soruldugununda.
  Keywords: kuyu, well, dalgic, pompa, SuSeviye, StatikSuSeviye, debimetre, basinc.
version: "1.0.0"
---

# Kuyu Ekran Tipi (Well Screen)

## nView Ornekleri
- `a-kuyu-envest` - Envest standart kuyu ekrani
- `a-kuyu-envest-v2` - Envest kuyu ekrani v2
- `a-kuyu-envest-2-debi` - Cift debimetreli kuyu
- `a-kuyu-envest-act` - Aktuatorlu kuyu
- `a-kuyu-envest-bo` - Ozel kuyu versiyonu
- `a-kuyu-envest-drenaj` - Drenaj kuyusu
- `a-kuyu-p`, `a-kuyu-p-v2`, `a-kuyu-p-v3`, `a-kuyu-p-v4` - Farkli panel versiyonlari
- `a-kuyu-CP110`, `a-kuyu-OCP110` - Farkli cihaz modelleri
- `a-aqua-cnt-kuyu` - AQUA CNT tabanli kuyu
- `a-aqua-cnt-kuyu-v2` - AQUA CNT kuyu v2
- `a-aqua-cnt-kuyu-tank` - Tank ile birlikte kuyu
- `a-aqua-mini-kuyu-v1.0` - AQUA Mini kuyu
- `a-korubin-well-om` - Korubin well operations management

**Process adapter**: `well` (nType=777 veya nView icinde "kuyu"/"well" gecen)

## Ana Ekran (GENEL.phtml)
Kuyu animasyonlu SVG gorunumu:
- Su akis animasyonu (depo doldurma, serbest mod, sebeke)
- Depo seviye gosterimi (dinamik SVG path ile)
- Pompa verimlilik hesaplamalari (HM, debi, guc)
- Maliyet hesabi

## Menu Sayfalari (MENU.phtml)

| Sayfa | Aciklama |
|-------|----------|
| `tahsis` | Tahsis (allocation) |
| `maliyetdetay` | Maliyet detay |
| `pompaverim` | Pompa verimi hesaplamalari |
| `pump` | Pompa verileri |
| `calismamod` | Sabitleme / calisma modu |
| `sistem` | Sistem ayarlari |
| `pid` | PID kontrolcu ayarlari |
| `sensor` | Sensor ayarlari (basinc, hat basinc, seviye) |
| `klor_sensor` | Klor sensor ayarlari |
| `debimetre` | Debimetre ayarlari |
| `debimetre2` | 2. Debimetre ayarlari |
| `dozaj_ayar` | Dozaj ayarlari |
| `programtablo` | Programli calisma |
| `emniyet` | Emniyet ayarlari (frekans, voltaj, akim, basinc sinir degerleri) |
| `emniyet_reset_ayar` | Emniyet reset ayarlari |
| `maliyet` | Maliyet hesabi |
| `seviye_kontrol` | Samandira ayar |
| `depo` | Cikis depo ayarlari |
| `depo2` | Cikis depo 2 ayarlari |
| `depo_doldurma` | Depo doldurma ayarlari |
| `hidrofor_mod_ayar` | Hidrofor mod ayarlari |
| `haberlesme` | Haberlesme ayarlari |
| `surucu` | Surucu (inverter/VFD) ayarlari |
| `analog1_ayar` / `analog2_ayar` | Analog giris ayarlari |
| `act_ayar` | Aktuator ayarlari |
| `antiblokaj` | Anti-blokaj ayarlari |

## Tipik Taglar

### Anlik Izleme
- `SuSeviye` / `dinamikseviye` - Dinamik su seviyesi (metre)
- `StatikSuSeviye` - Statik su seviyesi (pompa dururken)
- `Debimetre` / `Debimetre1` - Debi (m3/h)
- `BasincSensoru` - Kuyu cikis basinci (bar)
- `BasincSensoru2` / `HatBasincSensoru` - Hat basinci (bar)
- `An_Guc` / `P1_Guc` - Motor gucu (kW)
- `An_SebFrekans` - Sebeke frekansi (Hz)
- `An_OrtVoltaj` - Ortalama voltaj (V)
- `An_OrtAkim` - Ortalama akim (A)
- `ToplamHm` - Toplam basma yuksekligi (metre)

### Sensor Ayarlari (sensor.phtml)
- `XS_BasincSensoruMax` - Basinc sensoru 20mA degeri (bar)
- `XS_BasincSensoruKalibre` - Basinc sensoru kalibrasyon (+/-)
- `XA_BasincSensoruAkim` - Anlik 4-20mA degeri (mA)
- `XS_HatBasincMax` - Hat basinc sensoru 20mA degeri
- `XS_HatBasincKalibre` - Hat basinc kalibrasyon
- `XS_SeviyeSensoruMax` - Seviye sensoru max
- `XS_SeviyeKalibre` - Seviye kalibrasyon

### Emniyet Parametreleri (emniyet.phtml)
- `XE_FrekansAlt/Ust/Sure/Eylem` - Sebeke frekans korumalari
- `XE_VoltajAlt/Ust/Sure` - Voltaj korumalari
- `XE_AkimAlt/Ust` - Akim korumalari
- `XE_BasincAlt/Ust` - Basinc korumalari

## Veri Sorgulama

Kuyu verisi almak icin:
1. `get_device_data(deviceId=nodeId)` - Tum canli tag degerleri
2. `get_device_tag_values(deviceId=nodeId, tagNames=["SuSeviye","Debimetre","An_Guc"])` - Belirli taglar
3. `get_chart_data(nodeId, logParamId, start, end)` - Tarihsel grafik
4. `compare_log_metrics(nodeId, primaryTagHint="debi", secondaryTagHint="guc")` - Debi-guc karsilastirma
5. `analyze_seasonal_level_profile(nodeId, tagHint="SuSeviye")` - Mevsimsel seviye profili

## Pompa Secimi Icin Dogru Veri Alma

**KRITIK:** Pompa boyutlandirma icin CANLI tag verilerini kullan, node parametrelerini (np_) KULLANMA!

### Yanlis Yaklasim (YAPMA!)
- `np_PompaDebi` → Bu pompa katalogundan girilmis STATIK deger, gercek debi degil
- `XD_BasmaYukseklik` → Bu sabit ayar degeri, gercek Hm degil

### Dogru Yaklasim
1. **Debi icin:** `Debimetre` veya `Debimetre1` tag'ini oku (canli m3/h)
   - Lt/sn ise x3.6 ile m3/h'e cevir
   - `get_device_tag_values(deviceId=nodeId, tagNames=["Debimetre"])` kullan

2. **Basma yuksekligi icin:** `ToplamHm` tag'ini oku (canli metre)
   - ToplamHm yoksa: `BasincSensoru` (bar) x 10.2 = metre
   - `get_device_tag_values(deviceId=nodeId, tagNames=["ToplamHm"])` kullan

3. **Pompa ara:**
   ```
   search_pumps(
     flow_m3h=<Debimetre canli degeri>,
     head_m=<ToplamHm canli degeri>,
     application="groundwater",
     sub_application="WELLINS"
   )
   ```

### Ornek Is Akisi
```
Kullanici: "Selafur Kuyu 4 icin pompa sec"

1. find_nodes_by_keywords("selafur kuyu 4") → nodeId bul
2. get_device_tag_values(deviceId=nodeId, tagNames=["Debimetre","ToplamHm","An_Guc"])
   → Debimetre=155 m3/h, ToplamHm=72 m, An_Guc=45 kW
3. search_pumps(flow_m3h=155, head_m=72, application="groundwater", sub_application="WELLINS")
   → En uygun pompalar listelenir
```

## Onemli Not
- Kuyu ekranlarinda Lt/sn tag'i varsa m3/h'e donusum (x3.6) otomatik yapilir
- `process_adapter = "well"` oldugunda Lt/sn oncelikli alinir (yanlis birim riski azaltilir)
- Pompa verimlilik hesabi: debi, basinc (veya Hm tag) ve guc gerektirir
- **np_ ile baslayan parametreler STATIK katalog degerleridir, canli olcum degil!**
