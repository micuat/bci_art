
# requires pyOSC
# pip install pyosc --pre
from OSC import OSCServer, OSCClient, OSCMessage
import numpy as np
from sklearn import svm

class Musepy:
    eegArray = []

    def __init__(self, server):
        self.server = server
        server.addMsgHandler( "/muse/eeg", self.eeg_callback )
    
    def set_on_feature_vector(self, func):
        self.func_feature_vector = func
    
    def compute_feature_vector(self, eegdata, Fs):
        # https://github.com/bcimontreal/bci_workshop/blob/master/bci_workshop_tools.py
        # print eegdata
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
