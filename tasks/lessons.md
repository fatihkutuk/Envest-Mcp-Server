# Lessons — Ajan Davranışı (Envest-Mcp-Server)

> Her düzeltmeden sonra buraya yeni satır ekle. Aynı hatayı tekrar yapma.

---

## L001 — "annexa" yaşlanma katsayısı DEĞİLDİR (22 Nisan 2026)

**Hata:** LLM annexa < 1 gördüğünde otomatik olarak "pompa %X yaşlanmış" yorumu üretti.

**Gerçek:** annexa = **katalog-gerçek ölçüm sapma toleransı** (ISO 9001 Annex A'dan kavramsal ödünç). Katalog her zaman tavandır; annexa kadar fark üretim/ölçüm normalidir.

**Kural:** "Pompada aşınma var" demek için **3 kanıt birlikte** olmalı:
1. annexa < 0.85 (tolerans dışı düşüş)
2. Zaman serisinde tutarlı H/Q düşüşü (tek ölçüm değil)
3. Mekanik işaret (titreşim, yağ sıcaklığı, kavitasyon gürültüsü)

Tekil düşük annexa ≠ aşınmış. Rapor dilinde "sapma toleransı dahilinde normal" denir, gerekmedikçe annexa'dan bahsedilmez.

---

## L002 — Kuyu pompalarında ToplamHm ayrıştırması well-lift'i ATLAMAMALI

**Hata:** Hidrolik analiz ilk sürümünde `ToplamHm = basınç + SuSeviye + sürtünme + yerel` olarak kuruldu. Residual %68 çıktı ve yanlış yorum riskine yol açtı.

**Gerçek:** Dalgıç kuyu pompası, üzerindeki **tüm su kolonunu** yukarı iter:
```
well_lift = max(0, nPMontaj − StatikSuSeviye)
```
Bu kalem çoğu zaman toplamın %40–60'ıdır. Atlarsan sürtünme payı doğru hesaplansa bile "residual büyük, hesap şüpheli" izlenimi oluşur.

**Kural:** `nView` 'kuyu' içeriyorsa `node_param.nPMontaj` + statik su seviyesini mutlaka oku ve well_lift'i ayrı bileşen olarak raporla.

---

## L003 — Mevcut client-side hesap dosyaları **tek gerçeklik kaynağıdır**

**Hata:** Sürtünme formülü ilk planda "Swamee-Jain explicit" olarak yazıldı. Oysa UI `calc.helper.js` iteratif Colebrook-White kullanıyor ve `g = 9.7905` gibi Türkiye pratiği sabitler içeriyor.

**Kural:** Hidrolik/ekonomik yeni tool yazarken, **önce** `\\10.10.10.72\public\dev.korubin\assets\js\calc.helper.js` (veya ilgili client-side kaynak) dosyasını oku. Formülleri, sabitleri (`g`, ν tablosu), birim dönüşümlerini (`XV_PipeRoughness / 1e9`) **birebir** taklit et. Server/client hesap ayrışması bug ve kullanıcı güven kaybı getirir.

---

## L004 — Önerilerde "asla zorla" kuralı

**Hata:** Eski skill akışı yatırım NPV pozitif çıkarsa boru büyütme öneriyordu. Sürtünme payı %3 iken bile.

**Kural:** Ekonomik pozitif sonuç **gerekli ama yeterli değil**. Hidrolik mantık da olmalı:
- friction_share < %10 → `recommended=false`, NPV pozitif bile olsa "statik baskın, boru değişimi kazanç sağlamaz" notu.
- LLM'in "mevcut pompa iyi" tanısına sadık kal; başka pompa/boru önerisi ancak **sayısal ve fiziksel** ortak kanıt varsa yapılır.

---

## L005 — Windows PowerShell + Python çağrısı

**Hata:** `python -c "..."` komutu "Python bulunamadı" hatası verdi (store-stub davranışı).

**Kural:** Windows'ta her zaman `py -c "..."` (launcher) kullan. Shell `python` alias'ı güvenilmez.

---

## L006 — Plan modu reddedildiğinde

**Hata:** Plan moduna `SwitchMode` denemesi kullanıcı tarafından reddedildi.

**Kural:** Bir kez reddedilirse bir daha deneme. Onun yerine `tasks/todo.md` dosyasına ayrıntılı plan yaz (user rule'u zaten bunu istiyor), kritik teyit sorularını (3'ü geçmeyecek) tek mesajda sor ve uygulamaya başla.

---

## L007 — Bilgi sorusu için kılavuz varsa SCADA tool'u çağırma (22 Nisan 2026)

**Hata:** "AQUA 100 modem status 2'de kalıyor" sorusuna cevap üretmek için **40'a yakın SCADA tool çağrısı** yapıldı. Oysa AQUA kullanım kılavuzu repoda PDF olarak duruyordu ve cevap doğrudan Tablo 1.1'de.

**Gerçek:** Bilgi sorusu ≠ durum sorusu. 
- **Bilgi sorusu** ("status 2 ne demek") → statik referans, kılavuzdadır.
- **Durum sorusu** ("bu cihazda şu an status ne") → canlı tag okuma.
- LLM ikisini karıştırıp bilgi sorusunu canlı tag'lerden + SQL'den türetmeye çalıştı.

**Kural:**
1. Cihaz/ürün hakkında **statik** bir soru geldiğinde **ilk adım** `list_skills` + ilgili cihaz skill'ini okumak. SCADA tool'una gerek yok.
2. Canlı durum teyidi gerekiyorsa **1 tane** `get_device_tag_values` ek çağrı yeter; 40 değil.
3. Kullanıcı belgeyi paylaşmışsa (PDF / image) onu skill'e çevirmek ana yatırım — sonraki her sorguda token tasarrufu sağlar.

---

## L008 — PDF → Skill dönüşümünde Vision, pypdf'ten güvenli

**Hata:** `pypdf` ve `pdfplumber` ile AQUA CNT kılavuzundan metin çıkarımı yapıldı — Türkçe karakterler bozuk çıktı (custom CID font encoding). Metin mühendisliği çalışmadı.

**Gerçek:** PDF'te custom font embedded olduğunda standart text extraction başarısız. **Vision / OCR** alternatifi gerekir.

**Kural:**
1. PDF → skill için `pypdfium2` ile sayfaları PNG olarak render et (scale 1.4 yeterli).
2. `Read` tool image okuması ile sayfa sayfa Vision'la geç; kritik tabloları markdown'a elle çevir.
3. Üretim sonunda PNG'leri **ve kaynak PDF'i de** sil — markdown skill dosyası kendi kendine yeter. Repo'yu MB'larca şişirmeye gerek yok. PDF gerekirse orijinal konumdan (envest-web assets vb.) tekrar alınabilir; skill dosyasında sadece "kaynak: X kılavuzu, Rev Y.Z" referansı kalmalı.
4. OCR (Tesseract) bu iş için gerekli değil — Vision zaten doğru okuyor.

---

## L009 — Skill bölümlemesinde LLM'in doğru dosyayı tek denemede bulması

**Hata:** Çok dosyalı skill eklendiğinde LLM "hangi dosya benim soruma cevap veriyor" diye sırayla her dosyayı açıp okuyabilir — token israfı.

**Gerçek:** `list_skills` **sadece metadata** (name + description + files listesi) döner. İçerik `get_skill` ile **lazy load**. Yani çok dosya olması TOKEN sorunu değil — **description kalitesi** sorunu.

**Kural — her yeni skill için:**
1. `description`: 2-3 cümle **+ çok sayıda keyword** (kullanıcı sorusu nasıl gelirse — Türkçe/İngilizce/kısa/uzun — hepsi). Bir paragraf yazma, yoğun ve eşleşmeye optimize yaz.
2. `SKILL.md` içinde **"Hangi soru → hangi dosya" routing tablosu**. LLM önce SKILL.md okur, sonra doğrudan ilgili alt dosyaya gider.
3. `core-rules/SKILL.md` → ana yönlendirme kuralını ekle ("X tipi soru geldiğinde önce Y skill'i, tool değil").
4. Alt dosyalar odaklı ve tek konu: bir soru tipi = bir dosya. Birleştirilmiş "mega dosya" routing'i zorlaştırır.

Smoke test zorunlu: `list_skills()` sonucunu gerçekte görerek metadata uzunluk + keyword eşleşmesini doğrula.

---

## L010 — Skill description YAML `|` literal block + loader `split("\n")[0]` = routing ölür (22 Nisan 2026)

**Hata:** AQUA CNT için 10 dosyalık skill, zengin 1869 karakterlik description ile yazıldı. Kullanıcı "modem status 2" sordu — LLM yine 13 tool çağırdı, skill'e girmedi. Routing tablosu, core-rules §10.1 vb. hepsi yerindeydi ama **LLM aqua-devices skill'ini list_skills çıktısında bulamadı**.

**Kök neden:** `mcps/scada/src/scada_mcp/skills/toolpack.py` içinde:
```python
desc = desc.strip().split("\n")[0]   # sadece ilk satır!
```
YAML `description: |` (literal block) style newline'ları korur. Benim description'ım 28 satıra bölünmüştü ve **ilk satır sadece** "AQUA CNT 100S / 100F / 100FP / 100SL kompakt pompa kontrol ve su izleme" (70 char) idi. İçinde ne "modem" ne "status" ne "alarm" vardı. LLM haklı olarak "bu benim sorumla eşleşmiyor" dedi.

**Fix (kök neden çözümü):** Loader'da satır satır kesmeyi bıraktım, tüm description'ı `" ".join(desc.split())` ile normalize ediyorum (newline → space, çoklu space → tek). Tüm 5 skill'den bu değişiklikle faydalanır, yeni skill eklendiğinde de otomatik çalışır.

**Kural:**
1. Skill description'ını YAML `|` (literal) ile yazmak istiyorsan kök neden çözüldüğü için sorun yok — ancak **her yeni skill eklendiğinde `list_skills` çıktısını fiilen simüle et** ve keyword'lerin normalize edilmiş metinde göründüğünü doğrula.
2. core-rules description'ına da "AQUA CNT, modem status, hedef status, alarm, register, modbus, APN, LED, CSQ, debimetre, cihaz dokuman" gibi **cihaz-bazlı yönlendirme keyword'leri** koy — LLM list_skills çıktısında *önce core-rules*'ı görürse oradan da `aqua-devices`'a yönelebilir.
3. Bir skill "yazıldığı halde LLM bulamıyor" semptomu varsa ilk kontrol: **loader nasıl gösteriyor?** Description içeriği değil, `list_skills` çıktısının **o anki formunu** incele.
