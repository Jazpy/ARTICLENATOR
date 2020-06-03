import os
import textract

from nltk import tokenize

class Article:
  def __init__(self, path):

    if not os.path.isfile(path):
      raise FileNotFoundError

    self.path      = path
    self.name      = os.path.basename(path)
    self.raw_text  = textract.process(self.path).decode('utf-8')

    self.sentences = tokenize.sent_tokenize(self.raw_text.replace('\n', ' '))
    self.sentences = [x.strip() for x in self.sentences]

  def get_name(self):
    return self.name

  def get_text(self):
    return self.text

  def get_sentences(self):
    return self.sentences

  def write_text(self, path):
    with open(path, 'w') as out:
      for line in self.sentences:
        out.write(f'{line}\n')
