"""
Tests:
Each test tests a different case. All tests written in this file should pass.
Before each test, there is a documentation of the case it tests.
"""


from z3 import And, Or, Implies
from final.syntax.while_lang import parse
from final.finalfeatures import main_func


# fill in basic hole
def test_1():
    program_1 = "x := ??"
    Q1 = lambda env: env['x'] == 8
    examples_1 = [{'input': {}, 'output': {'x': 8}}]
    P1 = lambda env: True
    assert main_func(parse(program_1), P1, Q1, [], examples_1)


# fill hole with condition
def test_2():
    program_2 = "x := ??; if (y - x) > 10 then z := 5 else z := 6"
    examples_2 = [
        {'input': {"y": 4}, 'output': {"z": 6}},
        {'input': {"y": 13}, 'output': {"z": 6}},
        {'input': {"y": 14}, 'output': {"z": 5}},
        {'input': {"y": 115}, 'output': {"z": 5}},
    ]
    P2 = lambda d: True
    Q2 = lambda d: And(Implies(d['y'] - d['x'] > 10, d['z'] == 5),
                       Implies(d['y'] - d['x'] <= 10, d['z'] == 6))
    assert main_func(parse(program_2), P2, Q2, [], examples_2)


# fill hole with condition
def test_3():
    P3 = lambda d: True
    Q3 = lambda d: Or(d['i'] == 1, d['i'] == 0)
    program_3 = "if  (x*y) > ?? then i := 1 else i := 0"
    examples_3 = [
        {'input': {"x": 5, 'y': 1}, 'output': {"i": 1}},
        {'input': {"x": 0, 'y': 1}, 'output': {"i": 0}},
        {'input': {"x": -10, 'y': -1}, 'output': {"i": 1}}
    ]

    assert main_func(parse(program_3), P3, Q3, [], examples_3)


# fill hole with operation
def test_4():
    program_4 = "x := ??;  z := x + y"
    examples_4 = [{'input': {'y': 10}, 'output': {'z': 11}},
                  {'input': {'y': 13}, 'output': {'z': 14}}]
    P4 = lambda d: True
    Q4 = lambda d: d['z'] == d['x'] + d['y']
    assert main_func(parse(program_4), P4, Q4, [], examples_4)


# fill hole in while condition + body
def test_5():
    program_5 = " while x < ?? do x := x + ??"
    examples_5 = [{'input': {'x': 10}, 'output': {'x': 15}},
                  {'input': {'x': 13}, 'output': {'x': 15}}]
    P5 = lambda d: And(d['x'] < 15, d['x'] > 6)
    linv5 = lambda d: d['x'] <= 15
    Q5 = lambda d: d['x'] >= 15
    assert main_func(parse(program_5), P5, Q5, linv5, examples_5)


# fill hole in while condition
def test_6():
    program_6 = """
            while a > ?? do
                a := a - 1 
        """

    P6 = lambda env: (env["a"] > 0)
    Q6 = lambda env: (env["a"] > 0)
    linv6 = lambda env: (env["a"] > 0)
    examples_6 = [{'input': {'a': 6}, 'output': {'a': 1}},
                  {'input': {'a': 3}, 'output': {'a': 1}},
                  {'input': {'a': 8}, 'output': {'a': 1}}]
    assert main_func(parse(program_6), P6, Q6, linv6, examples_6)


# fill hole in while condition + body
def test_7():
    program_7 = " while i > ?? do i := i - ??"
    P7 = lambda env: (env['i'] < 20)
    Q7 = lambda env: (env['i'] <= 10)
    linv7 = lambda env: (env['i'] <= 10)
    examples_7 = [{'input': {'i': 18}, 'output': {'i': 10}},
                  {'input': {'i': 12}, 'output': {'i': 10}}]

    assert main_func(parse(program_7), P7, Q7, linv7, examples_7)


# fill hole in condition
def test_8():
    program_8 = """

            if (5 * i) < ?? then i := i + 1 else i := i
        """
    examples_8 = [{'input': {'i': 0}, 'output': {'i': 1}},
                  {'input': {'i': 1}, 'output': {'i': 2}},
                  {'input': {'i': 2}, 'output': {'i': 2}}]
    linv8 = True

    P8 = lambda env: True

    Q8 = lambda env: True

    assert main_func(parse(program_8), P8, Q8, linv8, examples_8)


#fill hole in while condition
def test_9():
    program_9 = "i := 1; while i < ?? do i := i + 3"
    P9 = lambda env: (env['i'] == 1)
    Q9 = lambda env: (env['i'] == 10)
    linv9 = lambda env: And(env['i'] < 10, env['i'] - 3 < 10)
    examples_9 = [{'input': {}, 'output': {'i': 10}}]
    assert main_func(parse(program_9), P9, Q9, linv9, examples_9)


