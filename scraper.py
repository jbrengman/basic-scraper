import requests
from bs4 import BeautifulSoup
import sys
import json


def get_search_results(
        query=None, minAsk=None, maxAsk=None, bedrooms=None):
    search_params = {
        key: val for key, val in locals().items() if val is not None}
    if not search_params:
        raise ValueError("No valid keywords")

    base = 'http://seattle.craigslist.org/search/apa'
    resp = requests.get(base, params=search_params, timeout=3)
    resp.raise_for_status()
    write_results(resp.content)
    return resp.content, resp.encoding


def write_results(content):
    with open('apartments.html', 'w') as outfile:
        outfile.write(content)


def read_search_results():
    content = open('apartments.html', 'rb')
    encoding = 'utf-8'  # Not sure I should assume this
    return content, encoding


def parse_source(html, encoding='utf-8'):
    parsed = BeautifulSoup(html, from_encoding=encoding)
    return parsed


def extract_listings(parsed):
    location_attrs = {'data-latitude': True, 'data-longitude': True}
    listings = parsed.find_all('p', class_='row', attrs=location_attrs)
    extracted = []
    for listing in listings:
        location = {key: listing.attrs.get(key, '') for key in location_attrs}
        link = listing.find('span', class_='pl').find('a')
        price_span = listing.find('span', class_='price')
        this_listing = {
            'location': location,
            'link': link.attrs['href'],
            'description': link.string.strip(),
            'price': price_span.string.strip(),
            'size': price_span.next_sibling.strip(' \n-/')
        }
        extracted.append(this_listing)
    return extracted


def add_address(listing):
    url = 'http://maps.googleapis.com/maps/api/geocode/json'
    location = listing['location']
    latlng = '{data-latitude},{data-longitude}'.format(**location)
    parameters = {'latlng': latlng, 'sensor': 'false'}
    response = requests.get(url, params=parameters)
    response.raise_for_status()
    data = json.loads(response.text)
    listing['address'] = data['results'][0]['formatted_address']
    return listing


if __name__ == '__main__':
    import pprint
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        html, encoding = read_search_results()
    else:
        html, encoding = get_search_results(
            minAsk=500, maxAsk=1000, bedrooms=2
        )
    doc = parse_source(html, encoding)
    listings = extract_listings(doc)

    # Don't want to get all the addresses every time I run test
    # for listing in extract_listings(doc):
    #     listing = add_address(listing)
    #     pprint.pprint(listing)

    listing = add_address(listings[0])
    pprint.pprint(listing)
