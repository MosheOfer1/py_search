"""
Tests for the informed search techniques.
"""
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import random
from math import pow

import networkx as nx

from py_search.base import Node
from py_search.base import Problem
from py_search.base import AnnotatedProblem
from py_search.informed import best_first_search, near_optimal_front_to_end_bidirectional_search, \
    near_optimal_front_to_end_bidirectional_search_threads
from py_search.informed import iterative_deepening_best_first_search
from py_search.informed import beam_search
from py_search.informed import widening_beam_search
from py_search.problems.graph import GraphProblem


class EasyProblem(Problem):

    def successors(self, node):
        yield Node(node.state+1, node, 'expand', node.cost() + 1)
        yield Node(node.state+1, node, 'expand', node.cost() + 1)


class HeuristicHardProblem(Problem):

    def node_value(self, node):
        return -1 * abs(self.goal.state - node.state)

    def successors(self, node):
        if node.state < 15:
            yield Node(node.state + 1, node, 'expand', node.cost() + 1)

        if node.state > -15:
            yield Node(node.state - 1, node, 'expand', node.cost() + 1)


class HeuristicEasyProblem(Problem):

    def node_value(self, node):
        return abs(self.goal.state - node.state)

    def successors(self, node):
        yield Node(node.state + 1, node, 'expand', node.cost() + 1)
        yield Node(node.state + 1, node, 'expand', node.cost() + 1)


def test_best_first_search_without_heuristic():
    """
    Best first search without a heuristic is essentially breadth first.
    """
    for goal in range(1, 10):
        p = AnnotatedProblem(EasyProblem(0, goal))
        sol = next(best_first_search(p, graph=False))
        assert sol.state_node.state == goal
        assert p.nodes_expanded == pow(2, goal + 1) - 2
        assert p.goal_tests == pow(2, goal)

    try:
        p = EasyProblem(0, 10)
        next(best_first_search(p, graph=False, cost_limit=5))
        assert False
    except StopIteration:
        pass


def test_best_first_search_with_heuristic():
    """
    Best heuristic is essentially depth first.
    """
    for goal in range(1, 10):
        p = AnnotatedProblem(HeuristicEasyProblem(0, goal))
        sol = next(best_first_search(p, graph=False))
        assert sol.state_node.state == goal
        assert p.nodes_expanded == goal*2
        assert p.goal_tests == goal+1


def test_iterative_best_first_tree_search():
    """
    Test iterative deepening tree search. When there is a perfect heuristic the
    cost is increased until the heuristic is included, then search proceeds
    directly to the solution.
    """
    for goal in range(1, 10):
        p = AnnotatedProblem(HeuristicEasyProblem(0, goal))
        sol = next(iterative_deepening_best_first_search(p, graph=False))
        assert sol.state_node.state == goal
        assert p.nodes_expanded == goal*2
        assert p.goal_tests == goal+1

    try:
        p = HeuristicEasyProblem(0, 10)
        next(iterative_deepening_best_first_search(p, graph=False,
                                                   max_cost_limit=5))
        assert False
    except StopIteration:
        pass


def test_iterative_deepening_best_first_search():
    """
    Without heuristic it is basically the same as iterative_deepening_search.
    (here is the case where we use graph search).
    """
    for goal in range(1, 10):
        p = AnnotatedProblem(EasyProblem(0, goal))
        sol = next(iterative_deepening_best_first_search(p, graph=True))
        assert sol.state_node.state == goal
        assert p.nodes_expanded == sum([i*2 for i in range(1, goal+2)])-2
        assert p.goal_tests == sum([i+1 for i in range(1, goal+1)])+1


def test_beam1_tree_search():
    """
    Beam search with a width of 1 is like a depth first search, but with no
    backtracking.
    """
    for goal in range(1, 10):
        p = AnnotatedProblem(EasyProblem(0, goal))
        sol = next(beam_search(p, beam_width=1, graph=False))
        assert sol.state_node.state == goal
        assert p.nodes_expanded == goal*2
        assert p.goal_tests == goal+1


def test_beam2_tree_search():
    """
    Beam search with a width of 2 is slightly different. It is like a fusion of
    breadth and depth first searches.
    """
    for goal in range(1, 10):
        p = AnnotatedProblem(EasyProblem(0, goal))
        sol = next(beam_search(p, beam_width=2, graph=False))
        assert sol.state_node.state == goal
        assert p.nodes_expanded == 2 + (goal-1)*4
        assert p.goal_tests == 2 + (goal-1)*2


def test_beam2_graph_search():
    """
    like test_beam2_tree_search, but eliminates duplicate nodes
    """
    for goal in range(1, 10):
        p = AnnotatedProblem(EasyProblem(0, goal))
        sol = next(beam_search(p, beam_width=2, graph=True))
        assert sol.state_node.state == goal
        assert p.nodes_expanded == goal*2


def test_widening_beam_tree_search():
    """
    like test_beam2_tree_search, but eliminates duplicate nodes
    """
    for goal in range(1, 10):
        p = AnnotatedProblem(EasyProblem(0, goal))
        sol = next(widening_beam_search(p, graph=True))
        assert sol.state_node.state == goal
        assert p.nodes_expanded == goal*2
        assert p.goal_tests == goal+1
        assert p.goal_tests == goal+1

    for goal in range(1, 10):
        p = AnnotatedProblem(HeuristicHardProblem(0, goal))
        sol = next(widening_beam_search(p, graph=True))
        assert sol.state_node.state == goal

    try:
        p = HeuristicHardProblem(0, 10)
        next(widening_beam_search(p, max_beam_width=1))
        assert False
    except StopIteration:
        pass


def create_graph_problem(num_nodes):
    edges = []
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            if random.random() < (1 / 10):
                weight = float(int(random.uniform(10, 15)))
                edges.append((i, j, weight))
    G = nx.Graph()

    for edge in edges:
        G.add_edge(int(edge[0]), int(edge[1]), weight=edge[2])

    nodes = list(G.nodes)
    graph = GraphProblem(G, nodes[0], nodes[-1])
    return graph


def test_near_optimal_front_to_end_bidirectional_search():
    for x in range(50, 100, 2):
        g = create_graph_problem(x)
        shortest_path = next(best_first_search(g)).cost()
        sol = next(near_optimal_front_to_end_bidirectional_search(g))
        assert sol.cost() == shortest_path


def test_near_optimal_front_to_end_bidirectional_search_threads():
    for x in range(50, 100, 2):
        g = create_graph_problem(x)
        shortest_path = next(best_first_search(g)).cost()
        sol = next(near_optimal_front_to_end_bidirectional_search_threads(g))
        assert sol.cost() == shortest_path
