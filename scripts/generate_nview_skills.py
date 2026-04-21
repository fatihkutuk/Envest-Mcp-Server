"""
nView başına skill markdown dosyası üreten offline generator.

Kaynak: `<source>/<nView>/GENEL.phtml` ve `MENU.phtml`
Hedef : `<out>/<nView>.md`

Kullanım:
    python scripts/generate_nview_skills.py --nview a-kuyu-envest --dry-run
    python scripts/generate_nview_skills.py --nview a-kuyu-envest
    python scripts/generate_nview_skills.py --all           # tüm dizinler
    python scripts/generate_nview_skills.py --source ... --out ...

Çıktı idempotent (aynı girdi -> aynı çıktı). Frontmatter'da `generated: true`
işareti vardır; elle düzenlenen dosyaların regenerate edilirken üzerine
yazılmaması isteniyorsa `--skip-existing` verilir.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_SOURCE = "//10.10.10.72/public/dev.korubin/app/views/point/display/common"
DEFAULT_OUT = "mcps/scada/skills/korubin-scada/screen-types/nview"

# Tag prefix / isim rolü sözlüğü — aile skill'lerinden (kuyu.md, dma.md) türetildi.
TAG_PREFIX_ROLES: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"^XS_"), "sensor_setpoint", "Sensör kalibrasyon / scale ayarı (yazma)"),
    (re.compile(r"^XD_"), "dimension_setting", "Yapı/depo sabit boyut ayarı (yazma)"),
    (re.compile(r"^XE_"), "safety_param", "Emniyet eşiği (alt/üst/süre/eylem)"),
    (re.compile(r"^XC_"), "operating_mode", "Çalışma modu / mod seçim"),
    (re.compile(r"^XV_"), "install_constant", "Kurulum değişmezi (boru, motor, vb.)"),
    (re.compile(r"^XA_"), "analog_instant", "Anlık analog değer (ör. 4-20mA)"),
    (re.compile(r"^T_"), "counter", "Toplam sayaç (su, elektrik, çalışma, şalt)"),
    (re.compile(r"^An_"), "instant_electrical", "Anlık elektrik/motor ölçümü"),
    (re.compile(r"^Al_"), "alarm", "Alarm bayrağı"),
    (re.compile(r"^P\d_"), "pump_measurement", "Pompa bazlı ölçüm"),
    (re.compile(r"^np_"), "static_catalog", "STATİK katalog değeri — canlı değil, pompa seçiminde KULLANMA"),
]

TAG_NAME_ROLES: dict[str, str] = {
    "Debimetre": "Debi ölçümü (m³/h)",
    "Debimetre1": "Debi ölçümü 1",
    "Debimetre2": "Debi ölçümü 2",
    "BasincSensoru": "Çıkış basıncı",
    "BasincSensoru2": "Hat basıncı",
    "HatBasincSensoru": "Hat basıncı",
    "SuSeviye": "Dinamik su seviyesi",
    "StatikSeviye": "Statik su seviyesi",
    "StatikSuSeviye": "Statik su seviyesi",
    "dinamikseviye": "Dinamik seviye",
    "ToplamHm": "Toplam basma yüksekliği",
    "toplamHm": "Toplam basma yüksekliği (alias)",
    "kuyukot": "Kuyu kotu (altitude)",
    "depokot": "Depo kotu (altitude)",
    "CikisDepoSeviye": "Çıkış deposu seviyesi",
    "CikisDepoSeviye2": "İkinci çıkış deposu seviyesi",
    "BakiyeKlor": "Bakiye klor",
    "KlorSensoru": "Klor sensörü",
    "NPSHSeviye": "NPSH seviye",
    "SuSicaklik": "Su sıcaklığı",
    "MotorSicaklik": "Motor sıcaklığı",
    "PanoSicaklik": "Pano sıcaklığı",
    "DisOrtamSicaklik": "Dış ortam sıcaklığı",
    "Bulaniklik": "Bulanıklık (NTU)",
    "GirisToplamDebi": "Giriş toplam debi",
    "CikisToplamDebimetre": "Çıkış toplam debi",
    "Pompa1StartStopDurumu": "Pompa 1 start/stop durumu",
    "Pompa1StartStopWr": "Pompa 1 start/stop yazma kontrolü",
    "Pompa1OtoWr": "Pompa 1 Oto/Manuel yazma kontrolü",
}


def infer_role(tag_id: str) -> tuple[str, str]:
    """(role_code, description) — tag isimden önce prefix kuralı, sonra sözlük."""
    # Prefix kontrolü
    for pat, code, desc in TAG_PREFIX_ROLES:
        if pat.match(tag_id):
            return code, desc
    # İsim sözlüğü
    if tag_id in TAG_NAME_ROLES:
        return "measurement", TAG_NAME_ROLES[tag_id]
    # Alfabetik küçük/büyük varyantları dene
    if tag_id.lower() in {k.lower() for k in TAG_NAME_ROLES}:
        for k, v in TAG_NAME_ROLES.items():
            if k.lower() == tag_id.lower():
                return "measurement", v
    # Start/Stop / Wr suffix -> yazma kontrolü
    if tag_id.endswith("Wr"):
        return "write_control", "Yazma kontrolü (switch/setpoint)"
    if "StartStop" in tag_id or "Durum" in tag_id:
        return "status", "Durum / mod göstergesi"
    return "unknown", ""


# --- Regex: <dim> ve <div class="col..."> blokları içinden id / fixed / t / z çıkar ---

# Not: PHP-mixed içerikte basit line-based regex güvenli değil. Çok satırlı bloklar için DOTALL kullanılır.

_DIM_BLOCK = re.compile(
    r"""<dim\s+([^>]*?)>(.*?)</dim>""",
    re.DOTALL | re.IGNORECASE,
)
_COL_BLOCK = re.compile(
    r"""<div\s+class="col\d*"\s+([^>]*?)>(.*?)</div>""",
    re.DOTALL | re.IGNORECASE,
)
_DIV_WITH_ID_BLOCK = re.compile(
    r"""<div\s+([^>]*?\bid=["'][^"']+["'][^>]*?)>(.*?)</div>""",
    re.DOTALL | re.IGNORECASE,
)

_ATTR_ID = re.compile(r"""\bid\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
_ATTR_FIXED = re.compile(r"""\bfixed\s*=\s*["']?(\d+)["']?""", re.IGNORECASE)
_INNER_T = re.compile(r"""<t[^>]*>(.*?)</t>""", re.DOTALL | re.IGNORECASE)
_INNER_Z = re.compile(r"""<z[^>]*>(.*?)</z>""", re.DOTALL | re.IGNORECASE)
_LANGT = re.compile(r"""<\?=?\s*langt\(\s*['"]([^'"]+)['"]\s*\)\s*\?>""")
_PHP_ANY = re.compile(r"""<\?=?.*?\?>""", re.DOTALL)


