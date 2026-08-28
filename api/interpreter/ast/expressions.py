from .ast_nodes import Expression
from ..env.types import OxigenType
from .type_checker import TypeChecker
import uuid

def _result_type(val):
    """Infer OxigenType from a raw Python value."""
    if isinstance(val, bool):   return OxigenType.BOOL
    if isinstance(val, int):    return OxigenType.I32
    if isinstance(val, float):  return OxigenType.F64
    if isinstance(val, str):    return OxigenType.STRING
    if isinstance(val, list):   return OxigenType.ARRAY
    if isinstance(val, dict):   return OxigenType.STRUCT
    return OxigenType.NULL

class LiteralNode(Expression):
    def __init__(self, value, val_type, line, column):
        super().__init__(line, column)
        self.value = value
        self.val_type = val_type

    def execute(self, env, error_manager, console):
        return self.value, self.val_type

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        label = str(self.value).replace('"', '\\"')
        dot = f'{node_id} [label="Literal\\n{label}"];\n'
        return node_id, dot, counter

class IdentifierNode(Expression):
    def __init__(self, id_name, line, column):
        super().__init__(line, column)
        self.id_name = id_name

    def execute(self, env, error_manager, console):
        symbol = env.get_variable(self.id_name)
        if symbol is None:
            from ..errors.error import InterpreterError, ErrorType
            error_manager.add_error(InterpreterError(
                ErrorType.SEMANTIC, f"La variable '{self.id_name}' no ha sido declarada.", self.line, self.column))
            return None, OxigenType.NULL
        return symbol.value, symbol.type

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label="Ident\\n{self.id_name}"];\n'
        return node_id, dot, counter

class ArithmeticNode(Expression):
    def __init__(self, left, operator, right, line, column):
        super().__init__(line, column)
        self.left = left; self.operator = operator; self.right = right

    def execute(self, env, error_manager, console):
        val_l, type_l = self.left.execute(env, error_manager, console)
        val_r, type_r = self.right.execute(env, error_manager, console)
        if val_l is None or val_r is None: return None, OxigenType.NULL
        res_type = TypeChecker.check_arithmetic(self.operator, type_l, type_r, self.line, self.column, error_manager)
        if res_type == OxigenType.NULL: return None, OxigenType.NULL
        try:
            op = self.operator
            if op == '+':
                if type_l == OxigenType.STRING or type_r == OxigenType.STRING:
                    return str(val_l) + str(val_r), OxigenType.STRING
                return val_l + val_r, res_type
            elif op == '-': return val_l - val_r, res_type
            elif op == '*':
                if type_l == OxigenType.STRING and type_r == OxigenType.I32:
                    return str(val_l) * int(val_r), OxigenType.STRING
                if type_l == OxigenType.I32 and type_r == OxigenType.STRING:
                    return str(val_r) * int(val_l), OxigenType.STRING
                return val_l * val_r, res_type
            elif op == '/':
                if val_r == 0:
                    from ..errors.error import InterpreterError, ErrorType
                    error_manager.add_error(InterpreterError(ErrorType.SEMANTIC, "División por cero.", self.line, self.column))
                    return None, OxigenType.NULL
                result = val_l / val_r
                if res_type == OxigenType.I32: result = int(result)
                return result, res_type
            elif op == '%': return val_l % val_r, res_type
        except Exception as e:
            from ..errors.error import InterpreterError, ErrorType
            error_manager.add_error(InterpreterError(ErrorType.SEMANTIC, str(e), self.line, self.column))
        return None, OxigenType.NULL

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label="{self.operator}"];\n'
        id_l, dot_l, counter = self.left.get_dot(counter)
        id_r, dot_r, counter = self.right.get_dot(counter)
        dot += dot_l + dot_r + f'{node_id} -> {id_l};\n{node_id} -> {id_r};\n'
        return node_id, dot, counter

class LogicalNode(Expression):
    def __init__(self, operand, operator, right, line, column):
        super().__init__(line, column)
        self.operand = operand; self.operator = operator; self.right = right

    def execute(self, env, error_manager, console):
        if self.operator == '!':
            val, typ = self.operand.execute(env, error_manager, console)
            if val is None: return None, OxigenType.NULL
            return not bool(val), OxigenType.BOOL
        val_l, type_l = self.operand.execute(env, error_manager, console)
        if self.operator == '&&':
            if not val_l: return False, OxigenType.BOOL
            val_r, _ = self.right.execute(env, error_manager, console)
            return bool(val_l) and bool(val_r), OxigenType.BOOL
        elif self.operator == '||':
            if val_l: return True, OxigenType.BOOL
            val_r, _ = self.right.execute(env, error_manager, console)
            return bool(val_l) or bool(val_r), OxigenType.BOOL
        return None, OxigenType.NULL

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label="{self.operator}"];\n'
        id_l, dot_l, counter = self.operand.get_dot(counter)
        dot += dot_l + f'{node_id} -> {id_l};\n'
        if self.right:
            id_r, dot_r, counter = self.right.get_dot(counter)
            dot += dot_r + f'{node_id} -> {id_r};\n'
        return node_id, dot, counter

