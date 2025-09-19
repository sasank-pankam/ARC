from pathlib import Path
from . import BaseGraph, InvalidOperationError, log
from src.models import GraphNode
import yaml


class ServiceGraph(BaseGraph):
    def __init__(self, config_file: Path) -> None:
        self.graph = {}  # map that maintains all the nodes.
        # internally the nodes are connected.
        self.loaded_from_config = False

        if config_file.exists() and config_file.is_file():
            self.loaded_from_config = True
            self.config_file = config_file
            self.from_config()

        log.info("loaded graph.")
        log.debug(f"Service mapping= {GraphNode.srevice_to_id}")

    def add(
        self, node_id: int, service: str, parents: set[int], children: set[int]
    ) -> GraphNode:
        if node_id in self.graph:
            this = self.graph[node_id]
        else:
            this = GraphNode(node_id, service)
        self.graph[node_id] = this

        for child_id in children:
            if child_id in self.graph:
                child = self.graph[child_id]
            else:
                child = GraphNode(child_id, service)
            child.parents.add(this)
            this.children.add(child)

        for parent_id in parents:
            if parent_id in self.graph:
                parent = self.graph[parent_id]
            else:
                parent = GraphNode(parent_id, service)
            parent.children.add(this)
            this.parents.add(parent)

        return this

    def remove(self, id):
        if id not in self.graph:
            raise InvalidOperationError(f"{id} not in graph.")

        this = self.graph[id]

        for child in this.children:
            child.parents.remove(this)

        for parent in this.parents:
            parent.children.remove(this)

    def get_connected_down(self, id: int):
        if id not in self.graph:
            raise InvalidOperationError(f"{id} not in graph.")

        curr = [self.graph[id]]
        while len(curr):
            children = set()
            for i in curr:
                children.update(i.children)
            yield from children
            curr = children
        return

    def get_connected(self, id: int):
        if id not in self.graph:
            raise InvalidOperationError(f"{id} not in graph.")

        curr = [self.graph[id]]
        while len(curr):
            parents = set()
            for i in curr:
                parents.update(i.parents)
            yield from parents
            curr = parents
        return

    def get_parents(self, id: int):
        # if id not in self.graph:
        #     raise InvalidOperationError(f"{id} not in graph.")
        #
        # curr = [self.graph[id]]
        # while len(curr):
        #     parents = set()
        #     for i in curr:
        #         parents.update(i.parents)
        #     yield from parents
        #     curr = parents
        # return

        if id not in self.graph:
            raise InvalidOperationError(f"{id} not in graph.")

        this = self.graph[id]
        return this.parents

    def get_dependents(self, id) -> list:
        if id not in self.graph:
            raise InvalidOperationError(f"{id} not in graph.")

        this = self.graph[id]
        return this.children

    def from_config(self):
        if not self.loaded_from_config:
            raise InvalidOperationError("Must not load from the config file")

        with open(self.config_file, "r") as f:
            config = yaml.safe_load(f)

        self.graph.update(
            {n["id"]: GraphNode(n["id"], n["service"]) for n in config["nodes"]}
        )
        for node in config["nodes"]:
            id = node["id"]
            service = node["service"]
            parents = node.get("parents", list())
            children = node.get("children", list())

            self.add(id, service, parents, children)

    def get_node(self, id: int) -> GraphNode:
        if not self.has_node(id):
            raise ValueError
        return self.graph[id]

    def has_node(self, id: int) -> bool:
        return id in self.graph

    async def update(self):
        """Decide the logic for updation request or config or what erver."""
        pass
