# -*- coding: utf-8 -*-
"""KubiosCloudDemo.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1dUQCxiLZonO0kuAImTZ09stcipMSJoVt

# Kubios Cloud Demo
26.4.2023, Sakari Lukkarinen\
Hyvinvointi- ja terveysteknologia\
Tieto- ja viestintäteknologia\
Metropolia Ammattikorkeakoulu

## Johdanto

Tämän Notebookin tarkoituksena on demonstroida kuinka voidaan lukea dataa henkilökohtaiselta Kubios Cloud tililtä ja näyttää mittaustulokset. Koodi perustuu KubiosCloud kirjautumisesimerkkiin ja Kubios Cloud API ohjeisiin.

### Ohjeet

1. Kirjoita USERNAME ja PASSWORD kenttiin sama käyttäjätunnus ja salasana kuin mitä olet käyttänyt Kubios HRV sovelluksessa. Jos olet unohtanut salasanasi, voit pyytää uutta salasanaa osoitteesta: https://analysis.kubioscloud.com/v2/portal/index
1. Tämän lisäksi tarvitse CLIENT_ID tunnuksen ja LOGIN_URL, TOKEN_URL ja REDIRECT_URL-osoitteet, jotka löytyvät kurssin työtilan dokumenteista.
1. Kun olet kirjoittanut tarvittavat tiedot Notebookin alkuun, aja Notebook solu solulta.
1. Osa koodeista vaatii toimiakseen, että edelliset koodit on suoritettu onnistuneesti, joten tarkista huolellisesti, että kaikki informaatio, joka on JSON rakenteissa on validia.
1. Lopussa sinulla pitäisi olla käytössä analyysitulokset ja  datatiedostot kirjoitettuna JSON ja CSV tiedostoihin.

### Lisää luettavaa

- [Kubioscloud example for authorization](https://bitbucket.org/kubios/workspace/snippets/4X95xd/kubioscloud-example-for-authorization-code)
- [Kubios Cloud API reference](https://analysis.kubioscloud.com/v1/portal/documentation/apis.html#kubioscloud-api-reference)
  - [Get user information](https://analysis.kubioscloud.com/v2/portal/documentation/api_user.html#get-user-information)
  - [List results](https://analysis.kubioscloud.com/v2/portal/documentation/api_result.html)

## 1. Asetukset

- Käytä Kubios HRV sovelluksessa käyttämääsi käyttäjätunnusta ja salasanaa. 
- Lisää oman sovelluksesi nimi USER_AGENT kenttään.
- Kopioi OMAn työtilasta loput asetukset.
"""

# Käytä Kubios HRV sovelluksessa käyttämääsi käyttäjätunnusta ja salasanaa
USERNAME = "abo.ehea.m.z@hotmail.com"
PASSWORD = "Zeko00963"

# Käytä tässä kentässä teidän sovelluksen nimeä
USER_AGENT = "TestApp 1.0" 

# Kopioi nämä tiedot OMAn työtilan dokumenteista
CLIENT_ID = "74571pdhuc7vvak4tl45uts8u8"
LOGIN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/login"
TOKEN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/oauth2/token"
REDIRECT_URL = "https://analysis.kubioscloud.com/v1/portal/login"

"""### 1.1. Tarvittavat kirjastot"""

#!/usr/bin/env python3

import uuid
from pprint import pprint
import requests
import urllib
import json
import os
from urllib.parse import parse_qs, urlparse
import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

"""## 2. Kirjautuminen

### 2.1. Kirjautumisfunktio

Oheinen funktio on kopioitu ja muunneltu [Kubioscloud kirjautumisesimerkistä](https://bitbucket.org/kubios/workspace/snippets/4X95xd/kubioscloud-example-for-authorization-code). Funktiolle annetaan syötteenä:

- username - käyttäjätunnus
- password - salasana
- client_id - asiakastunnus, jota käytetään AWS-palvelun tunnistamisessa

Lisäksi funktio käyttää REDIRECT_URL ja LOGIN_URL osoitteita sekä USER_AGENT muuttujaa, jotka on määritelty aiemmin asetuksissa.

Tuloksena funktio palauttaa valtuutusavaimet, joka sisältää "id_token" ja "access_token" -kentät. Nämä tarvitaan myöhemmissä RESTapi kutsuissa.
"""