class RelationalNode(Expression):
    def __init__(self, left, operator, right, line, column):
        super().__init__(line, column)
        self.left = left; self.operator = operator; self.right = right

    def execute(self, env, error_manager, console):
        val_l, type_l = self.left.execute(env, error_manager, console)
        val_r, type_r = self.right.execute(env, error_manager, console)
        if val_l is None or val_r is None: return None, OxigenType.NULL
        # Allow mixed numeric comparisons
        op = self.operator
        if op == '==': return val_l == val_r, OxigenType.BOOL
        if op == '!=': return val_l != val_r, OxigenType.BOOL
        if op == '>':  return val_l > val_r,  OxigenType.BOOL
        if op == '<':  return val_l < val_r,  OxigenType.BOOL
        if op == '>=': return val_l >= val_r, OxigenType.BOOL
        if op == '<=': return val_l <= val_r, OxigenType.BOOL
        return None, OxigenType.NULL

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label="{self.operator}"];\n'
        id_l, dot_l, counter = self.left.get_dot(counter)
        id_r, dot_r, counter = self.right.get_dot(counter)
        dot += dot_l + dot_r + f'{node_id} -> {id_l};\n{node_id} -> {id_r};\n'
        return node_id, dot, counter

class ArrayInitNode(Expression):
    def __init__(self, expr_list, line, column):
        super().__init__(line, column)
        self.expr_list = expr_list

    def execute(self, env, error_manager, console):
        values = [expr.execute(env, error_manager, console)[0] for expr in self.expr_list]
        return values, OxigenType.ARRAY

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label="Array"];\n'
        for expr in self.expr_list:
            id_c, dot_c, counter = expr.get_dot(counter)
            dot += dot_c + f'{node_id} -> {id_c};\n'
        return node_id, dot, counter

class ArrayAccessNode(Expression):
    def __init__(self, array_expr, index_expr, line, column):
        super().__init__(line, column)
        self.array_expr = array_expr; self.index_expr = index_expr

    def execute(self, env, error_manager, console):
        arr, typ = self.array_expr.execute(env, error_manager, console)
        idx, idx_type = self.index_expr.execute(env, error_manager, console)
        if arr is None or idx is None: return None, OxigenType.NULL
        if not isinstance(arr, list):
            from ..errors.error import InterpreterError, ErrorType
            error_manager.add_error(InterpreterError(ErrorType.SEMANTIC, "No es un arreglo.", self.line, self.column))
            return None, OxigenType.NULL
        idx = int(idx)
        if idx < 0 or idx >= len(arr):
            from ..errors.error import InterpreterError, ErrorType
            error_manager.add_error(InterpreterError(ErrorType.SEMANTIC, f"Índice {idx} fuera de límites (len={len(arr)}).", self.line, self.column))
            return None, OxigenType.NULL
        val = arr[idx]
        return val, _result_type(val)

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label="Index[]"];\n'
        id_a, dot_a, counter = self.array_expr.get_dot(counter)
        id_i, dot_i, counter = self.index_expr.get_dot(counter)
        dot += dot_a + dot_i + f'{node_id} -> {id_a};\n{node_id} -> {id_i};\n'
        return node_id, dot, counter

class SliceNode(Expression):
    def __init__(self, array_expr, from_expr, to_expr, line, column):
        super().__init__(line, column)
        self.array_expr = array_expr; self.from_expr = from_expr; self.to_expr = to_expr

    def execute(self, env, error_manager, console):
        arr, _ = self.array_expr.execute(env, error_manager, console)
        frm, _ = self.from_expr.execute(env, error_manager, console)
        to_, _ = self.to_expr.execute(env, error_manager, console)
        if arr is None: return None, OxigenType.NULL
        return arr[int(frm):int(to_)], OxigenType.ARRAY

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label="Slice"];\n'
        return node_id, dot, counter

class FieldAccessNode(Expression):
    def __init__(self, target_expr, field_name, line, column):
        super().__init__(line, column)
        self.target_expr = target_expr; self.field_name = field_name

    def execute(self, env, error_manager, console):
        val, typ = self.target_expr.execute(env, error_manager, console)
        if isinstance(val, dict):
            if self.field_name in val:
                fv = val[self.field_name]
                return fv, _result_type(fv)
            from ..errors.error import InterpreterError, ErrorType
            error_manager.add_error(InterpreterError(ErrorType.SEMANTIC, f"Campo '{self.field_name}' no existe.", self.line, self.column))
        return None, OxigenType.NULL

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label=".{self.field_name}"];\n'
        id_t, dot_t, counter = self.target_expr.get_dot(counter)
        dot += dot_t + f'{node_id} -> {id_t};\n'
        return node_id, dot, counter

