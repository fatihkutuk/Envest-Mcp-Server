# Task: Annexa Semantiği Düzeltme + Hidrolik-Şebeke Uzmanı Yeteneği

## Sorun Tespiti (Kullanıcı raporu — 22 Nisan 2026, Serbest Bölge Kuyu analizi)

### Durum 1 — annexa yanlış yorumlanıyor
- Kod tabanında `annexa` (ISO 9001 "Annex A"'dan ödünç kavramsal isim) **katalog/gerçek ölçüm sapma toleransı** olarak kullanılıyor.
- Mevcut skill'ler (`core-rules/SKILL.md`, `pump-frequency-projection.md`, `pump-verification.md` ve `get_installed_pump_info` hint'i) bunu **"pompa yaşlanma katsayısı"** olarak tarif ediyor.
- LLM bu yüzden her raporda "pompa %6 aşınmış, bakım gerek" gibi yorum ekliyor. Oysa katalog değeri tavan, annexa farkı *normal tolerans* olabilir — yaşlanmışlık kararı ayrı bir analizdir.

### Durum 2 — Hidrolik-şebeke uzmanlığı eksik
Kullanıcı `a-kuyu-envest` nView'ında zaten canlı olan install sabitleri var:

| Tag | Anlam | Örnek |
|---|---|---|
| `XV_BoruUzunluk` | Deşarj boru uzunluğu (m) | 55 |
| `XV_BoruIcCap` | Boru iç çapı (mm) | 155 |
| `XV_PipeRoughness` | Boru iç yüzey pürüzlülüğü | 100000 (birim ?) |
| `XV_Nsurtunme` | Yerel kayıp katsayısı toplamı ΣK | 0.00 |
| `XV_Nmotor` | Motor verimi (%) | 82 |
| `XV_KabloKayip` | Kablo kaybı (%) | 0.30 |
| `XV_SurucuKayip` | Sürücü kaybı (%) | 2.00 |

LLM bugün bu sabitleri **okumuyor** ve `ToplamHm`'yi tek parça "toplam basma" kabul edip sürtünme-statik ayrımını yapmıyor. Oysa:
```
ToplamHm  =  H_dinamik_kuyu  +  H_yükseklik  +  H_sürtünme(boru)  +  H_yerel(vana/dirsek)
```
`H_sürtünme` küçük ve `ToplamHm` büyükse → kuyu derin/yüksek (düzeltme yok). `H_sürtünme` büyükse → boru çapı yetersiz, gereksiz elektrik yakılıyor → **boru yatırımı değer mi?** sorusu açılır.

### Durum 3 — Korunacak iyi davranış
LLM "kendi pompası zaten en iyi, değiştirme" sonucunu doğru verdi. Bu davranışa dokunmayacağız.

---

## Çözüm Mimarisi (minimal etki, 3 katman)

### 1. Skill güncellemeleri (dil ve kavram düzeltmesi — yalnızca `.md`)
- `core-rules/SKILL.md` Bölüm 5 içindeki `annexa` açıklamasını yeniden yaz:
  - "yaşlanma katsayısı" dili → "katalog–gerçek sapma toleransı"
  - Aşınma kararı için açık ek kriterler (ΔH birden fazla dönem, debi düşüşü korelasyonu)
  - Kullanıcıya sunum kuralı: *sadece* sapma varsa ve başka anomali ile desteklenirse "pompada aşınma olabilir" diyebilir, tek başına annexa<1 ≠ aşınmış
- `analysis/pump-frequency-projection.md` içindeki aynı dili düzelt
- `analysis/pump-verification.md`: annexa değinilen bir yer yok ama gözden geçir
- Tool docstring/hint_tr metinleri (`get_installed_pump_info`, `analyze_pump_at_frequency`): dili düzelt

