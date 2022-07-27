import joblib
import numpy as np
import matplotlib.pyplot as plt

def ecdf(sample):

    # convert sample to a numpy array, if it isn't already
    sample = np.atleast_1d(sample)

    # find the unique values and their corresponding counts
    quantiles, counts = np.unique(sample, return_counts=True)

    # take the cumulative sum of the counts and divide by the sample size to
    # get the cumulative probabilities between 0 and 1
    cumprob = np.cumsum(counts).astype(np.double) / sample.size

    return quantiles, cumprob

nn_file = '/home/ubuntu/CodeCommit/faiss_deduplicate/wd/quora_question_pairs/results/test_nn.obj'
loaded_obj = joblib.load(nn_file)

# Assemble the distances into an array
dist_list = []
for cur_obj in loaded_obj:
    dist_list.append(cur_obj[0])

dist_array = np.vstack(dist_list)

# compute the ECDF of the samples
qe, pe = ecdf(dist_array[:, 0])

fig, ax = plt.subplots(2, 1, figsize=(12, 8))
ax[0].hist(dist_array[:, 0], bins=50)
ax[1].plot(qe, pe, '-r', lw=2, label='CDF')
ax[0].grid()
ax[1].grid()
ax[1].set_ylabel('Cumulative Probability')
ax[1].set_xlabel('Nearest Neighbor Distance')
ax[0].set_ylabel('Histogram (Count)')
ax[0].set_title('FAISS Nearest Neighbor Distribution')

# Plot the ECDF