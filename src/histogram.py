import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

def get_cmap(n, name='hsv'):
  cm  = plt.cm.get_cmap(name, n)
  ret = []

  for i in range(n):
    ret.append(cm(i))

  return ret

class Histogram:
  def __init__(self, concept):
    self.concept = concept
    self.labels  = []
    self.counts  = []

  def count_concept(self, subconcept, articles):
    years = []

    # Extract years from all articles associated to this subconcept
    for article in articles:
      years.append(article.get_year())

    self.labels.append(subconcept)
    self.counts.append(years)

  def plot(self, pathname):
    bins = np.arange(2010, 2021)

    # Plot formatting
    plt.figure(figsize=(32, 18), dpi=300)
    plt.title(f'Terms for topic: {self.concept}', fontsize=70)
    plt.xlabel('Year of publication', fontsize=50)
    plt.ylabel('Articles with reference to term', fontsize=50)
    plt.xticks(ticks=bins, labels=bins, fontsize=20)
    plt.yticks(fontsize=30)
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

    # Plotting
    plot = plt.hist(self.counts, bins, histtype='bar', stacked=False, fill=True,
      label=self.labels)

    plt.legend(loc='upper left', labels=self.labels, fontsize=30)

    plt.savefig(pathname)