def _clean_label(raw: str | None) -> tuple[str | None, str | None]:
    """(label, langt_key) — label PHP'siz düz metin, langt_key varsa ham key."""
    if not raw:
        return None, None
    s = raw.strip()
    if not s:
        return None, None
    # langt('x') varsa önce key çıkar
    m = _LANGT.search(s)
    langt_key = m.group(1) if m else None
    # Tüm PHP blokları temizle
    s = _PHP_ANY.sub("", s).strip()
    s = re.sub(r"\s+", " ", s).strip(" :")
    return (s or None), langt_key


def parse_genel_phtml(content: str) -> dict[str, dict]:
    """Çıktı: {tag_id: {unit, fixed, label, langt_key, role, role_desc, container}}"""
    results: dict[str, dict] = {}
    # dim blokları
    for attrs, inner in _DIM_BLOCK.findall(content):
        mid = _ATTR_ID.search(attrs)
        if not mid:
            continue
        tag_id = mid.group(1)
        fixed_m = _ATTR_FIXED.search(attrs)
        fixed = int(fixed_m.group(1)) if fixed_m else None
        t_m = _INNER_T.search(inner)
        z_m = _INNER_Z.search(inner)
        label, langt_key = _clean_label(t_m.group(1) if t_m else None)
        unit, _ = _clean_label(z_m.group(1) if z_m else None)
        role, role_desc = infer_role(tag_id)
        if not label and role_desc:
            label = role_desc
        if tag_id not in results:
            results[tag_id] = {
                "unit": unit,
                "fixed": fixed,
                "label": label,
                "langt_key": langt_key,
                "role": role,
                "role_desc": role_desc,
                "container": "dim",
            }
    # col2/col blokları (div class="col*")
    for attrs, inner in _COL_BLOCK.findall(content):
        mid = _ATTR_ID.search(attrs)
        if not mid:
            continue
        tag_id = mid.group(1)
        if tag_id in results:
            continue
        fixed_m = _ATTR_FIXED.search(attrs)
        fixed = int(fixed_m.group(1)) if fixed_m else None
        t_m = _INNER_T.search(inner)
        z_m = _INNER_Z.search(inner)
        label, langt_key = _clean_label(t_m.group(1) if t_m else None)
        unit, _ = _clean_label(z_m.group(1) if z_m else None)
        role, role_desc = infer_role(tag_id)
        if not label and role_desc:
            label = role_desc
        results[tag_id] = {
            "unit": unit,
            "fixed": fixed,
            "label": label,
            "langt_key": langt_key,
            "role": role,
            "role_desc": role_desc,
            "container": "col",
        }
    # Bir de üst seviye <div id="X"> blokları içinde sensör tipindeki ID'ler olabilir
    for attrs, inner in _DIV_WITH_ID_BLOCK.findall(content):
        mid = _ATTR_ID.search(attrs)
        if not mid:
            continue
        tag_id = mid.group(1)
        if tag_id in results:
            continue
        # sadece <z>…</z> ya da <t>…</t> varsa değerli
        z_m = _INNER_Z.search(inner)
        t_m = _INNER_T.search(inner)
        if not (z_m or t_m):
            continue
        # ID'ler layout div'leri (textLayer, nscreen, ctrlLayer vb.) olmamalı
        if tag_id.lower() in {"nscreen", "textlayer", "ctrllayer", "depoval", "effmeter"}:
            continue
        fixed_m = _ATTR_FIXED.search(attrs)
        fixed = int(fixed_m.group(1)) if fixed_m else None
        label, langt_key = _clean_label(t_m.group(1) if t_m else None)
        unit, _ = _clean_label(z_m.group(1) if z_m else None)
        role, role_desc = infer_role(tag_id)
        if not label and role_desc:
            label = role_desc
        results[tag_id] = {
            "unit": unit,
            "fixed": fixed,
            "label": label,
            "langt_key": langt_key,
            "role": role,
            "role_desc": role_desc,
            "container": "div",
        }
    return results


