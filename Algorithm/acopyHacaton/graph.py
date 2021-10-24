class LiteGrath:
    def __init__(self, node=0, **kwargs):
        self.args = kwargs
        self.count_nodes = node
        self.nodes = []
        self.edges = [[{'weight': None} for __ in range(node)] for _ in range(node)]
    
    def add_node(self, **kwargs):
        self.nodes.append(kwargs)
    
    def add_edge(self, u, v, **kwargs):
        for key, value in kwargs.items():
            self.edges[u][v][key] = value