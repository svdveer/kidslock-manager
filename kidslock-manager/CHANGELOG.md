# 📝 Changelog - KidsLock Manager

## 1.1.9 (Huidige Versie)
- 🚀 **Definitieve Ingress Fix**: Alle formulier-acties zijn nu relatief gemaakt. Geen `404 Not Found` meer na het klikken op vergrendel-knoppen.
- 🔗 **Slimme Redirects**: De webserver begrijpt nu de Ingress-tunnel van Home Assistant beter door gebruik van `./` redirects.
- 🎨 **UI Optimalisatie**: De interface schaalt nu beter op mobiele telefoons (Dashboard-vriendelijk).

## 1.1.8
- 🛠️ **Foutafhandeling**: Timeout toegevoegd aan TV-verbindingen. De interface "hangt" niet meer als een TV offline is.
- 🛡️ **Verbinding Fix**: Problemen met weigerende verbindingen (Connection Refused) worden nu netjes gelogd in de Add-on logs.
- ⏱️ **Default Waarden**: De config is korter omdat de add-on nu zelf begrijpt dat 120 min en 21:00 de standaard zijn.

## 1.1.7
- ✨ **Onbeperkt Modus**: Visuele ondersteuning voor de "∞" status op het dashboard.
- 🕒 **Pauze Logica**: De klok stopt nu direct met aftellen als de TV niet meer reageert op een Ping.
- 🔒 **Auto-Lock**: Verbeterde bedtijd-controle die strikter handhaaft.

## 1.1.0 - 1.1.6
- Initiële versies met MQTT integratie en basis Web UI.