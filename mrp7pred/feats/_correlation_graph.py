"""
Correlation graph to remove highly colinearly features
"""

import pandas as pd
import numpy as np
from numpy import ndarray
from pandas import DataFrame
from typing import List, Dict
from sklearn import datasets  # for test


class Node(object):
    def __init__(self, value: int):
        """
        A simple node class

        Attributes
        --------
        value: int
            Node value
        edge: Dict[Node, int]
            Edges stored in a dictionary with neighbor node as keys
            and PCC as values
        """
        self.value = value  # node value
        self.edge: Dict[Node, float] = dict()

    def link(self, node: Node, pcc: float) -> None:
        """
        Link a new node to current node
        """
        self.edge[node] = pcc

    def unlink(self, node: Node) -> None:
        """
        Remove a neighbor
        """
        if not self.edge.get(node):
            raise ValueError(f"{node.value} is not the neighbor of {self.value}")
        del node.edge[self]  # remove self from node's neighbor
        del self.edge[node]  # remove node from self's neighbor

    def has_leaf_child(self) -> bool:
        """
        Check if current node has leaf child
        """
        for neighbor in self.edge.keys():
            if len(neighbor.edge) == 1:
                return True
        return False

    def get_overall_weight(self) -> float:
        """
        Calculate sum of connected edges
        """
        return sum(self.edge.values())


class CorrelationGraph(object):
    """
    The CorrelationGraph class is composed of Node classes.
    Initialization will build a non-directed graph based on given
    correlation matrix.
    The goal is to remove as many high-colinear features while
    keeping as many total features as possible.

    For a given correlation matrix e.g. (cell values are Pearson Correlations,
    PCC)

        A       B       C       D       E
    A   -       -       -       -       -
    B   0.11    -       -       -       -
    C   0.93    0.96    -       -       -
    D   0.54    0.99    1.00    -       -
    E   0.75    0.95    0.44    0.92    -

    i.e. threshold = 0.90

    1. Class instantiate
    --------
    Instantiating a CorrelationGraph class will transform the matrix
    into a graph.
    Only correlation higher than threshold will be added

    Nodes -> Features
    Edge weights -> PCC
    In this case, we first identfy all nodes with PCC >= threshold

    A-(0.93)-C-(0.96)-B-(0.95)-E
             |        |        |
             |        (0.99)   |
             (1.00)   |        (0.92)
             |_______ D _______|

    After graph initialization, R1 and R2 will keep running until no edge
    exists

    2. R1: Remove nodes which have leaf child
    --------
    First round of iteration will look for nodes which have leaf child, e.g.
    C in above graph. Because removing C is the most efficient way to decrease
    the overall colinearity (edge weight) in the graph.
    The graph now becomes:

    A        B-(0.95)-E
             |        |
             (0.99)   |
             |        (0.92)
             D _______|
    Now we have a single node A and a cycle B-D-E left.

    3. R2: Deal with cycles or pairs
    --------
    If no node has leaf child, second round of iteration will loop through cycles
    and pairs, remove the node with highest overall PCC. In this case, B will be
    removed and the graph becomes:

    A        D-(0.92)-E

    Now we have node with leaf child D and E. The child of the first node being
    iterated will be removed (R1)
    """

    def __init__(self, corr_matrix: DataFrame, threshold: float = 0.9):
        """
        Initialize graph

        Parameters
        --------
        corr_matric: DataFrame
            n * n DataFrame
        threshold: float
            threshold to remove features
        """
        if corr_matrix.shape[0] != corr_matrix.shape[1]:
            raise ValueError("Input dataframe is not (n, n).")

        print("Creating correlation matrix ... ", end="", flush=True)
        self.nodes: List[Node] = []
        self.to_drop: List[int] = []
        self.num_edges: int = 0
        # self.edges = []
        for row in range(corr_matrix.shape[0]):
            node = Node(row)
            if node not in self.nodes:
                self.nodes.append(node)
            for col in range(row + 1, corr_matrix.shape[0]):
                corr = corr_matrix.iloc[row, col]
                if corr >= threshold:
                    node_new = Node(col)
                    node.link(node_new, corr)
                    self.num_edges += 1
                    if node_new not in self.nodes:
                        self.nodes.append(node_new)
        print("Done!")

    def _remove_node(self, node: Node) -> None:
        """
        Remove a node from graph
        """
        if node not in self.nodes:
            raise ValueError("Node does not exist")
        self.nodes.remove(node)
        for neighbor in node.edge.keys():
            neighbor.unlink(node)

    def _remove_nodes_with_leaf_child(self) -> None:
        """
        Remove nodes with leaf child
        """
        # R1
        for node in self.nodes:
            if len(node.edge) == 0:
                self.nodes.remove(node)
                continue
            if node.has_leaf_child():
                self.to_drop.append(node.value)
                # remove node from all neighbors
                for neighbor in node.edge.keys():
                    neighbor.unlink(node)
                    self.num_edges -= 1
                self.nodes.remove(node)

    def _remove_nodes_in_cycles(self) -> None:
        """
        Remove nodes in cycles and pairs
        """
        # R2
        max_weight = 0.0
        max_weight_node = Node(-1)  # place holder
        for node in self.nodes:
            if len(node.edge) == 0:
                self.nodes.remove(node)
                continue
            sum_weight = sum(node.edge.values())
            if sum(node.edge.values()) > max_weight:
                max_weight_node = node
                max_weight = sum_weight
        self.to_drop.append(max_weight_node.value)

    def prune(self):
        """
        Repeat R1 and R2 on current graph
        Cannot use traversing algorithms like BFS, since the graph is
        probabily not fullly connected
        Here we loop through all nodes
        """
        while self.num_edges != 0:
            self._remove_nodes_with_leaf_child()
            self._remove_nodes_in_cycles()


if __name__ == "__main__":
    iris = datasets.load_iris()
    X = iris.data
    y = iris.target
    df = pd.DataFrame(X)
    print("df.head() ... ")
    print(df.head())

    # create correlation matrix
    print("Correlation matrix ... ")
    correlation_matrix = df.corr().abs()
    print(correlation_matrix)

    cg = CorrelationGraph(correlation_matrix)
    cg.prune()
    to_drop = cg.to_drop
    print("To drop ... ")
    print(to_drop)