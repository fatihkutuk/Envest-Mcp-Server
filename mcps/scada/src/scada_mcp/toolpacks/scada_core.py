from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

import json as _json

from ..config import instance_as_public_dict, mcp_public_privacy_notice
from ..manifest import load_manifest
from ..korubin_ui_tool_routing import korubin_ui_and_tool_routing_payload
from ..scada_tag_lexicon import scada_tag_lexicon_payload
from ..tool_selector import select_tools as _select_tools
from ..tools.core import prefixed_name
from ..types import InstanceConfig


class ScadaCorePack:
    id = "scada_core"

    def register(self, mcp: FastMCP, cfg: InstanceConfig) -> None:
        prefix = cfg.tool_prefix

        manifest_tool = prefixed_name(prefix, "get_scada_mcp_manifest")

        @mcp.tool(name=manifest_tool)
        def get_scada_mcp_manifest() -> Any:
            """MCP manifest: tool grupları ve instance özeti."""
            manifest = load_manifest(cfg.base_dir)
            manifest["instance"] = instance_as_public_dict(cfg)
            manifest["privacy"] = mcp_public_privacy_notice()
            manifest["registered_tool_name"] = manifest_tool
            return manifest

        ui_route_tool = prefixed_name(prefix, "get_korubin_ui_and_tool_routing_tr")

        @mcp.tool(name=ui_route_tool)
        def get_korubin_ui_and_tool_routing_tr() -> Any:
            """Panel şablon yapısı, URL↔phtml eşleme, ürün kılavuzu vs canlı tag ayrımı ve döngü önleme rehberi."""
            return korubin_ui_and_tool_routing_payload(tool_prefix=prefix)

        routing_tool = prefixed_name(prefix, "get_scada_site_routing_hints")

        @mcp.tool(name=routing_tool)
        def get_scada_site_routing_hints() -> Any:
            """Site/MCP yönlendirme ipuçları: DMA, debi-güç karşılaştırma, seviye profili araçları."""
            # Do NOT branch on tool_prefix: prefixes may vary per deployment.
            # Prefer explicit instance identity fields that are stable for the user/admin.
            role = str(cfg.instance_id or "").strip() or "instance"
            dma_tool = f"{prefix}analyze_dma_seasonal_demand"
            dma_list = f"{prefix}list_dma_station_nodes"
            compare_tool = f"{prefix}compare_log_metrics"
            return {
                "_schema": "korubin_mcp_site_routing",
                "version": 1,
                "panel_ve_arac_modeli_tr": {
                    "arac": ui_route_tool,
                    "ne_zaman_tr": (
                        "Nokta ekranı menüsü, şablon yolu, ürün dokümanı (Aqua 100 vb.) ile canlı tag/Kepware ayrımı "
                        "veya MCP'de tekrarlayan çağrılar — önce bu aracı kullanın."
                    ),
                },
                "bu_mcp_cagrisi": {
                    "mcp_name": cfg.mcp_name,
                    "arac_oneki": prefix,
                    "rol_kodu": role,
                    "panel_base_url": cfg.panel_base_url or "",
                },
                "kullaniciya_netlik_sorusu_ornek_tr": (
                    "Aynı sorunun farklı MCP instance'ları olabilir. Lütfen hedefi netleştirin: "
                    "hangi site/panel (panel_base_url) veya hangi kurulum (mcp_name / instance_id)?"
                ),
                "etiket_varsayilanlari_araci": f"{prefix}get_scada_tag_naming_defaults_tr",
                "dma_debi_kmeans_tr": {
                    "soru_ornekleri": [
                        "debi bölgeleri",
                        "tez gibi K-Means",
                        "saatlik talep dilimleri",
                        "DMA debi profili",
                    ],
                    "arac": dma_tool,
                    "parametre_ornekleri": {
                        "nodeId": 22537,
                        "nodeAdiAra": "Kale - 12 (BAHÇELİEVLER)",
                    },
                    "not_tr": (
                        "SCADA canlı taglerinde genelde tek «Debimetre» vardır; alt bölge debi ayrımı yoktur. "
                        "Tezdeki gibi günün dilimlerine bölme için log debimetre + bu araç kullanılır. "
                        "Yanıt chart + tez_scatter_chart içerir. «Grafik» sonrası get_chart_data çağırılmaz; "
                        "dma_grafik_ve_dongu_model_talimat_tr ve dusunce_dongusu_kes_model_talimat_tr alanlarını modele okutun."
                    ),
                    "dma_liste_araci": dma_list,
                },
                "kuyu_debi_guc_karsilastirma_tr": {
                    "soru_ornekleri": [
                        "serbest bölge kuyusunda debi ile gücü karşılaştır",
                        "debi ve motor gücü birlikte grafik",
                        "akış ile kW trendi",
                    ],
                    "arac": compare_tool,
                    "parametre_ornekleri": {
                        "nodeAdiAra": "Serbest Bölge",
                        "primaryTagHint": "debi",
                        "secondaryTagHint": "güç",
                    },
                    "not_tr": (
                        "İki farklı birim (ör. m³/h ve kW) aynı grafikte: compare_log_metrics ortak zaman kovası kullanır; "
                        "yanıtta dual_axis_suggested ve datasets.yAxisID (y / y1) vardır. "
                        "İpucu boşsa debi+akış ve güç/kW için varsayılan tag araması yapılır."
                    ),
                },
                "dinamik_seviye_mevsimsel_tr": {
                    "soru_ornekleri": [
                        "dinamik seviye düştüğü saatler",
                        "mevsimsel seviye",
                        "kuyu seviyesi yaz kış",
                    ],
                    "arac": f"{prefix}analyze_seasonal_level_profile",
                    "parametre_ornekleri": {"nodeId": 1192, "tagHint": "SuSeviye"},
                    "not_tr": (
                        "Aynı matematik (saatlik ortalama + K-Means) seviye logunda; yanıtta tez_grafigi ile scatter+medoid (X) çizilebilir. "
                        "Çizgi chart da hazırdır; «grafik göster» için tekrar araç çağırmayın (grafik_sunumu_model_talimat_tr). "
                        "Yıllık düşüş: analyze_log_trend long_term."
                    ),
                },
                "mcp_privacy": mcp_public_privacy_notice(),
                "kisir_dongu_kisaca_tr": (
                    f"Aynı soruda {manifest_tool} ve {routing_tool} yalnızca birer kez; "
                    f"ürün/model sorusunda tag aracını sonuç çıkmayınca tekrarlamayın — {ui_route_tool} içindeki karar ağacına bakın."
                ),
            }

        lex_tool = prefixed_name(prefix, "get_scada_tag_naming_defaults_tr")

        @mcp.tool(name=lex_tool)
        def get_scada_tag_naming_defaults_tr() -> Any:
            """SCADA tag adlandırma kuralları: Debimetre, an_guc, seviye, basınç, x/al_/xe/xd önekleri."""
            return scada_tag_lexicon_payload()

        # --- Smart Tool Selector ---
        selector_tool = prefixed_name(prefix, "smart_tool_select")

        @mcp.tool(name=selector_tool)
        def smart_tool_select(user_query: str) -> Any:
            """Kullanıcı sorusuna göre en uygun araçları önerir. Çok sayıda araç arasından hızlı seçim için önce bunu çağırın."""
            return _select_tools(user_query, prefix=prefix)

    def manifest_groups(self, *, prefix: str) -> list[dict]:
        p = prefix
        return [
            {
                "id": "routing",
                "title_tr": "Yönlendirme / belirsizlik çözümü",
                "tools": [
                    p + "get_korubin_ui_and_tool_routing_tr",
                    p + "get_scada_site_routing_hints",
                    p + "get_scada_mcp_manifest",
                    p + "get_scada_tag_naming_defaults_tr",
                    p + "smart_tool_select",
                ],
            },
            {
                "id": "nodes",
                "title_tr": "Node / nokta sayımı",
                "tools": [],
            },
        ]
