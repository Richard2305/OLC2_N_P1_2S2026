import ply.yacc as yacc
from .lexer import tokens, lexer
from .ast.ast_nodes import ASTNode, Expression, Instruction
from .ast.expressions import (LiteralNode, IdentifierNode, ArithmeticNode,
    LogicalNode, RelationalNode, ArrayInitNode, ArrayAccessNode,
    FunctionCallNode, MethodCallNode, FieldAccessNode, SliceNode,
    StructInitNode, TypeofNode)
from .ast.instructions import (PrintlnNode, DeclarationNode, AssignmentNode,
    BlockNode, IfNode, WhileNode, FunctionNode, TransferNode, LoopNode, RepeatNode,
    MatchNode, StructDeclNode, ArrayAssignmentNode, ExpressionStmtNode)
from .env.types import OxigenType
from .errors.error import InterpreterError, ErrorType

# ──────────────────────────────────────────────────────────────────────────
# Precedence
# ──────────────────────────────────────────────────────────────────────────
precedence = (
    ('right', 'ELSE'),
    ('left',  'OR'),
    ('left',  'AND'),
    ('right', 'NOT'),
    ('left',  'EQ', 'NEQ'),
    ('left',  'LT', 'LTE', 'GT', 'GTE'),
    ('left',  'PLUS', 'MINUS'),
    ('left',  'TIMES', 'DIVIDE', 'MOD'),
    ('right', 'UMINUS'),
    ('left',  'DOT'),
    ('left',  'LBRACKET'),
)

# ──────────────────────────────────────────────────────────────────────────
# Program
# ──────────────────────────────────────────────────────────────────────────
def p_program(p):
    '''program : top_list'''
    p[0] = p[1]

def p_top_list(p):
    '''top_list : top_list top_item
                | top_item'''
    if len(p) == 3: p[1].append(p[2]); p[0] = p[1]
    else: p[0] = [p[1]]

def p_top_item(p):
    '''top_item : function_decl
                | struct_decl'''
    p[0] = p[1]

# ──────────────────────────────────────────────────────────────────────────
# Struct declaration
# ──────────────────────────────────────────────────────────────────────────
def p_struct_decl(p):
    '''struct_decl : STRUCT IDENTIFIER LBRACE struct_fields RBRACE'''
    p[0] = StructDeclNode(p[2], p[4], p.lineno(1), p.lexpos(1))

def p_struct_fields(p):
    '''struct_fields : struct_fields struct_field
                     | struct_field
                     | empty'''
    if len(p) == 3: p[1].append(p[2]); p[0] = p[1]
    elif p[1] is None: p[0] = []
    else: p[0] = [p[1]]

def p_struct_field(p):
    '''struct_field : IDENTIFIER COLON type COMMA'''
    p[0] = (p[1], p[3])

# ──────────────────────────────────────────────────────────────────────────
# Function declaration
# ──────────────────────────────────────────────────────────────────────────
def p_function_decl(p):
    '''function_decl : FN IDENTIFIER LPAREN param_list RPAREN LBRACE stmt_list RBRACE
                     | FN IDENTIFIER LPAREN param_list RPAREN ARROW type LBRACE stmt_list RBRACE'''
    if len(p) == 9:
        p[0] = FunctionNode(p[2], p[4], None, BlockNode(p[7], p.lineno(6), p.lexpos(6)), p.lineno(1), p.lexpos(1))
    else:
        p[0] = FunctionNode(p[2], p[4], p[7], BlockNode(p[9], p.lineno(8), p.lexpos(8)), p.lineno(1), p.lexpos(1))

def p_param_list(p):
    '''param_list : param_list COMMA param
                  | param
                  | empty'''
    if len(p) == 4: p[1].append(p[3]); p[0] = p[1]
    elif p[1] is None: p[0] = []
    else: p[0] = [p[1]]

def p_param(p):
    '''param : IDENTIFIER COLON type
             | MUT IDENTIFIER COLON type'''
    if len(p) == 4: p[0] = (p[1], p[3], False)
    else:           p[0] = (p[2], p[4], True)

