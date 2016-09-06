var port_python = process.argv[2];
var port_receive = process.argv[3];
var port_http = process.argv[4];

var express = require('express');
var app = express();
var http = require('http').Server(app);
var io = require('socket.io')(http);

var osc = require('node-osc');
var svm_python = new osc.Client('127.0.0.1', port_python);
var oscServer = new osc.Server(port_receive, '127.0.0.1');

oscServer.on("message", function (msg, rinfo) {
    console.log("message:");
    console.log(msg);
    io.emit('bci command', msg);
});

app.get('/', function(req, res){
    res.sendFile(__dirname + '/index.html');
});
app.get('/jquery-1.11.1.js', function(req, res){
    res.sendFile(__dirname + '/jquery-1.11.1.js');
});
app.use('/libraries', express.static('libraries'));
app.use('/assets', express.static('assets'));

io.on('connection', function(socket){
    console.log('a user connected');
    socket.on('disconnect', function(){
        console.log('user disconnected');
    });
    socket.on('bci command', function(msg){
        io.emit('bci command', msg);
        svm_python.send(msg);
        console.log('message: ' + msg);
    }
);});

http.listen(port_http, function(){
    console.log('listening on *:' + port_http);
});
