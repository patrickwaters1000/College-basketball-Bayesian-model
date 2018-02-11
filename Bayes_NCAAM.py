import numpy as np
import pandas as pd
from numpy.linalg import inv
from numpy import dot
from math import isnan
import datetime

class Bayes_NCAAM_Model(object):
    def __init__(self,teams,sigma=10.0,home_adv=3.0,forget_rate=0.0):
        self.teams=teams
        self.nbr_teams=len(teams)
        self.team_nbr={x:i for i,x in enumerate(teams)}
        self.mu=np.zeros(self.nbr_teams)
        self.A=np.identity(self.nbr_teams)/100
        self.sigma=sigma
        self.home_adv=home_adv
        self.forget_rate=forget_rate
        self.history=pd.DataFrame(columns=['Date','Away','Home','Actual','Forecast','Spread'])

        
    
    def update(self,games):
        m=self.nbr_teams
        L=np.array([[0 for j in range(m)] for i in range(m)])
        score_diffs=np.array([0 for i in range(m)])
        for row in games.itertuples():
            h=self.team_nbr[row.Home]
            a=self.team_nbr[row.Away]
            d=row.Home_pts-row.Away_pts-self.home_adv*int(row.Ntrl!=0)
            score_diffs[h]+=d
            score_diffs[a]-=d
            L[h,h]+=1
            L[a,a]+=1
            L[a,h]-=1
            L[h,a]-=1
            
        v= dot(self.A,self.mu) + score_diffs/self.sigma**2
        self.A = self.A + L/self.sigma**2
        self.mu= dot(inv(self.A),v)
        
    def forget(self):
        self.A=self.A/(1+self.forget_rate)
        
    def predict_game(self,home,away):
        home=self.team_nbr[home]
        away=self.team_nbr[away]
        return self.mu[home]-self.mu[away]+self.home_adv
    
    def predict(self,games):
        ser=games.apply(lambda row: self.predict_game(row.Home,row.Away), axis=1)
        return ser.values
    
    def RunGames(self,games,add_to_hist=True):
        record=games[['Date','Away','Home','Spread']]
        record['Forecast']=self.predict(games)
        record['Actual']=games['Home_pts']-games['Away_pts']
        if add_to_hist:
            self.history=self.history.append(record)
        self.update(games)

    def rankings(self):
        df=pd.DataFrame({'Team':self.teams,'Strengths':self.mu})
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
