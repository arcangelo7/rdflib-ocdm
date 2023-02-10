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
    from rdflib import URIRef
    from typing import List, Tuple, Optional

from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timezone

from rdflib import ConjunctiveGraph, Graph

from prov.prov_entity import ProvEntity
from prov.provenance import OCDMProvenance
from prov.snapshot_entity import SnapshotEntity


class OCDMGraphCommons():
    def __init__(self, info_dir: str = "", database: str = ""):
        self.__merge_index = dict()
        self.__entity_index = dict()
        self.provenance = OCDMProvenance(self, info_dir, database)

    def preexisting_finished(self: Graph|ConjunctiveGraph|OCDMGraphCommons, c_time: str = None):
        self.preexisting_graph = deepcopy(self)
        for subject in self.subjects(unique=True):
            self.__entity_index[subject] = {'to_be_deleted': False}
            count = self.provenance.counter_handler.read_counter(subject)
            if count == 0:
                if c_time is None:
                    cur_time: str = datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat(sep="T")
                else:
                    cur_time: str = datetime.fromtimestamp(c_time, tz=timezone.utc).replace(microsecond=0).isoformat(sep="T")
                new_snapshot: SnapshotEntity = self.provenance._create_snapshot(subject, cur_time)
                new_snapshot.has_description(f"The entity '{str(subject)}' has been created.")

    def merge(self: Graph|ConjunctiveGraph|OCDMGraphCommons, res: URIRef, other: URIRef):
        triples_list: List[Tuple] = list(self.triples((None, None, other)))
        for triple in triples_list:
            self.remove(triple)
            new_triple = (triple[0], triple[1], res)
            self.add(new_triple)
        triples_list: List[Tuple] = list(self.triples((other, None, None)))
        for triple in triples_list:
            self.remove(triple)
        self.__merge_index.setdefault(res, set()).add(other)
        self.__entity_index[other]['to_be_deleted'] = True

    @property
    def merge_index(self) -> dict:
        return self.__merge_index

    @property
    def entity_index(self) -> dict:
        return self.__entity_index
    
    def generate_provenance(self, c_time: float = None) -> None:
        return self.provenance.generate_provenance(c_time)
    
    def get_entity(self, res: str) -> Optional[ProvEntity]:
        return self.provenance.get_entity(res)
    
class OCDMGraph(OCDMGraphCommons, Graph):
    def __init__(self, info_dir: str = "", database: str = ""):
        Graph.__init__(self)
        OCDMGraphCommons.__init__(self, info_dir, database)

class OCDMConjunctiveGraph(OCDMGraphCommons, ConjunctiveGraph):
    def __init__(self, info_dir: str = "", database: str = ""):
        ConjunctiveGraph.__init__(self)
        OCDMGraphCommons.__init__(self, info_dir, database)