import sys
import os
import re
import snorkel
import pandas as pd

import labelers
from article    import Article
from classifier import Classifier

def main():
  # Setup
  pd.set_option('display.max_rows', None)
  pd.set_option('display.max_colwidth', 200)

  article_dir = '../articles'

  # Validate article dir
  if not os.path.exists(article_dir):
    print('Article directory does not exist!', file=sys.stderr)
    return

  # Get all pdfs inside dir
  print(f'Finding articles in directory: {article_dir}')
  pdf_paths = [f'{article_dir}/{x}' for x in os.listdir(article_dir)]
  pdf_paths = [x for x in pdf_paths if os.path.isfile(x) and x.endswith('.pdf')]

  # Create article objects for pdfs found
  print('Tokenizing all pdf files found...')
  articles = []
  for pdf_path in pdf_paths:
    try:
      articles.append(Article(pdf_path))
    except:
      print(f'Article path {pdf_path} is not a valid file!', file=sys.stderr)

  # Read articles
  print('Extracting all sentences from articles into dataframe...')
  sentence_rows = []
  for article in articles:
    for sentence in article.get_sentences():

      # Filter out some useless sentences
      if not labelers.simple_filter(sentence):
        continue

      # Fill this sentence's fields
      s_dict = {}
      s_dict['article']  = article.get_name()
      s_dict['sentence'] = sentence

      sentence_rows.append(s_dict)

  all_sentences = pd.DataFrame(sentence_rows)

  # Random sentence set for training
  trn_sentences = all_sentences.sample(200, random_state=2)

  # Build classifiers for all categories
  print('Building classifiers...')
  software_classifier = Classifier(labelers.registered_software)

  # Train all classifiers on the given data
  print('Training classifier models...')
  software_classifier.train(trn_sentences)

  # Run all classifiers on full data
  print('Running classifier models on full corpus...')
  try:
    predictions = software_classifier.classify(all_sentences)
  except RuntimeError as e:
    print(e, file=sys.stderr)

  # Print predictions
  print(predictions)

if __name__ == "__main__":
  main()
