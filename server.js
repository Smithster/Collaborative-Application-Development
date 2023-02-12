const http = require('http');
const fs = require('fs');

const hostname = '127.0.0.1';
const port = 7777;

const server = http.createServer((req, res) => {
    fs.readFile('static/graphPage.html', (err, data) =>{
        res.statusCode = 200;
        res.setHeader('Content-Type', 'text/html')
        res.write(data);
    });
});

server.listen(port, hostname, () => {
    console.log(`Server running at http://${hostname}:${port}/`);
});
