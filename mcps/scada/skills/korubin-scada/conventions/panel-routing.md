---
name: panel-routing
description: |
  Korubin panel URL yapisi, nView -> sayfa eslestirmesi, fallback routing mantigi.
  Use when: bir node icin hangi ekran sayfasi (emniyet, sensor, debimetre vb.) acildigini anlamak,
  veya tag yapisini ogrenmek icin ekran sayfasina gitmek gerektiginde.
  Keywords: panel, url, nview, phtml, emniyet, sensor, main, fallback, routing.
version: "1.0.0"
---

# Korubin Panel URL Yapisi ve Routing

Kullaniciya **asla dosya yolu** (orn. `\\10.10.10.72\public\...`) gosterme.
Onun yerine **panel URL'si** uzerinden yonlendir.

## Temel URL Pattern

```
https://<panel_base_url>/panel/point/<node_id>/<menu>
```

Ornekler:
- `https://korubin.com/panel/point/21450/emniyet` → Node 21450'nin emniyet ayarlari
- `https://korubin.com/panel/point/23280/sensor` → Node 23280'in sensor ayarlari
- `https://korubin.com/panel/point/23280/debimetre` → Debimetre ayarlari

## panel_base_url Ne?

Her instance'in kendi panel URL'i vardir (instance.yaml'da `panel_base_url` alani):
- Korubin bulut → `korubin.com`
- Diger saha kurulumlari → farkli domain'ler

## Yaygin Menu Sayfalari

Tag'lerin tanimli oldugu ana menu sayfalari:

| Menu | URL Sonu | Icerik |
|------|----------|--------|
| `emniyet` | `/emniyet` | Frekans, voltaj, akim, basinc limitleri (`XE_*`) |
| `sensor` | `/sensor` | Basinc, hat basinc, seviye sensor ayarlari (`XS_*`) |
| `debimetre` | `/debimetre` | Debimetre kalibre, range (`XS_Debi*`) |
| `debimetre2` | `/debimetre2` | Ikinci debimetre |
| `depo` | `/depo` | Cikis depo ayarlari (`XD_*`) |
| `depo2` | `/depo2` | Ikinci depo |
| `pump` | `/pump` | Pompa verileri |
| `sistem` | `/sistem` | Sistem ayarlari |
| `pid` | `/pid` | PID kontrolcu (`XC_*`) |
| `calismamod` | `/calismamod` | Calisma mod ayarlari |
| `maliyet` | `/maliyet` | Maliyet hesabi |
| `pompaverim` | `/pompaverim` | Pompa verim hesabi |
| `programtablo` | `/programtablo` | Programli calisma |
| `haberlesme` | `/haberlesme` | Haberlesme ayarlari |
| `antiblokaj` | `/antiblokaj` | Anti-blokaj |

## Fallback Routing Mantigi

Kullanici `https://korubin.com/panel/point/<id>/emniyet` girdiginde:

1. **Once node'un nView'ini bul** (orn. `a-aqua-cnt-kuyu-v2`)
2. **O nView klasorunde `emniyet.phtml` var mi bak**
3. **Varsa** → onu render et
4. **Yoksa** → `main.phtml`'e bak:
   - `main.phtml` icinde bir **link** var mi? (orn. `a-kuyu-envest-2` gosteriyor olabilir)
   - Varsa → o nView'in `emniyet.phtml`'ine git
5. **O da yoksa** → 404

## Tag Yapisini Ogrenme Yolu

Bir node'un tag yapisini anlamak icin:

### Yontem 1: URL Uzerinden
Panel URL'sine git, sayfayi incele:
```
https://<panel_base_url>/panel/point/<node_id>/<menu>
```

### Yontem 2: Tool ile
```
get_node(nodeId) → nView bilgisini al
search_tags(deviceId=nodeId, pattern="XS_*") → sensor ayarlarini listele
get_device_data(deviceId=nodeId) → tum canli tag'leri al
```

### Yontem 3: Product Type Dokumani
Eger node'un `nView` alani bir urun tipini isaret ediyorsa:
- `node_product_type` tablosundan urun dokumani
- `get_node_scada_context(nodeId)` tool'u

## Kullaniciya Yonlendirme

Kullaniciya bilgi verirken iç dosya yolu DEGIL, panel URL'si ver:

**YANLIS:**
> "XS_BasincSensoruMax ayarini `\\10.10.10.72\public\...emniyet.phtml` dosyasindan gorebilirsiniz"

**DOGRU:**
> "XS_BasincSensoruMax ayari icin panelde: `https://korubin.com/panel/point/21450/emniyet` sayfasina gidin, basinc sensoru max degerini oradan gorebilirsiniz."

## Onemli Notlar

- **`panel_base_url`** `load_instance(cfg).panel_base_url` ile her instance'ta tanimli
- Kullaniciya sunulan her yonlendirme bu URL uzerinden olmali
- Ic IP veya dosya yolu asla kullanicaya gosterilmez (guvenlik)
- Farkli instance'larda farkli panel URL'si olabilir
