import sqlite3
from os.path import exists
import os
#You can always get the latest update from the link below and make sure to put the cvl file in the same directory
#https://www.kaggle.com/gpreda/covid-world-vaccination-progress

def parsenumber(number) :
    number=str(number)
    number=number.split('.')[0].strip()
    number=list(number)
    out=number
    last3=[]
    while len(number)>3 :
        last3=number[-3:]+last3
        last3.insert(0,',')
        del number[-3:]
        out=number+last3
    return listtostr(out)

def listtostr(list) :
    str=''
    for element in list :
        str+=element
    return str


def parsedata(cline) :
    date=cline[2]
    vaccinated=parsenumber(cline[4])
    f_vaccinated=parsenumber(cline[5])
    dv=parsenumber(cline[6])
    vaccinated_ph=cline[9]
    f_vaccinated_ph=cline[10]
    vaccine=cline[12]
    if cline[12].startswith('"') : #countries which have several vaccines
        sindex=13
        while True:
            text=cline[sindex]
            vaccine=vaccine+text
            if text.endswith('"') :
                source_name=cline[sindex+1]
                break
            else :
                sindex+=1
    else :
        source_name=cline[13]

    global k_vaccinated
    global k_f_vaccinated
    global k_vaccinated_ph
    global k_f_vaccinated_ph

    #keep the latest data if country doesn't publish new data
    if len(vaccinated)<1 :
        vaccinated=k_vaccinated
    else :
        k_vaccinated=vaccinated

    if len(f_vaccinated)<1 :
        f_vaccinated=k_f_vaccinated
    else :
        k_f_vaccinated=f_vaccinated

    if len(dv) < 1 : dv=None

    if len(vaccinated_ph)<1 :
        vaccinated_ph=k_vaccinated_ph
    else :
        k_vaccinated_ph=vaccinated_ph

    if len(f_vaccinated_ph)<1 :
        f_vaccinated_ph=k_f_vaccinated_ph
    else :
        k_f_vaccinated_ph=f_vaccinated_ph

    return (date,vaccinated,f_vaccinated,dv,vaccinated_ph,f_vaccinated_ph,vaccine,source_name)

#if exists('vaccination_data.sqlite') : os.remove('vaccination_data.sqlite')
conn=sqlite3.connect('vaccination_data.sqlite')
cur=conn.cursor()

cur.executescript('''
            DROP TABLE IF EXISTS Vaccine;
            DROP TABLE IF EXISTS Daily;

            CREATE TABLE IF NOT EXISTS Vaccine(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Country TEXT UNIQUE,
            Vaccines TEXT,
            Source TEXT
            );
            CREATE TABLE IF NOT EXISTS Daily(
            Country_id INTEGER,
            Vaccinated  REAL,
            Fully_Vaccinated  REAL,
            Daily_Vaccinated REAL,
            "Vaccinated(%)"  REAL,
            "Fully_Vaccinated(%)"  REAL,
            Date TEXT
            );
            CREATE TABLE IF NOT EXISTS Geodata(
            Country_id INTEGER,
            geo TEXT NULL
            )''')

handle=open('country_vaccinations.csv')
linelist=list()

k_vaccinated=None
k_f_vaccinated=None
k_vaccinated_ph=None
k_f_vaccinated_ph=None


for line in handle :
    linelist.append(line)

firstline=True #first line realted to a country
count=0
for i in range(len(linelist)) :
    count+=1
    if i == 0 : continue #omitting the first line
    infos=linelist[i].split(',')
    if firstline :
        country=infos[0]
        print('Retrieving data related to: ',country)
        cur.execute('INSERT INTO Vaccine (Country) VALUES (?)',(country,))
        cur.execute('SELECT id FROM Vaccine WHERE Country=?',(country,))
        country_id=cur.fetchone()[0]
        datas=parsedata(infos)
        (date,vaccinated,f_vaccinated,dv,vaccinated_ph,f_vaccinated_ph,vaccine,source_name)=datas
        cur.execute('''
        INSERT INTO Daily (Country_id,Vaccinated,Fully_Vaccinated,Daily_Vaccinated,"Vaccinated(%)","Fully_Vaccinated(%)",Date) VALUES
         (?,?,?,?,?,?,?)''',(country_id,vaccinated,f_vaccinated,dv,vaccinated_ph,f_vaccinated_ph,date))
        firstline=False
    try :
        if linelist[i+1].startswith(country) : #not the last line for a country
            datas=parsedata(infos)
            (date,vaccinated,f_vaccinated,dv,vaccinated_ph,f_vaccinated_ph,vaccine,source_name)=datas
            cur.execute('''
            INSERT INTO Daily (Country_id,Vaccinated,Fully_Vaccinated,Daily_Vaccinated,"Vaccinated(%)","Fully_Vaccinated(%)",Date) VALUES
             (?,?,?,?,?,?,?)''',(country_id,vaccinated,f_vaccinated,dv,vaccinated_ph,f_vaccinated_ph,date))

        else : #the last line of the csv file
            raise IndexError
    except IndexError :
        firstline=True

        datas=parsedata(infos)
        (date,vaccinated,f_vaccinated,dv,vaccinated_ph,f_vaccinated_ph,vaccine,source_name)=datas

        cur.execute('''
        INSERT INTO Daily (Country_id,Vaccinated,Fully_Vaccinated,Daily_Vaccinated,"Vaccinated(%)","Fully_Vaccinated(%)",Date) VALUES
         (?,?,?,?,?,?,?)''',(country_id,vaccinated,f_vaccinated,dv,vaccinated_ph,f_vaccinated_ph,date))

        cur.execute('UPDATE Vaccine SET Vaccines=? , Source=? WHERE id=?',(vaccine,source_name,country_id))

        k_vaccinated=None
        k_f_vaccinated=None
        k_vaccinated_ph=None
        k_f_vaccinated_ph=None

    if count%50==0 : conn.commit()
conn.commit()
print('Finished with getting data from csv file, run geoload.py to fill up geodata column.')

#you can run the command below in your sqlite browser if you want

#SELECT Vaccine.Country,Daily.Vaccinated,Daily.Fully_Vaccinated,Daily."Vaccinated(%)",Daily."Fully_Vaccinated(%)",max(Date),Vaccine.Vaccines
#FROM Vaccine JOIN Daily ON Vaccine.id=Daily.Country_id
#GROUP BY Country_id
#ORDER BY "Fully_Vaccinated(%)" DESC
