"""
Class that deals with different representations of recipe graphs.

This class has functions to read from and write to different formats, as well has functions that
manipulate the graph, e.g. reduction from full graph to action graph.
Internally, the recipe graph is ALWAYS represented as an nx.DiGraph from which this class inherits.
"""
# Last updated by Theresa, Jan 2023

import os
import networkx as nx
import copy
import ast




#########################################################################
## New functions in order to make the whole project based on Network X ##
## author: Theresa                                                     ##
#########################################################################
# TODO: include the functions in the lower part of this file as methods of this class

class RecipeGraph(nx.DiGraph):  
    # class inherits from network X directed graph
    # additional attribute tokenized_recipe_text which could be a list of string tokens

    def __init__(self):
        nx.DiGraph.__init__(self)
        self.recipe_text = None
        self.upos = None
        self.misc = None

    def write_to_conll(self, outfile, tag_format="iob2"):
        """
        CoNLL-U columns: ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC
        """
        # TODO: action graphs and fat graph tags should be in IOB2 format; in general, the choice
        ## between IOB2 and BIOUL should be an argument of this function with default value IOB2.

        c_graph= nx.DiGraph() # create new (temporary) graph s.t. self does not get messed up
        for node in self.nodes:
            if node != "end":
                tokens = self.nodes[node]["label"].split("_")
                if len(tokens) == 2:
                    tokens = tokens[1].split(" ")
                elif len(tokens) == 1:
                    tokens = tokens[0].split(" ")
                else:
                    raise RuntimeError(f"Unexpected value {tokens} for variable 'tokens'.")

                # if node has more than one text token, split node into several nodes s.t. each original token gets its own node
                if tag_format == "iob2":
                    new_nodes = list()
                    first_token = tokens.pop(0)
                    attributes = self.nodes[node]
                    first_attributes = copy.deepcopy(attributes)
                    first_attributes["label"] = first_token
                    first_attributes["node-type"] = "B-" + attributes["node-type"]
                    new_nodes.append((node, first_attributes))
                    for n,t in enumerate(tokens):
                        n += 1
                        # each node corresponds to exactly one token in the original recipe text
                        node_attributes = copy.deepcopy(self.nodes[node])
                        node_attributes["label"] = t
                        node_attributes["node-type"] = "I-" + attributes["node-type"]
                        new_nodes.append((node+n,node_attributes))
                else:
                    # tag_format == "bioul"
                    raise NotImplementedError()
                c_graph.add_nodes_from(new_nodes)

        # Write graph into CoNLL-U file
        with open(outfile, "w", encoding="utf-8") as o:

            for id, token in enumerate(self.recipe_text):
                id += 1

                columns = [str(id), token, "_"]  # ID FORM LEMMA
                columns.append(self.upos[id - 1])  # UPOS

                if id in c_graph: # would that be the case or do I have to compare against node["label"].split(" ")[0].split("_")[0] ?
                    columns.append(c_graph.nodes[id]['node-type']) # XPOS
                    columns.append("_") # FEATS
                    if c_graph.nodes[id]["node-type"].startswith("B"):
                        columns.extend(self.heads_to_columns(id)) # HEAD DEPREL DEPS
                    else:
                        columns.extend(["0", "root", "_"]) # HEAD DEPREL DEPS
                    columns.append(self.misc[id-1]) # MISC (might be more detailed in the future depending on node attributes
                else:
                    columns.extend(["O", "_", "0", "root", "_"]) # XPOS FEATS HEAD DEPREL DEPS
                    columns.append(self.misc[id-1]) # MISC
                o.write("\t".join(columns))
                o.write("\n")
        print(f"NetworkX graph has been transformed in conllu format. File: {os.path.abspath(outfile)}")

    def heads_to_columns(self, node):
        """
        Compile information for edges in one line of the CoNLL-U file for columns 7-9 (HEAD, DEPREL, DEPS)

        Arguments:
            :successors: list of head nodes
        Return:
            :columns: list(str)
        """
        successors = list(self.successors(node))

        # first head and edge label
        if len(successors) > 0:
            first_head = successors.pop()
            first_label = self.edges[node,first_head]["label"] #TODO is this read in properly?
        else:
            # no heads; therefore, fill columns 7 and 8 with 0-edge
            first_head = str(0)
            first_label = "root"

        #additional edges
        if len(successors) > 0:
            additional_edges = []
            #(head,label) pairs for remaining edges
            for head in successors:
                label = self.edges[node,head]["label"]
                additional_edges.append((head,label))
        else:
            # no remaining pairs; therefore, fill column 9 with wildcard placeholder
            additional_edges = "_"

        columns = [str(first_head), first_label, str(additional_edges).replace(" ","")] # TODO: the replace should also be performed in json_to_conll.py (or even better: just implement read_parser_output() in here; then conversion from json to conllu will use this writing function)
        
        return columns
    


    #TODO's

    # reading in from annotation tool file format (implement only if needed; might be available somewhere)
    # I think some coreference files have the same format
    def read_graph_from_brat(self, file):
        raise NotImplementedError

    # from flow file format as used by Y'20 (implement only if needed; might already be available somewhere)
    def read_graph_from_flow(self, file):
        raise NotImplementedError

    # from tagger and parser outputs
    def read_tagger_output_json(self, file):
        raise NotImplementedError
    def read_parser_output_json(self, file):
        raise NotImplementedError
    def read_sandros_parsers_output(self, file):
        raise NotImplementedError


    # Functions to connect Katharina's part of the project:

    def yield_node(token):
        """associates tokens with AMR nodes (graphs?);
        AMR node: """
        # return self[token]["amr"]
        raise NotImplementedError
    def import_amr_nodes(amr_graph):
        """
        Set AMR attribute in recipe graph nodes
        """
        # for node in amr_graph:
            #identify corresponding node in self
            # self[some_token]["amr"] = amr node ID of node
        raise NotImplementedError

