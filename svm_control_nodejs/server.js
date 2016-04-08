var app = require('express')();
var http = require('http').Server(app);
var io = require('socket.io')(http);

var osc = require('node-osc');
var svm_python = new osc.Client('127.0.0.1', 12000);

app.get('/', function(req, res){
    res.sendfile('index.html');
});

io.on('connection', function(socket){
    console.log('a user connected');
    socket.on('disconnect', function(){
        console.log('user disconnected');
    });
    socket.on('chat message', function(msg){
        io.emit('chat message', msg);
        svm_python.send(msg);
        console.log('message: ' + msg);
    }
);});

http.listen(3000, function(){
    console.log('listening on *:3000');
});
