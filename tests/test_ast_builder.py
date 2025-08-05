import pytest
from src.ast_builder import parse_formula
from src.evaluator import evaluate_ast

@pytest.mark.parametrize("formula, context, expected", [
    # Простая арифметика
    ("=1+2", {}, 3),
    ("=5-3", {}, 2),
    ("=4*2", {}, 8),
    ("=8/2", {}, 4),

    # Скобки и приоритеты
    ("=1+2*3", {}, 7),
    ("=(1+2)*3", {}, 9),

    # Константы и ссылки на ячейки
    ("=A1+3", {"A1": 4}, 7),
    ("=A1+B1", {"A1": 2, "B1": 5}, 7),

    # Функции SUM и IF
    ("=SUM(1,2,3)", {}, 6),
    ("=SUM(A1,B1)", {"A1": 1, "B1": 2}, 3),
    ("=IF(A1>0, 10, 20)", {"A1": 5}, 10),
    ("=IF(A1>0, 10, 20)", {"A1": -1}, 20),

    # Межлистовые ссылки
    ("=Sheet1!A1+Sheet2!B2", {"Sheet1!A1": 3, "Sheet2!B2": 4}, 7),
])
def test_parse_and_evaluate(formula, context, expected):
    node = parse_formula(formula)
    # Проверяем, что вернулся корневой узел AST
    from src.evaluator import FormulaNode
    assert isinstance(node, FormulaNode)

    result = evaluate_ast(node, context)
    assert result == expected

def test_invalid_syntax_raises():
    with pytest.raises(Exception):
        parse_formula("=1++2")  # синтаксическая ошибка