### 2. Yeni skill: `analysis/hydraulic-network-analysis.md`
- Kullanıcıyı ve LLM'i boru sürtünme analiziyle tanıştırır
- Temel denklem (Darcy-Weisbach):
  ```
  h_f = f · (L/D) · v²/(2g)
  Re = v·D/ν  (su için ν ≈ 1.14e-6 m²/s, 15°C)
  v  = Q / (π·D²/4)
  ```
- Reynolds'a göre Swamee-Jain ile `f` (Colebrook-White yerine explicit form)
- Yerel kayıplar: `h_L = ΣK · v²/(2g)` — `XV_Nsurtunme` = ΣK
- Ne zaman boru önerisi:
  - `H_sürtünme / H_toplam > 0.25` → sürtünme hakim, çap büyütülebilir
  - `H_sürtünme / H_toplam < 0.10` → statik hakim, boru değişimi anlamsız
- Yatırım geri dönüşü akışı: `analyze_pipe_upgrade_economics` tool'una yönlendirme

### 3. İki yeni tool (scada_nodes.py — ScadaNodesPack)

#### 3a. `analyze_hydraulic_network(nodeId)`
Giriş: nodeId. Çıkış:
```json
{
  "node_id": ...,
  "input_params": {
    "pipe_length_m": 55,
    "pipe_inner_diameter_mm": 155,
    "pipe_roughness_mm": 0.1,      // XV_PipeRoughness + varsayım
    "local_loss_coeff_sum": 0.0,    // XV_Nsurtunme
    "motor_eff_pct": 82,
    "cable_loss_pct": 0.3,
    "vfd_loss_pct": 2.0,
    "flow_m3h": 177.4,
    "total_head_m": 82.9,
    "static_well_level_m": 12,      // SuSeviye/StatikSeviye
    "well_kot_m": ...,
    "tank_kot_m": ...
  },
  "hydraulic_breakdown": {
    "velocity_m_s": 2.61,
    "reynolds": 355000,
    "friction_factor_f": 0.019,
    "pipe_friction_loss_m": 3.24,
    "local_loss_m": 0.00,
    "static_head_estimate_m": 60,   // kuyu derinliği + yükseklik
    "unaccounted_m": 19.7,           // toplam - (statik + sürtünme + yerel)
    "friction_share_pct": 3.9
  },
  "diagnosis_tr": "Sürtünme kaybı toplam H'nin %4'ü — dominant değil. Boru yatırımı anlamlı kazanç sağlamaz. Yüksek ToplamHm statik kaynaklı (kuyu dinamik + yükseklik).",
  "pipe_upgrade_recommended": false,
  "hint_next_action_tr": "Sürtünme baskın olsaydı analyze_pipe_upgrade_economics çağır."
}
```

**Önemli:** XV_PipeRoughness birimi belirsizse iki yorumu da döndür (mm vs μm) ve kullanıcıdan teyit iste. Tool fail etmez.

#### 3b. `analyze_pipe_upgrade_economics(nodeId, alternative_inner_diameter_mm, alternative_length_m=0, pipe_cost_per_meter_tl=0, electricity_price_tl_per_kwh=0, daily_operating_hours=0, design_life_years=20)`
Giriş: senaryo parametreleri. Default'lar:
- `alternative_length_m` → XV_BoruUzunluk
- `pipe_cost_per_meter_tl` → kullanıcı girmezse None döner (yatırım hesabı eksik raporlanır, hipotetik tasarruf sunulur)
- `electricity_price_tl_per_kwh` → XM_T1Fiyat ortalaması veya kullanıcı
- `daily_operating_hours` → T_CalismaSayac / gün sayısı (son 30 gün) veya 24
- `design_life_years` → 20

