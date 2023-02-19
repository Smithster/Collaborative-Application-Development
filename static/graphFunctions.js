const test = () => {
  bookings = document.getElementById('bookings').value
  startDate = document.getElementById('startDate').value
  bookingOpen = document.getElementById('bookingStart').value
  fromDate = document.getElementById('fromDate').value
  eventType = document.getElementById('eventType').value

  if (fromDate == ''){fromDate = new Date()}

  constraints = {
    'bookings' : bookings,
    'startDate' : startDate,
    'bookingStart' : bookingStart,
    'fromDate' : fromDate,
    'eventType' : eventType
  }

  fetch(`/prediction/${JSON.stringify(constraints)}`)
  .then(response => response.blob())
  .then(imgBlob => {
      const imageUrl = URL.createObjectURL(imgBlob);
      graph = document.getElementById("graph")
      graph.src = imageUrl
  });
};