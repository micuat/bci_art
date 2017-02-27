# Muse command
# muse-io --device Muse-70]2 --osc 'osc.udp://localhost:12000'

from OSC import OSCServer, OSCClient, OSCMessage, OSCClientError
import sys
from time import sleep
import numpy as np
from sklearn import svm
import musepy

N = 3

port_muse = int(sys.argv[1])
port_node = int(sys.argv[2])
port_of = int(sys.argv[3])


# muse-io server
server = OSCServer( ("localhost", port_muse) )
server.timeout = 0

# musepy
mp = musepy.Musepy(server)

# node.js
client = OSCClient()
client.connect( ("localhost", port_node) )
clientof = OSCClient()
clientof.connect( ("localhost", port_of) )

run = True

# this method of reporting timeouts only works by convention
# that before calling handle_request() field .timed_out is
# set to False
def handle_timeout(self):
    self.timed_out = True

# funny python's way to add a method to an instance of a class
import types
server.handle_timeout = types.MethodType(handle_timeout, server)

classifier_ready = False

class Dataset:
    state = "none"
    maxSampleNum = 30
    identifier = 0

    def __init__(self, id):
        self.identifier = id
        return

    def initialize(self):
        m = OSCMessage("/bci_art/svm/progress/" + str(self.identifier))
        m.append(0)
        m.append(self.maxSampleNum)
        client.send(m)
        self.state = "none"

    def startRecording(self):
        self.state = "recording_initial"

    def isRecording(self):
        return self.state == "recording_initial" or self.state == "recording"

    def stopRecording(self):
        if self.isRecording():
            self.state = "recorded"

    def record(self, sample):
        if self.state == "recording_initial":
            self.feat_matrix = np.array([sample])
            self.state = "recording"
        elif self.state == "recording":
            self.feat_matrix = np.concatenate((self.feat_matrix, [sample]), axis=0)
        else:
            return

        m = OSCMessage("/bci_art/svm/progress/" + str(self.identifier))
        m.append(int(self.feat_matrix.shape[0]))
        m.append(self.maxSampleNum)
        client.send(m)

        if self.feat_matrix.shape[0] >= self.maxSampleNum:
            print "done"
            print self.feat_matrix
            m = OSCMessage("/bci_art/svm/done/" + str(self.identifier))
            client.send(m)
            self.state = "done"

def control_record_callback(path, tags, args, source):
    command = path.split("/")[4]
    if classifier_ready:
        reset()

    m = OSCMessage("/bci_art/svm/start/" + command + "/received")
    client.send(m)
    datasets[int(command)].startRecording()
    for i in range(0, N):
        if i != int(command) and datasets[i].isRecording():
            datasets[i].initialize()

def reset():
    for i in range(0, N):
        datasets[i].initialize()
    global classifier_ready
    classifier_ready = False

def reset_callback(path, tags, args, source):
    reset()

def quit_callback(path, tags, args, source):
    # don't do this at home (or it'll quit)
    global run
    run = False

datasets = [Dataset(0)]
for i in range(1, N):
    datasets.append(Dataset(i))


def default_callback(path, tags, args, source):
    # do nothing
    return

for i in range(0, N):
  server.addMsgHandler( "/bci_art/svm/start/" + str(i), control_record_callback )
server.addMsgHandler( "/bci_art/svm/reset", reset_callback )
server.addMsgHandler( "/bci_art/quit", quit_callback )
server.addMsgHandler( "default", default_callback )

def on_feature_vector(feat_vector):
    print feat_vector
    for i in range(0, N):
        datasets[i].record(feat_vector)

    global classifier_ready
    dataset_ready = True
    for i in range(0, N):
        if datasets[i].state != "done":
            dataset_ready = False

    if classifier_ready == False and dataset_ready:
        global classifier
        classifier = svm.SVC()

        X = datasets[0].feat_matrix
        for i in range(1, N):
            X = np.concatenate((X, datasets[i].feat_matrix))
    
        y = np.zeros((datasets[0].feat_matrix.shape[0], 1))
        for i in range(1, N):
            y = np.concatenate((y, i * np.ones((datasets[i].feat_matrix.shape[0], 1))))
        classifier.fit(X, y)

        classifier_ready = True

        print "prep m"
        m = OSCMessage("/bci_art/svm/score")
        m.append(classifier.score(X, y))
        print "send"
        client.send(m)

    if classifier_ready:
        prediction_result = classifier.predict(feat_vector)
        print prediction_result
        m = OSCMessage("/bci_art/svm/prediction")
        m.append(prediction_result)
        client.send(m)
        try:
            clientof.send(m)
        except OSCClientError:
            print "caught osc error"

mp.set_on_feature_vector(on_feature_vector)

def each_frame():
    # clear timed_out flag
    server.timed_out = False
    # handle all pending requests then return
    while not server.timed_out:
        server.handle_request()

while run:
    sleep(0.1)
    each_frame()

server.close()
