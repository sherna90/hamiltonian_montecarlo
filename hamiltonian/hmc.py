
import numpy as np
import scipy as sp
import os
from utils import *
from numpy.linalg import inv
from copy import deepcopy
from multiprocessing import Pool
from tqdm import tqdm, trange
import h5py 
import os 
from scipy.optimize import check_grad

def unwrap_self_mcmc(arg, **kwarg):
    return HMC.sample(*arg, **kwarg)

class HMC:
    def __init__(self, X,y,logp, grad, start,hyper, path_length=10,verbose=True):
        self.X=X
        self.y=y
        self.start = start
        self.hyper = hyper
        self.step_size = {}
        self.path_length = path_length
        self.logp = logp
        self.grad=grad
        self._accepted=0
        self._direction=1.0
        self._mass_matrix={}
        self._inv_mass_matrix={}
        for var in self.start.keys():
            dim=(np.array(self.start[var])).size
            #self.step_size[var]=(1./dim)**(0.25)
            self.step_size[var]=np.random.uniform(0.0104, 0.0156)
            if dim==1:
                self._mass_matrix[var]=1
                self._inv_mass_matrix[var]=1
            else:
                self._mass_matrix[var]=np.ones(dim)
                self._inv_mass_matrix[var]=np.ones(dim)
        self._verbose=verbose


    def step(self,state,momentum,rng):
        path_length = rng.rand() * self.path_length
        n_steps = max(1, int(path_length / max(self.step_size.values())))
        direction = 1.0 if rng.rand() > 0.5 else -1.0
        epsilon={var:direction*self.step_size[var] for var in self.start.keys()}
        #epsilon={var:self.step_size[var] for var in self.start.keys()}
        q = deepcopy(state)
        p = self.draw_momentum(rng)
        q_new=deepcopy(q)
        p_new=deepcopy(p)
        grad_q=self.grad(self.X,self.y,q,self.hyper)
        for var in self.start.keys():
            p_new[var]-= (0.5*epsilon[var])*grad_q[var]
            q_new[var]+=epsilon[var]*self._inv_mass_matrix[var].reshape(self.start[var].shape)*p_new[var]
        for i in range(n_steps-1):
            q_new, p_new = self.leapfrog(q_new, p_new, epsilon)
        grad_q=self.grad(self.X,self.y,q_new,self.hyper)
        for var in self.start.keys():
           p_new[var]-= (0.5*epsilon[var])*grad_q[var]
        if self.accept(q, q_new, p, p_new):
            q = q_new
            p = p_new
            self._accepted += 1
        return q,p

    def acceptance_rate(self):
        return float(self._accepted)/len(self._samples)

    def leapfrog(self,q, p,epsilon):
        grad_q=self.grad(self.X,self.y,q,self.hyper)
        for var in self.start.keys():
            #dim=(np.array(self.start[var])).size
            p[var]-= (0.5*epsilon[var])*grad_q[var]
            q[var]+=epsilon[var]*self._inv_mass_matrix[var].reshape(self.start[var].shape)*p[var]
        return q, p

    def accept(self,current_q, proposal_q, current_p, proposal_p):
        accept=False
        E_new = self.energy(proposal_q,proposal_p)
        E = self.energy(current_q,current_p)
        A = np.exp(E - E_new)
        g = np.random.rand()
        if np.isfinite(A) and (g < A):
            accept=True
        return accept


    def energy(self, q, p):
        U=0
        for var in self.start.keys():
            U+=0.5*np.sum(p[var].reshape(-1)**2)
        K=self.logp(self.X,self.y,q,self.hyper)
        return K + U


    def draw_momentum(self,rng):
        momentum={}
        for var in self.start.keys():
            dim=(np.array(self.start[var])).size
            momentum[var]=np.zeros(dim)
            for i in range(dim):
                momentum[var][i]=rng.normal(0,self._mass_matrix[var][i])
            momentum[var]=momentum[var].reshape(self.start[var].shape)
        return momentum


    def sample(self,niter=1e4,burnin=1e3,backend=None,rng=None):
        samples=[]
        if rng==None:
            rng = np.random.RandomState(0)
        q,p=self.start,self.draw_momentum(rng)
        for i in tqdm(range(int(niter+burnin))):
            q,p=self.step(q,p,rng)
            if i==burnin : 
                acc_rate=self._accepted/float(burnin)
                self.step_size={var:self.tune(self.step_size[var],acc_rate) for var in self.start.keys()}
                print('burnin acceptance rate : {0:.4f}'.format(acc_rate))
                self._accepted=0
            if i>burnin:
                samples.append(q)
                #if self._verbose and (i%(niter/10)==0):
                #    print('acceptance rate : {0:.4f}'.format(self.acceptance_rate()) )
        posterior={var:[] for var in self.start.keys()}
        for s in samples:
            for var in self.start.keys():
                posterior[var].append(s[var].reshape(-1))
        for var in self.start.keys():
            posterior[var]=np.array(posterior[var])
        #return posterior
        #if backend is None:
        #    for i in tqdm(range(int(niter)),total=int(niter)):
        #        q,p=self.step(q,p)
        #        self._samples.append(q)
        #        if self._verbose and (i%(niter/10)==0):
        #            print('acceptance rate : {0:.4f}'.format(self.acceptance_rate()) )
        #    posterior={var:[] for var in self.start.keys()}
        #    for s in self._samples:
        #        for var in self.start.keys():
        #            posterior[var].append(s[var].reshape(-1))
        #    for var in self.start.keys():
        #        posterior[var]=np.array(posterior[var])
        #else:
        #    posterior=h5py.File(backend,'w')
        #    num_samples=int(niter)
        #    dset = {var:posterior.create_dataset(var, (num_samples,self.start[var].reshape(-1).shape[0]), maxshape=(None,self.start[var].reshape(-1).shape[0]) ) for var in self.start.keys()}
        #    for i in tqdm(range(int(niter)),total=int(niter)):
        #        q,p=self.step(q,p)
        #        for var in self.start.keys():
        #            dset[var][-1,:]=q[var].reshape(-1)
        #    posterior.flush()
        return posterior

    def multicore_sample(self,niter=1e4,burnin=1e3,backend=None,ncores=2):
        pool = Pool(processes=ncores)
        rng = [np.random.RandomState(i) for i in range(ncores)]
        results=pool.map(unwrap_self_mcmc, zip([self]*ncores, [int(niter/ncores)]*ncores,[burnin]*ncores,[backend]*ncores,rng))
        posterior={var:np.concatenate([r[var] for r in results],axis=0) for var in self.start.keys()}
        return posterior

    def compute_mass_matrix(self,samples,cov=True):
        posterior={var:[] for var in self.start.keys()}
        for s in samples:
            for var in self.start.keys():
                posterior[var].append(s[var].reshape(-1))
        for var in self.start.keys():
            posterior[var]=np.array(posterior[var])
            self._mass_matrix[var]=np.var(posterior[var],axis=0)
            self._inv_mass_matrix[var]=1./self._mass_matrix[var]
            
    def tune(self,scale,acc_rate):
            new_scale=scale
            if acc_rate < 0.001:
                print('reduce by 90 percent')
                new_scale *= 0.1
            elif acc_rate < 0.05:
                print('reduce by 50 percent')
                new_scale *= 0.5
            elif acc_rate < 0.2:
                print('reduce by ten percent')
                # reduce by ten percent
                new_scale *= 0.9
            elif acc_rate > 0.95:
                print('increase by factor of ten')
                # increase by factor of ten
                new_scale *= 10.0
            elif acc_rate > 0.75:
                print('increase by double')
                new_scale *= 2.0
            elif acc_rate > 0.5:
                print('increase by ten percent')
                # increase by ten percent
                new_scale *= 1.1
            return new_scale      