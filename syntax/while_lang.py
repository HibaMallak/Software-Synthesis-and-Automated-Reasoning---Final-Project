import typing
from final.syntax.tree import Tree
from final.syntax.parsing.earley.earley import Grammar, Parser, ParseTrees
from final.syntax.parsing.silly import SillyLexer

_all_ = ["parse"]

class WhileParser:
    # Tokens and Rules of grammar
    TOKENS = (
        r"(if|then|else|while|do|skip|assert)(?![\w\d_]) "
        r"(?P<id>[^\W\d]\w*) "
        r"(?P<num>[+\-]?\d+) "
        r"(?P<op>[!<>]=|([+\-*/<>=])) "
        r"(?P<hole>\?\?) "                         # Hole handling
        r"(?P<lbracket>\[) "                      # Left bracket for arrays
        r"(?P<rbracket>\]) "                      # Right bracket for arrays
        r"(?P<comma>,) "                          # Comma for array elements
        r"[();]  :=".split()  # Tokens for semicolons, parentheses, etc.
    )

    GRAMMAR = r"""
    S   ->   S1     |   S1 ; S
    S1  ->   skip   |   id := E   |   if E then S else S1   |   while E do S1 | assert E
    S1  ->   id := lbracket num_list rbracket               # Array initialization
    S1  ->   id lbracket E rbracket array_indices := E                          # Array update with nested indices
    S1  ->   id lbracket E rbracket := E  
    S1  ->   id lbracket E rbracket array_indices                                # Array access with nested indices
    S1  ->   ( S )
    E   ->   E0   |   E0 op E0  | num_list
    E0  ->   id   |   num   |   hole |  id lbracket E rbracket  | id lbracket E rbracket array_indices  
    E0  ->   ( E )
    array_indices -> lbracket E rbracket  # Support nested indices
    hole -> ??                                               # hole handling
    num_list ->  E  | num_list comma num_list |  lbracket num_list rbracket
    """

    def __init__(self) -> None:
        self.tokenizer = SillyLexer(self.TOKENS)
        self.grammar = Grammar.from_string(self.GRAMMAR)

    def __call__(self, program_text: str) -> typing.Optional[Tree]:
        tokens = list(self.tokenizer(program_text))

        earley = Parser(grammar=self.grammar, sentence=tokens, debug=False)
        earley.parse()

        if earley.is_valid_sentence():
            trees = ParseTrees(earley)
            assert len(trees) == 1
            return self.postprocess(trees.nodes[0])
        else:
            return None

    def postprocess(self, t: Tree) -> Tree:

        if t.root == "E0" and len(t.subtrees) == 5 and t.subtrees[4].root == "array_indices":
            return Tree("array_access", [self.postprocess(s) for s in [t.subtrees[0], t.subtrees[2], t.subtrees[4]]])



        elif t.root == "S1" and len(t.subtrees) == 7 and t.subtrees[4].root == "array_indices":
            return Tree("array_update", [self.postprocess(s) for s in [t.subtrees[0], t.subtrees[2], t.subtrees[4], t.subtrees[6]]])

        elif t.root in ["γ", "S", "S1", "E", "E0"] and len(t.subtrees) == 1:
            return self.postprocess(t.subtrees[0])

        # Handle assignment and operations
        elif (
                t.root in ["S", "S1", "E"]
                and len(t.subtrees) == 3
                and t.subtrees[1].root in [":=", ";", "op"]
        ):
            return Tree(
                t.subtrees[1].subtrees[0].root,
                [self.postprocess(s) for s in [t.subtrees[0], t.subtrees[2]]],
            )

        elif len(t.subtrees) == 3 and t.subtrees[0].root == "(":
            return self.postprocess(t.subtrees[1])

        elif t.root == "S1" and t.subtrees[0].root in ["if", "while", "assert"]:
            return self.postprocess(Tree(t.subtrees[0].root, t.subtrees[1::2]))

        elif t.root == "num":
            return Tree(t.root, [Tree(int(t.subtrees[0].root))])  # Parse ints

        elif t.root == "hole":  # Parse hole
            return Tree(t.root, [])

        # Handle array initialization
        elif t.root == "S1" and len(t.subtrees) >= 4 and t.subtrees[2].root == "lbracket":
            elements = [self.postprocess(sub) for sub in t.subtrees[3:-1] if sub.root != ","]
            return Tree("array_init", [self.postprocess(t.subtrees[0]), Tree("elements", elements)])

        # Handle nested array access with multiple indices
        elif t.root == "E0" and t.subtrees[1].root == "lbracket":
            array_var = self.postprocess(t.subtrees[0])
            indices = self.collect_indices(t.subtrees[1:])  # Updated function
            return Tree("array_access", [array_var] + indices)

        # Handle nested array update
        elif t.root == "S1" and t.subtrees[1].root == "lbracket":
            array_var = self.postprocess(t.subtrees[0])
            indices = self.collect_indices(t.subtrees[1:-2])
            value = self.postprocess(t.subtrees[-1])  # Updated value
            return Tree("array_update", [array_var] + indices + [value])

        elif t.root == "array_indices":
            # Handle array indices or nested brackets

            indices = []

            for subtree in t.subtrees:

                if subtree.root == "lbracket":  # Found start of index

                    index_expr = self.postprocess(t.subtrees[1])  # Process inside brackets

                    indices.append(index_expr)

            return Tree("array_indices", indices)  # Return all collected indices as a node

        return Tree(t.root, [self.postprocess(s) for s in t.subtrees])

    # Helper function to collect all nested array indices
    def collect_indices(self, subtrees: list) -> list:
        indices = []
        i = 0
        while i < len(subtrees):
            if subtrees[i].root == "lbracket":
                indices.append(self.postprocess(subtrees[i + 1]))  # Process inside brackets
                i += 3  # Move past 'lbracket E rbracket'
            else:
                i += 1
        return indices


def parse(program_text: str) -> typing.Optional[Tree]:
    return WhileParser()(program_text)