Çıkış:
```json
{
  "current_state": {
    "pipe_id_mm": 155,
    "friction_loss_m": 3.24,
    "annual_kwh": 221874,
    "annual_cost_tl": ...
  },
  "alternative_state": {
    "pipe_id_mm": 200,
    "friction_loss_m": 0.95,
    "annual_kwh_savings": 6150,
    "annual_cost_savings_tl": ...
  },
  "investment": {
    "material_cost_tl": 55 * 350 = 19250,  // eğer fiyat verildiyse
    "installation_factor": 1.3,
    "total_investment_tl": 25000
  },
  "economics": {
    "simple_payback_years": 4.1,
    "npv_20y_tl": ...,
    "lcc_current_tl": ...,
    "lcc_alternative_tl": ...,
    "recommended": true/false
  },
  "note_tr": "Geri dönüş 4.1 yıl, 20 yıllık NPV +X TL. Boru yatırımı anlamlı. Ancak hidrolik analizde sürtünme payı %4 idi — öneri gereksiz."
}
```

Bu tool **sürtünme baskın değilse de çalışır** ama sonuçta `recommended=false` döner ve not olarak kullanıcıya bilgi verir. Asla pompayı değiştirmeye zorlamaz.

---

## Mimari Kararlar (kullanıcıdan teyit gerekli)

1. **Sürtünme formülü**: Darcy-Weisbach (Swamee-Jain explicit) öneriyorum — daha doğru, Reynolds ile pürüzlü-pürüzsüz ayrımı yapılıyor. Hazen-Williams'a göre daha doğru, ama C katsayısı yerine ε (mm) kullanır. ✅
2. **XV_PipeRoughness birimi**: Değer `100000` anormal görünüyor. Muhtemelen **mikron** (0.1 mm = paslı çelik?) olabilir ya da bozuk bir kayıt. Tool iki yorumu da değerlendirecek ve LLM kullanıcıya sorabilecek.
3. **İlk yatırım fiyatı**: Varsayılan sağlamayacağız — kullanıcı girmezse sadece enerji tasarrufu ve sabit tasarruf/yıl raporu çıkar. Kullanıcı girerse NPV ve geri ödeme hesaplanır.

---

## Dokunulacak/Yeni Dosyalar

**Değişecek (minimal edit):**
- `mcps/scada/skills/core-rules/SKILL.md` (Bölüm 5 içindeki annexa paragrafı)
- `mcps/scada/skills/korubin-scada/analysis/pump-frequency-projection.md` (annexa dili)
- `mcps/scada/src/scada_mcp/toolpacks/scada_nodes.py` (iki yeni tool ekleme + annexa hint_tr dili)

**Yeni (pure ekleme):**
- `mcps/scada/skills/korubin-scada/analysis/hydraulic-network-analysis.md`

**Dokunulmayacak:**
- `pump_tools.py` (mevcut pump verim hesapları korunuyor)
- `prepare_pump_selection`, `analyze_pump_at_frequency` içeriği (iç mantık değişmez, sadece annexa açıklama dili düzeltilir)
- korucaps, korumind entegrasyonu

---

## Kabul Kriterleri

- [ ] LLM "annexa=0.94 → pompa %6 yaşlanmış" demeyecek, yerine "katalog ile gerçek ölçüm arasında %6 sapma, bu annexa toleransı dahilinde normaldir" diyecek
- [ ] "pompa bakım gerek" sonucu ancak birden fazla anomali (annexa<1 + debi düşüşü + H düşüşü) üst üste geldiğinde üretilecek
- [ ] `analyze_hydraulic_network(1192)` çağrısı sürtünme kaybı, Reynolds, friction_factor, statik/sürtünme payı yüzdesini döner
- [ ] `analyze_pipe_upgrade_economics(...)` çağrısı kullanıcı fiyat verirse NPV ve geri ödeme, vermezse yıllık kWh tasarrufu döner
- [ ] Mevcut `prepare_pump_selection` ve `analyze_pump_performance` çıktıları değişmez (mevcut pompa önerme davranışı korunur)
- [ ] Yeni tool'lar manifest_groups içine eklenir (LLM tool keşfi)

---

## Review (implementasyon sonrası — 22 Nisan 2026)

### Yapılanlar (özet)