class StructInitNode(Expression):
    def __init__(self, name, fields, line, column):
        super().__init__(line, column)
        self.name = name; self.fields = fields  # list of (field_name, expr)

    def execute(self, env, error_manager, console):
        result = {}
        for fname, fexpr in self.fields:
            fval, ftyp = fexpr.execute(env, error_manager, console)
            result[fname] = fval
        return result, OxigenType.STRUCT

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label="Struct\\n{self.name}"];\n'
        for _, fexpr in self.fields:
            id_f, dot_f, counter = fexpr.get_dot(counter)
            dot += dot_f + f'{node_id} -> {id_f};\n'
        return node_id, dot, counter

class FunctionCallNode(Expression):
    def __init__(self, name, arg_list, line, column):
        super().__init__(line, column)
        self.name = name; self.arg_list = arg_list

    def execute(self, env, error_manager, console):
        import random as rnd
        # Built-in: random
        if self.name == 'random' and len(self.arg_list) == 2:
            a, _ = self.arg_list[0].execute(env, error_manager, console)
            b, _ = self.arg_list[1].execute(env, error_manager, console)
            return rnd.randint(int(a), int(b)), OxigenType.I32
        # typeof
        if self.name == 'typeof' and len(self.arg_list) == 1:
            _, t = self.arg_list[0].execute(env, error_manager, console)
            return str(t), OxigenType.STRING
        # User-defined function
        func_entry = env.get_function(self.name)
        if not func_entry:
            from ..errors.error import InterpreterError, ErrorType
            error_manager.add_error(InterpreterError(ErrorType.SEMANTIC, f"La función '{self.name}' no ha sido declarada.", self.line, self.column))
            return None, OxigenType.NULL
        func_node = func_entry["node"]
        from ..env.environment import Environment
        local_env = Environment(env.get_global(), f"fn_{self.name}")
        for i, (pname, ptype, pmut) in enumerate(func_node.params):
            pval, ptyp = (self.arg_list[i].execute(env, error_manager, console) if i < len(self.arg_list) else (None, OxigenType.NULL))
            local_env.save_variable(pname, ptype, pval, pmut, self.line, self.column)
        result = func_node.block.execute(local_env, error_manager, console)
        if result and result[0] == "return":
            return result[1], result[2]
        return None, OxigenType.NULL

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label="Call\\n{self.name}"];\n'
        for arg in self.arg_list:
            id_a, dot_a, counter = arg.get_dot(counter)
            dot += dot_a + f'{node_id} -> {id_a};\n'
        return node_id, dot, counter

class MethodCallNode(Expression):
    def __init__(self, target_expr, method_name, args, line, column):
        super().__init__(line, column)
        self.target_expr = target_expr; self.method_name = method_name; self.args = args

    def execute(self, env, error_manager, console):
        val, typ = self.target_expr.execute(env, error_manager, console)
        m = self.method_name
        if val is None: return None, OxigenType.NULL

        if m == 'len':
            return len(val), OxigenType.I32
        elif m == 'contains' and self.args:
            sub, _ = self.args[0].execute(env, error_manager, console)
            return sub in str(val), OxigenType.BOOL
        elif m == 'replace' and len(self.args) >= 2:
            s1, _ = self.args[0].execute(env, error_manager, console)
            s2, _ = self.args[1].execute(env, error_manager, console)
            return str(val).replace(str(s1), str(s2)), OxigenType.STRING
        elif m == 'to_uppercase':
            return str(val).upper(), OxigenType.STRING
        elif m == 'to_lowercase':
            return str(val).lower(), OxigenType.STRING
        elif m == 'split' and self.args:
            sep, _ = self.args[0].execute(env, error_manager, console)
            return str(val).split(str(sep)), OxigenType.ARRAY
        elif m == 'reverse':
            if isinstance(val, list):
                val.reverse()
                # Update the original variable if target is IdentifierNode
                if isinstance(self.target_expr, IdentifierNode):
                    env.update_variable(self.target_expr.id_name, val)
                return val, OxigenType.ARRAY
        return None, OxigenType.NULL

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label=".{self.method_name}()"];\n'
        id_t, dot_t, counter = self.target_expr.get_dot(counter)
        dot += dot_t + f'{node_id} -> {id_t};\n'
        return node_id, dot, counter

class TypeofNode(Expression):
    def __init__(self, expr, line, column):
        super().__init__(line, column)
        self.expr = expr

    def execute(self, env, error_manager, console):
        _, t = self.expr.execute(env, error_manager, console)
        return str(t), OxigenType.STRING

    def get_dot(self, counter):
        node_id = f"n{counter}"; counter += 1
        dot = f'{node_id} [label="typeof"];\n'
        id_e, dot_e, counter = self.expr.get_dot(counter)
        dot += dot_e + f'{node_id} -> {id_e};\n'
        return node_id, dot, counter
