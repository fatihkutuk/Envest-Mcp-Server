---
name: calisma-modlari-kuyu
description: |
  Korubin SCADA KUYU nView'larının çalışma modu (calismamod / sabitleme) sayfalarının
  nView-bazlı karşılaştırması. a-kuyu-envest, a-aqua-cnt-kuyu-v2, a-kuyu-p-v4 ve a-kuyu-p
  arasındaki XC_CalismaModu vv numaralandırma farklarını ve XC_SabitModSecim opsiyonlarını
  içerir. Aynı "vv" değerinin farklı nView'larda FARKLI anlamlara gelebildiğine dikkat.
  Use when: "kuyu çalışma modu", "a-kuyu-envest mod", "a-kuyu-p-v4 mod farkı",
  "a-aqua-cnt-kuyu-v2 XC_CalismaModu", "depo doldurma vv kaç", "terfi vv numarası",
  "serbest kuyu vv", "kuyu nView farkları".
  Keywords: kuyu calisma modu, XC_CalismaModu kuyu, a-kuyu-envest, a-aqua-cnt-kuyu-v2,
  a-kuyu-p-v4, a-kuyu-p, calismamod, sabitleme, XC_SabitModSecim, XC_SabitModBasinc,
  XC_SabitModDebi, XC_SabitModSeviye, XC_SabitModGuc, XC_SabitModFrekans, XC_KuyuModu,
  XC_TerfiMasterModu, XC_TerfiSlaveModu, XC_OtoDepoDolMod, XC_OtoHidroforMod,
  XC_OtoSerbestMod, XE_Basinc2yeGoreCalis, XC_BasincPiSet, XZ_BasincPiSn, depo doldurma,
  hidrofor, serbest kuyu, terfi, nView mod haritasi.
version: "1.0.0"
---

# Korubin SCADA — Kuyu nView'ları Çalışma Modu Karşılaştırması

Panel URL pattern: `https://<panel_base_url>/panel/point/<nodeId>/calismamod`
(a-kuyu-p için: `/sabitleme`)

> **UYARI:** `XC_CalismaModu` için kullanılan `vv` numaraları nView'a göre **farklıdır**.
> Bir nView'da `vv=1` "Depo Doldurma" iken, başkasında `vv=1` "Serbest Kuyu" olabilir.
> Analiz/rapor üretirken mutlaka hedef node'un nView'ını tespit edip bu tabloya bak.

---

### a-kuyu-envest

**XC_CalismaModu:**
| vv | Mod |
|----|-----|
| 1 | Depo Doldurma Modu |
| 2 | Hidrofor Modu |
| 3 | Serbest Kuyu Modu |

**XC_SabitModSecim:** 1=Basınç, 2=Debi, 3=Seviye, 4=Güç, 5=Frekans (5 opsiyon)

**Setpoints:** `XC_SabitModBasinc` (bar), `XC_SabitModDebi` (m³/h), `XC_SabitModSeviye` (m), `XC_SabitModGuc` (kW), `XC_SabitModFrekans` (hz)

**Submodes:** `XC_KuyuModu`, `XC_TerfiMasterModu`, `XC_TerfiSlaveModu` (checkbox, `ch-akpas`)

**nView-specific:** Klasik 3'lü CalismaModu düzeni (Terfi yok); submode olarak ayrı Kuyu/Master/Slave bayrakları mevcut.

---

### a-aqua-cnt-kuyu-v2

**XC_CalismaModu:**
| vv | Mod |
|----|-----|
| 0 | Serbest Akış (free-flow-mode) |
| 1 | Hedef Seviye — Depo Doldurma (target-level / reservoir-filling-mode) |
| 2 | Hedef Basınç — Hidrofor (target-pressure / booster-mode) |
| 3 | Basınç PI Aktif (activate-pressure-pi) |
| 4 | Hedef Seviye — Seviye Doldurma |

**XC_SabitModSecim:** YOK (bu nView sabit mod seçimi sunmuyor).

**Setpoints (sabit mod yerine):**
- `XD_MinSuBasinc` (bar), `XD_MaxSuBasinc` (bar) — basınç aralığı
- `XC_BasincPiSet` (bar) — vv=3 seçiliyken görünür
- `XZ_BasincPiSn` (sn) — vv=3 seçiliyken görünür
- `XC_BasincPiSet` (m, seviye doldurma seti) — vv=4 seçiliyken görünür
- `XZ_BasincPiSn` (sn, seviye doldurma zaman seti) — vv=4 seçiliyken görünür

**Submodes:** Kuyu/Terfi/Master/Slave bayrakları **YOK**. Yerine:
- `XE_Basinc2yeGoreCalis` (vv=1) — ikinci basınç sensörünü referans al
- `XC_AntiBlokajAktif` (checkbox) — anti-blocking açma

