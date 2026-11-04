#!/usr/bin/env python3
"""Baut die Website aus den Inhalten in content/ nach _site/.
Läuft automatisch bei jeder Änderung (GitHub Actions). Lokal: python3 build.py
Nur Python-Standardbibliothek; Pillow ist optional und verkleinert große Fotos."""
import json, os, shutil, html, re, sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "_site")
FEHLT = []

class D(dict):
    """Dict, das bei fehlenden Schlüsseln leer zurückgibt statt abzubrechen."""
    def __getitem__(self, k):
        v = dict.get(self, k, "")
        return "" if v is None else v
    def get(self, k, d=""):
        v = dict.get(self, k, d)
        return d if v is None else v

def _d(x):
    if isinstance(x, dict): return D({k: _d(v) for k, v in x.items()})
    if isinstance(x, list): return [_d(v) for v in x]
    return x

def lade(name):
    try:
        with open(os.path.join(ROOT, "content", name), encoding="utf-8") as f:
            return _d(json.load(f))
    except FileNotFoundError:
        FEHLT.append(f"Datei fehlt: content/{name}"); return D()
    except json.JSONDecodeError as ex:
        print(f"FEHLER: content/{name} ist beschädigt ({ex}). Die Website wird nicht neu veröffentlicht, die alte Fassung bleibt online.")
        zf = os.environ.get("GITHUB_STEP_SUMMARY")
        if zf:
            with open(zf, "a", encoding="utf-8") as f:
                f.write(f"## ❌ Nicht veröffentlicht\n\nDie Datei content/{name} ist beschädigt. Letzte Änderung rückgängig machen.\n")
        sys.exit(1)

def obj(x):
    return x if isinstance(x, dict) else D()

def liste(x):
    return [obj(i) for i in x] if isinstance(x, list) else []

def e(s):  # Text sicher ins HTML
    return html.escape(str(s or ""), quote=True)

def bildpfad(p):
    p = (p or "").strip()
    return p.lstrip("/") if p else ""

def pruefe(wert, was):
    if not str(wert or "").strip():
        FEHLT.append(was)
    return wert

# ---------- Shop ----------
def preis_cent(s):
    """'12,90 €' → 1290. 'ab 4,90' oder leer → None (nicht bestellbar, nur Anzeige)."""
    t = str(s or "").strip().lower()
    if not t or t.startswith("ab") or " ab " in t: return None
    m = re.search(r"\d[\d.,]*", t)
    if not m: return None
    z = m.group(0)
    if "," in z:                      # 1.290,50 → Punkt ist Tausender
        ganz, _, rest = z.partition(","); ganz = ganz.replace(".", "")
    elif z.count(".") == 1 and len(z.split(".")[1]) <= 2:   # 12.90 → Punkt ist Komma
        ganz, rest = z.split(".")
    else:                             # 1.290 → Tausender
        ganz, rest = z.replace(".", ""), ""
    if not ganz.isdigit(): return None
    return int(ganz) * 100 + int((rest or "0")[:2].ljust(2, "0"))

def euro(cent):
    return f"{cent // 100},{cent % 100:02d} €"

def slug(t):
    t = str(t or "").lower()
    for a, b in [("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")]: t = t.replace(a, b)
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "artikel"

def wahr(x, standard=False):
    if isinstance(x, bool): return x
    if x in (None, ""): return standard
    return str(x).strip().lower() in ("1", "true", "ja", "yes", "on")

def shop_einstellungen(a):
    sh = obj(a.get("shop"))
    return D({
        "aktiv": wahr(sh.get("aktiv"), False),
        "schluessel": (sh.get("schluessel") or "").strip(),
        "pauschale": preis_cent(sh.get("versand_pauschale")) if str(sh.get("versand_pauschale") or "").strip() else 490,
        "frei_ab": preis_cent(sh.get("versandfrei_ab")) if str(sh.get("versandfrei_ab") or "").strip() else None,
        "lieferzeit": (sh.get("lieferzeit") or "3–5 Werktage nach Zahlungseingang").strip(),
        "lieferzeit_wunsch": (sh.get("lieferzeit_wunsch") or "5–10 Werktage nach Zahlungseingang").strip(),
        "abholung": (sh.get("abholung_text") or "Abholung im Allee Café in Burhave oder nach Absprache in Nordenham").strip(),
        "zahlung": (sh.get("zahlung_text") or "Vorkasse per Überweisung oder PayPal – die Rechnung mit allen Angaben kommt per E-Mail.").strip(),
    })

