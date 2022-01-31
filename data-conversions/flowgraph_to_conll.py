# Author: Theresa Schmidt, 2021 <theresas@coli.uni-saarland.de>

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
Transforms data from Yamakata et al. (2020) (based upon a set of papers by Shinsuke Mori)
into files in CoNLL-U and CoNLL-2003 formats.

Tested with Python 3.7
and data by Yamakata Lab@U-Tokyo (https://sites.google.com/view/yy-lab/resource)

References:
    - Yamakata et al. (2020)
      English recipe flow graph corpus.
      In Proceed-ings of the 12th Language Resources and Evaluation Conference,  pages  5187–5194,  Marseille,  France.
      European Language Resources Association.
    - CoNLL-U: https://universaldependencies.org/format.html
"""


import argparse
from collections import defaultdict
import logging


def read_list(filename):
    """
    Read in *.list file, i.e. a tsv file with
    columns paragraph-id, sentence-id, character-id, token, POS-tag, label.

    Returns:
        - id_dict : dictionary from list-style IDs to CoNLL-style token IDs
        - out_lines : list of [token_ID, token, POS_tag, tag] sub-lists
    """
    # Counter for each token to get its token ID (formerly: character IDs)
    counter = 0

    # Flags to identify sentence boundaries
    paragraph_id = "1"
    sent_id = "1"

    # Dictionary from list / flow ID to token ID
    id_dict = dict()

    # List of data corresponding to lines in the CoNLL2003 file;
    # each line is either [] (for sentence boundaries) or [id, token, pos, tag] (for content lines)
    out_lines = []

    with open(filename, "r", encoding="latin-1") as f:
        for line in f:
            # Ignore empty lines and lines with comments marked by line initial '#'
            if line == "\n" or line.startswith("#"):
                pass
            else:
                counter += 1
                data = line.split()

                # Insert line breaks at sentence boundaries
                if data[0] != paragraph_id or data[1] != sent_id:
                    sent_id = data[1]
                    paragraph_id = data[0]
                    out_lines.append([])

                id_dict[(data[0], data[1], data[2])] = counter
                out_lines.append(
                    [counter, data[3], data[4], reverse_tag(data[5])]
                )  # ListIndexOutOfRange can occur bc
                # POS tag of ':' is generally missing. --> Due to encoding problems?
        return id_dict, out_lines


def read_flow(filename, id_dict):
    """
    Reads in *.flow file and returns dependency dictionary.

    Returns:
        out_dict : dictionary from child IDs to dependency type and head IDs
    """
    out_dict = defaultdict(list)

    with open(filename, "r", encoding="latin-1") as f:
        for line in f:
            # Ignore empty lines and lines with comments marked by line initial '#'
            if line == "\n" or line.startswith("#"):
                pass
            else:
                data = line.split()
                # out_dict maps child token to head token and relation type pair(s)
                out_dict[id_dict[(data[0], data[1], data[2])]].append(
                    (id_dict[data[4], data[5], data[6]], data[3])
                )

    return out_dict


def reverse_tag(tag):
    """
    Yamakata et al.(2020) use tags like Ac-I while AllenNLP expects tags like I-Ac
    """
    if tag == "O":
        return tag
    else:
        return tag[-1] + "-" + tag[:-2]


def write_conll2003(lines, outfile):
    with open(outfile, "a", encoding="utf-8") as f:
        for line in lines:
            if line == []:
                f.write("\n")
            else:
                f.write(line[1] + "\t" + line[2] + "\tO\t" + line[3] + "\n")


def write_conllu(lines, flow_dict, outfile):
    with open(outfile, "a", encoding="utf-8") as f:
        for line in lines:
            if line == []:
                pass
            else:
                # Write id,form,lemma,(u)pos,xpos(label),feats
                f.write(
                    str(line[0])
                    + "\t"
                    + line[1]
                    + "\t_\t"
                    + line[2]
                    + "\t"
                    + line[3]
                    + "\t_\t"
                )

                # Find heads
                if flow_dict[line[0]]:
                    if flow_dict[line[0]] == []:
                        raise RuntimeError("Unexpected error!")

                    deps = flow_dict[line[0]]

                    # Write head,deprel,deps,misc
                    f.write(str(deps[0][0]) + "\t" + deps[0][1] + "\t")
                    if len(deps) > 1:
                        f.write(str(deps[1:]) + "\t_\n")
                    else:
                        f.write("_\t_\n")

                else:  # Token has no head, so it must be root

                    # Write head,deprel,deps,misc
                    f.write("0\troot\t_\t_\n")


if __name__ == "__main__":

    # parser for command line arguments
    arg_parser = argparse.ArgumentParser(
        description="""Combine flow graph file (*.flow) and NER file (*.list) into CoNLL files.
                        Output formats: tsv files with CoNLL2003 format 
                        (realized columns: TOKEN, POS-TAG, _ , (COOK) LABEL and with CoNLL-U format 
                        (realized columns: ID, TOKEN, _ , POS-TAG, (COOK) LABEL, _,
                        HEAD, DEPREL, _ , _)."""
    )
    arg_parser.add_argument(
        "list",
        metavar="list_file",
        help="""Path to an annotated file in list format for a a single recipe.
                                (columns: paragraph-id, sentence-id, character-id, token, POS-tag, label""",
    )
    arg_parser.add_argument(
        "flow",
        metavar="flow_file",
        help="""Path to a corresponding file defining a flow graph in flow format.
                                (columns: id of first token in a sequence (paragraph-id, sentence-id, character-id),
                                dependency type, id of first token of head sequence (paragraph-id, sentence-id, 
                                character-id)).""",
    )
    arg_parser.add_argument(
        "-c3",
        "--conll2003",
        dest="conll2003",
        metavar="conll2003_output_file",
        help="""Specify an output file for the ConLL2003 format.
                                Default: prefix from list file + '.conll03'""",
    )
    arg_parser.add_argument(
        "-cu",
        "--conllu",
        dest="conllu",
        metavar="conllu_output_file",
        help="""Specify an output file for the ConLL-U format. Default:
                                prefix from flow file + '.conllu'""",
    )
    arg_parser.add_argument(
        "-o",
        "--output_prefix",
        dest="out",
        metavar="output_prefix",
        help="""Specify a prefix to be used in the output files'
                                names. If file names are specified by -c3 and -cu, -o
                                has no effect. Default: see -c3 and -cu.""",
    )
    args = arg_parser.parse_args()

    # determine file names
    if args.conll2003 == None:
        if args.out:
            args.conll2003 = str(args.out) + ".conll03"
        else:
            args.conll2003 = str(args.list)[:-4] + "conll03"
    if args.conllu == None:
        if args.out:
            args.conllu = str(args.out) + ".conllu"
        else:
            args.conllu = str(args.flow)[:-4] + "conllu"

    # Execution
    logging.info(
        f"zipping {args.list}\n and {args.flow}\ninto {args.conll2003} with "
        f"labels and\n into {args.conllu} with labels and dependecies."
    )
    id_dict, lines = read_list(args.list)
    write_conll2003(lines, args.conll2003)

    flow_dict = read_flow(args.flow, id_dict)
    write_conllu(lines, flow_dict, args.conllu)