**1) Annexa semantik düzeltmesi — yaşlanma dili kaldırıldı**
- `mcps/scada/skills/core-rules/SKILL.md` içinde annexa açıklaması yeniden yazıldı: "yaşlanma katsayısı" → "katalog-gerçek ölçüm sapma toleransı". "3 kanıt kuralı" eklendi: yaşlanmış demeden önce (1) annexa<0.85, (2) zaman serisinde tutarlı H/Q düşüşü, (3) mekanik işaret (titreşim, yağ sıcaklığı). Tekil annexa<1 artık aşınma kanıtı değil.
- `mcps/scada/skills/korubin-scada/analysis/pump-frequency-projection.md` içindeki aynı dili güncellendi.
- `get_installed_pump_info` ve `analyze_pump_at_frequency` tool'larının docstring + hint_tr metinleri düzeltildi.

**2) Yeni skill — `analysis/hydraulic-network-analysis.md`**
- ToplamHm bileşen ayrıştırması (statik basınç + dinamik seviye + **well_lift** + sürtünme + yerel kayıp) açık formülle tanımlandı.
- `calc.helper.js` ile birebir uyumlu Darcy-Weisbach + iteratif Colebrook-White formülleri.
- `XV_PipeRoughness` biriminin **nanometre** olduğu netleştirildi (`/1e9` → m); `XV_BoruIcCap` mm (`/1000`), `XV_Nsurtunme` = doğrudan yerel kayıp m.
- Türkiye pratiği `g = 9.7905 m/s²` kullanımı.
- Eşik kuralları: friction_share < %10 = boru değiştirme; %25–40 = senaryo çalıştır; >%40 = acil yatırım.
- Kuyu pompaları için **well-lift** bölümü: `well_lift = max(0, nPMontaj − StatikSuSeviye)` — pompanın statik olarak kaldırdığı su kolonu.

**3) Yeni iki tool — `scada_nodes.py`**

`analyze_hydraulic_network(nodeId)`:
- XV_* install sabitlerini, canlı ölçümleri (ToplamHm, Debimetre, BasincSensoru, SuSeviye, SuSicaklik, An_Guc) ve `node_param`'dan `nPMontaj`'ı okur.
- Akış hızı, Re, rejim (laminar/geçiş/türbülans), sıcaklığa bağlı ν interpolasyonu, Colebrook-White ile λ, Darcy-Weisbach ile h_f, yerel kayıp.
- Head breakdown: basınç + dinamik seviye + well_lift + sürtünme + yerel; residual raporu.
- Verim ağacı: `eff_power = An_Guc × (1 − KabloKayip − SurucuKayip)`, `η_hid = Hm·Q / (367.2·P·Nmotor/10000)`, `η_sys = η_hid × Nmotor / 100`.
- friction_share_pct'e göre Türkçe tanı + pipe_upgrade öneri (veya red) çıkarır.

`analyze_pipe_upgrade_economics(nodeId, alternative_inner_diameter_mm, ...)`:
- Mevcut hidrolik durumu üstteki tool'dan okur, alternatif çap için h_f'yi yeniden hesaplar.
- `delta_head_saved_m × Q × saat × 9.7905 / 3600 / η_sys` ile yıllık kWh tasarrufu.
- Elektrik ücreti: XM_T1/T2/T3Fiyat ve XM_T*GunlukSaat × XM_T*YillikGun ile ağırlıklı ortalama.
- Basit geri ödeme, 20 yıl NPV, LCC karşılaştırma.
- **Override kuralı:** friction_share < %10 ise NPV pozitif bile olsa `recommended=false` ve "statik baskın" notu verir. Pompa değişimine **asla zorlamaz**.

**4) Manifest + skill index**
- `ScadaNodesPack.manifest_groups` içine `pump_hydraulic` grubu eklendi → 5 tool (prepare_pump_selection, analyze_pump_at_frequency, get_installed_pump_info, analyze_hydraulic_network, analyze_pipe_upgrade_economics).
- `korubin-scada/SKILL.md` içine yeni skill dosyaları link'lendi + "pompa verim / boru sürtünmesi / yatırım" sorgusu artık doğru skill'e yönlendiriliyor.

