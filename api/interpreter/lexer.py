import ply.lex as lex
from .errors.error import InterpreterError, ErrorType

reserved = {
    'fn':       'FN',
    'let':      'LET',
    'mut':      'MUT',
    'if':       'IF',
    'else':     'ELSE',
    'while':    'WHILE',
    'repeat':   'REPEAT',
    'loop':     'LOOP',
    'match':    'MATCH',
    'break':    'BREAK',
    'continue': 'CONTINUE',
    'return':   'RETURN',
    'struct':   'STRUCT',
    'true':     'TRUE',
    'false':    'FALSE',
    'i32':      'TYPE_I32',
    'f64':      'TYPE_F64',
    'bool':     'TYPE_BOOL',
    'char':     'TYPE_CHAR',
    'String':   'TYPE_STRING',
}

tokens = [
    'IDENTIFIER',
    'INT_LITERAL',
    'FLOAT_LITERAL',
    'STRING_LITERAL',
    'CHAR_LITERAL',
    'RAW_STRING',
    'LABEL',             # 'outer  'inner  (loop labels)
    'FORMAT_DEBUG',      # {:?}

    # Compound operators
    'PLUS_ASSIGN', 'MINUS_ASSIGN', 'TIMES_ASSIGN', 'DIVIDE_ASSIGN', 'MOD_ASSIGN',
    'EQ', 'NEQ', 'GTE', 'LTE', 'AND', 'OR',
    'ARROW', 'FAT_ARROW', 'DOUBLE_COLON', 'RANGE',

    # Simple operators
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
    'ASSIGN', 'GT', 'LT', 'NOT', 'AMPERSAND',

    # Punctuation
    'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET',
    'COMMA', 'SEMICOLON', 'COLON', 'DOT', 'PRINTLN_MACRO',
] + list(reserved.values())

# ──────────────────────────────────────────────────────────────────────────
# Functions  (complex / variable-length patterns)
# ──────────────────────────────────────────────────────────────────────────

def t_COMMENT_BLOCK(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')

def t_COMMENT_LINE(t):
    r'//[^\n]*'
    pass  # discard

def t_RAW_STRING(t):
    r'r\#"(?:.|\n)*?"\#|r"(?:.|\n)*?"'
    # Handles both r"..." and r#"..."# properly, even with internal quotes
    val = t.value
    if val.startswith('r#"') and val.endswith('"#'):
        t.value = val[3:-2]
    elif val.startswith('r"') and val.endswith('"'):
        t.value = val[2:-1]
    return t

def t_STRING_LITERAL(t):
    r'"([^"\\]|\\.)*"'
    raw = t.value[1:-1]
    raw = (raw.replace('\\n', '\n')
               .replace('\\t', '\t')
               .replace('\\"', '"')
               .replace('\\\\', '\\'))
    t.value = raw
    return t

def t_CHAR_LITERAL(t):
    r"'([^'\\]|\\.)'"
    v = t.value[1:-1]
    escapes = {'\\n': '\n', '\\t': '\t', "\\'": "'", '\\"': '"', '\\\\': '\\'}
    t.value = escapes.get(v, v)
    return t

def t_LABEL(t):
    r"'[a-zA-Z_][a-zA-Z_0-9]*"
    t.value = t.value[1:]  # strip leading '
    return t

def t_FLOAT_LITERAL(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_INT_LITERAL(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_PRINTLN_MACRO(t):
    r'println!'
    return t

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    col = _find_column(t.lexer.lexdata, t)
    if hasattr(t.lexer, 'error_manager'):
        t.lexer.error_manager.add_error(
            InterpreterError(ErrorType.LEXICAL,
                             f"Carácter no reconocido: '{t.value[0]}'",
                             t.lexer.lineno, col))
    t.lexer.skip(1)

def _find_column(source, token):
    line_start = source.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1

# ──────────────────────────────────────────────────────────────────────────
# String patterns
# ──────────────────────────────────────────────────────────────────────────
t_FORMAT_DEBUG  = r'\{:\?}'

t_PLUS_ASSIGN   = r'\+='
t_MINUS_ASSIGN  = r'-='
t_TIMES_ASSIGN  = r'\*='
t_DIVIDE_ASSIGN = r'/='
t_MOD_ASSIGN    = r'%='
t_EQ            = r'=='
t_NEQ           = r'!='
t_GTE           = r'>='
t_LTE           = r'<='
t_AND           = r'&&'
t_OR            = r'\|\|'
t_ARROW         = r'->'
t_FAT_ARROW     = r'=>'
t_DOUBLE_COLON  = r'::'
t_RANGE         = r'\.\.'

t_PLUS          = r'\+'
t_MINUS         = r'-'
t_TIMES         = r'\*'
t_DIVIDE        = r'/'
t_MOD           = r'%'
t_ASSIGN        = r'='
t_GT            = r'>'
t_LT            = r'<'
t_NOT           = r'!'
t_AMPERSAND     = r'&'

t_LPAREN        = r'\('
t_RPAREN        = r'\)'
t_LBRACE        = r'\{'
t_RBRACE        = r'\}'
t_LBRACKET      = r'\['
t_RBRACKET      = r'\]'
t_COMMA         = r','
t_SEMICOLON     = r';'
t_COLON         = r':'
t_DOT           = r'\.'

t_ignore = ' \t\r'

# Build
lexer = lex.lex()
