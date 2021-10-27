var http = require('http'),
	fs = require('fs'),
	socket = require('socket.io'),
	osc = require('node-osc');

// https://socket.io/get-started/chat


console.log("go to http://localhost:8080 in your web browser.");

const server = http.createServer((req, res) => {
	// res.setHeader("Access-Control-Allow-Origin", "*");
	// res.setHeader("Access-Control-Allow-Headers", "X-Requested-With");
	// res.setHeader("Access-Control-Allow-Headers", "Content-Type");
	// res.setHeader("Access-Control-Allow-Methods", "PUT, GET, POST, DELETE, OPTIONS");
	let url = ''
	if (req.url === '/') {
		url = '/index.html'
	} else {
		url = req.url
	}
	fs.readFile(__dirname + url, function( err, data ) {
		if( err ) {
			res.writeHead( 500 );
			return res.end('Error loading index.html');
		}

		res.writeHead( 200 );
		res.end( data );
	});
})

var isConnected = false;

var oscServer, oscClient
var io = socket(server)

io.sockets.on('connection', function (socket) {
	socket.on("config", function (obj) {
    	oscServer = new osc.Server(obj.server.port, obj.server.host)
	    oscClient = new osc.Client(obj.client.host, obj.client.port)
	    oscClient.send('/status', socket.sessionId + ' connected')
		oscServer.on('message', function(msg, rinfo) {
			socket.emit("message", msg)
		});
		socket.emit("connected", 1)
		isConnected = true
	});
 	socket.on("message", function (obj) {
		oscClient.send.apply(oscClient, obj)
  	});
	socket.on('disconnect', function(){
		if (isConnected) {
			oscServer.close()
			oscClient.close()
		}
		isConnected = false
  	});
});

server.listen(8080)




