from lark import Lark, Transformer, v_args
from src.evaluator import ConstantNode, CellNode, FunctionNode, BinaryOpNode, FormulaNode



# Определение грамматики для Excel-подобных формул
EXCEL_GRAMMAR = r"""CELL: /[A-Za-z]+\d+(:[A-Za-z]+\d+)?/
SHEET_NAME: /[A-Za-z_]\w+/
NAME: /[A-Za-z_]\w*/
?start: expr
?expr: expr "+" term   -> add
     | expr "-" term   -> sub
     | term
?term: term "*" factor -> mul
     | term "/" factor -> div
     | factor
?factor: cell_ref
       | function_call
       | NUMBER         -> number
       | "(" expr ")"
function_call: NAME "(" [args] ")"
args: expr ("," expr)*
cell_ref: SHEET_NAME "!" CELL -> sheet_cell
        | CELL                -> cell
%import common.NUMBER  -> NUMBER
%import common.WS_INLINE
%ignore WS_INLINE
"""

#%import common.CNAME   -> NAME




@v_args(inline=True)
class ToAST(Transformer):
    """
    Класс ToAST отвечает за преобразование дерева разбора (Parse Tree) Lark
    в наше пользовательское AST на основе узлов-объектов: ConstantNode, CellNode,
    FunctionNode и BinaryOpNode.
    """
    # Импорт стандартных операторных функций из модуля operator
    # add, sub, mul и div используются автоматически при совпадении правил Lark
    from operator import add, sub, mul, truediv as div

    def number(self, token):
        """
        Метод обрабатывает лексему NUMBER из грамматики.
        token: токен, содержащий строку с числом (например, "3.14").
        Возвращает объект ConstantNode с числовым значением.
        """
        # Конвертируем строку токена в float и создаём узел константы
        return ConstantNode(float(token))

    def cell(self, token):
        """
        Метод обрабатывает локальную ссылку на ячейку без имени листа,
        например A1 или B2:C3.
        token.value — строка вида "A1".
        Возвращает объект CellNode.
        """
        # Создаём узел, который при eval достанет значение по ключу token.value
        return CellNode(token.value)

    def sheet_cell(self, sheet, cell):
        """
        Метод обрабатывает межлистовую ссылку на ячейку,
        например Sheet1!A1 или Sheet2!B2:C3.
        sheet.value — имя листа, cell.value — адрес ячейки или диапазона.
        Возвращает объект CellNode с полным адресом.
        """
        # Объединяем имя листа и адрес ячейки в формате "Sheet!Cell"
        full_ref = f"{sheet.value}!{cell.value}"
        return CellNode(full_ref)

    def function_call(self, name, *args):
        """
        Обрабатывает узел вызова функции:
        - name: Token с именем функции (например, 'SUM')
        - *args: один или несколько аргументов, которые могут быть
        либо списками (если их обёрнуло правило args), либо
        уже преобразованными AST-узлами (ConstantNode, CellNode, и т.д.)
        """
        flat = []  # Здесь будем накапливать "расплющенный" список аргументов
        
        # Проходим по всем полученным аргументам
        for a in args:
            # Если аргумент — это список (правило args вернуло список дочерних узлов),
            # то разворачиваем его в общий список flat
            if isinstance(a, list):
                flat.extend(a)
            else:
                # Иначе просто добавляем одиночный узел
                flat.append(a)
        
        # name.value.upper() — приводим имя функции к верхнему регистру,
        # чтобы ключ словаря excel_funcs находился без учёта регистра.
        # flat — это список AST-узлов аргументов, готовых к вычислению.
        return FunctionNode(name.value.upper(), flat)


    def add(self, a, b):
        """
        Правило для оператора сложения '+'.
        При совпадении создаёт узел BinaryOpNode('+', left, right).
        a, b — дочерние узлы-операнды (уже преобразованные в FormulaNode).
        """
        return BinaryOpNode('+', a, b)

    def sub(self, a, b):
        """
        Правило для оператора вычитания '-'.
        """
        return BinaryOpNode('-', a, b)

    def mul(self, a, b):
        """
        Правило для оператора умножения '*'.
        """
        return BinaryOpNode('*', a, b)

    def div(self, a, b):
        """
        Правило для оператора деления '/'.
        """
        return BinaryOpNode('/', a, b)
    
    def start(self, children):
        return children[0]
    
    def args(self, children):
        """
        Правило `args: expr ("," expr)*`.
        Здесь дочерние элементы уже распакованы как отдельные аргументы,
        поэтому собираем их обратно в список.
        """
        return list(children)






# ----------------------------------------------------------------------------
# Создание парсера и обёртки для преобразования строковых формул
# ----------------------------------------------------------------------------

# Инициализируем Lark-парсер, передав в него нашу грамматику EXCEL_GRAMMAR и алгоритм lalr
#parser = Lark(EXCEL_GRAMMAR, parser='lalr')
parser = Lark(EXCEL_GRAMMAR, parser='lalr', lexer='standard')




def parse_formula(formula: str) -> FormulaNode:
    """
    Главная функция парсинга формулы:
      1. Убирает ведущий символ '=' (как в Excel).
      2. Пропускает оставшийся текст через Lark-парсер, получая Parse Tree.
      3. Преобразует Parse Tree в наш AST (набор объектов FormulaNode).

    Параметры:
    - formula: строка формулы, например "=SUM(A1,B2)+IF(C3>0,D4,E5)".

    Возвращает:
    - Экземпляр FormulaNode (корневой узел AST).
    """
    # 1) Удаляем префикс '=' если он есть
    text = formula.lstrip('=')  # 'SUM(A1,B2)+IF(C3>0,D4,E5)'

    # 2) Лексико-синтаксический анализ: строим дерево разбора
    #    Lark выберет правильные правила грамматики EXCEL_GRAMMAR
    tree = parser.parse(text)

    # 3) Преобразуем Parse Tree в удобную объектную модель AST
    #    ToAST — наш класс-Transformer, который создаёт узлы FormulaNode
    ast = ToAST().transform(tree)

    # Возвращаем корень AST для последующего вычисления
    return ast
