---
name: alarm-codes
description: |
  SCADA alarm ve cihaz durum kodlari.
  Use when: alarm durumlarini yorumlamak, cihaz statusCode anlamak gerektiginde.
  Keywords: alarm, durum, statusCode, calisiyor, ariza, hata.
version: "1.0.0"
---

# Korubin SCADA Alarm ve Durum Kodlari

## Channel Device Status Kodlari (statusCode)

Kepware/DataExchanger cihazlarinin baglanti durumu icin kullanilir. `channeldevice.statusCode` ve `channeldevicestatus` tablolarindan gelir.

### Calisiyor (Aktif) Kodlari
Bu kodlardan biri goruldugunde cihaz "calisiyor" kabul edilir:

| Kod | Anlam |
|-----|-------|
| 11 | Calisiyor (normal) |
| 31 | Calisiyor (alternatif) |
| 41 | Calisiyor (alternatif) |
| 61 | Calisiyor |
| 71 | Calisiyor |
| 81 | Calisiyor |
| 91 | Calisiyor |

### Hatali / Calismiyor Kodlari
Bu kodlardan biri goruldugunde cihazda iletisim sorunu veya ariza vardir:

| Kod | Anlam |
|-----|-------|
| 12 | Hatali / Calismiyor |
| 22 | Hatali / Calismiyor |
| 32 | Hatali / Calismiyor |
| 42 | Hatali / Calismiyor |
| 52 | Hatali / Calismiyor |
| 62 | Hatali / Calismiyor |
| 72 | Hatali / Calismiyor |
| 82 | Hatali / Calismiyor |
| 92 | Hatali / Calismiyor |

**Not**: Gercek statusDefinition metni veritabanindaki `channeldevicestatus` tablosundan gelir ve kuruluma gore farklilik gosterebilir. Yukaridaki liste PHP DataExchangerTools / DashboardTools ile ayni "calisiyor" / "calismiyor" siniflandirmasini kullanir.

## Node Durumlari (nState)

`kbindb.node` tablosundaki `nState` alani:

| Deger | Anlam |
|-------|-------|
| >= 0 | Aktif nokta |
| < 0 | Pasif / silinmis nokta |

## Alarm Parametreleri

`kbindb.alarmparameters` tablosu alarm tanimlarini icerir:
- `nid`: Alarm'in bagli oldugu node ID
- `alType`: Alarm tipi
- `state`: Alarm tanim durumu (aktif/pasif)

`kbindb.alarmstate` tablosu anlik alarm durumlarini tutar:
- `state = 1`: Su an tetiklenmis (aktif alarm)
- `state = 0`: Normal / alarm yok

## Emniyet Alarm Parametreleri (XE_ prefix)

Emniyet ayarlarinda tanimli parametreler (sensor.phtml, emniyet.phtml):

| Tag | Aciklama | Birim |
|-----|----------|-------|
| `XE_FrekansAlt` | Frekans alt siniri | Hz |
| `XE_FrekansUst` | Frekans ust siniri | Hz |
| `XE_FrekansSure` | Frekans gecikme suresi | sn |
| `XE_FrekansEylem` | Frekans eylem (pompa dursun) | boolean |
| `XE_VoltajAlt` | Voltaj alt siniri | V |
| `XE_VoltajUst` | Voltaj ust siniri | V |
| `XE_VoltajSure` | Voltaj gecikme suresi | sn |
| `XE_AkimAlt` | Akim alt siniri | A |
| `XE_AkimUst` | Akim ust siniri | A |
| `XE_BasincAlt` | Basinc alt siniri | bar |
| `XE_BasincUst` | Basinc ust siniri | bar |

Her emniyet parametresinin bir "Eylem" (XE_*Eylem) checkbox'i vardir. Isaretlenirse sinir asildiginda pompa durur.

## Alarm Sorgu Araclari

- `list_alarms`: Tum alarm tanimlarini listeler
- `get_active_alarms`: Su an tetiklenmis alarmlari getirir
- `get_alarm_subscribers`: Alarm abonelerini (bildirim alacak kullanicilari) listeler
- `get_alarm_statistics`: Belirli zaman araliginda alarm istatistikleri
- `export_active_alarms`: Aktif alarmlari Excel/CSV olarak disari aktarir
