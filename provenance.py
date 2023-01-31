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

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ocdm_graph import OCDMConjunctiveGraph, OCDMGraph
    from typing import Dict, Optional

from datetime import datetime, timezone
from query_utils import get_update_query
from rdflib import ConjunctiveGraph, Graph, URIRef
from counter_handler.counter_handler import CounterHandler
from counter_handler.filesystem_counter_handler import FilesystemCounterHandler
from counter_handler.in_memory_counter_handler import InMemoryCounterHandler
from support import get_se_count
from copy import deepcopy

class OCDMProvenance(object):
    def __init__(self, prov_subj_graph: OCDMConjunctiveGraph|OCDMGraph, info_dir: str = ""):
        self.prov_g = prov_subj_graph

        if info_dir is not None and info_dir != "":
            self.counter_handler: CounterHandler = FilesystemCounterHandler(info_dir)
        else:
            self.counter_handler: CounterHandler = InMemoryCounterHandler()

    def generate_provenance(self, c_time: float = None) -> None:
        if c_time is None:
            cur_time: str = datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat(sep="T")
        else:
            cur_time: str = datetime.fromtimestamp(c_time, tz=timezone.utc).replace(microsecond=0).isoformat(sep="T")
        for cur_subj in self.prov_g.subjects(unique=True):
            last_snapshot_res: Optional[URIRef] = self._retrieve_last_snapshot(cur_subj)
            update_query = get_update_query(
                self._generate_subj_graph(self.prov_g.preexisting_graph, cur_subj), 
                self._generate_subj_graph(self.prov_g, cur_subj))
            print(update_query)
            
    def _retrieve_last_snapshot(self, prov_subject: URIRef) -> Optional[URIRef]:
        subj_count: str = get_se_count(prov_subject)
        try:
            if int(subj_count) <= 0:
                raise ValueError('prov_subject is not a valid URIRef. Extracted count value should be a positive '
                                 'non-zero integer number!')
        except ValueError:
            raise ValueError('prov_subject is not a valid URIRef. Unable to extract the count value!')

        last_snapshot_count: str = str(self.counter_handler.read_counter(int(subj_count)))
        if int(last_snapshot_count) <= 0:
            return None
        else:
            return URIRef(str(prov_subject) + '/prov/se/' + last_snapshot_count)

    def _generate_subj_graph(self, graph: ConjunctiveGraph|Graph, subj: URIRef) -> ConjunctiveGraph|Graph:
        subj_graph: ConjunctiveGraph|Graph = Graph() if isinstance(graph, Graph) else ConjunctiveGraph()
        if isinstance(subj_graph, ConjunctiveGraph):
            for quad in graph.quads((subj, None, None, None)):
                subj_graph.add(quad)
        elif isinstance(subj_graph, Graph):
            for triple in graph.triples((subj, None, None)):
                subj_graph.add(triple)
        return subj_graph