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
Traverses a directory structure of Y'20 style recipe graphs and runs the reduce_graph module on all files generating action (or fat) graphs. All files are expected to be in CoNLL-U format, specifying tags in the 5th column. The tags will be changed s.t. all labels starting with 'A' are changed into 'A' and all other labels are changed into O. For the action tags with 'A', BIOUL tags will also be changed into IOB2 tags, i.e. U will be changed into B, and L will be changed into I. Paths between actions in the recipe graph become edges in the action graph.
"""


import os
import argparse
import reduce_graph


def only_actions(line):
    """
    Takes line from tagged (and parsed) file in CoNLL-U format. Tags can be in BIOUL or IOB2 and will be returned in IOB2.

    Returns the line with the tags changed as follows:
    All labels starting with an A are assumed to be action labels and will be changed to A, e.g. B-At -> B-A ; L-Ac2 -> I-A ; U-Af -> B-A.
    All other labels will be changed to O, e.g. U-F -> O ; I-Q -> O .
    """
    if line == "\n":
        return "\n"
    else:
        l = line.split()
        if l[4] == "O":
            return line
        elif l[4][2] == "A":
            # conflate all action labels into 'A'
            # change BIOUL to IOB2
            if l[4].startswith("B"):
                l[4] = "B-A"
            elif l[4].startswith("I"):
                l[4] = "I-A"
            elif l[4].startswith("U"):
                l[4] = "B-A"
            elif l[4].startswith("L"):
                l[4] = "I-A"
            else:
                raise RuntimeError("Unknown BIOUL tag ", l[4])
            # preserve BIOUL, IOB or similar
            # l[4] = l[4][:3]

            r = "\t".join(l)
            r += "\n"
            return r
        else:
            # all non-action tags are changed into O
            l[4] = "O"
            r = "\t".join(l)
            r += "\n"
            return r


def read_print(infile, outfile):
    with open(infile, "r", encoding="utf-8") as i:
        with open(outfile, "w", encoding="utf-8") as o:
            for line in i:
                o.write(only_actions(line))


def traverse(root_dir, out_dir):
    """
    Traverse all subdirectories of 'root_dir' and change the tags in all files found. Result files are saved to a potentially new directory out_dir.
    """
    global sequences, reduced_graph
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    for dirName, subdirList, fileList in os.walk(root_dir):

        outpath = ("\\").join([out_dir] + dirName.split("\\")[1:])
        if not os.path.exists(outpath):
            os.mkdir(outpath)

        for file in fileList:
            infile = dirName + "\\" + os.fsdecode(file)
            outfile = outpath + "\\" + os.fsdecode(file)
            # read_print(infile, outfile)

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

            (
                child2heads,
                head2children,
                desired_tokens_ids,
                sequences,
            ) = reduce_graph.read_file(infile, desired)
            # Compute reduced graph
            reduced_graph = reduce_graph.generate_graph(
                child2heads, head2children, desired_tokens_ids
            )

            # transform graph
            token2heads = reduce_graph.get_token_head_mapping(reduced_graph, sequences)

            # final output
            reduce_graph.write_to_file(
                outpath, infile, os.fsdecode(file), token2heads, desired
            )


if __name__ == "__main__":
    # parser for command line arguments
    arg_parser = argparse.ArgumentParser(
        description="""Traverses a directory structure of Y'20 style recipe graphs and rebuilds it in a new directory OUT_DIR containing action (or fat) graphs. All files are expected to be in CoNLL-U format, specifying tags in the 5th column. The tags will be changed s.t. all labels starting with 'A' are changed into 'A' and all other labels are changed into O. For the action tags with 'A', BIOUL tags will also be changed into IOB2 tags, i.e. U will be changed into B, and L will be changed into I. Paths between actions in the recipe graph become edges in the action graph."""
    )
    arg_parser.add_argument(
        "dir",
        help="""Parent dircetory""",
    )
    arg_parser.add_argument(
        "--out-dir",
        dest="out_dir",
        default="ActionGraphs",
        help="""You may specify an output directory. Default: ./ActionGraphs""",
    )
    args = arg_parser.parse_args()

    traverse(args.dir, args.out_dir)
