import pandas as pd
import os
# use pd.csv_read() load file to panads dataframe, column name: ["time","Open","High","Low", "Close"] from ./raw/{file_name}
# add column "symbol" based on file name split by "-", use first part of file name as symbol
# check if any rows missing in dataframe based on time interval, if so, use last row to fill in missing data
#   example:
#   before:
#       2010-01-01 22:00:00,1.43293,1.43287,1.43296,1.43277
#       2010-01-01 22:05:00,1.43294,1.43296,1.43304,1.43281
#       2010-01-01 22:15:00,1.43295,1.43304,1.43305,1.43278
#       2010-01-01 22:20:00,1.43292,1.43294,1.43296,1.43240
# 
#   missing timestamp 2010-01-01 22:10:00 so use last row to fill in missing data
#  after:
#       2010-01-01 22:00:00,1.43293,1.43287,1.43296,1.43277
#       2010-01-01 22:05:00,1.43294,1.43296,1.43304,1.43281
#       2010-01-01 22:10:00,1.43294,1.43296,1.43304,1.43281
#       2010-01-01 22:15:00,1.43295,1.43304,1.43305,1.43278
#       2010-01-01 22:20:00,1.43292,1.43294,1.43296,1.43240
# save dataframe to ./processed/{file_name}

def data_processor(file_name) -> None:
    df = pd.read_csv("./raw/"+file_name, names=["time","Open","High","Low", "Close"])
    symbol = file_name.split("-")[0]
    df["symbol"] = symbol
    df = df.set_index("time")
    df = df.sort_index()
    df = df.asfreq("5T")
    df = df.fillna(method="ffill")
    df.to_csv("./processed/"+file_name)   

def compare_rows(df, index1, index2) -> int: 
    time1 = df.index[index1]
    time2 = df.index[index2]
    return (time2-time1).seconds

# test cases for compare_rows(file_name)
def test_compare_rows(file_name): 
    series = pd.Series([0.0, None, 2.0, 3.0], index=index)
    df = pd.DataFrame({{'s': series}})
    df    
    df = pd.read_csv("./raw/"+file_name, names=["time","Open","High","Low", "Close"])
    symbol = file_name.split("-")[0]
    df["symbol"] = symbol
    df = df.set_index("time")
    df = df.sort_index()
    index = pd.date_range(df["time"], periods=4, freq='T')
    print(df)
    df1 = df.asfreq("5T")
    df = pd.merge(df1,df, left_index=True, right_index=True, how="left")
    print('---------',df)
    # df1 left join df on time
    
    if not os.path.exists("./processed/"):
        os.makedirs("./processed/")

    df.to_csv("./processed/EURUSD-2010_01_01-2012_12_31-test.csv.csv")
    assert compare_rows(df, 0, 1) == 5
    assert compare_rows(df, 0, 2) == 10
    assert compare_rows(df, 0, 3) == 15
    assert compare_rows(df, 0, 4) == 20
    assert compare_rows(df, 0, 5) == 25
    assert compare_rows(df, 0, 6) == 30
    assert compare_rows(df, 0, 7) == 35
    assert compare_rows(df, 0, 8) == 40
    assert compare_rows(df, 0, 9) == 45
    assert compare_rows(df, 0, 10) == 50
    assert compare_rows(df, 0, 11) == 55
    assert compare_rows(df, 0, 12) == 60
    assert compare_rows(df, 0, 13) == 65
    assert compare_rows(df, 0, 14) == 70
    print(df)
    
if __name__ == "__main__": 
    file_name = "EURUSD-2010_01_01-2012_12_31-test.csv"
    test_compare_rows(file_name)
    