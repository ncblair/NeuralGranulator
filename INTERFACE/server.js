var http = require('http'),
	fs = require('fs'),
	socket = require('socket.io'),
	osc = require('node-osc');

// https://socket.io/get-started/chat


console.log("To start the demo, go to http://localhost:8080 in your web browser.");

const server = http.createServer((req, res) => {
	// Why doesn't this work! This might cause OSC to fail hmm.
	// res.setHeader("Access-Control-Allow-Origin", "http://localhost:8080/socket.io/");
	res.setHeader("Access-Control-Allow-Origin", "*");
	res.setHeader("Access-Control-Allow-Headers", "X-Requested-With");
	res.setHeader("Access-Control-Allow-Headers", "Content-Type");
	res.setHeader("Access-Control-Allow-Methods", "PUT, GET, POST, DELETE, OPTIONS");
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
// var io = require('socket.io')(server, {
// 	cors: {
// 	  origin: "http://localhost:8080",
// 	  methods: ["GET", "POST"],
// 	}
//   });

var oscServer, oscClient
var io = socket(server)

io.sockets.on('connection', function (socket) {
	console.log('connection');
	socket.on("config", function (obj) {
		isConnected = true;
    	oscServer = new osc.Server(obj.server.port, obj.server.host);
	    oscClient = new osc.Client(obj.client.host, obj.client.port);
	    oscClient.send('/status', socket.sessionId + ' connected');
		oscServer.on('message', function(msg, rinfo) {
			socket.emit("message", msg);
		});
		socket.emit("connected", 1);
	});
 	socket.on("message", function (obj) {
		oscClient.send.apply(oscClient, obj);
  	});
	socket.on('disconnect', function(){
		if (isConnected) {
			oscServer.kill();
			oscClient.kill();
		}
  	});
});

server.listen(8080)



