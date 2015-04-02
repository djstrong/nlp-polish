__author__ = 'djstrong'

import cPickle
import shelve
import csv

lemma_form_weights = shelve.open('lemma_form_weights.shelve', protocol=2)

with open('lemma_form_weights.csv') as f:
    reader = csv.reader(f)
    for row in reader:
        form,lemma,tags,weight = row
        weight = float(weight)
        lemma_form_weights[' '.join([form,lemma,tags])] = weight

lemma_form_weights.close()