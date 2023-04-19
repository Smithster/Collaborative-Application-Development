import time
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import data.dataProcessing as dataProcessing
import xgboost as xgb
from sklearn.model_selection import train_test_split

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

#Making a dataframe for cumulative data of events
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

# replacing dates with day, month, year and weekday values
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

# this is just timing how long it takes for the server to start
endTime = time.time()
processingTime = endTime - startTime
print(
    f"Preprocessing Data Complete! Time Taken: {str(processingTime)} seconds.")


# function to produce graphs, created so that it
# wouldn't have to be recoded every time we wanted a graph
def getGraph(dataList={},
             title='',
             markers='.',
             lineStyle='',
             xLabel='',
             yLabel='',
             legend=False):
    fig = Figure()
    ax = fig.add_subplot()
    for data in dataList:
        ax.plot(
            dataList[data][0],
            dataList[data][1],
            label=data,
            marker=markers,
            ls=lineStyle,
        )
        ax.locator_params(nbins=3)
        ax.tick_params('x', labelrotation=25)
        ax.set_xlabel(xLabel)
        ax.set_ylabel(yLabel)
    ax.set_title(title)
    if legend:
        ax.legend()
    return fig


# Gets cumulative values for the events where the days to event is equal to the days to event from the user input
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


#Gathers information from the data to train the regressor
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


# uses the constraints from the user to create the test data for predictions
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
    print(eventTypes, constraints['EventType'])
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


# call to start making a prediction, starts with gathering all required information
def getPrediction(constraints):
    print(eventCumulativeData.info())
    startTime = time.time()
    print("Starting prediction...")
    print("Gathering data...")
    trainx, trainy = getTrainData(constraints)
    testx, x = getTestData(constraints)

    # seperating the data randomly to train the regressor
    trainx, traintestx, trainy, traintesty = train_test_split(trainx,
                                                              trainy,
                                                              test_size=0.3,
                                                              random_state=42)

    print(trainy, traintesty)

    # Create and fit the regressor model
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

    # Generate predictions using the test data
    print("Making predictions...")
    y = mod.predict(testx)

    #TODO or alternatively use this
    # mod = RandomForestRegressor(n_estimators=1000)
    # print(f'creating regressor model...')
    # mod.fit(trainx, trainy)
    # print(f'making predictions...')
    # y = mod.predict(testx)

    groupSizePrediction = y
    cumulativePrediction = int(y.cumsum()[-1]) + int(constraints['GroupSize'])

    endTime = time.time()
    print(f'Done! Time taken was {endTime - startTime} seconds.')

    # finish by returning a graph to the web app
    return getGraph(
        dataList={
            'Predicted Bookings': [x, groupSizePrediction],
        },
        title=
        f'{constraints["EventName"]}, Cumulative bookings: {cumulativePrediction}',
        lineStyle='-',
        markers='',
        xLabel='Date',
        yLabel='Predicted bookings (for the day)')


# This is just used by the web app to gather event types for the select input
def getEventTypes():
    eventTypesList = []
    for eventType in eventTypes.index:
        eventTypesList.append(eventType)
    return eventTypesList
