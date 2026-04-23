---
name: korubin-scada
description: |
  Korubin/Koru1000 SCADA platform domain knowledge.
  Use when: user asks about SCADA screens, tags, devices, alarms, Korubin panel, Envest products.
  Keywords: Korubin, Envest, kuyu, terfi, depo, DMA, SCADA, tag, alarm, debimetre, seviye, basinc.
version: "1.0.0"
---

# Korubin SCADA Platform - Domain Knowledge

> **ONCE OKU:** `get_skill(skill_name='core-rules')` — her gorev oncesi okunmasi gereken
> kritik kurallar (coklu instance, birim, yuvarlama, tag semantigi, pompa secimi).
> Bu dosya SCADA'ya ozel detay; core-rules genel davranis kurallari.

## Overview

Korubin, Envest firmasinin gelistirdigi web tabanli SCADA (Supervisory Control and Data Acquisition) platformudur. Su idareleri, belediyeler ve endustriyel tesisler icin kuyu, terfi istasyonu, depo ve DMA (District Metered Area) izleme/kontrol sistemi sunar.

Platform bilesenleri:
- **Korubin Web Panel**: Nokta (node) bazli ekranlar, `.phtml` sablonlarindan olusur
- **Kepware/DataExchanger**: OPC-UA / Modbus uzerinden PLC/RTU ile haberlesme
- **AQUA CNT Serisi**: Saha cihazlari (AQUA CNT 100, AQUA CNT 80, AQUA LP Logger, SMART PCS)
- **KoruMind MCP**: SCADA verilerine LLM erisimi saglayan MCP (Model Context Protocol) sunucusu

## Sub-Files

### Screen Types (`screen-types/`)
Ekran tiplerine gore SCADA bilgisi. Her aile dosyasi bir nView ailesini (kuyu, terfi, depo, dma, system) kapsar.

| Dosya | Aciklama |
|-------|----------|
| [kuyu.md](screen-types/kuyu.md) | Kuyu (derin kuyu / dalgic pompa) ekran ailesi |
| [terfi.md](screen-types/terfi.md) | Terfi istasyonu (booster/riser) ekran ailesi |
| [depo.md](screen-types/depo.md) | Su deposu ekran ailesi |
| [dma.md](screen-types/dma.md) | DMA (izole alt olcum bolgesi) + tez yontemi basinc olcekleme |
| [system.md](screen-types/system.md) | Sistem / genel gozetim ekran ailesi |

### Per-nView Details (`screen-types/nview/`) **otomatik uretilmis**

Her spesifik nView icin tek bir `.md` dosyasi — GENEL.phtml'den cikarilmis tag/birim/etiket/rol tablosu, alt menu sayfalari, JS `data.*` mod/alarm referanslari ve (varsa) `uisettings.phtml`'den ui_* bayraklari.

**Kapsam:** DB'de en cok kullanilan 53 nView icin `screen-types/nview/<nView>.md` dosyasi uretilmistir. Liste (azalan kullanim sayisina gore):

| Aile | nView'lar |
|---|---|
| **Kuyu** | `a-kuyu-envest` (668), `a-aqua-cnt-kuyu-v2` (370), `a-kuyu-p-v4` (43), `a-kuyu-p` (27), `a-kuyu-m` (24), `a-aqua-cnt-kuyu` (18), `a-kuyu-cp110gm` (14), `a-aqua-mini-kuyu-v1.0` (10), `a-kuyu-p-v4.1` (9), `a-kuyu-cp100gm` (9), `a-kuyu-envest-drenaj` (9), `a-kuyu-rtu-v1` (5), `a-kuyu-OCP110` (4) |
| **Depo** | `a-depo-envest` (195), `a-aqua-cnt-depo-klor` (75), `a-aqua-cnt-depo-v2` (73), `a-depo-p-b` (18), `a-aqua-mini-depo-v1.0` (15), `a-aqua-cnt-depo` (12), `a-depo-envest-brm` (7), `a-depo-p` (6), `a-depo-OCS110` (6), `a-depo-aski-1000depo` (6), `a-depo-tosya` (3) |
| **Terfi** | `a-terfi-envest` (117), `a-aqua-cnt-terfi-v2` (26), `a-aqua-cnt-terfi-v2-3b` (26), `a-terfi-p-v3` (10), `a-terfi-p-v4` (8), `a-terfi-p` (4), `a-sanko-terfi` (4), `a-terfi-2p-envest-y` (3), `a-terfi-bilge-otomasyon` (3), `a-terfi-envestdalgic` (3) |
| **DMA** | `a-dma-p-v3` (29), `a-aqua-cnt-dma-v1.2` (27), `a-gaski-dma` (20), `a-aqua-cnt-dma-klorv2` (7), `a-aqua-cnt-dma` (-), `a-aqua-cnt-dma-klor` (-), `a-aqua-cnt-dma-klorindividual` (-), `a-gaski-dma-v0.1` (4), `a-dma-p` (-), `a-dma-ocp110` (-) |
| **Diger** | `_a-multi` (270), `a-atik` (12), `a-hidro-p-v3` (11), `a-atik-cc120gm` (9), `a-aqua-cnt-lowpower` (8), `a-gozlem-m` (7), `a-sanal-d` (7), `a-aqua-cnt-bkv` (6), `a-gaz-hakkari` (4), `a-gaz-meha` (4), `a-sogutma-temsu-f4` (4), `a-tmaster` (3), `a-izleme-p` (3), `a-pompa-test` (3) |

