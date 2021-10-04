import os
import datetime as dt
import pandas as pd
from finta import TA

def read_csv(file,ts_index = 'time'):
    """read csv into df and index on time
    add hourly, dayofweek(0-6, Sun-Sat)
    Args:
        file (str): file path/name.csv
    """
    df = pd.read_csv(file)
    df['datetime'] = pd.to_datetime(df['time'])
    df.index = df['datetime']
    df['minute'] =df['datetime'].dt.minute
    df['hour'] =df['datetime'].dt.hour
    df['weekday'] = df['datetime'].dt.dayofweek
    df['week'] = df['datetime'].dt.isocalendar().week
    df['month'] = df['datetime'].dt.month
    df['year'] = df['datetime'].dt.year
    # df = df.set_index('time')
    return df 
def tech_indictors(df):
    df['RSI'] = TA.RSI(df)
    df['SMA'] = TA.SMA(df)
    
    #fill NaN to 0
    df = df.fillna(0)
    print(f'--------df head ----------------\n{df.head(10000)}\n---------------------------------')
    
    return df 
    
def split_timeserious(df, key_ts='datetime', freq='W', symbol='GBPUSD', path=''):
    """import df and split into hour, daily, weekly, monthly based and 
    save into subfolder

    Args:
        df (pandas df with timestamp is part of multi index): 
        spliter (str): H, D, W, M, Y
    """
    
    freq_name = {'H':'hourly','D':'daily','W':'weekly','M':'monthly','Y':'Yearly'}
    count = 0
    for n, g in df.groupby(pd.Grouper(level=key_ts,freq=freq)):
        p =f'./data/split/{symbol}/{freq_name[freq]}'
        os.makedirs(p, exist_ok=True)
        fname = f'{symbol}_{n:%Y%m%d}_{freq}_{count}.csv'
        fn = f'{p}/{fname}'
        print(f'save to:{fn}')
        g.to_csv(fn)
        count += 1
    return 

file = './data/raw.csv'
df = read_csv(file)
df = tech_indictors(df)
split_timeserious(df,freq='D')