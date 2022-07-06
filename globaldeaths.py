#!/usr/bin/env python
# coding: utf-8

# In[16]:


import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import os


# In[2]:

if os.path.exists('GlobalDeathes.csv') : os.remove('GlobalDeathes.csv')

import datetime
df=pd.read_csv("datasets//time_series_covid19_deaths_global.csv")
df.drop(['Lat','Long'],axis=1,inplace=True)
df=df.set_index(['Country/Region','Province/State'])

df=df.groupby('Country/Region').sum()
df.index.name='Date'
trp=df.T



data=dict()
for country in trp.columns :
    deathes=list()
    for item in range(len(trp[country])) :
        if item ==0 :

            deathes.append(trp[country][item])
            continue
        else :

            if trp[country][item]<trp[country][item-1] : trp[country][item]=trp[country][item-1]
            deathes.append(trp[country][item]-trp[country][item-1])

    data[country]=deathes

daily_df=pd.DataFrame(data)
daily_df.index=trp.index
dates=[str(datetime.datetime.strptime(item,'%m/%d/%y')).split()[0] for item in list(trp.index)]
daily_df.index=dates


df_us=pd.read_csv('datasets//time_series_covid19_deaths_US.csv')
df_us.drop(['UID','iso2','iso3','code3','FIPS','Admin2','Lat','Long_','Combined_Key','Population'],axis=1,inplace=True)
df_us=df_us.groupby('Country_Region').sum()
df_us.index.name='Date'
trp_us=df_us.T
trp_us

deathes=list()
for item in range(len(trp_us['US'])) :
    if item ==0 :

        deathes.append(trp_us['US'][item])
        continue
    else :

        if trp_us['US'][item]<trp_us['US'][item-1] : trp_us['US'][item]=trp_us['US'][item-1]
        deathes.append(trp_us['US'][item]-trp_us['US'][item-1])
daily_us=pd.DataFrame({'US':deathes})
daily_us.index=dates

whole_df=pd.merge(daily_df,daily_us,how='inner',left_index=True,right_index=True)
whole_df.rename(columns={'US_x':'United States','Taiwan*':'Taiwan'},inplace=True)
whole_df.drop('US_y',axis=1,inplace=True)
whole_df.to_csv('GlobalDeathes.csv')


# In[10]:


#def total_deaths(row) :
#    row['total']=sum(row)
#    return row
#whole_df=whole_df.apply(total_deaths,axis=1)


# In[13]:


#Dates=[datetime.datetime.strptime(date,'%Y-%m-%d') for date in list(whole_df.index)]


# In[33]:


# plt.figure()
# plt.plot_date(Dates,list(whole_df['total']),color='#E41A42',linestyle='solid',marker=None,linewidth=1)
# plt.gcf().autofmt_xdate()
# for spine in plt.gca().spines.values() :
    # spine.set_visible(False)
# plt.tick_params(bottom=False,left=False,labelbottom=True,labelleft=True)
# plt.title('Daily Global deaths',fontsize=20)
# plt.xticks(fontsize=11)
# plt.xticks(fontsize=11)
# fig=plt.gcf()
# fig.set_figwidth(12)
# fig.set_figheight(8)
# plt.savefig('globaldeaths_vis.png',edgecolor='w',facecolor='w')


# In[ ]:
