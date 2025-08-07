from lark import Lark, Transformer, v_args
from src.evaluator import ConstantNode, CellNode, FunctionNode, BinaryOpNode, FormulaNode
from lark.exceptions import UnexpectedInput

# Определение грамматики для Excel-подобных формул
# Грамматика будет поддерживать операторы, ссылки на ячейки, функции и арифметику

EXCEL_GRAMMAR = r"""
    // Комментарии начинаются с '//' и продолжаются до конца строки
    COMMENT: /\/\/[^\n]*/
    %ignore COMMENT

    // --- Терминалы ---
    // Для чисел, строк и переменных
    CELL:       /[A-Za-z]+\d+(:[A-Za-z]+\d+)?/   // Ячейки, например A1 или B2:C3
    SHEET_NAME: /[A-Za-z_]\w+/                    // Названия листов, например Sheet1 или My_Sheet

    // Импортируем стандартные токены
    %import common.CNAME      -> NAME
    %import common.NUMBER     -> NUMBER
    %import common.WS_INLINE
    %ignore WS_INLINE          // Игнорируем пробелы и табуляцию

    // Основное правило для формул
    ?start: expr

    // Операции с термами, включая арифметику и сложение
    ?expr: expr "+" term    -> add
         | expr "-" term    -> sub
         | term

    // Операции с термами умножения и деления
    ?term: factor "*" factor -> mul
         | factor "/" factor -> div
         | factor

    // Факторы: это могут быть ячейки, числа или выражения в скобках
    ?factor: NUMBER          -> number
           | NAME            -> cell
           | "(" expr ")"

    // Правила для операций
    add: expr "+" term  -> add_op
    sub: expr "-" term  -> sub_op
    mul: term "*" factor -> mul_op
    div: term "/" factor -> div_op

    // Разбор функций с несколькими аргументами
    function_call: NAME "(" [ expr ("," expr)* ] ")" -> function_call

    // Разбор ячеек и ссылок
    cell_ref: SHEET_NAME "!" CELL   -> sheet_cell
            | CELL                  -> cell
"""





# Инициализация парсера Lark с заданной грамматикой и алгоритмом обработки ошибок
# Мы будем использовать 'lalr' для парсинга и 'contextual' лексер для лучшей работы с контекстом
parser = Lark(EXCEL_GRAMMAR, parser='lalr', lexer='contextual')


@v_args(inline=True)  # Включение inline для упрощения возвращаемых значений
class ToAST(Transformer):
    """
    Класс ToAST преобразует дерево разбора (Parse Tree) в наше собственное AST (объектное представление),
    которое состоит из различных узлов: ConstantNode, CellNode, FunctionNode, BinaryOpNode.
    """

    # Для операторов используем стандартные операторы Python
    from operator import add, sub, mul, truediv as div

    def number(self, token):
        """
        Преобразует лексему NUMBER (число) в объект ConstantNode.
        """
        # Конвертируем строковое значение в число (например, "3" в 3.0)
        return ConstantNode(float(token))

    def cell(self, token):
        """
        Преобразует ссылку на ячейку (например, "A1") в объект CellNode.
        """
        return CellNode(token.value)  # Используем значение токена (адрес ячейки) для создания узла

    def sheet_cell(self, sheet, cell):
        """
        Преобразует межлистовую ссылку (например, "Sheet1!A1") в объект CellNode с полным адресом.
        """
        full_ref = f"{sheet.value}!{cell.value}"  # Формируем полный адрес: "Sheet1!A1"
        return CellNode(full_ref)

    def function_call(self, name, *args):
        """
        Преобразует вызов функции (например, SUM(A1, B1)) в объект FunctionNode.
        """
        # Преобразуем имя функции в верхний регистр и создаем объект FunctionNode с аргументами
        return FunctionNode(name.value.upper(), list(args))

    # Операторы: создание бинарных узлов для операций
    def add(self, a, b):
        """
        Создает узел для операции сложения "+"
        """
        return BinaryOpNode('+', a, b)

    def sub(self, a, b):
        """
        Создает узел для операции вычитания "-"
        """
        return BinaryOpNode('-', a, b)

    def mul(self, a, b):
        """
        Создает узел для операции умножения "*"
        """
        return BinaryOpNode('*', a, b)

    def div(self, a, b):
        """
        Создает узел для операции деления "/"
        """
        return BinaryOpNode('/', a, b)

    # Методы для операций сравнения (например, A1 > 0)
    def gt(self, a, b):
        return BinaryOpNode('>', a, b)

    def lt(self, a, b):
        return BinaryOpNode('<', a, b)

    def ge(self, a, b):
        return BinaryOpNode('>=', a, b)

    def le(self, a, b):
        return BinaryOpNode('<=', a, b)

    def eq(self, a, b):
        return BinaryOpNode('=', a, b)

    def ne(self, a, b):
        return BinaryOpNode('<>', a, b)

    def start(self, children):
        """
        Вспомогательный метод для начала парсинга (первый узел дерева).
        """
        return children[0]


def parse_formula(formula: str) -> FormulaNode:
    """
    Главная функция для парсинга формулы:
      1. Убирает ведущий символ '=' (как в Excel).
      2. Пропускает оставшийся текст через Lark-парсер, получая Parse Tree.
      3. Преобразует Parse Tree в наш AST (объект FormulaNode).

    Параметры:
    - formula: строка формулы (например "=SUM(A1,B2)+IF(C3>0,D4,E5)").
    
    Возвращает:
    - Экземпляр FormulaNode (корневой узел AST).
    """
    # 1) Убираем префикс '=' если он есть
    text = formula.lstrip('=')  # Например, из "=SUM(A1,B2)" получится "SUM(A1,B2)"

    # 2) Лексико-синтаксический анализ: строим дерево разбора с помощью Lark
    try:
        tree = parser.parse(text)
    except UnexpectedInput as e:
        raise SyntaxError(f"Invalid formula syntax: {e}") from e

    # 3) Преобразуем Parse Tree в объектное представление (AST) с помощью ToAST
    ast = ToAST().transform(tree)

    # Возвращаем корень AST для последующего вычисления
    return ast
