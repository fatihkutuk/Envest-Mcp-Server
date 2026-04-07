"""
Korubin panel şablon modeli + MCP araç seçimi özeti (statik).
Amaç: modelin system prompt yerine bu yükü bir kez okuyup doğru araca gitmesi.
"""

from __future__ import annotations

from typing import Any


def korubin_ui_and_tool_routing_payload(*, tool_prefix: str) -> dict[str, Any]:
    """
    tool_prefix: örn. "korubin_" — dönen metinde tam MCP araç adları için kullanılır.
    """
    p = tool_prefix or ""

    def t(name: str) -> str:
        return p + name

    return {
        "_schema": "korubin_ui_tool_routing",
        "version": 1,
        "ozet_tr": (
            "Korubin web paneli «nokta» (node) ekranları şablon klasörüne (node.nView) göre .phtml dosyalarından üretilir. "
            "Kullanıcı cihazın kendi ekranındaki «model / menü / LED / modem durumu» gibi şeylerden bahsediyorsa bu genelde "
            "ürün JSON kılavuzudur; Kepware channel/device veya _tagoku ile karıştırılmamalıdır."
        ),
        "panel_url_modeli": {
            "sablon_tr": "https://{panel_base_url}/panel/point/{nodeId}/{segment}",
            "segment_aciklama_tr": (
                "URL’deki son yol parçası (ör. sensor, bilgi/device_edit) sunucuda ilgili .phtml dosyasına çözülür: "
                "çoğunlukla `{segment}.phtml` veya `alt/segment.phtml` (segment içinde / varsa alt klasör)."
            ),
            "ornekler": [
                "/panel/point/12345/sensor → sensor.phtml",
                "/panel/point/12345/bilgi/device_edit → bilgi altında device_edit.phtml",
            ],
            "panel_base_url_not_tr": "instance.panel_base_url MCP manifestinde; https yoksa istemci https ekler.",
        },
        "views_kok_ve_yerel_dokum_tr": {
            "sunucu_canonical_tr": (
                "Canlı Korubin uygulamasında tüm panel şablonları `app/views/` altındadır (PHP uygulama köküne göre). "
                "Nokta ekran tipleri: `app/views/point/display/common/{nView}/` (ve bazı kurulumlarda `point/display/editor/...`). "
                "Ortak ayar/sayfa iskeleti: `app/views/point/joint/` (ör. log, bilgi alt sayfaları buraya bağlanır)."
            ),
            "korbin1_7_system_info_tr": (
                "Repo içinde `korbin1.7-system-info/` (genelde .gitignore): sunucudaki `app/` ağacının kopyasıdır; "
                "MCP’nin dosya okuması için değil, model/yerel geliştirici referansı ve sunucuda aynı göreli yolların "
                "doğrulanması içindir. MCP şablon okuyacaksa `KORUBIN_POINT_DISPLAY_ROOT` gerçek disk yolunu göstermelidir "
                "(sunucuda örn. `/var/www/.../app/views/point/display/common`, yerelde döküm kullanıyorsanız "
                "`.../korbin1.7-system-info/app/views/point/display/common`)."
            ),
        },
        "ekran_sablonlari_display_common": {
            "kok_tr": (
                "`KORUBIN_POINT_DISPLAY_ROOT` tam olarak `.../app/views/point/display/common` olmalıdır "
                "(içinde doğrudan `a-aqua-cnt-kuyu` gibi nView klasörleri durur; `display/common` tekrar eklenmez). "
                "`read_point_display_template` yolu: `{ROOT}/{n_view_folder}/{relative_path}`."
            ),
            "ana_ekran_dosyalari_tr": (
                "Ana içerik dosya adı projede çoğunlukla `GENEL.phtml` (veya `genel.phtml`); ayrıca `MAIN.phtml` kullanılan "
                "ekranlar var — şüphede ikisini de kontrol edin."
            ),
            "menu_phtml_tr": (
                "MENU.phtml (veya benzeri) menü satırlarını içerir. Bağlantı `./sensor` gibi göreliyse, "
                "aynı nView klasöründeki `sensor.phtml` açılır; tam URL yine `/panel/point/{nodeId}/sensor` biçimindedir."
            ),
            "linked_klasor_tr": (
                "MAIN.phtml içinde başka bir nView adı (`$linked = 'a-aqua-cnt-terfi'` gibi) tanımlıysa: "
                "bu ekranda dosya yoksa veya ortak şablon kullanımı için içerik o klasörden yüklenir — "
                "menü yolları yine kullanıcıya görünen nView + segment ile düşünülmelidir."
            ),
            "joint_klasoru_tr": (
                "Sunucuda `app/views/point/joint/` altındaki şablonlar genelde ayar / bilgi / log çerçevesidir; "
                "URL segmenti `bilgi/device_edit` gibi çok parçalı olabilir (ilgili .phtml joint veya alt klasörde)."
            ),
        },
        "phtml_icindeki_isimlendirme": {
            "div_id_tag_tr": (
                "Çoğu şablonda bir kapsayıcının `id` özniteliği SCADA tag adına karşılık gelir; sunucu tagoku’dan "
                "okunan değeri ilgili içteki `<v>` (value) öğesine basar."
            ),
            "nf_node_param_tr": (
                "`nf` benzeri işaretçiler node parametrelerinden (nodeParam / yapılandırma) doldurulur — canlı tag değildir."
            ),
            "not_tr": "Kesin eşleme her projede aynı değildir; şüphede ilgili .phtml dosyasını okuyun.",
        },
        "arac_secimi_karar_agaci_tr": {
            "urun_cihaz_dokumani": {
                "sinyaller": [
                    "Aqua 100 / aqua_cnt",
                    "modem çalışma kodu",
                    "cihaz menüsü tuşları",
                    "LED durumları",
                    "donanım özellikleri modeller",
                    "modbus haritası (cihaz dokümanı)",
                ],
                "kullan": [t("get_product_specs"), t("search_product_manual"), t("get_product_settings"), t("get_product_troubleshoot")],
                "kullanma": [
                    t("search_tags"),
                    t("list_channel_devices"),
                    "Önce tag aramaya düşme; kullanıcı ‘product specs’ / kılavuza işaret ediyorsa ürün araçları öncelikli.",
                ],
            },
            "anlik_deger_alarm_trend": {
                "sinyaller": ["şu an kaç bar", "canlı debi", "aktif alarm", "grafik", "log"],
                "kullan": [
                    t("get_device_tag_values"),
                    t("get_device_data"),
                    t("get_active_alarms"),
                    t("get_chart_data"),
                ],
            },
            "kepware_opc_adres_surucu": {
                "sinyaller": ["channel", "device type", "OPC", "Kepware", "tag address"],
                "kullan": [t("list_channel_devices"), t("get_channel_device_detail"), t("get_tag_address")],
            },
            "panel_hangi_sayfa_hangi_tag": {
                "sinyaller": ["hangi menü", "sensor sayfası", "şablonda ne var", "MENU.phtml"],
                "adim_tr": (
                    f"1) {t('get_node')} veya {t('get_node_scada_context')} ile nView alın. "
                    f"2) {t('read_point_display_template')} ile MENU.phtml / genel.phtml / sensor.phtml okuyun. "
                    f"3) Gerekirse {t('get_node_panel_settings_guide')} (panel_navigation_hints.json varsa)."
                ),
            },
            "veritabani_sema_sql": {
                "sinyaller": ["tablo yapısı", "ilişki", "hangi kolon", "SQL"],
                "kullan": [t("get_database_schema"), t("get_table_info"), t("run_safe_query")],
                "referans_dokuman_not_tr": (
                    "Yerel geliştirme klasöründe (repo dışı veya gitignore): dbdataexchnager.sql, relations.sql, kbindb.sql "
                    "şema referansıdır; canlı sorgu için MCP şema araçlarını kullanın."
                ),
            },
        },
        "onemli_mcp_araclari": {
            "routing_manifest": [t("get_scada_site_routing_hints"), t("get_scada_mcp_manifest")],
            "kavramlar": [t("get_korubin_data_concepts")],
            "tag_sozlugu_varsayilan": [t("get_scada_tag_naming_defaults_tr")],
        },
        "kisir_dongu_onleme_tr": {
            "kurallar": [
                f"{t('get_scada_mcp_manifest')} ve {t('get_scada_site_routing_hints')} aynı soruda en fazla birer kez yeterli.",
                "Aynı araç + aynı parametreyle ardışık 2+ çağrı yapıyorsanız durun; eksik bilgiyi kullanıcıdan isteyin veya farklı araç seçin.",
                "Ürün sorusunda tag araması sonuç vermiyorsa: ürün JSON araçlarına geçin, tag aramayı tekrarlamayın.",
                "Şablon okunamıyorsa (KORUBIN_POINT_DISPLAY_ROOT yok): kullanıcıya kök yolun sunucuda tanımlı olması gerektiğini söyleyin; boş döngüye girmeyin.",
            ],
        },
    }
