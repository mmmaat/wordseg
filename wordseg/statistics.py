# coding: utf-8

"""Extract statistics relevant for word segmenation corpora"""

# From https://github.com/alecristia/CDSwordSeg/blob/master/recipes/CatalanSpanish/_describe_gold.sh
# and https://github.com/ConstantineLignos/WordSegmentation.
# Copyright (C) 2010, 2011 Constantine Lignos

import collections
import itertools
import pandas as pd

from math import log2

from wordseg import utils
from wordseg.separator import Separator


class CorpusStatistics(object):
    def __init__(self, corpus, separator, log=utils.null_logger()):
        self.separator = separator
        if not self.separator.word:
            raise ValueError('word separator not defined')
        if not self.separator.phone:
            log.warning('phone separator not defined, some stats ignored')
        log.info('token separator is: %s', self.separator)

        # force to list and ignore empty lines
        self.corpus = list(utt.strip() for utt in corpus if len(utt.strip()))
        log.info('loaded %s utterances', len(self.corpus))

        # tokenize the text at each defined level ('word', 'syllable'
        # and/or 'phone') TODO can be optimize we are tokenizing the
        # entire text up to 3 times
        self.tokens = {}
        for level in self.separator.levels():
            self.tokens[level] = [
                list(self.separator.tokenize(utt, level, keep_boundaries=False))
                for utt in self.corpus]

        # estimates token frequencies at each level
        self.unigram = self._unigram('word')

    def _unigram(self, level):
        """Return dictionary of (token: frequency) items"""
        count =  collections.Counter(
            (t for utt in self.tokens[level] for t in utt)).most_common()
        total_count = sum(c[1] for c in count)
        return {c[0]: c[1] / total_count for c in count}

    def describe_corpus(self):
        """Basic description of the corpus

        Python implementation of https://github.com/alecristia/
        CDSwordSeg/blob/master/recipes/CatalanSpanish/_describe_gold.sh

        Raises
        ------
        If 'phone' and 'word' tokens are not definide in the separator.

        """
        # length of utterances in number of words
        wlen = [len(utt) for utt in self.tokens['word']]

        # the list of all words in the corpus
        words = [w for u in self.tokens['word'] for w in u]

        # ratio of uniques words per chunk of 10 words
        nuniques = [
            len(set(words[x:x+10])) / 10 for x in range(len(words) - 10)]

        stats = {
            # number of utterances
            'nutterances': len(self.corpus),
            # number of single word utterances
            'nutterances_single_word': wlen.count(1),
            # number of word tokens
            'nword_tokens': sum(wlen),
            # number of word types
            'nword_types': len(self.unigram),
            # number of word types with a frequency of 1 (hapax)
            'nword_hapax': list(self.unigram.values()).count(1 / sum(wlen)),
            # mean ratio of uniques words per chunk of 10 words
            'mattr': sum(nuniques) / len(nuniques)
        }

        # average word length in number of phonemes
        if 'phone' in self.separator.levels():
            stats['awl'] = sum(
                len(utt) for utt in self.tokens['phone']) / sum(wlen)

        return stats

    def top_frequency_tokens(self, level, n=None):
        return collections.Counter(
            (t for utt in self.tokens[level] for t in utt)).most_common(n)

    def normalized_segmentation_entropy(self):
        """Return the Normalized Segmentation Entropy computed on `text`

        Token separators must be defined for phones and words.

        Returns
        -------
        entropy : float
            The estimated NSE in bits.

        Raises
        ------


        Notes
        -----
        As explained in [1]_ we are interested in the ambiguity generated
        by the different possible parses that result from a
        segmentation. In order to quantify this idea in general, we define
        a Normalized Segmentation Entropy. To do this, we need to assign a
        probability to every possible segmentation. To this end, we use a
        unigram model where the probability of a lexical item is its
        normalized frequency in the corpus and the probability of a parse
        is the product of the probabilities of its terms. In order to
        obtain a measure that does not depend on the utterance length, we
        normalize by the number of possible boundaries in the
        utterance. So for an utterance of length N, the Normalized
        Segmentation Entropy (NSE) is computed using Shannon formula
        (Shannon, 1948) as follows:

        .. math::

            NSE = -\sum_i P_ilog_2(P_i) / (N-1),

        where :math:`P_i` is the probability of the word :math:`i` and
        :math:`N` the number of phonemes in the text.

        .. [1] A. Fourtassi, B. Börschinger, M. Johnson and E. Dupoux,
           "Whyisenglishsoeasytosegment". In Proceedings of the Fourth Annual
           Workshop on Cognitive Modeling and Computational Linguistics
           (pp. 1-10), 2013.

        """
        # count the number of phones in the text
        N = sum(len(utt) for utt in self.tokens['phone'])

        # word lexicon with probabilities
        P = self.unigram

        # the probability of each word in the text
        probs = (P[word] for utt in self.tokens['word'] for word in utt)

        # compute the entropy
        return -1 * sum(p * log2(p) / (N - 1) for p in probs)


@utils.CatchExceptions
def main():
    """Entry point of the 'wordseg-stats' command"""
    # command initialization
    streamin, streamout, separator, log, args = utils.prepare_main(
        name='wordseg-stats',
        description=__doc__,
        separator=Separator())

    stats = CorpusStatistics(streamin, separator, log=log)
    basics = stats.describe_corpus()
    streamout.write(' '.join(basics.keys()) + ' nse\n')
    streamout.write(
        ' '.join(str(v) if isinstance(v, int) else '{0:0.4f}'.format(v)
                 for v in basics.values()) + ' {0:0.4f}'.format(
                         stats.normalized_segmentation_entropy()) + '\n')


if __name__ == '__main__':
    main()