PRODUKTE = []   # alle bestellbaren Artikel, für das eingebettete Shop-JSON
def produkt_daten(p, bereich, id_vorgabe=None):
    pid = id_vorgabe or f"{slug(bereich)[:1]}-{slug(p.get('name'))}"
    n = 2
    while any(x["id"] == pid for x in PRODUKTE): pid = f"{pid}-{n}"; n += 1
    cent = preis_cent(p.get("preis"))
    d = {"id": pid, "name": str(p.get("name") or ""), "beschreibung": str(p.get("beschreibung") or ""),
         "text": str(p.get("beschreibung_lang") or ""), "preis": cent, "preis_text": str(p.get("preis") or ""),
         "bild": bildpfad(p.get("bild")), "alt": str(p.get("bild_beschreibung") or ""),
         "wunschtext": wahr(p.get("wunschtext")), "wunschtext_hinweis": str(p.get("wunschtext_hinweis") or ""),
         "verfuegbar": wahr(p.get("verfuegbar"), True), "bereich": bereich}
    PRODUKTE.append(d)
    return d

# ---------- Logo ----------
HERZ = ("M0 93 C5 97.5 10 97.5 15 93 C20 88.5 25 88.5 30 93 C37 99.3 46 88.8 50 86 C70 72 90 58 90 38 C90 24 80 15 68 15 "
        "C59 15 53 20 50 27 C47 20 41 15 32 15 C20 15 10 24 10 38 C10 56 28 70 44 81")
NADEL = "M-2 -2.4 L30 0 L-2 2.4 C-7 2.4 -9 1.2 -9 0 C-9 -1.2 -7 -2.4 -2 -2.4 Z"
_n = [0]
def herz(breite, farbe="#1E3A4C"):
    _n[0] += 1; i = f"h{_n[0]}"
    hoehe = round(breite * 87.78 / 96.4)
    return (f'<svg width="{breite}" height="{hoehe}" viewBox="-3.2 11.8 96.4 87.78" aria-hidden="true">'
            f'<mask id="{i}" maskUnits="userSpaceOnUse" x="-3.2" y="11.8" width="96.4" height="87.78"><rect x="-3.2" y="11.8" width="96.4" height="87.78" fill="#fff"/>'
            f'<ellipse transform="translate(44 81) rotate(34.51)" cx="-5" cy="0" rx="2.2" ry="0.95" fill="#000"/></mask>'
            f'<g mask="url(#{i})"><path d="{HERZ}" fill="none" stroke="{farbe}" stroke-width="4.4" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path transform="translate(44 81) rotate(34.51)" d="{NADEL}" fill="{farbe}"/></g></svg>')

def faden():
    w = "M0 18 C8 25 16 25 24 18 C32 11 40 11 48 18 C56 25 64 25 72 18 C80 11 88 11 96 18 C104 25 112 25 120 18 C128 11 136 11 144 18 C152 25 160 25 168 18"
    return (f'<div class="faden" aria-hidden="true"><svg width="170" height="36" viewBox="0 0 170 36" style="margin-right:-3px;margin-top:15px">'
            f'<path class="welle-linie" d="{w}" fill="none" stroke="#1E3A4C" stroke-width="2" stroke-linecap="round"/></svg>{herz(44)}</div>')

# ---------- Bausteine ----------
def bild(p, alt, extra=""):
    p = bildpfad(p)
    if p and not str(alt or "").strip():
        FEHLT.append(f"Bildbeschreibung fehlt: {p}")
    if not p:
        return f'<div class="platzhalter" {extra}>Foto folgt</div>'
    return f'<img src="{e(p)}" alt="{e(alt)}" loading="lazy" decoding="async" {extra}>'

def produktkarte(p, hell=False, bereich="", shop=None):
    pruefe(p.get("bild"), f"{bereich}: Foto für „{p.get('name')}“")
    pruefe(p.get("preis"), f"{bereich}: Preis für „{p.get('name')}“")
    link = (p.get("etsy_link") or "").strip()
    d = produkt_daten(p, bereich)
    pt = str(p.get("preis") or "").strip()
    if pt and "€" not in pt: pt += " €"
    preis = (f'<div class="preis">{euro(d["preis"])}</div>' if d["preis"] is not None else (f'<div class="preis">{e(pt)}</div>' if pt else ""))
    bestellbar = bool(shop and shop["aktiv"] and d["preis"] is not None)
    if bestellbar:
        name = f'<a class="karte-link" href="warenkorb.html#artikel/{e(d["id"])}" data-artikel="{e(d["id"])}">{e(p.get("name"))}</a>'
    elif link:
        name = f'<a class="karte-link" href="{e(link)}" target="_blank" rel="noopener">{e(p.get("name"))}</a>'
    else:
        name = e(p.get("name"))
    marke = '<span class="marke-aus">Ausverkauft</span>' if bestellbar and not d["verfuegbar"] else ""
    return (f'<article class="karte{" karte-hell" if hell else ""}{" bestellbar" if bestellbar else ""}"><div class="bild">{bild(p.get("bild"), p.get("bild_beschreibung"))}{marke}</div>'
            f'<div class="unterzeile"><div><div class="name">{name}</div><div class="beschr">{e(p.get("beschreibung"))}</div></div>{preis}</div></article>')

