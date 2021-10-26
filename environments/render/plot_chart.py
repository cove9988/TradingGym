import mplfinance as mpf
import pandas as pd
import datetime

class TradingChart():
    """An ohlc trading visualization using matplotlib made to render tgym environment"""
    def __init__(self, df, transaction_history, **kwargs):
        self.ohlc = df[['time','open','high','low','close','symbol']].copy
        self.ohlc = self.ohlc.rename(columns={'time':'Date','open':'Open','high':'High','low':'Low','close':'Close'})
        self.ohlc.index = pd.DatetimeIndex(self.ohlc['Date'])
        self.transaction_history = transaction_history
        self.parameters = {"figscale":6.0,"style":"nightclouds", "type":"hollow_and_filled", "warn_too_much_data":2000 }
        self.symbols = self.ohlc['symbol'].unique()
    def transaction_line(self, symbol):
        _lines=[]
        _colors=[]

        for tr in self.transaction_history:
            if tr["Symbol"] == symbol :   
                if tr['ClosePrice'] > 0 :
                    if tr['Type'] == 0 :
                        if tr['Reward'] > 0 :
                            _lines.append([(tr['ActionTime'],tr['ActionPrice']),(tr['CloseTime'],tr['ClosePrice'])])
                            _colors.append('c')
                            
                        else:
                            _lines.append([(tr['ActionTime'],tr['ActionPrice']),(tr['CloseTime'],tr['ClosePrice'])])
                            _colors.append('r')
                    elif tr['Type'] == 1 :
                        if tr['Reward'] > 0 :
                            _lines.append([(tr['ActionTime'],tr['ActionPrice']),(tr['CloseTime'],tr['ClosePrice'])])
                            _colors.append('b')
                        else:
                            _lines.append([(tr['ActionTime'],tr['ActionPrice']),(tr['CloseTime'],tr['ClosePrice'])])
                            _colors.append('k')
        return _lines, _colors
    
    def plot(self,symbol=''):
        if symbol: 
            _lines, _colors = self.transaction_line(symbol)
            _seq = dict(alines=_lines, colors=_colors)
            _ohlc = self.ohlc[['symbol'==symbol]]
            mpf.plot(_ohlc, alines=_seq, **self.parameters, savefig=f'./data/config/{s}-{datetime.datetime.now().strftime("%Y%m%d%H%M%S"}')
        else:            
            for s in self.symbols:
                _lines, _colors = self.transaction_line(s)
                _seq = dict(alines=_lines, colors=_colors)
                _ohlc = self.ohlc[['symbol' == s]]
                mpf.plot(_ohlc, alines=_seq, **self.parameters, savefig=f'./data/config/{s}-{datetime.datetime.now().strftime("%Y%m%d%H%M%S"}')
        