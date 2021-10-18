# from gym.envs.registration import register
# from copy import deepcopy

# from . import data 

# df = data.USDGBP5M
# size = 40
# register(
#     id='forex-trading-v0',
#     entry_point='tradinggym.env:tgym',
#     kwargs={'df': deepcopy(df),
#             'window_size':size,
#             'frame_bound':(size,len(df))}
# )