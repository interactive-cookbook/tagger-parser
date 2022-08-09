import os
import numpy as np
import argparse


def find_edges_to_nonnodes(folder_path: str):


    unlabelled_nodes_with_outgoing_edges = []
    unlabelled_tokens_with_incoming_edges = []
    tokens_that_are_not_nodes_with_incoming_edges = []

    # go through all files in all subfolders of the folder "folder_path"
    for dish_directory in os.listdir(folder_path):
        for recipe in os.listdir("/".join([folder_path, dish_directory])):
            recipe_path = "/".join([folder_path, dish_directory, recipe])
            with open(recipe_path, "r", encoding="utf-8") as rec:
                nodes_information = dict()
                ids_labelled_tokens = set()
                ids_first_tokens_in_nodes = set()
                ids_tokens_with_incoming_edges = set()

                for line in rec:
                    if line == "\n":
                        # evaluate recipe
                        random_targets, nonhead_targets = evaluate(nodes_information, ids_tokens_with_incoming_edges, ids_labelled_tokens, ids_first_tokens_in_nodes, recipe)
                        unlabelled_tokens_with_incoming_edges.extend(random_targets)
                        tokens_that_are_not_nodes_with_incoming_edges.extend(nonhead_targets)
                        # reset before next recipe
                        nodes_information = dict()
                        ids_labelled_tokens = set()
                        ids_first_tokens_in_nodes = set()
                        ids_tokens_with_incoming_edges = set()

                    else:
                        col_values = line.strip().split("\t")
                        id = col_values[0]
                        token = col_values[1]
                        label = col_values[4]
                        edge = col_values[6]

                        # skip not tagged tokens
                        #if label == "O":
                        #    continue
                        # skip all but the first of multi-token words
                        #if label[0] == "I":
                        #    continue

                        nodes_information[id] = token

                        # check if unlabelled nodes have outgoing edges
                        if label == "O" and edge != "0":
                            unlabelled_nodes_with_outgoing_edges.append((recipe, id, token))

                        elif label != "O":
                            # the current token is labelled
                            ids_labelled_tokens.add(id)
                            if label.startswith("B"):
                                ids_first_tokens_in_nodes.add(id)
                            if edge != "0":
                                # and the connected node has an incoming edge
                                ids_tokens_with_incoming_edges.add(edge)

    return unlabelled_nodes_with_outgoing_edges, unlabelled_tokens_with_incoming_edges, tokens_that_are_not_nodes_with_incoming_edges

def evaluate(nodes_information, ids_tokens_with_incoming_edges, ids_labelled_tokens, ids_first_tokens_in_nodes, recipe):
    random_targets = []
    nonhead_targets = []

    # some files seem to be empty? -> avoid mistakes
    #if not nodes_information:
    #   continue
    
    # check whether all tokens with incoming edges are actually tagged
    for n in ids_tokens_with_incoming_edges:
        if n not in ids_labelled_tokens:
            random_targets.append((recipe, n, nodes_information[n]))

    for n in ids_tokens_with_incoming_edges:
        # check whether the token is a node
        if n not in ids_first_tokens_in_nodes:
            nonhead_targets.append((recipe, n, nodes_information[n]))

    return random_targets, nonhead_targets






if __name__=="__main__":

    arg_parser = argparse.ArgumentParser(
        description="""Checks all files in dir for superfluous edges."""
    )
    arg_parser.add_argument(
        "dir",
        help="""Dircetory containing dishname directories which in turn contain recipes in CoNLL-U format.""",
    )
    args = arg_parser.parse_args()

    #random_sources, random_targets, nonhead_targets = find_edges_to_nonnodes("./ActionGraphs")
    random_sources, random_targets, nonhead_targets = find_edges_to_nonnodes(args.dir)

    print("Unlabelled nodes with outgoing edges:")
    for node in random_sources:
        print(node)

    print("Unlabelled nodes with incoming edges:")
    for node in random_targets:
        print(node)

    print("Tokens that are not node IDs with incoming edges:")
    for node in nonhead_targets:
        print(node)
