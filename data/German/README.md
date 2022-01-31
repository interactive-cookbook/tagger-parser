# German Corpus

The data is **split** into train, development and test set with proportions 80:10:10.

| | Train | Development | Test
:--- | :---: | :---: | :---:
**# recipes** | 80 | 10 | 10

**POS tags** are included in the corpus but were not used for parsing. The German POS tags (STTS) were annotated with the [ParZu parser](https://github.com/rsennrich/ParZu).

### Parser

The dependency parserrequires data in [CoNLL-U](https://universaldependencies.org/format.html) format where each line represents a token and columns are tab-separated. The relevant columns are FORM, LABEL, HEAD, DEPREL (only FORM and LABEL as input to prediction). The column DEPRELS contains additional dependency relations if a token has more than one head.

Excerpt from the corpus in CoNLL-U format:

```
ID	FORM 	(LEMMA)	POS	LABEL	(FEATS)	HEAD	DEPREL	DEPRELS	(MISC)

82	Dann    _       ADVO    O       _       0       root    _	_ 
83	etwa	_	ADVO	O	_	0	root	_	_ 
84	drei	_	CARD	B-Bedingung	_	86	Zeitangabe	_	_ 
85	Minuten	_	NN	L-Bedingung	_	86	Zeitangabe	_	_ 
86	cremig	_	ADJD	B-Kochschritt	_	91	Nullanapher	_	_ 
87	rühren	_	VVINF	L-Kochschritt	_	91	Nullanapher	_	_ 
88	.	_	$.O	O	_	0	root	_	_ 
89	Den	_	ART	B-Zutat	_	91	Input	_	_ 
90	Rum	_	NN	L-Zutat	_	91	Input	_	_ 
91	unterrühren	_	VVINF	U-Kochschritt	_	100	Nullanapher	_	_ 
```

### Tagger

The tagger requires data in [CoNLL-2003](https://www.clips.uantwerpen.be/conll2003/ner/) format where each line represents a token and columns are tab-separated. The relevant columns are TOKEN and LABEL (only TOKEN as inut to prediction).

Excerpt from the corpus in CoNLL-2003 format:

```
TOKEN POS (CHUNK) LABEL

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
```

The annotation scheme for the German data is explained in [this](https://github.com/TheresaSchmidt/Recipe-Parser/blob/master/Bachelors_Thesis_Schmidt_Theresa.pdf) Bachelors Thesis.
