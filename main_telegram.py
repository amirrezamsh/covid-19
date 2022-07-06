import telegram
from telegram import (ReplyKeyboardMarkup,InlineKeyboardMarkup,InlineKeyboardButton)
from telegram.ext import Updater
from telegram.ext import (CommandHandler,MessageHandler,CallbackQueryHandler,Filters)
import logging
import sqlite3
import pandas as pd
import numpy as np
import re
import datetime
import matplotlib.pyplot as plt
#from mpl_toolkits.basemap import Basemap
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from geonamescache import GeonamesCache
import matplotlib as mpl
import os
from zipfile import ZipFile

if not os.path.exists('Telegrambotdatabase.csv') :
    with open('Telegrambotdatabase.csv','w') as h :
        h.write('user_id,first_name,input,date\n')

def update_dataframe(update,context) :
    if update!=0 and context!=0 :
        with open('Telegrambotdatabase.csv','a') as h :
            fname=update.message.from_user.first_name
            lname=update.message.from_user.last_name
            if fname==None : fname=''
            if lname==None : lname=''
            h.write(str(update.effective_chat.id)+','+'"'+fname+' '+lname+'"'+','+str(update.message.text)+','+str(datetime.datetime.now()).split()[0]+'\n')
    if os.path.exists('globaldeaths_vis.png') : os.remove('globaldeaths_vis.png')
    global df
    global Dates
    df=pd.read_csv('GlobalDeathes.csv')
    df.set_index('Unnamed: 0',inplace=True)
    def total_deaths(row) :
        row['total']=sum(row)
        return row
    df=df.apply(total_deaths,axis=1)
    df['7day_mean']=df['total'].rolling(7).mean()
    df['7day_mean']=df['7day_mean'].replace(np.nan,0)
    Dates=[datetime.datetime.strptime(date,'%Y-%m-%d') for date in list(df.index)]
    if update!=0 and context!=0 :
        context.bot.send_message(chat_id=update.effective_chat.id,text='Dataframe successfully updated!')




def update_database(update,context) :
    if update!=0 and context!=0 :
        fname=update.message.from_user.first_name
        lname=update.message.from_user.last_name
        if fname==None : fname=''
        if lname==None : lname=''
        with open('Telegrambotdatabase.csv','a') as h :
            h.write(str(update.effective_chat.id)+','+'"'+fname+' '+lname+'"'+','+update.message.text+','+str(datetime.datetime.now()).split()[0]+'\n')

    if os.path.exists('numbervspercent_vis.png') : os.remove('numbervspercent_vis.png')
    global data
    if os.path.exists('vaccines_vis.png') : os.remove('vaccines_vis.png')
    if os.path.exists('numbervspercent_vis.png') : os.remove('numbervspercent_vis.png')

    conn=sqlite3.connect('vaccination_data.sqlite')
    cur=conn.cursor()
    cur.execute('''
                SELECT Vaccine.Country,Daily.Vaccinated,Daily.Fully_Vaccinated,Daily."Vaccinated(%)",Daily."Fully_Vaccinated(%)",max(Date),Vaccine.Vaccines
                FROM Vaccine JOIN Daily ON Vaccine.id=Daily.Country_id
                GROUP BY Country_id
                ORDER BY "Fully_Vaccinated(%)" DESC''')

    data=dict()
    for item in cur :

        data[item[0]]={'Vaccinated':item[1],'Fully_Vaccinated':item[2],'Vaccinated_p':item[3],
                            'Fully_Vaccinated_p':item[4],'last_Date':item[5],'Vaccines':item[6]}


    if update!=0 and context!=0 :
        context.bot.send_message(chat_id=update.effective_chat.id,text='Database successfully updated!')



update_dataframe(0,0)
update_database(0,0)


