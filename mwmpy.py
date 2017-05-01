
# requires python-mindwave
# https://github.com/micuat/python-mindwave
import numpy as np
import _thread
import time
from mindwave.pyeeg import bin_power
from mindwave.parser import ThinkGearParser, TimeSeriesRecorder
from mindwave.bluetooth_headset import connect_magic, connect_bluetooth_addr
from mindwave.bluetooth_headset import BluetoothError

class Mwmpy:
    eegArray = []
    
    def startup(self):
        # stub: set address manually
        address = None

        if address is None:
            socket, socket_addr = connect_magic()
            if socket is None:
                print ("No MindWave Mobile found.")
                sys.exit(-1)
        else:
            socket = connect_bluetooth_addr(address)
            if socket is None:
                print ("Connection failed.")
                sys.exit(-1)
            socket_addr = address
        print ("Connected with MindWave Mobile at %s" % socket_addr)
        for i in range(5):
            try:
                if i>0:
                    print ("Retrying...")
                time.sleep(2)
                len(socket.recv(10))
                break
            except BluetoothError as e:
                print (e)
            if i == 5:
                print ("Connection failed.")
                sys.exit(-1)
        return socket
            
    def loop(self):
        socket = self.startup()
        recorder = TimeSeriesRecorder()
        parser = ThinkGearParser(recorders= [recorder])

        quit = False
        while quit is False:
            try:
                data = socket.recv(10000)
                parser.feed(data)
            except BluetoothError:
                pass
            
            if len(recorder.raw)>=512*5:
                feature_vector = self.compute_feature_vector(recorder.raw[-512*5:], 512)
                print(feature_vector)
            time.sleep(0.1)

    def __init__(self):
        try:
            _thread.start_new_thread( self.loop, () )
        except:
            print ("Error: unable to start thread")
    
    def set_on_feature_vector(self, func):
        self.func_feature_vector = func
    
    def compute_feature_vector(self, eegdata, Fs):
        # https://github.com/bcimontreal/bci_workshop/blob/master/bci_workshop_tools.py
        eegdata = np.array([eegdata]).T

        # 1. Compute the PSD
        winSampleLength = len(eegdata)

        # Apply Hamming window
        w = np.hamming(winSampleLength)
        dataWinCentered = eegdata - np.mean(eegdata, axis=0) # Remove offset
        dataWinCenteredHam = (dataWinCentered.T*w).T

        NFFT = self.nextpow2(winSampleLength)
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

    def nextpow2(self, i):
        """
        Find the next power of 2 for number i

        """
        n = 1
        while n < i:
            n *= 2
        return n

    def eeg_callback(self, path, tags, args, source):
        eeg = args[1]
        # print eeg
        if self.eegArray == []:
            self.eegArray = [eeg]
        else:
            self.eegArray = np.concatenate((self.eegArray, [eeg]))

        if len(self.eegArray) == 220:
            feat_vector = self.compute_feature_vector(self.eegArray, 220)
            self.func_feature_vector(feat_vector)
            self.eegArray = self.eegArray[220/4:]