# ──────────────────────────────────────────────────────────────────────────
# Types
# ──────────────────────────────────────────────────────────────────────────
def p_type_simple(p):
    '''type : TYPE_I32
            | TYPE_F64
            | TYPE_BOOL
            | TYPE_CHAR
            | TYPE_STRING
            | IDENTIFIER'''
    if p[1] == 'i32':    p[0] = OxigenType.I32
    elif p[1] == 'f64':  p[0] = OxigenType.F64
    elif p[1] == 'bool': p[0] = OxigenType.BOOL
    elif p[1] == 'char': p[0] = OxigenType.CHAR
    elif p[1] == 'String': p[0] = OxigenType.STRING
    else:                  p[0] = OxigenType.STRUCT

def p_type_array(p):
    '''type : LBRACKET type SEMICOLON INT_LITERAL RBRACKET'''
    p[0] = OxigenType.ARRAY

# ──────────────────────────────────────────────────────────────────────────
# Statements
# ──────────────────────────────────────────────────────────────────────────
def p_stmt_list(p):
    '''stmt_list : stmt_list stmt
                 | stmt'''
    if len(p) == 3:
        if p[2] is not None: p[1].append(p[2])
        p[0] = p[1]
    else:
        p[0] = [p[1]] if p[1] is not None else []

def p_stmt(p):
    '''stmt : let_decl SEMICOLON
            | assignment_stmt SEMICOLON
            | println_stmt SEMICOLON
            | return_stmt SEMICOLON
            | break_stmt SEMICOLON
            | continue_stmt SEMICOLON
            | expression SEMICOLON
            | if_stmt
            | while_stmt
            | loop_stmt
            | match_stmt
            | block_stmt
            | error SEMICOLON
            | error RBRACE'''
    if len(p) == 3 and p.slice[1].type == 'expression':
        p[0] = ExpressionStmtNode(p[1], p.lineno(1), p.lexpos(1))
    elif len(p) == 3 and p.slice[1].type == 'error':
        p[0] = None
    else:
        p[0] = p[1]

def p_block_stmt(p):
    '''block_stmt : LBRACE stmt_list RBRACE'''
    p[0] = BlockNode(p[2], p.lineno(1), p.lexpos(1))

# ──────────────────────────────────────────────────────────────────────────
# println!
# ──────────────────────────────────────────────────────────────────────────
def p_println_stmt_plain(p):
    '''println_stmt : PRINTLN_MACRO LPAREN expression RPAREN'''
    p[0] = PrintlnNode([p[3]], p.lineno(1), p.lexpos(1))

def p_println_stmt_fmt(p):
    '''println_stmt : PRINTLN_MACRO LPAREN expression COMMA arg_list RPAREN'''
    p[0] = PrintlnNode([p[3]] + p[5], p.lineno(1), p.lexpos(1))

def p_arg_list(p):
    '''arg_list : arg_list COMMA expression
                | expression'''
    if len(p) == 4: p[1].append(p[3]); p[0] = p[1]
    else: p[0] = [p[1]]

# ──────────────────────────────────────────────────────────────────────────
# Let declaration – separate rules per variant
# ──────────────────────────────────────────────────────────────────────────
def p_let_no_init_typed_mut(p):
    '''let_decl : LET MUT IDENTIFIER COLON type'''
    p[0] = DeclarationNode(True, p[3], p[5], None, p.lineno(1), p.lexpos(1))

def p_let_no_init_typed(p):
    '''let_decl : LET IDENTIFIER COLON type'''
    p[0] = DeclarationNode(False, p[2], p[4], None, p.lineno(1), p.lexpos(1))

def p_let_init_typed_mut(p):
    '''let_decl : LET MUT IDENTIFIER COLON type ASSIGN expression'''
    p[0] = DeclarationNode(True, p[3], p[5], p[7], p.lineno(1), p.lexpos(1))

def p_let_init_typed(p):
    '''let_decl : LET IDENTIFIER COLON type ASSIGN expression'''
    p[0] = DeclarationNode(False, p[2], p[4], p[6], p.lineno(1), p.lexpos(1))

def p_let_init_mut(p):
    '''let_decl : LET MUT IDENTIFIER ASSIGN expression'''
    p[0] = DeclarationNode(True, p[3], None, p[5], p.lineno(1), p.lexpos(1))

def p_let_init(p):
    '''let_decl : LET IDENTIFIER ASSIGN expression'''
    p[0] = DeclarationNode(False, p[2], None, p[4], p.lineno(1), p.lexpos(1))

