import sys
import string
import os
import re
import snorkel
import nltk
import pandas as pd

import labelers
from article    import Article
from classifier import Classifier
from relgraph   import RelGraph
from histogram  import Histogram

def main():
  # Setup
  pd.set_option('display.max_rows', None)
  pd.set_option('display.max_colwidth', 200)

  article_dir       = '../articles'
  png_dir           = '../pngs'
  training_set_size = 2000
  top_choices       = 10

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
    training_set_size, random_state=1))
  tst_sentences = pd.DataFrame(all_sentences['sentence'])

  # Build classifiers for all categories
  print('Building classifiers...')
  classifiers = []
  classifiers.append(Classifier(labelers.registered_software, 'software'))
  classifiers.append(Classifier(labelers.registered_species,  'species'))
  classifiers.append(Classifier(labelers.registered_sample,   'sample'))
  classifiers.append(Classifier(labelers.registered_method,   'method'))
  classifiers.append(Classifier(labelers.registered_molecule, 'molecule'))
  classifiers.append(Classifier(labelers.registered_property, 'property'))

  # Train all classifiers on the given data
  print('Training classifier models...')
  for i, cl in enumerate(classifiers):
    cl.train(trn_sentences)
    print(f'{i + 1} / {len(classifiers)}...')

  # Run all classifiers on full data
  print('Running classifier models on full corpus...')
  for cl in classifiers:
    try:
      predictions = cl.classify(tst_sentences)
    except RuntimeError as e:
      print(e, file=sys.stderr)
      continue

    stat_string = f'* Classified with "{cl.get_name().upper()}" labels *'
    print('*' * len(stat_string))
    print(stat_string)
    print('*' * len(stat_string))

    # Add predictions to article
    for prediction, article in zip(predictions, all_sentences['article']):
      article.add_prediction(prediction)

    # Get most used terms for CLASS predictions
    all_dicts     = []
    filtered_tags = ('DT', 'IN', 'CC', 'EX', 'TO', 'WDT', 'PRP',
                    'VBG', 'CD', 'WRB', 'MD', 'VBZ', 'RP', 'SYM',
                    'UH', 'PRP', 'PRP$', 'RB', 'RBS', 'WP', 'VB')
    for article in articles:
      curr_dict = {}

      for sentence, prediction in \
      zip(article.get_sentences(), article.get_predictions()):
        if prediction != 0:
          continue

        filtered_sentence = re.sub(r'[^\w\s]', '', sentence.lower(), re.UNICODE)
        toks = nltk.word_tokenize(filtered_sentence)
        tags = [x[1] for x in nltk.pos_tag(toks)]

        # Walk over sentence with two word sliding window
        for i in range(len(toks) - 1):
          w0           = toks[i]
          w1           = toks[i + 1]
          compound     = f'{w0} {w1}'

          # Skip over useless tags
          if (tags[i] in filtered_tags or
              (len(w0) == 1 and w0 in string.punctuation)):
            continue

          # Add single word
          count         = curr_dict.get(w0, 0) + 1
          curr_dict[w0] = count

          # Skip over useless tags
          if (tags[i + 1] in filtered_tags or
              (len(w1) == 1 and w1 in string.punctuation)):
            continue

          # Add two words
          count               = curr_dict.get(compound, 0) + 1
          curr_dict[compound] = count

      all_dicts.append((article, curr_dict))

      # Clean the predictions for next iteration
      article.clean_predictions()

    # Merge dictionaries
    main_dict = {}
    for article, d in all_dicts:
      for key in d.keys():
        main_get   = main_dict.get(key, (0, list()))
        main_count = main_get[0] + 1
        main_list  = main_get[1]
        main_list.append(article)

        main_dict[key] = (main_count, main_list)

    # Filter low freqs and sort by freq
    main_dict = dict(filter(lambda x: x[1][0] > 2, main_dict.items()))
    main_dict_ordered_keys = sorted(main_dict.keys(),
                                    key=lambda x: main_dict.get(x)[0],
                                    reverse=True)

    # Update top_choices if there are less available choices
    with open('common.txt', 'r') as c:
      common = c.readlines()

    for w in common:
      w = w.strip()
      if w in main_dict_ordered_keys:
        main_dict_ordered_keys.remove(w)

    top_choices = min(top_choices, len(main_dict_ordered_keys))

    print('Building relationship graph and keyword histogram...')
    rel_graph = RelGraph(cl.get_name().upper())
    histo = Histogram(cl.get_name().upper())

    for i, k in enumerate(main_dict_ordered_keys[:top_choices]):
      article_list = main_dict.get(k)[1]
      rel_graph.link_concept(k.upper(), article_list)
      histo.count_concept(k.upper(), article_list)

    try:
      print('Rendering graph...')
      rel_graph.cairo_render(f'{png_dir}/{cl.get_name()}', 2160)
      print(f'Success rendering to: {png_dir}/{cl.get_name()}.png')

      print('Rendering histogram...')
      histo.plot(f'{png_dir}/{cl.get_name()}_hist')
      print(f'Success rendering to: {png_dir}/{cl.get_name()}_hist.png')
    except Exception as e:
      print(f'Could not render. {repr(e)}')

if __name__ == "__main__":
  main()
