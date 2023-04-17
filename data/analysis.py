import time
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import sklearn
import data.dataProcessing as dataProcessing
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

#Limiting variables for results
data = 'merged'

startTime = time.time()
print("Starting...")

try:
    data = dataProcessing.getTable(data)
except:
    dataProcessing.initDatabase()
    data = dataProcessing.getTable(data)

#Organise the data by the datetime value of each order
data = data.sort_values('StatusCreatedDate')

#Making a list of events with event names
events = data[['EventName', 'EventId', 'EventType']]
events = events.groupby('EventId').first()

#Making list of event type Ids
eventTypes = data.EventType.unique()
eventTypes = pd.DataFrame({'EventType': eventTypes})
eventTypes['TypeID'] = eventTypes.index

eventTypes.set_index('EventType', inplace=True)

#Data alterations (dropping/altering columns)
data = data.drop([
    'BookingReference', 'AttendeeReference', 'IsLeadAttendee',
    'AttendeeGrossCost', 'EventName', 'AttendeeType', 'BookingStatus',
    'TicketType', 'ClientId'
],
                 axis=1)

eventCumulativeData = pd.DataFrame()
for event in events.index:
    eventInstance = data[data.EventId == event].iloc[0]
    eventStart = eventInstance['StartDate']
    eventType = eventTypes.loc[eventInstance['EventType'], 'TypeID']
    eventResample = data[data.EventId == event].resample(
        'D', on='StatusCreatedDate').agg({'GroupSize': sum})
    eventResample.reset_index(inplace=True)
    eventResample['StartDate'] = eventStart
    eventResample['EventType'] = eventType
    eventResample['EventId'] = event
    eventResample['Cumulative'] = eventResample.GroupSize.cumsum()
    eventResample['DaysToEvent'] = (eventResample['StartDate'] -
                                    eventResample['StatusCreatedDate']).dt.days
    eventResample = eventResample[eventResample.DaysToEvent >= 0]
    eventCumulativeData = pd.concat([eventCumulativeData, eventResample])

eventCumulativeData['StatusCreatedDay'] = eventCumulativeData[
    'StatusCreatedDate'].dt.day
eventCumulativeData['StatusCreatedMonth'] = eventCumulativeData[
    'StatusCreatedDate'].dt.month
eventCumulativeData['StatusCreatedYear'] = eventCumulativeData[
    'StatusCreatedDate'].dt.year
eventCumulativeData['StatusCreatedWeekday'] = eventCumulativeData[
    'StatusCreatedDate'].dt.weekday
eventCumulativeData['StartDay'] = eventCumulativeData['StartDate'].dt.day
eventCumulativeData['StartMonth'] = eventCumulativeData['StartDate'].dt.month
eventCumulativeData['StartYear'] = eventCumulativeData['StartDate'].dt.year
eventCumulativeData['StartWeekday'] = eventCumulativeData[
    'StartDate'].dt.weekday
eventCumulativeData.drop(['StartDate', 'StatusCreatedDate'],
                         axis=1,
                         inplace=True)
print(eventCumulativeData.info())

endTime = time.time()
processingTime = endTime - startTime
print(
    f"Preprocessing Data Complete! Time Taken: {str(processingTime)} seconds.")


def getGraph(dataList={}, title='', markers='.', lineStyle=''):
    fig = Figure()
    ax = fig.add_subplot()
    for data in dataList:
        ax.plot(dataList[data][0],
                dataList[data][1],
                label=data,
                marker=markers,
                ls=lineStyle)
    ax.set_title(title)
    ax.legend()
    return fig


def getSelectCumulative(constraints):
    cumData = eventCumulativeData.copy(deep=True)
    daysToEvent = (constraints['StartDate'] - constraints['FromDate']).days
    print(cumData[cumData.DaysToEvent == daysToEvent])
    daysToEventMatches = cumData[cumData.DaysToEvent == daysToEvent]

    cumData['FromCumulative'] = None
    for event in daysToEventMatches['EventId']:
        cumData.loc[cumData.EventId == event, 'FromCumulative'] = cumData.loc[
            (cumData.EventId == event) & (cumData.DaysToEvent == daysToEvent),
            'Cumulative']

    cumData.dropna(inplace=True)
    cumData['FromCumulative'] = cumData['FromCumulative'].astype('int')
    print(cumData.info())
    return cumData


