import os
import argparse

def only_actions(line):
	"""
	Takes line from tagged file in CoNLL-U format. Tags can be in BIOUL or IOB2 and will be returned in IOB2. 

	Returns the line with the tags changed as follows:
	All labels starting with an A are assumed to be action labels and will be changed to A, e.g. B-At -> B-A ; L-Ac2 -> I-A ; U-Af -> B-A.
	All other labels will be changed to O, e.g. U-F -> O ; I-Q -> O . 
	"""
	if line == "\n":
		return ("\n")
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
			#l[4] = l[4][:3]

			r = ("\t".join(l))
			r += "\n"
			return r
		else:
			# all non-action tags are changed into O
			l[4] = "O"
			r = ("\t".join(l))
			r += "\n"
			return r

def read_print(infile,outfile):
	with open(infile,"r", encoding="utf-8") as i:
		with open(outfile,"w", encoding="utf-8") as o:
			for line in i:
				o.write(only_actions(line))

def traverse(root_dir, out_dir):
	"""
	Traverse all subdirectories of 'root_dir' and change the tags in all files found. Result files are saved to a potentially new directory out_dir.
	"""
	if not os.path.exists("OnlyActions"):
		os.mkdir("OnlyActions")

	for dirName, subdirList, fileList in os.walk(root_dir):

		targetpath = ("\\").join(["OnlyActions"] + dirName.split("\\")[1:])
		if not os.path.exists(targetpath):
			os.mkdir(targetpath)

		for file in fileList:
			sourcefile = dirName + "\\" + os.fsdecode(file)
			targetfile = targetpath + "\\" + os.fsdecode(file)
			read_print(sourcefile, targetfile)




if __name__ == "__main__":
	# parser for command line arguments
    arg_parser = argparse.ArgumentParser(
        description="""Traverses a directory structure and rebuilds it in a new directory OUT_DIR. All files are expected to be in CoNLL-U format, specifying tags in the 5th column. The tags will be changed s.t. all labels starting with 'A' are changed into 'A' and all other labels are changed into O. For the action tags with 'A', BIOUL tags will also be changed into IOB2 tags, i.e. U will be changed into B and L will be changed into I."""
    )
    arg_parser.add_argument(
        "dir",
        help="""Parent dircetory""",
    )
    arg_parser.add_argument(
    	"--out-dir",
    	dest="out_dir",
    	default="OnlyActions",
    	help="""You may specify an output directory. Default: ./OnlyActions""")
    args = arg_parser.parse_args()

    traverse(args.dir, args.out_dir)
