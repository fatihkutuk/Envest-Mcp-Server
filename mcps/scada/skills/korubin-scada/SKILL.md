---
name: korubin-scada
description: |
  Korubin/Koru1000 SCADA platform domain knowledge.
  Use when: user asks about SCADA screens, tags, devices, alarms, Korubin panel, Envest products.
  Keywords: Korubin, Envest, kuyu, terfi, depo, DMA, SCADA, tag, alarm, debimetre, seviye, basinc.
version: "1.0.0"
---

# Korubin SCADA Platform - Domain Knowledge

## Overview

Korubin, Envest firmasinin gelistirdigi web tabanli SCADA (Supervisory Control and Data Acquisition) platformudur. Su idareleri, belediyeler ve endustriyel tesisler icin kuyu, terfi istasyonu, depo ve DMA (District Metered Area) izleme/kontrol sistemi sunar.

Platform bilesenleri:
- **Korubin Web Panel**: Nokta (node) bazli ekranlar, `.phtml` sablonlarindan olusur
- **Kepware/DataExchanger**: OPC-UA / Modbus uzerinden PLC/RTU ile haberlesme
- **AQUA CNT Serisi**: Saha cihazlari (AQUA CNT 100, AQUA CNT 80, AQUA LP Logger, SMART PCS)
- **KoruMind MCP**: SCADA verilerine LLM erisimi saglayan MCP (Model Context Protocol) sunucusu

## Sub-Files

### Screen Types (`screen-types/`)
Ekran tiplerine gore SCADA bilgisi. Her dosya bir nView ailesini kapsar.

| Dosya | Aciklama |
|-------|----------|
| [kuyu.md](screen-types/kuyu.md) | Kuyu (derin kuyu / dalgic pompa) ekranlari |
| [terfi.md](screen-types/terfi.md) | Terfi istasyonu (booster/riser) ekranlari |
| [depo.md](screen-types/depo.md) | Su deposu ekranlari |
| [dma.md](screen-types/dma.md) | DMA (izole alt olcum bolgesi) ekranlari |
| [system.md](screen-types/system.md) | Sistem / genel gozetim ekranlari |

### Conventions (`conventions/`)
| Dosya | Aciklama |
|-------|----------|
| [tag-naming.md](conventions/tag-naming.md) | Tag adlandirma kurallari ve onek anlami |
| [alarm-codes.md](conventions/alarm-codes.md) | Alarm ve durum kodlari |

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
- **Urun/cihaz dokumani sorusu** (Aqua 100, modem kodu, LED durumlari, modbus haritasi):
  -> `get_product_specs`, `search_product_manual`, `get_product_settings`, `get_product_troubleshoot`
- **Anlik deger / alarm / trend sorusu** (su an kac bar, canli debi, aktif alarm, grafik):
  -> `get_device_tag_values`, `get_device_data`, `get_active_alarms`, `get_chart_data`
- **Kepware / OPC / adres sorusu** (channel, device type, tag address):
  -> `list_channel_devices`, `get_channel_device_detail`, `get_tag_address`
- **Panel ekran sorusu** (hangi menu, sensor sayfasi, sablonda ne var):
  -> `get_node` ile nView al, sonra `read_point_display_template` ile MENU/GENEL oku
- **DMA debi profili / K-Means**: -> `analyze_dma_seasonal_demand`
- **Debi-guc karsilastirma**: -> `compare_log_metrics`
- **Seviye profili**: -> `analyze_seasonal_level_profile`
