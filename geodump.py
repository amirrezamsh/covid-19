import sqlite3
import json
import codecs
from os.path import exists
import os

if exists('where.js') : os.remove('where.js')
conn = sqlite3.connect('vaccination_data.sqlite')
cur = conn.cursor()

cur.execute('''
            SELECT Vaccine.Country,Daily.Vaccinated,Daily.Fully_Vaccinated,Daily."Vaccinated(%)",Daily."Fully_Vaccinated(%)",Geodata.geo,max(Date)
            FROM Vaccine JOIN Daily JOIN Geodata ON Vaccine.id=Daily.Country_id and Vaccine.id=Geodata.Country_id
            GROUP BY Daily.Country_id
            ORDER BY Vaccine.id''')

fhand = codecs.open('where.js', 'w', "utf-8")
fhand.write("myData = [\n")
count = 0
for row in cur :
    try :
        data = str(row[5].decode())
        js = json.loads(str(data))
    except: continue

    if not('status' in js and js['status'] == 'OK') : continue

    lat = js["results"][0]["geometry"]["location"]["lat"]
    lng = js["results"][0]["geometry"]["location"]["lng"]
    if lat == 0 or lng == 0 : continue
    where = js['results'][0]['formatted_address']
    where = where.replace("'", "")
    country=str(row[0])
    vaccinated=str(row[1])
    Fully_Vaccinated=str(row[2])
    vaccinate_percent=str(row[3])
    Fully_vaccinate_percent=str(row[4])

    if len(vaccinated)<1 : vaccinated=0.0
    if len(Fully_Vaccinated)<1 : Fully_Vaccinated=0.0
    if len(vaccinate_percent)<1 : vaccinate_percent=0.0
    if len(Fully_vaccinate_percent)<1 : Fully_vaccinate_percent=0.0

    try :
        print(where, lat, lng)

        count = count + 1
        if count > 1 : fhand.write(",\n")
        output = "["+str(lat)+","+str(lng)+',"'+str(vaccinated)+'","'+str(Fully_Vaccinated)+'","'+str(vaccinate_percent)+'","'+str(Fully_vaccinate_percent)+'","'+str(country)+'"]'
        fhand.write(output)
    except:
        continue

fhand.write("\n];\n")
cur.close()
fhand.close()
print(count, "records written to where.js")
print("Open where.html to view the data in a browser")
