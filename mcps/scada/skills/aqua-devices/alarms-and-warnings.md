# AQUA CNT — Alarmlar ve Uyarılar (Tablo 4.1 + Uyarı/Alarm Word)

> **Kaynak:** AQUA CNT Kullanım Kılavuzu, Tablo 4.1 (s28) + Uyarı Word 1
> bit tablosu + Alarm Word 1 bit tablosu (s34).

- **Kırmızı LED** saniyede bir yanıp sönüyorsa sistemde **alarm** var.
- Alarm otomatik olarak **3 defa × 15 dk** arayla kendini resetler.
  4. kez oluşursa **kalıcı alarm** olur ve kullanıcının **manuel reset**
  yapması gerekir (ana menü → Alarm ve Uyarılar → OK tuşu).
- Alarm / Uyarı değerlerinin register karşılığı için `modbus-reference.md`.

---

## 1. Tablo 4.1 — Alarm Listesi (Ekran Adı + Anlamı)

| Alarm (ekran) | Açıklama |
|---|---|
| **Akım Alarm** | Akım Motor Korumada tanımlanan min/max aralığının dışında |
| **Basınç Alarm** | Basınç Motor Korumada tanımlanan aralığın dışında |
| **Debi Alarm** | Debi Motor Korumada tanımlanan aralığın dışında |
| **Motor Calisma Hata** | Motora start verildi, 30 sn içinde **"çalışıyor bilgisi"** gelmedi |
| **Motor Termik Hata** | Motor termiği açık **veya** sürücü hazır değil (dijital giriş) |
| **Su Seviyesi Alarm** | Seviye Motor Korumada tanımlanan min/max aralığının dışında |
| **Analizor Hab. Hata** | Akım hatası tanımlı **ve** analizör ile haberleşme yok |
| **Debimetre Hab. Uyarı** | Debi hatası tanımlı değil **ve** debimetre haberleşme yok |
| **Analizor Hab. Uyarı** | Akım hatası tanımlı değil **ve** analizör ile haberleşme yok |
| **Pil Sıcaklık Düşük** | Pil NTC < 0 °C (şarj olamaz) |
| **Pil Sıcaklık Yüksek** | Pil NTC > 45 °C (şarj olamaz) |
| **Hafızaya Ulaşılmıyor** | Log flash hafıza arızası → serviste değerlendir |
| **AdcKanal1Ulasilamiyor** | Analog kanal 1 ulaşılamıyor → servise gönder |
| **AdcKanal2Ulasilamiyor** | Analog kanal 2 ulaşılamıyor → servise gönder |
| **AdcKanal3Ulasilamiyor** | Analog kanal 3 ulaşılamıyor → servise gönder |
| **SurucuElModCalisiyor** | Motor **çalış çıkışı verilmeden** "çalışıyor girişi" geliyor → sürücü el moda alınmış |
| **Dusuk Guc Modu Aktif** | Pil gücü zayıf **ve** harici besleme yok |
| **Voltaj Alarm** | Voltaj, Motor Koruma Min/Max Voltaj aralığının dışında |
| **Giriş Besleme Voltajı** | Giriş Besleme Voltajı düşük |
| **Pil Kapalı** | Pil anahtarı kapalı konumda |

---

## 2. Uyarı Word 1 (Modbus Register 26) — Bit Bit

| Bit | Uyarı Adı | Ne zaman oluşur? |
|---|---|---|
| 0 | Analizor Hab. Uyarı | Akım hata tanımsız, analizör ile hab. yok |
| 1 | Debimetre Hab. Uyarı | Debi hata tanımsız, debimetre ile hab. yok |
| 2 | Log Bir Tur Döndü | Flash log dairesel tampon bir tur döndü |
| 3 | Lcd Bağlı Değil | Membran panel kablosu kopuk / kontrol et |
| 4 | Flash Hafızaya Ulaşılamıyor | Flash chip hatası |
| 5 | ADC Kanal1 Ulaşılamıyor | AI1 arızalı |
| 6 | ADC Kanal2 Ulaşılamıyor | AI2 arızalı |
| 7 | ADC Kanal3 Ulaşılamıyor | AI3 arızalı |
| 8 | Sürücü El Modda Çalışıyor | El moda alınmış, AQUA çıkış vermediği halde çalışıyor |
| 9 | Pil kapalı | Pil anahtarı kapalı |
| 10-15 | **Yedek** | - |