def user_login(username: str, password: str, client_id: str):

    # Luo yksilöllinen satunnainen tunniste kirjautumisistunnolle. Lisätietoja:
    # https://en.wikipedia.org/wiki/Universally_unique_identifier ja
    # https://docs.python.org/3/library/uuid.html
    csrf = str(uuid.uuid4())

    # Avaa sessio
    session = requests.session()
    print(f"Kirjaudu KubiosCloud palveluun:")

    # Sisäänkirjautumisdata
    login_data = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URL,
        "username": username,
        "password": password,
        "response_type": "token",
        "scope": "openid",
        "_csrf": csrf,
    }

    # Lähetä kirjautumispyyntö
    login_response = session.post(
        LOGIN_URL,
        data = login_data,
        allow_redirects = False,
        headers={"Cookie": f"XSRF-TOKEN={csrf}", "User-Agent": USER_AGENT},
    )

    # Verifoi tulokset
    login_response.raise_for_status()
    location_url = login_response.headers["Location"]
    if location_url == LOGIN_URL:
        raise AuthenticationError(f"Status: {login_response.status_code}, Autentikaatio epäonnistui.")

    # Virheen käsittely
    assert (login_response.status_code == 302), f"Status: {login_response.status_code}, Autentikointi epäonnistui."
    
    # Kerää valtuutusmerkit
    parsed = urlparse(location_url)
    parameters = parse_qs(parsed.fragment)
    tokens = {
        "id_token": parameters["id_token"][0],
        "access_token": parameters["access_token"][0],
    }

    print('Kirjautuminen onnistui.')

    return tokens

"""### 2.2. Hanki valtuutusavaimet (token)

Tässä on esimerkki kuinka kirjautumisfunktiota käytetään. Jos kirjautuminen on onnistunut, niin pprint näyttää valtuutusavaimet (tokens).
"""

tokens = user_login(USERNAME, PASSWORD, CLIENT_ID)
pprint(tokens)

"""## 3. Mittaustulosten ja -tietojen lukeminen ja tallentaminen

### 3.1. Lue käyttäjän tiedot

Seuraava koodi lukee KubiosCloud palvelusta käyttäjän tiedot ja tulostaa ne. Lisäksi tiedot tallennetaan tiedostoon
"""

# Avaa sessio, tätä käytetään koko Notebookin ajan
session = requests.session()

# HEADERS tarvitaan kaikissa RESTapi-kutsuissa. Se sisältää
# valtuutusavaimen (token) ja oman sovelluksen tunnuksen.
HEADERS = {"Authorization": tokens["id_token"], "User-Agent": USER_AGENT}

# Lue käyttäjän tiedot Kubioscloudista
response = session.get(
    "https://analysis.kubioscloud.com/v1/user/self",
    headers = HEADERS)
user_info = response.json()['user']

# Näytä vastaus
pprint(user_info)

# Luo data-kansio
if os.path.exists('./data') == False:
  os.mkdir('./data')

# Tallenna käyttäjätiedot
with open("./data/user_info.json", "w") as outfile:
    json.dump(user_info, outfile)
print("Käyttäjätiedot tallennettu tiedostoon ./data/user_info.json.")

"""### 3.2. Listaa kaikki analyysitulokset

Seuraava esimerkki näyttää kaikki analyysitulokset annetusta ajanhetkestä alkaen. Jos aikaleimaa ei anneta, näytetään viimeisten 30 päivän tulokset. Huomaa, että aikaleima pitää antaa ISO-formaatissa. Koska aika annetaan URL-osoitteeseen, pitää erikoismerkit [URL-koodata](https://www.w3schools.com/tags/ref_urlencode.asp). 

- %3A on  kaksoispiste ':', jota käytetään tuntien, minuuttien ja sekuntien erottimena ja 
- %2B on '+', joka kertoo missä aikavyöhykkeessä ollaan.
"""

