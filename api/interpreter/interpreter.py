from .lexer import lexer
from .parser import parser
from .env.environment import Environment
from .errors.error import ErrorManager
import traceback

class CompilerEngine:
    def __init__(self):
        self.error_manager = ErrorManager()
        self.global_env = Environment(name="Global")
        self.console = []
        
    def execute(self, source_code):
        self.error_manager.clear()
        self.global_env = Environment(name="Global")
        self.console = []
        
        # Inject error manager
        lexer.error_manager = self.error_manager
        parser.error_manager = self.error_manager
        lexer.lineno = 1  # Reset line counter for each execution
        
        ast_nodes = None
        try:
            # Parse
            ast_nodes = parser.parse(source_code, lexer=lexer)
            
            if ast_nodes:
                # First pass: register functions
                main_func = None
                for node in ast_nodes:
                    if node is None: continue
                    from .ast.instructions import FunctionNode
                    if isinstance(node, FunctionNode):
                        node.execute(self.global_env, self.error_manager, self.console)
                        if node.name == "main":
                            main_func = node
                
                # Execute main
                if main_func:
                    from .env.environment import Environment as Env
                    main_env = Env(self.global_env, "main")
                    main_func.block.execute(main_env, self.error_manager, self.console)
                else:
                    self.console.append("[Error] No se encontró la función 'main'.")
                    
        except Exception as e:
            self.console.append(f"[Error Interno] {str(e)}")
            traceback.print_exc()
            
        ast_dot = "digraph G {\nnode [shape=box];\n"
        if ast_nodes and not self.error_manager.has_errors():
            counter = 0
            for i, node in enumerate(ast_nodes):
                id_n, dot_n, counter = node.get_dot(counter)
                ast_dot += dot_n
                ast_dot += f'Root -> {id_n};\n'
        ast_dot += "}"
        
        return {
            "console": "\n".join(self.console),
            "errors": self.error_manager.get_errors_dict(),
            "symbols": self.get_symbols_dict(),
            "ast_dot": ast_dot
        }
        
    def get_symbols_dict(self):
        symbols = []
        for sym in self.global_env.all_symbols:
            symbols.append(sym.to_dict())
        return symbols