def getTrainData(constraints):
    trainData = getSelectCumulative(constraints)
    trainx = trainData[[
        'StatusCreatedDay', 'StatusCreatedMonth', 'StatusCreatedYear',
        'StatusCreatedWeekday', 'EventId', 'EventType', 'StartDay',
        'StartMonth', 'StartYear', 'StartWeekday', 'DaysToEvent',
        'FromCumulative'
    ]]
    trainy = trainData['GroupSize']
    return trainx, trainy


def getTestData(constraints):
    testx = pd.DataFrame()
    testx['StatusCreatedDate'] = pd.date_range(constraints['FromDate'],
                                               constraints['StartDate'],
                                               freq='D')
    testx['StatusCreatedDay'] = testx['StatusCreatedDate'].dt.day
    testx['StatusCreatedMonth'] = testx['StatusCreatedDate'].dt.month
    testx['StatusCreatedYear'] = testx['StatusCreatedDate'].dt.year
    testx['StatusCreatedWeekday'] = testx['StatusCreatedDate'].dt.weekday
    testx['EventId'] = data.EventId.max() + 1
    testx['EventType'] = eventTypes.loc[constraints['EventType'], 'TypeID']
    testx['StartDay'] = constraints['StartDate'].day
    testx['StartMonth'] = constraints['StartDate'].month
    testx['StartYear'] = constraints['StartDate'].year
    testx['StartWeekday'] = constraints['StartDate'].weekday()

    graphx = testx['StatusCreatedDate']

    testx.drop(['StatusCreatedDate'], axis=1, inplace=True)

    testx['DaysToEvent'] = 0
    testx['FromCumulative'] = constraints['GroupSize']
    testx['FromCumulative'] = testx['FromCumulative'].astype('int')
    startCum = int(constraints['GroupSize'])
    for i in range(len(testx.index)):
        testx.loc[i, 'DaysToEvent'] = len(testx.index) - i
    return testx, graphx


def getPrediction(constraints):
    print(eventCumulativeData.info())
    startTime = time.time()
    print("Starting prediction...")
    print("Gathering data...")
    trainx, trainy = getTrainData(constraints)
    testx, x = getTestData(constraints)

    # print("Encoding data for fitting...")
    # encoder = LabelEncoder()
    # for data in [trainx, testx]:
    #     for column in data.columns:
    #         data[column] = encoder.fit_transform(data[column])

    # TODO might need this
    trainx, traintestx, trainy, traintesty = train_test_split(trainx,
                                                              trainy,
                                                              test_size=0.3,
                                                              random_state=42)

    print(trainy, traintesty)

    mod = xgb.XGBRegressor(base_score=0.5,
                           booster='gbtree',
                           n_estimators=1000,
                           early_stopping_rounds=50,
                           objective='reg:linear',
                           max_depth=3,
                           learning_rate=0.01)
    print("Creating regressor model...")

    mod.fit(trainx,
            trainy,
            eval_set=[(trainx, trainy), (traintestx, traintesty)],
            verbose=100)

    print("Making predictions...")
    y = mod.predict(testx)

    print(trainx.info(), trainy.info())

    print('testx.info()', testx.info())

    #TODO or alternatively use this
    # mod = RandomForestRegressor(n_estimators=1000)
    # print(f'creating regressor model...')
    # mod.fit(trainx, trainy)
    # print(f'making predictions...')
    # y = mod.predict(testx)

    groupSizePrediction = y
    print(y.cumsum()[-1], constraints['GroupSize'])
    cumulativePrediction = int(y.cumsum()[-1]) + int(constraints['GroupSize'])

    endTime = time.time()
    print(f'Done! Time taken was {endTime - startTime} seconds.')

    return getGraph(
        dataList={
            'Predicted Bookings': [x, groupSizePrediction],
        },
        title=
        f'{constraints["EventName"]}, Cumulative bookings: {cumulativePrediction}',
        lineStyle='-',
        markers='')


def getEventTypes():
    eventTypesList = []
    for eventType in eventTypes.index:
        eventTypesList.append(eventType)
    return eventTypesList
