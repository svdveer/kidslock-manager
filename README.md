# 🔐 KidsLock Manager

**KidsLock Manager** is een Home Assistant Add-on gecombineerd met een Android TV applicatie om schermtijd effectief te beheren. Voorkom eindeloze discussies door limieten en bedtijden automatisch af te dwingen via je smart home.

## 🚀 Functies

* **Tijdslimieten**: Stel per TV een maximaal aantal minuten per dag in.
* **Bedtijd-slot**: De TV vergrendelt automatisch na een ingesteld tijdstip.
* **Onbeperkt Modus**: Schakel met één klik de restricties uit voor filmavonden of weekenden.
* **Live Monitoring**: Zie direct of de TV aanstaat, hoeveel tijd er nog over is en wat de huidige status is.
* **MQTT Integratie**: Volledige ondersteuning voor Home Assistant dashboards en automatiseringen.
* **Android TV App**: Een lichtgewicht client die het scherm vergrendelt met een instelbare pincode.

## 📦 Installatie

### 1. Android TV App

1. Download de nieuwste APK van de [Releases pagina](https://github.com/svdveer/kidslock-repository/releases).
2. Installeer de APK op je TV (bijv. via de 'Downloader' app of USB-stick).
3. Open de app en verleen de gevraagde rechten:
* **Toon boven andere apps** (Overlay permission).
* **Gebruikstoegang** (Usage access).


4. Noteer het **IP-adres** dat in de app wordt weergegeven.

### 2. Home Assistant Add-on

1. Ga naar je Home Assistant -> **Instellingen** -> **Add-ons** -> **Add-on winkel**.
2. Klik op de drie puntjes rechtsboven -> **Repositories**.
3. Voeg deze URL toe: `https://github.com/svdveer/kidslock-repository`.
4. Zoek naar **KidsLock Manager** en klik op **Installeren**.

## ⚙️ Configuratie

Stel je TV's en MQTT-gegevens in bij de tab **Configuratie** van de add-on:

```yaml
mqtt:
  host: "core-mosquitto"
  username: "je-mqtt-gebruiker"
  password: "je-wachtwoord"
tvs:
  - name: "Woonkamer"
    ip: "192.168.1.100"
    daily_limit: 120
    bedtime: "20:00"
    no_limit_mode: false

```

## 🛠️ Ontwikkeling

Deze add-on is gebouwd met:

* **FastAPI**: Voor de Web UI en API.
* **Paho-MQTT**: Voor communicatie met Home Assistant.
* **SQLite**: Voor het opslaan van resterende tijd en logs.
* **Python 3.12**: De kernlogica van de monitor loop.

## 📄 Licentie

Vrij te gebruiken voor persoonlijk gebruik (MIT Licentie).

---

### Hoe voeg je dit toe?

1. Open **Studio Code Server** in Home Assistant.
2. Maak een nieuw bestand aan in de root van je repo genaamd `README.md`.
3. Plak de bovenstaande tekst erin.
4. Sla op en `git push`. GitHub zal dit nu automatisch als een mooie startpagina tonen!

