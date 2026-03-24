import json

cfg_path = 'C:/Users/mat/Desktop/nieruchomosci-monitor/config.json'
with open(cfg_path, encoding='utf-8') as f:
    cfg = json.load(f)

cfg['markets']['alicante'] = {
    'enabled': True,
    'label': 'Alicante ES',
    'max_price_m2': 3500,
    'currency': 'EUR',
    'sources': ['idealista_es'],
    'city_filter': ['Alicante', 'Alacant'],
    'type': 'mieszkanie',
    'flag': '',
    'roi_rating': 5,
    'roi_note': 'Najwyzszy yield w Europie Zachodniej: 8,7% poza centrum. 3402 EUR/m2. Silny rynek turystyczny. ITP 10%, IRNR 19%.'
}

cfg['markets']['malaga'] = {
    'enabled': True,
    'label': 'Malaga ES',
    'max_price_m2': 4500,
    'currency': 'EUR',
    'sources': ['idealista_es'],
    'city_filter': ['Malaga'],
    'type': 'mieszkanie',
    'flag': '',
    'roi_rating': 4,
    'roi_note': 'Najszybciej rosnace miasto Hiszpanii. Yield 7,1% poza centrum. Hub IT i nomadow. ITP 7% (Andaluzja).'
}

cfg['markets']['sofia'] = {
    'enabled': True,
    'label': 'Sofia BG',
    'max_price_m2': 3700,
    'currency': 'EUR',
    'sources': [],
    'city_filter': ['Sofia'],
    'type': 'mieszkanie',
    'flag': '',
    'roi_rating': 3,
    'roi_note': 'Najtansza stolica EU z EUR od 2024. Yield 4,4%. 10% flat tax od najmu. Hub IT wschod Europy.'
}

cfg['markets']['athens']['roi_note'] = 'Yield 3,8% centrum - slaby. Golden Visa aktywne: 800k/400k/250k EUR. Transfer tax 3%. Sens dla GV lub aprecjacji.'
cfg['markets']['bucharest']['roi_note'] = 'Yield 4,1% centrum (nie 6-8% jak podawano). Kredyty 7,14%. 10% flat tax. Waluta LEU nie EUR - ryzyko kursowe.'

with open(cfg_path, 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)

print('Markets total:', len(cfg['markets']))
for k, v in cfg['markets'].items():
    print(f"  {k}: {v['label']}")