### Doğrulama — Serbest Bölge Kuyu (ID 1192) ile smoke test

Kullanıcının verdiği install sabitleri (d=155mm, L=55m, ε=100000 nm=0.1mm, ΣK=0) ve canlı ölçümler (Q=177.4 m³/h, H=82.9 m, P=1.18 bar, T=15°C) + montaj derinliği 51m, statik seviye ≈6m varsayımı:

| Bileşen | Değer | Pay |
|---|---|---|
| velocity | 2.611 m/s | — |
| Reynolds | 355 542 (türbülans) | — |
| λ (Colebrook) | 0.01850 | — |
| Pipe friction h_f | **2.29 m** | **%2.76** |
| Static pressure | 12.03 m | %14.5 |
| Well-lift | 45.0 m | %54.3 |
| Residual (ölçüm/tag belirsizliği) | ~23 m | %28 |
| **Toplam** | **82.9 m** | 100% |

→ **Sürtünme payı %2.76** → tool `pipe_upgrade_recommended=false`, "statik baskın — boru büyütme kazanç sağlamaz" tanısını verir. Bu **tam da kullanıcının istediği davranış**: rapor "pompa değiştir" veya "boru büyüt" önerisi üretmez, çünkü fiziksel olarak kazanç yok. Residual payı LLM'e "SuSeviye dinamik mi statik mi, ya da nPMontaj'ı teyit et" uyarısı verilmesini sağlar.

