# -*- coding: utf-8 -*-
import itertools
import bisect
import random
import copy

class LiteAnt:
    """An ant.

    Ants explore a graph, using alpha and beta to guide their decision making
    process when choosing which edge to travel next.

    :param float alpha: how much pheromone matters
    :param float beta: how much distance matters
    """

    def __init__(self, alpha=1, beta=3):
        # self.alpha = max(alpha, sys.float_info.min)
        # self.beta = max(beta, sys.float_info.min)
        self.alpha = alpha
        self.beta = beta
        self.ans = 0
        self.path = []

    def __repr__(self):
        return f'Ant(alpha={self.alpha}, beta={self.beta})'

    def tour(self, graph):
        """Find a solution to the given graph.

        :param graph: the graph to solve
        :type graph: :class:`networkx.Graph`
        :return: one solution
        :rtype: :class:`~acopy.solvers.Solution`
        """
        solution = self.initialize_solution(graph)
        unvisited = self.get_unvisited_nodes(graph, solution)
        while unvisited:
            node = self.choose_destination(graph, solution.current, unvisited, solution)
            if solution.current in solution.destination_edges:
                solution.add_node(node, [(solution.current, node)], graph.args['edges'][solution.current][node]['time'], graph.args['edges'][solution.current][node]['distance'])
            else:
                solution.add_node(node, self.path, self.ans[node]['time'], self.ans[node]['distance'])
            unvisited.remove(node)
        solution.close()
        return solution

    def initialize_solution(self, graph):
        """Return a newly initialized solution for the given graph.

        :param graph: the graph to solve
        :type graph: :class:`networkx.Graph`
        :return: intialized solution
        :rtype: :class:`~acopy.solvers.Solution`
        """
        start = self.get_starting_node(graph)
        return LiteSolution(graph, start, ant=self)

    def get_starting_node(self, graph):
        """Return a starting node for an ant.

        :param graph: the graph being solved
        :type graph: :class:`networkx.Graph`
        :return: node
        """
        return graph.args['start_point']['id']
        # return np.random.choice(len(graph.nodes))

    def get_unvisited_nodes(self, graph, solution):
        """Return the unvisited nodes.

        :param graph: the graph being solved
        :type graph: :class:`networkx.Graph`
        :param solution: in progress solution
        :type solution: :class:`~acopy.solvers.Solution`
        :return: unvisited nodes
        :rtype: list
        """
        if solution.current in solution.destination_edges:
            nodes = []
            for edge in graph.args['edges'][solution.current]:
                if edge in solution.destination_edges[solution.current]:
                    nodes.append(edge)
        else:
            return [node for node in solution.destination_edges]

    def choose_destination(self, graph, current, unvisited, solution):
        """Return the next node.

        :param graph: the graph being solved
        :type graph: :class:`networkx.Graph`
        :param current: starting node
        :param list unvisited: available nodes
        :return: chosen edge
        """
        if current not in solution.destination_edges:
            self.dijkstra(graph, current, solution.destination_edges)
        if len(unvisited) == 1:
            return unvisited[0]
        scores = self.get_scores(graph, current, unvisited, solution)
        return self.choose_node(unvisited, scores)

    def dijkstra(self, graph, current, destination):
        if current not in graph.args['dijkstra']:
            destination_nodes = set()
            for node in destination:
                destination_nodes.add(node)
            d = {}
            p = {}
            q = set()
            d[current] = {
                'time': 0,
                'distance': 0
            }
            q.add((d[current]['time'], current))
            while len(destination_nodes) > 0:
                elem = q.pop()
                v = elem[1]
                for j in graph.args['edges'][v]:
                    to = j
                    to_time = graph.args['edges'][v][j]['time']
                    to_distance = graph.args['edges'][v][j]['distance']
                    if to in d:
                        if d[v]['time'] + to_time < d[to]['time']:
                            q.remove((d[to]['time'], to))
                            if to in destination_nodes:
                                destination_nodes.remove(to)
                            d[to] = {
                                'time': d[v]['time'] + to_time,
                                'distance': d[v]['distance'] + to_distance
                            }
                            p[to] = v
                            q.add((d[to]['time'], to))
                    else:
                        if to in destination_nodes:
                            destination_nodes.remove(to)
                        d[to] = {
                            'time': d[v]['time'] + to_time,
                            'distance': d[v]['distance'] + to_distance
                        }
                        p[to] = v
                        q.add((d[to]['time'], to))
            ans = {
                'd': d,
                'path': p
            }
            graph.args['dijkstra'] = ans
        else:
            self.path = graph.args['dijkstra']['path']
            self.cost = graph.args['dijkstra']['d'][current]['cost']
            self.distance = graph.args['dijkstra']['d'][current]['distance']

    def get_scores(self, graph, current, destinations, solution):
        """Return scores for the given destinations.

        :param graph: the graph being solved
        :type graph: :class:`networkx.Graph`
        :param current: the node from which to score the destinations
        :param list destinations: available, unvisited nodes
        :return: scores
        :rtype: list
        """
        if current not in solution.destination_edges:
            return [0.0002 for node in destinations]
        edges_cur = graph.args['edges'][current]
        return [edges_cur[node]['score'] for node in destinations]

    def choose_node(self, choices, scores):
        """Return one of the choices.

        Note that ``scores[i]`` corresponds to ``choices[i]``.

        :param list choices: the unvisited nodes
        :param list scores: the scores for the given choices
        :return: one of the choices
        """
        total = sum(scores)
        cumdist = list(itertools.accumulate(scores)) + [total]
        index = bisect.bisect(cumdist, random.random() * total)
        # index = bisect.bisect(cumdist, np.random.uniform() * total)
        return choices[min(index, len(choices) - 1)]

