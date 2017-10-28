# Muse command
# muse-io --device Muse-7042 --osc 'osc.udp://localhost:12000'

import sys
from time import sleep
import time
import numpy as np
from sklearn.manifold import TSNE
from pythonosc import udp_client
import musepy

port_muse = int(sys.argv[1])
port_node = int(sys.argv[2])

num_samples = 120

# musepy
mp = musepy.Musepy(port_muse)
mp.start()

# openFrameworks
client = udp_client.SimpleUDPClient("127.0.0.1", port_node)

run = True

def normalize(p):
    max = np.amax(p)
    min = np.amin(p)
    return (p - min) / (max - min)

feat_matrix = []

def plot_tsne():
    print(feat_matrix)
    print(feat_matrix.shape)
    global tsneResult
    model = TSNE(n_components=2, random_state=0, learning_rate=100)
    tsneResult = model.fit_transform(feat_matrix)
    tsneResult[:,0] = normalize(tsneResult[:,0])
    tsneResult[:,1] = normalize(tsneResult[:,1])
    print(tsneResult)

    timestamp = timestr = time.strftime("%Y%m%d-%H%M%S")
    np.save('t0.npy', feat_matrix)
    np.save('%st0.npy' % timestamp, feat_matrix)
    np.save('tsneResult.npy', tsneResult)
    np.save('%stsneResult.npy' % timestamp, tsneResult)

tsne_running = False
tsne_ready = False

def on_feature_vector(feat_vector):
    print(feat_vector)
    
    global tsne_running
    global tsne_ready
    global feat_matrix
    global num_samples

    if tsne_running:
        pass
    elif tsne_ready == False:
        if feat_matrix == []:
            feat_matrix = np.matrix(feat_vector)
        else:
            feat_matrix = np.concatenate((feat_matrix, [feat_vector]))
        
        if feat_matrix.shape[0] % 10 == 0:
            print(feat_matrix.shape[0])
        
        if feat_matrix.shape[0] >= num_samples:
            tsne_running = True
            plot_tsne()
            tsne_running = False
            tsne_ready = True
    else:
        closestDistance0 = 10000000000.0
        closestDistance1 = 10000000000.0
        closestDistance2 = 10000000000.0
        closestIndex0 = 0
        closestIndex1 = 0
        closestIndex2 = 0
        print(feat_matrix.shape)
        for i in range(0, num_samples):
            distance = np.linalg.norm(feat_matrix[i, :] - feat_vector)
            if distance < closestDistance0:
                closestDistance2 = closestDistance1
                closestDistance1 = closestDistance0
                closestDistance0 = distance
                closestIndex2 = closestIndex1
                closestIndex1 = closestIndex0
                closestIndex0 = i
            elif distance < closestDistance1:
                closestDistance2 = closestDistance1
                closestDistance1 = distance
                closestIndex2 = closestIndex1
                closestIndex1 = i
            elif distance < closestDistance2:
                closestDistance2 = distance
                closestIndex2 = i
        print(str(closestIndex0) + " " + str(closestIndex1) + " " + str(closestIndex2))
        print(tsneResult[closestIndex0, :])
        print(tsneResult[closestIndex1, :])
        print(tsneResult[closestIndex2, :])

        closestDistanceTotal = closestDistance0 + closestDistance1 + closestDistance2
        interpolated = (tsneResult[closestIndex0, :] * (closestDistance1 + closestDistance2) + tsneResult[closestIndex1, :] * (closestDistance1 + closestDistance0) + tsneResult[closestIndex2, :] * (closestDistance0 + closestDistance1)) / closestDistanceTotal * 0.5
        print(interpolated)
        client.send_message("/muse/tsne", (interpolated[0], interpolated[1], closestIndex0))

mp.set_on_feature_vector(on_feature_vector)

def each_frame():
    pass

while run:
    sleep(0.01)
    each_frame()

mp.exit()
