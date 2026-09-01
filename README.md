# TacoMex Menu Manager

Desktop-Anwendung zur lokalen Pflege einer Restaurant-Speisekarte mit SQLite, PySide6 und templatebasierten Exporten.

## Voraussetzungen

- Python 3.12 oder neuer
- Windows, macOS oder Linux fuer die Entwicklung
- Chromium via Playwright fuer PDF-Export

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## Anwendung Starten

```bash
python -m app.main
```

Beim ersten Start wird `data/tacomex_menu.db` angelegt und mit Demo-Kategorien und Demo-Gerichten gefuellt.

## Tests Ausfuehren

```bash
pytest
```

## Aktueller Funktionsumfang

- Persistente SQLite-Datenbank mit SQLAlchemy-Modellen fuer Kategorien, Gerichte und Einstellungen
- Demo-Daten beim ersten Start
- PySide6-Hauptfenster mit professionellem Dark Theme, Kategorienliste, Gerichtetabelle und scrollbarem Editor
- Kategorien erstellen, umbenennen, aktiv/inaktiv setzen, loeschen und sortieren
- Gerichte erstellen, bearbeiten, duplizieren, aktiv/inaktiv setzen, loeschen und sortieren
- Tabellenmodus zum schnellen Bearbeiten vieler Preise
- Tastenkurzel: Strg+S zum Speichern, Entf zum Loeschen nach Rueckfrage
- JSON-Export und JSON-Import
- HTML-Export als responsive statische Smartphone-Speisekarte
- QR-Code-Export als PNG/SVG plus einfache Druckvorlage
- PDF-Service mit Playwright/Chromium und Jinja2-Template
- Lokale Logdatei unter `data/logs/tacomex_menu_manager.log`
- Manueller SQLite-Backup-Service

## Projektstruktur

```text
app/
  main.py
  gui/
  models/
  database/
  services/
  templates/
data/
exports/
tests/
```

## PDF-Export

Der PDF-Export rendert HTML/CSS per Playwright nach DIN A4. Die Vorlage liegt unter:

```text
app/templates/pdf/modern_dark/
```

Weitere Designs koennen parallel als neue Template-Ordner ergaenzt werden.

## HTML-Export

Der HTML-Export erzeugt einen vollstaendigen statischen Ordner:

```text
exports/html/
  index.html
  assets/style.css
```

Dieser Ordner kann spaeter direkt auf `menu.tacomex.de` hochgeladen werden.

## Spaetere Windows-EXE

Eine PyInstaller-Paketierung kann spaeter beispielsweise so vorbereitet werden:

```bash
pip install pyinstaller
pyinstaller --name "TacoMex Menu Manager" --windowed --add-data "app/templates;app/templates" app/main.py
```

Vor der finalen Paketierung sollten Icons, Migrationsstrategie und der Zielpfad fuer Benutzerdaten unter Windows festgelegt werden.
