class GraphNode:
    srevice_to_id = {}

    def __init__(
        self,
        id: int,
        service: str,
        parents: set | None = None,
        children: set | None = None,
    ) -> None:
        self.id = id
        self.service = service

        # edges with dependency information.
        self.parents: set[GraphNode] = parents or set()
        self.children: set[GraphNode] = children or set()

        self.srevice_to_id[service] = id

    def __hash__(self) -> int:
        return hash(self.id)

    @classmethod
    def get_id(cls, service):
        return cls.srevice_to_id.get(service, -1)

    def __repr__(self):
        return str(self.id)
