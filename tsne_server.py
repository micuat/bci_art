# Muse command
# muse-io --device Muse-7042 --osc 'osc.udp://localhost:12000'

from pythonosc import osc_message_builder, udp_client
import sys
from time import sleep
import numpy as np
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import time
# # import musepy
import mwmpy

port_muse = int(sys.argv[1])
port_node = int(sys.argv[2])

count = 0
# muse-io server
# server = OSCServer( ("localhost", port_muse) )
# server.timeout = 0

# musepy
mp = mwmpy.Mwmpy() #musepy.Musepy(server)

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

    n0 = np.size(feat_matrix, 0);
    n0 = tsneResult.shape[0] / 3
    n1 = n0 * 2
    plt.plot(tsneResult[0:n0 - 1,0], tsneResult[0:n0 - 1,1], 'yo')
    plt.plot(tsneResult[n0:n1 - 1,0], tsneResult[n0:n1 - 1,1], 'ro')
    plt.plot(tsneResult[n1:,0], tsneResult[n1:,1], 'bo')
    plt.show()

tsne_ready = False

def on_feature_vector(feat_vector):
    print(feat_vector)
    
    global tsne_ready
    global feat_matrix
    if tsne_ready == False:
        if feat_matrix == []:
            feat_matrix = np.matrix(feat_vector)
        else:
            feat_matrix = np.concatenate((feat_matrix, [feat_vector]))
        
        if feat_matrix.shape[0] % 10 == 0:
            print(feat_matrix.shape[0])
        
        if feat_matrix.shape[0] == 120:
            plot_tsne()
            tsne_ready = True
    else:
        closestDistance0 = 10000000000.0
        closestDistance1 = 10000000000.0
        closestDistance2 = 10000000000.0
        closestIndex0 = 0
        closestIndex1 = 0
        closestIndex2 = 0
        for i in range(0, np.size(feat_matrix, 0)):
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

        m = OSCMessage("/muse/tsne")
        m.append(interpolated[0])
        m.append(interpolated[1])
        m.append(closestIndex0)
        try:
            client.send(m)
        except OSCClientError:
            print("caught osc error")


mp.set_on_feature_vector(on_feature_vector)

def each_frame():
    # clear timed_out flag
    # server.timed_out = False
    # handle all pending requests then return
    # while not server.timed_out:
    #     server.handle_request()
    global count
    count += 1
    #print(count)
    if count > 10000:
        exit()

while run:
    sleep(0.01)
    each_frame()

server.close()