# The Jovo prototype needs a function next_step() but maybe we'll have a separate class for that;
# also see dummy class in jovo repo



###################################
## functions for graph reduction ##
## author: Theresa               ##
###################################
"""
Reduce a nx.DiGraph of a full recipe graph into an action graph or fat graph.

FAT graph: contains only nodes with 'food', 'action' or 'tool' labels.
Action graph: contains only nodes with 'action' labels.
(Further types of reduced graphs can be added by defining sets of desired token labels.)

All sub-categories of the labels are merged into the super-categories (i.e. all actions are labelled 'A').
Where nodes are deleted, the edges between the remaining nodes are reconnected s.t. there is an edge between 
each pair of nodes if there was a path between these nodes.
(If tags come in BIOUL tagging scheme, they should be translated into IOB2. --> Issue of write_to_conll() function.)
"""
# Define desired labels
fat_labels = {"A", "Ac", "At", "Af", "Ac2", "F", "T"} # {"A","F","T"} would suffice
action_labels = {"A", "Ac", "At", "Af", "Ac2"} # {"A"} would suffice

def reduced_tag(tag):
    """
    Changes tags Ac, Ac2, At, Af into A.

    TODO:   Naming Issue "tag" vs "label" might lead to confusion:
    TODO:   Up till now, and especially when talking about the CoNLL-U graph representation,
    TODO:   the node type was denoted with something called a "label", e.g. Ac, F, T, ... whereas
    TODO:   the fourth column in the actual CoNLL-U files is called TAGS. A "tag" is composed of
    TODO:   a BIOUL or IOB2 component, indicating the position of the respective token within
    TODO:   a phrase that makes up a node, and a label component describing the node type; tag examples: B-Ac, I-T, etc..
    TODO:   The present conflict stems from the keyword "label" to mean the name of the node,  e.g. 5_the_butter.

    TODO: solution: call recipe labels NE_labels in accordance with Y'20 or even yamakata_labels or maybe node type (as below in read_conllu)
    """
    if tag in {"Ac", "Ac2", "At", "Af"}:
        return "A"
    else:
        return tag

