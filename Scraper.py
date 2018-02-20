import re
from io import StringIO
import pandas as pd
from math import isnan


save='NCAAM2014-2017.csv'
RAW_DATA=''
for start_year in range(14,17):
    load='11-{}_thru_4-{}.txt'.format(start_year,start_year+1)

    s = StringIO()
    with open(load) as file:
        for line in file:
            s.write(line)
    RAW_DATA+=s.getvalue()


month=r'(?:October|November|December|January|February|March|April)'
date_re=re.compile(month+r' \d+ \d+')
game_re=re.compile(r'final(?:.*\n){,25}(?:Push(?:.*\n){,3}Push|Over(?:.*\n){,2})')


#  Split data string by day, then by game.
date_list=[]
games_by_date=[]
find_dates=date_re.finditer(RAW_DATA)
this_day=next(find_dates)
for next_day in find_dates:
    todays_games=RAW_DATA[this_day.end():next_day.start()]
    date_list.append(this_day.group())
    game_strings=game_re.findall(todays_games)
    games_by_date.append(game_strings)
    this_day=next_day
todays_games=RAW_DATA[this_day.end():]
date_list.append(this_day.group())    
game_strings=game_re.findall(todays_games)
games_by_date.append(game_strings)

print(date_list)

#  Function for extracting data from one game string.
def read_game_string(game):
    ATS_finder_re=re.compile(r'\n.+ATS.*\n')
    game=ATS_finder_re.sub('\n',game)
    lines=game.split('\n')
    away=lines[1]
    home=lines[4]
    away_abbrev=lines[9]
    home_abbrev=lines[11]
    
    away_scores=re.findall(r'[\d]+',lines[10])
    if len(away_scores)<3:
        badly_formatted_games.append(game)
        return {}
    
    home_scores=re.findall(r'[\d]+',lines[12])

    vals={'Away':away, 'Away_pts':int(away_scores[-1]),
          'Home':home, 'Home_pts':int(home_scores[-1]),
          'Away_1st_half':int(away_scores[0]), 'Away_2nd_half':int(away_scores[1]),
          'Home_1st_half':int(home_scores[0]), 'Home_2nd_half':int(home_scores[1])}
    OT=len(re.findall('OT',lines[6]))
    if OT==1:
        vals['Away_OT']=int(away_scores[2])
        vals['Home_OT']=int(home_scores[2])

    redundant_spread_info=re.compile(r'(\+|-)([\d\.]+) ATS\n')
    game=redundant_spread_info.sub('',game)
    #  Spread: away term covers spread if away + spread > home
    #  If the game string contained spread info, the following RE should now find it:
    spread_re=re.compile(away_abbrev+r'\n(\+|-)([\d\.]+)\n'+home_abbrev)
    for match in spread_re.finditer(game):
        plus_or_minus,value = match.groups()
        spread=float(value) * {'+':1, '-':-1}[plus_or_minus]
        vals['Spread']=spread
        
    #  If possible, determine the over/under line (sometimes it is missing).
    over_under_re=re.compile(r'(\+|-)([\d\.]+) \([\d]+\)')
    for match in over_under_re.finditer(game):
        plus_or_minus,value = match.groups()
        over_under_result=float(value) * {'+':1, '-':-1}[plus_or_minus]
        vals['Over_under']=vals['Away_pts']+vals['Home_pts']-over_under_result

    #  Some data may be missing.  If so set it to 'Nan'.
    for key in ['Away_OT','Home_OT','Spread','Over_under']:
        if key not in vals:
            vals[key]=float('Nan')
            
    return vals





def date_convert(date_string):
    m,d,y=date_string.split(' ')
    d=d.zfill(2)
    m={'October':'10', 'November':'11', 'December':'12',
       'January':'01', 'February':'02', 'March':'03', 'April':'04'}[m]
    return '{}-{}-{}'.format(y,m,d)

CLEANED_DATA=[]
#  The function 'read_game_string' adds any strings it can't read to 'badly_formatted_games'.
badly_formatted_games=[]
for day,game_strings in zip(date_list,games_by_date):
    day=date_convert(day)
    for game_string in game_strings:
        D=read_game_string(game_string)
        if not D=={}:
            row=(day,D['Away'],D['Away_pts'],D['Home'],D['Home_pts'],D['Away_1st_half'],D['Away_2nd_half'],D['Away_OT'],D['Home_1st_half'],D['Home_2nd_half'],D['Home_OT'],D['Spread'],D['Over_under'])
            CLEANED_DATA.append(row)

CLEANED_DF=pd.DataFrame(CLEANED_DATA,columns=['Date','Away','Away_pts','Home','Home_pts',
                                              'Away_1st_half','Away_2nd_half','Away_OT',
                                              'Home_1st_half','Home_2nd_half','Home_OT',
                                              'Spread','Over_under'])

print(CLEANED_DF.iloc[:10])
print('\n Number of bogus game entries: {}'.format(len(badly_formatted_games)))
CLEANED_DF.to_csv(save,index=False)
for G in badly_formatted_games:
    print(G)
