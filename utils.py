import re
import numpy as np
import sympy
from itertools import product as iproduct

def get_variables(expr: str) -> list[str]:
    seen = []
    for ch in expr:
        if ch.isalpha() and ch not in seen:
            seen.append(ch)
    return sorted(seen)

def minimize_sop(variables: list[str], minterms: list[int]) -> str:
    from sympy.logic.boolalg import SOPform
    from sympy import symbols
    try:
        syms = symbols(" ".join(variables))
        # Handle single variable case (symbols returns a tuple for >1, else single symbol)
        if len(variables) == 1:
            syms = [syms]
        
        expr = SOPform(syms, minterms)
        return _format_sympy_expr(expr, variables)
    except Exception as e:
        return f"Error: {e}"

def _format_sympy_expr(expr, variables) -> str:
    from sympy.logic.boolalg import And, Or, Not, BooleanTrue, BooleanFalse
    if isinstance(expr, BooleanTrue): return "1"
    if isinstance(expr, BooleanFalse): return "0"
    if isinstance(expr, Or):
        return " + ".join(_format_sympy_expr(arg, variables) for arg in expr.args)
    if isinstance(expr, And):
        def sort_key(arg):
            symbol = arg.args[0] if isinstance(arg, Not) else arg
            try: return variables.index(str(symbol))
            except: return 0
        sorted_args = sorted(expr.args, key=sort_key)
        return "".join(_format_sympy_expr(arg, variables) for arg in sorted_args)
    if isinstance(expr, Not):
        return f"{_format_sympy_expr(expr.args[0], variables)}'"
    return str(expr)

def _parse_term(term: str, variables: list[str]) -> list[int]:
    assignment = {v: None for v in variables}
    pattern = re.compile(r"([A-Za-z])('?)")
    for match in pattern.finditer(term.strip()):
        var, complement = match.group(1), match.group(2)
        if var in assignment:
            assignment[var] = 0 if complement == "'" else 1

    free_vars = [v for v in variables if assignment[v] is None]
    fixed_vals = [assignment[v] for v in variables if assignment[v] is not None]
    fixed_vars = [v for v in variables if assignment[v] is not None]

    minterms = []
    for combo in iproduct([0, 1], repeat=len(free_vars)):
        full = dict(zip(free_vars, combo))
        full.update(dict(zip(fixed_vars, fixed_vals)))
        bits = [full[v] for v in variables]
        minterm = int("".join(map(str, bits)), 2)
        minterms.append(minterm)
    return minterms

def parse_sop(expr: str, variables: list[str] | None = None) -> tuple[list[str], list[int]]:
    # Normalize input and smart quotes from Word/Browser
    expr = expr.replace("’", "'").replace("‘", "'").replace("“", "").replace("”", "").strip()
    
    if variables is None:
        variables = get_variables(expr)
    n = len(variables)
    if not (1 <= n <= 6):
        raise ValueError(f"Supports 1-6 variables. Detected {n}.")

    terms = [t.strip() for t in expr.split("+") if t.strip()]
    minterms = set()
    for term in terms:
        minterms.update(_parse_term(term, variables))
    return variables, sorted(minterms)

def gray_code(n: int) -> list[int]:
    return [i ^ (i >> 1) for i in range(2**n)]

def gray_code_labels(n: int) -> list[str]:
    return [format(g, f"0{n}b") for g in gray_code(n)]

_AXIS_SPLIT = {
    1: (1, 0),
    2: (1, 1),
    3: (1, 2),
    4: (2, 2),
    5: (2, 3),
    6: (3, 3),
}

def build_kmap(minterms: list[int], n_vars: int) -> tuple[np.ndarray, list[str], list[str], int, int]:
    n_row_bits, n_col_bits = _AXIS_SPLIT[n_vars]
    row_seq, col_seq = gray_code(n_row_bits), gray_code(n_col_bits)
    kmap = np.zeros((len(row_seq), len(col_seq)), dtype=int)

    for r, row_val in enumerate(row_seq):
        for c, col_val in enumerate(col_seq):
            minterm_idx = (row_val << n_col_bits) | col_val
            if minterm_idx in minterms:
                kmap[r, c] = 1
    return kmap, gray_code_labels(n_row_bits), gray_code_labels(n_col_bits), n_row_bits, n_col_bits

def ascii_kmap(kmap: np.ndarray, row_labels: list[str], col_labels: list[str], row_vars: str, col_vars: str) -> str:
    n_rows, n_cols = kmap.shape
    cell_w, row_lbl_w = 4, 8
    corner = f"{row_vars}\\{col_vars}"
    
    col_lbl_row = f"{corner:>{row_lbl_w}} |"
    for lbl in col_labels:
        col_lbl_row += f" {lbl:^{cell_w}} |"
    
    sep = "-" * len(col_lbl_row)
    lines = [sep, col_lbl_row, sep]
    for r in range(n_rows):
        row_str = f"{row_labels[r]:>{row_lbl_w}} |"
        for c in range(n_cols):
            row_str += f" {'1' if kmap[r, c] else '0':^{cell_w}} |"
        lines.extend([row_str, sep])
    return "\n".join(lines)