def visual_vaccines() :
    if not os.path.exists('vaccines_vis.png') :
        all_vaccines=dict()
        for country,vaccines in data.items() :
            vaccines=vaccines['Vaccines']
            vaccines=vaccines.replace('"','').replace('Sputnik V','Sputnik-V')
            for vaccine in vaccines.split(' ') :
                if not vaccine in all_vaccines.keys() : all_vaccines[vaccine]=1
                else :
                    all_vaccines[vaccine]=all_vaccines[vaccine]+1

        all_vaccines={vaccine:count for vaccine,count in sorted(all_vaccines.items(),key=lambda x : x[1],reverse=True)}
        dlts=[]
        for vaccine,count in all_vaccines.items() :
            if count<10 : dlts.append(vaccine)
        for vaccine in dlts :
            del all_vaccines[vaccine]

        plt.figure()
        limit=len(all_vaccines)
        if limit>10 : limit=10
        xvals=range(len(list(all_vaccines)[:limit]))
        yvals=list(all_vaccines.values())[:limit]
        plt.yticks(xvals,list(all_vaccines)[:limit])

        bars=plt.barh(xvals,yvals,color='#5BCAA0')
        bars[0].set_color('#AC5BCA')
        for spine in plt.gca().spines.values() :
            spine.set_visible(False)
        plt.tick_params(bottom=False,left=False,labelleft=True,labelbottom=False)
        plt.title(f'Number of locations currently adminestrating each vaccine (top{limit})',fontsize=15)
        for bar in bars :
            #if bar==bars[-1] or bar==bars[-2] :
            #    plt.gca().text(bar.get_width()-2.8,bar.get_y()+bar.get_height()/2,str(bar.get_width()),color='w',ha='center',fontsize=11)
            #else :
            plt.gca().text(bar.get_width()-5,bar.get_y()+(bar.get_height()/2)-0.1,str(bar.get_width()),color='w',ha='center',fontsize=14)
        plt.gca().invert_yaxis()
        fig=plt.gcf()
        fig.set_figwidth(12)
        fig.set_figheight(8)
        plt.savefig('vaccines_vis.png',edgecolor='w',facecolor='w')


def visual_globaldeaths() :
    if not os.path.exists('globaldeaths_vis.png') :
        plt.figure()
        starts=datetime.datetime(2020,12,14)
        plt.plot_date(Dates,list(df['total']),color='#E41A42',linestyle='solid',marker=None,linewidth=1,alpha=0.2)
        plt.plot_date(Dates,list(df['7day_mean']),color='#E41A42',linestyle='solid',marker=None,linewidth=1.5,label='7-day mean')
        plt.axvline(starts,color='#55BE64',label='vaccination starts')
        plt.gcf().autofmt_xdate()
        for spine in plt.gca().spines.values() :
            spine.set_visible(False)
        plt.tick_params(bottom=False,left=False,labelbottom=True,labelleft=True)
        plt.title('Daily Global deaths',fontsize=20)
        plt.xticks(fontsize=11)
        plt.xticks(fontsize=11)
        plt.legend()
        fig=plt.gcf()
        fig.set_figwidth(12)
        fig.set_figheight(8)
        plt.savefig('globaldeaths_vis.png',edgecolor='w',facecolor='w')


def visual_choropleth() :
    if not os.path.exists('choropleth_vis.png') :
        gc = GeonamesCache()
        countries = gc.get_countries()
        iso_codes={vals['name']:vals['iso3'] for vals in countries.values()}
        vaccine_df=pd.DataFrame(data)
        vaccine_df=vaccine_df.T
        num_colors=9
        bins=np.linspace(0,100,num_colors)

        iso_df=pd.Series(iso_codes)
        vaccine_df=pd.merge(vaccine_df,iso_df.rename('iso'),left_index=True,right_index=True)
        vaccine_df['Vaccinated_p'].dropna(inplace=True)
        vaccine_df['Vaccinated_p']=vaccine_df['Vaccinated_p'].apply(lambda x : 100 if x>100 else x*1)
        vaccine_df['bin']=np.digitize(vaccine_df['Vaccinated_p'].values, bins)-1

        fig = plt.figure(figsize=(16, 8))
        ax = fig.add_subplot(111)
        if not os.path.exists('ShapeFiles') :
            with ZipFile('shape1.zip','r') as my_zip :
                my_zip.extractall('ShapeFiles')
        shapefile = 'ShapeFiles//ne_10m_admin_0_countries'

        m=Basemap(projection='mill',
             llcrnrlat=-60,urcrnrlat=90,llcrnrlon=-180,urcrnrlon=180,resolution='c')

        m.fillcontinents(lake_color='#94f8ff')
        m.drawmapboundary(fill_color='#94f8ff')

        m.readshapefile(shapefile,name='units', color='#797A7B',linewidth=1)

        patches=[]
        bins1=[]
        for info, shape in zip(m.units_info, m.units):
            patches.append(Polygon(np.array(shape), True))
            iso3 = info['ADM0_A3']
            if iso3 not in list(df['iso']) :
                bin=0
            else :
                bin=df.loc[df.index[df['iso']==iso3].tolist()[0]]['bin']

            bins1.append(bin)

        p = PatchCollection(patches,zorder=2, cmap=plt.cm.get_cmap('Purples',8))
        p.set_array(np.array(bins1))
        ax.add_collection(p)

        cb = fig.colorbar(p, ax=ax, shrink=0.8, ticks = range(0,9))
        cb.ax.set_yticklabels([str(bin) for bin in bins])
        cb.ax.set_xlabel('(%)',size=15)
        plt.title("Percentage of people who's got the first dose")
        plt.savefig('choropleth_vis.png',edgecolor='w',facecolor='w')

