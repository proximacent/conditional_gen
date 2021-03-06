import codecs, os
import json
import pickle
import numpy as np
from helper import histogram, bar_chart, get_x_y, get_unique_labels
import matplotlib.pyplot as plt
import pickle
import time

# Tensorflow log reg
# print('Training with tensorflow logistic regression')
# t1 = time.time()
# f1_test, f1_val, coefs = log_regression_tf(trX, trY, vaX, vaY, teX, teY)
# print('training min: {}'.format(round((time.time() - t1)/60, 1)))
# print('%05.2f test f1'%f1_test)
# print('%05.2f validation f1'%f1_val)

# TODO does the original data contain the connective inside the args!!??

def train(folder, relation, saveas):
  """ Logistic regression to discover discourse relation neurons """
  from models import log_regression_tf, log_regression_sk
  # Load hidden states previously extracted
  print("loading hidden states")
  data = pickle.load(open("neurons.pkl", "rb"))
  # ids is dictionary of disc IDs, discs is numpy array
  ids, h_arr = data['ids'], data['discs']
  h_size = h_arr.shape[1]

  t0 = time.time()
  plot_number = 0
  results = []
  for relation in relations:
    print('**Testing on relation: ', relation)
    for folder in folders:
      plot_number += 1
      print('computing logistic reg for {} in dir {}'.format(relation, folder))
      train_path = 'data/'+folder+'/train.json'
      val_path = 'data/'+folder+'/dev.json'
      test_path = 'data/'+folder+'/test.json'
      # Get data
      trX, trY =  get_x_y(ids, h_arr, train_path, relation)
      vaX, vaY =  get_x_y(ids, h_arr, val_path, relation)
      teX, teY =  get_x_y(ids, h_arr, test_path, relation)

      # Skip if no data
      if len(trX)==0 or len(vaX)==0:continue

      # SKlearn log reg
      print('Training with sklearn logistic regression')
      t1 = time.time()
      score_te, score_va, c, nnotzero, notzero_coefs_ids, notzero_coefs = \
                                  log_regression_sk(trX, trY, vaX, vaY, teX, teY)
      print('training min: {}'.format(round((time.time() - t1)/60, 1)))
      print('%05.2f test accuracy'%score_te)
      print('%05.2f regularization coef'%c)
      print('%05d features used'%nnotzero)

      results.append({
          'relation'         : relation,
          'folder'           : folder,
          'score_test'       : score_te,
          'score_val'        : score_va,
          'size_train'       : len(trX),
          'size_val'         : len(vaX),
          'size_test'        : len(teX),
          'coefficient'      : c,
          'nnotzero'         : nnotzero,
          'notzero_coefs_ids' : notzero_coefs_ids,
          'notzero_coefs'    : notzero_coefs
          })

  # Save results
  pickle.dump(results, open(saveas,"wb"))
  print('total exec time: {} min'.format(round((time.time() - t0)/60, 1)))

def find_result(data, relation, folder):
  for result in data:
    if result['relation'] == relation:
      if result['folder'] == folder:
        return result
  # If not found, return none
  return None

def chart_single(pkl):
  """ Export all results from pickle to chart """
  data = pickle.load(open(pkl, "rb"))
  with open('rs.csv', 'w') as f:
    f.write('folder,relation,accuracy,neurons,std,>1std,>2std\n')
    for d in data:
      folder = d["folder"]
      relation = d["relation"]
      f.write(folder+','+relation+',')
      weights = d['notzero_coefs']
      std = weights.std()
      gt1 = np.sum(np.greater(weights, std))
      gt2 = np.sum(np.greater(weights, 2*std))
      name = relation + '-' + folder
      label = 'accuracy:{:0.2f}, neurons:{:0.0f}, std:{:0.2f}, >1 std:{:0.0f}, >2 std:{:0.0f}'.format(d['score_test'], d['nnotzero'], std, gt1, gt2)
      label_write = '{:0.2f}, {:0.0f}, {:0.2f}, {:0.0f}, {:0.0f}'.format(d['score_test'], d['nnotzero'], std, gt1, gt2)
      x = range(d['notzero_coefs'].shape[0])
      plt.bar(x, d['notzero_coefs'], width=1)
      plt.xlabel(label, fontsize=16)
      plt.savefig('charts/top-level/'+name, dpi=96)
      plt.clf()
      f.write(label_write+'\n')
      # plt.show()

def chart_group(pkl, max_rows):
  """
  Chart list of results
  Args:
    pkl: file path to pickled results
    max_rows: max num of rows per chart
  """
  data = pickle.load(open(pkl, "rb"))
  relations = list(set([x['relation'] for x in data])); relations.sort()
  folders   = list(set([x['folder'] for x in data])); folders.sort()
  plots = max_rows*len(folders)

  # Loop through list
  plot_number = 0
  for r, relation in enumerate(relations):
    for f, folder in enumerate(folders):
      plot_number += 1
      # Get single result
      d = find_result(data, relation, folder)
      isLast = True if r==(len(relations)-1) and f==(len(folders)-1) else False
      if d is None:
        if (plot_number%plots==0 and plot_number!=0) or isLast==True:
          plt.rcParams["figure.figsize"] = [16,9]
          plt.subplots_adjust(hspace=0.6,wspace=0.5)
          # plt.savefig('my_fig.png', dpi=96)
          plt.show()
          plot_number=0
        continue

      # Chart
      title = relation + ' ' + folder
      label = 'size tr/va/te {:0.0f}/{:0.0f}/{:0.0f}, acc {:0.2f}, reg coef {:0.2f}, neurons: {:0.0f}'.format(d['size_train'],
            d['size_val'], d['size_test'], d['score_test'], d['coefficient'],
                                                                d['nnotzero'])
      bar_chart(d['notzero_coefs'], title, label, max_rows,\
                                                      len(folders), plot_number)
      if plot_number%plots == 0 or isLast==True:
        plt.rcParams["figure.figsize"] = [16,9]
        plt.subplots_adjust(hspace=0.6,wspace=0.5)
        # plt.savefig('my_fig.png', dpi=96)
        plt.show()
        plot_number=0

# histogram(notzero_coefs, bins=100)
if __name__=="__main__":
  # Fine grained
  relations = get_unique_labels('data/mapping_none.json')
  folders = ['fine_binary_implicit', 'fine_binary_all', 'fine_binary_explicit']

  # Coarse, with separate entrel
  relations = get_unique_labels('data/mapping_to_top_w_entrel.json')
  folders = [
    'coarse_binary_split_entrel_implicit_entrel',
    'coarse_binary_split_entrel_all',
    'coarse_binary_split_entrel_explicit'
    ]

  # train(folders, relations, "coarse_results_split_entrel.pkl")
  # chart_group("coarse_results_split_entrel.pkl", 4)
  chart_single("coarse_results_split_entrel.pkl")


