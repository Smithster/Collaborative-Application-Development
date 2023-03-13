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
data = 'data1'

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
eventTypes = pd.Series(eventTypes)
#Data alterations (dropping/altering columns)
data = data.drop(['BookingReference','AttendeeReference',
'IsLeadAttendee','AttendeeGrossCost',
'EventName', 'AttendeeType', 
'BookingStatus','TicketType', 'ClientId'], axis=1)

eventCumulativeData = pd.DataFrame()
for event in events.index:
    eventInstance = data[data.EventId == event].iloc[0]
    eventStart = eventInstance['StartDate']
    eventType = eventInstance['EventType']
    eventName = events.loc[event, 'EventName']
    eventResample = data[data.EventId == event].resample('D', on='StatusCreatedDate').agg({
        'GroupSize': sum
    })
    eventResample.reset_index(inplace=True)
    eventResample['StartDate'] = eventStart
    eventResample['EventType'] = eventType
    eventResample['EventName'] = eventName
    eventResample['Cumulative'] = eventResample.GroupSize.cumsum()
    eventResample['DaysToEvent'] = (eventResample['StartDate'] - eventResample['StatusCreatedDate']).dt.days
    eventResample = eventResample[eventResample.DaysToEvent >= 0]
    eventCumulativeData = pd.concat([eventCumulativeData, eventResample])

endTime = time.time()
processingTime = endTime - startTime
print("Preprocessing Data Complete! Time Taken: " + str(processingTime) + " seconds.")

def getGraphs(dataList = {}, title = '', markers = '.', lineStyle = ''):
    fig = Figure()
    for data in dataList:
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
        ax.plot(dataList[data][0], dataList[data][1], label = data, marker=markers, ls=lineStyle)
    ax.set_title(title)
    ax.legend()
    return fig

def getEventData(EventId, eventFilter=None):
    EventData = data[data.EventId == EventId]
    EventData.drop(['EventId'], axis=1)
    # filterEvent(EventData)
    return EventData

def getEventRangeDays(EventData):
    EventFirst = EventData.sort_values('StatusCreatedDate').iloc(0)
    EventBookingStart = EventFirst['StatusCreatedDate']
    EventStartDate = EventFirst['StartDate']
    return EventStartDate - EventBookingStart

def getSelectCumulative(constraints):
    trainData = eventCumulativeData
    for event in events.index:
        eventName = events.loc[event, 'EventName']
        daysToEvent = constraints['StartDate'] - constraints['FromDate']
        daysToEventMatches = trainData[trainData.DaysToEvent == daysToEvent]
        eventFromDateData = daysToEventMatches[daysToEventMatches.EventName == eventName]
        trainData.loc[trainData.EventName == eventName, 'FromCumulative'] = eventFromDateData['Cumulative']
    return trainData

def getTrainData(constraints):
    trainData = getSelectCumulative(constraints)
    trainx = trainData[['StatusCreatedDate', 'EventName', 'EventType', 'StartDate', 'DaysToEvent', 'FromCumulative']]
    trainy = trainData[['GroupSize', 'Cumulative']]
    return trainx, trainy

def getTestData(constraints):
    testx = pd.DataFrame()
    testx['StatusCreatedDate'] = pd.date_range(constraints['FromDate'], constraints['StartDate'],
    freq='D')
    testx['EventName'] = constraints['EventName']
    testx['EventType'] = constraints['EventType']
    testx['StartDate'] = constraints['StartDate']
    testx['DaysToEvent'] = 0
    testx['FromCumulative'] = constraints['GroupSize']
    startCum = int(constraints['GroupSize'])
    for i in range(len(testx.index)):
        testx.loc[i, 'DaysToEvent'] = len(testx.index) - i
    return testx

