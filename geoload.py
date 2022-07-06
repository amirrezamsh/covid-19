import urllib.request, urllib.parse, urllib.error
import http
import sqlite3
import json
import time
import ssl
import sys



api_key = False
# If you have a Google Places API key, enter it here
# api_key = 'AIzaSy___IDByT70'

if api_key is False:
    api_key = 42
    serviceurl = "http://py4e-data.dr-chuck.net/json?"
else :
    serviceurl = "https://maps.googleapis.com/maps/api/geocode/json?"

# Additional detail for urllib
# http.client.HTTPConnection.debuglevel = 1

conn = sqlite3.connect('vaccination_data.sqlite')
cur = conn.cursor()

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
gdata=dict()
cur.execute('SELECT id,Country FROM Vaccine')

for element in cur :
    address =element[1]
    c_id=element[0]
    gdata[address]=c_id

geodata=dict()

cur.execute('SELECT geo FROM Geodata')
for item in cur :
    name=json.loads(item[0])['country_name']
    jsonfile=json.loads(item[0])
    geodata[name]=jsonfile

print('len geodata is',len(geodata))
time.sleep(5)
b_conn=sqlite3.connect('b_vaccination_data.sqlite')
conn.backup(b_conn)
cur1 = b_conn.cursor()

cur1.executescript('''DROP TABLE IF EXISTS Geodata;
                    CREATE TABLE IF NOT EXISTS Geodata(
                    Country_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    geo TEXT NULL
                    )''')


count = 0
for country in gdata.keys():
    if count > 250 :
        print('Retrieved 200 locations, restart to retrieve more')
        break
    if country in geodata.keys() :
        print('found',country)
        continue

    parms = dict()
    parms["address"] = country
    if api_key is not False: parms['key'] = api_key
    url = serviceurl + urllib.parse.urlencode(parms)

    print('Retrieving', url)
    uh = urllib.request.urlopen(url, context=ctx)
    data = uh.read().decode()
    print('Retrieved', len(data), 'characters', data[:20].replace('\n', ' '))
    count = count + 1

    try:
        js = json.loads(data)
        js['country_name']=country
    except:
        print(data)  # We print in case unicode causes an error
        continue

    if 'status' not in js or (js['status'] != 'OK' and js['status'] != 'ZERO_RESULTS') :
        print('==== Failure To Retrieve ====')
        print(data)
        break
    #data=json.dumps(js)
    #cur.execute('''REPLACE INTO Geodata (geo,Country_id) VALUES (?,?)''', (memoryview(data.encode()),country_id))
    geodata[country]=js
    if count % 50 == 0 :
        print('Pausing for a bit...')
        time.sleep(2)
if sorted(geodata)==list(gdata.keys()) : print('Ok')
time.sleep(2)
for country in gdata.keys() :
    #print(type(geodata[country]))
    #print(len(geodata[country]))
    mydata=memoryview(json.dumps(geodata[country]).encode())
    #print(mydata)
    cur1.execute('INSERT INTO Geodata (geo) VALUES (?)',(mydata,))
b_conn.commit()
b_conn.backup(conn)
conn.commit()
print("Run geodump.py to read the data from the database so you can vizualize it on a map.")
