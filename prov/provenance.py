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
    from typing import List, Dict, Optional

from collections import OrderedDict
from datetime import datetime, timezone

from rdflib import ConjunctiveGraph, Graph, URIRef

from counter_handler.counter_handler import CounterHandler
from counter_handler.filesystem_counter_handler import FilesystemCounterHandler
from counter_handler.in_memory_counter_handler import InMemoryCounterHandler
from counter_handler.sqlite_counter_handler import SqliteCounterHandler
from prov.prov_entity import ProvEntity
from prov.snapshot_entity import SnapshotEntity
from query_utils import get_update_query
from support import get_prov_count


class OCDMProvenance(object):
    def __init__(self, prov_subj_graph: OCDMConjunctiveGraph|OCDMGraph, info_dir: str = "", database: str = ""):
        self.prov_g = prov_subj_graph
        # The following variable maps a URIRef with the related provenance entity
        self.res_to_entity: Dict[str, ProvEntity] = dict()
        if info_dir is not None and info_dir != "":
            self.counter_handler: CounterHandler = FilesystemCounterHandler(info_dir)
        elif database is not None and database != "":
            self.counter_handler: SqliteCounterHandler = SqliteCounterHandler(database)
        else:
            self.counter_handler: CounterHandler = InMemoryCounterHandler()

    def generate_provenance(self, c_time: float = None) -> None:
        if c_time is None:
            cur_time: str = datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat(sep="T")
        else:
            cur_time: str = datetime.fromtimestamp(c_time, tz=timezone.utc).replace(microsecond=0).isoformat(sep="T")
        merge_index = self.prov_g.merge_index
        prov_g_subjects = OrderedDict(sorted(self.prov_g.entity_index.items(), key=lambda x: not x[1]['to_be_deleted'], reverse=True))
        for cur_subj in prov_g_subjects:
            last_snapshot_res: Optional[URIRef] = self._retrieve_last_snapshot(str(cur_subj))
            if last_snapshot_res is None:
                # CREATION SNAPSHOT
                cur_snapshot: SnapshotEntity = self._create_snapshot(cur_subj, cur_time)
                cur_snapshot.has_description(f"The entity '{str(cur_subj)}' has been created.")
            else:
                update_query = get_update_query(
                    self._generate_subj_graph(self.prov_g.preexisting_graph, cur_subj), 
                    self._generate_subj_graph(self.prov_g, cur_subj))[0]
                cur_subj_merge_index = {k: v for k, v in merge_index.items() if k == cur_subj}
                snapshots_list = self._get_snapshots_from_merge_list(cur_subj_merge_index)
                if update_query and len(snapshots_list) == 0:
                    # MODIFICATION SNAPSHOT
                    last_snapshot: SnapshotEntity = self.add_se(prov_subject=cur_subj, res=last_snapshot_res)
                    last_snapshot.has_invalidation_time(cur_time)
                    cur_snapshot: SnapshotEntity = self._create_snapshot(cur_subj, cur_time)
                    cur_snapshot.derives_from(last_snapshot)
                    cur_snapshot.has_description(f"The entity '{str(cur_subj)}' was modified.")
                    cur_snapshot.has_update_action(update_query)
                elif len(snapshots_list) > 0:
                    # MERGE SNAPSHOT
                    last_snapshot: SnapshotEntity = self.add_se(prov_subject=cur_subj, res=last_snapshot_res)
                    last_snapshot.has_invalidation_time(cur_time)
                    cur_snapshot: SnapshotEntity = self._create_snapshot(cur_subj, cur_time)
                    cur_snapshot.derives_from(last_snapshot)
                    for snapshot in snapshots_list:
                        cur_snapshot.derives_from(snapshot)
                    if update_query:
                        cur_snapshot.has_update_action(update_query)
                    cur_snapshot.has_description(self._get_merge_description(cur_subj, snapshots_list))
        self.prov_g.preexisting_finished()

    @staticmethod
    def _get_merge_description(cur_subj: URIRef, snapshots_list: List[SnapshotEntity]) -> str:
        merge_description: str = f"The entity '{str(cur_subj)}' was merged"
        is_first: bool = True
        for snapshot in snapshots_list:
            if is_first:
                merge_description += f" with '{snapshot.prov_subject}'"
                is_first = False
            else:
                merge_description += f", '{snapshot.prov_subject}'"
        merge_description += "."
        return merge_description
            
    def _retrieve_last_snapshot(self, prov_subject: URIRef) -> Optional[URIRef]:
        last_snapshot_count: str = str(self.counter_handler.read_counter(str(prov_subject)))
        if int(last_snapshot_count) <= 0:
            return None
        else:
            return URIRef(str(prov_subject) + '/prov/se/' + last_snapshot_count)

    def _generate_subj_graph(self, graph: ConjunctiveGraph|Graph, subj: URIRef) -> ConjunctiveGraph|Graph:
        subj_graph: ConjunctiveGraph|Graph = ConjunctiveGraph() if isinstance(graph, ConjunctiveGraph) else Graph()
        if isinstance(graph, ConjunctiveGraph):
            for quad in graph.quads((subj, None, None, None)):
                subj_graph.add(quad)
        elif isinstance(graph, Graph):
            for triple in graph.triples((subj, None, None)):
                subj_graph.add(triple)
        return subj_graph

    def _create_snapshot(self, cur_subj: URIRef, cur_time: str) -> SnapshotEntity:
        new_snapshot: SnapshotEntity = self.add_se(prov_subject=cur_subj)
        new_snapshot.is_snapshot_of(cur_subj)
        new_snapshot.has_generation_time(cur_time)
        return new_snapshot
    
    def _get_snapshots_from_merge_list(self, cur_subj_merge_index: dict) -> List[SnapshotEntity]:
        snapshots_list: List[SnapshotEntity] = []
        for _, merge_entities in cur_subj_merge_index.items():
            for merge_entity in merge_entities:
                last_entity_snapshot_res: Optional[URIRef] = self._retrieve_last_snapshot(merge_entity)
                if last_entity_snapshot_res is not None:
                    snapshots_list.append(self.add_se(prov_subject=merge_entity, res=last_entity_snapshot_res))
        return snapshots_list

    def add_se(self, prov_subject: URIRef, res: URIRef = None) -> SnapshotEntity:
        if res is not None and res in self.res_to_entity:
            return self.res_to_entity[res]
        count = self._add_prov(str(prov_subject), res)
        se = SnapshotEntity(str(prov_subject), self, count)
        return se

    def _add_prov(self, prov_subject: str, res: URIRef) -> Optional[str]:
        if res is not None:
            res_count: int = int(get_prov_count(res))
            if res_count > self.counter_handler.read_counter(prov_subject):
                self.counter_handler.set_counter(res_count, prov_subject)
            return str(res_count)
        return str(self.counter_handler.increment_counter(prov_subject))

    def get_entity(self, res: str) -> Optional[ProvEntity]:
        if res in self.res_to_entity:
            return self.res_to_entity[res]