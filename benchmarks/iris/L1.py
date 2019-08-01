from sklearn.decomposition import IncrementalPCA
from sklearn.metrics.pairwise import paired_manhattan_distances
import h5py
f=h5py.File('iris_0.h5','r')

n_components = 2
alpha = 1
batch_size = 10
n_iter = 25
random_state = 2018
model = IncrementalPCA(n_components=n_components, batch_size=batch_size)

weights=f['weights']
bias=f['bias']

for i in range(int(weights.shape[0]/batch_size)):
    weights_model =model.partial_fit(weights[i*batch_size+1:(i+1)*batch_size,:].reshape(-1,4*3))
    #weights_model =model.partial_fit(weights[i*batch_size+1:(i+1)*batch_size,:].reshape(-1,25088*38))

test_weights=weights[:100,:].reshape(-1,4*3)
#test_weights=weights[:100,:].reshape(-1,25088*38)
weights_encoded=model.fit_transform(test_weights)
weights_decoded=model.inverse_transform(weights_encoded)
distance=paired_manhattan_distances(test_weights,weights_decoded)
print(distance)