def generate_reduced_graph(G, desired):
    """
    traverse full graph and delete nodes with undesired labels;
    reconnect their predecessor(s) to their successor(s)

    Arguments:
        - G: an nx.DiGraph
        - desired: a List of NE-labels to define which kinds of nodes are to be preserved in the reduced graph
    """

    # copy nodes so we can delete nodes while iterating over them
    _nodes = copy.deepcopy(G.nodes)
    for node in _nodes:
        #print(f"node: {node} (should be int ID)")
        #print(node, G.nodes[node])
        if node != "end":
            tag = reduced_tag(G.nodes[node]['node-type'])
            if not tag in desired:
                # add new edges from all predecessors of node to all successors
                G.add_edges_from([(p,s) for p in G.predecessors(node) for s in G.successors(node)])
                # delete node from G
                G.remove_node(node)
            else:
                # change G[node]['tag'] to its reduced form
                G.nodes[node]['tag'] = tag
        else:
            pass # TODO: do we need to do anything about the end nodes? What do they mean?
    # add label "edge" to all edges; I believe it was the alignment model that expects the label "edge" in action graphs
    for h,t in G.edges:
        G[h][t]['label'] = "edge"
    return G


#################################################################
## functions for reading from and writing to simplified conllu ##
## original author: Iris                                       ##
## edits by: Theresa                                           ##
#################################################################

def edges_from_columns(columns):
    """
    Compiles (edge, edge_label) pairs list for one line in a CoNLL-U file.
    :param columns: list of column values from one line in a CoNLL-U file
    :return: list of (int, string) pairs describing all edges and their labels annotated in this line
    """
    main_edge = (int(columns[6]), columns[7])
    edges = set()
    edges.add(main_edge)
    if columns[8] == "_":
        pass
    elif columns[8].startswith("["):
        try:
            edges = edges.union(set(ast.literal_eval(columns[8]))) # parses IDs as int
        except SyntaxError:
            #SyntaxError: unexpected EOF while parsing
            raise SyntaxError("Elements in column DEPS must not contain white space.")
    else:
        # Sandro's parsers' output format
        _edges = columns[8].split("|")
        for _e in _edges:
            id,label = _e.split(":")
            edges.add(tuple(int(id),label))

    return edges

