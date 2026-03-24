import json
path = 'C:/Users/mat/Desktop/nieruchomosci-monitor/config.json'
with open(path, encoding='utf-8') as f:
    cfg = json.load(f)
for m in ['alicante', 'malaga', 'valencia']:
    cfg['markets'][m]['sources'] = ['pisos']
    cfg['markets'][m]['flag'] = '\U0001f1ea\U0001f1f8'
with open(path, 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)
for m in ['alicante', 'malaga', 'valencia']:
    print(m, cfg['markets'][m]['sources'])