- **Ne zaman kullanilir:** Bir node'un `nView` alani bilindiginde o ekrana ozel tag semantigini (ornek: `a-dma-p-v3`'te `BasincSensoru = Cikis Basinci / bar`, `GirisBasinc = Giris Basinci / bar`) kesinlemek icin.
- **Uretim:** `python scripts/generate_nview_skills.py --nview <name>` veya `--all` ile toplu yenileme. Kaynak: `https://<panel_base_url>/panel/point/<node_id>/<menu>`
- **Bulma:** Skill loader `rglob("*.md")` kullandigi icin ayri manifest gerekmez.
- **uisettings.phtml:** Bazi DMA/depo/BKV nView'larinda (`ui_girisbasinc`, `ui_cikisbasinc`, `ui_debimetre1/2` vb.) node konfigurasyonuna gore tag'ler aktif olur — skill icindeki "Arayuz Ayarlari" tablosundan kontrol edilir.

### Conventions (`conventions/`)
| Dosya | Aciklama |
|-------|----------|
| [tag-naming.md](conventions/tag-naming.md) | Tag adlandirma kurallari ve onek anlami (XE_, XS_, XD_, XC_, XA_, T_, An_) |
| [alarm-codes.md](conventions/alarm-codes.md) | Alarm ve durum kodlari |
| [panel-routing.md](conventions/panel-routing.md) | Panel URL yapisi, nView->sayfa eslestirmesi, fallback routing |

### Analysis (`analysis/`) — Derin analiz ve is akislari
| Dosya | Aciklama |
|-------|----------|
| [pump-verification.md](analysis/pump-verification.md) | Pompa secimi oncesi veri dogrulama, pompa calisiyor mu kontrolu, formulle cross-check |
| [pump-frequency-projection.md](analysis/pump-frequency-projection.md) | VFD frekans projeksiyonu (sistem eğrisi + Affinity), annexa sapma toleransı |
| [hydraulic-network-analysis.md](analysis/hydraulic-network-analysis.md) | Pompa verim analizi akışkanlar mekaniği katmanı: Darcy-Weisbach sürtünme, statik/sürtünme/yerel kayıp ayrıştırması, boru çapı senaryosu, geri ödeme (LCC) |
| [log-anomaly-detection.md](analysis/log-anomaly-detection.md) | Sensor arizasi, donmus deger, hat patlak tespiti, akilli SQL sorgulamasi |
| [water-production.md](analysis/water-production.md) | Sayac endeks farkindan tarih araligindaki su uretimi/tuketimi hesabi |
| [user-audit.md](analysis/user-audit.md) | log_tagyaz_user_log tablosundan kullanici degisiklik denetimi |

### Device Types (`device-types/`)
| Dosya | Aciklama |
|-------|----------|
| [pump.md](device-types/pump.md) | Pompa izleme ve verimlilik |
| [flowmeter.md](device-types/flowmeter.md) | Debimetre (akis olcer) |
| [level-sensor.md](device-types/level-sensor.md) | Seviye sensoru |
| [pressure-sensor.md](device-types/pressure-sensor.md) | Basinc sensoru |