# ──────────────────────────────────────────────────────────────────────────
# Assignment – separate rules
# ──────────────────────────────────────────────────────────────────────────
def p_assign_simple(p):
    '''assignment_stmt : expression ASSIGN expression'''
    if not isinstance(p[1], IdentifierNode):
        raise SyntaxError("Asignación inválida")
    p[0] = AssignmentNode(p[1].id_name, p[3], p[2], p.lineno(2), p.lexpos(2))

def p_assign_compound(p):
    '''assignment_stmt : expression PLUS_ASSIGN expression
                       | expression MINUS_ASSIGN expression
                       | expression TIMES_ASSIGN expression
                       | expression DIVIDE_ASSIGN expression
                       | expression MOD_ASSIGN expression'''
    if not isinstance(p[1], IdentifierNode):
        raise SyntaxError("Asignación inválida")
    p[0] = AssignmentNode(p[1].id_name, p[3], p[2], p.lineno(2), p.lexpos(2))

def p_assign_field(p):
    '''assignment_stmt : expression DOT IDENTIFIER ASSIGN expression'''
    if isinstance(p[1], IdentifierNode):
        target = f"{p[1].id_name}.{p[3]}"
    elif isinstance(p[1], FieldAccessNode):
        if isinstance(p[1].left, IdentifierNode):
            target = f"{p[1].left.id_name}.{p[1].field}.{p[3]}"
        else:
            target = f"nested.{p[3]}"
    else:
        target = f"expr.{p[3]}"
    p[0] = AssignmentNode(target, p[5], p[4], p.lineno(4), p.lexpos(4))

def p_assign_array(p):
    '''assignment_stmt : expression LBRACKET expression RBRACKET ASSIGN expression'''
    if not isinstance(p[1], IdentifierNode):
        raise SyntaxError("Asignación de arreglo inválida")
    p[0] = ArrayAssignmentNode(p[1].id_name, p[3], p[6], p[5], p.lineno(5), p.lexpos(5))

# ──────────────────────────────────────────────────────────────────────────
# Control flow
# ──────────────────────────────────────────────────────────────────────────
def p_if_simple(p):
    '''if_stmt : IF expression LBRACE stmt_list RBRACE'''
    p[0] = IfNode(p[2], BlockNode(p[4], p.lineno(3), p.lexpos(3)), None, p.lineno(1), p.lexpos(1))

def p_if_else(p):
    '''if_stmt : IF expression LBRACE stmt_list RBRACE ELSE LBRACE stmt_list RBRACE'''
    p[0] = IfNode(p[2], BlockNode(p[4], p.lineno(3), p.lexpos(3)),
                  BlockNode(p[8], p.lineno(7), p.lexpos(7)), p.lineno(1), p.lexpos(1))

def p_if_elif(p):
    '''if_stmt : IF expression LBRACE stmt_list RBRACE ELSE if_stmt'''
    p[0] = IfNode(p[2], BlockNode(p[4], p.lineno(3), p.lexpos(3)), p[7], p.lineno(1), p.lexpos(1))

def p_while_stmt(p):
    '''while_stmt : WHILE expression LBRACE stmt_list RBRACE'''
    p[0] = WhileNode(p[2], BlockNode(p[4], p.lineno(3), p.lexpos(3)), p.lineno(1), p.lexpos(1))

def p_loop_plain(p):
    '''loop_stmt : LOOP LBRACE stmt_list RBRACE'''
    p[0] = LoopNode(BlockNode(p[3], p.lineno(2), p.lexpos(2)), None, p.lineno(1), p.lexpos(1))






def p_repeat_plain(p):
    '''loop_stmt : REPEAT expression LBRACE stmt_list RBRACE'''
    p[0] = RepeatNode(
        BlockNode(p[4], p.lineno(3), p.lexpos(3)),
        p[2],
        None,
        p.lineno(1),
        p.lexpos(1)
    )




def p_loop_labeled(p):
    '''loop_stmt : LABEL COLON LOOP LBRACE stmt_list RBRACE'''
    p[0] = LoopNode(BlockNode(p[5], p.lineno(4), p.lexpos(4)), p[1], p.lineno(1), p.lexpos(1))

def p_match_stmt(p):
    '''match_stmt : MATCH expression LBRACE match_arms RBRACE'''
    p[0] = MatchNode(p[2], p[4], p.lineno(1), p.lexpos(1))

