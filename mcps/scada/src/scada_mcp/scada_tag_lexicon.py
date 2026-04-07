"""
Korubin SCADA log/tag adlandırma varsayılanları.
Ekran tipine özel sabit tanımlı değilse bu kalıplar ve önek kuralları geçerlidir (Türkçe açıklamalı).
"""

from __future__ import annotations

import re
from typing import Any

# --- Varsayılan arama parçaları (tagPath / açıklama LIKE ile eşleşir) ---
# Kullanıcı «debi» dediğinde: debimetre1/2, demimetre (yaygın yazım) dahil.
DEFAULT_DEBI_SEARCH_FRAGMENTS: tuple[str, ...] = (
    "debimetre",
    "debimetre1",
    "debimetre2",
    "demimetre",
    "deminetre",
    "debi",
    "akış",
    "akis",
    "flow",
)
DEFAULT_GUC_SEARCH_FRAGMENTS: tuple[str, ...] = (
    "an_guc",
    "p1_guc",
    "güç",
    "guc",
    "aktif",
    "power",
    "kw",
    "motoraktif",
    "MotorAktifGüç",
)
DEFAULT_STATIK_SEVIYE_FRAGMENTS: tuple[str, ...] = (
    "statik",
    "StatikSuSeviye",
    "statikseviye",
)
DEFAULT_DINAMIK_SEVIYE_FRAGMENTS: tuple[str, ...] = (
    "dinamik",
    "dinamikseviye",
    "SuSeviye",
    "suseviye",
    "dinamik seviye",
)
# Statik/dinamik yok ama «seviye» denmişse
DEFAULT_GENEL_SEVIYE_FRAGMENTS: tuple[str, ...] = (
    "suseviye",
    "su seviye",
    "seviye",
    "level",
    "SuSeviye",
)
# Kuyu çıkış / hat basıncı (kuruluma göre değişir; tipik adaylar)
DEFAULT_KUYU_CIKIS_BASINC_FRAGMENTS: tuple[str, ...] = (
    "basincsensoru",
    "basınçsensoru",
    "BasincSensoru",
    "kuyuçıkış",
    "kuyucikis",
)
DEFAULT_HAT_BASINC_FRAGMENTS: tuple[str, ...] = (
    "hatbasinc",
    "hatbasınc",
    "hatbasıncsensoru",
    "hatbasincsensoru",
    "basincsensoru2",
    "BasincSensoru2",
    "hat basınç",
)

# analyze_dma_seasonal_demand vb. için tek satır ipucu (ek genişleme resolve içinde de yapılır)
DEFAULT_DMA_DEBI_HINT = "debimetre debimetre1 debimetre2 demimetre debi akış flow"
DEFAULT_COMPARE_GUC_HINT = "an_guc p1_guc güç aktif power kw MotorAktifGüç"
DEFAULT_LEVEL_HINT = (
    "dinamik seviye SuSeviye suseviye statik StatikSuSeviye depo DepoSeviye kuyu "
    "yeraldi yersuyu seviye level"
)

_OZET_TR = """
Ekran tipine özel tablo yoksa yaygın varsayılanlar:
• Debi: Debimetre, Debimetre1, Debimetre2; bazen «Demimetre» yazımı. «Güç»: an_guc, p1_guc, aktif kW benzeri.
• Seviye: «statik seviye» statik seviyedir; «dinamik seviye» dinamik seviyedir; aksi belirtilmedikse genel su/seviye SuSeviye vb.
• Kuyu çıkış basıncı çoğunlukla basincsensoru; hat basıncı hatbasinc, hatbasıncsensoru, ikinci hat için basincsensoru2 vb. olabilir.
• x ile başlayan tagler çoğunlukla ayar/set parametresidir.
• al_ ile başlayan: cihaz alarmı; xe: emniyet alarmı; xd: genelde depo alarmı.
Bu liste öneridir; gerçek tag yolları projeye göre değişir — şüphede log parametre listesini doğrulayın.
""".strip()


