const test = () => {
  EventName = document.getElementById('EventName').value
  GroupSize = document.getElementById('GroupSize').value
  StartDate = document.getElementById('StartDate').value
  StartBookings = document.getElementById('StartBookings').value
  FromDate = document.getElementById('FromDate').value
  eventType = document.getElementById('EventType').value
  
  if (FromDate == ''){FromDate = new Date()}

  constraints = {
    'EventName' : EventName,
    'GroupSize' : GroupSize,
    'StartDate' : StartDate,
    'StartBookings' : StartBookings,
    'FromDate' : FromDate,
    'EventType' : eventType
  }

  fetch(`/prediction/${JSON.stringify(constraints)}`)
  .then(response => response.blob())
  .then(imgBlob => {
    const imageUrl = URL.createObjectURL(imgBlob);
    graph = document.getElementById("graph")
    graph.src = imageUrl
  }).catch((error) => {
    console.log(error)
  });
};

const getEventTypes = () => {
  fetch('/getEventTypes')
  .then(response => response.json())
  .then(eventTypes => {
    eventTypes.forEach(eventType => {
      eventTypeOption = document.createElement("option")
      eventTypeOption.innerHTML = eventType
      document.getElementById("EventType").appendChild(eventTypeOption)
    });
  }).catch((error) => {
    console.log(error)
  });
}

getEventTypes()