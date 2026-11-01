# Website mit Herz & Hand KS – Anleitung

Die Website liegt kostenlos bei GitHub. Inhalte ändert ihr im Browser über das Bearbeitungsfenster **Pages CMS**. Nach jedem Speichern baut sich die Seite automatisch neu (1–2 Minuten).

## Einmalig einrichten (ca. 30 Minuten, am Computer)

### 1. GitHub-Konto anlegen
Auf github.com ein kostenloses Konto anlegen. Der Name taucht später in der Adresse auf, bis eure eigene Domain verbunden ist (z. B. `herzundhandks.github.io`).

### 2. Dateien hochladen – Weg A (Terminal, Mac)
ZIP entpacken, Terminal öffnen und den folgenden Block einfügen (Pfad ggf. anpassen).

Zum Kopieren am besten die Datei ANLEITUNG.md aus dem ZIP öffnen, nicht dieses PDF.

```
brew install gh
gh auth login
cd ~/Downloads/website-herz-und-hand
git init -b main
git add -A
git config user.name "HerzHand"
git config user.email "web@herzhand.invalid"
git commit -m "Website"
gh repo create herzhand-web --public --source . --push
```

`brew` ist der Homebrew-Paketmanager; falls er fehlt, zuerst von brew.sh installieren. `gh auth login` fragt ein paar Dinge: GitHub.com → HTTPS → Login with a web browser.

### 2. Dateien hochladen – Weg B (nur Browser)
1. Auf github.com oben rechts **+** → **New repository** → Name `herzhand-web` → **Public** → **Create repository**.
2. Auf „uploading an existing file“ klicken.
3. Im Finder versteckte Dateien sichtbar machen: **Cmd + Shift + .** (Punkt). Wichtig, sonst fehlen `.github` und `.pages.yml`.
4. Den **Inhalt** des entpackten Ordners (nicht den Ordner selbst) ins Browserfenster ziehen → **Commit changes**.
5. Prüfen: Im Repository müssen die Ordner `.github` und `content` sowie die Datei `.pages.yml` zu sehen sein. Fehlt `.github`, den Ordner noch einmal einzeln hochladen.

Das Repository muss öffentlich sein: Mit dem kostenlosen GitHub-Konto gibt es die Website nur für öffentliche Repositories. Es enthält ohnehin nur, was auf der Website steht.

### 3. Website einschalten
1. Im Repository: **Settings → Pages → Source: GitHub Actions** auswählen.
2. Die Vorlagen, die GitHub dort vorschlägt („Static HTML“, „Jekyll“ …), **nicht** anklicken. Der passende Ablauf ist schon dabei.
3. Oben auf **Actions** → links **Website veröffentlichen** → rechts **Run workflow** → grüner Knopf **Run workflow**. (Der erste Lauf direkt nach dem Hochladen schlägt fehl, weil die Website da noch nicht eingeschaltet war. Das ist normal.)
4. Nach 1–2 Minuten ist der Lauf grün. Die Adresse steht unter Settings → Pages.
5. Bei jedem Lauf zeigt GitHub unter **Summary** die Liste „Noch offen“: Dort steht, welche Angaben noch fehlen.

### 4. Bearbeitungsfenster verbinden
1. app.pagescms.org öffnen → mit GitHub anmelden.
2. Pages CMS den Zugriff auf das Repository `herzhand-web` erlauben.
3. Fertig: Links seht ihr „Allgemein“, „Wattmusikanten-Kollektion“, „Persönlich gemacht“, „Was wir machen“, „Texte der Startseite“, „Impressum und Datenschutz“.
4. Weitere Personen könnt ihr per E-Mail einladen, sie brauchen dafür kein GitHub-Konto.

### 5. Eigene Domain (optional, ca. 1 € im Monat)
1. Domain bei einem Anbieter eurer Wahl kaufen.
2. Beim Anbieter in den DNS-Einstellungen eintragen:
   - A-Einträge für die Domain selbst: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - CNAME für `www`: `EUER-GITHUB-NAME.github.io`
