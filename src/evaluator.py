from typing import Any, Dict, Tuple, List

# ----------------------------------------------------------------------------
# Базовые классы узлов AST (Abstract Syntax Tree)
# ----------------------------------------------------------------------------

class FormulaNode:
    """
    Абстрактный базовый класс для всех узлов AST.
    Каждый узел должен реализовать метод eval(context),
    возвращающий вычисленное значение узла.
    """
    def eval(self, context: Dict[str, Any]) -> Any:
        # При отсутствии переопределения вызываем ошибку.
        raise NotImplementedError("FormulaNode.eval must be implemented in subclasses")


class ConstantNode(FormulaNode):
    """
    Узел для хранения констант (чисел, строк и т.д.).
    """
    def __init__(self, value: Any):
        # Сохраняем значение константы
        self.value = value

    def eval(self, context: Dict[str, Any]) -> Any:
        # Всегда возвращаем первоначальное значение, контекст не используется
        return self.value


class CellNode(FormulaNode):
    """
    Узел для ссылки на ячейку.
    Хранит адрес ячейки и при Eval() вытаскивает из context.
    """
    def __init__(self, ref: str):
        # Сохраняем адрес ячейки, например "A1" или "Sheet1!B2"
        self.ref = ref

    def eval(self, context: Dict[str, Any]) -> Any:
        # Получаем значение ячейки из словаря context.
        # context.get(ref) возвращает None, если ключа нет,
        # что позволяет безопасно обрабатывать отсутствующие ячейки.
        return context.get(self.ref)


class FunctionNode(FormulaNode):
    """
    Узел для вызова Excel-функций.
    Хранит имя функции и список аргументов (дочерних узлов).
    """
    def __init__(self, name: str, args: List[FormulaNode]):
        # Имя функции, например 'SUM', 'IF'
        self.name = name
        # Список аргументов — других узлов AST
        self.args = args

    def eval(self, context: Dict[str, Any]) -> Any:
        # Сначала рекурсивно вычисляем все аргументы
        values = [arg.eval(context) for arg in self.args]
        # Затем вызываем соответствующую функцию из excel_funcs,
        # передавая распакованный список значений
        return excel_funcs[self.name](*values)


class BinaryOpNode(FormulaNode):
    """
    Узел для бинарных операций: +, -, *, /.
    Хранит оператор и два дочерних узла (левый и правый операнды).
    """
    def __init__(self, op: str, left: FormulaNode, right: FormulaNode):
        # Операция, например '+', '-', '*', '/'
        self.op = op
        # Левый и правый операнды (узлы)
        self.left = left
        self.right = right

    def eval(self, context: Dict[str, Any]) -> Any:
        # Сначала вычисляем левый и правый операнды
        l = self.left.eval(context)
        r = self.right.eval(context)
        # В зависимости от оператора применяем нужную арифметику
        if self.op == '+':
            return l + r
        if self.op == '-':
            return l - r
        if self.op == '*':
            return l * r
        if self.op == '/':
            return l / r
        # В случае неподдерживаемого оператора кидаем ошибку
        raise ValueError(f"Unsupported operator {self.op}")


# ----------------------------------------------------------------------------
# Словарь с базовыми функциями, имитирующими Excel-функции
# ----------------------------------------------------------------------------

def _ensure_sequence(values: Tuple[Any, ...]) -> Tuple[Any, ...]:
    """
    Если передали один аргумент-итерируемый (список/кортеж), возвращаем его,
    иначе возвращаем все аргументы как кортеж.
    Это позволяет поддерживать как вызов SUM(1,2,3), так и SUM([1,2,3]).
    """
    # Если ровно один аргумент и он список или кортеж — возвращаем его
    if len(values) == 1 and isinstance(values[0], (list, tuple)):
        return values[0]
    # Иначе возвращаем сам полученный кортеж
    return values

# Определяем функции, которые будут использоваться для вычисления
excel_funcs = {
    'SUM': lambda *values: sum(_ensure_sequence(values)),
    'AVERAGE': lambda *values: (
        # Среднее: сумма / количество, если не пусто, иначе 0
        (sum(_ensure_sequence(values)) / len(_ensure_sequence(values)))
        if _ensure_sequence(values) else 0
    ),
    'MIN': lambda *values: min(_ensure_sequence(values)),
    'MAX': lambda *values: max(_ensure_sequence(values)),
    'IF': lambda condition, true_value, false_value:
        # Условная функция: возвращаем true_value, если condition истинно, иначе false_value
        true_value if condition else false_value,
    # Можно добавить другие Excel-функции аналогичным образом
}


# ----------------------------------------------------------------------------
# Функции-утилиты для работы с AST
# ----------------------------------------------------------------------------

def evaluate_cell(cell: str, context: Dict[str, Any]) -> Any:
    """
    Получает значение ячейки из контекста.

    Parameters:
    - cell: строка-адрес ячейки (например, "A1" или "Sheet1!B2").
    - context: словарь, где ключи — адреса ячеек, а значения — их текущие значения.

    Возвращает: значение ячейки или None, если ключ не найден.
    """
    return context.get(cell)


def evaluate_ast(ast: Any, context: Dict[str, Any]) -> Any:
    """
    Рекурсивно вычисляет значения для AST (абстрактного синтаксического дерева).

    Logic:
    - Если ast — строка, считаем это ссылкой на ячейку: возвращаем evaluate_cell.
    - Если ast — кортеж, где первый элемент — имя функции из excel_funcs,
      вычисляем эту функцию.
    - Другие типы узлов можно добавить по мере расширения
    """

    # 0) Если нам попался уже готовый узел FormulaNode,
    #    просто делегируем ему вычисление
    if isinstance(ast, FormulaNode):
        return ast.eval(context)


    # 1) Листья-строки: ссылки на ячейки
    if isinstance(ast, str):
        return evaluate_cell(ast, context)

    # 2) Узлы-функции: ast = (name, [args...])
    if isinstance(ast, tuple) and ast[0] in excel_funcs:
        # Извлекаем имя функции
        func = excel_funcs[ast[0]]
        # Рекурсивно вычисляем все аргументы узла
        args = [evaluate_ast(arg, context) for arg in ast[1]]
        # Вызываем функцию с распакованными аргументами
        return func(*args)

    # Здесь можно добавить обработку узлов операций и других конструкций
    raise ValueError(f"Unsupported AST node: {ast}")
