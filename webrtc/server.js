var express = require('express');
var http = require('http');
var path = require('path');
var WebSocket = require('ws');

var app = express();
app.use(express.static(path.join(__dirname, 'html')));

const server = http.createServer(app);
const wss = new WebSocket.Server({ server });


wss.on('connection', function connection(ws) {
	console.log('Connected client');
  	ws.on('message', function incoming(message) {
	    console.log('received: %s', message);
	    wss.clients.forEach(function each(client) {
    		client.send(message);
  		});
  	});
});

server.listen(8800, function listening() {
  console.log('Listening on %d', server.address().port);
});