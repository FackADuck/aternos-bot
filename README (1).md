# Aternos Discord Bot

Een Discord bot die de status van je Aternos server weergeeft en je de server kunt laten starten via een knop.

## Installatie

### 1. Vereisten
- Python 3.10 of hoger
- pip

### 2. Installeer de packages
```bash
pip install -r requirements.txt
```

### 3. Maak een `.env` bestand aan
Kopieer `.env.example` naar `.env` en vul je gegevens in:
```bash
cp .env.example .env
```

Vul dan in:
- `DISCORD_TOKEN` → van https://discord.com/developers/applications
- `ATERNOS_USERNAME` / `ATERNOS_PASSWORD` → je Aternos login
- `ATERNOS_SERVER_NAME` → (deel van) het adres van je server
- `STATUS_CHANNEL_ID` → ID van het kanaal voor het statusbericht

### 4. Discord bot instellen
1. Ga naar https://discord.com/developers/applications
2. Maak een nieuwe applicatie aan
3. Ga naar "Bot" → kopieer de token → plak in `.env`
4. Onder "Privileged Gateway Intents": zet **Message Content Intent** aan
5. Ga naar "OAuth2 → URL Generator":
   - Scopes: `bot`
   - Bot permissions: `Send Messages`, `Read Messages/View Channels`, `Manage Messages`, `Embed Links`
6. Open de gegenereerde URL om de bot toe te voegen aan je server

### 5. Kanaal instellen
1. Zet ontwikkelaarsmodus aan in Discord (Instellingen → Geavanceerd)
2. Rechtsklik op het kanaal → "Kanaal-ID kopiëren"
3. Plak het ID in `.env` bij `STATUS_CHANNEL_ID`
4. Zorg dat de bot alleen berichten van zichzelf kan zien in dit kanaal (andere gebruikers: geen schrijfrechten)

### 6. Starten
```bash
python bot.py
```

## Wat doet de bot?
- Plaatst automatisch 1 bericht in het opgegeven kanaal
- Toont de serverstatus met kleurcodering:
  - 🟢 Groen = Online
  - 🟠 Oranje = Aan het starten
  - 🔴 Rood = Offline
- Toont een **▶ Start Server** knop als de server offline is
- Ververst elke 30 seconden automatisch