### Product Types (`product-types/`)
| Dosya | Aciklama |
|-------|----------|
| [aqua-cnt-100.md](product-types/aqua-cnt-100.md) | AQUA CNT 100 kompakt tip pompa kontrol |
| [aqua-cnt-80.md](product-types/aqua-cnt-80.md) | AQUA CNT 80 LoRa/GSM pompa-depo kontrol |
| [aqua-lp-logger.md](product-types/aqua-lp-logger.md) | AQUA LP pilli veri toplama |
| [smart-pcs.md](product-types/smart-pcs.md) | SMART PCS basinc yonetim alani kontrol |

## Key Architecture Concepts

### Node (Nokta)
Her sahada izlenen fiziksel nokta bir `node` kaydina karsilik gelir. `kbindb.node` tablosunda:
- `id` (nodeId): Benzersiz tamsayi
- `nName`: Kullanici gorunur ad (orn. "Kale - 12 (BAHCELIEVLER)")
- `nView`: Ekran sablonu ailesi (orn. "a-kuyu-envest", "a-terfi-envest")
- `nType`: Tip kodu (777 = kuyu, 666 = sistem, vb.)
- `nState`: Durum (>= 0 aktif)
- `nPath`: Hiyerarsik konum yolu

### Panel URL Modeli
```
https://{panel_base_url}/panel/point/{nodeId}/{segment}
```
- `segment` -> `.phtml` dosyasina cozulur
- Ornek: `/panel/point/12345/sensor` -> `sensor.phtml`

### Veri Katmanlari
1. **Canli veri (_tagoku)**: PLC/OPC'den anlik okunan tag degerleri
2. **Log veri (noktalog.log_{nodeId})**: Tarihsel kayitlar, grafik/trend icin
3. **Alarm (alarmparameters + alarmstate)**: Alarm tanimlari ve durumlari
4. **Counter (_servercounters)**: Sayac degerleri (toplam debi vb.)

### Tool Routing Karar Agaci

**EN SIK SORU: "X noktasinda Y ayarini nereden yaparim / calisma modu ne / emniyet nasil ayarlanir"**

Zorunlu akis (3 adim, baska tool eklemeyin):
1. `find_nodes_by_keywords(keywords="<node adi>")` -> nodeId ve nView'i alin
2. `get_skill(skill_name="korubin-scada", file_path="screen-types/nview/<nView>.md")`
   -> dosyadaki "Alt Menü Sayfaları" tablosunda hangi alt sayfa hangi ayari (XC_*, XS_*, XE_*, XD_*, XM_*, XINV_*, XHID_*, X_*) iceriyor acik yazar
3. (Istege bagli) Canli deger icin `get_device_tag_values(deviceId=nodeId, tagNames=["XC_CalismaModu", ...])`

YANLIS YOL (bu sorularda KULLANMAYIN): `search_product_manual`, `get_product_specs`,
`get_product_settings`, `get_product_troubleshoot`, `get_operational_engineering_hints`,
`get_scada_summary`, `get_scada_semantics`, `get_database_schema`, `run_safe_query`,
`read_point_display_template`. Bunlar cihaz katalog / genel bilgi icindir; SCADA panel
menusundeki ayar yerini soylemez.

---

- **AQUA CNT cihaz dokuman sorusu** (modem status kodu, LED, alarm, modbus register, menu, APN, antiblokaj, ultrasonik debimetre hatasi I/J/H/K, Control Word bit, pil, 100S/100F/100FP/100SL):
  -> **ONCE** `get_skill('aqua-devices')` → `SKILL.md` icindeki routing tablosundan dogru alt dosyayi oku (ornek: `modem-status.md`, `alarms-and-warnings.md`, `modbus-reference.md`). Cevap **kilavuzdadir**, SCADA tool'u gerekmez. **YASAK:** 20+ tool cagirarak kilavuz bilgisi turetmeye calismak.
- **Diger urun/cihaz dokuman sorusu** (SMART PCS, AQUA 80, AQUA LP Logger):
  -> `get_product_specs`, `search_product_manual`, `get_product_settings`, `get_product_troubleshoot`
- **Anlik deger / alarm / trend sorusu** (su an kac bar, canli debi, aktif alarm, grafik):
  -> `get_device_tag_values`, `get_device_data`, `get_active_alarms`, `get_chart_data`
