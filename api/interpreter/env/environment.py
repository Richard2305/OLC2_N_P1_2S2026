class Symbol:
    def __init__(self, name, symbol_type, value, is_mut, env_name, line, column, category="Variable"):
        self.name = name
        self.type = symbol_type
        self.value = value
        self.is_mut = is_mut
        self.env_name = env_name
        self.line = line
        self.column = column
        self.category = category  # Variable, Función, Struct

    def to_dict(self):
        # Symbol Table
        return {
            "identificador": self.name,
            "categoria": self.category,
            "tipo": str(self.type),
            "ambito": self.env_name,
            "linea": self.line,
            "valor": str(self.value) if self.category == "Variable" else "—"
        }

class Environment:
    def __init__(self, previous=None, name="Global"):
        self.previous = previous
        self.name = name
        self.symbols = {}
        self.functions = {}
        self.structs = {}
        if previous is not None:
            self.all_symbols = previous.all_symbols
        else:
            self.all_symbols = []

    def save_variable(self, name, symbol_type, value, is_mut, line, column):
        symbol = Symbol(name, symbol_type, value, is_mut, self.name, line, column)
        self.symbols[name] = symbol
        self.all_symbols.append(symbol)

    def get_variable(self, name):
        env = self
        while env is not None:
            if name in env.symbols:
                return env.symbols[name]
            env = env.previous
        return None
        
    def save_function(self, name, func_node, line, column):
        symbol = Symbol(name, "Función", None, False, self.name, line, column, category="Función")
        self.functions[name] = {
            "node": func_node,
            "symbol": symbol
        }
        self.all_symbols.append(symbol)
        
    def get_function(self, name):
        env = self
        while env is not None:
            if name in env.functions:
                return env.functions[name]
            env = env.previous
        return None

    def save_struct(self, name, struct_node, line, column):
        symbol = Symbol(name, "Struct", None, False, self.name, line, column, category="Struct")
        self.structs[name] = {
            "node": struct_node,
            "symbol": symbol
        }
        self.all_symbols.append(symbol)
        
    def get_struct(self, name):
        env = self
        while env is not None:
            if name in env.structs:
                return env.structs[name]
            env = env.previous
        return None

    def update_variable(self, name, value):
        env = self
        while env is not None:
            if name in env.symbols:
                env.symbols[name].value = value
                return True
            env = env.previous
        return False
        
    def get_global(self):
        env = self
        while env.previous is not None:
            env = env.previous
        return env