def preishinweis(shop):
    if not (shop and shop["aktiv"]): return ""
    return '<p class="preishinweis">Alle Preise sind Endpreise, keine Umsatzsteuer gemäß § 19 UStG, zzgl. <a href="versand.html">Versand</a> – Abholung kostenlos.</p>'

def kopf(v, titel, text, rechts=""):
    t = f'<p class="einleitung">{e(text)}</p>' if text else ""
    return f'<div class="kopf"><div><div class="vorzeile">{e(v)}</div><h2 class="h2">{e(titel)}</h2>{t}</div>{rechts}</div>'

def baue_start():
    a = lade("allgemein.json"); s = lade("start.json"); k = lade("kollektion.json")
    ez = lade("einzelstuecke.json"); hw = lade("handwerke.json")
    etsy = (a.get("etsy_link") or "").strip()          # leer = kein Etsy: Knöpfe zeigen „Anfragen“ bzw. den eigenen Shop
    shop = shop_einstellungen(a)
    if shop["aktiv"] and not shop["schluessel"]: FEHLT.append("Shop: Bestell-Schlüssel (Web3Forms) fehlt – Bestellungen gehen bis dahin als E-Mail-Entwurf raus")
    mail = (a.get("email") or "").strip(); pruefe(mail, "Allgemein: E-Mail-Adresse")
    anfrage = "anfrage.html"
    insta = (a.get("instagram_name") or "").strip().lstrip("@")

    h = obj(s.get("hero"))
    hero = f'''<section class="wrap" aria-label="Start"><div class="hero">
<svg class="welle" viewBox="0 0 1280 150" preserveAspectRatio="none" aria-hidden="true"><path d="M0 66 C107 20 213 20 320 66 S533 112 640 66 S853 20 960 44 S1173 52 1280 46 V150 H0 Z" fill="#F1E8D8"/></svg>
<div class="raster hero-inhalt"><div class="hero-text"><div class="vorzeile" style="color:#1E3A4C">{e(h["vorzeile"])}</div>
<h1 class="h1"><span class="leicht">{e(h["titel_leicht"])}</span><br><span class="fett">{e(h["titel_fett"])}</span></h1>
<p class="einleitung">{e(h["text"])}</p>
<div class="hero-knoepfe"><a class="knopf knopf-voll" href="#kollektion">{e(h["knopf_1"])}</a><a class="knopf knopf-rand" href="#wunschstueck">{e(h["knopf_2"])}</a></div>
<div class="hero-info"><b>Werkstatt in {e(a.get("ort"))}</b><i></i><span>{e(a.get("versand_hinweis"))}</span></div></div>
<div class="hero-bild"><canvas id="turm" role="img" aria-label="Animierter Turm der Wattmusikanten: Kuh, Schaf, Möwe und Krabbe halten die Balance. Antippen schubst ihn an."></canvas>
<noscript>{bild(h.get("bild"), h.get("bild_beschreibung"))}</noscript></div></div></div></section>'''

    ko = obj(s.get("kollektion")); pr = liste(k.get("produkte"))
    oben = "".join(produktkarte(p, bereich="Kollektion", shop=shop) for p in pr[:2])
    rest = "".join(produktkarte(p, bereich="Kollektion", shop=shop) for p in pr[2:4])
    mehr = "".join(produktkarte(p, bereich="Kollektion", shop=shop) for p in pr[4:])
    hk = obj(ko.get("hinweis_karte"))
    magnet = produkt_daten(D({"name": hk.get("artikelname") or "Wattmusikanten-Magnet", "beschreibung": hk.get("text"), "beschreibung_lang": hk.get("beschreibung_lang"),
                              "preis": hk.get("preis"), "bild": hk.get("bild") or s.get("hero", D()).get("bild"), "bild_beschreibung": hk.get("bild_beschreibung") or s.get("hero", D()).get("bild_beschreibung"),
                              "verfuegbar": hk.get("verfuegbar")}), "Kollektion", "k-magnet")
    hk_preis = (f'<span class="preis" style="color:#FBF8F2">{euro(magnet["preis"])}</span>' if magnet["preis"] is not None else
                (f'<span class="preis" style="color:#FBF8F2">{e(hk["preis"])}</span>' if (hk.get("preis") or "").strip() else ""))
    if shop["aktiv"] and magnet["preis"] is not None:
        hk_knopf = f'<a class="knopf knopf-sand" href="warenkorb.html#artikel/k-magnet" data-artikel="k-magnet">{"In den Warenkorb" if magnet["verfuegbar"] else "Ausverkauft"}</a>'
    elif (hk.get("link") or etsy):
        hk_knopf = f'<a class="knopf knopf-sand" href="{e(hk.get("link") or etsy)}" target="_blank" rel="noopener">Zum Etsy-Shop</a>'
    else:
        hk_knopf = f'<a class="knopf knopf-sand" href="{e(anfrage)}">Anfragen</a>'
    hinweis = (f'<article class="karte hinweis"><div class="herz" aria-hidden="true">{herz(110, "#FBF8F2")}</div><h3 class="h3">{e(hk["titel"])}</h3><p>{e(hk["text"])}</p>'
               f'<div class="figuren">' + "".join(f"<span>{x}</span>" for x in ["Krabbe", "Möwe", "Schaf", "Kuh"]) + "</div>" +
               f'<div class="fuss">{hk_knopf}{hk_preis}</div></article>')
    rechts = (f'<a class="link" href="warenkorb.html">Zum Warenkorb</a>' if shop["aktiv"] else
              (f'<a class="link" href="{e(etsy)}" target="_blank" rel="noopener">Alle im Etsy-Shop</a>' if etsy else f'<a class="link" href="#laeden">In unserem Laden</a>'))
    koll = f'''<section class="wrap abschnitt" id="kollektion">{kopf(ko["vorzeile"], ko["titel"], ko["text"], rechts)}
<div class="raster kollektion">{oben}<div class="kollektion-rest">{rest}</div>{hinweis}<div class="kollektion-mehr">{mehr}</div></div>{preishinweis(shop)}</section>'''

    es = obj(s.get("einzelstuecke"))
    einz = f'''<section class="band" id="persoenlich"><div class="wrap">{kopf(es["vorzeile"], es["titel"], es["text"])}
<div class="raster einzelstuecke">{"".join(produktkarte(p, hell=True, bereich="Persönlich gemacht", shop=shop) for p in liste(ez.get("produkte")))}</div>{preishinweis(shop)}</div></section>'''

    ws = obj(s.get("werkstatt")); zeilen = ""
    for i, x in enumerate(liste(hw.get("handwerke")), 1):
        pruefe(x.get("bild"), f"Werkstatt: Foto für „{x.get('name')}“")
        stich = "".join(f'<span class="pille">{e(t.strip())}</span>' for t in (x.get("stichworte") or "").split(",") if t.strip())
        zeilen += (f'<div class="raster handwerk"><div class="nr">{i:02d}</div><div class="inhalt"><h3 class="h3">{e(x.get("name"))}</h3><p class="text">{e(x.get("text"))}</p>'
                   f'<div class="stichworte">{stich}<a class="link" href="anfrage.html?thema={quote(str(x.get("name") or ""))}">{e(x.get("name"))} anfragen</a></div></div>'
                   f'<div class="bild">{bild(x.get("bild"), x.get("bild_beschreibung"))}</div></div>')
    werk = f'''<section class="wrap abschnitt" id="werkstatt"><div class="raster kopf-geteilt"><div><div class="vorzeile">{e(ws["vorzeile"])}</div><h2 class="h2">{e(ws["titel"])}</h2></div><p class="einleitung">{e(ws["text"])}</p></div>{zeilen}</section>'''

    w = obj(s.get("wunschstueck"))
    schritte = "".join(f'<div class="schritt"><div class="nr">{i:02d}</div><div><b>{e(x["titel"])}</b><span>{e(x["text"])}</span></div></div>' for i, x in enumerate(liste(w.get("schritte")), 1))
    mailzeile = f'<p class="wunsch-mail">{e(mail)}</p>' if mail else ""
    wunsch = f'''<section class="wrap abschnitt" id="wunschstueck"><div class="wunsch">
<div class="figur figur-moewe hoch" aria-hidden="true"><img src="assets/fig/moewe-krabbe.png" alt="" width="387" height="420" loading="lazy"></div>
<div class="raster wunsch-karte"><div class="wunsch-text"><div class="vorzeile">{e(w["vorzeile"])}</div>
<h2 class="h2"><span class="leicht">{e(w["titel_leicht"])}</span><br><span class="fett">{e(w["titel_fett"])}</span></h2>
<div class="schritte">{schritte}</div><a class="knopf knopf-sand" href="{e(anfrage)}">{e(w["knopf"])}</a>{mailzeile}</div>
<div class="wunsch-bild">{bild(w.get("bild"), w.get("bild_beschreibung"))}</div></div></div></section>'''

    l = obj(s.get("laeden")); lad = ""
    for x in liste(l.get("liste")):
        pruefe(x.get("adresse"), f"Läden: Adresse {x.get('ort')}"); pruefe(x.get("oeffnungszeiten"), f"Läden: Öffnungszeiten {x.get('ort')}")
        adr = ", ".join(t for t in [x.get("adresse"), x.get("ort")] if t)
        route = f'<a class="link" href="https://www.google.com/maps/search/?api=1&amp;query={quote(adr)}" target="_blank" rel="noopener">Route planen</a>'
        zeiten = f'<div class="zeiten-titel">Öffnungszeiten</div><div class="zeiten">{e(x["oeffnungszeiten"])}</div>' if (x.get("oeffnungszeiten") or "").strip() else ""
        lad += (f'<article class="karte karte-hell laden"><div><h3 class="h3">{e(x.get("ort"))}</h3><div class="art">{e(x.get("art"))}<br>{e(x.get("adresse"))}</div>{route}</div><div>{zeiten}</div></article>')
    laeden = f'''<section class="band" id="laeden"><div class="wrap"><div class="raster kopf-geteilt"><div><div class="vorzeile">{e(l["vorzeile"])}</div><h2 class="h2">{e(l["titel"])}</h2></div><p class="einleitung">{e(l["text"])}</p></div>
<div class="raster laeden"><div class="karte karte-hell laeden-bild"><div class="bild">{bild(l.get("bild"), l.get("bild_text"))}<span class="marke-klein">{e(l.get("bild_text"))}</span></div></div><div class="laeden-liste">{lad}</div></div></div></section>'''

    u = obj(s.get("ueber_uns"))
    pruefe(u.get("text"), "Über uns: Text"); pruefe(u.get("namen"), "Über uns: Namen"); pruefe(u.get("bild"), "Über uns: Werkstattfoto")
    titel = "<br>".join(e(t) for t in (u.get("titel") or "").split("\n"))
    utext = f'<p class="einleitung">{e(u["text"])}</p>' if (u.get("text") or "").strip() else ""
    unamen = f'<div class="ueber-namen">{e(u["namen"])}</div>' if (u.get("namen") or "").strip() else ""
    ubild = bild(u.get("bild"), u.get("bild_beschreibung")) if bildpfad(u.get("bild")) else f'<div class="platzhalter"><span style="opacity:.5">{herz(110)}</span>Foto folgt: eure Werkstatt</div>'
    ueber = f'''<section class="wrap abschnitt" id="ueber-uns"><div class="raster ueber"><div class="ueber-text"><div class="vorzeile">{e(u["vorzeile"])}</div><h2 class="h2">{titel}</h2>{utext}{unamen}
{f'<a class="knopf knopf-rand" href="https://www.instagram.com/{e(insta)}/" target="_blank" rel="noopener">Folgt uns auf Instagram</a>' if insta else ""}</div>
<div class="ueber-bild"><div class="figur figur-schaf hoch" aria-hidden="true"><img src="assets/fig/schaf.png" alt="" width="420" height="335" loading="lazy"></div><div class="rahmen">{ubild}</div></div></div></section>'''

    return hero + faden() + koll + einz + werk + wunsch + laeden + ueber, a

