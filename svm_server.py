# Muse command
# muse-io --device Muse-70]2 --osc 'osc.udp://localhost:12000'

# $ python -u svm_server.py 12000 13000

import sys
import threading
from time import sleep
import numpy as np
from sklearn import svm
import musepy
from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server

Ndefault = 2
Nmax = 16

port_muse = int(sys.argv[1])
port_node_listen = 12100
port_node_send = 12200
port_of = int(sys.argv[2])

# node.js
client = udp_client.SimpleUDPClient("localhost", port_node_send)
clientof = udp_client.SimpleUDPClient("localhost", port_of)
classifier_ready = False

class Dataset:
    state = "none"
    maxSampleNum = 30
    identifier = 0

    def __init__(self, id):
        self.identifier = id
        return

    def initialize(self):
        client.send_message("/bci_art/svm/progress/" + str(self.identifier), (0, self.maxSampleNum))
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

        client.send_message("/bci_art/svm/progress/" + str(self.identifier),
            (int(self.feat_matrix.shape[0]), self.maxSampleNum))

        if self.feat_matrix.shape[0] >= self.maxSampleNum:
            print("done")
            print(self.feat_matrix)
            client.send_message("/bci_art/svm/done/" + str(self.identifier), ())
            self.state = "done"

def control_record_callback(path, *args):
    print(args)
    command = path.split("/")[4]
    if classifier_ready:
        reset(len(datasets))

    client.send_message("/bci_art/svm/start/" + command + "/received", ())
    print(command)
    datasets[int(command)].startRecording()
    for i in range(0, len(datasets)):
        if i != int(command) and datasets[i].isRecording():
            datasets[i].initialize()

def reset(N):
    global datasets
    datasets = [Dataset(0)]
    for i in range(1, N):
        datasets.append(Dataset(i))
    for i in range(0, N):
        datasets[i].initialize()
    global classifier_ready
    classifier_ready = False
    print(len(datasets))

def reset_callback(path, *args):
    if len(args) > 0:
        reset(args[0])
    else:
        reset(Ndefault)

def on_feature_vector(feat_vector):
    print(feat_vector)
    for dataset in datasets:
        dataset.record(feat_vector)

    global classifier_ready
    dataset_ready = True
    for dataset in datasets:
        if dataset.state != "done":
            dataset_ready = False

    if classifier_ready == False and dataset_ready:
        global classifier
        classifier = svm.SVC()

        X = datasets[0].feat_matrix
        for i in range(1, len(datasets)):
            X = np.concatenate((X, datasets[i].feat_matrix))
    
        y = np.zeros((datasets[0].feat_matrix.shape[0], 1))
        for i in range(1, len(datasets)):
            y = np.concatenate((y, i * np.ones((datasets[i].feat_matrix.shape[0], 1))))
        classifier.fit(X, y.ravel())

        classifier_ready = True
        client.send_message("/bci_art/svm/score", classifier.score(X, y.ravel()))

    if classifier_ready:
        prediction_result = classifier.predict(feat_vector.reshape(1, -1))
        print(prediction_result)
        client.send_message("/bci_art/svm/prediction", prediction_result)
        try:
            clientof.send_message("/bci_art/svm/prediction", prediction_result)
        except OSCClientError:
            print("caught osc error")



def main():
    global datasets
    datasets = [Dataset(0)]
    for i in range(1, Ndefault):
        datasets.append(Dataset(i))
    for i in range(0, Ndefault):
        datasets[i].initialize()

    dispatch = dispatcher.Dispatcher()

    for i in range(0, Nmax):
        dispatch.map("/bci_art/svm/start/" + str(i), control_record_callback)
    dispatch.map("/bci_art/svm/reset", reset_callback)
    server = osc_server.ThreadingOSCUDPServer(("127.0.0.1", port_node_listen), dispatch)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

    # musepy
    mp = musepy.Musepy(port_muse)
    mp.set_on_feature_vector(on_feature_vector)
    mp.start()

if __name__ == "__main__":
    main()
