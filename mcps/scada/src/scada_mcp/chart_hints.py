"""Chart JSON yanıtlarına eklenecek kısa model talimatları (KoruMind / LLM)."""

# KoruMind chart şeması: server/docs/MCP-CHART-WIDGET.md — MCP araçları chart_contract ile uyumlu alanlar üretir
# (series_kind=log tarih ekseni; chart_alternates; chart_js_type; yAxisLabel).
# SCADA tag varsayılanları (debimetre1/2, an_guc, x/al_/xe/xd): get_scada_tag_naming_defaults_tr + scada_tag_lexicon.

# Genel chart yanıtları — «grafik göster» sonrası gereksiz araç ve düşünce döngüsünü kesmek için.
GRAFIK_SUNUMU_MODEL_TALIMAT_TR = (
    "Bu yanıt çizim verisi taşıyorsa (kökte labels+datasets ve/veya tez_scatter_chart): kullanıcı yalnızca «grafik / çiz / göster» diyorsa "
    "YENİ MCP aracı ÇAĞIRMAYIN; uzun düşünce zinciri yazmayın; aynı paragrafı tekrarlamayın. "
    "Veriyi doğrudan KoruMind grafik bileşenine iletin veya en fazla 1–2 kısa cümle yazın. "
    "DMA debi bölgeleri / tez tarzı saat×debi için bu yanıttaki tez_scatter_chart (ve varsa line özet) yeterlidir; "
    "get_chart_data veya get_node_log_chart_data bunun yerine kullanılmaz (tarih ekseni, kümesiz ham seri). "
    "Ham zaman serisi ancak kullanıcı açıkça «tarih ekseni / günlük eğri / ham log grafiği» istediğinde uygundur. "
    "İki farklı sinyali (debi+güç vb.) aynı zaman ekseninde karşılaştırma: compare_log_metrics. "
    "get_multi_chart_data çıktısı zaman serisidir: coklu_log_grafik_model_talimat_tr ve koru_mind_disallowed_chart_types_for_this_payload "
    "— pasta/halka önerme; KoruMind araç çubuğunda line/bar kullan."
)

# Herhangi bir araç yanıtı sonrası modelin boş yere tekrar etmesini azaltmak için.
DUSUNCE_DONGUSU_KES_MODEL_TALIMAT_TR = (
    "DÖNGÜ YASAK: Aynı gerekçeyi, aynı araç aday listesini veya aynı paragrafı art arda yazmayın. "
    "Yanıt alındıysa bir sonraki mesajda ya kullanıcıya kısa cevap verin ya da en fazla TEK yeni araç çağırın. "
    "Anlamsız veya eksik araç adı (ör. yalnızca düğüm adı) üretmeyin."
)

# analyze_dma_seasonal_demand başarı yanıtına özel — önceki sohbette en çok burada sapma oluyor.
DMA_ANALIZ_SONRASI_GRAFIK_TALIMAT_TR = (
    "Bu mesaj analyze_dma_seasonal_demand çıktısıdır. Kullanıcı «grafiksel göster / tez gibi / bölgeler» derse: "
    "tez_scatter_chart (scatter, küme rengi) + kök _type_chart line kullanın. "
    "get_chart_data, get_node_log_chart_data, get_multi_chart_data bu istek için ÇAĞIRILMAZ. "
    "analyze_dma_seasonal_demand tekrar çağrılmaz (veri zaten burada). "
    "Düşünce zincirinde aynı cümleyi on kez tekrarlamayın; maksimum 2 cümle. "
    "İSTİSNA — basınç ölçekleme: Kullanıcı «X-Y bar arasına ölçekle / basınç bandı / PRV set çizelgesi» derse: "
    "analyze_dma_seasonal_demand'i minPressure=X, maxPressure=Y ile TEKRAR çağırın "
    "(yeni parametre olduğu için aynı-analiz-aynı-parametre kuralı ihlal edilmez). "
    "BasincSensoru log grafiği/tag'i bu istek için KULLANILMAZ; ölçekleme debi küme merkezlerine uygulanır "
    "ve sonuçta tez_basinc_ayarlama.calisma_tablosu döner."
)

# Genel döngü önleme — tüm araç yanıtlarına uygulanabilir.
GENEL_DONGU_ONLEME_TR = (
    "KURAL: Aynı aracı aynı parametrelerle 2 kereden fazla çağırmayın. "
    "Hata alırsanız: (1) farklı parametre deneyin, (2) farklı araç kullanın, (3) kullanıcıya durumu açıklayın. "
    "Node adı (ör. 'ESKİ', 'Gölkent') bir araç adı DEĞİLDİR — araç adları her zaman instance prefix'i ile başlar (ör. `<instance_prefix>_get_node`)."
)

SEVIYE_ANALIZ_SONRASI_GRAFIK_TALIMAT_TR = (
    "Bu mesaj analyze_seasonal_level_profile çıktısıdır. «Grafik»: tez_scatter_chart (varsa) + kök line. "
    "get_chart_data / get_node_log_chart_data bu istek için otomatik seçilmez. "
    "Düşünce döngüsü yok; aynı aracı aynı node için tekrar çağırmayın."
)
