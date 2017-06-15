// p5js

var N = 2;

var gauge;
function Gauge() {
  this.sMax = 0;
  this.s = 0;
  this.score = function(s) {
    this.sMax = s;
  }
  this.draw = function() {
    fill('#E005FF'); // reset button
    b = 50;
    rect(/*width * 0.5 - b * 0.5*/width - b, 0, b, height);
    if(this.s < this.sMax) {
      this.s += 0.01;
      if(this.s > this.sMax) this.s = this.sMax;
    }
    fill(0, 128);
    rect(/*width * 0.5 - b * 0.5*/width - b, 0, b, (1 - this.s) * height);
    textAlign(CENTER);
    textFont("Monaco, Courier New, Courier");
    textSize(16);
    fill(255);
    text(int(this.s * 100) + " %", /*width * 0.5*/ width - b / 2, height - 50);
  }
}
var hemis;
function Hemi(x, y, w, h, i, c) {
  this.x = x;
  this.y = y;
  this.w = w;
  this.h = h;
  this.i = i;
  this.c = c;
  this.p = 0;
  this.bang = 5;
  this.bangMax = 10;
  this.predicted = function() {
    this.bang += 1;
    if(this.bang > this.bangMax) this.bang = this.bangMax;
    socket.emit('osc command', {address:"/bci/interpolated/" + this.i, data:this.bang * 10});
  }
  this.unpredicted = function() {
    this.bang -= 1;
    if(this.bang < 0) this.bang = 0;
    socket.emit('osc command', {address:"/bci/interpolated/" + this.i, data:this.bang * 10});
  }
  this.progress = function(p) {
    this.p = p;
  }
  this.draw = function() {
    fill(this.c);
    rect(this.x, this.y, this.w, this.h);
    fill(255, 200 * this.bang / this.bangMax);
    rect(this.x, this.y + this.h * (1 - this.p), this.w, this.h + this.p);
  }
  this.inside = function(x, y) {
    if(this.x < x && x < this.x + this.w && this.y < y && y < this.y + this.h)
      return true;
    else
      return false;
  }
};

function reset() {
  socket.emit('bci command', "/bci_art/svm/reset");
  hemis = [];
  for(var i = 0; i < N; i++) {
    hemis.push(new Hemi(map(i, 0, N, 0, width), 0, width / N, height, i, color(i * 256/N, 0, 0)));
  }
  gauge = new Gauge();
}

function setup() {
  noStroke();
  var pcanvas = createCanvas(window.innerWidth, 480);
  frameRate(10);
  pcanvas.parent('p5container');
  reset();
}

function windowResized() {
  resizeCanvas(window.innerWidth, 480);
//  lhemi.w = width * 0.5;
//  rhemi.x = width * 0.5;
//  rhemi.w = width * 0.5;
}

function draw() {
  for(i = 0; i < N; i++) {
    hemis[i].draw();
  }
  gauge.draw();
}

function mousePressed() {
  if(mouseY > 0 && mouseY < height && mouseX > 0 && mouseX < width) { // on canvas
    b = 50;
    if(/*width * 0.5 - b * 0.5*/width - b < mouseX/* && mouseX < width * 0.5 + b * 0.5*/) { // reset button
      reset();
    }
    else {
      for(var i = 0; i < N; i++) {
        if(hemis[i].inside(mouseX, mouseY))
          socket.emit('bci command', "/bci_art/svm/start/" + i);
      }
    }
  }
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

  if(msg == "/bci_art/svm/done/1") {
  }
  if(msg == "/bci_art/svm/done/2") {
  }
  for(var i = 0; i < N; i++) {
    if(msg[0] == "/bci_art/svm/progress/" + i) {
      hemis[i].progress(msg[1] / msg[2]);
    }
  }
  if(msg[0] == "/bci_art/svm/score") {
    gauge.score(msg[1]);
  }
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
