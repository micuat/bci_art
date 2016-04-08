# Muse command
# muse-io --device Muse-7042 --osc 'osc.udp://localhost:12000'

from OSC import OSCServer, OSCClient, OSCMessage
import sys
from time import sleep
import numpy as np
from sklearn import svm

# muse-io server
server = OSCServer( ("localhost", 12000) )
server.timeout = 0

# node.js
client = OSCClient()
client.connect( ("localhost", 13000) )

run = True

# this method of reporting timeouts only works by convention
# that before calling handle_request() field .timed_out is
# set to False
def handle_timeout(self):
    self.timed_out = True

# funny python's way to add a method to an instance of a class
import types
server.handle_timeout = types.MethodType(handle_timeout, server)

class Dataset:
    state = "none"
    maxSampleNum = 50
    classifier_ready = False

    def __init__(self):
        return

    def initialize(self):
        self.state = "none"

    def startRecording(self):
        if self.state == "none":
            self.state = "recording_initial"

    def stopRecording(self):
        if self.state == "recording_initial" or self.state == "recording":
            self.state = "recorded"

    def record(self, sample):
        if self.state == "recording_initial":
            self.feat_matrix = np.copy(sample)
            self.state = "recording"
        elif self.state == "recording":
            self.feat_matrix = np.concatenate((self.feat_matrix, sample))
            if self.feat_matrix.shape[0] >= self.maxSampleNum:
                print "done"
                self.state = "done"

feat_vector = np.array([[0.0, 0.0, 0.0, 0.0]])
feat_vector_update = [0, 0, 0, 0]
datasets = [Dataset(), Dataset()]

def power_abs_callback(path, tags, args, source):
    powerBand = path.split("/")[3]
    if powerBand == "delta_absolute" and feat_vector[0][0] != args[1]:
        feat_vector[0][0] = args[1]
        feat_vector_update[0] = 1
    elif powerBand == "theta_absolute" and feat_vector[0][1] != args[1]:
        feat_vector[0][1] = args[1]
        feat_vector_update[1] = 1
    elif powerBand == "alpha_absolute" and feat_vector[0][2] != args[1]:
        feat_vector[0][2] = args[1]
        feat_vector_update[2] = 1
    elif powerBand == "beta_absolute" and feat_vector[0][3] != args[1]:
        feat_vector[0][3] = args[1]
        feat_vector_update[3] = 1

    if np.all(feat_vector_update) == 1:
        datasets[0].record(feat_vector)
        datasets[1].record(feat_vector)
        
        if datasets[0].state == "done" and datasets[1].state == "done":
            global classifier
            classifier = svm.SVC()
            X = np.concatenate((datasets[0].feat_matrix, datasets[1].feat_matrix))
            y = np.concatenate((np.zeros((datasets[0].feat_matrix.shape[0], 1)), np.ones((datasets[1].feat_matrix.shape[0], 1))))
            classifier.fit(X, y)
            datasets[0].initialize()
            datasets[1].initialize()
            datasets[0].classifier_ready = True

        if datasets[0].classifier_ready:
            prediction_result = classifier.predict(feat_vector)
            print prediction_result
            m = OSCMessage("/bci_art/svm/prediction")
            m.append(prediction_result)
            client.send(m)
        
        print feat_vector
        feat_vector_update[0] = 0
        feat_vector_update[1] = 0
        feat_vector_update[2] = 0
        feat_vector_update[3] = 0

def control_record_callback(path, tags, args, source):
    command = path.split("/")[4]
    if command == "1":
        print "1st sample set"
        m = OSCMessage("/bci_art/svm/start/1/received")
        client.send(m)
        datasets[0].startRecording()
    elif command == "2":
        print "2nd sample set"
        m = OSCMessage("/bci_art/svm/start/2/received")
        client.send(m)
        datasets[1].startRecording()

def quit_callback(path, tags, args, source):
    # don't do this at home (or it'll quit blender)
    global run
    run = False

def default_callback(path, tags, args, source):
    # do nothing
    return

server.addMsgHandler( "/muse/elements/delta_absolute", power_abs_callback )
server.addMsgHandler( "/muse/elements/theta_absolute", power_abs_callback )
server.addMsgHandler( "/muse/elements/alpha_absolute", power_abs_callback )
server.addMsgHandler( "/muse/elements/beta_absolute", power_abs_callback )
server.addMsgHandler( "/bci_art/svm/start/1", control_record_callback )
server.addMsgHandler( "/bci_art/svm/start/2", control_record_callback )
server.addMsgHandler( "/bci_art/quit", quit_callback )
server.addMsgHandler( "default", default_callback )

# user script that's called by the game engine every frame
def each_frame():
    # clear timed_out flag
    server.timed_out = False
    # handle all pending requests then return
    while not server.timed_out:
        server.handle_request()

# simulate a "game engine"
while run:
    # do the game stuff:
    sleep(0.1)
    # call user script
    each_frame()

server.close()
