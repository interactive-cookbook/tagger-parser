# Author: Siyu Tao, 2022, reusing some code from Theresa Schmidt 2021 (read_prediction.py)
# Last Edit: 2022/07/06

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
Performs labeled evaluation on parser output

Takes AllenNLP prediction for sequence tags (.json) and a corresponding gold file (.conllu). 
Evaluates parser performance by label.
Tested with Python 3.7
"""

import argparse
import json
from ast import literal_eval
import logging
from collections import defaultdict
import csv

def read_prediction_tokens(pred_file):
    """
    Reads in the tokens from the tagger's output file.

    Returns: a String list
    """
    tokens = []
    with open(pred_file, encoding="utf-8") as f:
        for line in f:
            j = json.loads(line)
            tokens.extend(j["words"])
    return tokens

def read_prediction_tags(pred_file):
    """
    Reads in the predicted tags from the tagger's output file. Or the tags used as part of the input for the parser.
    Also determines the source of the data, i.e. whether it was generated by the tagger or the parser.

    Returns: a String list with the predicted tags.
    """
    model_type = None
    tags = []
    with open(pred_file, encoding="utf-8") as f:
        for line in f:
            j = json.loads(line)
            try:
                tags.extend(j["tags"])
                model_type = "tagger"
            except KeyError:
                tags.extend(j["pos"])
                model_type =  "parser"
    return tags, model_type

def read_prediction_dependencies(pred_file):
    """
    Reads in the predictions from the parser's output file.

    Returns: two String list with the predicted heads and dependency names, respectively.
    """
    heads = []
    deps = []
    with open(pred_file, encoding="utf-8") as f:
        for line in f:
            j = json.loads(line)
            heads.extend(j["predicted_heads"])
            deps.extend(j["predicted_dependencies"])
    heads = list(map(str, heads))
    return heads,deps

def read_gold_conllu(gold_file):
    """
    Reads in the gold annotation file in CoNLL-U format (all dependencies, i.e. multiple dependency relations per token, if applicable).

    Returns:
        - unlabelled: a list of sets with head token ID's; len(unlabelled) = num_tokens(gold_file)
        - labelled: a list of sets with (head, dependency name) pairs; len(labelled) = num_tokens(gold_file)
    """
    labelled = []
    unlabelled = []
    with open(gold_file, "r", encoding="utf-8") as f:
        for line in f:
            if line == "\n":
                continue
            line = line.split("\t")
            edges = set()
            edges.add((line[6],line[7]))
            if line[8] != "_":
                for head, dep in literal_eval(line[8]):
                    # literal eval produces int for heads, changed to str
                    edge = (str(head), str(dep))
                    edges.add(edge)
            heads = set([str(h) for h,d in edges])
            labelled.append(edges)
            unlabelled.append(heads)
    return unlabelled, labelled

# ARCHIVED CODE: unlabeled evaluation
# def evaluate_parser_unlabelled(args):
#     # WARNING: unlabelled evaluation!
#     # TODO: implement labelled evaluation or delete for now

#     # read in goldfile
#     gold_unlabelled, _ = read_gold_conllu(args.gold_file)
#     # Read in prediction for the parsing task
#     pred_heads, _ = read_prediction_dependencies(args.pred_file)
#     # Check compatibility
#     if len(gold_unlabelled) != len(pred_heads):
#         raise IOError("Your gold data and predicted data don't match in length.")

#     # Compare prediction and expectation, and count errors
#     tp = 0
#     tn = 0
#     fp = 0
#     fn = 0

#     for gold,pred in zip(gold_unlabelled,pred_heads):
#         # pred is str
#         # gold is set of str
#         if pred in gold:
#             if pred == "0":
#                 # no edge pointing to this token
#                 tn +=1
#             else:
#                 # predicted edge which is also there in gold
#                 tp += 1
#         else:
#             if pred == "0":
#                 # no edge detected where there is at least one
#                 fn += 1
#             else:
#                 # detected edge where there is none in gold
#                 fp += 1
#                 if gold != set(["0"]):
#                     # instead, there should have been at least one other edge pointing to this token
#                     fn += 1 #TODO: only if we evaluate as if it were a graph parser!
#         # If there were more than 1 expected edges in the gold data, there necessarily are false negatives because
#         # the tree parser can only detect one edge per token
#         # TODO: only if we evaluate as if it were a graph parser!
#         fn += (len(gold) - 1)
#     print("TP", tp)
#     print("TN", tn)
#     print("FP", fp)
#     print("FN", fn)
#     print("Precision", (tp/(tp+fp)))
#     print("Recall", (tp/(tp+fn)))
#     print("F1", (tp/(tp+0.5*(fp+fn))))

def evaluate_parser_labelled(args):
    # labelled evaluation!
    # TODO: work-in-progress

    # read in goldfile
    gold_unlabelled, gold_labelled = read_gold_conllu(args.gold_file)
    # Read in prediction for the parsing task
    pred_heads, pred_deps = read_prediction_dependencies(args.pred_file)
    # Check compatibility
    if len(gold_unlabelled) != len(pred_heads):
        raise IOError("Your gold data and predicted data don't match in length.")
    
    # print(len(pred_heads), len(pred_deps))
    # Compare prediction and expectation, and count errors
    tp = {}
    tp = defaultdict(lambda:0,tp)
    fp = {}
    fp = defaultdict(lambda:0,fp)
    fn = {}
    fn = defaultdict(lambda:0,fn)

    for gold_labeled, pred_head, pred_dep in zip(gold_labelled,pred_heads, pred_deps):
        gold = dict()
        for gold_head, gold_dep in gold_labeled:
            gold[gold_head] = gold_dep
        if pred_head == "0":
            # if no edge is predicted
            if pred_head not in gold.keys():
                # but edge exists in gold (i.e. "0" is not in gold)
                for gold_head, gold_dep in gold.items():
                    fn[gold_dep] += 1
        else:
            # if edge is predicted
            for gold_head, gold_dep in gold.items():
                if gold_head == "0":
                    # but edge should not have been predicted - false pos
                    fp[pred_dep] += 1
                elif gold_head == pred_head and gold_dep == pred_dep:
                    # perfect match
                    tp[gold_dep] += 1
                else:
                    # record fn and fp
                    fn[gold_dep] += 1
                    fp[pred_dep] += 1

    # for label in tp.keys():
    #     print("Label:", label)
    #     print("TP", tp[label])
    #     print("FP", fp[label])
    #     print("FN", fn[label])
    #     print("Recall", (tp[label]/(tp[label]+fn[label])))
    #     print("Precision", (tp[label]/(tp[label]+fp[label])))
    #     print("F1", (tp[label]/(tp[label]+0.5*(fp[label]+fn[label]))))
    #     print("-"*15)

    # DEBUG - some labels were never predicted by model (likely errors in data)
    # fn_minus_tp = set(fn.keys()).difference(set(tp.keys()))
    # print("In FP but not in TP:", set(fp.keys()).difference(set(tp.keys())))
    # print("In FN but not in TP:", set(fn.keys()).difference(set(tp.keys())))
    # print("In FN but not in FP:", set(fn.keys()).difference(set(fp.keys())))

    header = ["Label", "TP", "FP", "FN", "Recall", "Precision", "F1"]
    print('{0:<10} {1:>5} {2:>5} {3:>5} {4:<9} {5:<9} {6:<9}'.format(*header))
    for label in sorted(tp.keys()):
        output = label, tp[label], fp[label], fn[label], (tp[label]/(tp[label]+fn[label])), (tp[label]/
            (tp[label]+fp[label])), (tp[label]/(tp[label]+0.5*(fp[label]+fn[label])))
        print('{0:<10} {1:>5} {2:>5} {3:>5} {4:<9.4} {5:<9.4} {6:<9.4}'.format(*output))
    
    # debug
    # for label in fn_minus_tp:
    #     output = label, tp[label], fp[label], fn[label]
    #     print('{0:<10} {1:>5} {2:>5} {3:>5}'.format(*output))
    
    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as o:
            tsv_writer = csv.writer(o, delimiter='\t')
            tsv_writer.writerow(header)
            for label in sorted(tp.keys()):
                output = label, tp[label], fp[label], fn[label], (tp[label]/(tp[label]+fn[label])), (tp[label]/
                    (tp[label]+fp[label])), (tp[label]/(tp[label]+0.5*(fp[label]+fn[label])))
                tsv_writer.writerow(output)


def execute_eval(args):
    logging.info(
        "Evaluating " + args.pred_file + "\nwith respect to " + args.gold_file)

    evaluate_parser_labelled(args)


if __name__ == "__main__":

    # parser for command line arguments
    arg_parser = argparse.ArgumentParser(
        description="""Takes AllenNLP parser prediction and complementary annotated (gold) file. \n
        Prints out labeled evaluation results""")
    arg_parser.add_argument("-p", "--prediction", dest="pred_file", metavar="PRED_FILE", required=True,
                            help="""Prediction file in json format. Output of AllenNLP parser.""")
    arg_parser.add_argument("-g", "--gold", dest="gold_file", metavar="GOLD_FILE", required=True,
                            help="""Annotated (gold) file in CoNLL-U format.""")
    arg_parser.add_argument("-o", "--output", dest="output_file", metavar="OUTPUT_FILE", required=False,
                            help="""Optional: specify output path to write eval results. Print on console only when not specified.""")

    args = arg_parser.parse_args()

    args.debug = False

    #########################
    #### Start execution ####
    #########################

    execute_eval(args)