from ..env.types import OxigenType
from ..errors.error import InterpreterError, ErrorType

class TypeChecker:
    @staticmethod
    def check_arithmetic(op, left_type, right_type, line, col, error_manager):
        if op == '+':
            if left_type == OxigenType.I32 and right_type == OxigenType.I32: return OxigenType.I32
            if left_type == OxigenType.F64 and right_type == OxigenType.F64: return OxigenType.F64
            if left_type == OxigenType.STRING and right_type == OxigenType.STRING: return OxigenType.STRING
            
            # Promotions i32 and f64
            if left_type == OxigenType.I32 and right_type == OxigenType.F64: return OxigenType.F64
            if left_type == OxigenType.F64 and right_type == OxigenType.I32: return OxigenType.F64
            
        elif op == '-':
            if left_type == OxigenType.I32 and right_type == OxigenType.I32: return OxigenType.I32
            if left_type == OxigenType.F64 and right_type == OxigenType.F64: return OxigenType.F64
            # Promotions
            if left_type == OxigenType.I32 and right_type == OxigenType.F64: return OxigenType.F64
            if left_type == OxigenType.F64 and right_type == OxigenType.I32: return OxigenType.F64

        elif op == '*':
            if left_type == OxigenType.I32 and right_type == OxigenType.I32: return OxigenType.I32
            if left_type == OxigenType.F64 and right_type == OxigenType.F64: return OxigenType.F64
            if left_type == OxigenType.I32 and right_type == OxigenType.STRING: return OxigenType.STRING
            if left_type == OxigenType.STRING and right_type == OxigenType.I32: return OxigenType.STRING
            
            # Promotions
            if left_type == OxigenType.I32 and right_type == OxigenType.F64: return OxigenType.F64
            if left_type == OxigenType.F64 and right_type == OxigenType.I32: return OxigenType.F64

        elif op == '/':
            if left_type == OxigenType.I32 and right_type == OxigenType.I32: return OxigenType.I32
            if left_type == OxigenType.F64 and right_type == OxigenType.F64: return OxigenType.F64
            
            # Promotions
            if left_type == OxigenType.I32 and right_type == OxigenType.F64: return OxigenType.F64
            if left_type == OxigenType.F64 and right_type == OxigenType.I32: return OxigenType.F64

        elif op == '%':
            if left_type == OxigenType.I32 and right_type == OxigenType.I32: return OxigenType.I32
            if left_type == OxigenType.F64 and right_type == OxigenType.F64: return OxigenType.F64
            
            # Promotions
            if left_type == OxigenType.I32 and right_type == OxigenType.F64: return OxigenType.F64
            if left_type == OxigenType.F64 and right_type == OxigenType.I32: return OxigenType.F64
            
        error_manager.add_error(InterpreterError(
            ErrorType.SEMANTIC, 
            f"No es posible aplicar el operador '{op}' entre los tipos {left_type.value} y {right_type.value}.", 
            line, col
        ))
        return OxigenType.NULL
        
    @staticmethod
    def check_relational(op, left_type, right_type, line, col, error_manager):
        if op in ['==', '!=']:
            if left_type == right_type: return OxigenType.BOOL
        elif op in ['>', '<', '>=', '<=']:
            if left_type in [OxigenType.I32, OxigenType.F64] and right_type in [OxigenType.I32, OxigenType.F64]:
                return OxigenType.BOOL
            if left_type == OxigenType.CHAR and right_type == OxigenType.CHAR:
                return OxigenType.BOOL
            if left_type == OxigenType.STRING and right_type == OxigenType.STRING:
                return OxigenType.BOOL
                
        error_manager.add_error(InterpreterError(
            ErrorType.SEMANTIC, 
            f"No es posible aplicar el operador '{op}' entre los tipos {left_type.value} y {right_type.value}.", 
            line, col
        ))
        return OxigenType.NULL

    @staticmethod
    def check_logical(op, left_type, right_type, line, col, error_manager):
        if left_type == OxigenType.BOOL and right_type == OxigenType.BOOL:
            return OxigenType.BOOL
            
        error_manager.add_error(InterpreterError(
            ErrorType.SEMANTIC, 
            f"No es posible aplicar el operador '{op}' entre los tipos {left_type.value} y {right_type.value}.", 
            line, col
        ))
        return OxigenType.NULL