3. Im Repository unter **Settings → Pages → Custom domain** die Domain eintragen, später **Enforce HTTPS** anhaken.
4. Empfohlen: Die Domain in den GitHub-Einstellungen unter **Pages → Verified domains** bestätigen. Das schützt davor, dass jemand anderes sie übernimmt.

## Im Alltag

| Was | Wo im Bearbeitungsfenster |
|---|---|
| Preise, Produkte, Fotos | Kollektion und „Persönlich gemacht“ |
| Öffnungszeiten | „Texte der Startseite“ → Läden |
| Texte, Über uns | „Texte der Startseite“ |
| E-Mail, Etsy-Link, Instagram | „Allgemein“ |
| Impressum, Datenschutz | „Impressum und Datenschutz“ |

**Fotos:** einfach hochladen. Große Handyfotos werden beim Bauen automatisch verkleinert. Am schönsten wirken sie im Hochformat 4:5 (Produkte) bzw. quer 4:3 (Handwerke, Läden). Zu jedem Foto kurz beschreiben, was zu sehen ist (für Suchmaschinen und Menschen mit Sehbehinderung).

**Leere Felder** werden auf der Seite einfach ausgeblendet. Ein Produkt ohne Foto zeigt „Foto folgt“.

**Noch kein Etsy-Shop?** Das Feld „Link zum Etsy-Shop“ unter „Allgemein“ einfach leer lassen. Dann heißen alle Shop-Knöpfe „Anfragen“ und führen zur E-Mail, der Hinweis in der Kollektion zeigt auf die Läden. Sobald der Shop steht: Link eintragen, speichern – fertig.

**Etwas kaputt gemacht?** Jede Änderung wird gespeichert. Auf GitHub unter **Commits** lässt sich jede Version wiederherstellen.

**Änderung erscheint nicht?** Unter **Actions** nachsehen: Ein roter Lauf bedeutet, dass die Seite nicht neu gebaut wurde. Die alte Fassung bleibt dann online. Meist hilft es, die letzte Änderung rückgängig zu machen.

**Fotos vom iPhone:** Das iPhone speichert oft im Format HEIC, das Browser nicht zeigen. In den iPhone-Einstellungen unter Kamera → Formate „Maximale Kompatibilität“ wählen, dann entstehen JPG-Dateien.

## Vor dem Start ausfüllen
- E-Mail-Adresse für Anfragen
- Preise
- Adresse Burhave, Hausnummer Bernhardstraße, Öffnungszeiten
- Über uns: Text, Namen, Werkstattfoto
- Fotos: Buch, Kalender, Handtuch, Stickerei
- Impressum: Name, Anschrift, E-Mail
- Datenschutzerklärung aus einem Generator (z. B. e-recht24 oder datenschutz-generator.de). Darin angeben: Hosting bei GitHub Pages (GitHub Inc., USA; Server speichern IP-Adressen in Logdateien), keine Cookies, kein Tracking, Schrift wird lokal geladen, Links zu Etsy, Instagram und Google Maps.

**Impressum bei zwei Inhabern:** Führt ihr das Geschäft zu zweit, seid ihr in der Regel eine GbR. Dann gehören der Name der GbR und beide Namen ins Impressum.

## Hinweis zum Hosting
GitHub Pages ist laut den Nutzungsbedingungen nicht als kostenloser Hoster für Onlineshops oder gewerbliche Seiten gedacht. Eure Seite verkauft nichts selbst, sondern verweist auf Etsy; das ist eine Grauzone. Wer auf Nummer sicher gehen will, verbindet dasselbe Repository kostenlos mit **Cloudflare Pages** (gewerbliche Nutzung erlaubt): Dort „Mit Git verbinden“, Build-Befehl `pip install pillow && python build.py`, Ausgabeordner `_site`. Pages CMS funktioniert genauso weiter. Danach in GitHub unter Settings → Pages die Seite abschalten, damit es sie nicht doppelt gibt. Auf Cloudflare wird ohne weiteren Schritt eine Ersatzschrift statt Figtree angezeigt.

Hinweis: Ich bin kein Anwalt. Impressum und Datenschutz vor dem Start bitte prüfen lassen oder einen Generator nutzen.
