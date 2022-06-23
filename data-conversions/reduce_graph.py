# Author: Theresa Schmidt, 2022 <theresas@coli.uni-saarland.de>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Takes CoNLL-U file with exactly one recipe graph (Yamakata'20 labels) and computes reduced graph for it. The reduced graph either contains only action, tool and food nodes (mode "fat") or only action nodes (mode "a"). BIOUL lables are changed into IOB2 labels. The output is a CoNLL-U file. 
"""


from collections import defaultdict
from ast import literal_eval
from copy import copy
import argparse
import os


def has_target(line):
    # whether the node described in line has at least one head
    if line == ["\n"]:
        return False
    else:
        return line[6] != "0"


def heads(line):
    # Heads of a token are in column 6 and in column 8 (in the latter case paired with dep types)
    if line[8] == "_":
        return [line[6]]
    else:
        return [x for (x, y) in literal_eval(line[8])].append(line[6])


def is_desired_token(line, desired):
    # returns True if the token's seuquence tag (CoNLL-U column 4) is one of the desired labels, i.e. one of
    # {Ac, Ac2, At, Af, F, T}, the set of all actions, tools and foods
    # (for event graphs / action graphs only {Ac, Ac2, At, Af})

    try:
        return line[4] in desired
    except IndexError:
        return False


def graph_columns(index, tag, token2heads):
    # computes CoNLL-U representation of the structural information for one token

    ## tokens without heads
    try:
        heads = copy(token2heads[index])
    except KeyError:
        return ["0", "root", "_"]

    ## tokens which have a head
    if tag.startswith("B"):
        if len(heads) == 1:
            return [str(heads.pop()), "edge", "_"]
        else:
            # print("heads: ", heads)
            # print([str(heads.pop()), "edge"] + [str([(x, "edge") for x in heads])])
            return [str(heads.pop()), "edge"] + [str([(x, "edge") for x in heads])]
    else:
        # in sequences, only the first token is annotated with head(s)
        return ["0", "root", "_"]


def read_file(infile, desired):
    """
    Reads a CoNLL-U file

    Returns:
        - child2heads           dictionary mapping all tokens to a (possibly empty) list of head indices
        - head2children         dictionary mapping all tokens to a (possibly empty) list of child indices
        - desired_tokens_ids    set of indices of all tokens that will be preserved in the reduced graph
        - sequences             list of index lists of all nodes in the reduced graph
    """

    child2heads = defaultdict(list)
    head2children = defaultdict(list)
    desired_tokens_ids = set()
    sequences = []
    seq_buffer = []

    with open(infile, "r", encoding="utf-8") as f:
        for line in f:
            line = line.split("\t")
            if has_target(line):
                targets = heads(line)
                child2heads[line[0]].extend(targets)
                for t in targets:
                    child2heads[t].extend(
                        []
                    )  # s.t. all nodes are listed in c2h-dict in the end
                    head2children[t].append(line[0])
                head2children[line[0]].extend(
                    []
                )  # s.t. all nodes are listed as keys in h2c-dict in the end
            if is_desired_token(line, desired):
                desired_tokens_ids.add(line[0])
                # SEQUENCES
                if line[4].startswith("B"):
                    sequences.append(seq_buffer)
                    seq_buffer = [line[0]]
                elif line[4].startswith("I"):
                    seq_buffer.append(line[0])

    return child2heads, head2children, desired_tokens_ids, sequences


def get_token_head_mapping(reduced_graph, sequences):
    """
    Creates a dictionary that maps tokens to heads in order to represent the reduced graph in CoNLL-U format.
    """

    # Add up the heads of all tokens in a sequence
    seq2heads = defaultdict(set)
    for seq in sequences:
        for child, head in reduced_graph:
            for s in seq:
                if child == s:
                    seq2heads[tuple(seq)].add(head)
                elif head == s:
                    continue  # because usually, the child points to the first token of the head sequence only
    token2heads = dict()
    for seq in seq2heads:
        for s in seq:
            token2heads[s] = seq2heads[seq]

    return token2heads


def iob2(bio):
    """
    If bio comes from the BIOUL tagging scheme, it is changed into the respective IOB2 tag.
    """
    if bio == "B":
        return bio
    elif bio == "I":
        return bio
    elif bio == "U":
        return "B"
    elif bio == "L":
        return "I"
    else:
        raise RuntimeError("Unknown BIOUL tag ", bio)


def reduced_label(label):
    """
    Changes labels Ac, Ac2, At, Af into A; leaves all other labels unchanged.
    """
    if label in {"Ac", "Ac2", "At", "Af"}:
        return "A"
    else:
        return label


def reduced_tag(tag):
    """
    Changes labels Ac, Ac2, At, Af into A and BIOUL tagging scheme into IOB2 tagging scheme.
    """
    bio, label = tag.split("-")
    bio = iob2(bio)
    label = reduced_label(label)

    r = bio + "-" + label
    return r


def write_to_file(outdirectory, infile, outfile, token2heads, desired):

    # Make outfile directory if necessary
    if not os.path.exists(outdirectory):
        os.makedirs(outdirectory)

    # Write event graph into CoNLL-U file
    with open(outdirectory + "/" + outfile, "w", encoding="utf-8") as o:
        with open(infile, "r", encoding="utf-8") as f:
            for line in f:
                line = line.split("\t")
                if is_desired_token(line, desired):
                    # copies line from infile, reduces xpos tags to three letters (e.g. "B-Ac" becomes "B-A"), and replaces HEAD, DEP and DEPS columns with the reduced graph
                    o.write(
                        "\t".join(
                            line[0:4]
                            + [reduced_tag(line[4])]
                            + ["_"]
                            + graph_columns(line[0], line[4], token2heads)
                        )
                    )
                    o.write("\t_\n")
                else:
                    o.write("\t".join(line[0:4] + ["O", "_", "0", "root", "_", "_"]))
                    o.write("\n")


def generate_graph(child2heads, head2children, desired_tokens_ids):
    """
    Builds up a new graph from the structural information in child2heads and head2children.
    """
    agenda = []
    reduced_graph = set()

    # Fill agenda with leaves
    for head in head2children:
        if head2children[head] == []:
            for tgt in child2heads[head]:
                agenda.append(
                    (head, tgt)
                )  # pair of leaf node (most likely an ingredient) and its parent node

    # Determine reduced graph by traversing the original graph
    while agenda:
        # print(agenda)
        child, head = agenda.pop()
        if child in desired_tokens_ids:
            if head in desired_tokens_ids:
                reduced_graph.add((child, head))
                for tgt in child2heads[head]:
                    agenda.append((head, tgt))
            else:
                for tgt in child2heads[head]:
                    agenda.append((child, tgt))
        else:
            for tgt in child2heads[head]:
                agenda.append((head, tgt))

    return reduced_graph


def main(desired, infile, outdirectory, outfile):

    child2heads, head2children, desired_tokens_ids, sequences = read_file(
        infile, desired
    )

    # Compute reduced graph
    reduced_graph = generate_graph(child2heads, head2children, desired_tokens_ids)

    # transform graph
    token2heads = get_token_head_mapping(reduced_graph, sequences)

    # final output
    write_to_file(outdirectory, infile, outfile, token2heads, desired)


if __name__ == "__main__":

    # parser for command line arguments
    arg_parser = argparse.ArgumentParser(
        description="""Takes CoNLL-U file with exactly one recipe graph (Yamakata'20 labels) and computes reduced graph for it. The reduced graph either contains only action, tool and food nodes (mode "fat") or only action nodes (mode "a"). BIOUL lables are changed into IOB2 labels. The output is a CoNLL-U file."""
    )
    arg_parser.add_argument(
        "mode",
        help="""Specify which node types the reduced graph should have. Choose either "fat" or "a". """,
    )
    arg_parser.add_argument(
        "-f", "--file", dest="infile", help="""CoNLL-U file with recipe graph"""
    )
    arg_parser.add_argument(
        "-o",
        "--output_file",
        dest="out",
        metavar="OUTPUT_FILE",
        help="""Output file path. Default: data/dishname/<recipe_name>.conllu   (the dish name and recipe name are derived from the input filename which can have dot-separated prefixes and must have <recipe_name> as second to last element, e.g. 'parsed.tagged.baked_ziti_3.conllu' will have output file path 'data/baked_ziti/baked_ziti_3.conllu')""",
    )
    args = arg_parser.parse_args()

    # define set of 'desired labels'
    if args.mode == "fat":
        desired = {
            "B-Ac",
            "I-Ac",
            "U-Ac",
            "L-Ac",
            "B-At",
            "I-At",
            "U-At",
            "L-At",
            "B-Af",
            "I-Af",
            "U-Af",
            "L-Af",
            "B-Ac2",
            "I-Ac2",
            "U-Ac2",
            "L-Ac2",
            "B-F",
            "I-F",
            "U-F",
            "L-F",
            "B-T",
            "I-T",
            "U-T",
            "L-T",
        }
    elif args.mode == "a":
        desired = {
            "B-Ac",
            "I-Ac",
            "U-Ac",
            "L-Ac",
            "B-At",
            "I-At",
            "U-At",
            "L-At",
            "B-Af",
            "I-Af",
            "U-Af",
            "L-Af",
            "B-Ac2",
            "I-Ac2",
            "U-Ac2",
            "L-Ac2",
        }
    else:
        raise IOError("Please specify a valid mode, i.e. either 'fat' or 'a'.")

    if args.out:
        print(os.path.split(args.out))
        outdirectory, outfilename = os.path.split(args.out)
        if not outdirectory:
            outdirectory = "."
    else:
        # assumption: args.infile = "some_prefix.possibly_even_more_prefixes.dish_name_and_id.conllu"
        name_elements = args.infile.split(".")[-2].split("_")
        outdirectory = "data/" + "_".join(name_elements[:-1])
        outfilename = "_".join(name_elements) + ".conllu"

    main(
        desired,
        args.infile,
        outdirectory,
        outfilename,
    )