_DATA_ACCESS = re.compile(r"""\bdata\.([A-Za-z_][A-Za-z0-9_]*)""")
_DATA_BRACKET = re.compile(r"""\bdata\[\s*["']([A-Za-z_][A-Za-z0-9_]*)["']\s*\]""")


def parse_data_refs(content: str) -> list[str]:
    """JS blokundaki `data.X` / `data["X"]` tag isimlerini toplar."""
    seen: dict[str, bool] = {}
    for m in _DATA_ACCESS.finditer(content):
        seen[m.group(1)] = True
    for m in _DATA_BRACKET.finditer(content):
        seen[m.group(1)] = True
    return sorted(seen.keys())


_MENU_LINK = re.compile(
    r"""<a\s+href=["']\./([^"']+)["'][^>]*>(.*?)</a>""",
    re.DOTALL | re.IGNORECASE,
)
_MAIN_LINKED = re.compile(
    r"""\$linked\s*=\s*["']([^"']+)["']""",
    re.IGNORECASE,
)

# Subpage içeriği için patternler:
#  <h1>Başlık</h1> — sayfa başlığı
#  <f id="XD_..." fixed="N">…<z>UNIT</z>…</f> — kaydedilebilir ayar parametresi
_SUB_H1 = re.compile(r"""<h1[^>]*>(.*?)</h1>""", re.DOTALL | re.IGNORECASE)
_SUB_F_FIELD = re.compile(
    r"""<f\b([^>]*\bid\s*=\s*["'][^"']+["'][^>]*)>(.*?)</f>""",
    re.DOTALL | re.IGNORECASE,
)


