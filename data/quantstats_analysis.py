import pandas as pd
import quantstats as qs

def quantstats_analysis(env, df, rl_name, start_index, end_index):
    qs.extend_pandas()
    net_worth = pd.Series(env.history['total_profit'], index=df.index[start_index+1:end_index])
    returns = net_worth.pct_change().iloc[1:]
    qs.reports.full(returns)
    qs.reports.html(returns, output=f'./data/result_analysis/{rl_name}_quantstats.html')