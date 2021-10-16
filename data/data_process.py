import os
import sys
import pandas as pd
from finta import TA

def read_csv(file,dt_col_name = 'time'):
    """read csv into df and index on time
    dt_col_name can be any unit from minutes to day. time is the index of pd
    must have pd columns [(time_col),(asset_col), open,close,high,low,day]
    data_process will add additional time information: time(index), minute, hour, weekday, week, month,year, day(since 1970)
    use StopLoss and ProfitTaken to simplify the action,
    feed a fixed StopLoss (SL = 200) and PT = SL * ratio
    action space: [action[0,2],ratio[0,10]]
    rewards is point
    
    add hourly, dayofweek(0-6, Sun-Sat)
    Args:
        file (str): file path/name.csv
    """
    df = pd.read_csv(file)
    df['time'] = pd.to_datetime(df[dt_col_name])
    df.index = df['time']
    df['minute'] =df['time'].dt.minute
    df['hour'] =df['time'].dt.hour
    df['weekday'] = df['time'].dt.dayofweek
    df['week'] = df['time'].dt.isocalendar().week
    df['month'] = df['time'].dt.month
    df['year'] = df['time'].dt.year
    df['day'] = df['time'].dt.day
    # df = df.set_index('time')
    return df 
def tech_indictors(df):
    df['RSI'] = TA.RSI(df)
    df['SMA'] = TA.SMA(df)
    
    #fill NaN to 0
    df = df.fillna(0)
    print(f'--------df head - tail ----------------\n{df.head(3)}\n{df.tail(3)}\n---------------------------------')
    
    return df 
    
def split_timeserious(df, key_ts='time', freq='W', symbol=''):
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
"""
python ./data/data_process.py GBPUSD W ./data/raw/GBPUSD_raw.csv
symbol="GBPUSD"
freq = [H, D, W, M]
file .csv, column names [time, open, high, low, close, vol]
"""
if __name__ == '__main__':
    symbol, freq, file = sys.argv[1],sys.argv[2],sys.argv[3]
    try :
        df = read_csv(file)
    except Exception:
        print(f'No such file or directory: {file}') 
        exit(0)
    df = tech_indictors(df)
    split_timeserious(df,freq=freq, symbol=symbol)