def parse_menu_phtml(content: str) -> list[dict]:
    rows: list[dict] = []
    for href, inner in _MENU_LINK.findall(content):
        # label: <l>...</l> veya tüm iç metin
        l_m = re.search(r"""<l[^>]*>(.*?)</l>""", inner, re.DOTALL | re.IGNORECASE)
        label, langt_key = _clean_label(l_m.group(1) if l_m else inner)
        rows.append({"page": href.strip(), "label": label or "", "langt_key": langt_key})
    return rows


def parse_subpage(path: Path) -> dict:
    """Alt sayfa (menü linkindeki phtml) için başlık + form alan ID'lerini çıkar."""
    if not path.is_file():
        return {"found": False, "title": None, "title_langt_key": None, "fields": []}
    content = path.read_text(encoding="utf-8", errors="replace")
    h1_m = _SUB_H1.search(content)
    title, title_key = _clean_label(h1_m.group(1) if h1_m else None)
    fields: list[dict] = []
    for attrs, inner in _SUB_F_FIELD.findall(content):
        mid = _ATTR_ID.search(attrs)
        if not mid:
            continue
        fid = mid.group(1)
        fixed_m = _ATTR_FIXED.search(attrs)
        fixed = int(fixed_m.group(1)) if fixed_m else None
        z_m = _INNER_Z.search(inner)
        unit, _ = _clean_label(z_m.group(1) if z_m else None)
        fields.append({"id": fid, "unit": unit or "", "fixed": fixed})
    return {"found": True, "title": title, "title_langt_key": title_key, "fields": fields}


def parse_main_linked(content: str) -> str | None:
    """MAIN.phtml'de `$linked = 'X'` referansı varsa X'i döndür (parent nView)."""
    m = _MAIN_LINKED.search(content)
    return m.group(1).strip() if m else None


# uisettings.phtml — checkbox ile hangi tag/sensörün UI'da aktif olduğunu seçtiren sayfa.
# Pattern: <tr><td><?= langt('Label') ?></td>...<nf id='ui_X'><input...></nf></tr>
_UI_ROW = re.compile(
    r"""<tr\b[^>]*>(.*?)</tr>""",
    re.DOTALL | re.IGNORECASE,
)
_UI_NF_ID = re.compile(r"""<nf\b[^>]*\bid\s*=\s*['"]([^'"]+)['"]""", re.IGNORECASE)


def parse_uisettings_phtml(content: str) -> list[dict]:
    """Her satırda bir checkbox (`<nf id='ui_X'>`) ve ona ait etiket (<td>).
    Çıktı: [{ui_key, label, langt_key}, ...]"""
    rows: list[dict] = []
    for inner in _UI_ROW.findall(content):
        nf_m = _UI_NF_ID.search(inner)
        if not nf_m:
            continue
        ui_key = nf_m.group(1).strip()
        # İlk <td>…</td> içeriği genelde etiket
        td_m = re.search(r"""<td[^>]*>(.*?)</td>""", inner, re.DOTALL | re.IGNORECASE)
        label, langt_key = _clean_label(td_m.group(1) if td_m else None)
        rows.append({"ui_key": ui_key, "label": label or "", "langt_key": langt_key})
    return rows