def seite(titel, inhalt, a, beschreibung=""):
    etsy = (a.get("etsy_link") or "").strip(); mail = (a.get("email") or "").strip()
    insta = (a.get("instagram_name") or "").strip().lstrip("@")
    tel = (a.get("telefon") or "").strip()
    anfrage = "anfrage.html"
    shop = shop_einstellungen(a)
    if shop["aktiv"]:
        shop_knopf = ('<a class="knopf knopf-voll knopf-klein warenkorb-knopf" href="warenkorb.html" aria-label="Warenkorb">'
                      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 6h15l-1.5 9h-12z"/><path d="M6 6 5 3H2"/><circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/></svg>'
                      '<span>Warenkorb</span><span class="zahl" data-warenkorb-zahl hidden>0</span></a>')
        shop_fuss = '<a href="warenkorb.html">Warenkorb</a><a href="versand.html">Versand &amp; Zahlung</a>'
    else:
        shop_knopf = (f'<a class="knopf knopf-voll knopf-klein" href="{e(etsy)}" target="_blank" rel="noopener">Etsy-Shop</a>' if etsy
                      else f'<a class="knopf knopf-voll knopf-klein" href="{e(anfrage)}">Anfragen</a>')
        shop_fuss = f'<a href="{e(etsy)}" target="_blank" rel="noopener">Etsy-Shop</a>' if etsy else '<a href="index.html#laeden">Unser Laden</a>'
    recht_links = '<a href="impressum.html">Impressum</a><a href="datenschutz.html">Datenschutz</a>' + ('<a href="widerruf.html">Widerruf</a><a href="agb.html">AGB</a>' if shop["aktiv"] else "")
    shop_json = json.dumps({"aktiv": shop["aktiv"], "schluessel": shop["schluessel"], "pauschale": shop["pauschale"], "frei_ab": shop["frei_ab"],
                            "lieferzeit": shop["lieferzeit"], "lieferzeit_wunsch": shop["lieferzeit_wunsch"], "abholung": shop["abholung"], "zahlung": shop["zahlung"], "email": mail,
                            "firma": a.get("firmenname") or "mit Herz & Hand KS", "artikel": PRODUKTE}, ensure_ascii=False).replace("</", "<\\/")
    kontakt = ([f'<a href="{e(anfrage)}">Wunschstück anfragen</a>'] + ([f'<span style="user-select:all">{e(mail)}</span>'] if mail else [])
               + ([f'<span style="user-select:all">{e(tel)}</span>'] if tel else [])
               + ([f'<a href="https://www.instagram.com/{e(insta)}/" target="_blank" rel="noopener">Instagram</a>'] if insta else []))
    name = e(a.get("firmenname"))
    return f'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(titel)}</title>
