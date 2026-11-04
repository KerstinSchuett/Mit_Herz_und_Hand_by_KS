/* Warenkorb und Bestellung – läuft komplett im Browser.
   Artikel und Einstellungen kommen aus dem eingebetteten JSON (#shop-daten), der Warenkorb liegt im localStorage.
   Die Bestellung geht als E-Mail über Web3Forms an die Adresse hinter dem Bestell-Schlüssel. */
(() => {
  const el = document.getElementById('shop-daten'); if (!el) return;
  let DATEN; try { DATEN = JSON.parse(el.textContent); } catch (e) { return; }
  // ---------- Anfrageformular (unabhängig vom Shop) ----------
  const anfrage = document.querySelector('[data-anfrage]');
  if (anfrage) {
    const thema = new URLSearchParams(location.search).get('thema'); if (thema && anfrage.thema) anfrage.thema.value = thema;
    anfrage.querySelectorAll('.feld input, .feld textarea').forEach(i => i.addEventListener('input', () => { i.classList.remove('falsch'); anfrage.querySelector('.fehler').hidden = true; }));
    anfrage.addEventListener('submit', async e => {
      e.preventDefault();
      const fehler = anfrage.querySelector('.fehler'), knopf = anfrage.querySelector('.bestellknopf');
      if (anfrage.botcheck.checked) return;
      if (!anfrage.checkValidity()) { anfrage.querySelectorAll(':invalid').forEach(i => i.classList.add('falsch')); const er = anfrage.querySelector(':invalid'); if (er) er.focus(); fehler.textContent = 'Bitte fülle Name, E-Mail und deine Idee aus und setze das Häkchen.'; fehler.hidden = false; return; }
      const f = Object.fromEntries(new FormData(anfrage).entries()); Object.keys(f).forEach(k => { if (typeof f[k] === 'string') f[k] = f[k].trim(); });
      const text = [`Wunschstück-Anfrage über die Website`, '', `Name: ${f.name}`, `E-Mail: ${f.email}`, f.telefon ? `Telefon: ${f.telefon}` : '', f.thema ? `Thema: ${f.thema}` : '', '', f.nachricht].filter(x => x !== '').join('\n');
      const mailto = `mailto:${encodeURIComponent(DATEN.email)}?subject=${encodeURIComponent('Wunschstück-Anfrage' + (f.thema ? ': ' + f.thema : ''))}&body=${encodeURIComponent(text)}`;
      knopf.disabled = true; knopf.textContent = 'Wird gesendet …';
      let ok = false;
      if (DATEN.schluessel) {
        try {
          const r = await fetch('https://api.web3forms.com/submit', { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
            body: JSON.stringify({ access_key: DATEN.schluessel, subject: 'Wunschstück-Anfrage' + (f.thema ? ': ' + f.thema : '') + ' von ' + f.name, from_name: DATEN.firma + ' – Website', email: f.email, name: f.name, anfrage: text, botcheck: '' }) });
          let antwort = null; try { antwort = await r.json(); } catch (e2) {}
          ok = r.ok && !!(antwort && antwort.success);
        } catch (err) { ok = false; }
      }
      if (ok) {
        anfrage.outerHTML = `<div class="wk-danke"><h2 class="h3">Danke, ${esc(f.name.split(' ')[0])}! Deine Anfrage ist bei uns.</h2><p class="einleitung">Wir melden uns an <b>${esc(f.email)}</b>, meist innerhalb von zwei Werktagen.</p><p><a class="knopf knopf-voll" href="index.html">Zur Startseite</a></p></div>`;
      } else {
        knopf.disabled = false; knopf.textContent = 'Anfrage senden';
        fehler.innerHTML = `Die Anfrage konnte gerade nicht automatisch gesendet werden. Bitte schick sie uns per E-Mail – der Text ist fertig: <a class="link" href="${mailto.replace(/"/g, '&quot;')}">Anfrage per E-Mail senden</a> oder an <span style="user-select:all">${esc(DATEN.email)}</span>`;
        fehler.hidden = false;
      }
    });
  }
  if (!DATEN.aktiv) return;
  const ARTIKEL = Object.fromEntries((DATEN.artikel || []).map(a => [a.id, a]));
  const SPEICHER = 'hhks-warenkorb';
  const euro = c => (c / 100).toFixed(2).replace('.', ',') + ' €';
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  // ---------- Warenkorb ----------
  function lesen() { try { const w = JSON.parse(localStorage.getItem(SPEICHER) || '[]'); return Array.isArray(w) ? w : []; } catch (e) { return []; } }
  function schreiben(w) { try { localStorage.setItem(SPEICHER, JSON.stringify(w)); } catch (e) {} zaehler(); }
  function zaehler() {
    const n = lesen().reduce((s, p) => s + (p.menge || 0), 0);
    document.querySelectorAll('[data-warenkorb-zahl]').forEach(z => { z.textContent = n; z.hidden = n === 0; });
  }
  function hinzufuegen(id, menge, wunschtext) {
    const w = lesen(); const gleich = w.find(p => p.id === id && (p.wunschtext || '') === (wunschtext || ''));
    if (gleich) gleich.menge = Math.min(99, gleich.menge + menge); else w.push({ id, menge, wunschtext: wunschtext || '' });
    schreiben(w);
  }
  function versandkosten(w, abholung) {
    if (abholung) return 0;
    const summe = w.reduce((s, p) => s + (ARTIKEL[p.id]?.preis || 0) * p.menge, 0);
    if (DATEN.frei_ab != null && summe >= DATEN.frei_ab) return 0;
    return DATEN.pauschale || 0;
  }
  zaehler();

  // ---------- Artikel-Fenster ----------
  let dialog = null;
  function artikelFenster(id) {
    const a = ARTIKEL[id]; if (!a || a.preis == null) return;
    if (!dialog) {
      dialog = document.createElement('dialog'); dialog.className = 'artikel-fenster'; document.body.appendChild(dialog);
      dialog.addEventListener('click', e => { if (e.target === dialog) dialog.close(); });
    }
    const bild = a.bild ? `<img src="${esc(a.bild)}" alt="${esc(a.alt)}">` : '<div class="platzhalter">Foto folgt</div>';
    dialog.innerHTML = `<form method="dialog" class="artikel-inhalt"><button class="schliessen" value="zu" formnovalidate aria-label="Schließen">×</button>
<div class="artikel-bild">${bild}</div>
<div class="artikel-text"><div class="vorzeile">${esc(a.bereich)}</div><h2 class="h3">${esc(a.name)}</h2>
<p class="text">${esc(a.text || a.beschreibung)}</p>
<div class="artikel-preis">${euro(a.preis)}<small>Keine Umsatzsteuer gemäß § 19 UStG · zzgl. <a href="versand.html">Versand</a></small></div>
${a.wunschtext ? `<label class="feld"><span>Wunschtext${a.wunschtext_hinweis ? ' <em>(' + esc(a.wunschtext_hinweis) + ')</em>' : ''}</span><input name="wunschtext" maxlength="120" autocomplete="off" required></label>` : ''}
${a.verfuegbar ? `<div class="artikel-aktion"><label class="menge"><span>Menge</span><input name="menge" type="number" min="1" max="99" value="1"></label><button class="knopf knopf-voll" value="kaufen">In den Warenkorb</button></div>`
                : '<p class="marke-aus-text">Gerade ausverkauft – schreib uns, wenn du Bescheid bekommen möchtest.</p>'}
<p class="artikel-hinweis">Lieferzeit: ${esc(a.wunschtext ? DATEN.lieferzeit_wunsch : DATEN.lieferzeit)}. ${esc(DATEN.abholung)} ist kostenlos.</p></div></form>`;
    const form = dialog.querySelector('form');
    form.addEventListener('submit', e => {
      if (e.submitter && e.submitter.value === 'kaufen') {
        const menge = Math.max(1, Math.min(99, parseInt(form.menge.value, 10) || 1));
        const wt = form.wunschtext ? form.wunschtext.value.trim() : '';
        if (a.wunschtext && !wt) { e.preventDefault(); form.wunschtext.focus(); return; }
        hinzufuegen(a.id, menge, wt);
        hinweis(`„${a.name}“ liegt im Warenkorb.`);
        if (typeof zeichnen === 'function' && document.querySelector('[data-warenkorb]')) zeichnen();
      }
    });
    dialog.showModal();
  }
  function hinweis(text) {
    let t = document.querySelector('.shop-hinweis');
    if (!t) { t = document.createElement('div'); t.className = 'shop-hinweis'; t.setAttribute('role', 'status'); document.body.appendChild(t); }
    t.innerHTML = `<span>${esc(text)}</span><a class="link" href="warenkorb.html">Zum Warenkorb</a>`;
    t.classList.add('da'); clearTimeout(t._t); t._t = setTimeout(() => t.classList.remove('da'), 5000);
  }
  document.addEventListener('click', e => {
    const a = e.target.closest('[data-artikel]'); if (!a) return;
    e.preventDefault(); artikelFenster(a.dataset.artikel);
  });
  const hashArtikel = () => { const m = location.hash.match(/^#artikel\/([\w-]+)/); if (m && ARTIKEL[m[1]]) artikelFenster(m[1]); };
  window.addEventListener('hashchange', hashArtikel);

  // ---------- Warenkorbseite ----------
  const wurzel = document.querySelector('[data-warenkorb]');
  if (!wurzel) { hashArtikel(); return; }
  let abholung = false, gesendet = null;
  function zeichnen() {
    if (gesendet) return;
    const w = lesen().filter(p => ARTIKEL[p.id] && ARTIKEL[p.id].preis != null);
    if (!w.length) {
      wurzel.innerHTML = `<p class="einleitung">Dein Warenkorb ist noch leer.</p><p><a class="knopf knopf-voll" href="index.html#kollektion">Zur Kollektion</a></p>`;
      return;
    }
    const zeilen = w.map((p, i) => { const a = ARTIKEL[p.id]; return `<div class="wk-zeile">
<div class="wk-bild">${a.bild ? `<img src="${esc(a.bild)}" alt="${esc(a.alt)}">` : ''}</div>
<div class="wk-name"><b>${esc(a.name)}</b>${p.wunschtext ? `<span>Wunschtext: ${esc(p.wunschtext)}</span>` : ''}<span>${euro(a.preis)} je Stück</span>
${a.verfuegbar ? '' : '<span class="marke-aus-text">Gerade ausverkauft – bitte entfernen</span>'}</div>
<div class="wk-menge"><button type="button" data-menge="${i}" data-d="-1" aria-label="Weniger">−</button><span>${p.menge}</span><button type="button" data-menge="${i}" data-d="1" aria-label="Mehr">+</button></div>
<div class="wk-summe">${euro(a.preis * p.menge)}</div>
<button type="button" class="wk-weg" data-weg="${i}" aria-label="Entfernen">×</button></div>`; }).join('');
    const summe = w.reduce((s, p) => s + ARTIKEL[p.id].preis * p.menge, 0);
    const versand = versandkosten(w, abholung);
    const freiText = DATEN.frei_ab != null ? ` (ab ${euro(DATEN.frei_ab)} kostenlos)` : '';
    const lieferzeit = w.some(p => ARTIKEL[p.id].wunschtext) ? DATEN.lieferzeit_wunsch : DATEN.lieferzeit;
    wurzel.innerHTML = `<div class="wk-liste">${zeilen}</div>
<div class="wk-versand"><label><input type="radio" name="lieferung" value="versand" ${abholung ? '' : 'checked'}> Versand innerhalb Deutschlands – ${euro(DATEN.pauschale)}${freiText}</label>
<label><input type="radio" name="lieferung" value="abholung" ${abholung ? 'checked' : ''}> ${esc(DATEN.abholung)} – kostenlos</label></div>
<div class="wk-gesamt"><div><span>Zwischensumme</span><b>${euro(summe)}</b></div><div><span>${abholung ? 'Abholung' : 'Versand'}</span><b>${euro(versand)}</b></div><div class="gesamt"><span>Gesamt</span><b>${euro(summe + versand)}</b></div>
<small>Keine Umsatzsteuer gemäß § 19 UStG. Lieferzeit: ${esc(lieferzeit)}.</small></div>
<h2 class="h3" id="bestellen">Bestellen</h2>
<p class="text">${esc(DATEN.zahlung)}</p>
<form class="bestellformular" novalidate>
<div class="felder">
<label class="feld"><span>Vorname und Name</span><input name="name" autocomplete="name" required></label>
<label class="feld"><span>E-Mail</span><input name="email" type="email" autocomplete="email" required></label>
<label class="feld"><span>Telefon (optional)</span><input name="telefon" type="tel" autocomplete="tel"></label>
<label class="feld breit"><span>Straße und Hausnummer</span><input name="strasse" autocomplete="street-address" required></label>
<label class="feld"><span>PLZ</span><input name="plz" inputmode="numeric" autocomplete="postal-code" pattern="\\d{5}" required></label>
<label class="feld"><span>Ort</span><input name="ort" autocomplete="address-level2" required></label>
<label class="feld breit"><span>Anmerkung (optional)</span><textarea name="anmerkung" rows="3"></textarea></label>
<input type="checkbox" name="botcheck" class="botcheck" tabindex="-1" autocomplete="off" aria-hidden="true">
</div>
<label class="haken"><input type="checkbox" name="recht" required><span>Ich habe die <a href="widerruf.html" target="_blank">Widerrufsbelehrung</a>, die <a href="agb.html" target="_blank">AGB</a> und die <a href="datenschutz.html" target="_blank">Datenschutzerklärung</a> gelesen.</span></label>
${w.some(p => p.wunschtext) ? '<label class="haken"><input type="checkbox" name="personal" required><span>Mir ist bekannt, dass Artikel mit Wunschtext nach meinen Angaben gefertigt werden und deshalb vom Widerruf ausgeschlossen sind.</span></label>' : ''}
<p class="fehler" role="alert" hidden></p>
<div class="wk-zusammenfassung"><b>Deine Bestellung</b>${w.map(p => `<span>${p.menge} × ${esc(ARTIKEL[p.id].name)}${p.wunschtext ? ' („' + esc(p.wunschtext) + '“)' : ''} – ${euro(ARTIKEL[p.id].preis * p.menge)}</span>`).join('')}
<span>${abholung ? 'Abholung – kostenlos' : 'Versand innerhalb Deutschlands – ' + euro(versand)}</span><span class="gesamt">Gesamt ${euro(summe + versand)}</span>
<span>Endpreise, keine Umsatzsteuer gemäß § 19 UStG · Zahlung per Vorkasse (Überweisung oder PayPal) nach Rechnung · Lieferzeit ${esc(lieferzeit)}${abholung ? ', Abholung nach Benachrichtigung' : ''}</span></div>
<button class="knopf knopf-voll bestellknopf" type="submit">Zahlungspflichtig bestellen</button>
</form>`;
    wurzel.querySelectorAll('[data-menge]').forEach(b => b.addEventListener('click', () => { const w2 = lesen(); const i = +b.dataset.menge; w2[i].menge = Math.max(1, Math.min(99, w2[i].menge + +b.dataset.d)); schreiben(w2); zeichnen(); }));
    wurzel.querySelectorAll('[data-weg]').forEach(b => b.addEventListener('click', () => { const w2 = lesen(); w2.splice(+b.dataset.weg, 1); schreiben(w2); zeichnen(); }));
    wurzel.querySelectorAll('input[name=lieferung]').forEach(r => r.addEventListener('change', () => { abholung = r.value === 'abholung'; zeichnen(); }));
    wurzel.querySelector('form').addEventListener('submit', absenden);
    wurzel.querySelectorAll('.feld input, .feld textarea').forEach(i => i.addEventListener('input', () => { i.classList.remove('falsch'); const f = wurzel.querySelector('.fehler'); if (f) f.hidden = true; }));
  }

  function bestellnummer() {
    const d = new Date(), z = n => String(n).padStart(2, '0');
    return `HH-${String(d.getFullYear()).slice(2)}${z(d.getMonth() + 1)}${z(d.getDate())}-${Math.floor(1000 + Math.random() * 9000)}`;
  }
  function bestelltext(nr, f, w, versand, summe) {
    const z = [];
    z.push(`Bestellung ${nr} – ${DATEN.firma}`, '');
    w.forEach(p => z.push(`${p.menge} × ${ARTIKEL[p.id].name}${p.wunschtext ? ` (Wunschtext: ${p.wunschtext})` : ''} – ${euro(ARTIKEL[p.id].preis * p.menge)}`));
    z.push(abholung ? 'Abholung – 0,00 €' : `Versand – ${euro(versand)}`, `GESAMT: ${euro(summe + versand)}`, '');
    z.push(`Name: ${f.name}`, `E-Mail: ${f.email}`, f.telefon ? `Telefon: ${f.telefon}` : '', `Adresse: ${f.strasse}, ${f.plz} ${f.ort}`, `Lieferung: ${abholung ? 'Abholung' : 'Versand'}`, f.anmerkung ? `Anmerkung: ${f.anmerkung}` : '');
    z.push('', `Lieferzeit: ${w.some(p => ARTIKEL[p.id].wunschtext) ? DATEN.lieferzeit_wunsch : DATEN.lieferzeit}`, 'Zahlung: Vorkasse (Überweisung oder PayPal) nach Rechnung. Keine Umsatzsteuer gemäß § 19 UStG.');
    return z.filter(x => x !== '').join('\n');
  }
  async function absenden(e) {
    e.preventDefault();
    const form = e.target, fehler = form.querySelector('.fehler'), knopf = form.querySelector('.bestellknopf');
    fehler.hidden = true;
    if (form.botcheck.checked) return;
    const w = lesen().filter(p => ARTIKEL[p.id] && ARTIKEL[p.id].preis != null);
    if (w.some(p => !ARTIKEL[p.id].verfuegbar)) { fehler.textContent = 'Ein Artikel im Warenkorb ist gerade ausverkauft. Bitte entferne ihn.'; fehler.hidden = false; return; }
    if (!form.checkValidity()) {
      form.querySelectorAll(':invalid').forEach(i => i.classList.add('falsch'));
      const erstes = form.querySelector(':invalid'); if (erstes) erstes.focus();
      fehler.textContent = 'Bitte fülle alle Pflichtfelder aus und bestätige die Häkchen.'; fehler.hidden = false; return;
    }
    const f = Object.fromEntries(new FormData(form).entries());
    Object.keys(f).forEach(k => { if (typeof f[k] === 'string') f[k] = f[k].trim(); });
    const nr = bestellnummer(), summe = w.reduce((s, p) => s + ARTIKEL[p.id].preis * p.menge, 0), versand = versandkosten(w, abholung);
    const text = bestelltext(nr, f, w, versand, summe);
    knopf.disabled = true; knopf.textContent = 'Wird gesendet …';
    let ok = false;
    if (DATEN.schluessel) {
      try {
        const r = await fetch('https://api.web3forms.com/submit', { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body: JSON.stringify({ access_key: DATEN.schluessel, subject: `Bestellung ${nr} von ${f.name}`, from_name: DATEN.firma + ' – Website', email: f.email, name: f.name,
            bestellung: text, bestellnummer: nr, gesamt: euro(summe + versand), botcheck: '' }) });
        let antwort = null; try { antwort = await r.json(); } catch (e2) {}
        ok = r.ok && !!(antwort && antwort.success);
      } catch (err) { ok = false; }
    }
    const mailto = `mailto:${encodeURIComponent(DATEN.email)}?subject=${encodeURIComponent('Bestellung ' + nr)}&body=${encodeURIComponent(text)}`;
    const kopie = `mailto:${encodeURIComponent(f.email)}?subject=${encodeURIComponent('Meine Bestellung ' + nr + ' bei ' + DATEN.firma)}&body=${encodeURIComponent(text + '\n\nWiderrufsbelehrung: ' + location.origin + location.pathname.replace(/[^/]*$/, '') + 'widerruf.html\nAGB: ' + location.origin + location.pathname.replace(/[^/]*$/, '') + 'agb.html')}`;
    if (ok) {
      gesendet = nr; schreiben([]);
      wurzel.innerHTML = `<div class="wk-danke"><h2 class="h3">Danke, ${esc(f.name.split(' ')[0])}! Deine Bestellung ist bei uns.</h2>
<p class="einleitung">Bestellnummer <b>${nr}</b>. Wir prüfen alles und schicken dir die Rechnung mit Bankverbindung und PayPal-Link an <b>${esc(f.email)}</b>. Sobald die Zahlung da ist, geht es los – ${esc(DATEN.lieferzeit)}.</p>
<pre class="wk-kopie">${esc(text)}</pre>
<p><a class="knopf knopf-rand" href="${kopie.replace(/"/g, '&quot;')}">Kopie an ${esc(f.email)} mailen</a> <a class="knopf knopf-voll" href="index.html">Zur Startseite</a></p></div>`;
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      knopf.disabled = false; knopf.textContent = 'Zahlungspflichtig bestellen';
      fehler.innerHTML = `Die Bestellung konnte gerade nicht automatisch übermittelt werden. Bitte schick sie uns direkt per E-Mail – der Text ist schon fertig: <a class="link" href="${mailto.replace(/"/g, '&quot;')}">Bestellung ${esc(nr)} per E-Mail senden</a>`;
      fehler.hidden = false;
    }
  }
  zeichnen(); hashArtikel();
})();
