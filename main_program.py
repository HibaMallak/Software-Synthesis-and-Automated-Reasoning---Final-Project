import typing
import operator
from z3 import (Int, IntVal, ForAll, simplify, Implies, Not, And, Or, Solver, unsat, Ast, Array, IntSort, K, Sort,
                Store, Select)
from final.syntax import Tree

Formula: typing.TypeAlias = Ast | bool
PVar: typing.TypeAlias = str
Env: typing.TypeAlias = dict[PVar, Formula]
Invariant: typing.TypeAlias = typing.Callable[[Env], Formula]

z3_hole_counter = 0  # used to handle array access with hole expressions


OP = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.floordiv,
    "!=": operator.ne,
    ">": operator.gt,
    "<": operator.lt,
    "<=": operator.le,
    ">=": operator.ge,
    "=": operator.eq,
}


# Initialize environment
def mk_env(pvars: set[PVar]) -> Env:
    env = {}
    for v in pvars:
        env[v] = Int(v)
    return env


# Update the environment with new values
def upd(d: Env, k: PVar, v: Formula) -> Env:
    d = d.copy()
    d[k] = v
    return d


# returns a list with array elements, used when initializing arrays
def parse_num_list(tree, env, linv: Invariant):
    if str(tree.root) == "num":
        return [int(tree.subtrees[0].root)]
    elif str(tree.root) == "id":
        return [eval_expr(tree, env, linv)]
    elif str(tree.root) in OP:
        left = parse_num_list(tree.subtrees[0], env, linv)
        right = parse_num_list(tree.subtrees[1], env, linv)
        return [OP[tree.root](left[0], right[0])]
    elif str(tree.root).startswith("hole_"):
        return [tree.root]
    elif str(tree.root) == "array_access":
        return [eval_expr(tree, env, linv)]
    elif str(tree.root) == "num_list":
        numbers = []
        numbers.extend(parse_num_list(tree.subtrees[0], env, linv))
        if len(tree.subtrees) > 2 and str(tree.subtrees[2].root) == "num_list":
            numbers.extend(parse_num_list(tree.subtrees[2], env, linv))
        return numbers
    elif str(tree.root) == "comma":
        return []  # Skip commas
    else:
        raise ValueError(f"Unexpected tree node: {tree.root}")




# Evaluate expressions, now including 2 or 1 dimensional array access with bounds checking
def eval_expr(expr: Tree, env: Env, linv: Invariant) -> Formula:
    global z3_hole_counter
    if str(expr.root) == "num":
        return int(expr.subtrees[0].root)
    elif str(expr.root) == "id":
        var_name = str(expr.subtrees[0].root)
        if var_name in env:
            return env[var_name]
    elif str(expr.root) == "num_list":

        elements = [parse_num_list(expr, env, linv)]
        elements = [item for sublist in elements for item in (sublist if isinstance(sublist, list) else [sublist])]
        elements = [item for sublist in elements for item in (sublist if isinstance(sublist, list) else [sublist])]
        length = len(elements)
        z3_array = K(IntSort(), 0)
        for idx, val in enumerate(elements):
            z3_array = Store(z3_array, idx, val)
        return (z3_array, length, -1)
    elif str(expr.root) == "array_access":
        array_name = expr.subtrees[0].subtrees[0].root
        index_expr = expr.subtrees[1]
        if len(expr.subtrees) == 3:
            inner_index_expr = expr.subtrees[2].subtrees[0]
        else:
            inner_index_expr = -1
        x1 = eval_expr(index_expr, env, linv)
        if inner_index_expr == -1:
            x2 = -1
        else:
            x2 = eval_expr(inner_index_expr, env, linv)

        array_tuple = env[array_name]
        inner_arr_len = array_tuple[2]

        if inner_arr_len != -1 and type(x2) is int and x2 == -1:  # when array is two dimensional, but access is with one index
            raise ValueError("unsupported array access")

        if "hole_" in str(x1): # if first index is hole
            z3_var = Int('hole_z3'+str(z3_hole_counter))
            z3_hole_counter += 1
            s.add(z3_var == x1)
            external_index_value = z3_var
        else:
            external_index_value = IntVal(int(str(eval_expr(index_expr, env, linv))))

        if x2 == -1:
            internal_index_value = IntVal(-1)
        else:
            if "hole_" in str(x2): # if second index is hole
                z3_var = Int('hole_z3'+str(z3_hole_counter))
                z3_hole_counter += 1
                s.add(z3_var == x2)
                internal_index_value = z3_var
            else:
                internal_index_value = IntVal(int(str(eval_expr(inner_index_expr, env, linv))))

        result_get = getter(array_tuple, external_index_value, internal_index_value, env, linv)
        return result_get

    elif str(expr.root) in OP:
        left = eval_expr(expr.subtrees[0], env, linv)
        right = eval_expr(expr.subtrees[1], env, linv)
        result = OP[expr.root](left, right)
        if type(result) is not int and type(result) is not bool:
            result = simplify(result)
        return result
    elif str(expr.root).startswith("hole_"):
        return expr.root
    return False  # Default return for unrecognized expressions


