---
name: core-rules
description: |
  HER GOREV ONCESI OKUNMALI. Tum Envest MCP instance'lari (SCADA, KoruCAPS, DB) icin
  kritik davranis kurallari: coklu instance arama, birim kurallari, yuvarlama yasagi,
  ayar vs olcum ayrimi, pompa secimi akisi, log analizi, panel URL yonlendirmesi.
  Use when: ANY task on this MCP server. Call get_skill('core-rules') BEFORE any other tool.
  Keywords: core, rules, always, first, kritik, zorunlu, cross-instance, prefix, kurallar.
version: "1.0.0"
priority: "always-read-first"
---

# Envest MCP - Core Rules (HER GOREV ONCESI OKU)

> **Bu dosya her gorev basinda okunmalidir.** Bu kurallar BUTUN instance'lar icin
> gecerlidir (SCADA, KoruCAPS, Database). Her kural gercek bir hata senaryosundan cikarildi.

---

## 1. COKLU INSTANCE / PREFIX KURALI

Bu MCP sunucusu **tek port** uzerinden **birden fazla SCADA** ve sistemi servis eder.
Tool isimleri `<instance_prefix>_<tool>` formatindadir:

- `corumscada_find_nodes_by_keywords` → Corum SCADA
- `envestbulutkorubin_find_nodes_by_keywords` → Envest Korubin Bulut
- `korucaps_search_pumps` → KoruCAPS pompa secimi (ortak)
- `database_*` → generic DB tool (varsa)

### ZORUNLU AKIS — Node ararken TEK TOOL kullan

Token coklu instance icin mint edildiyse merged MCP'de **server-side** bir tool vardir:

```
find_node_everywhere(keywords="selafur kuyu 4")
```

Bu tool **tum SCADA instance'larinda** ayni anda arar. Prefix hatirlamaya / tek tek
denemeye gerek **YOK**. Response donus:
- `selected_tool_prefix` → sonraki tool cagrilarinda bu prefix'i kullan (orn. `envestbulutkorubin_get_node`)
- `total_found == 0` → kullaniciya bildir, tahmin yurutme
- Birden fazla esleme → kullaniciya hangisi oldugunu sor

### YASAK
- `<prefix>_find_nodes_by_keywords` ile tek tek prefix denemek (find_node_everywhere tek cagrida hallediyor)
- Ilk deneme bos donunce "bulunamadi" deyip bitirmek — find_node_everywhere ZATEN tum instance'lari tarar
- Tool response'unda `next_action_required: ...` varsa ignore etmek

---

## 2. BIRIM KURALLARI — DEBI VARSAYILAN m3/h

Tag adinda **acik sekilde** `LtSn`, `Ltsn`, `LT_SN`, `lt/sn` gecmedikce → debi **m3/h** kabul edilir.

| Tag adi | Birim |
|---------|-------|
| `Debimetre`, `Debimetre1`, `Debimetre2`, `ToplamDebi` | m3/h |
| `DebimetreLtSn`, `LtSn`, `Qltsn` | Lt/sn |
| `T_ToplamDebi`, `T_ToplamDebimetre` | m3 (kumulatif sayac) |
| `BasincSensoru`, `HatBasincSensoru` | bar |
| `ToplamHm` | metre (basma yuksekligi) |
| `SuSeviye`, `StatikSuSeviye` | metre |
| `An_Guc`, `P1_Guc` | kW |

### Donusumler
- Lt/sn → m3/h : **× 3.6**
- bar → mSS (Hm) : **× 10.197**
- kPa → bar : ÷ 100
- mbar → bar : ÷ 1000

---

## 3. DEGERLERI YUVARLAMA

Sensor/tag degerleri **aynen** kullanilmali.

- `ToplamHm = 131.45` → pompa seciminde `131.45` gonder, `131` DEGIL
- `Debimetre = 157.82` → `157.82` gonder, `160` veya `158` DEGIL
- Yuvarlama yalnizca kullaniciya **gosterirken** yapilir (orn. "~157.8 m³/h")
- Islem/tool cagrisi **her zaman ham deger** ile

---

## 4. TAG SEMANTIGI — X* = AYAR, T_* = SAYAC

### `X*` ile baslayan tag'ler = AYAR (setpoint / konfigurasyon)
Gercek olcum **degildir**. Kullanici "basinc ne?" sordugunda `XS_BasincSensoruMax` degerini gosterme!