- **Kepware / OPC / adres sorusu** (channel, device type, tag address):
  -> `list_channel_devices`, `get_channel_device_detail`, `get_tag_address`
- **Panel ekran sorusu** (hangi menu, sensor sayfasi, sablonda ne var):
  -> `get_node` ile nView al, sonra `read_point_display_template` ile MENU/GENEL oku
- **DMA debi profili / K-Means**: -> `analyze_dma_seasonal_demand`
- **DMA basinc bandi / PRV set cizelgesi / "X-Y bar'a olcekle"**: -> `analyze_dma_seasonal_demand(minPressure=X, maxPressure=Y)` (BasincSensoru tag grafigi DEGIL)
- **Debi-guc karsilastirma**: -> `compare_log_metrics`
- **Seviye profili**: -> `analyze_seasonal_level_profile`
- **Bir node'un ekran tagleri sorulunca** (ornek: "a-kuyu-envest'te toplamhm nedir"): once aile skili (kuyu.md), sonra `screen-types/nview/<nView>.md` detay tablosu.
- **Pompa secimi / degisikligi sorusu**: -> `analysis/pump-verification.md` oku, sonra canli Hm ve Debi tag'lerini al, `korucaps_search_pumps` kullan. **np_ parametrelerini DEGIL canli tag'leri kullan!**
- **Pompa VERİM analizi / "neden çok enerji çekiyor" / sürtünme / boru çapı / yatırım sorusu**: -> `analysis/hydraulic-network-analysis.md` oku, sonra `analyze_hydraulic_network(nodeId)` → ayrıştırma al, gerekirse `analyze_pipe_upgrade_economics(...)` ile senaryo. ToplamHm'i tek sayı kabul etme, bileşenlerine ayır.
- **Sensor arizasi / patlak / anormal deger sorusu**: -> `analysis/log-anomaly-detection.md` oku, sonra ilgili tool'lar (`get_node_log_data`, `analyze_log_trend`, `run_safe_query`)
- **Su uretimi / tuketim sorusu** ("Mart ayinda kac m3 uretilmis"): -> `analysis/water-production.md` oku, sonra `T_` sayac tag'ini bul, endeks farki hesapla
- **"Kim bu ayari degistirmis / neden sapti" sorusu**: -> `analysis/user-audit.md` oku, `run_safe_query` ile `log_tagyaz_user_log` tablosunu sorgula
- **Panel URL / hangi sayfadan ayarlanir sorusu**: -> `conventions/panel-routing.md` oku. Iç dosya yolu DEGIL, `https://<panel_base_url>/panel/point/<nodeId>/<menu>` formatinda yonlendir.

## KRITIK Kurallar

1. **Debi birimi varsayilan m3/h'tir** - Tag adinda `LtSn`/`Ltsn` gecmedikce m3/h kabul et
2. **Degerleri YUVARLAMA** - `Hm=131.45` aynen kullan, `131` degil
3. **`np_*` parametreleri STATIK katalog degerleridir** - Gercek olcum icin canli tag (`Debimetre`, `ToplamHm`) oku
4. **`X*` tag'leri AYAR'dir** - `XS_DebimetreMax` = sensor max ayari, gercek debi DEGIL
5. **Pompa durumu kontrol et** - `Pompa1StartStopDurumu=0` iken Hm/Debi guvenilmez, loglardan calisma donemini bul
6. **Formulle dogrula** - `P1 ≈ (Q × H) / 236` ile tutarsizliklari yakala
7. **Panel URL kullan** - Iç IP/dosya yolu asla kullaniciya gosterme

## Cross-Instance Node Search (Coklu SCADA)

Bu MCP'de birden fazla SCADA instance olabilir. Her instance'ın prefix'i **dinamik** (token'a göre).
Kullanici **hangi SCADA** oldugunu belirtmediyse:

**ZORUNLU AKIS — TEK TOOL:**
```
find_node_everywhere(keywords="...")
```

Bu tool tum SCADA instance'larinda ayni anda arar, dogru prefix'i bulur, response'ta
`selected_tool_prefix` doner. Sonraki tool cagrilari bu prefix'le yapilir.

Mevcut instance'lari listelemek icin: `list_scada_instances`.

**YASAK:** Prefix tahmin etmek, tek tek deneme. `find_node_everywhere` tek cagrida hallediyor.
