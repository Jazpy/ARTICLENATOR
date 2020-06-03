import re
from enum             import IntEnum
from snorkel.labeling import labeling_function
from snorkel.labeling import LabelingFunction

###############################################################
# Procedure for new labels (classes)                          #
#                                                             #
# Write at least 3 labeler functions associated to said label #
# Register functions in new labeler function list             #
###############################################################

# Labels returned by labeler functions
class Label(IntEnum):
  ABSTAIN = -1
  CLASS   =  0
  PASS    =  1

#######################
# Auxiliary functions #
#######################

def count_char_kinds(w):
  uppers = sum(c.isupper() for c in w)
  lowers = sum(c.islower() for c in w)
  digits = sum(c.isdigit() for c in w)

  return (uppers, lowers, digits)

def contains_keyword(s, keywords, label, lower=True):
  s = s.sentence
  if lower:
    s = s.lower()

  if any(keyword in s for keyword in keywords):
    return label

  return Label.PASS

def new_contains(keywords, label=Label.CLASS):
  return LabelingFunction(name=f'contains_{keywords[0]}',
                          f=contains_keyword,
                          resources=dict(keywords=keywords, label=label))

# Function used to exclude certain sentences from labeling analysis
# NOT A LABELER
def simple_filter(sentence):
  toks       = sentence.split()
  digits     = sum(c.isdigit() for c in sentence)
  s_no_space = sentence.replace(' ', '')

  # Filter out sentences with doi links, emails, or other unrelated stuff
  keywords  = ['license', 'doi', '@']
  # Filter out sentences with references of the form: 'Genes 1(2):227–243.',
  # and stuf like 'pp 465-657'
  ref_regex  = '.*[0-9]+\(.*\)\:.[0-9]+.*'
  pp_regex   = '.*pp[0-9]+.[0-9]+.*'

  # Filter out sentences with less than 2 words
  if len(toks) < 2:
    return False
  # Filter out sentences that contain banned keywords
  if any(keyword in sentence.lower() for keyword in keywords):
    return False
  # Filter out sentences with mostly numbers
  if digits > len(sentence) / 2:
    return False
  # Filter out reference regex
  if (re.match(ref_regex,  s_no_space) or
      re.match(pp_regex,   s_no_space)):
    return False
  # Filter out et al if sentence is short
  if 'et al.' in sentence and len(toks) < 10:
    return False

  return True

#############################
# Begin labeler heuristics #
#############################

############
# SOFTWARE #
############

contains_version  = new_contains(['version'])
contains_software = new_contains(['software'])
contains_package  = new_contains(['package'])
contains_script   = new_contains(['script'])

@labeling_function()
def cap_words(s):
  words = s.sentence.split()

  for word in words:
    word_nd = word.replace('.', '')
    uppers, lowers, digits = count_char_kinds(word_nd)

    # If all-caps and more than two chars, usually software
    if uppers == len(word_nd) and len(word_nd) >= 3:
      return Label.CLASS

  return Label.ABSTAIN

@labeling_function()
def version_number(s):
  # Matches stuff like '2.5.1417'
  if re.match('[0-9]+(\.[0-9]+)+', s.sentence):
    return Label.CLASS

  return Label.ABSTAIN

###########
# SPECIES #
###########

contains_strain  = new_contains(['strain'])
contains_species = new_contains(['species'])

@labeling_function()
def latin_suffix(s):
  words = s.sentence.split()

  for word in words:
    if word.lower().endswith('ium'):
      return Label.CLASS

  return Label.ABSTAIN

@labeling_function()
def abbreviated_species(s):
  words = s.sentence.split()

  if len(words) < 2:
    return Label.PASS

  for i in range(len(words) - 1):
    w1 = words[i]
    w2 = words[i + 1]

    if re.match('[A-Z]\.', w1) and len(w2) > 4:
      return Label.CLASS

  return Label.ABSTAIN

##########
# SAMPLE #
##########

contains_sample = new_contains(['sample'])
contains_genome = new_contains(['genome'])

@labeling_function()
def sample_name(s):
  words = s.sentence.split()

  for word in words:
    alpha_start = word[0].isalpha()
    uppers, lowers, digits = count_char_kinds(word)

    # If word begins with alphabetic char, has more than one alphabetic char,
    # and it has a lot of numbers (over 33.3%), label it as a sample name
    if alpha_start and (uppers > 1 or lowers > 1) and (digits > len(word) / 3):
      return Label.CLASS

  return Label.ABSTAIN

##########
# METHOD #
##########

contains_enrich    = new_contains(['enrich'])
contains_fold      = new_contains(['fold'])
contains_method    = new_contains(['method'])
contains_capture   = new_contains(['captur'])
contains_combine   = new_contains(['combine'])
contains_technique = new_contains(['technique'])

############
# MOLECULE #
############

contains_adna = new_contains(['adna'])
contains_dna  = new_contains(['dna'])
contains_rna  = new_contains(['rna'])

############
# PROPERTY #
############

contains_clonal = new_contains(['clonal'])
contains_gc     = new_contains(['gc cont'])
contains_hybrid = new_contains(['hybrid'])
contains_bias   = new_contains(['bias'])
contains_dup    = new_contains(['dupli'])
contains_length = new_contains(['length'])

###################################################
# All labeler functions should be registered here #
###################################################

registered_software = [contains_version, contains_software, contains_package,
                       contains_script, cap_words, version_number]
registered_species  = [contains_strain, contains_species,
                       latin_suffix, abbreviated_species]
registered_sample   = [contains_sample, contains_genome, sample_name]
registered_method   = [contains_enrich, contains_fold, contains_method,
                       contains_capture, contains_combine, contains_technique]
registered_molecule = [contains_adna, contains_dna, contains_rna]
registered_property = [contains_clonal, contains_gc, contains_hybrid,
                       contains_bias, contains_dup, contains_length]
