---
name: nview-a-terfi-2p-envest-y
description: |
  nView 'a-terfi-2p-envest-y' için GENEL.phtml'den otomatik çıkarılmış tag/birim/etiket eşlemesi.
  Use when: node.nView == "a-terfi-2p-envest-y" ve tag anlamı, birim, rolü soruluyorsa.
  Keywords: Debimetre, a-terfi-2p-envest-y.
version: "1.0.0"
generated: true
source: https://<panel_base_url>/panel/point/<node_id>/<menu>
---

# nView: a-terfi-2p-envest-y

Aile bağlamı: **terfi.md (terfi istasyonu)** — ortak iş akışı için aile skiline bakın.

## Ana Ekran Tag'leri (GENEL.phtml)

| Tag ID | Anlam / Etiket | Birim | Fixed | Rol | Not |
|---|---|---|---|---|---|
| `Debimetre` | Debi 1 | m³/h | 2 | measurement | Debi ölçümü (m³/h) |
| `An_FrekansP1` | Anlık elektrik/motor ölçümü | Hz | 1 | instant_electrical | langt=Şebeke Frekansı; (div) |
| `An_FrekansP2` | Anlık elektrik/motor ölçümü | Hz | 1 | instant_electrical | langt=Şebeke Frekansı; (div) |
| `An_GucFaktoruP1` | Anlık elektrik/motor ölçümü |  | 2 | instant_electrical | langt=Güç Faktörü; (div) |
| `An_GucFaktoruP2` | Anlık elektrik/motor ölçümü |  | 2 | instant_electrical | langt=Güç Faktörü; (div) |
| `An_GucP1` | Anlık elektrik/motor ölçümü | kW | 2 | instant_electrical | langt=Sistem Güç; (div) |
| `An_GucP2` | Anlık elektrik/motor ölçümü | kW | 2 | instant_electrical | langt=Sistem Güç; (div) |
| `An_L1AkimP1` | L1 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L1AkimP2` | L1 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L1VoltajP1` | L1 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L1VoltajP2` | L1 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L2AkimP1` | L2 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L2AkimP2` | L2 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L2VoltajP1` | L2 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L2VoltajP2` | L2 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L3AkimP1` | L3 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L3AkimP2` | L3 | A | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L3VoltajP1` | L3 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `An_L3VoltajP2` | L3 | V | 1 | instant_electrical | Anlık elektrik/motor ölçümü; (div) |
| `T_CalismaSayacP1` | Toplam sayaç (su, elektrik, çalışma, şalt) | h |  | counter | langt=Çalışma Sayacı; (col) |
| `T_CalismaSayacP2` | Toplam sayaç (su, elektrik, çalışma, şalt) | h |  | counter | langt=Çalışma Sayacı; (col) |
| `T_ElektrikSayacP1` | Toplam sayaç (su, elektrik, çalışma, şalt) | kW/h | 2 | counter | langt=Elektrik Sayacı; (div) |
| `T_ElektrikSayacP2` | Toplam sayaç (su, elektrik, çalışma, şalt) | kW/h | 2 | counter | langt=Elektrik Sayacı; (div) |
| `T_PompSaltSayisiP1` | Toplam sayaç (su, elektrik, çalışma, şalt) | adet |  | counter | langt=Şalt Sayısı; (col) |
| `T_PompSaltSayisiP2` | Toplam sayaç (su, elektrik, çalışma, şalt) | adet |  | counter | langt=Şalt Sayısı; (col) |
| `T_SuSayac` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ |  | counter | langt=Su Sayacı 1; (div) |
| `T_SuSayac2` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ |  | counter | langt=Su Sayacı 2; (div) |
| `T_SuSayacTotal` | Toplam sayaç (su, elektrik, çalışma, şalt) | m³ |  | counter | langt=Toplam ; (div) |
| `BakiyeKlor` | Bakiye klor | ppm |  | measurement | langt=Bakiye Klor Değer; (div) |
| `CikisBasinc1` | Ç.Basınç 1 | bar | 2 | unknown |  |
| `CikisBasinc2` | Ç.Basınç 2 | bar | 2 | unknown |  |
| `CikisDepoSeviye` | Çıkış deposu seviyesi | m | 2 | measurement |  |
| `Debimetre2` | Debi 2 | m³/h | 2 | measurement | Debi ölçümü 2 |
| `GirisBasincSensoru` | G.Basınç 1 | bar | 2 | unknown |  |
| `GirisBasincSensoru2` | G.Basınç 2 | bar | 2 | unknown |  |
| `GirisDepoSeviye` |  | m | 2 | unknown |  |
| `GirisDepoSeviye2` |  | m | 2 | unknown |  |
| `HatBasincSensoru` | H.Basınç 1 | bar | 2 | measurement | Hat basıncı |
| `HatBasincSensoru2` | H.Basınç 2 | bar | 2 | unknown |  |
| `Hm_P1` | [langt:Hm] | m | 2 | unknown | (div) |
| `Hm_P2` | [langt:Hm] | m | 2 | unknown | (div) |
| `P1GucDeger` | [langt:P1 Güç] | kWh |  | unknown | (col) |
| `P2GucDeger` | [langt:P2 Güç] | kWh |  | unknown | (col) |
| `PompaVerimDeger_P1` | [langt:Hidrolik Verim] | % | 2 | unknown | (col) |
| `PompaVerimDeger_P2` | [langt:Hidrolik Verim] | % | 2 | unknown | (col) |
| `SistemVerim_P1` | [langt:Sistem Verim] | % | 2 | unknown | (col) |
| `SistemVerim_P2` | [langt:Sistem Verim] | % | 2 | unknown | (col) |
| `Surucu1Frekans` | [langt:Çalışma Frekansı] | hz |  | unknown | (div) |
| `Surucu2Frekans` | [langt:Çalışma Frekansı] | hz |  | unknown | (div) |
| `ToplamDebi` | [langt:Toplam Debi] | m³ | 2 | unknown | (div) |
| `XD_CikisDepoYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |
| `XD_GirisDepo2Yukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |
| `XD_GirisDepoYukseklik` | Yapı/depo sabit boyut ayarı (yazma) | m | 2 | dimension_setting |  |

