# Documentación Técnica - Intérprete OxigenScript

## Arquitectura del Proyecto

El proyecto OxigenScript está construido como una aplicación monolítica utilizando **Django (Python)** para el backend web y la API de ejecución, combinada con **PLY (Python Lex-Yacc)** para el análisis léxico y sintáctico.

La arquitectura sigue el patrón de diseño **Interpreter** y utiliza **Árboles de Sintaxis Abstracta (AST)** para la representación del código fuente antes de su ejecución.

### Componentes Principales

1. **Analizador Léxico (`lexer.py`)**: 
   Define las expresiones regulares para identificar palabras reservadas, símbolos, y valores literales (enteros, decimales, strings, booleanos). Procesa el texto de entrada y lo convierte en una secuencia de `Tokens`.

2. **Analizador Sintáctico (`parser.py`)**: 
   Utiliza las gramáticas LALR definidas para construir el AST. Contiene las reglas sintácticas como declaraciones, asignaciones, ciclos (while, loop), funciones y estructuras (structs).

3. **Árbol de Sintaxis Abstracta (AST)**:
   - `expressions.py`: Contiene los nodos que siempre devuelven un valor y un tipo (`(value, OxigenType)`). Por ejemplo, operaciones aritméticas, relacionales, lógicas, acceso a arreglos y llamadas a métodos.
   - `instructions.py`: Contiene los nodos de sentencias que controlan el flujo o modifican el entorno, como variables (`let`), asignaciones (`=`), ciclos (`while`), condiciones (`if`), y llamadas a macros (`println!`).

4. **Chequeo de Tipos (`type_checker.py`) y Entorno (`env.py`)**:
   Implementa validaciones semánticas estrictas, permitiendo control de mutabilidad, reglas de "sombreado" (shadowing), y promoción de tipos (ej. `i32` a `f64`).

5. **Motor de Ejecución (`interpreter.py`)**:
   Orquesta la fase de Parsing y la de Ejecución. Intercepta los errores (léxicos, sintácticos y semánticos), almacena los prints de consola y recolecta la tabla de símbolos y reporte de AST en Dot.

## Flujo de Datos

1. **Recepción del Input**: El usuario envía el código a través de la UI (Frontend), y es recibido en `api/views.py`.
2. **Análisis**: El `CompilerEngine` de `interpreter.py` instancia el `lexer` y el `parser`.
3. **Parseo y Generación de AST**: Si el parseo es exitoso, se genera un bloque de nodos raíz.
4. **Validaciones Semánticas Iniciales**: Se recopilan funciones, structs y constantes y se guardan en el Entorno Global.
5. **Ejecución**: Se ubica la función `main()` y se llama su método `execute()`. Las variables, resultados y posibles errores semánticos se registran en el `Environment` y `ErrorManager`.
6. **Respuesta API**: Se compila un JSON de respuesta con el texto de la consola, la lista de errores, los símbolos detectados y el código Graphviz para renderizar el AST.

## Patrones Implementados

- **Evaluación de Expresiones por Tipado Fuerte**: OxigenScript evalúa operaciones y devuelve una tupla de `(Valor, Tipo)`.
- **Ámbitos (Scope) Jerárquicos**: Soporte total para variables locales. Cada bloque (`{}`) y función genera un nuevo `Environment` hijo que preserva las variables superiores pero aislando las nuevas.
- **Corto Circuito Lógico**: Las operaciones `&&` y `||` detienen su evaluación inmediatamente cuando el primer operando determina el resultado.
- **Inmutabilidad por Defecto**: Variables requieren `let mut` explícito para aceptar reasignaciones, siendo forzado de forma nativa por el validador semántico.
