---
name: nview-a-dma-ocp110
description: |
  nView 'a-dma-ocp110' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-dma-ocp110" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: Debimetre, a-dma-ocp110.
version: "1.0.0"
generated: true
source: //10.10.10.72/public/dev.korubin/app/views/point/display/common/a-dma-ocp110/GENEL.phtml
---

# nView: a-dma-ocp110

Aile bağlamı: **dma.md (debi bölge K-Means + basınç ölçekleme)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `Debimetre` | Debi ölçümü (m³/h) | m³/h | 2 | measurement |  |
| `debimetreLt` |  | lt/sn | 2 | unknown |  |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **measurement**: `Debimetre2`
- **unknown**: `_NoError`, `js`

## Birim Özeti

- **Debi**: `Debimetre`, `debimetreLt`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