def visual_top10() :
    if not os.path.exists('numbervspercent_vis.png') :
        df=pd.DataFrame(data)
        df=df.T
        df['Vaccinated']=df['Vaccinated'].apply(lambda x : str(x).replace(',',''))
        df['Vaccinated']=df['Vaccinated'].astype(float)
        df=df.sort_values(by='Vaccinated',ascending=False)
        countries=list(df.index)[:10]
        vaccinated=list(df['Vaccinated'])[:10]
        percent=list(df['Vaccinated_p'])[:10]
        fig,(ax1,ax2)=plt.subplots(1,2)
        x=np.arange(0,10,1)

        bar1=ax1.barh(x,vaccinated,color='#E98ADB')
        ax1.invert_xaxis()
        for spine in ax1.spines.values() :
            spine.set_visible(False)
        ax1.tick_params(left=False,labelleft=False,bottom=False,labelbottom=False)
        for bar in bar1 :
            ax1.text(bar.get_width()+45e6,bar.get_y()+bar.get_height()/2,str(bar.get_width()/1e6).split('.')[0],ha='center',fontsize=10,
                    color='#2B006D')

        bar2=ax2.barh(x,percent,color='#8AE997')
        for spine in ax2.spines.values() :
            spine.set_visible(False)
        ax2.tick_params(left=False,bottom=False,labelbottom=False)
        ax2.yaxis.set_major_locator(plt.FixedLocator(range(10)))
        ax2.yaxis.set_major_formatter(plt.FixedFormatter(countries))



        for bar in bar2 :
            ax2.text(bar.get_width()-7,bar.get_y()+bar.get_height()/2,str(bar.get_width()),ha='center',fontsize=10,color='w')

        ax1.invert_yaxis()
        ax2.invert_yaxis()

        ax1.set_title('Number of people vaccinated (million)',fontsize=10)
        ax2.set_title('Percentage of people vaccinated',fontsize=10)
        fig.set_figwidth(10)
        fig.set_figheight(6)
        plt.tight_layout()
        plt.savefig('numbervspercent_vis.png',edgecolor='w',facecolor='w')


updater=Updater(token='1709856501:AAHdC355SRJqPHCP1qv5DuFjbVTNZDXuWi4',use_context=True)

dispatcher=updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

def start_function(update,context) :
    fname=update.message.from_user.first_name
    lname=update.message.from_user.last_name
    if fname==None : fname=''
    if lname==None : lname=''
    with open('Telegrambotdatabase.csv','a') as h :
        h.write(str(update.effective_chat.id)+','+'"'+fname+' '+lname+'"'+','+'"'+str(update.message.text)+'"'+','+str(datetime.datetime.now()).split()[0]+'\n')


    first_name=update.message.from_user.first_name
    starttext=f'''Hi {first_name}, Are you curious about vaccination progress and Coronavirus death toll in our world? I am here to help you.
Just send me any country name in English'''
    context.bot.send_message(chat_id=update.effective_chat.id,text=starttext)

def help_function(update,context) :
    mytext='''Send me a country name or select Visualization from the menu'''
    context.bot.send_message(chat_id=update.effective_chat.id,text=mytext)

def vis_function(update,context) :


    keyboard=[[InlineKeyboardButton('Vaccines',callback_data='vis_vaccines'),
            InlineKeyboardButton('Global Deaths',callback_data='vis_globaldeaths')],[InlineKeyboardButton('Choropleth map',callback_data='vis_choropleth'),
            InlineKeyboardButton('Top 10',callback_data='vis_top10')]]

    inline_markup=InlineKeyboardMarkup(keyboard)

    context.bot.send_message(chat_id=update.effective_chat.id,text='please choose',reply_markup=inline_markup)


def anything(update,context) :
    #repkey=False
    cnt=update.message.text
    cnt=cnt.split()
    cnt=[part.capitalize() for part in cnt]
    cnt=' '.join(cnt)

    if cnt.upper()=='USA' : cnt='United States'
    if cnt.upper()=='UK' : cnt='United Kingdom'
    if cnt.upper()=='UAE' : cnt='United Arab Emirates'

    if not (cnt in set.intersection(set(list(df.columns)),set(data.keys()))) :
        possibles=list()
        letters=list(cnt)
        for country in set.intersection(set(list(df.columns)),set(data.keys())) :
            if not (country.startswith(cnt[0]) or country.startswith(cnt[-1])) : continue
            count=0
            for letter in letters :
                if letter in country : count+=1
            if count>=len(country)-2 : possibles.append(country)
        if len(possibles)<1 :
            mytext=f"Sorry, Couldn't find any country named {cnt}"
            context.bot.send_message(chat_id=update.effective_chat.id,text=mytext)
        else :
            mytext="You probably meant one of the countries below"
            keyboard=[[item] for item in possibles]
            markup=ReplyKeyboardMarkup(keyboard,resize_keyboard=True,one_time_keyboard=True)
            context.bot.send_message(chat_id=update.effective_chat.id,text=mytext,reply_markup=markup)

    else :
        cnt=cnt.replace(' ','&')
        mytext='Please choose'
        keyboard=[[InlineKeyboardButton('Vaccination',callback_data=cnt+'__vaccination'),
                InlineKeyboardButton('Deaths',callback_data=cnt+'__deaths')]]

        inline_markup=InlineKeyboardMarkup(keyboard)

        context.bot.send_message(chat_id=update.effective_chat.id,text=mytext,reply_markup=inline_markup)



