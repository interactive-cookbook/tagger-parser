For the English corpus, the original data can be found at https://sites.google.com/view/yy-lab/resource/english-recipe-ner .

POS tags are included in the corpus but were not used for parsing. The German POS tags (STTS) were annotated with the ParZu parser (https://github.com/rsennrich/ParZu).

Excerpt from the corpus (English):

TOKEN POS _ LABEL

Place	VV0	O	B-Ac
the	AT	O	O
potatoes	NN2	O	B-F
in	II	O	O
a	AT1	O	O
pan	NN1	O	B-T
of	IO	O	O
water	NN1	O	B-F
.	.	O	O
Bring	VV0	O	B-Ac
to	II	O	I-Ac
the	AT	O	I-Ac
boil	NN1	O	I-Ac
and	CC	O	O


Excerpt from the corpus (German):

TOKEN POS _ LABEL

In	APPR	O	U-Praeposition
Muffinformen	NN	O	U-Geraet
füllen	VVFIN	O	U-Kochschritt
.	$.O	O	O
Die	ART	O	B-Zwischenprodukt
Muffins	NN	O	L-Zwischenprodukt
dann	ADVO	O	O
bei	APPR	O	B-Bedingung
180	CARD	O	I-Bedingung
Grad	NN	O	I-Bedingung
Umluft	NN	O	L-Bedingung
22-25	ADJA	O	B-Bedingung
Minuten	NN	O	L-Bedingung
backen	VVINF	O	U-Kochschritt