# JS içinde: if (pdata.np["ui_X"]) { $("#TagId").css("display", "block"); }
# ui_key'i hangi tag ID'sine bağladığını yakalar.
_UI_TO_TAG = re.compile(
    r"""pdata\.np\[["']([^"']+)["']\][^{}]{0,200}?\$\(["']#([A-Za-z_][A-Za-z0-9_]*)["']\)""",
    re.DOTALL,
)


def parse_ui_to_tag_links(genel_content: str) -> dict[str, list[str]]:
    """ui_key -> [tag_id,…] (hangi ui bayrağı hangi dim'i gösterir/gizler)."""
    mapping: dict[str, list[str]] = {}
    for ui_key, tag_id in _UI_TO_TAG.findall(genel_content):
        if not ui_key.startswith("ui_"):
            continue
        mapping.setdefault(ui_key, [])
        if tag_id not in mapping[ui_key]:
            mapping[ui_key].append(tag_id)
    return mapping


# --- Markdown renderer -----------------------------------------------------

_PRESSURE_UNITS = {"bar", "mbar", "kpa", "pa"}
_FLOW_UNITS = {"m³/h", "m3/h", "lt/sn", "l/s"}
_LEVEL_UNITS = {"m", "cm"}


def _family_hint(nview: str) -> str:
    n = nview.lower()
    if "dma" in n:
        return "dma.md (debi bölge K-Means + basınç ölçekleme)"
    if "kuyu" in n or "well" in n:
        return "kuyu.md (canlı tag + SP serisi dalgıç pompa)"
    if "terfi" in n or "booster" in n or "riser" in n:
        return "terfi.md (terfi istasyonu)"
    if "depo" in n or "tank" in n:
        return "depo.md (depo izleme)"
    return "system.md (genel)"