## JavaScript `data.*` Referansları (dim dışı mod/alarm/sayaç)

Aşağıdaki tag'ler GENEL.phtml JS bloğunda `data.X` olarak okunuyor ama görsel dim olarak çizilmiyor (mod seçim, alarm bayrağı, vb.):

- **install_constant**: `XV_KabloKayip`, `XV_Nmotor`, `XV_Nsurtunme`, `XV_SurucuKayip`
- **instant_electrical**: `An_Guc`
- **measurement**: `BasincSensoru`, `Debimetre1`, `Pompa1StartStopDurumu`
- **status**: `Pompa2StartStopDurumu`, `Pompa3StartStopDurumu`, `Pompa4StartStopDurumu`

## Alt Menü Sayfaları (MENU.phtml)

Kullanıcı bir ayar/konfigürasyon sorduğunda (örn. "depo doldurma ayarları nereden"), aşağıdaki tablodan ilgili alt sayfayı ve içindeki ayar parametrelerini verin. `Başlık` sayfanın `<h1>`'inden, `Ayar Parametreleri` sayfada tanımlı `<f id="...">` kaydedilebilir alanlardan türetilir.

| Sayfa (phtml) | Menü Etiketi | Sayfa Başlığı | Ayar Parametreleri |
|---|---|---|---|
| `surucu` | [langt:Sürücü] | [langt:Sürücü -1- Ayarları] | `XINV_SoftMinLimit_D1`, `XINV_SoftMaxLimit_D1`, `XINV_HardMaxLimit_D1`, `XC_SabitFrekansDeger_D1`, `XINV_SoftMinLimit_D2`, `XINV_SoftMaxLimit_D2`, `XINV_HardMaxLimit_D2`, `XC_SabitFrekansDeger_D2` |
| `sensor` | [langt:Sensör] | [langt:Sensör Ayarları] | `XS_HatBasincMin`, `XS_HatBasincMax`, `XS_HatBasincKalibre`, `HatBasincSensoru`, `XS_HatBasinc2Min`, `XS_HatBasinc2Max`, `XS_HatBasinc2Kalibre`, `HatBasincSensoru2` …+20 |
| `emniyet` | [langt:Emniyet] | [langt:Emniyet Ayarları] | `XE_DebiAlt`, `XE_DebiUst`, `XE_DebiSure`, `XE_DebiAlt2`, `XE_DebiUst2`, `XE_DebiSure2`, `XE_GirisDepoAlt`, `XE_GirisDepoUst` …+46 |
| `emniyet_reset_ayar` | [langt:Emniyet Reset] | [langt:Emniyet Reset Ayarları] | `XE_OtoAlarmResetSayac`, `XE_OtoAlarmResetSet`, `XE_OtoAlarmResetBeklemeSn`, `XE_OtoAlarmSayacResetlemeSn` |
| `giris_depo` | [langt:Giriş Depo Kontorlü.] | [langt:Giriş Depo Kontrolü] | `XB_GirisDepoUstP1`, `XB_GirisDepoAltP1`, `XB_GirisDepoUstP2`, `XB_GirisDepoAltP2`, `XD_GirisDepoEn`, `XD_GirisDepoBoy`, `XD_GirisDepoYukseklik`, `GirisDepoSeviye` |
| `cikis_depo` | [langt:Çıkış Depo Ayr.] | [langt:Çıkış Depo Ayarları] | `XD_CikisDepoEn`, `XD_CikisDepoBoy`, `XD_CikisDepoYukseklik`, `CikisDepoSeviye` |
| `depo_doldurma` | [langt:Depo Doldurma] | [langt:Depo Doldurma Ayarları] | `XD_DepoSeviyeAltP1`, `XD_DepoSeviyeUstP1`, `XD_DepoSeviyeAltP2`, `XD_DepoSeviyeUstP2` |
| `haberlesme` | [langt:Haberleşme] | [langt:Haberleşme Ayarlar] | `XH_SunucuHabTimeOut`, `XH_Link1HabTimeOut`, `XH_HabYokCalismaP1`, `XH_HabYokDurmaP1`, `XH_HabYokCalismaP2`, `XH_HabYokDurmaP2` |
| `antiblokaj` | [langt:Antiblokaj] | [langt:Antiblokaj Mod] | `XC_AntiBlokajCalismaP1`, `XC_AntiBlokajDurmaP1`, `XC_AntiBlokajCalismaP2`, `XC_AntiBlokajDurmaP2` |
| `modem_reset` | [langt:Modem Reset] | [langt:Modem Reset] | `XMOD_ModemResetTimeout` |
| `fonksiyonel_cikis` | [langt:Fonksiyonel Çıkış] | [langt:Fonksiyonel Çıkış Ayarları] | — |
| `verim1` | Verim 1 | [langt:Verim 1] | `XEF_MotorVerim_P1`, `XEF_SurucuKaybi_P1`, `XEF_MekanikKayip_P1` |
| `verim2` | Verim 2 | [langt:Verim 2] | `XEF_MotorVerim_P2`, `XEF_SurucuKaybi_P2`, `XEF_MekanikKayip_P2` |

## Birim Özeti

- **Basınç (bar)**: `CikisBasinc1`, `CikisBasinc2`, `GirisBasincSensoru`, `GirisBasincSensoru2`, `HatBasincSensoru`, `HatBasincSensoru2`
- **Debi**: `Debimetre`, `Debimetre2`
- **Seviye / uzunluk (m/cm)**: `CikisDepoSeviye`, `GirisDepoSeviye`, `GirisDepoSeviye2`, `Hm_P1`, `Hm_P2`, `XD_CikisDepoYukseklik`, `XD_GirisDepo2Yukseklik`, `XD_GirisDepoYukseklik`

## Not

- Bu dosya `scripts/generate_nview_skills.py` ile otomatik üretildi. Elle düzenlemeyin; regenerate çağrısı üzerine yazar.
- `langt:KEY` etiketleri çevirinin ham PHP key'idir; dil kaynağı erişilebildiğinde manuel eşleme yapılabilir.
- Yaklaşık tag rolleri prefix/ isim kurallarıyla türetildi; kesin semantik için aile skiline ve tag-naming.md'ye bakın.
