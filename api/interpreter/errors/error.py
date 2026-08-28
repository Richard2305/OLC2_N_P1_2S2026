class ErrorType:
    LEXICAL = "Léxico"
    SYNTACTIC = "Sintáctico"
    SEMANTIC = "Semántico"

class InterpreterError:
    def __init__(self, error_type, description, line, column):
        self.error_type = error_type
        self.description = description
        self.line = line
        self.column = column

    def __str__(self):
        return f"[Error {self.error_type}] Línea {self.line}, Columna {self.column}\n{self.description}"

    def to_dict(self):
        return {
            "tipo": self.error_type,
            "descripcion": self.description,
            "linea": self.line,
            "columna": self.column
        }

class ErrorManager:
    def __init__(self):
        self.errors = []

    def add_error(self, error: InterpreterError):
        self.errors.append(error)

    def has_errors(self):
        return len(self.errors) > 0

    def get_errors(self):
        return self.errors
    
    def get_errors_dict(self):
        return [err.to_dict() for err in self.errors]
    
    def clear(self):
        self.errors = []