def render_markdown(
    nview: str,
    source_path: str,
    tags: dict[str, dict],
    data_refs: list[str],
    menu_pages: list[dict],
    ui_settings: list[dict] | None = None,
    ui_to_tag: dict[str, list[str]] | None = None,
    menu_source_nv: str | None = None,
) -> str:
    # Frontmatter keywords — tag grubuna göre zenginleştir
    kw_parts: list[str] = [nview]
    for tag_id in tags.keys():
        if tag_id in {"Debimetre", "BasincSensoru", "ToplamHm", "SuSeviye", "StatikSeviye"}:
            kw_parts.append(tag_id)
    kw = ", ".join(sorted(set(kw_parts)))

    lines: list[str] = []
    lines.append("---")
    lines.append(f"name: nview-{nview}")
    lines.append("description: |")
    lines.append(
        f"  nView '{nview}' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi."
    )
    lines.append(
        f"  Use when: node.nView == \"{nview}\" ve tag anlamı, birim, rolü soruluyorsa."
    )
    lines.append(f"  Keywords: {kw}.")
    lines.append("version: \"1.0.0\"")
    lines.append("generated: true")
    lines.append(f"source: {source_path}")
    lines.append("---")
    lines.append("")
    lines.append(f"# nView: {nview}")
    lines.append("")
    lines.append(f"Aile bağlamı: **{_family_hint(nview)}** — ortak iş akışı için aile skiline bakın.")
    lines.append("")

    # Ana ekran tag tablosu
    lines.append("## Ana Ekran Tag'leri (GENEL.phtml)")
    lines.append("")
    lines.append("| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |")
    lines.append("|---|---|---|---|---|---|")

    def _tag_sort_key(item: tuple[str, dict]) -> tuple[int, str]:
        tid = item[0]
        order = 3
        if tid in {
            "SuSeviye",
            "StatikSeviye",
            "BasincSensoru",
            "BasincSensoru2",
            "Debimetre",
            "ToplamHm",
        }:
            order = 0
        elif tid.startswith("An_"):
            order = 1
        elif tid.startswith("T_"):
            order = 2
        elif tid.startswith("XD_") or tid.startswith("XS_"):
            order = 4
        elif tid.startswith("XE_") or tid.startswith("XC_") or tid.startswith("XV_"):
            order = 5
        elif tid.startswith("Al_"):
            order = 6
        return (order, tid.lower())

    for tag_id, info in sorted(tags.items(), key=_tag_sort_key):
        label = info.get("label") or ""
        if not label and info.get("langt_key"):
            label = f"[langt:{info['langt_key']}]"
        unit = info.get("unit") or ""
        fixed = "" if info.get("fixed") is None else str(info["fixed"])
        role = info.get("role") or ""
        note_parts: list[str] = []
        if info.get("role_desc") and info.get("role_desc") != label:
            note_parts.append(info["role_desc"])
        if info.get("langt_key") and label and f"[langt:" not in label:
            note_parts.append(f"langt={info['langt_key']}")
        container = info.get("container")
        if container and container != "dim":
            note_parts.append(f"({container})")
        note = "; ".join(note_parts)
        # Pipe karakteri escape
        safe_label = label.replace("|", "\\|")
        safe_note = note.replace("|", "\\|")
        lines.append(f"| `{tag_id}` | {safe_label} | {unit} | {fixed} | {role} | {safe_note} |")
    lines.append("")

    # Data refs (JS tarafındaki ek tag isimleri — görsel tag dışında mod/alarm)
    dim_set = set(tags.keys())
    extra_data = [d for d in data_refs if d not in dim_set]
    if extra_data:
        lines.append("## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)")
        lines.append("")
        lines.append("Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):")
        lines.append("")
        grouped: dict[str, list[str]] = {}
        for tid in extra_data:
            role, _ = infer_role(tid)
            grouped.setdefault(role, []).append(tid)
        for role_code in sorted(grouped.keys()):
            group = sorted(grouped[role_code])
            lines.append(f"- **{role_code}**: {', '.join(f'`{t}`' for t in group)}")
        lines.append("")

    # UI Ayarları — node'da hangi tag'lerin aktif olduğunu kontrol eder
    if ui_settings:
        lines.append("## Arayüz Ayarları (uisettings.phtml)")
        lines.append("")
        lines.append("Bu nView'da bazı tag'ler **node konfigürasyonuna göre** aktif olur. Node parametre (`np`) üzerinde şu bayraklar kontrol edilir; bir DMA noktasında hangi basınç/debi sensörünün gerçekten kullanıldığını anlamak için bu tabloya bakın:")
        lines.append("")
        lines.append("| np anahtarı | Etiket | Aktifse görünür tag'ler |")
        lines.append("|---|---|---|")
        for s in ui_settings:
            ui_key = s.get("ui_key") or ""
            label = s.get("label") or (f"[langt:{s['langt_key']}]" if s.get("langt_key") else "")
            linked = (ui_to_tag or {}).get(ui_key, [])
            linked_str = ", ".join(f"`{t}`" for t in linked) if linked else "—"
            lines.append(f"| `{ui_key}` | {label} | {linked_str} |")
        lines.append("")
        lines.append("> **DMA basınç bölgeleme analizi için ipucu:** `ui_cikisbasinc=1` ise node'da çıkış basınç sensörü (genelde `BasincSensoru`) aktif; `ui_girisbasinc=1` ise giriş basınç (`GirisBasincSensoru` veya `GirisBasinc`) aktif. Tool `analyze_dma_seasonal_demand` bu tag'lerin log'undan min/max türeterek PRV bandını otomatik belirler.")
        lines.append("")

    # Menü sayfaları — başlık + ayar parametreleri ile zenginleştirilmiş
    if menu_pages:
        lines.append("## Alt Menü Sayfaları (MENU.phtml)")
        lines.append("")
        lines.append(
            "Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. \"depo doldurma ayarları nereden\"), "
            "aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. "
            "`Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id=\"...\">` "
            "kaydedilebilir alanlardan türetilir."
        )
        lines.append("")
        lines.append("| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |")
        lines.append("|---|---|---|---|")
        for m in menu_pages:
            lbl = m.get("label") or (f"[langt:{m['langt_key']}]" if m.get("langt_key") else "")
            baslik = m.get("baslik") or (
                f"[langt:{m['baslik_langt_key']}]" if m.get("baslik_langt_key") else ""
            )
            fields = m.get("ayar_alanlari") or []
            if fields:
                # İlk 8 alanı göster, fazlaysa "…+N"
                shown = ", ".join(f"`{f['id']}`" for f in fields[:8])
                if len(fields) > 8:
                    shown += f" …+{len(fields) - 8}"
            else:
                shown = "—"
            safe_lbl = lbl.replace("|", "\\|")
            safe_bas = (baslik or "").replace("|", "\\|")
            safe_shown = shown.replace("|", "\\|")
            lines.append(f"| `{m['page']}` | {safe_lbl} | {safe_bas} | {safe_shown} |")
        lines.append("")
        if menu_source_nv and menu_source_nv != nview:
            lines.append(
                f"> Not: Bu nView'ın kendi `MENU.phtml`'i yoktu; menü `{menu_source_nv}` "
                f"paylaşımlı şablonundan alındı (MAIN.phtml `$linked`)."
            )
            lines.append("")

    # Birim bazlı kısa özet
    pressure_tags = [t for t, i in tags.items() if (i.get("unit") or "").lower() in _PRESSURE_UNITS]
    flow_tags = [t for t, i in tags.items() if (i.get("unit") or "").lower() in _FLOW_UNITS]
    level_tags = [t for t, i in tags.items() if (i.get("unit") or "").lower() in _LEVEL_UNITS]
    lines.append("## Birim Özeti")
    lines.append("")
    if pressure_tags:
        lines.append(f"- **Basınç ({', '.join(sorted({(tags[t].get('unit') or '').lower() for t in pressure_tags}))})**: {', '.join(f'`{t}`' for t in sorted(pressure_tags))}")
    if flow_tags:
        lines.append(f"- **Debi**: {', '.join(f'`{t}`' for t in sorted(flow_tags))}")
    if level_tags:
        lines.append(f"- **Seviye / uzunluk (m/cm)**: {', '.join(f'`{t}`' for t in sorted(level_tags))}")
    lines.append("")

    lines.append("## Not")
    lines.append("")
    lines.append("- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.")
    lines.append("- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.")
    lines.append("- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.")
    return "\n".join(lines) + "\n"


