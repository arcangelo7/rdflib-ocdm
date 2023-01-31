#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2023 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# Permission to use, copy, modify, and/or distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright notice
# and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.

import unittest
import os
from ocdm_graph import OCDMConjunctiveGraph, OCDMGraph
from provenance import OCDMProvenance
from rdflib import URIRef, Literal

class TestOCDMProvenance(unittest.TestCase):
    def test_generate_provenance(self):
        graph = OCDMGraph()
        graph.parse(os.path.join('test', 'br.nt'))
        graph.preexisting_finished()
        graph.remove((URIRef('https://w3id.org/oc/meta/br/0605'), URIRef('http://purl.org/dc/terms/title'), Literal('A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy')))
        graph.add((URIRef('https://w3id.org/oc/meta/br/0605'), URIRef('http://purl.org/dc/terms/title'), Literal('Bella zì')))
        ocdmprovenance = OCDMProvenance(graph)
        ocdmprovenance.generate_provenance()

    def test_generate_provenance_graph(self):
        graph = OCDMConjunctiveGraph()
        graph.parse(os.path.join('test', 'br.nq'))
        graph.preexisting_finished()
        graph.remove((URIRef('https://w3id.org/oc/meta/br/0605'), URIRef('http://purl.org/dc/terms/title'), Literal('A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy')))
        graph.add((URIRef('https://w3id.org/oc/meta/br/0605'), URIRef('http://purl.org/dc/terms/title'), Literal('Bella zì')))
        ocdmprovenance = OCDMProvenance(graph)
        ocdmprovenance.generate_provenance()

if __name__ == '__main__':
    unittest.main()