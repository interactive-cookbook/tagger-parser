import networkx as nx
#recipe="chocolate_glaze_5.conllu" # example of recipe graph
recipe="recipe.conllu" # example of action graph

# still need to organize the functions in a class
# codebase taken from Katharina's work and adjusted/extended by Iris

#########################################################################
## New functions in order to make the whole project based on Network X ##
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
                tag=tag
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

    G_name="G_"+str(conllu_graph_file)

    # attributes: key=node, value=dict("label":X, "tag":X, "origin":G_name, "alignment":node_aligned, "amr":corresponding_amr) # the attributes list will be expanded if needed
    nodes_attributes = collections.defaultdict(dict)
    for node_tuple in nodes:
        label=node_tuple[1]["label"]
        nodes_attributes[node_tuple[0]] = {"label":label, "tag":tags_dict[label], "origin":G_name} #"alignment":0, "amr":0}
    nx.set_node_attributes(G, nodes_attributes)
    # attributes can be accessed like this:
    # print(G.nodes['1']['label'])

    return G

  
def write_graph_to_conllu(networkx_graph):
    """
    #:param outdirectory: it is possible to either specify outdir or it gets automatically created
    :param networkx_graph: path to graph file in NetworkX format
    :return: an action/recipe graph file (so only the lines that contain the tagged tokens are included) in conllu format
    """
    outfile="duplicate.conllu"

    G = networkx_graph

    # Write action graph into CoNLL-U file
    with open((outfile), "w", encoding="utf-8") as o:
        #with open(networkx_graph, "r", encoding="utf-8") as g:
        for node in G.nodes:
            #print(node)
            #outfile = G.nodes[node]["origin"] # sometimes it doesn't work, look at it further
            if node != "end":
                id = node
                print(node)
                print(G.nodes[node])
                token = G.nodes[node]["label"]
                tag = G.nodes[node]["tag"]
                line = [id, token, "_", "_", tag, "_"]

            for edge in G.edges:
                if edge[0] == node:
                    line.append(edge[1]) # TODO: double-check

            o.write("\t".join(line))
            o.write("\n")

    print("NetworkX graph has been transformed in conllu format")
    

# function 1
#print(_read_graph_conllu(recipe,False)[2])
# function 2
G=read_graph_from_conllu(recipe)
# function 3
write_graph_to_conllu(G)