# Tämä esimerkki esittelee miten aikaleima muodostetaan

# Muodosta Python datetime objekti
d = datetime.datetime(2023,1,1,0,0,0)

# Näytä aikaleima isoformaatissa
print('ISO-formaatti    =', d.isoformat())

# Näytä aikaleima isoformaatissa, mukaanlukien aikavyöhyke
print('aikavyöhyke      =', d.strftime("%Y-%m-%dT%H:%M:%S+00:00"))

# Muotoile aikaleima URL-yhteensopivaksi
url_time = d.strftime("%Y-%m-%dT%H:%M:%S+00:00").replace(':', '%3A').replace('+', '%2B')
print('url-yhteensopiva =', url_time)

## Listaa kaikki analyysitulokset alkaen annetusta aikaleimasta
GET_RESULT = "https://analysis.kubioscloud.com/v2/result/self" + "?from=2023-01-01T00%3A00%3A00%2B00%3A00"

response = session.get(GET_RESULT, headers = HEADERS)
all_results = response.json()['results']

# Näytä viimeisin tulos
pprint(all_results[-1])

## Tallenna tulokset tiedostoon
with open("./data/all_results.json", "w") as outfile:
    json.dump(all_results, outfile)
print("Tulokset tallennettu tiedostoon ./data/all_results.json")

"""### 3.3. Tallenna yksittäiset mittaustulokset

Seuraava koodi lukee `all_results` rakenteesta kaikki tulokset yksitellen ja kirjoittaa jokaisen yksittäisen mittauskerran tulokset erillisiin tiedostoihin. Koodi luo seuraavat tiedostot:

- r_xxx.json - sisältää analyysitulokset
- r_xxx_data.csv - sisältää PPI-datan
- r_xx_details.json - sisältää URL-linkin raakadataan

On myös mahdollista tarkastella pelkästään analyysituloksia. Tällöin ei tarvitse käyttää DATA_URL, vaan kaikki tarvittava tieto on all_results -tietorakenteessa.

Itse mittausdataan (PPI-data) päästää käsiksi `results`-kentän `measure_id` avulla. Käyttämällä `measure_id` RESTapi kutsussa saadaan tarkemmat tiedot (details) yksittäisestä mittauskerrasta, joka sisältää myös DATA_URL, jonka avulla voidaan lukea binäärimuotoon tallennettu PPI-data.
"""

# Käy läpi kaikki mittaukset yksitellen
for n, r in enumerate(all_results):

    # Tallenna yksittäiset tulokset
    with open(f'./data/r_{n:0=3d}.json', "w") as outfile:
        json.dump(r, outfile)
    
    # Lue yksittäiset mittaustiedot
    MEASURE_ID = r['measure_id']
    GET_RESULT_INFORMATION = "https://analysis.kubioscloud.com/v2/measure/self/session/" + MEASURE_ID
    response = session.get(GET_RESULT_INFORMATION, headers = HEADERS)
    details = response.json()
    
    # Tallenna tiedot
    with open(f'./data/r_{n:0=3d}_details.json', "w") as outfile:
        json.dump(details, outfile)

    ## Lue mittausdatan DATA_URL ja 'measured_timestamp'
    DATA_URL = details['measure']['channels'][0]['data_url']
    measured = details['measure']['measured_timestamp']

    ## Lue raakadata byte muuttujaan. Data on binäärikoodattu
    data = urllib.request.urlopen(DATA_URL)
    byte = data.read(2)
    rr = []

    ## Muunna binääridata numpy array:ksi
    while byte:
        rr.append(int.from_bytes(byte, byteorder = "little"))
        byte = data.read(2)
    rr = np.array(rr)
    
    ## Tallenna PPI-data tiedostoon
    np.savetxt(f'./data/r_{n:0=3d}_data.csv', rr, fmt="%d", delimiter=",")
    
    ## Näytä viesti, että tiedot tallennettu
    print(f'Tallennettu ./data/r_{n:0=3d} tiedostot.')