<meta name="description" content="{e(beschreibung)}">
<meta name="theme-color" content="#FBF8F2">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="preload" href="assets/fonts/figtree.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="wrap nav"><a class="marke" href="index.html">{herz(38)}<span><span>mit</span> Herz &amp; Hand KS</span></a>
<nav class="nav-links" aria-label="Hauptmenü"><a href="index.html#kollektion">Wattmusikanten</a><a href="index.html#persoenlich">Persönlich gemacht</a><a href="index.html#wunschstueck">Wunschstück</a><a href="index.html#laeden">Laden</a></nav>
{shop_knopf}</header>
<main>{inhalt}</main>
<footer class="fuss-bereich"><div class="wrap"><div class="raster fuss-spalten">
<div><a class="marke" href="index.html">{herz(42)}<span><span>mit</span> Herz &amp; Hand KS</span></a><p class="text">{e(a.get("footer_text"))}</p></div>
<div class="fuss-liste"><div class="vorzeile">Shop</div><a href="index.html#kollektion">Wattmusikanten</a><a href="index.html#persoenlich">Persönlich gemacht</a>{shop_fuss}</div>
<div class="fuss-liste"><div class="vorzeile">Kontakt</div>{"".join(kontakt)}</div></div>
<div class="fuss-zeile"><span>© {name} · {e(a.get("ort"))}</span><nav aria-label="Rechtliches">{recht_links}</nav></div>
<svg class="wortmarke" viewBox="0 0 1280 118" aria-hidden="true"><text x="-9" y="150" textLength="1298" lengthAdjust="spacingAndGlyphs" font-family="Figtree, Inter, sans-serif" font-weight="800" font-size="196" fill="#1E3A4C" fill-opacity=".07">mit Herz &amp; Hand</text></svg></div>
<div class="figur figur-kuh hoch" aria-hidden="true"><img src="assets/fig/kuh.png" alt="" width="420" height="286" loading="lazy"></div></footer>
<script type="application/json" id="shop-daten">{shop_json}</script>
<script src="assets/main.js" defer></script>
<script src="assets/turm.js" defer></script>
<script src="assets/shop.js" defer></script>
</body>
</html>
'''

def baue_recht(a):
    r = lade("rechtliches.json"); i = obj(r.get("impressum"))
    for k, t in [("name", "Name"), ("strasse", "Straße"), ("plz_ort", "PLZ und Ort"), ("email", "E-Mail")]:
        pruefe(i.get(k), f"Impressum: {t}")
    zeilen = "<br>".join("<br>".join(e(t) for t in str(x).split("\n")) for x in [i.get("name"), i.get("strasse"), i.get("plz_ort")] if x)
    kontakt = "<br>".join(x for x in [f"E-Mail: {e(i['email'])}" if i.get("email") else "", f"Telefon: {e(i['telefon'])}" if i.get("telefon") else ""] if x)
    imp = (f'<section class="wrap recht"><h1 class="h2">Impressum</h1><h2>Angaben gemäß § 5 DDG</h2><p>{zeilen}</p>'
           f'<h2>Kontakt</h2><p>{kontakt}</p>' + (f'<h2>Umsatzsteuer</h2><p>{e(i["zusatz"])}</p>' if i.get("zusatz") else "") + '</section>')
    ds = (r.get("datenschutz") or "").strip(); pruefe(ds, "Datenschutzerklärung")
    return imp, textseite("Datenschutz", ds, "Die Datenschutzerklärung wird gerade erstellt."), r

def textseite(titel, text, leer="Dieser Text wird gerade erstellt."):
    # Absätze durch Leerzeile; eine Zeile, die mit "## " beginnt, wird Zwischenüberschrift
    text = (text or "").strip()
    inner = "".join((f"<h2>{e(p[3:].strip())}</h2>" if p.startswith("## ") else f"<p>{e(p)}</p>") for p in text.split("\n\n")) if text else f"<p>{e(leer)}</p>"
    return f'<section class="wrap recht"><h1 class="h2">{e(titel)}</h1>{inner}</section>'

def versandtext(t, shop):
    """Beträge aus den Shop-Einstellungen in den Text einsetzen, damit nichts doppelt gepflegt wird."""
    frei = f"ab einem Bestellwert von {euro(shop['frei_ab'])} liefern wir versandkostenfrei" if shop["frei_ab"] is not None else "eine Versandkostenfreigrenze gibt es derzeit nicht"
    for k, v in {"{pauschale}": euro(shop["pauschale"]), "{frei_ab}": frei, "{lieferzeit}": shop["lieferzeit"], "{lieferzeit_wunsch}": shop["lieferzeit_wunsch"], "{abholung}": shop["abholung"]}.items():
        t = (t or "").replace(k, v)
    return t

def baue_anfrage(mail):
    return '''<section class="wrap recht anfrage-seite"><div class="vorzeile">Wunschstück</div><h1 class="h2">Erzähl uns deine Idee</h1>
