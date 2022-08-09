import os
import numpy as np
import argparse


def find_disconnected_nodes(folder_path: str):

    disconnected_nodes = []

    # go through all files in all subfolders of the folder "folder_path"
    for dish_directory in os.listdir(folder_path):
        for recipe in os.listdir(os.path.join(folder_path, dish_directory)):
            recipe_path = os.path.join(folder_path, dish_directory, recipe)
            with open(recipe_path, "r", encoding="utf-8") as rec:
                nodes_information = dict()
                ids_nodes_incoming_edges = set()
                ids_nodes_outgoing_edges = set()
                for line in rec:
                    col_values = line.strip().split("\t")
                    id = col_values[0]
                    token = col_values[1]
                    label = col_values[4]
                    edge = col_values[6]

                    # skip not tagged tokens
                    if label == "O":
                        continue
                    # skip all but the first of multi-token words
                    if label[0] == "I":
                        continue

                    nodes_information[id] = token

                    if edge != "0":
                        # the current node has an outgoing edge
                        ids_nodes_outgoing_edges.add(id)
                        # and the connected node has an incoming edge
                        ids_nodes_incoming_edges.add(edge)

                # some files seem to be empty? -> avoid mistakes
                if not nodes_information:
                    continue
                # all nodes with an incoming or an outgoing edge
                nodes_with_an_edge = ids_nodes_incoming_edges.union(ids_nodes_outgoing_edges)
                # all nodes from the graph
                tagged_nodes = set(nodes_information.keys())

                nodes_without_edge = []
                for n in tagged_nodes:
                    if n not in nodes_with_an_edge:
                        nodes_without_edge.append(n)

                for node in nodes_without_edge:
                    disconnected_nodes.append((recipe, node, nodes_information[node]))

    return disconnected_nodes




if __name__=="__main__":

    arg_parser = argparse.ArgumentParser(
        description="""Checks all files in dir for disconnected nodes."""
    )
    arg_parser.add_argument(
        "dir",
        help="""Dircetory containing dishname directories which in turn contain recipes in CoNLL-U format.""",
    )
    args = arg_parser.parse_args()

    #disc_nodes, head_nodes = find_disconnected_graphs("./round2_ActionGraphs")
    disc_nodes = find_disconnected_nodes(args.dir)

    print("Disconnected nodes: ")
    for node in disc_nodes:
        print(node)