#fill hole with assert
def test_10():
    program_10 = "x := ??; assert x = 3"
    P10 = lambda env: True
    Q10 = lambda env: True
    linv10 = lambda env: True
    examples_10 = []
    assert main_func(parse(program_10), P10, Q10, linv10, examples_10)


#fill hole in while with assert
def test_11():
    program_11 = "i := 1; while i < 10 do (i := i + ??); assert i = 20"
    P11 = lambda env: (env['i'] < 10)
    Q11 = lambda env: (env['i'] == 20)
    linv11 = lambda env: (env['i'] <= 20)
    examples_11 = []
    assert main_func(parse(program_11), P11, Q11, linv11, examples_11)


#advanced fill hole with assert
def test_12():
    program_12 = "x := y * ??; assert x = (y + y)"
    P10 = lambda env: True
    Q10 = lambda env: True
    linv10 = lambda env: True
    examples_10 = []
    assert main_func(parse(program_12), P10, Q10, linv10, examples_10)


#fill hole + assert in while body and assert after while
def test_13():
    program_13 = "i := 1; while i < 20 do (i := i + ??; assert i <= 20); assert i = 20"
    P13 = lambda env: (env['i'] < 10)
    Q13 = lambda env: (env['i'] == 20)
    linv13 = lambda env: (env['i'] <= 20)
    examples_13 = []
    assert main_func(parse(program_13), P13, Q13, linv13, examples_13)


#array initialization(operations) + access
def test_14():
    program_14 = "x := 10; y := 3 ; arr := [ x + y, 5 , x + (x + y)]; a := arr[0]; b := arr[2] "
    P14 = lambda env: True
    Q14 = lambda env: And(env['a'] == 13, env['b'] == 23)
    linv14 = lambda env: True
    examples_14 = []
    assert main_func(parse(program_14), P14, Q14, linv14, examples_14)


#fill holes + array access
def test_15():
    program_15 = "arr := [ 4 , 5 , 1]; x := arr[2] + ??"
    P15 = lambda env: True
    Q15 = lambda env: env['x'] == 2
    linv15 = lambda env: True
    examples_15 = []
    assert main_func(parse(program_15), P15, Q15, linv15, examples_15)


#array access + assert
def test_16():
    program_16 = "arr := [ 4 , 5 , 1]; x := arr[2] + arr[1]; assert x = 6"
    P16 = lambda env: True
    Q16 = lambda env: env['x'] == 6
    linv16 = lambda env: True
    examples_16 = []
    assert main_func(parse(program_16), P16, Q16, linv16, examples_16)


#array access + update
def test_17():
    program_17 = "arr := [ 4 , 5 , 1]; arr[0] := 10; x := arr[0]"
    P17 = lambda env: True
    Q17 = lambda env: env['x'] == 10
    linv17 = lambda env: True
    examples_17 = []
    assert main_func(parse(program_17), P17, Q17, linv17, examples_17)


#array access out of bounds, handling with raising exception
def test_18():
    program_18 = "arr := [ 15, 20 , 999, 4 , 3]; x := arr[5]"
    P18 = lambda env: True
    Q18 = lambda env: env['x'] == 0
    linv18 = lambda env: True
    examples_18 = []
    try:
        assert main_func(parse(program_18), P18, Q18, linv18, examples_18)
    except ValueError as e:
        assert str(e) == 'Array access out of bounds'


#array access out of bounds, handling with raising exception
def test_19():
    program_19 = "arr := [ 15, 20 , 999, 4 , 3]; arr[-2] := 2"
    P19 = lambda env: True
    Q19 = lambda env: env['x'] == 0
    linv19 = lambda env: True
    examples_19 = []
    try:
        assert main_func(parse(program_19), P19, Q19, linv19, examples_19)
    except ValueError as e:
        assert str(e) == 'Array access out of bounds'


#initializing array with hole element + assert
def test_20():
    program_20 = "arr := [ ?? ]; assert arr[0] = 10"
    P20 = lambda env: True
    Q20 = lambda env: True
    linv20 = lambda env: True
    examples_20 = []
    assert main_func(parse(program_20), P20, Q20, linv20, examples_20)


#initializing array with [hole element operation, hole element] + assert + array access
def test_21():
    program_21 = "hello := [ ?? + y , ??]; assert hello[0] = 13; x := hello[1]"
    P21 = lambda env: env['y'] == 10
    Q21 = lambda env: True
    linv21 = lambda env: True
    examples_21 = [{'input': {'y': 10}, 'output': {'x': 4}}]
    assert main_func(parse(program_21), P21, Q21, linv21, examples_21)


