from .ast_nodes import Instruction
from ..env.types import OxigenType

def _result_type(val):
    if isinstance(val, bool):   return OxigenType.BOOL
    if isinstance(val, int):    return OxigenType.I32
    if isinstance(val, float):  return OxigenType.F64
    if isinstance(val, str):    return OxigenType.STRING
    if isinstance(val, list):   return OxigenType.ARRAY
    if isinstance(val, dict):   return OxigenType.STRUCT
    return OxigenType.NULL

# ─────────────────────────────────────────────
class PrintlnNode(Instruction):
    def __init__(self, expressions, line, column):
        super().__init__(line, column)
        self.expressions = expressions

    def execute(self, env, error_manager, console):
        if not self.expressions:
            console.append("")
            return
        fmt_node = self.expressions[0]
        fmt_str, _ = fmt_node.execute(env, error_manager, console)
        fmt_str = str(fmt_str) if fmt_str is not None else ""

        vals = []
        for exp in self.expressions[1:]:
            v, t = exp.execute(env, error_manager, console)
            if isinstance(v, list):
                inner = []
                for item in v:
                    if isinstance(item, str): inner.append(f'"{item}"')
                    else: inner.append(str(item))
                vals.append("[" + ", ".join(inner) + "]")
            elif isinstance(v, bool): vals.append("true" if v else "false")
            elif v is None: vals.append("None")
            elif isinstance(v, str): vals.append(v)  # keep strings as-is (empty string shows as empty)
            else: vals.append(str(v))

        # Single-pass: replace {} or {:?} placeholders in order
        result = fmt_str
        for val_str in vals:
            if '{:?}' in result:
                result = result.replace('{:?}', val_str, 1)
            elif '{}' in result:
                result = result.replace('{}', val_str, 1)
            # else: no placeholder left, ignore extra args

        console.append(result)

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label="println!"];\n'
        for expr in self.expressions:
            id_e, dot_e, counter = expr.get_dot(counter)
            dot += dot_e + f'{node_id} -> {id_e};\n'
        return node_id, dot, counter

class ExpressionStmtNode(Instruction):
    def __init__(self, expression, line, column):
        super().__init__(line, column)
        self.expression = expression

    def execute(self, env, error_manager, console):
        self.expression.execute(env, error_manager, console)
        return None  # Expressions as statements don't return values to control flow

    def get_dot(self, counter):
        return self.expression.get_dot(counter)

# ─────────────────────────────────────────────
class DeclarationNode(Instruction):
    def __init__(self, is_mut, id_name, decl_type, expression, line, column):
        super().__init__(line, column)
        self.is_mut = is_mut; self.id_name = id_name
        self.decl_type = decl_type; self.expression = expression

    def _default_value(self, t):
        if t == OxigenType.I32:     return 0
        if t == OxigenType.F64:     return 0.0
        if t == OxigenType.BOOL:    return False
        if t == OxigenType.CHAR:    return '\0'
        if t == OxigenType.STRING:  return ""
        if t == OxigenType.ARRAY:   return []
        return None

    def execute(self, env, error_manager, console):
        if self.expression:
            val, t = self.expression.execute(env, error_manager, console)
        else:
            t = OxigenType.NULL
            val = None

        final_type = self.decl_type if self.decl_type else t

        # Apply default value if no expression and type known
        if val is None and final_type != OxigenType.NULL:
            val = self._default_value(final_type)

        # Semantic type check
        if (self.decl_type and t != OxigenType.NULL and self.decl_type != t
                and not _is_compatible(self.decl_type, t)):
            from ..errors.error import InterpreterError, ErrorType
            error_manager.add_error(InterpreterError(
                ErrorType.SEMANTIC,
                f"Tipos incompatibles: se declaró '{self.decl_type}' pero se asignó '{t}'.",
                self.line, self.column))
            return

        env.save_variable(self.id_name, final_type, val, self.is_mut, self.line, self.column)

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        mut_s = "mut " if self.is_mut else ""
        dot = f'{node_id} [label="let {mut_s}{self.id_name}"];\n'
        if self.expression:
            id_e, dot_e, counter = self.expression.get_dot(counter)
            dot += dot_e + f'{node_id} -> {id_e};\n'
        return node_id, dot, counter

def _is_compatible(declared, inferred):
    """i32 <-> f64 promotion is OK."""
    numeric = {OxigenType.I32, OxigenType.F64}
    if declared in numeric and inferred in numeric:
        return True
    return False

