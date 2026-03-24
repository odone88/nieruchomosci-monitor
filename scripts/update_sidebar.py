#!/usr/bin/env python3
"""Replace sidebar with updated investment guide data."""
import re

HTML_FILE = 'C:/Users/mat/Desktop/nieruchomosci-monitor/templates/index.html'

NEW_SIDEBAR = '''  <aside class="sidebar" id="sidebar">
    <div class="guide-title">📊 Gdzie inwestować? <span style="font-size:0.7rem;color:var(--text2);font-weight:400">Numbeo marzec 2026</span></div>

    <div style="font-size:0.72rem;color:var(--text2);margin-bottom:10px;padding:8px;background:rgba(59,130,246,0.08);border-radius:6px;border-left:2px solid var(--blue)">
      Yieldy brutto. Netto o ~3-5 pp niżej po kosztach zarządzania, wakatu i podatków.
    </div>

    <div class="city-card" style="border-color:#16a34a">
      <div class="city-card-header">
        <span class="city-name">&#127466;&#127480; Alicante / Costa Blanca</span>
        <span class="stars">&#9733;&#9733;&#9733;&#9733;&#189;</span>
      </div>
      <div class="city-stat-row">3 402 EUR/m&#178; &middot; yield <strong style="color:var(--green)">8,7%</strong> poza centrum</div>
      <div class="city-note">Najwyższy yield w zestawieniu. Silny popyt turystyczny (Bryjczycy, Skandynawowie). Bezpośrednie loty z PL. ITP 10%, IRNR 19%. Airbnb: licencja VUT wymagana, ale dostępna.</div>
    </div>

    <div class="city-card" style="border-color:#16a34a">
      <div class="city-card-header">
        <span class="city-name">&#127466;&#127480; Malaga</span>
        <span class="stars">&#9733;&#9733;&#9733;&#9733;</span>
      </div>
      <div class="city-stat-row">4 422 EUR/m&#178; &middot; yield <strong style="color:var(--green)">7,1%</strong> poza centrum</div>
      <div class="city-note">Najszybciej rosnące miasto Hiszpanii — hub IT i nomadów cyfrowych. Silna aprecjacja kapitału. ITP <strong>7%</strong> (Andaluzja = najtaniej w ES). Centrum: nowe licencje STR ograniczone.</div>
    </div>

    <div class="city-card">
      <div class="city-card-header">
        <span class="city-name">&#127466;&#127480; Valencia</span>
        <span class="stars">&#9733;&#9733;&#9733;&#9733;</span>
      </div>
      <div class="city-stat-row">4 853 EUR/m&#178; &middot; yield <strong style="color:var(--yellow)">6,2%</strong> poza centrum</div>
      <div class="city-note"><strong style="color:var(--red)">&#9888; POWODZ DANA X 2024:</strong> Gminy południa (Paiporta, Torrent, Aldaia) zniszczone. Sprawdź mapę SNCZI przed zakupem! Centrum miasta — OK. STR: nowe licencje wstrzymane w wielu dzielnicach. Golden Visa ES: <strong>zlikwidowane IV 2025</strong>.</div>
    </div>

    <div class="city-card">
      <div class="city-card-header">
        <span class="city-name">&#127477;&#127481; Porto</span>
        <span class="stars">&#9733;&#9733;&#9733;&#9733;</span>
      </div>
      <div class="city-stat-row">4 460 EUR/m&#178; &middot; yield <strong style="color:var(--yellow)">5,3%</strong> centrum</div>
      <div class="city-note">Stabilny wzrost, ograniczona podaż centrum. Tańsze niż Lizbona o ~30%. STR: nowe licencje AL zamrożone w obszarach historycznych. Podatek od najmu 28% (nierezydent). Golden Visa: <strong>scieżka nieruchomości usunięta 2024</strong>.</div>
    </div>

    <div class="city-card">
      <div class="city-card-header">
        <span class="city-name">&#127463;&#127468; Sofia</span>
        <span class="stars">&#9733;&#9733;&#9733;&#189;</span>
      </div>
      <div class="city-stat-row">3 642 EUR/m&#178; &middot; yield <strong style="color:var(--yellow)">4,4%</strong> centrum</div>
      <div class="city-note">Najtańsza stolica EU z EUR od 2024/2025 → zero ryzyka walutowego. <strong>10% flat tax</strong> od najmu (najkorzystniej w UE). Hub IT wschód Europy. Brak Golden Visa. Mała płynność rynku.</div>
    </div>

    <div class="city-card">
      <div class="city-card-header">
        <span class="city-name">&#127473;&#127483; Ryga</span>
        <span class="stars">&#9733;&#9733;&#9733;</span>
      </div>
      <div class="city-stat-row">2 711 EUR/m&#178; &middot; yield <strong style="color:var(--yellow)">4,4%</strong> centrum</div>
      <div class="city-note">Najniższa cena wejścia spośród stolic EU. EUR + NATO. <strong>Golden Visa: 250k EUR</strong> poza Rygą / 500k w Rydze. Ryzyko geopolityczne (bliskość Rosji). Mały rynek, ograniczona płynność.</div>
    </div>

    <div class="city-card">
      <div class="city-card-header">
        <span class="city-name">&#127479;&#127476; Bukareszt</span>
        <span class="stars">&#9733;&#9733;&#9733;</span>
      </div>
      <div class="city-stat-row">~3 800 EUR/m&#178; &middot; yield <strong style="color:var(--text2)">4,1%</strong> centrum</div>
      <div class="city-note">Rosnąca klasa średnia, hub IT. Yield realnie 4,1% (nie 6-8% jak często podawano). Kredyty lokalne po 7,14%! <strong>10% flat tax</strong> od najmu. Waluta: LEU (nie EUR) — ryzyko kursowe.</div>
    </div>

    <div class="city-card">
      <div class="city-card-header">
        <span class="city-name">&#127468;&#127479; Ateny</span>
        <span class="stars">&#9733;&#9733;&#9733;</span>
      </div>
      <div class="city-stat-row">3 551 EUR/m&#178; &middot; yield <strong style="color:var(--text2)">3,8%</strong> centrum</div>
      <div class="city-note"><strong>Golden Visa aktywne:</strong> 800k EUR (Ateny/wyspy), 400k EUR (reszta GR), 250k EUR (adaptacja budynku). Yield 3,8% słaby — sens tylko dla Golden Visa lub zakładu na aprecjację. Transfer tax: zaledwie 3%.</div>
    </div>

    <div style="border-top:1px solid var(--border);margin:12px 0 10px;padding-top:10px">
      <div class="guide-title" style="margin-bottom:8px">&#9940; Unikać</div>
    </div>

    <div class="city-card avoid">
      <div class="city-card-header">
        <span class="city-name">&#127473;&#127481; Wilno</span>
        <span class="stars">&#9733;&#9733; PULAPKA</span>
      </div>
      <div class="city-stat-row">5 244 EUR/m&#178; &middot; yield <strong>3,0%</strong> &middot; P/R = 33&times;</div>
      <div class="city-note">Droższe niż Walencja czy Porto, yield tylko 3%. Najgorzej wyceniony rynek w zestawieniu. Omijaj.</div>
    </div>

    <div class="city-card avoid">
      <div class="city-card-header">
        <span class="city-name">&#127465;&#127466; Berlin</span>
        <span class="stars">&#9733;&#9733; OMIJAJ</span>
      </div>
      <div class="city-stat-row">4 000–7 000 EUR/m&#178; &middot; yield ~2-3%</div>
      <div class="city-note">Kontrola czynszów (Mietspiegel) → yield niemożliwy do poprawienia. Ryzyko dalszych regulacji. Za te pieniądze kup 2 mieszkania w Alicante.</div>
    </div>

    <div class="city-card avoid">
      <div class="city-card-header">
        <span class="city-name">&#127479;&#127480; Belgrad (non-EU)</span>
        <span class="stars">&#9733;&#9733; RYZYKO</span>
      </div>
      <div class="city-stat-row">~4 300 EUR/m&#178; &middot; yield 3,9% &middot; ryzyko walutowe</div>
      <div class="city-note">Yield 3,9% nie kompensuje ryzyka non-EU. Dinar serbski, słabsza egzekucja prawa. Serbia w EU kandydaturze od 2012 — wejście niepewne.</div>
    </div>

    <div style="border-top:1px solid var(--border);margin:12px 0 10px;padding-top:10px">
      <div class="guide-title" style="margin-bottom:8px">&#128130; Golden Visa 2025</div>
    </div>
    <div style="font-size:0.75rem;color:var(--text2);line-height:1.7">
      <div>&#127468;&#127479; <strong>Grecja</strong> — 800k/400k/250k EUR &#10003;</div>
      <div>&#127473;&#127483; <strong>Latwa</strong> — 250k/500k EUR &#10003;</div>
      <div>&#127477;&#127481; <strong>Portugalia</strong> — &#10007; nieruchomości usunięte 2024</div>
      <div>&#127466;&#127480; <strong>Hiszpania</strong> — &#10007; zlikwidowane 3 IV 2025</div>
      <div style="font-size:0.68rem;margin-top:6px;opacity:0.7">Polak (obywatel EU) nie potrzebuje Golden Visa do zamieszkania w żadnym kraju EU.</div>
    </div>
  </aside>'''

with open(HTML_FILE, encoding='utf-8') as f:
    content = f.read()

start = content.index('<aside class="sidebar" id="sidebar">')
end = content.index('</aside>') + len('</aside>')
old = content[start:end]

result = content[:start] + NEW_SIDEBAR + content[end:]

with open(HTML_FILE, 'w', encoding='utf-8') as f:
    f.write(result)

print(f'Done. Replaced {len(old)} chars with {len(NEW_SIDEBAR)} chars.')
