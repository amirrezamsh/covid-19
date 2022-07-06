import matplotlib.pyplot as plt
import sqlite3
import pandas as pd

def recommend(mycountry,dic) :
    possibles=list()
    letters=list(mycountry)
    for country in list(dic.keys()) :
        if not (country.startswith(mycountry[0]) or country.startswith(mycountry[-1])) : continue
        count=0
        for letter in letters :
            if letter in country : count+=1
        if count>=len(country)-2 : possibles.append(country)
    if len(possibles)<1 :
        print("Couldn't find any matches with this country :",mycountry)
        exit()
        print('here')
    recommendation=','.join(possibles)
    return 'Do you mean '+recommendation+' ? :'


conn=sqlite3.connect('vaccination_data.sqlite')
cur=conn.cursor()

cur.execute('SELECT Country,id FROM Vaccine')

cntid={ country:id for (country,id) in cur}
cnt1=input('Enter the first country: ').capitalize()
if not (cnt1 in list(cntid.keys())) :
    while True :
        ans=recommend(cnt1,cntid)
        cnt1=input(ans).capitalize()
        if cnt1 in list(cntid.keys()) : break

cur.execute('SELECT Date,Vaccinated FROM DAILY WHERE Country_id=?',(cntid[cnt1],))
x1,y1=[],[]
for date,vaccinated in cur :
    x1.append(date)
    y1.append(vaccinated)

cnt2=input('Enter the second country: ').capitalize()
if not (cnt2 in list(cntid.keys())) :
    while True :
        ans=recommend(cnt2,cntid)
        cnt2=input(ans).capitalize()
        if cnt2 in list(cntid.keys()) : break
cur.execute('SELECT Date,Vaccinated FROM DAILY WHERE Country_id=?',(cntid[cnt2],))
x2,y2=[],[]
for date,vaccinated in cur :
    x2.append(date)
    y2.append(vaccinated)


plt.plot(x1,y1,label=cnt1)
plt.plot(x2,y2,label=cnt2)
plt.legend()
plt.title(f'Cumulative vaccinated persons in {cnt1} and {cnt2}')
plt.show()

#cnt2=input('Enter the second country: ')