def _norm_blob(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _dedupe_keep_order(xs: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in xs:
        k = x.strip().lower()
        if len(k) < 2 or k in seen:
            continue
        seen.add(k)
        out.append(x.strip())
    return out


def hint_expansion_fragments(hint: str) -> list[str]:
    """
    Kısa doğal dil ipuçlarını SQL LIKE için parçalara çevirir (OR ile birleştirilebilir).
    """
    raw = (hint or "").strip()
    if not raw:
        return []
    nb = _norm_blob(raw)
    out: list[str] = []

    # Kullanıcının kendi tokenları
    parts = re.split(r"[\s,;]+", raw)
    for p in parts:
        p = p.strip()
        if len(p) > 1:
            out.append(p)

    def wants_debi() -> bool:
        return any(
            x in nb
            for x in (
                "debi",
                "debimetre",
                "demimetre",
                "deminetre",
                "akış",
                "akis",
                "flow",
                "debimetre1",
                "debimetre2",
            )
        )

    def wants_guc() -> bool:
        return any(x in nb for x in ("güç", "guc", "kw", "power", "aktif", "an_guc", "p1_guc", "motor"))

    def wants_seviye() -> bool:
        return "seviye" in nb or "seviyesi" in nb or "level" in nb or "suseviye" in nb.replace(" ", "")

    def wants_basinc() -> bool:
        return "basınç" in nb or "basinc" in nb or "basınç" in raw.lower()

    if wants_debi():
        out.extend(DEFAULT_DEBI_SEARCH_FRAGMENTS)
    if wants_guc():
        out.extend(DEFAULT_GUC_SEARCH_FRAGMENTS)
    if wants_seviye():
        if "statik" in nb:
            out.extend(DEFAULT_STATIK_SEVIYE_FRAGMENTS)
        elif "dinamik" in nb:
            out.extend(DEFAULT_DINAMIK_SEVIYE_FRAGMENTS)
        else:
            out.extend(DEFAULT_GENEL_SEVIYE_FRAGMENTS)
    if wants_basinc():
        if "hat" in nb:
            out.extend(DEFAULT_HAT_BASINC_FRAGMENTS)
        if "kuyu" in nb and ("çıkış" in nb or "cikis" in nb or "çıkış" in raw.lower()):
            out.extend(DEFAULT_KUYU_CIKIS_BASINC_FRAGMENTS)
        elif wants_basinc() and "hat" not in nb and "kuyu" not in nb:
            out.extend(DEFAULT_KUYU_CIKIS_BASINC_FRAGMENTS)
            out.extend(DEFAULT_HAT_BASINC_FRAGMENTS)

    return _dedupe_keep_order(out)[:22]


def tag_path_prefix_role_tr(tag_path: str) -> str | None:
    """Tag yolunun başına göre kısa rol; bilinmiyorsa None."""
    tp = (tag_path or "").strip()
    if not tp:
        return None
    low = tp.lower()
    if low.startswith("al_"):
        return "cihaz_alarmi"
    if low.startswith("xe"):
        return "emniyet_alarmi"
    if low.startswith("xd"):
        return "depo_alarmi_genelde"
    if low.startswith("x"):
        return "ayar_parametresi_setpoint"
    return None


def scada_tag_lexicon_payload() -> dict[str, Any]:
    """MCP / model referansı için yapılandırılmış özet."""
    return {
        "_type": "scada_tag_lexicon",
        "kapsam_tr": (
            "Ekran tipine özel sabit yoksa geçerli sayılan varsayılan tag kalıpları ve önek anlamları. "
            "Gerçek proje farklı olabilir; logParamId ile doğrulama önerilir."
        ),
        "varsayilan_aranacak_parcalar": {
            "debi_akış": list(DEFAULT_DEBI_SEARCH_FRAGMENTS),
            "güç_kw": list(DEFAULT_GUC_SEARCH_FRAGMENTS),
            "statik_seviye": list(DEFAULT_STATIK_SEVIYE_FRAGMENTS),
            "dinamik_seviye": list(DEFAULT_DINAMIK_SEVIYE_FRAGMENTS),
            "seviye_genel_fallback": list(DEFAULT_GENEL_SEVIYE_FRAGMENTS),
            "kuyu_çıkış_basınç_tipik": list(DEFAULT_KUYU_CIKIS_BASINC_FRAGMENTS),
            "hat_basınç_tipik": list(DEFAULT_HAT_BASINC_FRAGMENTS),
        },
        "on_ek_kurallari_tr": {
            "x_ile_baslayan": "Ayar / setpoint parametresi (ekran tipine göre istisna olabilir).",
            "al_": "Cihaz alarmı.",
            "xe": "Emniyet alarmı.",
            "xd": "Genelde depo alarmı.",
        },
        "tek_satir_ipuclari": {
            "dma_debi": DEFAULT_DMA_DEBI_HINT,
            "karsilastirma_guc": DEFAULT_COMPARE_GUC_HINT,
            "seviye_genel": DEFAULT_LEVEL_HINT,
        },
        "ozet_paragraf_tr": _OZET_TR,
        "panel_sablon_ek_not_tr": (
            "Ekran şablonlarında (MENU.phtml, genel/MAIN.phtml) div id ile canlı tag eşlemesi ve ürün kılavuzu "
            "ile _tagoku ayrımı için MCP’de (instance önekli) get_korubin_ui_and_tool_routing_tr kullanılır."
        ),
    }