> `UyarılarWord-2` (register 27) **şu an tüm bitleri yedek**; gelecekte
> kullanılmak üzere rezerve.

---

## 3. Alarm Word 1 (Modbus Register 28) — Bit Bit

| Bit | Alarm Adı | Açıklama |
|---|---|---|
| 0 | Motor Calisma Hata | Start verildi, 30 sn'de "çalışıyor" bilgisi gelmedi |
| 1 | Motor Termik Hata | Termik açık / sürücü hazır değil |
| 2 | Su Seviye Alarm | Seviye koruma aralığı dışında |
| 3 | Akım alarm | Akım koruma aralığı dışında |
| 4 | Debi Alarm | Debi koruma aralığı dışında |
| 5 | Basınc Alarm | Basınç koruma aralığı dışında |
| 6 | Analizor Hab. Hata | Analizör haberleşme kalıcı hata |
| 7 | Debimetre Hab hata | Debimetre haberleşme kalıcı hata |
| 8 | SSR Hata | Sıvı Seviye Rölesi tetiklendi |
| 9 | Giriş Voltaj Yüksek | Besleme voltajı üst limit üstünde |
| 10 | Voltaj Alarm | Motor Koruma Voltaj aralığı dışında |
| 11-15 | **Yedek** | - |

> `AlarmlarWord-2` (register 29) **yedek** (rezerve).

---

## 4. Alarm Reset Mantığı

1. Alarm oluşur → kırmızı LED yanıp söner + motor durur.
2. **15 dk sonra** kendi kendine reset → tekrar çalışır.
3. Aynı alarm art arda **3 defa** oluşursa "kalıcı alarm" haline gelir.
4. Kalıcı alarmda:
   - Ekranda **Alarm ve Uyarılar** menüsüne gir.
   - Alarmı inceledikten sonra **OK tuşu** ile resetle.
   - VEYA Modbus Control Word 1 bit 0 (Alarm Reset) yazarak resetle.

---

## 5. Alarma Göre Önce Kontrol Edilmesi Gerekenler

| Alarm | İlk kontrol |
|---|---|
| Motor Calisma Hata | Sürücü çıkışta mı? Motor kontaktörü geliyor mu? Termik? |
| Motor Termik Hata | Motor koruma dijital girişi; termik kontaktör |
| SurucuElModCalisiyor | Sürücü paneli EL/OTO tuşu → **OTO** konuma al |
| Su Seviyesi Alarm | Min/Max Su Seviye Koruma ayarları doğru mu? Sensör tanımlı mı? |
| Akım Alarm | Motor çekiş akımı; pompa tıkalı/boşa çalışıyor mu? |
| Basınç / Debi Alarm | Sensör kalibrasyonu, hat tıkalı mı, çekvalf? |
| Pil Sıcaklık Düşük/Yüksek | Pano içi sıcaklık; kapalı alan ısınıyorsa havalandır |
| Giriş Voltaj Yüksek | Güneş paneli şarj regülatörü aşırı mı? |
| Voltaj Alarm | Trafo/şebeke; Min/Max Voltaj Koruma ayarları |
| Pil Kapalı | Pano içindeki **pil anahtarını sağ** konuma getir |
| Analizor / Debimetre Hab. | RS485 hattı, ID (Debimetre=1, Analizör=2), baud 9600/8/N |
| AdcKanal1/2/3 Ulaşılamıyor | Donanımsal — **üretici ile iletişime geç** |

Koruma eşiklerinin ne olduğunu ve nasıl ayarlandığını için
`motor-protection.md` dosyasına bak.
