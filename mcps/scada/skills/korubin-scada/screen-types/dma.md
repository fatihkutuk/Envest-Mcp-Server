---
name: screen-type-dma
description: |
  DMA (District Metered Area / izole alt olcum bolgesi) ekran tipi bilgisi.
  Use when: nView "dma" iceren ekranlar, DMA analizi, su kayip-kacak soruldugunda.
  Keywords: DMA, district metered area, debi, basinc, kayip, kacak, IWA, su dengesi.
version: "1.0.0"
---

# DMA Ekran Tipi (District Metered Area)

## nView Ornekleri
- `a-aqua-cnt-dma` - AQUA CNT standart DMA
- `a-aqua-cnt-dma-klor` - Klorlu DMA
- `a-aqua-cnt-dma-klorindividual` - Bireysel klor DMA
- `a-aqua-cnt-dma-klorv2` - Klor v2
- `a-aqua-cnt-dma-v1.2` - V1.2 versiyonu
- `a-dma-p`, `a-dma-p-v3` - Farkli panel versiyonlari
- `a-dma-ocp110` - OCP110 tabanli DMA
- `a-gaski-dma`, `a-gaski-dma-v0.1` - GASKI DMA versiyonlari

## Menu Sayfalari (a-aqua-cnt-dma)

| Sayfa | Aciklama |
|-------|----------|
| `sensor` | Sensor ayarlari |
| `giris_debimetre` | Giris debimetre |
| `cikis_debimetre` | Cikis debimetre |
| `debimetre3` - `debimetre7` | Ek debimetreler |
| `klor_sensor` | Klor sensor |
| `emniyet_sensor` | Sensor emniyet |
| `emniyet_klor` | Klor emniyet |
| `dozaj_ayar` | Dozaj ayar |
| `pompa_debi_link` | Pompa-debi baglantisi |
| `pompa_start_stop_link` | Pompa start/stop |
| `act_ayar` | ACT ayar |
| `oran_act_1_ayar` - `oran_act_4_ayar` | Oransal ACT (1-4) |
| `depo_ayar` | Depo ayar |
| `analog1_ayar` / `analog2_ayar` | Analog giris |
| `dma` | DMA ozel sayfasi |
| `dma_add` / `dma_edit` | DMA ekleme/duzenleme |
| `iwa` | IWA su dengesi sayfasi |
| `iwa_add` / `iwa_edit` | IWA ekleme/duzenleme |
| `map` / `map2` | Harita gorunumu |
| `genel_ayar` | Genel ayarlar |

## Tipik Taglar

### Debi
- `Debimetre` / `Debimetre1` - Ana debi olcumu (m3/h)
- `GirisToplamDebi` - Giris toplam debi
- `CikisToplamDebimetre` - Cikis toplam debi

### Basinc
- `BasincSensoru` - Bolge giris basinci (bar)
- `BasincSensoru2` - Hat / cikis basinci

### Klor
- `BakiyeKlor` / `KlorSensoru` - Bakiye klor

## DMA Analiz Araclari

### analyze_dma_seasonal_demand
DMA debi profilini saatlik ortalama + K-Means kumeleme ile analiz eder.

Parametreler:
- `nodeId` veya `nodeAdiAra` - DMA noktasi
- Cikti: `tez_scatter_chart` (scatter, kume rengi) + line chart

Kullanim ornekleri:
- "Debi bolgeleri goster"
- "Tez gibi K-Means analizi"
- "Saatlik talep dilimleri"
- "DMA debi profili"

### list_dma_station_nodes
DMA istasyonu nodelarini listeler.

### compare_log_metrics
Iki farkli sinyali (debi+basinc vb.) ayni zaman ekseninde karsilastirir.

## Onemli Notlar
- SCADA canli taglerinde genelde tek "Debimetre" vardir; alt bolge debi ayrimi yoktur
- Tez tarzi gunun dilimlerine bolme icin `analyze_dma_seasonal_demand` kullanilir
- Grafik sonrasi `get_chart_data` tekrar cagirilmaz; analiz sonucu zaten chart iceriyor
- IWA (International Water Association) su dengesi sayfasi su kayip-kacak hesaplamalari icindir
