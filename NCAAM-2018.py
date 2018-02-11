import numpy as np
import pandas as pd
from numpy.linalg import inv
from numpy import dot
import re
import matplotlib.pyplot as plt
from math import isnan
import datetime
from Bayes_NCAAM import *

D1=pd.read_csv('NCAAM2016-2017.csv')
D2=pd.read_csv('NCAAM2017-2018.csv')
D=D1.append(D2)[['date','away','home','away_score','home_score','spread']]
D=D.rename(columns={'date':'Date','away':'Away','home':'Home','away_score':'Away_pts','home_score':'Home_pts','spread':'Spread'})
D=D[D.Date<'2018-02-10']
D['Ntrl']=np.full(len(D),float('Nan'))
print(D.head())

nbr_games_by_day=D.groupby('Date')[['Away']].count().rename(columns={'Away':'Games'})
print(nbr_games_by_day.head())
nbr_games=len(D)
print('Data for {} games'.format(nbr_games))

teams=sorted(D['Away'].append(D['Home']).unique())
nbr_teams=len(teams)
team_nbr={x:i for i,x in enumerate(teams)}

model0=Bayes_NCAAM_Model(teams,forget_rate=0.00,home_adv=2.75)
model1=Bayes_NCAAM_Model(teams,forget_rate=0.00,home_adv=2.75)

first_month=D[(D.Date>='2016-11-01') & (D.Date<'2016-11-30')]
help_start=first_month[['Date','Away','Home','Away_pts','Spread']]
help_start['Home_pts']=help_start['Away_pts']+help_start['Spread']
help_start=help_start.dropna(axis=0,how='any')
help_start['Ntrl']=first_month['Ntrl']

model1.RunGames(help_start,add_to_hist=False)
date='2016-11-08'
while date<'2017-04-01':
    week_later=date_incr(date,7)
    week_of_games=D[(D.Date>=date) & (D.Date<date_incr(date,7))]
    model0.RunGames(week_of_games)
    model1.RunGames(week_of_games)
    model0.forget()
    model1.forget()
    date=week_later
    
##model0.A=model2.A/2
##model1.A=model2.A/2
##model2.A=model2.A/2
##date='2017-11-08'
##while date<'2018-02-10':
##    week_later=date_incr(date,7)
##    week_of_games=D[(D.Date>=date) & (D.Date<date_incr(date,7))]
##    model0.RunGames(week_of_games)
##    model1.RunGames(week_of_games)
##    model2.RunGames(week_of_games)
##    date=week_later


print(model0.history.iloc[-50:][['Spread','Actual','Forecast']])


error_df0=model0.ErrorLog()
error_df1=model1.ErrorLog()
rolling_errors0=[wt_mean_errs(df) for df in roll_df(error_df0,5)]
rolling_errors1=[wt_mean_errs(df) for df in roll_df(error_df1,5)]
model_roll_errs0,spread_roll_errs=zip(*rolling_errors0)
model_roll_errs1,ignore=zip(*rolling_errors1)

L=len(error_df1)
plt.plot(range(4,L),model_roll_errs0,'r-')
plt.plot(range(4,L),model_roll_errs1,'b-')
plt.plot(range(4,L),spread_roll_errs,'k-')
plt.plot(range(L),error_df0.ModelError.values,'r.')
plt.plot(range(L),error_df1.ModelError.values,'b.')
plt.plot(range(L),error_df1.SpreadError.values,'k.')
plt.xlim([0,L])
plt.ylim([8,12])
plt.show()