| Prefix | Anlam |
|--------|-------|
| `XE_` | Emniyet limiti (frekans/voltaj/akim/basinc + sure + eylem) |
| `XS_` | Sensor ayari (tip, range, kalibre, offset) |
| `XD_` | Depo ayari (seviye min/max, doldurma/bosaltma) |
| `XC_` | Kontrol/otomasyon ayari (PID, calisma modu, hedef) |
| `XA_` | Analog giris kalibrasyonu (4-20mA/0-10V) |
| `XV_` | Vana/aktuator limit |
| `XINV_` | Invertor (frekans) ayarlari |
| `XHID_` | Hidrofor ayarlari |

### `T_*` ile baslayan tag'ler = KUMULATIF SAYAC
- `T_ToplamDebi`, `T_ToplamDebimetre` → toplam gecen su (m3)
- Tarih araligindaki uretim = `son_endeks − ilk_endeks`
- Sonunda `S` varsa sunucu sayiyor (daha guvenilir, orn. `T_ToplamDebiS`)
- `S` yoksa cihaz sayiyor (reset riski var)

### `al_*`, `An_*`, sade tag'ler = CANLI OLCUM
- `al_Termik`, `al_KuruCalisma` → cihaz alarm bitleri
- `An_Guc`, `An_SebFrekans`, `An_OrtVoltaj` → analizor anlik degerleri
- `Debimetre`, `BasincSensoru`, `ToplamHm`, `SuSeviye` → saha sensor anlik degerleri

---

## 5. POMPA SECIMI AKISI

Kullanici bir node icin pompa secimi istediginde:

### ZORUNLU ADIM SIRASI

1. **Node'u bul** → `<prefix>_find_nodes_by_keywords` (Kural 1'e uy, coklu instance ara)
2. **nView'i al** → `<prefix>_get_node(nodeId)` → `nView` alani
3. **Ekran tipine gore skill oku** → `get_skill('korubin-scada', 'screen-types/nview/<nView>.md')`
4. **CANLI tag degerlerini oku** (MUTLAKA):
   - `<prefix>_get_device_tag_values(deviceId=nodeId, tagNames=["ToplamHm","Debimetre","Pompa1StartStopDurumu", ...])`
5. **Pompa calisiyor mu kontrol et**:
   - `Pompa1StartStopDurumu == 1` veya `PompaCalismaDurumu == 1` olmali
   - Durdugunda `Hm` ve `Debi` **guvenilmez** (dinamik degerler akis gerektirir)
   - Durmusken → loglardan calistigi bir donem bul → `<prefix>_get_node_log_data` ile dogrula
6. **Formulle cross-check (ZORUNLU)**: Hem **giris** verisi hem **cikis** (secilen pompa) tutarli mi?
   - **Hidrolik guc**: `P_hid (kW) = (Q × H) / 367` (Q: m3/h, H: metre — saf su)
   - **Sonuc verimle tersten**: `P1_hesap = P_hid / η_toplam` — oneri `P1`'i ile karsilastir
   - Ornek: Q=122 m3/h, H=67 m → P_hid = 22.3 kW → η=%61 → P1 ≈ 36.5 kW
   - Eger sistem/oneri P1=85 kW diyorsa → **TUTARSIZ**, degerler yanlis olabilir → tekrar oku
   - Giris tarafi: `An_Guc` (canli) ile de tutarsiz ise → ya pompa kapali ya sensor arizali
   - **Tutarsizligi GORURSEN → kullaniciya "veriler tutarsiz, bir daha kontrol edeyim" de ve tekrar oku.** Sessizce devam etme.
7. **Pompa ailesi sec**:
   - **Kuyu (dalgic)** → `SP` serisi
   - **Terfi / booster** → `CR` serisi
   - **Dalgic atiksu / drenaj** → uygun seri
8. **KoruCAPS'e gonder**:
   - `korucaps_search_pumps(flow_m3h=<canli_debi>, head_m=<canli_hm>, series="SP", ...)`
9. **np_* parametreleri KULLANMA**:
   - `np_PompaDebi`, `np_PompaHm`, `XD_BasmaYukseklik` → **katalog** degeridir, gercek olcum DEGIL
   - Istisna: canli veri alinamaz / pompa uzun suredir kapali → kullaniciya "katalog degeri kullaniyorum, dogrulanmasi gerekebilir" uyarisiyla

### Detay skill:
`get_skill('korubin-scada', 'analysis/pump-verification.md')`

---

## 6. LOG ANALIZI / ANORMALI TESPITI