<p class="einleitung">Gravur, Stickerei, Druck oder Plott – schreib uns, was du dir vorstellst. Wir melden uns mit einem Vorschlag und einem Preis.</p>
<form class="anfrageformular" data-anfrage novalidate>
<div class="felder">
<label class="feld"><span>Vorname und Name</span><input name="name" autocomplete="name" required></label>
<label class="feld"><span>E-Mail</span><input name="email" type="email" autocomplete="email" required></label>
<label class="feld"><span>Telefon (optional)</span><input name="telefon" type="tel" autocomplete="tel"></label>
<label class="feld"><span>Worum geht es?</span><input name="thema" placeholder="z. B. Gravur auf Schneidebrett"></label>
<label class="feld breit"><span>Deine Idee</span><textarea name="nachricht" rows="6" required placeholder="Was soll es werden, für wen, bis wann? Maße, Text, Stückzahl – alles, was du schon weißt."></textarea></label>
<input type="checkbox" name="botcheck" class="botcheck" tabindex="-1" autocomplete="off" aria-hidden="true">
</div>
<label class="haken"><input type="checkbox" name="recht" required><span>Ich bin einverstanden, dass meine Angaben zur Beantwortung der Anfrage gespeichert werden (<a href="datenschutz.html" target="_blank">Datenschutz</a>).</span></label>
<p class="fehler" role="alert" hidden></p>
<button class="knopf knopf-voll bestellknopf" type="submit">Anfrage senden</button>
<p class="anfrage-alternativ">Oder direkt per E-Mail an <span style="user-select:all">''' + e(mail) + '''</span></p>
</form></section>'''

def baue_warenkorb(shop):
    if not shop["aktiv"]:
        return textseite("Warenkorb", "Der Online-Shop ist gerade nicht geöffnet. Schreib uns gern eine E-Mail – wir melden uns schnell.")
    return '''<section class="wrap recht warenkorb-seite" id="warenkorb-seite"><h1 class="h2">Warenkorb</h1>