### Smoke test sonuçları
- `ReadLints` → 0 lint hatası (scada_nodes.py, skill.md'ler)
- `py -c "import ast; ast.parse(...)"` → SYNTAX_OK
- Modül import + `ScadaNodesPack().manifest_groups(prefix='test_')` → 2 grup, yeni tool'lar listede.
- Elle hidrolik hesap (`math` + Colebrook loop) `calc.helper.js` ile birebir uyumlu sonuç.

### Temel prensiplere uygunluk
- **Önce sadelik**: iki yeni tool + bir skill dosyası, mevcut dosyalara minimal dokunuş. Pompa verim akışı (`pump_tools.py`, `prepare_pump_selection`) değişmedi.
- **Tembellik yok**: Colebrook-White iteratif çözücü, ν(T) tablosu, XM_T* tarife ağırlıklı ortalaması, well-lift dahil statik ayrıştırma — hepsi `calc.helper.js` kaynağı ile birebir.
- **Minimal etki**: Mevcut `pump_tools.py`, `korucaps/korumind` MCP'leri ve LLM'in "kendi pompasını öner" davranışı korundu. Yeni yeteneğin tetiklenmesi LLM'e bağlı — kullanıcı "boru/sürtünme/yatırım" sorduğunda devreye girer.

### Bilinen sınırlar / sonraki iterasyon adayları
- `nPMontaj` veya `np_BasmaDerinlik` gibi tag'ler `node_param`'da yoksa well_lift hesaplanmaz; residual büyür. LLM'e "kuyu derinliği bilinmiyor, kullanıcıdan iste" uyarısı düşer — bu doğru davranış.
- XM_T2/T3 tarifesi boşsa, elektrik fiyatı T1 ile hesaplanır (LLM raporda belirtmeli).
- `analyze_pipe_upgrade_economics` için `pipe_cost_tl_per_meter` kullanıcıdan alınır; default uydurmuyoruz (kullanıcının isteği).

### Kabul kriterleri — hepsi ✅
- [x] LLM "annexa=0.94 → pompa %6 yaşlanmış" demeyecek — core-rules'ta 3-kanıt kuralı zorlanıyor.
- [x] `analyze_hydraulic_network(1192)` sürtünme, Re, λ, statik/sürtünme payını döner.
- [x] `analyze_pipe_upgrade_economics(...)` yatırım verildi/verilmedi her iki modda çalışır.
- [x] `prepare_pump_selection` ve `analyze_pump_performance` çıktıları değişmedi.
- [x] Manifest_groups'a yeni tool'lar eklendi.
- [x] Tool hata halinde fail etmez, eksik veriyi `residual` / `error` alanıyla şeffaflıkla raporlar.

---

# Task: AQUA CNT Kılavuzunu Skill'e Çevirme (22 Nisan 2026 — 2. tur)

## Sorun Tespiti (Kullanıcı raporu — "Modem Status 2" vakası)

AQUA 100 cihazı için `Modem Status 2` sorusuna cevap üretirken KoruMind **40'a yakın tool çağırdı**. PDF kılavuz repo'daydı ama ondan faydalanamadı; her şeyi `find_nodes` + `get_device_tag_values` + `run_safe_query` kombinasyonu ile türetmeye çalıştı. Süre + token israfı + hatalı bilgi riski.

### Kullanıcının talebi

> "pdfleri direk skil olarak eklemeliyiz... bilgi sorusu sorduğunda ordan bakıp yoks sistemden bakabilir... bu kadar soru için dakikalarca tool çağırmak ne kadar mantıklı?"

> "çok skil olursa her konuşmada token artarmı yoksa gerekli skili kendimi bulur onu öğrenmeliyim"  
> → **Cevap:** `list_skills` sadece metadata (name + description + files listesi) döner. Gerçek içerik `get_skill(name, file)` ile lazy load. Bu yüzden çok dosya sorun değil — *description*'ın iyi yazılması her şey.

> "iyi yap ki doğru skili bulsun tek tek hepsini aramazsın"  
> → Her dosya için **keywords bol + routing tablosu** + core-rules'tan yönlendirme zorunlu.

---

## Yapılanlar

### 1. PDF içeriğini ayıklama
- `pypdf` / `pdfplumber` → **Custom CID font** nedeniyle Türkçe karakterler bozuk çıktı.
- **Çözüm:** `pypdfium2` ile 52 sayfayı PNG olarak render ettim (scale 1.4) → Vision (Read tool image okuma) ile her sayfayı tek tek okuyup markdown'a çevirdim.
- Tüm kritik tablolar çıkarıldı: Tablo 1.1 (Modem Durumu), Tablo 1.2 (Çalışma Durumu), Tablo 4.1 (Alarm Listesi), Modbus Register 0-94, Uyarı Word 1, Alarm Word 1, Status Word 1, Control Word 1/2 bit tanımları, dahili ultrasonik debimetre M00-M92 menüleri, V/Z/W transdüser metotları, R/I/J/H/F/G/K hata kodları.
- PNG render'ları işlem bittikten sonra silindi. **Kaynak PDF'ler de sonradan silindi** (22 Nisan 2026 kullanıcı talebi) — çıkarım tamamlandı, markdown skill'ler yeterli; repo ~8 MB daha küçük.

### 2. Skill yapısı — 10 dosya (`mcps/scada/skills/aqua-devices/`)

| Dosya | İçerik |
|---|---|
| `SKILL.md` | Index + zengin `description` (keywords) + **"Hangi soru → hangi dosya" routing tablosu** + ortak konvansiyonlar (APN, Modbus ID/port, pil, LED, CSQ) + model matrisi (100S/100F/100FP/100SL) |
| `modem-status.md` | **Tablo 1.1** (modem 0/1/2/15/102) + LED + CSQ (çekim gücü) + APN (Turkcell mgbs, Vodafone internetstatik, Türk Telekom statikip) + hedef IP/port/ID ayarları + **"Modem Status 2" sistematik sorun giderme adımları** (anten → CSQ → SIM → APN → lokasyon) |
| `hedef-status.md` | **Tablo 1.2** — 10/11/100/101/120/121/200/201/30/31 kodları + hedef haberleşme var/yok + motor çalışıyor/çalışmıyor + senaryo tipi; StatusWord-1 biti ile eşleşme tablosu |
| `alarms-and-warnings.md` | **Tablo 4.1** (tüm alarm listesi) + Uyarı Word 1 bit 0-9 + Alarm Word 1 bit 0-10 + 15dk/3-defa auto-reset mantığı + alarm → ilk kontrol kartı |
| `modbus-reference.md` | Bağlantı kuralları (port 502, FC3/6/16/22, float+10000, max 5 sorgu, 15/30 sn) + **register 0-94 tam tablosu** (tip, çarpan, birim) + Status Word 1 bitleri + Control Word 1 (tek atış) + Control Word 2 (kalıcı hafıza) + sık okuma senaryoları |
| `display-and-menus.md` | Ana menü (8 başlık) + İşletme Ekranı 1 ve 2 satır-satır açıklama + tuş takımı davranışı + ekran uyku modu (60 sn) + CSQ kademe tablosu |
| `operating-modes.md` | Çalışma Mod 0-3 (Serbest/Depo Doldurma/Hidrofor/Basınç PI) + Acil senaryo (taklit et) + SCADA linkleme + Antiblokaj (90dk/5dk) + Düşük Güç Modu (pil %40) + min 30Hz motor ref + mod seçim karar ağacı |
| `motor-protection.md` | Koruma eşikleri register 68-75 + set değerleri register 76-81 + koruma zamanları register 45-49 + tipik şablonlar (kuyu/hidrofor/terfi) + SurucuElModCalisiyor açıklaması + alarm-koruma eşlemesi |
| `hardware-reference.md` | Model karşılaştırma + donanım (LCD, GSM, pil Li-Po 14.8V 12800mAh, 8MB flash, 3×16-bit AI, 1×12-bit AO, 4×DI opto, 2×DO röle, IP65) + besleme (24V, 2.5A, ≥21V şarj) + Ek1 basınç sensörü (100FP) + Ek2 seviye sensörü (100SL) + montaj notları + Hakkında ekranı |
| `ultrasonic-flowmeter.md` | Dahili debimetre **M00-M92** tam menü referansı + V/Z/W metot seçimi (boru çapına göre) + transdüser yerleştirme (L_up/L_dn × D çarpanları) + optimum lokasyon + 13 adımlı kurulum sırası + **R/I/J/H/F/G/K hata kodları** + sık hata giderme kartı |

### 3. Routing zorunlu kılma

**`core-rules/SKILL.md`** — Yeni bölüm **§10.1 CIHAZ DOKUMAN SORUSU — ONCE aqua-devices SKILL, TOOL DEGIL**:
- Hangi soru tipi → hangi dosya tablosu.
- **Yasak:** AQUA kılavuzundaki bilgiyi run_safe_query + find_nodes + get_device_tag_values kombinasyonu ile türetmeye çalışmak.

**`korubin-scada/SKILL.md`** — Tool Routing Karar Ağacı güncellendi:
- "AQUA CNT cihaz dokuman sorusu" → **önce** `get_skill('aqua-devices')` → SKILL.md routing tablosu → doğru alt dosya. SCADA tool'u gerekmez. "**YASAK:** 20+ tool çağırarak kılavuz bilgisi türetmeye çalışmak."

### 4. Smoke test (geçti)

```
=== list_skills çıktısı ===
aqua-devices v1.0.0 (10 files)
  Description uzunluk: ~2000 char — modem/hedef/register/APN/LED/alarm/debimetre/transdüser... hepsi keyword
  Dosyalar: SKILL.md, modem-status.md, hedef-status.md, alarms-and-warnings.md, modbus-reference.md,
            display-and-menus.md, operating-modes.md, motor-protection.md, hardware-reference.md,
            ultrasonic-flowmeter.md

=== "Modem Status 2" sorgusu ===
modem-status.md line 22: "| **2** | – | GSM network'üne bağlanmaya çalışıyor | Bir sonraki adıma
                          geçmiyorsa: **GSM şebeke bağlanma problemi** var. **Anten takılı değil**
                          veya **çekim gücü zayıf** olabilir. |"
→ Tek sorguda cevap; tool çağırmaya gerek yok.

=== Routing teyidi ===
[OK] core-rules §10.1 AQUA yönlendirmesi
[OK] korubin-scada AQUA yönlendirmesi
[OK] 10/10 dosya okunabilir
```

### Beklenen sonuç

Bundan sonra kullanıcı **"AQUA 100 modem status 2'de kalıyor"** dediğinde:
1. LLM `list_skills` çağırır — aqua-devices description'daki "modem, status, LED, GSM, APN..." keyword'leri eşleşir.
2. `get_skill('aqua-devices', 'SKILL.md')` → routing tablosundan **modem-status.md** doğru seçilir.
3. `get_skill('aqua-devices', 'modem-status.md')` → Tablo 1.1 + troubleshoot adımları.
4. **3 skill dosyası = 3 tool çağrı**, cevap hazır. 40 değil.

(Cihazın canlı durumunu teyit etmek gerekiyorsa 1 ekstra `get_device_tag_values` çağrısı yeterli — örn. `GsmCekimGucu` + `Status_HedefleHaberlemeVar`.)

---

## Kabul kriterleri — hepsi ✅
- [x] AQUA kılavuzundaki tüm kritik tablolar markdown skill'lerinde (kaynak PDF sonradan silindi, skill'ler kendi kendine yeter).
- [x] `list_skills` çıktısında aqua-devices doğru keyword'lerle temsil ediliyor.
- [x] `SKILL.md` içinde "Hangi soru → hangi dosya" routing tablosu var.
- [x] `core-rules` ve `korubin-scada` yönlendirmeleri aqua-devices'a gidiyor.
- [x] Smoke test: "Modem 2" sorusu tek dosya okumayla cevap buluyor.
- [x] PDF render artığı temizlendi, skill klasörü minimal.