# ─────────────────────────────────────────────
class AssignmentNode(Instruction):
    def __init__(self, id_name, expression, operator, line, column):
        super().__init__(line, column)
        self.id_name = id_name; self.expression = expression; self.operator = operator

    def execute(self, env, error_manager, console):
        # Support nested field access: "a.b"
        parts = self.id_name.split(".")
        root = parts[0]
        symbol = env.get_variable(root)
        if not symbol:
            from ..errors.error import InterpreterError, ErrorType
            error_manager.add_error(InterpreterError(
                ErrorType.SEMANTIC, f"La variable '{root}' no ha sido declarada.", self.line, self.column))
            return
        if not symbol.is_mut:
            from ..errors.error import InterpreterError, ErrorType
            error_manager.add_error(InterpreterError(
                ErrorType.SEMANTIC, "No es posible modificar una variable inmutable.", self.line, self.column))
            return

        val, t = self.expression.execute(env, error_manager, console)
        op = self.operator

        if len(parts) == 1:
            # Simple variable assignment
            cur = symbol.value
            if op != '=':
                real_op = op[0]
                cur = cur if cur is not None else 0
                if real_op == '+': val = cur + val
                elif real_op == '-': val = cur - val
                elif real_op == '*': val = cur * val
                elif real_op == '/':
                    result = cur / val
                    val = int(result) if symbol.type == OxigenType.I32 else result
                elif real_op == '%': val = cur % val
            env.update_variable(root, val)
        else:
            # Struct field assignment
            struct_dict = symbol.value
            if isinstance(struct_dict, dict):
                struct_dict[parts[1]] = val
                env.update_variable(root, struct_dict)

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label="{self.id_name} {self.operator}"];\n'
        id_e, dot_e, counter = self.expression.get_dot(counter)
        dot += dot_e + f'{node_id} -> {id_e};\n'
        return node_id, dot, counter

# ─────────────────────────────────────────────
class ArrayAssignmentNode(Instruction):
    def __init__(self, arr_name, index_expr, expr, operator, line, column):
        super().__init__(line, column)
        self.arr_name = arr_name; self.index_expr = index_expr
        self.expr = expr; self.operator = operator

    def execute(self, env, error_manager, console):
        symbol = env.get_variable(self.arr_name)
        if not symbol:
            from ..errors.error import InterpreterError, ErrorType
            error_manager.add_error(InterpreterError(ErrorType.SEMANTIC, f"Variable '{self.arr_name}' no declarada.", self.line, self.column))
            return
        if not symbol.is_mut:
            from ..errors.error import InterpreterError, ErrorType
            error_manager.add_error(InterpreterError(ErrorType.SEMANTIC, "Variable inmutable.", self.line, self.column))
            return
        idx, _ = self.index_expr.execute(env, error_manager, console)
        val, _ = self.expr.execute(env, error_manager, console)
        arr = symbol.value
        if isinstance(arr, list) and 0 <= int(idx) < len(arr):
            arr[int(idx)] = val
            env.update_variable(self.arr_name, arr)

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label="{self.arr_name}[i]="];\n'
        return node_id, dot, counter

# ─────────────────────────────────────────────
class BlockNode(Instruction):
    def __init__(self, instructions, line, column):
        super().__init__(line, column)
        self.instructions = instructions if instructions else []

    def execute(self, env, error_manager, console):
        from ..env.environment import Environment
        local_env = Environment(env, f"{env.name}_blk")
        for inst in self.instructions:
            if inst is None: continue
            result = inst.execute(local_env, error_manager, console)
            if result is not None:
                return result

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label="Bloque"];\n'
        for inst in self.instructions:
            if inst is None: continue
            id_i, dot_i, counter = inst.get_dot(counter)
            dot += dot_i + f'{node_id} -> {id_i};\n'
        return node_id, dot, counter

# ─────────────────────────────────────────────
class IfNode(Instruction):
    def __init__(self, condition, if_block, else_block, line, column):
        super().__init__(line, column)
        self.condition = condition; self.if_block = if_block; self.else_block = else_block

    def execute(self, env, error_manager, console):
        cond_val, cond_type = self.condition.execute(env, error_manager, console)
        if cond_val is None: return
        if bool(cond_val):
            return self.if_block.execute(env, error_manager, console)
        elif self.else_block:
            return self.else_block.execute(env, error_manager, console)

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label="If"];\n'
        id_c, dot_c, counter = self.condition.get_dot(counter)
        id_i, dot_i, counter = self.if_block.get_dot(counter)
        dot += dot_c + dot_i + f'{node_id} -> {id_c};\n{node_id} -> {id_i};\n'
        if self.else_block:
            id_e, dot_e, counter = self.else_block.get_dot(counter)
            dot += dot_e + f'{node_id} -> {id_e};\n'
        return node_id, dot, counter