#array, update and access array in while + assert array value
def test_22():
    program_22 = "a := [ 1, 4, 5]; x := 0; while x < 3 do (a[x] := a[x] + 1; x := x + 1); y := a[0]; assert y = 2 "
    P22 = lambda env: True
    Q22 = lambda env: env['x'] == 3
    linv22 = lambda env: env['x'] < 3
    examples_22 = []
    assert main_func(parse(program_22), P22, Q22, linv22, examples_22)


#array initializing with holes and assert
def test_23():
    program_23 = "hello := [ ?? * ?? , ??]; assert hello[0] = 20; x := hello[1]"
    P23 = lambda env: True
    Q23 = lambda env: True
    linv23 = lambda env: True
    examples_23 = [{'input': {}, 'output': {'x': 4}}]
    assert main_func(parse(program_23), P23, Q23, linv23, examples_23)


#fill hole in array + assert + accessing array out of bounds, expecting error
def test_24():
    program_24 = "hello1 := [ ??  , 5 , 7]; assert hello1[0] = 20; x := hello1[10]"
    P24 = lambda env: True
    Q24 = lambda env: True
    linv24 = lambda env: True
    examples_24 = []
    try:
        assert main_func(parse(program_24), P24, Q24, linv24, examples_24)
    except ValueError as e:
        assert str(e) == 'Array access out of bounds'


#array access
def test_25():
    program_25 = "a := [ 0 , 5 , 7]; x := a[0]; y := a[x] + 1"
    P25 = lambda env: True
    Q25 = lambda env: env['x'] == 0
    linv25 = lambda env: True
    examples_25 = []
    assert main_func(parse(program_25), P25, Q25, linv25, examples_25)


#array access + hole
def test_26():
    program_26 = "a := [ 9 , 5 , 7]; y := 0; a[y] := y; x := a[y] + ??"
    P26 = lambda env: True
    Q26 = lambda env: env['x'] == 1
    linv26 = lambda env: True
    examples_26 = []
    assert main_func(parse(program_26), P26, Q26, linv26, examples_26)


#array, update and access array in while
def test_27():
    program_27 = "a := [ 1, 4, 5]; x := 0; while x < 3 do (a[x] := a[x] + 1; x := x + 1); y := a[0] "
    P27 = lambda env: True
    Q27 = lambda env: And(env['x'] == 3, env['y'] == 2)
    linv27 = lambda env: env['x'] < 3
    examples_27 = []
    assert main_func(parse(program_27), P27, Q27, linv27, examples_27)


#recursively accessing array + hole
def test_28():
    program_28 = "a := [ 9 , 0 , 2, 4 , 1]; z := ??; x:= 2; b := [ a[a[z + x]] , 1 ]; y := b[0]"
    P28 = lambda env: True
    Q28 = lambda env: env['y'] == 1
    linv28 = lambda env: True
    examples_28 = []
    assert main_func(parse(program_28), P28, Q28, linv28, examples_28)


#recursively accessing array + hole + assert
def test_29():
    program_29 = "a := [ 9 , 0 , 2, 4 , 1]; z := ??; x:= 2; b := [ a[a[z + x]] , 1 ]; assert b[0] = 1"
    P29 = lambda env: True
    Q29 = lambda env: True
    linv29 = lambda env: True
    examples_29 = []
    assert main_func(parse(program_29), P29, Q29, linv29, examples_29)


#holes + accessing array with hole index + assert
def test_30():
    program_30 = "a := [ 9 , 0 , 2, 4 , 1]; z := ??; x:= 2; b := a[ 2 + ?? ]; assert a[z] = 9"
    P30 = lambda env: True
    Q30 = lambda env: And(env['b'] == 4, env['x'] == 2)
    linv30 = lambda env: True
    examples_30 = [{'input': {}, 'output': {'b': 4, 'x': 2}}]
    main_func(parse(program_30), P30, Q30, linv30, examples_30)


#holes + assert + initializing arrays with complex operations
def test_31():
    program_31 = "arr := [ x + ((y + z) + ??) , 3 ]; assert arr[??] = 5"
    P31 = lambda env: And(env['x'] == 1, And(env['z'] == 2, env['y'] == 2))
    Q31 = lambda env: True
    linv31 = lambda env: True
    examples_31 = []
    assert main_func(parse(program_31), P31, Q31, linv31, examples_31)


