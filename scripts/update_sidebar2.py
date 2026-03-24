#!/usr/bin/env python3
"""Update sidebar with Dublin, Milan, Amsterdam, London, Munich research data (Numbeo March 2026)."""

HTML_FILE = 'C:/Users/mat/Desktop/nieruchomosci-monitor/templates/index.html'

NEW_SIDEBAR = '''  <aside class="sidebar" id="sidebar">
    <div class="guide-title">&#128202; Gdzie inwestować? <span style="font-size:0.7rem;color:var(--text2);font-weight:400">Numbeo marzec 2026</span></div>

    <div style="font-size:0.75rem;color:var(--text2);margin-bottom:10px;padding:8px;background:rgba(59,130,246,0.08);border-radius:6px;border-left:2px solid var(--blue)">
      Yieldy brutto. Netto o ~3&#8209;5 pp niżej po kosztach zarządzania, wakatu i podatków.
    </div>

    <div class="city-card" style="border-color:#16a34a">
      <div class="city-card-header">
        <span class="city-name">&#127466;&#127480; Alicante / Costa Blanca</span>
        <span class="stars">&#9733;&#9733;&#9733;&#9733;&#189;</span>
      </div>
      <div class="city-stat-row">3 402 EUR/m&#178; &middot; yield <strong style="color:var(--green)">8,7%</strong> poza centrum</div>
      <div class="city-note">Najwyższy yield w zestawieniu. Silny popyt turystyczny (Brytyjczycy, Skandynawowie). Bezpośrednie loty z PL. ITP 10%, IRNR 19%. Airbnb: licencja VUT wymagana, ale dostępna.</div>
    </div>

    <div class="city-card" style="border-color:#16a34a">
      <div class="city-card-header">
        <span class="city-name">&#127470;&#127466; Dublin</span>
        <span class="stars">&#9733;&#9733;&#9733;&#9733;</span>
      </div>
      <div class="city-stat-row">7 034 EUR/m&#178; &middot; yield <strong style="color:var(--green)">6,5&ndash;7,3%</strong> (centr./poza)</div>
      <div class="city-note">Anglojęzyczna stolica UE z hub tech (Google, Meta, Apple) = stabilny popyt. Wysoki podatek dochodowy (20&#8209;40% + USC), netto ~4%. RPZ cap: +2%/rok czynszu. Opłata wejścia: stamp duty 1%. Najlepszy gross yield z ośmiu badanych miast.</div>
    </div>

    <div class="city-card" style="border-color:#16a34a">
      <div class="city-card-header">
        <span class="city-name">&#127466;&#127480; Malaga</span>
        <span class="stars">&#9733;&#9733;&#9733;&#9733;</span>
      </div>
      <div class="city-stat-row">4 422 EUR/m&#178; &middot; yield <strong style="color:var(--green)">7,1%</strong> poza centrum</div>
      <div class="city-note">Najszybciej rosnące miasto Hiszpanii &mdash; hub IT i nomadów cyfrowych. Silna aprecjacja kapitału. ITP <strong>7%</strong> (Andaluzja = najtaniej w ES). Centrum: nowe licencje STR ograniczone.</div>
    </div>

    <div class="city-card">
      <div class="city-card-header">
        <span class="city-name">&#127466;&#127480; Valencia</span>
        <span class="stars">&#9733;&#9733;&#9733;&#9733;</span>
      </div>
      <div class="city-stat-row">4 853 EUR/m&#178; &middot; yield <strong style="color:var(--yellow)">6,2%</strong> poza centrum</div>
      <div class="city-note"><strong style="color:var(--red)">&#9888; POWÓDŹ DANA X 2024:</strong> Gminy południa (Paiporta, Torrent, Aldaia) zniszczone. Sprawdź mapę SNCZI przed zakupem! Centrum miasta &mdash; OK. STR: nowe licencje wstrzymane w wielu dzielnicach.</div>
    </div>

    <div class="city-card">
      <div class="city-card-header">
        <span class="city-name">&#127477;&#127481; Porto</span>
        <span class="stars">&#9733;&#9733;&#9733;&#9733;</span>
      </div>
      <div class="city-stat-row">4 460 EUR/m&#178; &middot; yield <strong style="color:var(--yellow)">5,3%</strong> centrum</div>
      <div class="city-note">Stabilny wzrost, ograniczona podaż centrum. Tańszy niż Lizbona o ~30%. STR: nowe licencje AL zamrożone w obszarach historycznych. Podatek od najmu 25% (nierezydent). Golden Visa: &#10007; nieruchomości usunięte 2024.</div>
    </div>

    <div class="city-card">
      <div class="city-card-header">
        <span class="city-name">&#127470;&#127481; Milan (poza centrum)</span>
        <span class="stars">&#9733;&#9733;&#9733;</span>
      </div>
      <div class="city-stat-row">4 436 EUR/m&#178; &middot; yield <strong style="color:var(--yellow)">5,0%</strong> poza centrum</div>
      <div class="city-note">Centrum absurdalnie drogie (9 343 EUR/m², yield 3,6%) &mdash; tylko dzielnice jak Niguarda, Affori, Lambrate mają sens. Cedolare secca 21% (ryczałt). <strong style="color:var(--red)">&#9888; Eksmisje 3&ndash;5 lat</strong> &mdash; tylko z property managerem na miejscu.</div>
    </div>

    <div class="city-card">
      <div class="city-card-header">
        <span class="city-name">&#127475;&#127473; Amsterdam</span>
        <span class="stars">&#9733;&#9733;&#9733;</span>
      </div>
      <div class="city-stat-row">6 316&ndash;9 284 EUR/m&#178; &middot; yield <strong style="color:var(--yellow)">4,9&ndash;5,4%</strong></div>
      <div class="city-note"><strong style="color:var(--red)">&#9888; USTAWA 2024:</strong> Wet betaalbare huur &mdash; 90% nowego zasobu prywatnego objęte limitem czynszu ~1 157 EUR/mies. Airbnb: ban dla nierezydentów. Transfer tax <strong>10,4%</strong>. Box 3: podatek majątkowy ~36% od fikcyjnej stopy, nie od realnego czynszu.</div>
    </div>

    <div class="city-card">
      <div class="city-card-header">
        <span class="city-name">&#127463;&#127468; Sofia</span>
        <span class="stars">&#9733;&#9733;&#9733;&#189;</span>
      </div>
      <div class="city-stat-row">3 642 EUR/m&#178; &middot; yield <strong style="color:var(--yellow)">4,4%</strong> centrum</div>
      <div class="city-note">Najtańsza stolica EU z EUR od 2024/2025 &rarr; zero ryzyka walutowego. <strong>10% flat tax</strong> od najmu (najkorzystniej w UE). Hub IT wschód Europy. Brak Golden Visa. Mała płynność rynku.</div>
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
      <div class="city-note">Rosnąca klasa średnia, hub IT. Yield realnie 4,1% (nie 6&#8209;8% jak często podawano). Kredyty lokalne po 7,14%! <strong>10% flat tax</strong> od najmu. Waluta: LEU (nie EUR) &mdash; ryzyko kursowe.</div>
    </div>

    <div class="city-card">
      <div class="city-card-header">
        <span class="city-name">&#127468;&#127479; Ateny</span>
        <span class="stars">&#9733;&#9733;&#9733;</span>
      </div>
      <div class="city-stat-row">3 551 EUR/m&#178; &middot; yield <strong style="color:var(--text2)">3,8%</strong> centrum</div>
      <div class="city-note"><strong>Golden Visa aktywne:</strong> 800k EUR (Ateny/wyspy), 400k EUR (reszta GR), 250k EUR (adaptacja budynku). Yield 3,8% słaby &mdash; sens tylko dla Golden Visa lub zakładu na aprecjację. Transfer tax zaledwie 3%.</div>
    </div>

    <div style="border-top:1px solid var(--border);margin:12px 0 10px;padding-top:10px">
      <div class="guide-title" style="margin-bottom:8px">&#9940; Unikać</div>
    </div>

    <div class="city-card avoid">
      <div class="city-card-header">
        <span class="city-name">&#127473;&#127481; Wilno</span>
        <span class="stars">&#9733;&#9733; PUŁAPKA</span>
      </div>
      <div class="city-stat-row">5 244 EUR/m&#178; &middot; yield <strong>3,0%</strong> &middot; P/R = 33&times;</div>
      <div class="city-note">Droższe niż Walencja czy Porto, yield tylko 3%. Najgorzej wyceniony rynek w zestawieniu. Omijaj.</div>
    </div>

    <div class="city-card avoid">
      <div class="city-card-header">
        <span class="city-name">&#127465;&#127466; Berlin / Munich</span>
        <span class="stars">&#9733;&#9733; OMIJAJ</span>
      </div>
      <div class="city-stat-row">Berlin: 4&#8209;7k EUR/m² ~2&#8209;3% &middot; Munich: 8&#8209;11k EUR/m² ~3%</div>
      <div class="city-note">Mietspiegel (kontrola czynszów) &rarr; yield nie do poprawienia. Niemcy: najsilniejsza ochrona lokatorów w UE. Za cenę jednego mieszkania w Monachium kupujesz 3 w Alicante z 3&times; wyższym yieldiem.</div>
    </div>

    <div class="city-card avoid">
      <div class="city-card-header">
        <span class="city-name">&#127468;&#127463; Londyn</span>
        <span class="stars">&#9733;&#9733; DROGI/RYZYKO</span>
      </div>
      <div class="city-stat-row">9&#8209;17k EUR/m&#178; &middot; yield 3,2&#8209;4,6% &middot; non-EU</div>
      <div class="city-note">Najdroższe miasto w zestawieniu. Stamp duty: standardowe + 5% surcharge za dodatkową + 2% dla nierezydenta = 7&#8209;17% kosztów zakupu. Podatek dochodowy 20&#8209;45%. Post-Brexit brak prawa pobytu. Ryzyko walutowe GBP/PLN.</div>
    </div>

    <div class="city-card avoid">
      <div class="city-card-header">
        <span class="city-name">&#127479;&#127480; Belgrad (non-EU)</span>
        <span class="stars">&#9733;&#9733; RYZYKO</span>
      </div>
      <div class="city-stat-row">~4 300 EUR/m&#178; &middot; yield 3,9% &middot; ryzyko walutowe</div>
      <div class="city-note">Yield 3,9% nie kompensuje ryzyka non-EU. Dinar serbski, słabsza egzekucja prawa. Serbia w kandydaturze do EU od 2012 &mdash; wejście niepewne.</div>
    </div>

    <div style="border-top:1px solid var(--border);margin:12px 0 10px;padding-top:10px">
      <div class="guide-title" style="margin-bottom:8px">&#128130; Golden Visa 2025</div>
    </div>
    <div style="font-size:0.78rem;color:var(--text2);line-height:1.8">
      <div>&#127468;&#127479; <strong>Grecja</strong> &mdash; 800k/400k/250k EUR &#10003;</div>
      <div>&#127473;&#127483; <strong>Łotwa</strong> &mdash; 250k/500k EUR &#10003;</div>
      <div>&#127477;&#127481; <strong>Portugalia</strong> &mdash; &#10007; nieruchomości usunięte 2024</div>
      <div>&#127466;&#127480; <strong>Hiszpania</strong> &mdash; &#10007; zlikwidowane 3 IV 2025</div>
      <div style="font-size:0.72rem;margin-top:6px;opacity:0.7">Polak (obywatel EU) nie potrzebuje Golden Visa do zamieszkania w żadnym kraju EU.</div>
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
print(f'Total file: {len(result)} chars.')
