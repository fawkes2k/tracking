from requests import get
from zeep import Client
from zeep.wsse import UsernameToken
from csv import writer
from sys import argv
from re import match, search
from datetime import datetime

def error_exit(message: str): print(message); exit(-1)
def get_parcel_info_from_polish_post(item_number: str):
    client = Client('https://tt.poczta-polska.pl/Sledzenie/services/Sledzenie?wsdl', wsse=UsernameToken('sledzeniepp', 'PPSA'))
    parcel = client.service.sprawdzPrzesylke(item_number)
    events = parcel.danePrzesylki.zdarzenia
    if events is None: error_exit('Polish Post: Package not found')
    with open(f'{item_number}-PP.csv', 'w') as file:
        csv_writer = writer(file)
        csv_writer.writerow(('Czas', 'Nazwa jednostki', 'Kod zdarzenia', 'Kończące?', 'Nazwa zdarzenia', 'Kod przyczyny', 'Nazwa przyczyny'))
        for event in events.zdarzenie:
            row = (event.czas, event.jednostka.nazwa, event.kod, event.konczace, event.nazwa, event.przyczyna.kod, event.przyczyna.nazwa)
            csv_writer.writerow(row)

def get_parcel_info_from_universal_postal_union(item_number: str):
    content = get(f'https://globaltracktrace.ptc.post/gtt.api/service.svc/rest/ItemTTWithTrans/{item_number}/en')
    if len(content.content) == 0: error_exit('Universal Postal Union: Package not found')
    events = content.json()[0]['Events']
    with open(f'{item_number}-UP.csv', 'w') as file:
        csv_writer = writer(file)
        csv_writer.writerow(('Date & Time', 'Event', 'Location'))
        for event in events:
            ts, = search(r'(\d+)[-+]\d+', event['EventDT']).groups()
            time = datetime.fromtimestamp(int(ts) / 1000.0)
            csv_writer.writerow((time, event['EventNm'], event['EventLocation']))

def check_item_number(item_number: str):
    if not match(r'[A-Z]{2}[0-9]{9}[A-Z]{2}', item_number): error_exit('Wrong item number')
    get_parcel_info_from_universal_postal_union(item_number)
    get_parcel_info_from_polish_post(item_number)

if __name__ == '__main__':
    if len(argv) < 2: error_exit('Usage: track.py [item number]')
    check_item_number(argv[1])
