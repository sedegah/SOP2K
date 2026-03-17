import pytest
import numpy as np
from utils import parse_sop, build_kmap, gray_code, get_variables

def test_get_variables():
    assert get_variables("xy + x'y'z") == ['x', 'y', 'z']
    assert get_variables("AB + A'B'CD") == ['A', 'B', 'C', 'D']

def test_gray_code():
    assert gray_code(2) == [0, 1, 3, 2]
    assert gray_code(3) == [0, 1, 3, 2, 6, 7, 5, 4]

def test_parse_sop_3var():
    # xy + x'y'z
    # variables: x, y, z
    # xy: 110 (6), 111 (7)
    # x'y'z: 001 (1)
    # Expected minterms: [1, 6, 7]
    vars, minterms = parse_sop("xy + x'y'z")
    assert vars == ['x', 'y', 'z']
    assert minterms == [1, 6, 7]

def test_parse_sop_4var():
    # AB + A'B'CD
    # AB = 11xx (1100=12, 1101=13, 1110=14, 1111=15)
    # A'B'CD = 0011 (3)
    # Expected: [3, 12, 13, 14, 15]
    vars, minterms = parse_sop("AB + A'B'CD")
    assert vars == ['A', 'B', 'C', 'D']
    assert minterms == [3, 12, 13, 14, 15]

def test_build_kmap_3var():
    # xy + x'y'z -> minterms [1, 6, 7]
    # Rows: x (0, 1) -> Gray: 0, 1
    # Cols: yz (00, 01, 10, 11) -> Gray: 0, 1, 3, 2
    # Minterm calculation: (row << 2) | col
    # x=0: 000(0), 001(1), 011(3), 010(2)
    # x=1: 100(4), 101(5), 111(7), 110(6)
    # Minterms [1, 6, 7] correspond to:
    # Row 0 (x=0), Col 1 (yz=01) -> 1
    # Row 1 (x=1), Col 2 (yz=11) -> 7
    # Row 1 (x=1), Col 3 (yz=10) -> 6
    
    minterms = [1, 6, 7]
    kmap, _, _, _, _ = build_kmap(minterms, 3)
    
    expected = np.array([
        [0, 1, 0, 0],  # row 0 (x=0): minterms 0, 1, 3, 2
        [0, 0, 1, 1]   # row 1 (x=1): minterms 4, 5, 7, 6
    ])
    np.testing.assert_array_equal(kmap, expected)

def test_minimize_sop():
    from utils import minimize_sop
    # x'y'z + x'z + y'z -> z(x'y' + x' + y') -> z(x' + y') -> x'z + y'z
    # syms: x, y, z
    # minterms: {1, 3, 5}
    # Expected result: x'z + y'z (or equivalent)
    res = minimize_sop(['x', 'y', 'z'], [1, 3, 5])
    # Sympy might return "x'z + y'z" or "y'z + x'z"
    assert "x'z" in res
    assert "y'z" in res
    assert " + " in res

def test_parse_sop_partial():
    # Variables: x, y, z
    # Term: y'
    # Should cover: 000 (0), 001 (1), 100 (4), 101 (5)
    vars, minterms = parse_sop("y'", variables=['x', 'y', 'z'])
    assert minterms == [0, 1, 4, 5]

def test_parse_sop_2_vars():
    # A + B'
    # Vars: A, B
    # A -> 10, 11
    # B' -> 00, 10
    # Total -> 00, 10, 11 (0, 2, 3)
    vars, minterms = parse_sop("A + B'")
    assert vars == ['A', 'B']
    assert minterms == [0, 2, 3]

def test_invalid_var_count():
    with pytest.raises(ValueError, match="Supports 1-6 variables"):
        parse_sop("A+B+C+D+E+F+G")