**nView-specific:**
- `initPageData(data)` JS fonksiyonu vv=3 ve vv=4'e göre basınç/seviye satırlarını dinamik göster/gizle
- Hem klasik "hidrofor/booster" (vv=2) hem PI-controlled "basınç PI" (vv=3) ayrı opsiyonlar
- Farklı langt key'leri: `reservoir-filling-mode`, `booster-mode`, `free-flow-mode`, `activate-pressure-pi`
- vv=0 kullanımı bu nView'a özel (diğerlerinde vv=0 yok)

---

### a-kuyu-p-v4

**XC_CalismaModu:**
| vv | Mod |
|----|-----|
| 1 | Serbest Kuyu Modu |
| 2 | Hidrofor Modu |
| 3 | Depo Doldurma Modu |
| 4 | Terfi |

**XC_SabitModSecim:** 1=Basınç, 2=Debi, 3=Seviye, 4=Güç, 5=Frekans (5 opsiyon)

**Setpoints:** `XC_SabitModBasinc` (bar), `XC_SabitModDebi` (m³/h), `XC_SabitModSeviye` (m), `XC_SabitModGuc` (kW), `XC_SabitModFrekans` (hz)

**Submodes:** `XC_KuyuModu`, `XC_TerfiMasterModu`, `XC_TerfiSlaveModu` **YOK** (bu sayfada yer almıyor).

**nView-specific:**
- **vv numaralandırması a-kuyu-envest'e göre TAMAMEN TERS**: envest'te 1=Depo, 3=Serbest iken burada 1=Serbest, 3=Depo.
- **Terfi (vv=4)** ana CalismaModu'na eklenmiş; envest'teki ayrı submode bayrakları yerine.
- Submode bayrakları yok; tek seçim XC_CalismaModu üzerinden.

---

### a-kuyu-p  *(dosya adı: `sabitleme.phtml`, `calismamod.phtml` bu nView'da yok)*

**XC_CalismaModu:** Bu sayfada **XC_CalismaModu YOK**. Ana mod checkbox tag'leri ayrılmış:

| Tag | Mod |
|-----|-----|
| `XC_OtoDepoDolMod` | Depo Doldurma Modu |
| `XC_OtoHidroforMod` | Hidrofor Modu |
| `XC_OtoSerbestMod` | Serbest Kuyu Modu |

(Tek bir tag + vv yerine **üç ayrı boolean tag** kullanılıyor, class: `ch-akpas`.)

**XC_SabitModSecim:** 1=Basınç, 2=Debi, 3=Seviye, 4=Güç, 5=Frekans (5 opsiyon — envest ile aynı)

**Setpoints:** `XC_SabitModBasinc` (bar, fixed=2), `XC_SabitModDebi` (m³/h, fixed=2), `XC_SabitModSeviye` (m, fixed=2), `XC_SabitModGuc` (kW, **fixed=1**), `XC_SabitModFrekans` (hz, **fixed=1**)

**Submodes:** `XC_KuyuModu` / `XC_TerfiMasterModu` / `XC_TerfiSlaveModu` **YOK**.

**nView-specific:**
- Panel yolu farklı: `/sabitleme` (calismamod değil)
- `XC_CalismaModu` vv tabanlı seçim tamamen kaldırılmış → ayrı `XC_Oto*Mod` bayrakları
- Ek "Seviye Şamandıra Kontrol" bölümü: `XC_SevKontStart` (m), `XC_SevKontStop` (m), `XC_SevKontAktif` (vv=1)
- `XC_SabitModGuc` ve `XC_SabitModFrekans` için `fixed="1"` (diğer nView'larda "2")

---

## Hızlı Karşılaştırma — XC_CalismaModu vv Haritası

| Mod | a-kuyu-envest | a-aqua-cnt-kuyu-v2 | a-kuyu-p-v4 | a-kuyu-p |
|-----|:-:|:-:|:-:|:-:|
| Depo Doldurma | **1** | **1** | **3** | `XC_OtoDepoDolMod` |
| Hidrofor / Booster | **2** | **2** | **2** | `XC_OtoHidroforMod` |
| Serbest Kuyu / Free-flow | **3** | **0** | **1** | `XC_OtoSerbestMod` |
| Terfi | (submode: `XC_TerfiMasterModu`/`XC_TerfiSlaveModu`) | — | **4** | — |
| Basınç PI | — | **3** | — | — |
| Seviye Doldurma (PI) | — | **4** | — | — |

**Kritik Uyarılar:**
1. `vv=1` aynı mod değil! envest/aqua-cnt-v2'de **Depo Doldurma**, p-v4'te **Serbest Kuyu**.
2. `vv=3` envest'te **Serbest Kuyu**, aqua-cnt-v2'de **Basınç PI**, p-v4'te **Depo Doldurma**.
3. `a-kuyu-p` XC_CalismaModu KULLANMIYOR — üç ayrı boolean tag.
4. `a-aqua-cnt-kuyu-v2` submode bayraklarına (Kuyu/Master/Slave) sahip değil; yerine basınç PI + anti-blokaj var.
5. Rapor/analiz üretirken node'un nView'ı `nview_name` (veya `exports`/`scada.nodes.nview`) ile tespit edilip mod adı bu tablodan çözülmeli.

Ana referans için bkz. `calisma-modlari.md`.