def p_match_arms(p):
    '''match_arms : match_arms match_arm
                  | match_arm'''
    if len(p) == 3: p[1].append(p[2]); p[0] = p[1]
    else: p[0] = [p[1]]

def p_match_arm_expr(p):
    '''match_arm : expression FAT_ARROW println_stmt COMMA
                 | expression FAT_ARROW expression COMMA'''
    blk = BlockNode([p[3]], p.lineno(2), p.lexpos(2))
    p[0] = (p[1], blk)

def p_match_arm_block(p):
    '''match_arm : expression FAT_ARROW LBRACE stmt_list RBRACE COMMA'''
    p[0] = (p[1], BlockNode(p[4], p.lineno(3), p.lexpos(3)))

def p_match_arm_wild(p):
    '''match_arm : IDENTIFIER FAT_ARROW println_stmt COMMA
                 | IDENTIFIER FAT_ARROW expression COMMA'''
    blk = BlockNode([p[3]], p.lineno(2), p.lexpos(2))
    if p[1] == '_':
        p[0] = ('_', blk)
    else:
        p[0] = (IdentifierNode(p[1], p.lineno(1), p.lexpos(1)), blk)

def p_return_stmt(p):
    '''return_stmt : RETURN
                   | RETURN expression'''
    p[0] = TransferNode("return", p[2] if len(p) > 2 else None, None, p.lineno(1), p.lexpos(1))

def p_break_stmt(p):
    '''break_stmt : BREAK
                  | BREAK LABEL'''
    p[0] = TransferNode("break", None, p[2] if len(p) > 2 else None, p.lineno(1), p.lexpos(1))

def p_continue_stmt(p):
    '''continue_stmt : CONTINUE
                     | CONTINUE LABEL'''
    p[0] = TransferNode("continue", None, p[2] if len(p) > 2 else None, p.lineno(1), p.lexpos(1))

# ──────────────────────────────────────────────────────────────────────────
# Expressions
# ──────────────────────────────────────────────────────────────────────────
def p_expr_list(p):
    '''expr_list : expr_list COMMA expression
                 | expression
                 | empty'''
    if len(p) == 4: p[1].append(p[3]); p[0] = p[1]
    elif p[1] is None: p[0] = []
    else: p[0] = [p[1]]

