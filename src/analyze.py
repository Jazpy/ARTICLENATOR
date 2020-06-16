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

  article_dir       = '../articles'
  training_set_size = 2000

  # Validate article dir
  if not os.path.exists(article_dir):
    print('Article directory does not exist!', file=sys.stderr)
    return

  # Get all pdfs inside dir
  print(f'Finding articles in directory: {article_dir}')
  pdf_paths = [f'{article_dir}/{x}' for x in os.listdir(article_dir)]
  pdf_paths = [x for x in pdf_paths if os.path.isfile(x) and x.endswith('.pdf')]

  # Validate articles
  if not pdf_paths:
    print('Article directory has no PDF files!', file=sys.stderr)
    return

  # Create article objects for pdfs found
  print('Tokenizing all pdf files found...')
  articles = []
  for pdf_path in pdf_paths:
    try:
      articles.append(Article(pdf_path))
    except (FileNotFoundError, UnicodeDecodeError):
      print(f'Article path {pdf_path} is not a valid file!', file=sys.stderr)
    except LookupError:
      print('NLTK lookup error, try nltk.download(\'punkt\')', file=sys.stderr)
      return

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
      s_dict['article']  = article
      s_dict['sentence'] = sentence

      sentence_rows.append(s_dict)

  # Validate sentences
  if len(sentence_rows) < training_set_size:
    print(f'Could not extract enough ({training_set_size}) sentences!',
      file=sys.stderr)
    return

  # Build training and full sentence sets
  all_sentences = pd.DataFrame(sentence_rows)
  trn_sentences = pd.DataFrame(all_sentences['sentence'].sample(
    training_set_size, random_state=2))
  tst_sentences = pd.DataFrame(all_sentences['sentence'])

  # Build classifiers for all categories
  print('Building classifiers...')
  software_classifier = Classifier(labelers.registered_species)

  # Train all classifiers on the given data
  print('Training classifier models...')
  software_classifier.train(trn_sentences)

  # Run all classifiers on full data
  print('Running classifier models on full corpus...')
  try:
    predictions = software_classifier.classify(tst_sentences)
  except RuntimeError as e:
    print(e, file=sys.stderr)

  # Print predictions
  for prediction, sentence, article in \
    zip(predictions, all_sentences['sentence'], all_sentences['article']):
    article.add_prediction(prediction)

if __name__ == "__main__":
  main()
