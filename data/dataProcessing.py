import sqlite3
import pandas as pd
import time


def initDatabase():
    startTime = time.time()

    #Connect (or create) SQL database
    con = sqlite3.connect('data/database.db')

    data1 = pd.DataFrame(data=pd.read_csv("data/ORG01-01082021-31072022.csv"))
    merged = pd.DataFrame(data=pd.read_csv("data/merged.csv"))

    dataList = [data1, merged]

    # Data cleansing and pre-processing for event type column for useability from front end
    for data in dataList:
        data.drop_duplicates(inplace=True)
        data.EventType = data.EventType.fillna('Other Events')
        data.EventType = data.EventType.str.strip()
        data.EventType = data.EventType.str.replace('/', 'or')

    # data gets stored in SQLite database
    data1.to_sql('data1', con, if_exists='replace', index=False)
    merged.to_sql('merged', con, if_exists='replace', index=False)
    endTime = time.time()
    dTime = endTime - startTime
    print(f"Setting up data took {dTime} seconds")


# when needed, data gets called from the database
def getTable(index='data1'):
    con = sqlite3.connect('data/database.db')
    data = pd.read_sql(f'SELECT * FROM {index}', con, index_col=None)
    data['StatusCreatedDate'] = pd.to_datetime(data['StatusCreatedDate'],
                                               errors='coerce')
    data['StartDate'] = pd.to_datetime(data['StartDate'], errors='coerce')
    return data