<noscript><p>Für den Warenkorb muss JavaScript eingeschaltet sein. Du kannst uns deine Bestellung auch per E-Mail schicken.</p></noscript>
<div data-warenkorb></div></section>'''


def kopiere_bilder():
    ziel = os.path.join(OUT, "images"); os.makedirs(ziel, exist_ok=True)
    try:
        from PIL import Image, ImageOps
    except ImportError:
        Image = None
    quelle = os.path.join(ROOT, "images")
    if not os.path.isdir(quelle):
        return
    for wurzel, _, dateien in os.walk(quelle):
      for n in dateien:
        q = os.path.join(wurzel, n); rel = os.path.relpath(q, quelle); z = os.path.join(ziel, rel)
        os.makedirs(os.path.dirname(z), exist_ok=True)
        if Image and n.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            try:
                im = ImageOps.exif_transpose(Image.open(q))
                im.thumbnail((1600, 1600))
                if n.lower().endswith((".jpg", ".jpeg")):
                    im.convert("RGB").save(z, quality=82, optimize=True, progressive=True)
                else:
                    im.save(z, optimize=True)
                continue
            except Exception as ex:
                print("Hinweis: Bild nicht verkleinert:", n, ex)
        shutil.copy2(q, z)

def main():
    if os.path.exists(OUT):
        fonts = os.path.join(OUT, "assets", "fonts")
        keep = None
        if os.path.exists(fonts):
            keep = os.path.join(ROOT, ".fonts_tmp"); shutil.rmtree(keep, ignore_errors=True); shutil.copytree(fonts, keep)
        shutil.rmtree(OUT)
    else:
        keep = None
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"))
    if keep:
        shutil.copytree(keep, os.path.join(OUT, "assets", "fonts"), dirs_exist_ok=True); shutil.rmtree(keep)
    kopiere_bilder()
    start, a = baue_start()
    if not str(a.get("firmenname") or "").strip(): a["firmenname"] = "mit Herz & Hand KS"
    imp, ds, r = baue_recht(a)
    shop = shop_einstellungen(a)
    seiten = [("index.html", a.get("firmenname"), start), ("impressum.html", "Impressum · " + a.get("firmenname"), imp), ("datenschutz.html", "Datenschutz · " + a.get("firmenname"), ds),
              ("warenkorb.html", "Warenkorb · " + a.get("firmenname"), baue_warenkorb(shop)),
              ("anfrage.html", "Wunschstück anfragen · " + a.get("firmenname"), baue_anfrage(a.get("email")))]
    if shop["aktiv"]:
        for k, t in [("widerruf", "Widerrufsbelehrung"), ("agb", "AGB"), ("versand_zahlung", "Versand und Zahlung")]:
            pruefe(r.get(k), f"Shop: Text „{t}“")
        seiten += [("widerruf.html", "Widerrufsbelehrung · " + a.get("firmenname"), textseite("Widerrufsbelehrung", r.get("widerruf"))),
                   ("agb.html", "AGB · " + a.get("firmenname"), textseite("Allgemeine Geschäftsbedingungen", r.get("agb"))),
                   ("versand.html", "Versand und Zahlung · " + a.get("firmenname"), textseite("Versand und Zahlung", versandtext(r.get("versand_zahlung"), shop)))]
    beschr = "Gravur, Stickerei, Druck und Plott aus Nordenham – und die Butjenter Wattmusikanten."
    for datei, titel, inhalt in seiten:
        with open(os.path.join(OUT, datei), "w", encoding="utf-8") as f:
            f.write(seite(titel, inhalt, a, beschr))
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    if os.path.exists(os.path.join(ROOT, "CNAME")):
        shutil.copy2(os.path.join(ROOT, "CNAME"), os.path.join(OUT, "CNAME"))
    print("Fertig: _site/ gebaut.")
    if FEHLT:
        print("\nNoch offen (" + str(len(FEHLT)) + "):"); [print("  –", x) for x in FEHLT]
    zf = os.environ.get("GITHUB_STEP_SUMMARY")
    if zf:
        with open(zf, "a", encoding="utf-8") as f:
            f.write("## Website gebaut ✅\n\n" + ("### Noch offen\n" + "\n".join("- " + x for x in FEHLT) if FEHLT else "Alles ausgefüllt.") + "\n")

if __name__ == "__main__":
    main()
