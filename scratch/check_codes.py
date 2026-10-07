import urllib.request
import re

url = 'https://cricsheet.org/downloads/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8')

blocks = re.findall(r'<td class="name"[^>]*>\s*(.*?)\s*</td>.*?href="/downloads/([a-zA-Z0-9_]+)_csv2\.zip"', html, re.DOTALL)
for name, code in blocks:
    name_clean = ' '.join(name.split())
    print(f"{code:<20} | {name_clean}")
