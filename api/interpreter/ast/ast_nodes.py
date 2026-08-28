from abc import ABC, abstractmethod
from ..env.types import OxigenType

class ASTNode(ABC):
    def __init__(self, line, column):
        self.line = line
        self.column = column

    @abstractmethod
    def execute(self, env, error_manager, console):
        pass

    def get_dot(self, counter):
        pass

class Expression(ASTNode):
    pass

class Instruction(ASTNode):
    pass

# ================= EXPRESSIONS =================

class LiteralNode(Expression):
    def __init__(self, value, val_type, line, column):
        super().__init__(line, column)
        self.value = value
        self.val_type = val_type

    def execute(self, env, error_manager, console):
        return self.value, self.val_type

class IdentifierNode(Expression):
    def __init__(self, id_name, line, column):
        super().__init__(line, column)
        self.id_name = id_name

    def execute(self, env, error_manager, console):
        symbol = env.get_variable(self.id_name)
        if symbol is None:
            # Report error
            from ..errors.error import InterpreterError, ErrorType
            error_manager.add_error(InterpreterError(
                ErrorType.SEMANTIC, f"La variable '{self.id_name}' no ha sido declarada.", self.line, self.column
            ))
            return None, OxigenType.NULL
        return symbol.value, symbol.type

class ArithmeticNode(Expression):
    def __init__(self, left, operator, right, line, column):
        super().__init__(line, column)
        self.left = left
        self.operator = operator
        self.right = right

    def execute(self, env, error_manager, console):
        val_l, type_l = self.left.execute(env, error_manager, console)
        val_r, type_r = self.right.execute(env, error_manager, console)
        
        if val_l is None or val_r is None: return None, OxigenType.NULL
        
        try:
            if self.operator == '+':
                if type_l == OxigenType.STRING and type_r == OxigenType.STRING:
                    return str(val_l) + str(val_r), OxigenType.STRING
                return val_l + val_r, type_l # Simplified
            elif self.operator == '-': return val_l - val_r, type_l
            elif self.operator == '*': return val_l * val_r, type_l
            elif self.operator == '/': return val_l / val_r, type_l
            elif self.operator == '%': return val_l % val_r, type_l
        except Exception:
            from ..errors.error import InterpreterError, ErrorType
            error_manager.add_error(InterpreterError(
                ErrorType.SEMANTIC, f"No es posible aplicar el operador '{self.operator}' entre los tipos {type_l} y {type_r}.", self.line, self.column
            ))
        return None, OxigenType.NULL

class LogicalNode(Expression):
    def __init__(self, left, operator, right, line, column):
        super().__init__(line, column)
        self.left = left
        self.operator = operator
        self.right = right
        
    def execute(self, env, error_manager, console):
        val_l, type_l = self.left.execute(env, error_manager, console)
        if type_l != OxigenType.BOOL:
            return None, OxigenType.NULL
            
        # Short circuit
        if self.operator == '&&':
            if not val_l: return False, OxigenType.BOOL
            val_r, type_r = self.right.execute(env, error_manager, console)
            return val_l and val_r, OxigenType.BOOL
        elif self.operator == '||':
            if val_l: return True, OxigenType.BOOL
            val_r, type_r = self.right.execute(env, error_manager, console)
            return val_l or val_r, OxigenType.BOOL
            
        return None, OxigenType.NULL

class RelationalNode(Expression):
    def __init__(self, left, operator, right, line, column):
        super().__init__(line, column)
        self.left = left
        self.operator = operator
        self.right = right
        
    def execute(self, env, error_manager, console):
        val_l, type_l = self.left.execute(env, error_manager, console)
        val_r, type_r = self.right.execute(env, error_manager, console)
        
        if val_l is None or val_r is None: return None, OxigenType.NULL
        
        if self.operator == '==': return val_l == val_r, OxigenType.BOOL
        if self.operator == '!=': return val_l != val_r, OxigenType.BOOL
        if self.operator == '>': return val_l > val_r, OxigenType.BOOL
        if self.operator == '<': return val_l < val_r, OxigenType.BOOL
        if self.operator == '>=': return val_l >= val_r, OxigenType.BOOL
        if self.operator == '<=': return val_l <= val_r, OxigenType.BOOL
        
        return None, OxigenType.NULL

# ================= INSTRUCTIONS =================

class PrintlnNode(Instruction):
    def __init__(self, expressions, line, column):
        super().__init__(line, column)
        self.expressions = expressions # Can be a string with {} and variables

    def execute(self, env, error_manager, console):
        if len(self.expressions) == 0: return
        
        format_str_node = self.expressions[0]
        format_str, _ = format_str_node.execute(env, error_manager, console)
        
        if len(self.expressions) > 1:
            values = []
            for exp in self.expressions[1:]:
                v, t = exp.execute(env, error_manager, console)
                if v is not None: values.append(str(v))
            
            try:
                for v in values:
                    format_str = format_str.replace("{}", v, 1)
            except Exception:
                pass
        
        console.append(str(format_str))

class DeclarationNode(Instruction):
    def __init__(self, is_mut, id_name, decl_type, expression, line, column):
        super().__init__(line, column)
        self.is_mut = is_mut
        self.id_name = id_name
        self.decl_type = decl_type
        self.expression = expression

    def execute(self, env, error_manager, console):
        val, t = None, OxigenType.NULL
        if self.expression:
            val, t = self.expression.execute(env, error_manager, console)
            
        final_type = self.decl_type if self.decl_type else t
        
        if self.decl_type and t != OxigenType.NULL and self.decl_type != t:
            from ..errors.error import InterpreterError, ErrorType
            error_manager.add_error(InterpreterError(
                ErrorType.SEMANTIC, f"Tipos incompatibles. No es posible utilizar un valor de tipo {t} donde se esperaba un valor de tipo {self.decl_type}.", self.line, self.column
            ))
            return
            
        env.save_variable(self.id_name, final_type, val, self.is_mut, self.line, self.column)

class AssignmentNode(Instruction):
    def __init__(self, id_name, expression, operator, line, column):
        super().__init__(line, column)
        self.id_name = id_name
        self.expression = expression
        self.operator = operator # = += -= *= etc

    def execute(self, env, error_manager, console):
        symbol = env.get_variable(self.id_name)
        if not symbol:
            from ..errors.error import InterpreterError, ErrorType
            error_manager.add_error(InterpreterError(
                ErrorType.SEMANTIC, f"La variable '{self.id_name}' no ha sido declarada.", self.line, self.column
            ))
            return
            
        if not symbol.is_mut:
            from ..errors.error import InterpreterError, ErrorType
            error_manager.add_error(InterpreterError(
                ErrorType.SEMANTIC, f"No es posible modificar una variable inmutable.", self.line, self.column
            ))
            return
            
        val, t = self.expression.execute(env, error_manager, console)
        env.update_variable(self.id_name, val)

class BlockNode(Instruction):
    def __init__(self, instructions, line, column):
        super().__init__(line, column)
        self.instructions = instructions

    def execute(self, env, error_manager, console):
        from ..env.environment import Environment
        local_env = Environment(env, f"{env.name}_block")
        
        for inst in self.instructions:
            result = inst.execute(local_env, error_manager, console)
            # Handle return, break, continue here
            if result is not None:
                return result

class FunctionNode(Instruction):
    def __init__(self, name, params, return_type, block, line, column):
        super().__init__(line, column)
        self.name = name
        self.params = params
        self.return_type = return_type
        self.block = block

    def execute(self, env, error_manager, console):
        env.save_function(self.name, self, self.line, self.column)
