from enum import Enum, auto

class OxigenType(Enum):
    I32 = "i32"
    F64 = "f64"
    BOOL = "bool"
    CHAR = "char"
    STRING = "String"
    ARRAY = "array"
    STRUCT = "struct"
    NULL = "None"
    
    def __str__(self):
        return self.value
