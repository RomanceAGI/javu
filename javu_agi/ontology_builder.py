class OntologyNode:
    def __init__(self, concept, parent=None):
        self.concept = concept
        self.parent = parent
        self.children = []

    def add_child(self, child_node):
        if child_node.concept not in [c.concept for c in self.children]:
            self.children.append(child_node)


class OntologyBuilder:
    def __init__(self):
        self.root = OntologyNode("ROOT")

    def add_concept(self, concept, parent_concept="ROOT") -> bool:
        if self.find_node(self.root, concept):
            return False  # already exists
        parent_node = self.find_node(self.root, parent_concept)
        if not parent_node:
            return False
        new_node = OntologyNode(concept, parent=parent_node)
        parent_node.add_child(new_node)
        return True

    def find_node(self, node, concept):
        if node.concept == concept:
            return node
        for child in node.children:
            result = self.find_node(child, concept)
            if result:
                return result
        return None

    def export_tree(self):
        return self._export_node(self.root)

    def _export_node(self, node):
        return {
            "concept": node.concept,
            "children": [self._export_node(c) for c in node.children],
        }
