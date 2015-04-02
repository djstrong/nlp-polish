#!/usr/bin/env python
# -*- coding: utf-8 -*-
from universal_utils import cd

__author__ = 'djstrong'

import os
import sys
import shelve
import networkx as nx
from pkg_resources import resource_filename, Requirement

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

    def get_all_tokens(self):
        tokens = []
        for token in sentence.tokens:
            if isinstance(token, TokenGroup):
                for subtoken in token.tokens:
                    tokens.append(subtoken)
            else:  # Token
                tokens.append(token)
        return tokens

    def pretty_print(self, indent=0):
        print '  ' * indent, '-', 'Sentence(%s)' % (self.text, )
        for token in self.tokens:
            token.pretty_print(indent + 1)


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
        try:
            return 'Token(%s, %s, %s, %s, %s)' % (
                self.text, self.number, self.separator_before, str(self.lemmas), self.lemma)
        except AttributeError:
            return 'Token(%s, %s, %s, %s)' % (self.text, self.number, self.separator_before, str(self.lemmas))

    def pretty_print(self, indent):
        try:
            print '  ' * indent, '-', 'Token(%s, %s, %s, %s)' % (
                self.text, self.number, self.separator_before, self.lemma)
        except AttributeError:
            print '  ' * indent, '-', 'Token(%s, %s, %s)' % (self.text, self.number, self.separator_before)

        for lemma in self.lemmas:
            lemma.pretty_print(indent + 1)


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

    def pretty_print(self, indent):
        print '  ' * indent, '-', 'TokenGroup(%s, %s, %s)' % (self.text, self.number, self.separator_before)
        for token in self.tokens:
            token.pretty_print(indent + 1)


class Concraft:
    def __init__(self, port=10101):
        self.port = port

    def process(self, sentence):
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
        try:
            form, separator_before = token_line.split("\t")
        except ValueError:
            raise Exception('Probably concraft-pl not working.')
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
        self.weight = -1.0

    def __repr__(self):
        return 'LemmaConcraft(%s, %s, %s, %s)' % (self.form, self.lemma, self.tags, self.weight)

    def get_key(self):
        return ' '.join(map(lambda element: element.encode('utf-8'), [self.form, self.lemma, self.tags]))

    def pretty_print(self, indent):
        print '  ' * indent, '-', self


class TokenWeighter:
    pass


class LemmaWeighter:
    def __init__(self, db=None):
        if db is None:
            db = resource_filename(Requirement.parse("nlp_polish"), "nlp_polish/data/lemma_form_weights.shelve")

        self.lemma_form_weights = shelve.open(db, flag='r', protocol=2)

    def process(self, sentence):
        if not isinstance(sentence, Sentence):
            raise ValueError('Input to LemmaWeighter need to be Sentence')

        for token in sentence.get_all_tokens():
            for lemma in token.lemmas:
                try:
                    lemma.weight = self.lemma_form_weights[lemma.get_key()]
                except KeyError:
                    pass
        return sentence

class LemmaWeightDesambiguator:
    def process(self, sentence):
        for token in sentence.get_all_tokens():
            token.lemma = max(token.lemmas, key=lambda lemma: lemma.weight)
        return sentence


class MaltParser:
    TEMP_FILE = 'fileForMalt'

    def __init__(self, maltparser_path, model_name='skladnica_liblinear_stackeager_final'):
        self.maltparser_path = maltparser_path
        self.model_name = model_name

    def process(self, sentence):
        sentence.dependency_graph  = self.parse_text(sentence)
        return sentence

    def _text2maltparser(self, sentence):
        with open(self.TEMP_FILE, 'w') as file:
            for token in sentence.get_all_tokens():
                if token.text in ['.', ',', '?', '!']:
                    file.write(str(
                        token.number) + '\t' + token.text + '\t' + token.text + '\t' + 'interp' + '\t' + 'interp' + '\t' + '_' + '\t_\t_\t_\t_\n')
                else:
                    tags = token.lemma.tags
                    idx = tags.find(':')
                    if idx == -1:
                        pos = tags
                        other_tags = '_'
                    else:
                        pos = tags[:idx]
                        other_tags = tags[idx + 1:]
                        other_tags = other_tags.replace(':', '|')
                    file.write(str(
                        token.number) + '\t' + token.text + '\t' + token.lemma.lemma + '\t' + pos + '\t' + pos + '\t' + other_tags + '\t_\t_\t_\t_\n')


    def parse_text(self, sentence, output_type='nxgraph'):
        with cd(self.maltparser_path):
            self._text2maltparser(sentence)
            command = 'java -jar maltparser-*.jar -c ' + self.model_name + ' -i ' + self.TEMP_FILE + ' -if appdata/dataformat/conllx.xml -m parse 2>/dev/null'
            output = os.popen(command).read().decode('utf-8').strip()

            if output_type == 'nxgraph':
                graph = nx.DiGraph()
                tokens = sentence.get_all_tokens()
                for i, line in enumerate(output.split('\n')):
                    array = line.split('\t')
                    try:
                        parent_number = int(array[6]) - 1
                    except IndexError:
                        raise Exception('Probably MaltParser not working')
                    number_of_child = i
                    edge_name = array[7]
                    if parent_number != -1:
                        graph.add_edge(tokens[parent_number], tokens[number_of_child], edge=edge_name)
                    else:
                        graph.add_edge(Token('ROOT'), tokens[number_of_child], edge=edge_name)
                return graph
            elif output_type == 'parent_child_edgelabel_list':
                edge_list = []
                for i, line in enumerate(output.split('\n')):
                    array = line.split('\t')
                    parent_number = int(array[6]) - 1
                    number_of_child = i
                    edge_name = array[7]
                    if parent_number != -1:
                        edge_list.append([parent_number, number_of_child, edge_name])
                    else:
                        edge_list.append(['ROOT', number_of_child, edge_name])
                return edge_list
            else:
                raise ValueError('error, output_type can be nxgraph or list parent_child_edgelabel_list')

class Pipeline:
    def __init__(self):
        self.pipeline = []

    def add(self, tool):
        self.pipeline.append(tool)

    def process(self, result):
        for tool in self.pipeline:
            result = tool.process(result)
        return result

if __name__ == "__main__":
    sentence = Concraft().process(u'Oni nie mają nic.')
    print sentence
    LemmaWeighter().process(sentence)
    print sentence
    LemmaWeightDesambiguator().process(sentence)
    print sentence

    sentence.pretty_print()

    MaltParser('/home/kwrobel/malt/Malt/maltparser-1.8.1/').process(sentence)

    pipeline = Pipeline()
    pipeline.add(Concraft())
    pipeline.add(LemmaWeighter())
    pipeline.add(LemmaWeightDesambiguator())
    pipeline.add(MaltParser('/home/kwrobel/malt/Malt/maltparser-1.8.1/'))
    sentence=pipeline.process('asd')
    sentence.pretty_print()