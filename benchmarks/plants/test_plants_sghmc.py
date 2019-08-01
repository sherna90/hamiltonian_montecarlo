import warnings
warnings.filterwarnings("ignore")

import numpy as np
from sklearn import datasets
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import sys 
import pandas as pd
import time
import h5py 

sys.path.append("../../") 
import hamiltonian.cpu.softmax as softmax
import hamiltonian.cpu.sgld_multicore as sampler
import hamiltonian.utils as utils

niter = 12
burnin = 4

path_length=10
epochs=20
batch_size=50
alpha=1e-2

data_path = '../../data/'

plants_train=h5py.File(data_path+'train_features_labels.h5','r')
X_train=plants_train['train_features']
y_train=plants_train['train_labels']
plants_test=h5py.File(data_path+'validation_features_labels.h5','r')
X_test=plants_test['validation_features']
y_test=plants_test['validation_labels']

classes=np.unique(y_train)
D=X_train.shape[1]
K=y_train.shape[1]
import time

start_p={'weights':np.zeros((D,K)),
        'bias':np.zeros((K))}
hyper_p={'alpha':alpha}

model=softmax.SOFTMAX()
mcmc=sampler.sgld_multicore(model.loss, model.grad, start_p,hyper_p, path_length=1,verbose=1)
t0=time.time()

backend = "sghmc_plants2"
#backend = None
posterior_sample,logp_samples=mcmc.multicore_sample(X_train,y_train,niter,burnin,batch_size,backend=backend)
t1=time.time()
print("Ellapsed Time : ",t1-t0)

if backend:
    par_mean = mcmc.backend_mean(posterior_sample, niter)

    y_pred_mc=model.predict(X_test,par_mean)

    print(classification_report(y_test[:].argmax(axis=1), y_pred_mc))
    print(confusion_matrix(y_test[:].argmax(axis=1), y_pred_mc))
else:
    post_par={var:np.mean(posterior_sample[var],axis=0).reshape(start_p[var].shape) for var in posterior_sample.keys()}
    #post_par_var={var:np.var(posterior_sample[var],axis=0).reshape(start_p[var].shape) for var in posterior_sample.keys()}
    y_pred=model.predict(X_test,post_par)
    print(classification_report(y_test[:].argmax(axis=1), y_pred))
    print(confusion_matrix(y_test[:].argmax(axis=1), y_pred))

'''
print ('-------------------------------------------')
from sklearn.linear_model import LogisticRegression
softmax_reg = LogisticRegression(multi_class="multinomial", solver="lbfgs", C=1/alpha,fit_intercept=True)
softmax_reg.fit(X_train,np.argmax(y_train,axis=1))
y_pred2 = softmax_reg.predict(X_test)
print(classification_report(y_test[:].argmax(axis=1), y_pred2))
print(confusion_matrix(y_test[:].argmax(axis=1), y_pred2))
'''

plants_train.close()
plants_test.close()
