import pandas as pd
from forex_trading import tgym
from finrl import StockTradingEnvV2
parameters = {
"observation_list":["open","high","low","close","minute","hour","weekday","week","month","year","RSI","SMA"],
}
file = "./data/split/GBPUSD/weekly/GBPUSD_20191110_W_148.csv"
df = pd.read_csv(file)
t = StockTradingEnvV2(df, daily_information_cols=parameters,date_col_name="time")