import networkx as nx
import copy
#recipe="chocolate_glaze_5.conllu" # example of recipe graph
recipe="recipe.conllu" # perfect example: branched, disconnected, cyclic;
#                        source: "English Yamakata & Mori Corpus\r-200\test\recipe-00043-11216.conllu"

# still need to organize the functions in a class
# codebase taken from Katharina's work and adjusted/extended by Iris

#########################################################################
## New functions in order to make the whole project based on Network X ##
## author: Theresa                                                     ##
#########################################################################

## Pseudocode sketch for write_to_conllu that produces CoNLL-U files
# in the style we've been using in the project so far;;
## We don't need to keep using them: an alternative would be using
# the below style from Iris&Katharina's code and saving the recipe text in separate files.

"""
class RecipeGraph(nx.DiGraph):  
    # class inherits from network X directed graph
    # additional attribute tokenized_recipe_text which could be a list of string tokens
...

# or

class RecipeGraphComprehension():
    # class with two central attributes: a nx.DiGraph and some representation of the full recipe text
...

write_to_conll():
    for node in graph:
        if node has more than one text token:
            graph.add_nodes_from(list of (token_id,{'text':token_str) tuples)
    for id,token in enumerate(recipe_text):
        if id is a node id in graph:
            write id,token,node['tag'],heads_to_conllu(node.successors) to file
        else:
            write line where tag=O and head=0 with deprel=root and no additional heads
    # Note: action graphs and fat graph tags should be in IOB2 format; in general, the choice
    # between IOB2 and BIOUL should be an argument of this function with default value IOB2.
            
heads_to_conll(list of heads):
    compose tab-separated string with 
    first head, edge label of first head, (head,label) pairs of all additional edges
    
"""


# reading in from annotation tool file format (implement only if needed; might be available somewhere)
# I think some coreference files have the same format
def _read_graph_brat():
    raise NotImplementedError
def read_graph_brat():
    raise NotImplementedError

# from flow file format as used by Y'20 (implement only if needed; might already be available somewhere)
def _read_graph_flow():
    raise NotImplementedError
def read_graph_flow():
    raise NotImplementedError

# from tagger and parser outputs
def _read_tagger_output_json():
    raise NotImplementedError
def read_tagger_output_json():
    raise NotImplementedError
def _read_parser_output_json():
    raise NotImplementedError
def read_parser_output_json():
    raise NotImplementedError

