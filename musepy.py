import threading
import numpy as np
from pythonosc import dispatcher
from pythonosc import osc_server

class Musepy:
    eegArray = []

    def __init__(self, port):
        dispatch = dispatcher.Dispatcher()
        dispatch.map("/muse/eeg", self.eeg_callback)
        self.server = osc_server.ThreadingOSCUDPServer(("127.0.0.1", port), dispatch)
        self.server_thread = threading.Thread(target=self.server.serve_forever)

    def start(self):
        self.server_thread.start()

    def set_on_feature_vector(self, func):
        self.func_feature_vector = func

    def exit(self):
        self.server.shutdown()
    
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
        PSD = 2*np.abs(Y[0:int(NFFT/2),:])
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

    def eeg_callback(self, path, *args):
        eeg = args[1]
        if self.eegArray == []:
            self.eegArray = [eeg]
        else:
            self.eegArray = np.concatenate((self.eegArray, [eeg]))

        if len(self.eegArray) >= 220:
            self.eegArray = self.eegArray[0:220-1]
            feat_vector = self.compute_feature_vector(self.eegArray, 220)
            self.func_feature_vector(feat_vector)
            self.eegArray = self.eegArray[int(220/4):]
