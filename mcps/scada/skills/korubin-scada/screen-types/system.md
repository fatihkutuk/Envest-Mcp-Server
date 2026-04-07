---
name: screen-type-system
description: |
  Sistem / genel gozetim ekran tipi bilgisi.
  Use when: nView "system" iceren ekranlar, multi-node gozetim soruldugunda.
  Keywords: system, sistem, genel, gozetim, multi, overview.
version: "1.0.0"
---

# Sistem Ekran Tipi (System / Overview)

## nView Ornekleri
- `a-system` - Standart sistem ekrani
- `a-system-v2`, `a-system-yeni` - Yeni versiyonlar
- `a-system-advanced` - Gelismis sistem
- `a-system-editable` - Duzenlenebilir
- `a-system-editor-lite` - Hafif editor
- `a-system-baski` - Baski versiyonu
- `a-system-beypazari`, `a-system-kalecik`, `a-system-tosya`, `a-system-urgup`, `a-system-ortakoy`, `a-system-limak`, `a-system-edremit`, `a-system-everest` - Kuruluma ozel versiyonlar
- `a-system-n` - N versiyonu
- `_a-multi`, `_a-multi-elma-bahce` - Coklu gozetim ekranlari (alt cizgi ile baslar)

**Process adapter**: `system` (nType=666 veya nView "a-system"/"_a-multi" ile baslayan)

## Amaclari
Sistem ekranlari birden fazla noktayi tek ekranda gosteren gozetim ekranlaridir:
- Tum kuyularin durumunu tek ekranda goruntuleme
- Tum depolarin seviyelerini izleme
- Tum terfi istasyonlarinin durumunu gozetleme
- Bolgesel harita gorunumu

## Ozel Ekranlar

### a-envest-default
Envest varsayilan ekrani - ilk giris veya tanamsiz ekran tipi icin.

### a-envest-verimerkezi
Veri merkezi gozetim ekrani.

### Ozel alan ekranlari
- `a-debi-izleme` - Debi izleme
- `a-pressure` - Basinc izleme
- `a-gozlem-m`, `a-gozlem-v2` - Gozlem/monitoring
- `a-izleme-p`, `a-izleme-limak` - Izleme
- `a-network-g`, `a-network-pr` - Network gozetim

## Veri Sorgulama
Sistem ekranlari genellikle birden fazla node'dan veri ceker. LLM icin:
- `get_scada_summary` - Tum sistem ozeti
- `get_node_distribution` - Node dagilimi
- `get_scada_system_stats` - Tag istatistikleri
- `list_nodes` - Tum nodeleri listele
- `find_nodes_by_keywords` - Node ara
