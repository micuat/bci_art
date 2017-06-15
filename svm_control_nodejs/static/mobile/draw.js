// p5js

var N = 2;

var hemis;
function Hemi() {
  this.bang = 5;
  this.bangMax = 10;
  this.predicted = function() {
    this.bang += 1;
    if(this.bang > this.bangMax) this.bang = this.bangMax;
  }
  this.unpredicted = function() {
    this.bang -= 1;
    if(this.bang < 0) this.bang = 0;
  }
};

function setup() {
  noStroke();
  var pcanvas = createCanvas(window.innerWidth, window.innerHeight);
  frameRate(10);
  pcanvas.parent('p5container');
  hemis = [];
  for(var i = 0; i < N; i++) {
    hemis.push(new Hemi());
  }
}

function windowResized() {
  resizeCanvas(window.innerWidth, window.innerHeight);
}

function draw() {
  colorMode(HSB);
  background(map(hemis[0].bang, 0, hemis[0].bangMax, 0, 128), 255, 255);
}

// socket.io

var socket = io();
$('form').submit(function(){
  socket.emit('bci command', $('#m').val());
  $('#m').val('');
  return false;
});
socket.on('bci command', function(msg){
  $('#messages').prepend($('<li>').text(msg));
  var count = 0;
  $("li").each(function( index ) {
  count++;
  if(count > 5)
    $( this ).remove();
  });

  if(msg[0] == "/bci_art/svm/prediction") {
    for(var i = 0; i < N; i++) {
      if(int(msg[1]) == int(i)) {
        hemis[i].predicted();
      }
      else {
        hemis[i].unpredicted();
      }
    }
  }
});