# ─────────────────────────────────────────────
class WhileNode(Instruction):
    def __init__(self, condition, block, line, column):
        super().__init__(line, column)
        self.condition = condition; self.block = block

    def execute(self, env, error_manager, console):
        while True:
            cond_val, _ = self.condition.execute(env, error_manager, console)
            if cond_val is None or not bool(cond_val): break
            res = self.block.execute(env, error_manager, console)
            if res:
                if res[0] == "break": break
                if res[0] == "continue": continue
                if res[0] == "return": return res

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label="While"];\n'
        id_c, dot_c, counter = self.condition.get_dot(counter)
        id_b, dot_b, counter = self.block.get_dot(counter)
        dot += dot_c + dot_b + f'{node_id} -> {id_c};\n{node_id} -> {id_b};\n'
        return node_id, dot, counter

# ─────────────────────────────────────────────
class LoopNode(Instruction):
    def __init__(self, block, label, line, column):
        super().__init__(line, column)
        self.block = block; self.label = label

    def execute(self, env, error_manager, console):
        while True:
            res = self.block.execute(env, error_manager, console)
            if res:
                kind, val, typ, lbl = res[0], res[1], res[2], res[3] if len(res) > 3 else None
                if kind == "break":
                    if lbl is None or lbl == self.label: break
                    return res
                if kind == "continue":
                    if lbl is None or lbl == self.label: continue
                    return res
                if kind == "return": return res

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        lbl = f" '{self.label}" if self.label else ""
        dot = f'{node_id} [label="Loop{lbl}"];\n'
        id_b, dot_b, counter = self.block.get_dot(counter)
        dot += dot_b + f'{node_id} -> {id_b};\n'
        return node_id, dot, counter

# ─────────────────────────────────────────────
class MatchNode(Instruction):
    def __init__(self, expression, cases, line, column):
        super().__init__(line, column)
        self.expression = expression; self.cases = cases

    def execute(self, env, error_manager, console):
        val, typ = self.expression.execute(env, error_manager, console)
        for case_expr, case_block in self.cases:
            if case_expr == '_':
                return case_block.execute(env, error_manager, console)
            case_val, _ = case_expr.execute(env, error_manager, console)
            if val == case_val:
                return case_block.execute(env, error_manager, console)

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label="Match"];\n'
        id_e, dot_e, counter = self.expression.get_dot(counter)
        dot += dot_e + f'{node_id} -> {id_e};\n'
        return node_id, dot, counter

# ─────────────────────────────────────────────
class FunctionNode(Instruction):
    def __init__(self, name, params, return_type, block, line, column):
        super().__init__(line, column)
        self.name = name; self.params = params
        self.return_type = return_type; self.block = block

    def execute(self, env, error_manager, console):
        env.save_function(self.name, self, self.line, self.column)

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label="fn {self.name}"];\n'
        id_b, dot_b, counter = self.block.get_dot(counter)
        dot += dot_b + f'{node_id} -> {id_b};\n'
        return node_id, dot, counter

# ─────────────────────────────────────────────
class TransferNode(Instruction):
    def __init__(self, transfer_type, value, label, line, column):
        super().__init__(line, column)
        self.transfer_type = transfer_type; self.value = value; self.label = label

    def execute(self, env, error_manager, console):
        if self.value:
            val, typ = self.value.execute(env, error_manager, console)
            return (self.transfer_type, val, typ, self.label)
        return (self.transfer_type, None, OxigenType.NULL, self.label)

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        lbl = self.label if self.label else ""
        dot = f'{node_id} [label="{self.transfer_type} {lbl}"];\n'
        if self.value:
            id_v, dot_v, counter = self.value.get_dot(counter)
            dot += dot_v + f'{node_id} -> {id_v};\n'
        return node_id, dot, counter

# ─────────────────────────────────────────────
class StructDeclNode(Instruction):
    def __init__(self, name, fields, line, column):
        super().__init__(line, column)
        self.name = name; self.fields = fields  # [(fname, ftype)]

    def execute(self, env, error_manager, console):
        env.save_struct(self.name, self, self.line, self.column)

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label="struct {self.name}"];\n'
        return node_id, dot, counter
