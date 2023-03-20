########################################
#  PREVIOUS ANALYTICS CODE DOWN BELOW  #
########################################

def getTrainData(constraints):
    trainData = data
    for constraint in contraints:
        if invalidConstraint(constraints, constraint):
            continue
        trainData = trainData[constraint == constraints[constraint]]
    return trainData

def getTDeltaBookings():
    diffList = []
    bookingList= []
    for eventId in events.index:
        event = getEventData(eventId)
        diffList, bookingList = getEventTDBookings(event, diffList, bookingList)

    #Produce a plot of the events bookings with respect to how long the event had bookings
    return getGraphs(dataList={'Bookings': [diffList, bookingList]})


def getEventTDBookings(event, diffList, bookingList):

    #Sets the datetime of the first booking and last booking
    firstSaleDate = event.StatusCreatedDate.iloc[0]
    lastSaleDate = event.StatusCreatedDate.iloc[-1]

    #Finds the difference in datetime of the first and last booking
    dateDiff = pd.to_datetime(lastSaleDate) - pd.to_datetime(firstSaleDate)

    #Append to the list of data points for the event
    diffList.append(dateDiff.days)
    bookingList.append(event.GroupSize.sum())

    return diffList, bookingList

def getEventData(event):

    #Select event from event data
    eventData = data[data.EventId == event]

    return eventData

def getEventTypeDTime():
    for eventType in eventTypes:
        eventTypeData = data[data.EventType == eventType]
        eventTypeData = eventTypeData[['EventId', 'GroupSize', 'StatusCreatedDate']]
        x = []
        y = []
        for eventId in eventTypeData['EventId'].unique():
            eventData = eventTypeData[eventTypeData.EventId == eventId].sort_values('StatusCreatedDate')
            startTime = eventData['StatusCreatedDate'].iloc[0]
            endTime = eventData['StatusCreatedDate'].iloc[-1]
            dTime = (endTime - startTime).days
            bookings = eventData.GroupSize.sum()
            x.append(dTime)
            y.append(bookings)
        return getGraphs(dataList = {'Bookings': [x, y]}, lineStyle = '', markers = '.', title = f'{eventType} Delta Time Bookings') 

def getEventWeekly():
    for eventId in events.index:
        event = data[data.EventId == eventId]
        #Decides if the event should be plotted or ignored
        if not getFilter(event):
            continue
        #Resample the data into weekly groups
        event = event.resample('W', on='StatusCreatedDate').sum(numeric_only=True)
        #Graphs for weekly results
        x, y, y2 = event.index, event.GroupSize, event.GroupSize.cumsum()
        graph1Args = [x, y]
        graph2Args = [x, y2]
        getGraphs(dataList={'Week Sales': graph1Args, 'Cumulative Sales': graph2Args}, \
            title=events.at[eventId, 'EventName'])