# returns the number of nesting in arrays
def get_depth(array):
    if not isinstance(array, list):
        return 0
    if not array:
        return 1
    return 1 + max(get_depth(sub) for sub in array)


# checks if the array initialization is valid: all elements are of the same type
def is_valid_nested_array(arr):
    if not isinstance(arr, list):
        return True

    first_type = get_depth(arr[0]) if arr else None

    for element in arr:
        current_type = get_depth(element)
        if current_type != first_type:
            return False

        if isinstance(element, list):
            if not is_valid_nested_array(element):
                return False

    return True


# gets the tree from elements
def build_nested(tree, env, linv) -> list:
    tmp_tree = tree
    while str(tmp_tree.root) != 'lbracket' and tmp_tree.subtrees:
        tmp_tree = tmp_tree.subtrees[0]

    if str(tmp_tree.root) == 'lbracket':  # array is nested
        arr = []
        if tree.root == 'num_list':
            if len(tree.subtrees) == 3 and tree.subtrees[0].root == 'lbracket' and tree.subtrees[1].root == 'num_list':
                arr.extend(build_nested(tree.subtrees[1], env, linv))
            else:
                arr.extend(build_nested(tree.subtrees[0], env, linv))
                arr.extend(build_nested(tree.subtrees[2], env, linv))
        return arr
    else:

        numbers = parse_num_list(tree, env, linv)
        length = len(numbers)
        z3_array = K(IntSort(), 0)
        for idx, val in enumerate(numbers):
            z3_array = Store(z3_array, idx, val)
        return [(z3_array, length, -1)]



# used in array initialization, returns a tuple of the array object, array length, and the nested array length.
# if the array is one dimensional, the nested array length is defined as -1
def build_external(tree: Tree, env, linv)->tuple:
    arr = build_nested(tree, env, linv)

    length_in = -1  # for 1-dimensional array, inner_array length is undefined

    if len(arr) == 1 and arr[0][2] == -1:
        length_ex = arr[0][1]
    else:
        length_ex = len(arr)

    tmp_tree = tree
    while str(tmp_tree.root) != 'lbracket' and tmp_tree.subtrees:
        tmp_tree = tmp_tree.subtrees[0]

    if str(tmp_tree.root) == 'lbracket':  # if array is not nested
        length_in = arr[0][1]
        for inner_arr in arr:
            if inner_arr[1] != length_in:
                raise ValueError("array initialization is not valid")
        z3_array = K(IntSort(), K(IntSort(), IntVal(0)))
        for idx, val in enumerate(arr):
            z3_array = Store(z3_array, idx, val[0])

    else:
        z3_array = eval_expr(tree, env, linv)[0]
    return (z3_array, length_ex, length_in) # here the problem