"""## 4. Tulostiedostojen käsittely

Seuraavaksi esitellään kuinka paikallisesti tallennettuja tiedostoja voidaan käsitellä Pythonissa.

### 4.1. Lue ja näytä käyttäjän tiedot

Ensimmäiseksi luetaan ja näytetään käyttäjätiedot.
"""

with open('./data/user_info.json') as json_file:
    user_data = json.load(json_file)
pprint(user_data)

print()
print(f"email = {user_data['email']}")

"""### 4.2. Analyysitulokset

Seruaavaksi kerätään `all_results.json` tietorakenteesta kaikki `readiness`, `sns_index` ja `pns_index` tulokset sekä näihin liittyvät aikaleimat `daily_results`.

Listat muutetaan Pandas DataFrameksi, jota on näppärämpi käsitellä Pythonissa.
"""

# Load daily readiness data
with open('./data/all_results.json') as json_file:
    results = json.load(json_file)

# Collect daily results from the results
daily_result = []
readiness = []
sns_index = []
pns_index = []
for n, r in enumerate(results):
    daily_result.append(r['daily_result'])
    readiness.append(r['result']['readiness'])
    sns_index.append(r['result']['sns_index'])
    pns_index.append(r['result']['pns_index'])

# Create Pandas Dataframe for easier handling
dict = {'time': daily_result,
        'readiness': readiness,
        'sns_index': sns_index,
        'pns_index': pns_index}
df = pd.DataFrame(dict)

# Change time to datetime object and set it as index
df['time'] = pd.to_datetime(df['time'])
df.set_index('time', inplace = True)

"""Näytä DataFramen viisi viimeistä riviä."""

df.tail()

"""Näytä kuvailevat tilastotiedot:
- count = kuinka monta mittaustulosta on
- mean = keskiarvo
- std = standardihajonta
- min = pienin arvo
- max = suurin arvo
- 25%, 50%, 75% = kvartiiliarvot
"""

df.describe().T

"""Näytä readiness-arvot viivakuvaajana (plot)."""

df['readiness'].plot(style = 'o-');
plt.title('Daily readiness')
plt.grid()
plt.show()

"""### 4.3. Yksittäinen mittauskerta

Seuraavaksi tarkastellaan yksittäistä mittauskertaa tarkemmin.
"""

# Valitse N:s mittauskerta
N = 8

# Muodosta tiedostojen nimet
details_file = f'./data/r_{N:0=3d}.json'
rr_file = f'./data/r_{N:0=3d}_data.csv'

# Näytä tiedostojen nimet
print(f'Details-tiedosto = {details_file}')
print(f'Mittausdata      = {rr_file}')

"""Lue details-tiedostosta mittauspäivämäärä"""

# Read the details
with open(details_file) as json_file:
    details = json.load(json_file)
# details
print(details['daily_result'])

"""Lue mittausdatatiedosto käyttäen Pandas-kirjaston read_csv-funktiota. Laske sydämen syke ja peräkkäisten sykkeiden aika sekunteina."""

# Lue data
data = pd.read_csv(rr_file, header = None, names = ['rr'])

# Laske sydämen syke (BPM)
data['HR'] = 60*1000/data['rr']

# Laske aika
data['time'] = data['rr'].cumsum()/1000

# Näytä ensimmäiset 5 riviä
data.head()

"""Piirrä sykevälivaihtelukuvaaja"""

# Piirrä sykevälivaihtelu-kuvaaja
data.plot.line(x = 'time', y = 'rr', style = 'g')
plt.title(details['daily_result'])
plt.ylabel('rr (ms)')
plt.xlabel('¨Time (s)')
plt.grid()
plt.show()

"""Piirrä sydämen syke (BPM) -kuvaaja"""

# Piirrä sykekuvaaja
data.plot.line(x = 'time', y = 'HR', style = 'r')
plt.title(details['daily_result'])
plt.ylabel('heart rate (bpm)')
plt.xlabel('¨Time (s)')
plt.grid()
plt.show()

"""Laske lopuksi kuvailevat tilastolliset arvot."""

# Laske kuvaileva tilasto
data[['rr', 'HR']].describe().T

"""## 5. Tehtävät

Tähän tulee tehtävät....
"""