# --- Orchestration ---------------------------------------------------------


def _list_nviews(source: Path) -> list[str]:
    """GENEL.phtml içeren alt dizinleri döndürür."""
    out: list[str] = []
    for p in sorted(source.iterdir()):
        if not p.is_dir():
            continue
        if (p / "GENEL.phtml").is_file():
            out.append(p.name)
    return out


def generate_for_nview(
    source: Path,
    out_dir: Path,
    nview: str,
    dry_run: bool,
    skip_existing: bool,
) -> tuple[bool, str]:
    nv_dir = source / nview
    gen_path = nv_dir / "GENEL.phtml"
    if not gen_path.is_file():
        return False, f"GENEL.phtml yok: {gen_path}"
    content = gen_path.read_text(encoding="utf-8", errors="replace")
    tags = parse_genel_phtml(content)
    data_refs = parse_data_refs(content)
    # Menü kaynağı: kendi MENU.phtml > yoksa MAIN.phtml'deki $linked hedefinin MENU.phtml'i
    menu_pages: list[dict] = []
    menu_source_nv: str = nview
    menu_source_path: str | None = None
    menu_path = nv_dir / "MENU.phtml"
    if menu_path.is_file():
        menu_pages = parse_menu_phtml(
            menu_path.read_text(encoding="utf-8", errors="replace")
        )
        menu_source_path = str(menu_path).replace("\\", "/")
    else:
        main_path = nv_dir / "MAIN.phtml"
        if main_path.is_file():
            linked_nv = parse_main_linked(
                main_path.read_text(encoding="utf-8", errors="replace")
            )
            if linked_nv:
                linked_menu = source / linked_nv / "MENU.phtml"
                if linked_menu.is_file():
                    menu_pages = parse_menu_phtml(
                        linked_menu.read_text(encoding="utf-8", errors="replace")
                    )
                    menu_source_nv = linked_nv
                    menu_source_path = str(linked_menu).replace("\\", "/")
    # Her menü sayfasını zenginleştir — önce kendi klasörü, yoksa $linked klasörü
    menu_lookup_dirs = [nv_dir]
    if menu_source_nv != nview:
        menu_lookup_dirs.append(source / menu_source_nv)
    for mp in menu_pages:
        page_name = mp["page"]
        sub_path: Path | None = None
        for d in menu_lookup_dirs:
            candidate = d / f"{page_name}.phtml"
            if candidate.is_file():
                sub_path = candidate
                break
        if sub_path is not None:
            info = parse_subpage(sub_path)
            mp["baslik"] = info.get("title")
            mp["baslik_langt_key"] = info.get("title_langt_key")
            mp["ayar_alanlari"] = info.get("fields", [])
            mp["kaynak_path"] = str(sub_path).replace("\\", "/")
        else:
            mp["baslik"] = None
            mp["ayar_alanlari"] = []
    ui_settings: list[dict] = []
    ui_path = nv_dir / "uisettings.phtml"
    if ui_path.is_file():
        ui_settings = parse_uisettings_phtml(
            ui_path.read_text(encoding="utf-8", errors="replace")
        )
    ui_to_tag = parse_ui_to_tag_links(content)
    md = render_markdown(
        nview=nview,
        source_path=str(gen_path).replace("\\", "/"),
        tags=tags,
        data_refs=data_refs,
        menu_pages=menu_pages,
        ui_settings=ui_settings,
        ui_to_tag=ui_to_tag,
        menu_source_nv=menu_source_nv,
    )
    target = out_dir / f"{nview}.md"
    if dry_run:
        summary = (
            f"[DRY] {nview}: {len(tags)} dim tag, "
            f"{len([d for d in data_refs if d not in tags])} data.* ref, "
            f"{len(menu_pages)} menü, {len(ui_settings)} ui_* -> {target}"
        )
        return True, summary
    if skip_existing and target.is_file():
        return True, f"[SKIP] mevcut dosya korundu: {target}"
    out_dir.mkdir(parents=True, exist_ok=True)
    target.write_text(md, encoding="utf-8")
    return True, (
        f"[OK] {nview}: {len(tags)} dim tag, "
        f"{len([d for d in data_refs if d not in tags])} data.* ref, "
        f"{len(menu_pages)} menü, {len(ui_settings)} ui_* -> {target}"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default=DEFAULT_SOURCE, help="phtml klasörü yolu")
    ap.add_argument("--out", default=DEFAULT_OUT, help="nView skill çıkış klasörü")
    ap.add_argument("--nview", help="Tek bir nView üret")
    ap.add_argument("--all", action="store_true", help="Kaynak dizindeki tüm nView'lar")
    ap.add_argument("--list", action="store_true", help="Kaynaktaki nView'ları listele, dosya yazma")
    ap.add_argument("--dry-run", action="store_true", help="Özet yaz, dosya yazma")
    ap.add_argument(
        "--skip-existing",
        action="store_true",
        help="Çıkış dizininde mevcut dosyaları korur, üzerine yazmaz",
    )
    args = ap.parse_args(argv)

    source = Path(args.source)
    if not source.is_dir():
        print(f"HATA: kaynak dizin bulunamadı: {source}", file=sys.stderr)
        return 2

    if args.list:
        for nv in _list_nviews(source):
            print(nv)
        return 0

    out_dir = Path(args.out)

    targets: list[str] = []
    if args.nview:
        targets = [args.nview]
    elif args.all:
        targets = _list_nviews(source)
    else:
        ap.print_help()
        return 2

    errors = 0
    for nv in targets:
        ok, msg = generate_for_nview(
            source=source,
            out_dir=out_dir,
            nview=nv,
            dry_run=args.dry_run,
            skip_existing=args.skip_existing,
        )
        print(msg)
        if not ok:
            errors += 1
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