# What does Katharina need from this class?

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
fat_labels = {"Ac", "At", "Af", "Ac2", "F", "T"}
action_labels = {"Ac", "At", "Af", "Ac2"}

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
    """
    if tag in {"Ac", "Ac2", "At", "Af"}:
        return "A"
    else:
        return tag

def generate_reduced_graph(G, desired):
    # possibly simply traverse full graph and delete nodes with undesired labels; reconnect their predecessor(s) to their successor(s)

    # copy nodes so we can delete nodes while iterating over them
    _nodes = copy.deepcopy(G.nodes)
    for node in _nodes:
        print(f"node: {node} (should be int ID)")
        print(node, G.nodes[node])
        if node != "end":
            if not G.nodes[node]['tag'] in desired:
                # add new edges from all predecessors of node to all successors
                G.add_edges_from([(p,s) for p in G.predecessors(node) for s in G.successors(node)])
                # delete node from G
                G.remove_node(node)
            else:
                # change G[node]['tag'] to its reduced form
                G.nodes[node]['tag'] = reduced_tag(G.nodes[node]['tag'])
        else:
            pass # TODO: do we need to do anything about the end nodes? What do they mean?
    # add label "edge" to all edges; I believe it was the alignment model that expects the label "edge" in action graphs
    for h,t in G.edges:
        G[h][t]['label'] = "edge"
    return G


######################################################
## functions for reading from and writing to conllu ##
## original author: Iris                            ##
######################################################

def _read_graph_conllu(conllu_graph_file, token_ids):
    """
    Reads in a graph - either recipe graph or action graph - and extracts all nodes,
    edges, the tag labels from the file
    :param conllu_graph_file: path to graph file in conllu format
    :param token_ids: whether the node labels should include the token ids
                e.g. if ids = True than node is labelled with "1_Preheat" otherwise with "Preheat"
    :return: list of nodes, list of edges including labels, tags_dict (key = node, value = tag)
    """
    node_tuples=[]
    edge_list = []

    parents = []
    children = []

    with open(conllu_graph_file, "r", encoding="utf-8") as grf:
        complete_token = ""
        prev_id = 0
        tags_dict={}
        for line in grf:
            columns = line.strip().split()
            id = columns[0]
            token = columns[1]
            tag = columns[4]
            edge = columns[6]
            edge_label = columns[7]

            if tag == "O":
                if complete_token != "":
                    node_tuple = (prev_id, {"label": complete_token})
                    node_tuples.append(node_tuple)
                    complete_token = ""

            elif tag[0] == "B":
                if complete_token != "":
                    node_tuple = (prev_id, {"label": complete_token})
                    node_tuples.append(node_tuple)
                if token_ids:
                    complete_token = str(id) + "_" + token
                else:
                    #complete_token = token
                    complete_token = id
                prev_id = id
                if edge != "0":
                    edge_list.append((id, edge, {"label": edge_label}))
                    parents.append(id)
                    children.append(edge)

            elif tag[0] == "I":
                complete_token += " " + token

        if complete_token != "":
            node_tuple = (prev_id, {"label": complete_token})
            node_tuples.append(node_tuple)
            complete_token = ""

    # add 'end' node (should we add also the start node?)
    for child in children:
        if child not in parents:
            edge_list.append((child, "end", {"label": "end"}))


    # create dictionary with node as key and tag as value
    with open(conllu_graph_file, "r", encoding="utf-8") as grf:
        for line in grf:
            columns = line.strip().split()
            id = columns[0]
            tag = columns[4]
            if tag != "O":
                tag = tag.split("-")[1]
            for node_tuple in node_tuples:
                if node_tuple[0]==id:
                    tags_dict[str(node_tuple[1]["label"])]=tag

    return node_tuples, edge_list, tags_dict


def read_graph_from_conllu(conllu_graph_file, token_ids=True):
    """
    Reads into a graph file - either recipe or action graph - in conllu format and transforms it into
    a NetworkX object
    :param graph_file: path to graph file in conllu format
    :return: a graph in NetworkX format
    """
    import collections
    node_list=[]
    nodes, edges, tags_dict = _read_graph_conllu(conllu_graph_file, token_ids)

    # the following extracts not only the node indices, but also their labels
    for node_tuple in nodes:
        node_tuple=list(node_tuple)
        label=node_tuple[1]["label"]
        node_list.append(label)

    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    G_name="G_"+str(conllu_graph_file) # TODO: why is this a node attribute - better graph attribute?; Also, why begin with "G_"?

    # attributes: key=node, value=dict("label":X, "tag":X, "origin":G_name, "alignment":node_aligned, "amr":corresponding_amr) # the attributes list will be expanded if needed
    nodes_attributes = collections.defaultdict(dict)
    for node_tuple in nodes:
        label=node_tuple[1]["label"]
        nodes_attributes[node_tuple[0]] = {"label":label, "tag":tags_dict[label], "origin":G_name} #"alignment":0, "amr":0}
    nx.set_node_attributes(G, nodes_attributes)
    # attributes can be accessed like this:
    # print(G.nodes['1']['label'])

    return G

  
def write_graph_to_conllu(networkx_graph, outfile):
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
                tag = G.nodes[node]["tag"]
                line = [id, token, "_", "_", tag, "_"]

            for edge in G.edges:
                if edge[0] == node:
                    line.append(edge[1]) # TODO: double-check

            o.write("\t".join(line))
            o.write("\n")
    # TODO: bug: Why does the last line appear twice in the output file?
    print("NetworkX graph has been transformed in conllu format")
    

## Test ##
# 1. read graph from file
G=read_graph_from_conllu(recipe)
# 2. write to file
write_graph_to_conllu(G,outfile="duplicate.conllu")
# 3. reduce graph to FAT graph
G=generate_reduced_graph(G,fat_labels)
# 4. write fat graph
write_graph_to_conllu(G,"fatgraph.conllu")
# 5. further reduce graph to action graph
G=generate_reduced_graph(G,action_labels)
# 6. write action graph to file
write_graph_to_conllu(G,"actiongraph.conllu")

