class ActionEnum(enumerate):
    """
    Enum for action space
    :param enumerate: Enumerate class
    """
    HOLD = 0
    BUY = 1
    SELL = 2
    EXIT = 3

class Folder(enumerate):
    """
    Enum for folder
    :param enumerate: Enumerate class
    """
    MODEL = 'data/models/'
    LOG = 'data/log/'
    TENSORBOARD = 'data/tensorboard/'
    DATA_WEEKLY_GBPUSD = 'data/split/GBPUSD/weekly/'
    DATA_WEEKLY_EURUSD = 'data/split/EURUSD/weekly/'
    DATA_WEEKLY_USDJPY = 'data/split/USDJPY/weekly/'
    DATA_WEEKLY_AUDUSD = 'data/split/AUDUSD/weekly/'
    DATA_WEEKLY_NZDUSD = 'data/split/NZDUSD/weekly/'
    DATA_WEEKLY_USDCAD = 'data/split/USDCAD/weekly/'
    DATA_WEEKLY_USDCHF = 'data/split/USDCHF/weekly/'
    DATA_WEEKLY_GBPJPY = 'data/split/GBPJPY/weekly/'
    DATA_WEEKLY_EURJPY = 'data/split/EURJPY/weekly/'

def form_action(action):
    """
    Form action from action space
    :param action: action space
    """
    expected_action = 0.995
    r = 0.0
    if action <= -expected_action:
        r =-(action + 0.5) * 2
        return ActionEnum.SELL, r, "SELL"
    elif action >= +expected_action:
        r = (action - 0.5) * 2
        return ActionEnum.BUY, r, "BUY"   
    else:
        return ActionEnum.HOLD, r, "NIL"

def normalize(x,min, max):
    """
    Scale [min, max] to [0, 1]
    Normalize x to [min, max] 
    :param x: input value
    :param min: min value
    :param max: max value
    """
    return (x - min) / (max - min)    
    