import numpy as np
import pandas as pd
from numpy.linalg import inv
from numpy import dot
from math import isnan
import datetime
from scipy.stats import norm

class Elo_NCAAM_Model(object):
    def __init__(self,teams,sigma=0.5,home_adv=3.0):
        self.teams=teams
        self.nbr_teams=len(teams)
        self.team_nbr={x:i for i,x in enumerate(teams)}
        self.strengths=np.zeros(self.nbr_teams)
        self.sigma=sigma
        self.home_adv=home_adv
        self.history=pd.DataFrame(columns=['Date','Away','Home','Actual','Forecast','Spread'])

        
    
    def update(self,games):
        for row in games.itertuples():
            h=self.team_nbr[row.Home]
            a=self.team_nbr[row.Away]
            theta = self.strengths[h]- self.strengths[a] + self.home_adv*(1-row.Ntrl)
            theta = min(3,max(-3,theta))
            p=norm.cdf(theta)
            q=1-p
            r=self.sigma/np.sqrt(p*q)
            home_won = row.Home_pts > row.Away_pts
            delta= q*r if home_won else -p*r
            self.strengths[h] += delta
            self.strengths[a] -= delta
        
    
    def predict(self,games):
        games['HomeStr']=games.apply(lambda row: self.strengths[self.team_nbr[row.Home]]+self.home_adv*(1-row.Ntrl), axis=1)
        games['AwayStr']=games.apply(lambda row: self.strengths[self.team_nbr[row.Away]], axis=1)
        return 10*(games.HomeStr-games.AwayStr).values
    
    def RunGames(self,games,add_to_hist=True):
        if len(games)==0:
            return
        record=games[['Date','Away','Home','Spread']]
        record['Forecast']=self.predict(games)
        record['Actual']=games['Home_pts']-games['Away_pts']
        if add_to_hist:
            self.history=self.history.append(record)
        self.update(games)

    def rankings(self):
        df=pd.DataFrame({'Team':self.teams,'Strengths':self.strengths})
        df=df.sort_values(by='Strengths',ascending=False)
        df['Rank']=[i for i in range(1,len(self.teams)+1)]
        df=df.set_index('Rank')
        return df
    
    def ErrorLog(self):
        H=self.history
        H['SpreadErr']=H.apply(lambda row: abs(row.Spread - row.Actual), axis=1)
        H['ForecastErr']=H.apply(lambda row: abs(row.Forecast - row.Actual), axis=1)
        day=min(H['Date'].values)
        final_day=max(H['Date'].values)
        error_avgs=[]
        while day<=final_day:
            week=H[(H.Date>=day) & (H.Date<date_incr(day,7))]
            games=len(week)
            spread_avg=np.average(week['SpreadErr'].dropna().values)
            forecast_avg=np.average(week['ForecastErr'].values)
            error_avgs.append([day,games,forecast_avg,spread_avg])
            day=date_incr(day,7)
            
        log_df=pd.DataFrame(error_avgs, columns=['Date','Games','ModelError','SpreadError'])
        return log_df



def date_incr(date,incr):
    y,m,d=date.split('-')
    d=datetime.date(int(y),int(m),int(d))
    d=d+datetime.timedelta(days=incr)
    new_date=str(d.year)+'-'+str(d.month).zfill(2)+'-'+str(d.day).zfill(2)
    return new_date

#  Will be used to compute running averages weighted by numbers of games:
def roll_df(df,window):
    l=len(df)
    for i in range(l-window+1):
        yield df.iloc[i:i+window]
        
def wt_mean_errs(df):
    W=df.Games.sum()
    E1=df.apply(lambda row: row.Games * row.ModelError, axis=1).sum()
    E2=df.apply(lambda row: row.Games * row.SpreadError, axis=1).sum()
    if W>0:
        return (E1/W,E2/W)
    return (float('Nan'),float('Nan'))