# evaluates and returns the value of array_access
# accessing a 1-dimensional array only with index_inner = -1
def getter(arr_tuple, index_outer, index_inner, env, linv):
    arr = arr_tuple[0]
    array_len = arr_tuple[1]
    inner_array_len = arr_tuple[2]
    inner_array_len_int = int(str(inner_array_len))
    array_len_int = int(str(array_len))

    if type(index_inner) is int and type(index_outer) is int:
        index_outer_int = int(str(index_outer))
        index_inner_int = int(str(index_inner))

        if inner_array_len_int == -1 and index_inner_int != -1:  # accessing a 1-dimensional array only with index_inner =-1
            raise ValueError("Array access out of bounds")
        elif (((index_outer_int < 0 or index_outer_int >= array_len_int) or
              (inner_array_len_int > -1 and (index_inner_int < 0 or index_inner_int >= inner_array_len_int)))
                and linv(env)):  # Boundary check assertion
            raise ValueError("Array access out of bounds")

    elif type(index_outer) is int and type(index_inner) is not int: # only check outer index
        index_outer_int = int(str(index_outer))
        if (index_outer_int < 0 or index_outer_int >= array_len_int) and linv(env):
            raise ValueError("Array access out of bounds")

    elif type(index_outer) is not int and type(index_inner) is int:  # only check inner index
        index_inner_int = int(str(index_inner))
        if inner_array_len_int == -1 and index_inner_int != -1:  # accessing a 1-dimensional array only with index_inner =-1
            raise ValueError("Array access out of bounds")
        elif (inner_array_len_int > -1 and (index_inner_int < 0 or index_inner_int >= inner_array_len_int)) and linv(env):  # Boundary check assertion
            raise ValueError("Array access out of bounds")

    if inner_array_len == -1:  # array is not nested
        return simplify(Select(arr, index_outer))
    else:
        return simplify(Select(Select(arr, index_outer), index_inner))


# Collect variables
def collect_vars(ast: Tree) -> set[str]:
    vars = set()
    if str(ast.root) == "id":
        vars.add(ast.subtrees[0].root)
    else:
        for subtree in ast.subtrees:
            vars.update(collect_vars(subtree))
    return vars


def find_holes(ast: Tree) -> set[str]:
    holes = set()
    if str(ast.root).startswith("hole_"):
        holes.add(str(ast.root))
    else:
        for subtree in ast.subtrees:
            holes.update(find_holes(subtree))
    return holes


# Convert while loops into 10 nested if statements
def break_while_to_ifs(tree: Tree) -> Tree:
    if str(tree.root) == "while":
        condition = tree.subtrees[0]  # Loop condition
        body = tree.subtrees[1]  # Loop body

        # Create the first if statement for unwinding
        current_if = Tree("if", [condition, body, Tree("skip")])

        # Nest additional if statements up to 10 iterations
        for _ in range(9):
            current_if = Tree("if", [condition, Tree(";", [body, current_if]), Tree("skip")])

        return current_if

    # Recursively process subtrees
    new_subtrees = [break_while_to_ifs(subtree) for subtree in tree.subtrees]
    return Tree(tree.root, new_subtrees)


