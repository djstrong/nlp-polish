#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'djstrong'

import os
import sys
import shelve

reload(sys)
sys.setdefaultencoding("utf-8")


class Sentence:
    def __init__(self, tokens):
        self.tokens = tokens or []

    @property
    def text(self):
        result = []

        for token in self.tokens:
            result.append(token.separator_before)
            result.append(token.text)

        return ''.join(result)

    def __repr__(self):
        return 'Sentence(%s, %s)' % (self.text, str(self.tokens))


class Token:
    def __init__(self, text, number=0, separator_before=' '):
        """

        :param text:
        :type text: str

        :param number:
        :type number: int
        """
        self.text = text
        self.number = number
        if separator_before == 'space':
            self.separator_before = ' '
        elif separator_before == 'none':
            self.separator_before = ''
        else:
            self.separator_before = separator_before


    def __repr__(self):
        return 'Token(%s, %s, %s, %s)' % (self.text, self.number, self.separator_before, str(self.lemmas))


class TokenGroup():
    def __init__(self):
        self.tokens = []
        # self.super(text, number, separator_before)

    def add_token(self, token):
        self.tokens.append(token)

    @property
    def text(self):
        return ''.join(map(lambda token: token.text, self.tokens))

    @property
    def number(self):
        return self.tokens[0].number

    @property
    def separator_before(self):
        return self.tokens[0].separator_before

    def __repr__(self):
        return 'TokenGroup(%s, %s, %s, %s)' % (self.text, self.number, self.separator_before, str(self.tokens))


class Concraft:
    def __init__(self, port=10101):
        self.port = port

    def tag(self, sentence):
        output = self._run(sentence)
        tokens = self._parse(output)
        return Sentence(self._group_tokens(tokens))


    def _run(self, sentence):
        command = 'export PATH=$PATH:$HOME/.cabal/bin; echo %s | concraft-pl client --port %s | grep -P "(disamb$)|(^[^\t ])"' % (
            sentence.encode('utf-8'), self.port)
        output = os.popen(command).read().decode('utf-8').strip()
        return output

    def _parse(self, output):
        data = []

        lemma_lines = []
        token_line = None
        for line in output.split("\n"):
            if line.startswith("\t"):
                lemma_lines.append(line)
            else:
                if token_line is not None:
                    data.append((token_line, lemma_lines))
                    lemma_lines = []
                token_line = line
        data.append((token_line, lemma_lines))

        tokens = []
        for index, (token_line, lemma_lines) in enumerate(data):
            token = self._construct(token_line, lemma_lines, index)
            tokens.append(token)

        return tokens

    def _construct(self, token_line, lemma_lines, index):
        form, separator_before = token_line.split("\t")
        token = Token(form, separator_before=separator_before, number=index)

        token.lemmas = []

        for lemma_line in lemma_lines:
            lemma, tags, _ = lemma_line.strip().split("\t")
            lemma = LemmaConcraft(form, lemma, tags)
            token.lemmas.append(lemma)

        return token

    def _group_tokens(self, tokens):
        new_tokens = []
        last_token = None
        for token in tokens:
            if token.number == 0 or token.separator_before == ' ':
                if last_token is not None:
                    new_tokens.append(last_token)
                last_token = token
            elif token.separator_before == '':
                if not isinstance(last_token, TokenGroup):
                    token_group = TokenGroup()
                    token_group.add_token(last_token)
                    last_token = token_group
                last_token.add_token(token)

        new_tokens.append(last_token)

        return new_tokens


class LemmaConcraft:
    def __init__(self, form, lemma, tags):
        self.form = form
        self.lemma = lemma
        self.tags = tags

    def __repr__(self):
        return 'LemmaConcraft(%s, %s, %s)' % (self.form, self.lemma, self.tags)


print Concraft().tag(u'chciałabym dupa mają chciałabym żłobionych')

class TokenWeighter:
    pass

class LemmaWeighter:
    def __init__(self, db):
        self.lemma_form_weights = shelve.open('shelve.db', protocol=2)

    def tag(self, sentence):
        if not isinstance(sentence, Sentence):
            raise ValueError('Input to LemmaWeighter need to be Sentence')


class LemmaDesambiguator:
    pass

class MaltParser:
    pass