"Sensor bozuk mu?", "Hat patladi mi?", "Neden bu kadar yuksek?" sorularinda:

1. **Log skill'ini oku**: `get_skill('korubin-scada', 'analysis/log-anomaly-detection.md')`
2. Tag log'unu al: `<prefix>_get_node_log_data` veya `<prefix>_analyze_log_trend`
3. Donmus deger tespiti: ard arda N kayit ayni → sensor arizasi olasi
4. Ani sicrama: tek log icinde %>50 sapma → sinyal sorunu veya gercek olay
5. Karsilastir: komsu tag'lerle (orn. `BasincSensoru` + `BasincSensoru2`) tutarlilik

---

## 7. KULLANICI DENETIMI ("kim degistirmis")

"Bu ayari kim degistirdi?", "Ne zaman sapti?" sorularinda:

1. **User-audit skill'ini oku**: `get_skill('korubin-scada', 'analysis/user-audit.md')`
2. `<prefix>_run_safe_query` ile `log_tagyaz_user_log` tablosunu sorgula
3. Sorgu orneklerini skill dosyasindan al

---

## 8. SU URETIMI / TUKETIM HESABI

"Mart ayinda kac m3 su uretildi?" sorularinda:

1. **Water-production skill'ini oku**: `get_skill('korubin-scada', 'analysis/water-production.md')`
2. `T_ToplamDebi` veya `T_ToplamDebimetre` sayac tag'ini bul
3. Tarih araliginda **ilk ve son endeks** al
4. Fark = o donemdeki uretim (m3)
5. Sifirlanma / reset kontrolu yap (cihaz sayaci ise `S` yoksa)

---

## 9. PANEL URL YONLENDIRME

Kullaniciya **asla dosya yolu** (`\\10.10.10.72\public\...`) veya **ic IP** gosterme.

### Dogru yonlendirme:
```
https://<panel_base_url>/panel/point/<nodeId>/<menu>
```

Ornekler:
- `/emniyet` → XE_ tag'leri (emniyet limitleri)
- `/sensor` → XS_ tag'leri (sensor ayarlari)
- `/debimetre` → Debimetre ayari/kalibrasyonu
- `/depo` → XD_ tag'leri
- `/pid` veya `/calismamod` → XC_ tag'leri

Detay: `get_skill('korubin-scada', 'conventions/panel-routing.md')`

---

## 10. SKILL KULLANIMI — PROGRESSIVE DISCLOSURE

Bu sunucuda domain bilgisi **skill** dosyalarinda saklanir (markdown). Her gorev icin:

1. **ILK** `list_skills` cagir → mevcut skill'leri gor
2. **BU dosyayi** zaten okudun (`core-rules`)
3. Gorev konusuna gore ilgili skill'i oku:
   - SCADA node/ekran → `korubin-scada` (SKILL.md sonra uygun alt dosya)
   - Database → `database-best-practices`
4. Tool cagrilarinda skill'deki kurallari uygula

### nView-spesifik bilgi
Bir node'un `nView` alanini ogrendikten sonra:
```
get_skill('korubin-scada', 'screen-types/nview/<nView>.md')
```
(orn. `a-kuyu-envest.md`, `a-dma-p-v3.md`)

---

## 11. GUVENLIK / GIZLILIK

- **Database** tool'larinin hata mesajlarinda kullanici adi/sifre gecebilir → MCP bu bilgileri maskeler, ama kullaniciya bilgi aktarirken **hic** DB baglanti detayi paylasma.
- Node ve tag degerleri saha verisidir → yayinlama, sadece kullaniciya raporla.
- Panel URL'i dogru instance'in `panel_base_url`'u ile olusturulmali — ic IP ile DEGIL.

---

## OZET — TEK SATIRLIK KURALLAR

1. SCADA belirtilmediyse **tum prefix'lerde** ara
2. Debi varsayilan **m3/h** (aksi yazilmadikca)
3. Degerleri **yuvarlama** — ham gonder
4. `X*` = AYAR, `T_*` = SAYAC, digerleri canli olcum
5. Pompa secimi: **canli tag** oku, `np_*` katalog DEGIL
6. Pompa calisiyor mu bak; durmus → log'dan donem bul
7. Kuyu → **SP**, Terfi → **CR** pompa serisi
8. Yon yapi: `panel_base_url/panel/point/<nodeId>/<menu>` — **ic yol / IP yasak**
9. Log/sorgu/denetim icin ilgili `analysis/*.md` skill'ini oku
10. Suphede kullaniciya sor, **tahmin yurutme**
