import urllib.request
import re

url = 'https://cricsheet.org/register/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8')
links = re.findall(r'href=[\'"]([^\'"]+\.(?:csv|zip))[\'"]', html)
print('CSV / ZIP links in register page:', links)

# Also check for any tables or descriptions in the page
sections = re.findall(r'<h3>(.*?)</h3>|<h4[^>]*>(.*?)</h4>|<a href=[\'"]([^\'"]+)[\'"]>([^<]+)</a>', html)
for s in sections[:30]:
    print(s)
