# Muse command
# muse-io --device Muse-7042 --osc 'osc.udp://localhost:12000'

from OSC import OSCServer, OSCClient, OSCMessage
import sys
from time import sleep
import numpy as np
from sklearn import svm

port_muse = int(sys.argv[1])
port_node = int(sys.argv[2])

# muse-io server
server = OSCServer( ("localhost", port_muse) )
server.timeout = 0

# node.js
client = OSCClient()
client.connect( ("localhost", port_node) )

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
        m.append(self.feat_matrix.shape[0])
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
    
    if command == "1":
        print "1st sample set"
        m = OSCMessage("/bci_art/svm/start/1/received")
        client.send(m)
        datasets[0].startRecording()
        if datasets[1].isRecording():
            datasets[1].initialize()
    elif command == "2":
        print "2nd sample set"
        m = OSCMessage("/bci_art/svm/start/2/received")
        client.send(m)
        datasets[1].startRecording()
        if datasets[0].isRecording():
            datasets[0].initialize()

def reset():
    datasets[0].initialize()
    datasets[1].initialize()
    global classifier_ready
    classifier_ready = False

def reset_callback(path, tags, args, source):
    reset()

def quit_callback(path, tags, args, source):
    # don't do this at home (or it'll quit blender)
    global run
    run = False

eegArray = []
datasets = [Dataset(1), Dataset(2)]

def compute_feature_vector(eegdata, Fs):
    # https://github.com/bcimontreal/bci_workshop/blob/master/bci_workshop_tools.py
    # print eegdata
    eegdata = np.array([eegdata]).T
    
    # 1. Compute the PSD
    winSampleLength = len(eegdata)
    
    # Apply Hamming window
    w = np.hamming(winSampleLength)
    dataWinCentered = eegdata - np.mean(eegdata, axis=0) # Remove offset
    dataWinCenteredHam = (dataWinCentered.T*w).T

    NFFT = nextpow2(winSampleLength)
    Y = np.fft.fft(dataWinCenteredHam, n=NFFT, axis=0)/winSampleLength
    PSD = 2*np.abs(Y[0:NFFT/2,:])
    f = Fs/2*np.linspace(0,1,NFFT/2)
    
    # SPECTRAL FEATURES
    # Average of band powers
    # Delta <4
    ind_delta, = np.where(f<4)
    meanDelta = np.mean(PSD[ind_delta,:],axis=0)
    # Theta 4-8
    ind_theta, = np.where((f>=4) & (f<=8))
    meanTheta = np.mean(PSD[ind_theta,:],axis=0)
    # Alpha 8-12
    ind_alpha, = np.where((f>=8) & (f<=12)) 
    meanAlpha = np.mean(PSD[ind_alpha,:],axis=0)
    # Beta 12-30
    ind_beta, = np.where((f>=12) & (f<30))
    meanBeta = np.mean(PSD[ind_beta,:],axis=0)
    
    feature_vector = np.concatenate((meanDelta, meanTheta, meanAlpha, meanBeta),axis=0)
    feature_vector = np.log10(feature_vector)   
    return feature_vector

def nextpow2(i):
    """ 
    Find the next power of 2 for number i
    
    """
    n = 1
    while n < i: 
        n *= 2
    return n

def eeg_callback(path, tags, args, source):
    eeg = args[1]
    # print eeg
    global eegArray
    if eegArray == []:
        eegArray = [eeg]
    else:
        eegArray = np.concatenate((eegArray, [eeg]))
    
    if len(eegArray) == 220:
        feat_vector = compute_feature_vector(eegArray, 220)
        
        datasets[0].record(feat_vector)
        datasets[1].record(feat_vector)
        
        global classifier_ready
        
        if classifier_ready == False and datasets[0].state == "done" and datasets[1].state == "done":
            global classifier
            classifier = svm.SVC()
            X = np.concatenate((datasets[0].feat_matrix, datasets[1].feat_matrix))
            y = np.concatenate((np.zeros((datasets[0].feat_matrix.shape[0], 1)), np.ones((datasets[1].feat_matrix.shape[0], 1))))
            classifier.fit(X, y)
            
            classifier_ready = True
            
            m = OSCMessage("/bci_art/svm/score")
            m.append(classifier.score(X, y))
            client.send(m)
            
        if classifier_ready:
            prediction_result = classifier.predict(feat_vector)
            print prediction_result
            m = OSCMessage("/bci_art/svm/prediction")
            m.append(prediction_result)
            client.send(m)
        
        print feat_vector
        eegArray = eegArray[110:]

def default_callback(path, tags, args, source):
    # do nothing
    return

server.addMsgHandler( "/muse/eeg", eeg_callback )
server.addMsgHandler( "/bci_art/svm/start/1", control_record_callback )
server.addMsgHandler( "/bci_art/svm/start/2", control_record_callback )
server.addMsgHandler( "/bci_art/svm/reset", reset_callback )
server.addMsgHandler( "/bci_art/quit", quit_callback )
server.addMsgHandler( "default", default_callback )

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
