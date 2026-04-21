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
Opsiyonel tez yontemi basinc olcekleme ile her saat dilimine PRV/pompa set basinci atar.

Parametreler:
- `nodeId` veya `nodeAdiAra` - DMA noktasi
- `kClusters` - Kume sayisi (6-18, default 12) - gunu kac dilime ayirmak istedigimizi belirler
- `startDate` / `endDate` - Analiz araligi
- `minPressure` / `maxPressure` (bar) - **Tez yontemi basinc olcekleme icin**
  - Her ikisi verilirse: debi kume merkezleri bu banda `mapminmax` ile olceklenir
  - Cikti: `tez_basinc_ayarlama.calisma_tablosu` (saat:dk basl./bitis + debi + basinc_set_bar)
  - Verilmezse: sadece K-Means donduru, `kullanici_basinc_bandi_sorusu_tr` ile band sorulur
- Cikti: `tez_scatter_chart` (scatter, kume rengi) + line chart (+ varsa basinc tablosu)

Kullanim ornekleri:
- "Debi bolgeleri goster" -> varsayilan cagri
- "Tez gibi K-Means analizi" -> varsayilan cagri
- "Saatlik talep dilimleri" -> varsayilan cagri
- "DMA debi profili" -> varsayilan cagri
- "4-6 bar arasina olcekle" -> `minPressure=4, maxPressure=6`
- "basinc bandi belirle" -> band sor, sonra tekrar cagir
- "PRV set cizelgesi" -> `minPressure`/`maxPressure` iste

## Tez Yontemi: Basinc Olcekleme (Fatih Kutuk LR tezi)

DMA'da "basinc" kavrami iki farkli anlama gelir - dogru tool'u secmek kritiktir:

| Kullanici ne soyledi | Ne ister | Dogru arac |
|---|---|---|
| "ESKI DMA'nin anlik basinci nedir?" | Canli sensor degeri | `get_device_tag_values(tagNames=["BasincSensoru"])` |
| "BasincSensoru trend grafigi" | Tarihsel log egrisi | `get_node_log_chart_data` |
| "Basinc bolgelerini belirle / saat dilimlerine gore basinc set" | Debi kumeleri -> bar | `analyze_dma_seasonal_demand` (+ minPressure/maxPressure) |
| "4-6 bar arasina olcekle / PRV set cizelgesi" | Tez yontemi mapminmax | `analyze_dma_seasonal_demand(minPressure=4, maxPressure=6)` |

### Tez akisi (MATLAB -> MCP esdegeri)
1. Saatlik ortalama debi vektoru (24 eleman) alinir
2. K-Means (default k=12) - kClusters ile 6-18 arasi ayarlanabilir
3. Kume merkezleri saate gore siralanir (medoid saatler)
4. Ardisik medoidler arasi ortalama = saat dilimi siniri
5. `mapminmax(kume_merkezleri_debi, minBar, maxBar)` -> her kume icin basinc set degeri
6. Cikti: `calisma_tablosu = [baslangic_sa:dk, bitis_sa:dk, debi, basinc_set_bar]`

### Varsayilan Davranis (band verilmediginde)
- Sadece K-Means + saatlik profil doner
- Ciktida `kullanici_basinc_bandi_sorusu_tr` ile "isterseniz minPressure/maxPressure verin" hatirlatmasi yapilir
- LLM once parametresiz cagirabilir, sonra kullaniciya bandi sorar; veya tahmin bir bant (orn. 3-5 bar) ile cagirip teyit ister

### Cakisma Durumlari
- Kullanici "basinc sabit" ya da "0'a olcekle" derse: mapminmax kaynak hep ayni degerse orta nokta doner (min+max)/2
- maxPressure <= minPressure: olcekleme devre disi, varsayilan davranis
- Seviye icin (analyze_seasonal_level_profile): basinc olcekleme YOKTUR (fiziksel anlamsiz)

### list_dma_station_nodes
DMA istasyonu nodelarini listeler.

### compare_log_metrics
Iki farkli sinyali (debi+basinc vb.) ayni zaman ekseninde karsilastirir.

## Onemli Notlar
- SCADA canli taglerinde genelde tek "Debimetre" vardir; alt bolge debi ayrimi yoktur
- Tez tarzi gunun dilimlerine bolme icin `analyze_dma_seasonal_demand` kullanilir
- Grafik sonrasi `get_chart_data` tekrar cagirilmaz; analiz sonucu zaten chart iceriyor
- IWA (International Water Association) su dengesi sayfasi su kayip-kacak hesaplamalari icindir
