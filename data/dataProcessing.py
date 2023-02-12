import sqlite3
import pandas as pd
import time

def initDatabase():
    startTime = time.time()

    #Connect (or create) SQL database
    con = sqlite3.connect('data/database.db')

    data1 = pd.DataFrame(data=pd.read_csv("data/ORG01-01082021-31072022.csv"))
    data2 = pd.DataFrame(data=pd.read_csv("data/ORG02-24112017-25012023.csv"))
    data3 = pd.DataFrame(data=pd.read_csv("data/ORG03-24112017-25012023.csv"))

    dataList = [data1, data2, data3]

    for data in dataList:
        data.drop_duplicates(inplace=True)
        data['StatusCreatedDate'] = pd.to_datetime(data['StatusCreatedDate'], errors='coerce')
        data['StartDate'] = pd.to_datetime(data['StartDate'], errors='coerce')

    data1.to_sql('data1', con, if_exists = 'replace', index = False)
    data2.to_sql('data2', con, if_exists = 'replace', index = False)
    data3.to_sql('data3', con, if_exists = 'replace', index = False)

    endTime = time.time()
    dTime = endTime - startTime
    print(f"Setting up data took {dTime} seconds")

def getTable(index = 'data1'):
    con = sqlite3.connect('data/database.db')
    data = pd.read_sql(f'SELECT * FROM {index}', con)
    return data