class LiteColony:
    """Colony of ants.

    Effectively this is a source of :class:`~acopy.ant.Ant` for a
    :class:`~acopy.solvers.Solver`.

    :param float alpha: relative factor for edge pheromone
    :param float beta: relative factor for edge weight
    """

    def __init__(self, alpha=1, beta=3):
        self.alpha = alpha
        self.beta = beta

    def get_ants(self, count):
        """Return the requested number of :class:`~acopy.ant.Ant` s.

        :param int count: number of ants to return
        :rtype: list
        """
        return [LiteAnt(**vars(self)) for __ in range(count)]

class LiteSolution:
    """Tour for a graph.

    :param graph: a graph
    :type graph: :class:`networkx.Graph`
    :param start: starting node
    :param ant: ant responsible
    :type ant: :class:`~acopy.ant.Ant`
    """

    def __init__(self, graph, start, ant=None):
        self.destination_edges = copy.deepcopy(graph.args['destination_edges'])
        self.graph = graph
        self.start = start
        self.ant = ant
        self.current = start
        self.cost = 0
        self.path = []
        self.nodes = [start]
        self.total_distance = 0

    def __iter__(self):
        return iter(self.path)

    def __eq__(self, other):
        return self.cost == other.cost

    def __lt__(self, other):
        return self.cost < other.cost

    # def __contains__(self, node):
    #     return node in self.visited or node == self.current

    def __hash__(self):
        return hash(self.get_id())
    
    def get_id(self):
        """Return the ID of the solution.
        The default implementation is just each of the nodes in visited order.
        :return: solution ID
        :rtype: tuple
        """
        first = min(self.nodes)
        index = self.nodes.index(first)
        return tuple(self.nodes[index:] + self.nodes[:index])

    def add_node(self, node, path, cost, distance):
        """Record a node as visited.

        :param node: the node visited
        """
        self.nodes.append(node)
        # self.visited.add(node)
        self._add_node(node, path, cost, distance)

    def close(self):
        """Close the tour so that the first and last nodes are the same."""
        # self._add_node(self.start)
        for edge in self.path:
            self.graph.args['edges'][edge[0]][edge[1]]['amount'] += 1 / self.cost

    def _add_node(self, node, path, cost, distance):
        # self.path.extend(path)
        edge = self.current, node
        self.path.append(edge)
        self.cost += cost
        self.total_distance += distance
        self.current = node

class LiteState:
    """Solver state.

    This class tracks the state of a solution in progress and is passed to each
    plugin hook. Specially it contains:

    ===================== ======================================
    Attribute             Description
    ===================== ======================================
    ``graph``             graph being solved
    ``colony``            colony that generated the ants
    ``ants``              ants being used to solve the graph
    ``limit``             maximum number of iterations
    ``gen_size``          number of ants being used
    ``solutions``         solutions found this iteration
    ``best``              best solution found this iteration
    ``is_new_record``     whether the best is a new record
    ``record``            best solution found so far
    ``previous_record``   previously best solution
    ===================== ======================================

    :param graph: a graph
    :type graph: :class:`networkx.Graph`
    :param list ants: the ants being used
    :param int limit: maximum number of iterations
    :param int gen_size: number of ants to use
    :param colony: source colony for the ants
    :type colony: :class:`~acopy.ant.Colony`
    """

    def __init__(self, graph, ants, limit, gen_size, colony):
        self.graph = graph
        self.ants = ants
        self.limit = limit
        self.gen_size = gen_size
        self.colony = colony
        self.solutions = None
        self.record = None
        self.previous_record = None
        self.is_new_record = False
        self._best = None
        self.iter_record = 0

    @property
    def best(self):
        return self._best

    @best.setter
    def best(self, best):
        self.is_new_record = self.record is None or best < self.record
        if self.is_new_record:
            self.previous_record = self.record
            self.record = best
        self._best = best

