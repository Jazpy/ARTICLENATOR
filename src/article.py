import os
import textract

from nltk import tokenize

class Article:
  article_counter = 0

  def __init__(self, path):

    if not os.path.isfile(path):
      raise FileNotFoundError

    self.path        = path
    self.name        = os.path.basename(path)
    self.raw_text    = textract.process(self.path).decode('utf-8')
    self.predictions = []

    self.sentences = tokenize.sent_tokenize(self.raw_text.replace('\n', ' '))
    self.sentences = [x.strip() for x in self.sentences]

    self.id = Article.article_counter
    Article.article_counter += 1

  def get_name(self):
    return self.name

  def get_id(self):
    return self.id

  def get_text(self):
    return self.raw_text

  def get_sentences(self):
    return self.sentences

  def clean_predictions(self):
    self.predictions = []

  def add_prediction(self, prediction):
    self.predictions.append(prediction)

  def get_predictions(self):
    return self.predictions

  def write_text(self, path):
    with open(path, 'w') as out:
      for line in self.sentences:
        out.write(f'{line}\n')
