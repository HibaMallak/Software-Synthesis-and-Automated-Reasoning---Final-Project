import ast

from final.main_program import upd, OP, parse_num_list, eval_expr, verify, wp,break_while_to_ifs, Formula, PVar, Env, Invariant
from z3 import *
from final.syntax.tree import Tree
hole_counter = 0  # holds the number of holes
from final.syntax.while_lang import parse

# find holes in the tree's nodes, and numbers them
def detect_holes(initial: Tree):
    global hole_counter
    if initial.root == "hole":
        hole_id = Int(f"hole_{hole_counter}")
        initial.root = hole_id
        hole_counter += 1
    else:
        if len(initial.subtrees) >= 1:
            detect_holes(initial.subtrees[0])
        if len(initial.subtrees) >= 2:
            detect_holes(initial.subtrees[1])
        if len(initial.subtrees) >= 3:
            detect_holes(initial.subtrees[2])
        if len(initial.subtrees) >= 4:
            detect_holes(initial.subtrees[3])


holes_solver = Solver()  # contains all holes constraints


# using wp calculator, we add all constraints of holes in the code
def add_constraints(tree: Tree, P, Q, linv, examples) -> None:
    global holes_solver
    modified_tree = break_while_to_ifs(tree)
    for io in examples:
        env = io['input']
        Q_out = lambda e: And(Q(e), *[e[key] == value for key, value in io['output'].items()])
        wp_prop = wp(Q_out, modified_tree, linv, env)
        holes_solver.add(wp_prop(env))


# check if holes can be filled correctly
def check_solver() -> ModelRef | None:
    global holes_solver
    if holes_solver.check() == unsat:
        raise ValueError("cannot fill holes")
    else:
        return holes_solver.model()


# fill values for holes
def fill_assignments(assign, tree: Tree):
    if str(tree.root) in assign:
        tree.subtrees = [Tree(str(assign[str(tree.root)]))]
        tree.root = "num"
    else:
        for subtree in tree.subtrees:
            fill_assignments(assign, subtree)


# cleans model from unnecessary assignments
def filter_model(model: ModelRef) -> dict:
    filtered_assignments = {}
    for decl in model.decls():
        name = decl.name()
        if not name.startswith("k!"):  # Ignore identifiers starting with "k!"
            filtered_assignments[name] = model[decl]
        else:
            filtered_assignments[name] = name[2:]
    return filtered_assignments


# checks if holes can be filled, and fills them
def check_fill(tree: Tree):
    global holes_solver
    if holes_solver.check() == unsat:
        raise ValueError("cannot fill holes")
    else:
        assignments = holes_solver.model()
        filtered = filter_model(assignments)
        fill_assignments(filtered, tree)


# Main Function
def main_func(tree: Tree, P: Invariant, Q: Invariant, linv: Invariant, examples) -> bool:
    detect_holes(tree)
    add_constraints(tree, P, Q, linv, examples)
    check_fill(tree)
    check_solver()
    return verify(P, break_while_to_ifs(tree), Q, linv)