def getPrediction(constraints):

    startTime = time.time()
    print("Starting prediction...")
    print("Gathering data...")
    trainx, trainy = getTrainData(constraints)
    testx = getTestData(constraints)
    
    x = testx['StatusCreatedDate']

    print("Encoding data for fitting...")
    encoder = LabelEncoder()
    for data in [trainx, testx]:
        for column in data.columns:
            data[column] = encoder.fit_transform(data[column])


    mod = xgb.XGBRegressor(base_score=0.5, booster='gbtree', n_estimators=1000, early_stopping_rounds=50, objective='reg:linear', max_depth=3, learning_rate=0.01)
    print("Creating regressor model...")
    # mod = RandomForestRegressor()

    trainx, traintestx, trainy, traintesty = train_test_split(trainx, trainy, test_size=0.3, random_state=42)

    mod.fit(trainx, trainy, eval_set=[(trainx, trainy), (traintestx, traintesty)], verbose = 100)

    print("Making predictions...")
    y = mod.predict(testx)

    groupSizePrediction = []
    cumulativePrediction = []

    for pair in y:
        groupSizePrediction.append(pair[0])
        cumulativePrediction.append(pair[1])
    
    # print(y)
    endTime = time.time()
    print(f'Done! Time taken was {endTime - startTime} seconds.')

    return getGraphs(dataList = {'Predicted Bookings' : [x, groupSizePrediction], 'Predicted Cumulative' : [x, cumulativePrediction]}, title = constraints['EventName'], lineStyle = '-', markers = '')

def invalidConstraint(constraints, constraint):
    if constraints[constraint] in ['', None, 'Null', 'NaN']:
        return True
    if constraint == 'bookings':
        if not constraints['bookings'].isNumeric():
            return True
    if constraint in ['startDate', 'bookingStart', 'fromDate']:
        try:
            pd.to_datetime(constraints[constraint])
        except:
            return True
    if constraint == 'eventType':
        if constraints[constraint] not in eventTypes:
            return True
    return False

########################################
#  PREVIOUS ANALYTICS CODE DOWN BELOW  #
########################################

# def getTrainData(constraints):
#     trainData = data
#     for constraint in contraints:
#         if invalidConstraint(constraints, constraint):
#             continue
#         trainData = trainData[constraint == constraints[constraint]]
#     return trainData

# def getTDeltaBookings():
#     diffList = []
#     bookingList= []
#     for eventId in events.index:
#         event = getEventData(eventId)
#         diffList, bookingList = getEventTDBookings(event, diffList, bookingList)

#     #Produce a plot of the events bookings with respect to how long the event had bookings
#     return getGraphs(dataList={'Bookings': [diffList, bookingList]})


# def getEventTDBookings(event, diffList, bookingList):

#     #Sets the datetime of the first booking and last booking
#     firstSaleDate = event.StatusCreatedDate.iloc[0]
#     lastSaleDate = event.StatusCreatedDate.iloc[-1]

#     #Finds the difference in datetime of the first and last booking
#     dateDiff = pd.to_datetime(lastSaleDate) - pd.to_datetime(firstSaleDate)

#     #Append to the list of data points for the event
#     diffList.append(dateDiff.days)
#     bookingList.append(event.GroupSize.sum())

#     return diffList, bookingList

# def getEventData(event):

#     #Select event from event data
#     eventData = data[data.EventId == event]

#     return eventData

# def getEventTypeDTime():
#     for eventType in eventTypes:
#         eventTypeData = data[data.EventType == eventType]
#         eventTypeData = eventTypeData[['EventId', 'GroupSize', 'StatusCreatedDate']]
#         x = []
#         y = []
#         for eventId in eventTypeData['EventId'].unique():
#             eventData = eventTypeData[eventTypeData.EventId == eventId].sort_values('StatusCreatedDate')
#             startTime = eventData['StatusCreatedDate'].iloc[0]
#             endTime = eventData['StatusCreatedDate'].iloc[-1]
#             dTime = (endTime - startTime).days
#             bookings = eventData.GroupSize.sum()
#             x.append(dTime)
#             y.append(bookings)
#         return getGraphs(dataList = {'Bookings': [x, y]}, lineStyle = '', markers = '.', title = f'{eventType} Delta Time Bookings') 

# def getEventWeekly():
#     for eventId in events.index:
#         event = data[data.EventId == eventId]
#         #Decides if the event should be plotted or ignored
#         if not getFilter(event):
#             continue
#         #Resample the data into weekly groups
#         event = event.resample('W', on='StatusCreatedDate').sum(numeric_only=True)
#         #Graphs for weekly results
#         x, y, y2 = event.index, event.GroupSize, event.GroupSize.cumsum()
#         graph1Args = [x, y]
#         graph2Args = [x, y2]
#         getGraphs(dataList={'Week Sales': graph1Args, 'Cumulative Sales': graph2Args}, \
#             title=events.at[eventId, 'EventName'])