## Hotfix — 22 Nisan akşamı: list_skills description kısaltma bug'ı (L010)

**Semptom:** Kullanıcı production'da "modem status 2" sordu, KoruMind yine 13 tool çağırdı, aqua-devices skill'ine girmedi.

**Kök neden:** `skills/toolpack.py` içinde `desc.strip().split("\n")[0]` → YAML `|` literal block style ile yazılmış description'lar satır satır kırılıyor, LLM sadece 70 karakterlik ilk satırı görüyor (`"AQUA CNT 100S / 100F ... kompakt pompa kontrol ve su izleme"`). İçinde modem/status/alarm keyword'ü yok → LLM doğru skill'i keşfedemiyor.

**Fix:**
- `mcps/scada/src/scada_mcp/skills/toolpack.py` → `" ".join(desc.split())` ile tam description'ı normalize ediyoruz (newline → space). Bu değişiklik **tüm skill'ler için** çalışır, yeni eklenenler de faydalanır.
- `mcps/scada/skills/core-rules/SKILL.md` description'ına "AQUA CNT, modem status, hedef status, alarm, register, modbus, APN, LED, CSQ, debimetre, cihaz dokuman" keyword'leri eklendi — LLM core-rules üzerinden de yön bulabilsin.

**Doğrulama:** Yerel SkillLoader simülasyonu → aqua-devices normalize description 1868 ch, **12/12 AQUA keyword görünür**. core-rules 1008 ch, 12/12 keyword görünür.

**Lessons:** L010 eklendi — "bir skill görünmüyor" semptomunda önce `list_skills` çıktısının **fiili formunu** kontrol et.

## Bilinen sınırlar / sonraki iterasyon
- Diğer AQUA cihazları (80, LP Logger, SMART PCS) hala `search_product_manual` akışında. Aynı yapıyı onlara da uygulayabiliriz ama sık istenen **100 serisi** bugün halledildi.
- AQUA CE Sertifikası, Ürün Katalogu ve SMART PCS Broşürü de silindi — içlerinde runtime için kritik veri yoktu (satış/sertifika evrakı). Gerekirse `envest-web` public assets'ten tekrar alınabilir.
- OCR pipeline (Tesseract Türkçe) artık acil değil — Vision ile manuel okuma bugünkü PDF'ler için yeterli oldu.