class LiteSolver:
    """ACO solver.

    Solvers control the parameters related to pheromone deposit and evaporation.
    If top is not specified, it defaults to the number of ants used to solve a
    graph.

    :param float rho: percentage of pheromone that evaporates each iteration
    :param float q: amount of pheromone each ant can deposit
    :param int top: number of ants that deposit pheromone
    :param list plugins: zero or more solver plugins
    """

    def __init__(self, rho=.03, q=1, iter_without_record=100):
        self.rho = rho
        self.q = q
        self.iter_without_record = iter_without_record

    def solve(self, *args, **kwargs):
        """Find and return the best solution.

        Accepts exactly the same parameters as the :func:`~optimize` method.

        :return: best solution found
        :rtype: :class:`~Solution`
        """
        best = None
        for solution in self.optimize(*args, **kwargs):
            best = solution
        return best

    def optimize(self, graph, colony, gen_size=None, limit=10000):
        """Find and return increasingly better solutions.

        :param graph: graph to solve
        :type graph: :class:`networkx.Graph`
        :param colony: colony from which to source each :class:`~acopy.ant.Ant`
        :type colony: :class:`~acopy.ant.Colony`
        :param int gen_size: number of :class:`~acopy.ant.Ant` s to use
                             (default is one per graph node)
        :param int limit: maximum number of iterations to perform (default is
                          unlimited so it will run forever)
        :return: better solutions as they are found
        :rtype: iter
        """
        # initialize the colony of ants and the graph
        gen_size = gen_size or graph.count_nodes
        ants = colony.get_ants(gen_size)
        for node_from in graph.args['edges']:
            for node_to in node_from:
                node_to.setdefault('pheromone', 0.0002)
                node_to.setdefault('amount', 0)
                node_to.setdefault('score', 0)
        # for u in range(graph.count_nodes):
        #     for v in range(graph.count_nodes):
        #         if u != v:
        #             graph.edges[u][v].setdefault('pheromone', 0.0002)
        #             graph.edges[u][v].setdefault('amount', 0)
        #             graph.edges[u][v].setdefault('score', 0)

        state = LiteState(graph=graph, ants=ants, limit=limit, gen_size=gen_size,
                      colony=colony)

        const_alpha = colony.alpha
        const_beta = colony.beta

        # find solutions and update the graph pheromone accordingly
        for __ in range(limit):
            iter_in_limit = __
            solutions = self.find_solutions(state.graph, state.ants)

            # we want to ensure the ants are sorted with the solutions, but
            # since ants aren't directly comparable, so we interject a list of
            # unique numbers that satifies any two solutions that are equal
            data = list(zip(solutions, range(len(state.ants)), state.ants))
            data.sort()
            solutions, __, ants = zip(*data)

            state.solutions = solutions
            state.ants = ants
            self.global_update(state, const_alpha, const_beta)

            # yield increasingly better solutions
            state.best = state.solutions[0]
            if state.is_new_record:
                state.iter_record = iter_in_limit
                yield state.record
            
            if state.iter_record + self.iter_without_record < iter_in_limit:
                break

    def find_solutions(self, graph, ants):
        """Return the solutions found for the given ants.

        :param graph: a graph
        :type graph: :class:`networkx.Graph`
        :param list ants: the ants to use
        :return: one solution per ant
        :rtype: list
        """
        return [ant.tour(graph) for ant in ants]

    def global_update(self, state, alpha, beta):
        """Perform a global pheromone update.

        :param state: solver state
        :type state: :class:`~State`
        """
        # for u in range(state.graph.count_nodes):
        #     for v in range(state.graph.count_nodes):
        #         if u != v:
        for node_from in graph.args['edges']:
            for node_to in node_from:
                amount = self.q * node_to['amount']
                p = node_to['pheromone']
                node_to['pheromone'] = (1 - self.rho) * p + amount
                node_to['amount'] = 0
                pre = 1 / max(2, node_to['weight'])
                node_to['score'] = p ** alpha * pre ** beta

