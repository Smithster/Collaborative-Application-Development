import time
import pandas as pd
from matplotlib import pyplot as plt
import sqlite3
# import data.dataProcessing as dataProcessing
import data.dataProcessing as dataProcessing

#Limiting variables for results
maxGraphs = 2
data = 'data1'

#Change filter conditions for events
def getFilter(event):
    conditions = [
        event.GroupSize.sum() < 10
    ]
    return all(conditions)

startTime = time.time()
print("Starting...")

#Variables for storage
graphCount = 0

try:    
    data = dataProcessing.getTable(data)
except:
    dataProcessing.initDatabase()
    data = dataProcessing.getTable(data)

#Organise the data by the dateimte value of each order
data = data.sort_values('StatusCreatedDate')
#Making a list of events with event names
events = data[['EventName', 'EventId', 'EventType']]
events = events.groupby('EventId').first()
#Making list of event type Ids
eventTypes = data.EventType.unique()
eventTypes = pd.Series(eventTypes)
#Data alterations (dropping/altering columns)
data = data.drop(['BookingReference','AttendeeReference','IsLeadAttendee','AttendeeGrossCost','EventName'], axis=1)

endTime = time.time()
processingTime = endTime - startTime
print("Preprocessing Data Complete! Time Taken: " + str(processingTime) + " seconds.")

def giveEventWeekly():
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
        giveGraphs(dataList={'Week Sales': graph1Args, 'Cumulative Sales': graph2Args}, \
            title=events.at[eventId, 'EventName'])

def giveGraphs(dataList = {}, title = '', markers = '.', lineStyle = ''):
    global graphCount
    if graphCount > maxGraphs:
        return
    for data in dataList:
        fig, ax = plt.subplots()
        ax.plot(dataList[data][0], dataList[data][1], label = data, marker=markers, ls=lineStyle)
    ax.set_title(title)
    ax.legend()
    graphCount += 1
    print("this is a test")
    return fig
    

def giveTDeltaBookings():
    diffList = []
    bookingList= []
    for eventId in events.index:
        event = getEventData(eventId)
        diffList, bookingList = giveEventTDBookings(event, diffList, bookingList)

    #Produce a plot of the events bookings with respect to how long the event had bookings
    return giveGraphs(dataList={'Bookings': [diffList, bookingList]})


def giveEventTDBookings(event, diffList, bookingList):

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
        return giveGraphs(dataList = {'Bookings': [x, y]}, lineStyle = '', markers = '.', title = f'{eventType} Delta Time Bookings')

#giveTDeltaBookings()
#giveEventWeekly()
#getEventTypeDTime()