def _read_graph_conllu(conllu_graph_file, token_ids, origin):
    # TODO: can only read IOB2 tag format so far
    """
    Reads in a graph - either recipe graph or action graph - and extracts all nodes,
    edges, tag labels from the file.
    Input format is CoNLL-U: either the one we have been using where DEPS column values are lists of pairs of strings
    (e.g. "[(29,'t'),(34,'d')]") or the one that Sandro's parsers output (e.g. "29:t|34:d").
    :param conllu_graph_file: path to graph file in conllu format
    :param token_ids: whether the node labels should include the token ids
                e.g. if ids = True then node is labelled with "1_Preheat" otherwise with "Preheat"
    :param origin: name of the recipe which the graph encodes
                    (We want to know where each node in a consolidated graph came from originally.)
    :return: list of nodes, list of edges including labels, tags_dict (key = node, value = tag)
    """
    node_tuples = []
    edge_list = []
    text_tokens = []
    upos_tokens = []
    misc_tokens = []

    parents = []
    children = []

    with open(conllu_graph_file, "r", encoding="utf-8") as grf:
        complete_token = ""
        prev_id = 0
        prev_label = "O"
        for line in grf:
            columns = line.strip().split()
            id = int(columns[0])
            token = columns[1]
            upos = columns[3]
            tag = columns[4]
            misc = columns[9]
            edges = edges_from_columns(columns)

            text_tokens.append(token)
            upos_tokens.append(upos)
            misc_tokens.append(misc)

            if tag == "O":
                if complete_token != "":
                    node_tuple = (prev_id, {"label": complete_token, "node-type": prev_label, "origin": origin})
                    node_tuples.append(node_tuple)
                    complete_token = ""

            elif tag[0] == "B":
                if complete_token != "":
                    node_tuple = (prev_id, {"label": complete_token, "node-type": prev_label, "origin": origin})
                    node_tuples.append(node_tuple)
                if token_ids:
                    complete_token = str(id) + "_" + token
                else:
                    #complete_token = token
                    complete_token = id #TODO: should be `complete_token = token`, right?
                prev_id = id
                prev_label = tag.split("-")[1]
                """if edge_head != "0":
                    edge_list.append((id, edge_head, {"label": edge_label}))
                    parents.append(id)
                    children.append(edge_head)"""
                for edge_head, edge_label in edges:
                    #edge_head = int(edge_head)
                    if edge_head != 0:
                        edge_list.append((id, edge_head, {"label": edge_label}))
                        parents.append(id)
                        children.append(edge_head)

            elif tag[0] == "I":
                complete_token += " " + token
                # TODO: put the following note / explanation into the GitHub Wiki
                ## We didn't use to ignore the annotations on the "I-" tokens. This is mainly an issue of the
                ## tree parser. With the proper graph parser, the parser can generate several edges on one
                ## token (i.e. the "B-" token).
                ## -  Reason for their existence: The parser annotates all tokens of the recipe text (as opposed to all
                ## nodes in the graph, i.e. all meaningful chunks of the text).
                ## - Argument why we'ven been adding such dependency edges to the corresponding node: the parser is
                ## a tree parser and this is the only way to get multiple heads for one node.
                ## Example of where the additional edge reflects the structure of the cooking process (both
                ## heads of "ice cubes" are meaningful:
                ## 130    Serve    _    _    B-Ac    _    137    t    _    _
                ## 131    tea    _    _    B-F    _    130    t    _    _
                ## 132    in    _    _    O    _    0    root    _    _
                ## 133    glasses    _    _    B-T    _    130    d    _    _
                ## 134    over    _    _    O    _    0    root    _    _
                ## 135    ice    _    _    B-F    _    133    f-part-of    _    _
                ## 136    cubes    _    _    I-F    _    137    t    _    _
                ## 137    to    _    _    B-Ac2    _    0    root    _    _
                ## 138    chill    _    _    I-Ac2    _    137    o    _    _
                ## (from github/ara2.../southern_sweet_tea_3.conllu)
                ## - Argument for ignoring dependency annotation on "I-" tokens: Strong bias
                ## multi-token nodes vs single-token nodes. Also, it's not clear whether the parsing
                ## accuracy on these annotations is satisfiable and whether it is actually correct to interpret them as
                ## equally good as the annotations on the "B-" tokens.
                ## Example where the additional edge makes no sense and is actually problematic because it is
                ## creating a cycle:
                ## 137	to	_	_	B-Ac2	_	0	root	_	_
                ## 138	chill	_	_	I-Ac2	_	137	o	_	_
                ## (from github/ara2.../southern_sweet_tea_3.conllu)

        if complete_token != "":
            node_tuple = (prev_id, {"label": complete_token, "node-type": prev_label, "origin": origin})
            node_tuples.append(node_tuple)

    # add 'end' node (TODO: should we add also the start node?)
    for child in children:
        if child not in parents:
            edge_list.append((child, "end", {"label": "end"}))

    # create dictionary with node label as key and node type (cook label) as value
    """
    # just added "node-type" as node attribute above instead of the following code block
    tags_dict=dict()
    with open(conllu_graph_file, "r", encoding="utf-8") as grf:
        for line in grf:
            columns = line.strip().split()
            id = columns[0]
            # id = int(id) # TODO: yes or no?
            tag = columns[4]
            if tag != "O":
                tag = tag.split("-")[1]
            for node_tuple in node_tuples:
                if node_tuple[0] == id:
                    tags_dict[str(node_tuple[1]["label"])] = tag
    """

    return node_tuples, edge_list, text_tokens, upos_tokens, misc_tokens #, tags_dict


