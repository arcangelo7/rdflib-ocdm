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
import json
from ocdm_graph import OCDMConjunctiveGraph, OCDMGraph
from prov.provenance import OCDMProvenance
from rdflib import URIRef, Literal
from prov.snapshot_entity import SnapshotEntity

class TestOCDMProvenance(unittest.TestCase):
    def setUp(self):
        self.subject = 'https://w3id.org/oc/meta/br/0605'

    def test_add_se(self):
        ocdm_graph = OCDMGraph()
        ocdm_prov_memory = OCDMProvenance(ocdm_graph)
        ocdm_graph.add((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('Bella zì')))
        se = ocdm_prov_memory.add_se(prov_subject=URIRef(self.subject))
        self.assertIsNotNone(se)
        self.assertIsInstance(se, SnapshotEntity)
        self.assertEqual(str(se.res), 'https://w3id.org/oc/meta/br/0605/prov/se/1')

    def test_generate_provenance(self):
        cur_time = 1607375859.846196
        cur_time_str = '2020-12-07T21:17:39+00:00'
        with self.subTest('Creation -> No snapshot -> Modification. OCDMGraph. in-memory counter'):
            ocdm_graph = OCDMGraph()
            ocdm_prov_memory = OCDMProvenance(ocdm_graph)
            ocdm_graph.parse(os.path.join('test', 'br.nt'))
            ocdm_graph.preexisting_finished()
            result = ocdm_prov_memory.generate_provenance(cur_time)
            self.assertIsNone(result)
            se_a: SnapshotEntity = ocdm_prov_memory.get_entity(f'{self.subject}/prov/se/1')
            self.assertIsNotNone(se_a)
            self.assertIsInstance(se_a, SnapshotEntity)
            self.assertEqual(URIRef(self.subject), se_a.get_is_snapshot_of())
            self.assertEqual(cur_time_str, se_a.get_generation_time())
            self.assertEqual(f"The entity '{self.subject}' has been created.", se_a.get_description())
            ocdm_prov_memory.generate_provenance(cur_time)
            se_a_2: SnapshotEntity = ocdm_prov_memory.get_entity(f'{self.subject}/prov/se/2')
            self.assertIsNone(se_a_2)
            ocdm_graph.remove((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy')))
            ocdm_graph.add((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('Bella zì')))
            ocdm_prov_memory.generate_provenance()
            se_a_2: SnapshotEntity = ocdm_prov_memory.get_entity(f'{self.subject}/prov/se/2')
            self.assertEqual(se_a_2.get_update_action(), 'DELETE DATA { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy" . }; INSERT DATA { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "Bella zì" . }')
            self.assertEqual(se_a_2.get_description(), f"The entity '{self.subject}' was modified.")
            self.assertEqual(ocdm_prov_memory.counter_handler.prov_counters, {self.subject: 2, 'https://w3id.org/oc/meta/br/0636066666': 1})
        with self.subTest('Modification. OCDMConjunctiveGraph. filesystem counter'):
            ocdm_conjunctive_graph = OCDMConjunctiveGraph()
            ocdm_prov = OCDMProvenance(ocdm_conjunctive_graph, info_dir=os.path.join('test', 'info_dir'))
            ocdm_conjunctive_graph.parse(os.path.join('test', 'br.nq'))
            ocdm_conjunctive_graph.preexisting_finished()
            with open(os.path.join('test', 'info_dir', 'provenance_index.json'), 'w', encoding='utf8') as outfile:
                json_object = json.dumps({self.subject: 1}, ensure_ascii=False, indent=None)
                outfile.write(json_object)
            ocdm_conjunctive_graph.remove((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy')))
            ocdm_conjunctive_graph.add((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('Bella zì')))
            ocdm_prov.generate_provenance()
            se_a_2: SnapshotEntity = ocdm_prov.get_entity(f'{self.subject}/prov/se/2')
            self.assertEqual(se_a_2.get_description(), f"The entity '{self.subject}' was modified.")
            self.assertEqual(se_a_2.get_is_snapshot_of(), URIRef(self.subject))
            self.assertEqual(se_a_2.get_derives_from()[0].res, URIRef('https://w3id.org/oc/meta/br/0605/prov/se/1'))
            self.assertEqual(se_a_2.get_update_action(), 'DELETE DATA { GRAPH <https://w3id.org/oc/meta/br/> { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy" . } }; INSERT DATA { GRAPH <https://w3id.org/oc/meta/br/> { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "Bella zì" . } }')
            with open(os.path.join('test', 'info_dir', 'provenance_index.json'), 'r', encoding='utf8') as outfile:
                self.assertEqual(json.load(outfile), {'https://w3id.org/oc/meta/br/0605': 2, 'https://w3id.org/oc/meta/br/0636066666': 1})
        with self.subTest('Modification. OCDMConjunctiveGraph. database counter'):
            ocdm_conjunctive_graph = OCDMConjunctiveGraph()
            ocdm_prov_db = OCDMProvenance(ocdm_conjunctive_graph, database=os.path.join('test', 'database.db'))
            ocdm_conjunctive_graph.parse(os.path.join('test', 'br.nq'))
            ocdm_conjunctive_graph.preexisting_finished()
            ocdm_prov_db.counter_handler.set_counter(1, self.subject)
            ocdm_conjunctive_graph.remove((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy')))
            ocdm_conjunctive_graph.add((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('Bella zì')))
            ocdm_prov_db.generate_provenance()
            se_a_2: SnapshotEntity = ocdm_prov_db.get_entity(f'{self.subject}/prov/se/2')
            self.assertEqual(se_a_2.get_description(), f"The entity '{self.subject}' was modified.")
            self.assertEqual(se_a_2.get_is_snapshot_of(), URIRef(self.subject))
            self.assertEqual(se_a_2.get_derives_from()[0].res, URIRef('https://w3id.org/oc/meta/br/0605/prov/se/1'))
            self.assertEqual(se_a_2.get_update_action(), 'DELETE DATA { GRAPH <https://w3id.org/oc/meta/br/> { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy" . } }; INSERT DATA { GRAPH <https://w3id.org/oc/meta/br/> { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "Bella zì" . } }')

if __name__ == '__main__':
    unittest.main()