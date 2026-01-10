# 🔐 KidsLock Manager

**KidsLock Manager** is een Home Assistant Add-on gecombineerd met een Android TV applicatie om schermtijd effectief te beheren. Voorkom eindeloze discussies door limieten en bedtijden automatisch af te dwingen via je smart home.

## 🚀 Functies

* **Tijdslimieten**: Stel per TV een maximaal aantal minuten per dag in.
* **Bedtijd-slot**: De TV vergrendelt automatisch na een ingesteld tijdstip.
* **Onbeperkt Modus (∞)**: Schakel met één klik alle restricties uit voor filmavonden of weekenden.
* **No-Refresh Web UI**: Een moderne interface die perfect werkt binnen de Home Assistant zijbalk en op dashboards.
* **MQTT Discovery**: TV's verschijnen automatisch als apparaten in Home Assistant (Switches & Sensoren voor resterende tijd).
* **Live Monitoring**: Zie direct of de TV online is en hoeveel tijd er nog over is.

## 📦 Installatie

### 1. Android TV App
1.  Download de nieuwste APK van de [Releases pagina](https://github.com/svdveer/kidslock-repository/releases).
2.  Installeer de APK op je TV (bijv. via de 'Downloader' app of een USB-stick).
3.  Verleen de gevraagde rechten in de Android instellingen:
    * **Toon boven andere apps** (Overlay permission).
    * **Gebruikstoegang** (Usage access).
4.  **Beheerder-pincode**: De standaard pincode om de TV handmatig te ontgrendelen is `1234` (instelbaar in de app).
5.  Noteer het **IP-adres** dat in de app wordt weergegeven.

### 2. Home Assistant Add-on
1.  Ga naar **Instellingen** > **Add-ons** > **Add-on winkel**.
2.  Klik op de drie puntjes rechtsboven > **Repositories**.
3.  Voeg deze URL toe: `https://github.com/svdveer/kidslock-repository`.
4.  Zoek naar **KidsLock Manager** en klik op **Installeren**.

## ⚙️ Configuratie

### MQTT Instellingen
Stel je MQTT-gegevens in bij de tab **Configuratie** van de add-on. Dit is nodig voor de communicatie met Home Assistant.

```yaml
mqtt:
  host: "core-mosquitto"
  port: 1883
  username: "je-gebruiker"
  password: "je-wachtwoord"

```

### TV's beheren

Zodra de add-on is gestart, klik je op **Web-interface openen**. Hier kun je:

* TV's toevoegen op basis van hun IP-adres.
* Dagelijkse tijdslimieten instellen (in minuten).
* Bedtijden configureren.
* Handmatig extra tijd toevoegen of de TV direct vergrendelen.

## 🛠️ Home Assistant Integratie

Omdat de add-on gebruikmaakt van MQTT Discovery, verschijnen de TV's automatisch als apparaten in Home Assistant. Je kunt ze vinden onder **Instellingen > Apparaten & Diensten > MQTT**.

* **Switch**: Gebruik de switch om de TV handmatig op slot te zetten of te ontgrendelen.
* **Sensor**: Volg de resterende tijd in minuten op je eigen dashboard.

## 📄 Licentie

MIT Licentie - Vrij voor persoonlijk gebruik.
Wil je dat ik nog even kritisch kijk naar de **pincode-functionaliteit** in de `main.py`, of is de huidige opzet voor nu voldoende voor je brainstormsessie?

```
