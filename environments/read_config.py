import json

class EnvConfig():
    def __init__(self,config_file ='./data/config/gdbusd-test-1.json') -> None:
        self.config = {}
        with open(config_file) as j: 
            self.config = json.load(j)

    def env_parameters(self,item=''):    
        if item:
            return self.config["env"][item]
        else:
            return self.config["env"]
        
    def symbol(self, asset="GBPUSD", item='') :
        if item:
            return self.config["symbol"][asset][item]
        else:
            return self.config["symbol"][asset]
        
    def trading_hour(self,place="NewYork"):
        if place:
            return self.config["trading_hour"][place]
        else:
            return self.config["trading_hour"]
    
if __name__ == '__main__':
    cf = EnvConfig()
    print(f'{cf.env_parameters()}')
    print(cf.env_parameters("observation_list"))
    print(f'asset_col: {cf.env_parameters()["asset_col"]}')
    print(cf.symbol(asset="GBPUSD")["point"])
    print(f'trading hour new york: {cf.trading_hour("new york")}')