def p_expr_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression MOD expression
                  | expression EQ expression
                  | expression NEQ expression
                  | expression GT expression
                  | expression GTE expression
                  | expression LT expression
                  | expression LTE expression
                  | expression AND expression
                  | expression OR expression'''
    op = p[2]
    ln, col = p.lineno(2), p.lexpos(2)
    if op in ('+', '-', '*', '/', '%'):
        p[0] = ArithmeticNode(p[1], op, p[3], ln, col)
    elif op in ('==', '!=', '>', '>=', '<', '<='):
        p[0] = RelationalNode(p[1], op, p[3], ln, col)
    else:
        p[0] = LogicalNode(p[1], op, p[3], ln, col)

def p_expr_uminus(p):
    '''expression : MINUS expression %prec UMINUS'''
    p[0] = ArithmeticNode(LiteralNode(0, OxigenType.I32, p.lineno(1), p.lexpos(1)), '-', p[2], p.lineno(1), p.lexpos(1))

def p_expr_not(p):
    '''expression : NOT expression'''
    p[0] = LogicalNode(p[2], '!', None, p.lineno(1), p.lexpos(1))

def p_expr_paren(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2]

def p_expr_method_call(p):
    '''expression : expression DOT IDENTIFIER LPAREN expr_list RPAREN'''
    p[0] = MethodCallNode(p[1], p[3], p[5], p.lineno(2), p.lexpos(2))

def p_expr_field_access(p):
    '''expression : expression DOT IDENTIFIER'''
    p[0] = FieldAccessNode(p[1], p[3], p.lineno(2), p.lexpos(2))

def p_expr_index(p):
    '''expression : expression LBRACKET expression RBRACKET'''
    p[0] = ArrayAccessNode(p[1], p[3], p.lineno(2), p.lexpos(2))

def p_expr_slice(p):
    '''expression : AMPERSAND IDENTIFIER LBRACKET expression RANGE expression RBRACKET'''
    arr = IdentifierNode(p[2], p.lineno(2), p.lexpos(2))
    p[0] = SliceNode(arr, p[4], p[6], p.lineno(1), p.lexpos(1))

# String::from(expr) and String::new()
def p_expr_string_from(p):
    '''expression : TYPE_STRING DOUBLE_COLON IDENTIFIER LPAREN expression RPAREN'''
    p[0] = p[5]

def p_expr_string_new(p):
    '''expression : TYPE_STRING DOUBLE_COLON IDENTIFIER LPAREN RPAREN'''
    p[0] = LiteralNode("", OxigenType.STRING, p.lineno(1), p.lexpos(1))

# typeof(expr)
def p_expr_typeof(p):
    '''expression : IDENTIFIER LPAREN expression RPAREN'''
    if p[1] == 'typeof':
        p[0] = TypeofNode(p[3], p.lineno(1), p.lexpos(1))
    else:
        p[0] = FunctionCallNode(p[1], [p[3]], p.lineno(1), p.lexpos(1))

# General function call ident(args)
def p_expr_func_call(p):
    '''expression : IDENTIFIER LPAREN expr_list RPAREN'''
    p[0] = FunctionCallNode(p[1], p[3], p.lineno(1), p.lexpos(1))

# Array literal [1, 2, 3] or [val; rep]
def p_expr_array(p):
    '''expression : LBRACKET expr_list RBRACKET
                  | LBRACKET expression SEMICOLON expression RBRACKET'''
    if len(p) == 4:
        p[0] = ArrayInitNode(p[2], None, p.lineno(1), p.lexpos(1))
    else:
        p[0] = ArrayInitNode(None, (p[2], p[4]), p.lineno(1), p.lexpos(1))

def p_opt_comma(p):
    '''opt_comma : COMMA
                 | empty'''
    pass

# Struct literal: Point { x: 1, y: 2 }
def p_expr_struct_init(p):
    '''expression : expression LBRACE struct_init_fields opt_comma RBRACE'''
    if not isinstance(p[1], IdentifierNode):
        raise SyntaxError("El nombre del struct debe ser un identificador")
    p[0] = StructInitNode(p[1].id_name, p[3], p.lineno(2), p.lexpos(2))

def p_struct_init_fields(p):
    '''struct_init_fields : struct_init_fields COMMA struct_init_field
                          | struct_init_field
                          | empty'''
    if len(p) == 4: p[1].append(p[3]); p[0] = p[1]
    elif p[1] is None: p[0] = []
    else: p[0] = [p[1]]

def p_struct_init_field(p):
    '''struct_init_field : IDENTIFIER COLON expression'''
    p[0] = (p[1], p[3])

def p_expr_literal(p):
    '''expression : INT_LITERAL
                  | FLOAT_LITERAL
                  | STRING_LITERAL
                  | RAW_STRING
                  | CHAR_LITERAL
                  | TRUE
                  | FALSE'''
    v = p[1]; ln, col = p.lineno(1), p.lexpos(1)
    if type(v) == int:     p[0] = LiteralNode(v, OxigenType.I32,    ln, col)
    elif type(v) == float: p[0] = LiteralNode(v, OxigenType.F64,    ln, col)
    elif v == 'true':      p[0] = LiteralNode(True, OxigenType.BOOL, ln, col)
    elif v == 'false':     p[0] = LiteralNode(False,OxigenType.BOOL, ln, col)
    elif p.slice[1].type == 'CHAR_LITERAL': p[0] = LiteralNode(v, OxigenType.CHAR, ln, col)
    else:                  p[0] = LiteralNode(v, OxigenType.STRING, ln, col)

def p_expr_id(p):
    '''expression : IDENTIFIER'''
    p[0] = IdentifierNode(p[1], p.lineno(1), p.lexpos(1))

# ──────────────────────────────────────────────────────────────────────────
def p_empty(p):
    'empty :'
    pass

# ──────────────────────────────────────────────────────────────────────────
# Error – panic mode
# ──────────────────────────────────────────────────────────────────────────
def p_error(p):
    if p:
        err = InterpreterError(ErrorType.SYNTACTIC,
            f"Error sintáctico cerca de '{p.value}'.", p.lineno, p.lexpos)
        if hasattr(parser, 'error_manager'):
            parser.error_manager.add_error(err)
        # Rely on PLY's built-in error recovery mechanisms. No manual token consumption.

parser = yacc.yacc()
