const test = () => {
  fetch("127.0.0.1:5000/DTBookings").then((img) => {
    img = new Blob([img], "image/png")
    
  });
};