import urllib.request
from bs4 import BeautifulSoup

html = urllib.request.urlopen("https://pasigcity.gov.ph/full-disclosure-portal")


soup = BeautifulSoup(html.read(), "lxml")

ordinances_2025 = soup.find_all(id = 'city-ordinance-accordion-2025')
print(ordinances_2025)