# Weakest precondition calculation
def wp(Q: Invariant, c: Tree, linv: Invariant, start_env: Env) -> Invariant:
    if c.root == "skip":
        return Q

    if c.root == ":=":
        var = c.subtrees[0].subtrees[0].root
        return lambda env: Q(upd(env, var, eval_expr(c.subtrees[1], env, linv)))

    if c.root == "array_init":
        array_name = c.subtrees[0].subtrees[0].root

        def array_init_wp(env):
            elements = [build_external(element, env, linv) for element in c.subtrees[1].subtrees]
            env = upd(env, array_name, elements[0])
            return Q(env)
        return array_init_wp

    if c.root == "array_update":
        array_name = c.subtrees[0].subtrees[0].root
        external_index_expr = c.subtrees[1]

        if len(c.subtrees) == 4:
            inner_index_expr = c.subtrees[2].subtrees[0]
            value_expr = c.subtrees[3]
        else:
            inner_index_expr = Tree('num' ,[Tree(-1 ,[])])
            value_expr = c.subtrees[2]


        def array_update_wp(env):
            inner_index = eval_expr(inner_index_expr, env, linv)
            external_index = eval_expr(external_index_expr, env, linv)
            value = eval_expr(value_expr, env, linv)
            array_obj, length_external, length_internal = env[array_name]

            if length_internal == -1 and inner_index != -1:  # accessing a 1-dimensional array only with index_inner =-1
                raise ValueError("Array access out of bounds")
            elif (((external_index < 0 or external_index >= length_external) or (
                    length_internal > -1 and (inner_index < 0 or inner_index >= length_internal)))
                  and linv(env)):  # Boundary check assertion
                raise ValueError("Array access out of bounds")

            if "hole_" in str(external_index):  # if first index is hole
                z3_var = Int('hole_z3' + str(z3_hole_counter))
                z3_hole_counter += 1
                s.add(z3_var == external_index)
                external_index_value = z3_var

            else:
                external_index_value = IntVal(int(str(eval_expr(external_index_expr, env, linv))))

            if "hole_" in str(inner_index):  # if second index is hole
                z3_var = Int('hole_z3' + str(z3_hole_counter))
                z3_hole_counter += 1
                s.add(z3_var == inner_index)
                internal_index_value = z3_var

            else:
                internal_index_value = IntVal(int(str(eval_expr(inner_index_expr, env, linv))))

            if internal_index_value == -1:
                updated_all_array = Store(array_obj, external_index_value, value)
            else:
                inner_array = Select(array_obj, external_index_value)
                updated_inner_array = Store(inner_array, internal_index_value, value)
                updated_all_array = Store(array_obj,external_index_value, updated_inner_array)

            env = upd(env, array_name, (updated_all_array, length_external, length_internal))
            return Q(env)

        return array_update_wp

    if c.root == ";":
        rightQ = wp(Q, c.subtrees[1], linv, start_env)
        leftQ = wp(rightQ, c.subtrees[0], linv, start_env)
        return lambda env: leftQ(env)

    if c.root == "if":
        true_label = wp(Q, c.subtrees[1], linv, start_env)
        false_label = wp(Q, c.subtrees[2], linv, start_env)
        return lambda env: (
            Or(And(true_label(env), eval_expr(c.subtrees[0], env, linv)),
               And(false_label(env), Not(eval_expr(c.subtrees[0], env, linv)))))

    if c.root == "while":
        if linv is None:
            raise ValueError(f"Linv is None")
        loop_cond = c.subtrees[0]
        loop_body = c.subtrees[1]
        all_vars = collect_vars(loop_cond).union(collect_vars(loop_body))
        the_vars = [Int(var) for var in collect_vars(loop_cond).union(collect_vars(loop_body))]

        def while_wp(env: Env) -> Invariant:
            the_holes = find_holes(loop_cond).union(find_holes(loop_body))
            new_env = mk_env(all_vars.union(the_holes))
            and1 = linv(env)
            wp_c = wp(linv, loop_body, linv, new_env)(new_env)
            and2 = ForAll(the_vars,
                          And(
                              Implies(And(linv(new_env),
                                          eval_expr(loop_cond, new_env, linv)), wp_c),
                              Implies(And(linv(new_env),
                                          Not(eval_expr(loop_cond, new_env, linv))), Q(new_env))))
            and3 = Implies(Not(eval_expr(loop_cond, new_env, linv)), Q(new_env))
            return And(and1, and2)

        return while_wp

    if c.root == "assert":
        return lambda env: And(eval_expr(c.subtrees[0], env, linv), Q(env))

    raise ValueError(f"Unknown command: {c.root}")


def extract_z3_variables(env: Env) -> list:
    z3_vars = []
    for key, value in env.items():
        if isinstance(value, tuple):
            z3_vars.append(value[0])
        else:
            z3_vars.append(value)
    return z3_vars


s = Solver()  # contains assertions


# Verify function, now handling array constraints
def verify(P: Invariant, ast: Tree, Q: Invariant, linv: Invariant) -> bool:
    pvars = collect_vars(ast)
    env = mk_env(pvars)
    result = wp(Q, ast, linv, env)
    s.add(ForAll(list(extract_z3_variables(env)), Implies(P(env), result(env))))
    if s.check() == unsat:
        return False
    else:
        mod = s.model()
        # printing the model_list for debugging purposes
        model_list = {key: mod[key] for key in mod if 'hole_z' not in str(key)}
        print(model_list)
        return True