def button(update,context) :

    query = update.callback_query
    query.answer()

    fname=query.message.chat.first_name
    lname=query.message.chat.last_name
    if fname==None : fname=''
    if lname==None : lname=''
    with open('Telegrambotdatabase.csv','a') as h :
        h.write(str(query.message.chat.id)+','+'"'+fname+' '+lname+'"'+','+'"'+str(query.data)+'"'+','+str(datetime.datetime.now()).split()[0]+'\n')


    cnt=str(query.data).split('__')[0]
    cnt=cnt.replace('&',' ')
    if re.search('.+__vaccination',query.data) :
        mytext=f'''{cnt}
Vaccinated(%) : {data[cnt]["Vaccinated"]}({data[cnt]["Vaccinated_p"]})
Fully Vaccinated(%) : {data[cnt]["Fully_Vaccinated"]}({data[cnt]["Fully_Vaccinated_p"]})
Last updated at {data[cnt]["last_Date"]}'''
        query.edit_message_text(text=mytext)
    elif re.search('.+__deaths',query.data):
        mytext=f'''Cumulative deathes : {df[cnt].sum()}
Last month average : {int(df[cnt][-30:].mean())}
Number of deaths on {df[cnt].index[-1]} : {df[cnt][-1]}'''
        query.edit_message_text(text=mytext)


def vis_button(update,context) :
    query = update.callback_query

    query.answer()

    fname=query.message.chat.first_name
    lname=query.message.chat.last_name
    if fname==None : fname=''
    if lname==None : lname=''
    with open('Telegrambotdatabase.csv','a') as h :
        h.write(str(query.message.chat.id)+','+'"'+fname+' '+lname+'"'+','+'"'+str(query.data)+'"'+','+str(datetime.datetime.now()).split()[0]+'\n')

    if str(query.data)=='vis_vaccines' :
        visual_vaccines()
        context.bot.send_photo(chat_id=update.effective_chat.id,photo=open('vaccines_vis.png','rb'))
    elif str(query.data)=='vis_globaldeaths' :
        visual_globaldeaths()
        context.bot.send_photo(chat_id=update.effective_chat.id,photo=open('globaldeaths_vis.png','rb'))

    elif str(query.data)=='vis_choropleth' :
        visual_choropleth()
        context.bot.send_photo(chat_id=update.effective_chat.id,photo=open('choropleth_vis.png','rb'))
    else :
        visual_top10()
        context.bot.send_photo(chat_id=update.effective_chat.id,photo=open('numbervspercent_vis.png','rb'))

def not_text(update,context) :
    fname=update.message.from_user.first_name
    lname=update.message.from_user.last_name
    if fname==None : fname=''
    if lname==None : lname=''
    with open('Telegrambotdatabase.csv','a') as h :
        h.write(str(update.effective_chat.id)+','+'"'+fname+' '+lname+'"'+','+'"'+'Not_text'+'"'+','+str(datetime.datetime.now()).split()[0]+'\n')


    context.bot.send_message(chat_id=update.effective_chat.id,text='Please send me a text message!')



help_handler=CommandHandler('help',help_function)

start_handler=CommandHandler('start',start_function)

visual_handler=CommandHandler('vis',vis_function)

updatedb_handler=CommandHandler('updatedatabase1390',update_database)

updatedf_handler=CommandHandler('updatedataframe1390',update_dataframe)

others_handler=MessageHandler(Filters.text & ~(Filters.command),anything)

callback_handler=CallbackQueryHandler(button,pattern='\S*__[vd]\S+')

callback_visual_handler=CallbackQueryHandler(vis_button,pattern='vis_.*')

media_handler=MessageHandler((Filters.photo | Filters.video | Filters.audio | Filters.document) & ~(Filters.command),not_text)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(visual_handler)
dispatcher.add_handler(callback_handler)
dispatcher.add_handler(callback_visual_handler)
dispatcher.add_handler(updatedb_handler)
dispatcher.add_handler(updatedf_handler)
dispatcher.add_handler(others_handler)
dispatcher.add_handler(media_handler)


updater.start_polling()