# initializing 2-dimensional arrays + accessing + updating + holes
def test_32():
    program_32 = " arr := [[1,3,5],[4,8,9]]; arr[1][1] := ??; x := arr[1][1]"
    my_tree = parse(program_32)
    P32 = lambda env: True
    Q32 = lambda env: env['x'] == 2
    linv32 = lambda env: True
    examples_32 = [{'input': {}, 'output': {'x': 2}}]
    assert main_func(parse(program_32), P32, Q32, linv32, examples_32)


# initializing 1 and 2-dimensional arrays + accessing + calculating two accesses
def test_33():
    program_33 = " arr1 := [[1,3,5],[4,8,9]]; arr2 := [2,7,11]; x := arr1[1][1] + arr2[2]"
    P33 = lambda env: True
    Q33 = lambda env: env['x'] == 19
    linv33 = lambda env: True
    examples_33 = []
    print(main_func(parse(program_33), P33, Q33, linv33, examples_33))


# accessing 2D array with one index
def test_34():
    program_34 = "arr := [[2,7],[11,10]]; x := arr[0]"
    P34 = lambda env: True
    Q34 = lambda env: True
    linv34 = lambda env: True
    examples_34 = []
    try:
        assert main_func(parse(program_34), P34, Q34, linv34, examples_34)
    except ValueError as e:
        assert str(e) == "unsupported array access"


# holes and accessing 2D arrays
def test_35():
    program_35 = "arr := [[2,7],[11,??]]; x := arr[1][1] * arr[0][1]"
    P35 = lambda env: True
    Q35 = lambda env: env['x'] == 21
    linv35 = lambda env: True
    examples_35 = [{'input': {}, 'output': {'x': 21}}]
    assert main_func(parse(program_35), P35, Q35, linv35, examples_35)


# using if-else and holes when updating 2D array
def test_36():
    program_36 = "a := [[1,6,7],[3,8,9]]; if x < ?? then a[0][1] := x else a[1][0] := x; y := a[0][1]; z := a[1][0]"
    P36 = lambda env: True
    Q36 = lambda env: Or(env['x'] == env['y'], env['x'] == env['z'])
    linv36 = lambda env: True
    examples_36 = [{'input': {'x': 10}, 'output': {'y': 10, 'z': 3}},
                   {'input': {'x': 11}, 'output': {'y': 6, 'z': 11}}]
    assert main_func(parse(program_36), P36, Q36, linv36, examples_36)


# array initialization is not valid
def test_37():
    program_37 = "a := [[1,6,7],[3]]"
    my_tree = parse(program_37)
    print(my_tree)
    P37 = lambda env: True
    Q37 = lambda env: True
    linv37 = lambda env: True
    examples_37 = []
    try:
        assert main_func(parse(program_37), P37, Q37, linv37, examples_37)
    except ValueError as e:
        assert str(e) == "array initialization is not valid"


# fills hole in assert so assert works
def test_38():
    program_38 = "a := [[1,6,7],[3,4,8]]; a[0][2] := a[1][1]; assert (a[0][2] + ??) = 22"
    P38 = lambda env: True
    Q38 = lambda env: True
    linv38 = lambda env: True
    examples_38 = []
    assert main_func(parse(program_38), P38, Q38, linv38, examples_38)


# the solver fills with {hole_0: 0, hole_1: 5} while we expect to get False (holes cannot be filled).
# this happens because arrays in z3 are infinite, and in our code is initialized to zeroes.
# In test_41 we see that (assert x = 'num') when 'num' is not zero, will not be satisfied.
def test_39():
    program_39 = "a := [[1,6,7],[3,4,8]]; x := a[??][??]; assert x = 0"
    P39 = lambda env: True
    Q39 = lambda env: True
    linv39 = lambda env: True
    examples_39 = []
    assert main_func(parse(program_39), P39, Q39, linv39, examples_39)


# accessing and updating 2D array elements in while statement
def test_40():
    program_40 = "a := [[1, 4],[2, 5]]; x := 0; while x < 2 do (a[x][0] := a[x][0] + 1; x := x + 1); y := a[0][0]"
    P40 = lambda env: True
    Q40 = lambda env: And(env['x'] == 2, env['y'] == 2)
    linv40 = lambda env: env['x'] < 2
    examples_40 = []
    assert main_func(parse(program_40), P40, Q40, linv40, examples_40)


# trying to fill holes in order to satisfy the assert statement fails,
# because the array 'a' has no element with value 17
def test_41():
    program_41 = "a := [[1,6,7],[3,4,8]]; x := a[??][??]; assert x = 17"
    P41 = lambda env: True
    Q41 = lambda env: True
    linv41 = lambda env: True
    examples_41 = []
    assert not main_func(parse(program_41), P41, Q41, linv41, examples_41)

