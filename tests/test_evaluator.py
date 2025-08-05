import pytest
from src.evaluator import (
    ConstantNode,
    CellNode,
    FunctionNode,
    BinaryOpNode,
    excel_funcs
)

def test_constant_node():
    """
    Проверяем, что ConstantNode просто хранит и возвращает своё значение,
    независимо от контекста.
    """
    # Создаём узел-константу со значением 42
    node = ConstantNode(42)
    # eval() должен вернуть то же самое число
    assert node.eval({}) == 42

def test_cell_node_existing():
    """
    Проверяем, что CellNode берёт значение из переданного словаря context
    по ключу-адресу ячейки.
    """
    # Контекст, где по адресу 'A1' лежит число 10
    ctx = {'A1': 10}
    node = CellNode('A1')
    # eval() вернёт 10 из контекста
    assert node.eval(ctx) == 10

def test_cell_node_missing():
    """
    Проверяем, что CellNode при отсутствии ключа в context
    по умолчанию возвращает None (текущая реализация).
    """
    node = CellNode('B2')
    # В пустом словаре нет ключа 'B2', значит eval() должен вернуть None
    assert node.eval({}) is None

def test_binary_op_node_add():
    """
    Проверяем бинарную операцию сложения через BinaryOpNode.
    Левая и правая части — это ссылки на ячейки, извлекаемые из context.
    """
    ctx = {'A1': 2, 'B1': 3}
    # Создаём узел A1 + B1
    node = BinaryOpNode('+', CellNode('A1'), CellNode('B1'))
    # Должно получиться 2 + 3 = 5
    assert node.eval(ctx) == 5

def test_binary_op_node_all_ops():
    """
    Проверяем все четыре арифметических оператора BinaryOpNode:
    вычитание, умножение и деление; для простоты используем константы.
    """
    left  = ConstantNode(6)
    right = ConstantNode(2)

    # 6 - 2 = 4
    assert BinaryOpNode('-', left, right).eval({}) == 4
    # 6 * 2 = 12
    assert BinaryOpNode('*', left, right).eval({}) == 12
    # 6 / 2 = 3
    assert BinaryOpNode('/', left, right).eval({}) == 3

def test_function_node_sum():
    """
    Проверяем работу FunctionNode для функции SUM:
    передаём список констант, внутри вызывается excel_funcs['SUM'].
    """
    # Создаём узлы для значений 1, 2 и 3
    args = [ConstantNode(1), ConstantNode(2), ConstantNode(3)]
    node = FunctionNode('SUM', args)
    # eval() должен вернуть сумму списка [1,2,3], т.е. 6
    expected = excel_funcs['SUM']([1, 2, 3])
    assert node.eval({}) == expected

def test_function_node_if():
    """
    Проверяем работу условной функции IF:
    если первое значение True — возвращаем второй аргумент,
    иначе — третий.
    """
    # Случай, когда условие истинно
    node_true = FunctionNode('IF', [
        ConstantNode(True),    # условие
        ConstantNode('yes'),   # если True
        ConstantNode('no')     # если False
    ])
    assert node_true.eval({}) == 'yes'

    # Случай, когда условие ложно
    node_false = FunctionNode('IF', [
        ConstantNode(False),
        ConstantNode('yes'),
        ConstantNode('no')
    ])
    assert node_false.eval({}) == 'no'
