import warnings
warnings.filterwarnings("ignore")

from sklearn import datasets
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import pymc3 as pm
import theano.tensor as tt
import sys 
sys.path.append("./") 


iris = datasets.load_iris()
data = iris.data  
labels = iris.target
classes=np.unique(iris.target)
X, y = iris.data, iris.target
X = (X - X.mean(axis=0)) / X.std(axis=0)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0,shuffle=True)

with pm.Model() as model_s:
    alpha = pm.Normal('alpha', mu=0, sd=2, shape=2)
    beta = pm.Normal('beta', mu=0, sd=2, shape=(4,2))
    alpha_f = tt.concatenate([[0],alpha])
    beta_f = tt.concatenate([np.zeros((4,1),beta)],axis=1)
    mu = alpha_f + pm.math.dot(X_train, beta_f)
    theta = tt.nnet.softmax(mu)

    yl = pm.Categorical('yl', p=theta, observed=y_train)
    #step = pm.Metropolis()
    #start=pm.find_MAP()
    step=pm.HamiltonianMC(path_length=10.0,is_cov=False,adapt_step_size=False)
    #step = pm.NUTS()
    trace_s = pm.sample(10000,step)

energy = trace_s['energy']
plt.hist(energy)
plt.show()
print(pm.summary(trace_s))
#pm.traceplot(trace_s)
#plt.show()