def read_graph_from_conllu(conllu_graph_file, token_ids=True):
    """
    Reads into a graph file - either recipe or action graph - in conllu format and transforms it into
    a NetworkX object.
    Input format is CoNLL-U: either the one we have been using where DEPS column values are lists of pairs of strings
    (e.g. "[(29,'t'),(34,'d')]") or the one that Sandro's parsers output (e.g. "29:t|34:d").
    :param graph_file: path to graph file in conllu format
    :return: a graph in NetworkX format
    """
    import collections
    node_list = []

    # conllu_graph_file_name = conllu_graph_file.split('/')[-1]  # remove path and keep only file name
    # conllu_graph_file_name = '.'.join(conllu_graph_file_name.split('.')[:-1])  # remove file ending .conllu
    conllu_graph_file_name = os.path.basename(conllu_graph_file)  # remove path and keep only file name
    conllu_graph_file_name = os.path.splitext(conllu_graph_file_name)[0]  # remove file ending .conllu
    G_name = "G_" + str(
        conllu_graph_file_name)  # TODO: should be a node attribute bc later, in the consolidated graph, we want to know where this node came from
    # TODO: should also be graph attribute

    nodes, edges, text_tokens, upos_tokens, misc_tokens = _read_graph_conllu(conllu_graph_file, token_ids, G_name)

    G = RecipeGraph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    # TODO: it would be better to create a small class with all the information of the original CoNLL-U file
    ## i.e. the column informations like tokens, upos, misc for the whole text (not just tokens that are in graph nodes),
    ## also "origin"
    ## Then, each node and G would have one attribute 'origin' which is an instance of the mentioned class. In particular,
    ## all nodes from the same file (and the graph, if applicable) have the exact same object as origin.
    G.recipe_text = text_tokens
    G.upos = upos_tokens
    G.misc = misc_tokens

    """
    # the following extracts not only the node indices, but also their labels
    for node_tuple in nodes:
        node_tuple = list(node_tuple)
        label = node_tuple[1]["label"]
        node_list.append(label)
    """

    # attributes: key=node, value=dict("label":X, "tag":X, "origin":G_name, "alignment":node_aligned, "amr":corresponding_amr)
    # the attributes list will be expanded if needed
    # attributes can be accessed like this:
    # print(G.nodes['1']['label'])
    """
    nodes_attributes = collections.defaultdict(dict)
    for node_tuple in nodes:
        label=node_tuple[1]["label"]
        nodes_attributes[node_tuple[0]] = {"label":label, "tag":tags_dict[label], "origin":G_name} #"alignment":0, "amr":0}
    nx.set_node_attributes(G, nodes_attributes)
    """

    return G

def write_graph_to_simple_conllu(networkx_graph, outfile):
    """
    #:param outdirectory: it is possible to either specify outdir or it gets automatically created
    :param networkx_graph: path to graph file in NetworkX format
    :return: an action/recipe graph file (so only the lines that contain the tagged tokens are included) in conllu format
    """

    G = networkx_graph

    # Write action graph into CoNLL-U file
    with open((outfile), "w", encoding="utf-8") as o:
        #with open(networkx_graph, "r", encoding="utf-8") as g:
        for node in G.nodes:
            #print(node)
            #outfile = G.nodes[node]["origin"] # sometimes it doesn't work, look at it further
            if node != "end":
                id = node
                #print(node)
                #print(G.nodes[node])
                token = G.nodes[node]["label"]
                try:
                    tag = G.nodes[node]["node-type"]
                except KeyError:
                    # KeyError for "node-type" means that the token is not a node in the recipe graph; therefore, the node type (and consequently the tag) is 'O'
                    tag = "O"
                line = [str(id), token, "_", "_", tag, "_"]

                for edge in G.edges:
                    if edge[0] == node:
                        line.append(str(edge[1])) # TODO: double-check

                o.write("\t".join(line))
                o.write("\n")
    # TODO: bug: Why does the last line appear twice in the output file?
    print("NetworkX graph has been transformed in conllu format")


## Test ##

recipe="recipe.conllu" # perfect example: branched, disconnected, cyclic;
#                        path: "English Yamakata & Mori Corpus\r-200\test\recipe-00043-11216.conllu"


# 1. read graph from file
G=read_graph_from_conllu(recipe)
# 2. write to file
write_graph_to_simple_conllu(G,outfile="duplicate_simple.conllu")
G.write_to_conll("duplicate.conllu")
# 3. reduce graph to FAT graph
G=generate_reduced_graph(G,fat_labels)
# 4. write fat graph
write_graph_to_simple_conllu(G,"fatgraph.conllu")
# 5. further reduce graph to action graph
G=generate_reduced_graph(G,action_labels)
# 6. write action graph to file
write_graph_to_simple_conllu(G,"actiongraph.conllu")
G.write_to_conll("real_actiongraph.conllu")

