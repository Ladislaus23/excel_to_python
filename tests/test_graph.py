import pytest
from src.graph import build_dependency_graph, has_cycle, topological_sort_kahn


# ТЕСТИРУЕМ ФУНКЦИЮ, СТРОЯЩУЮ ГРАФ ЗАВИСИМОСТЕЙ


@pytest.fixture
def test_data():
    """
    Фикстура для создания тестовых данных. Эта фикстура будет возвращать
    структуру данных, которая имитирует два листа с формулами в Excel.
    """
    all_sheets = {
        'Sheet1': {
            'data': {
                'A1': 10,  # Ячейка с числовым значением
                'B1': 20,  # Ячейка с числовым значением
                'C1': None  # Ячейка с формулой (предположим, что она должна быть в data тоже)
            },
            'formulas': {
                'C1': '=A1 + B1'  # Ячейка с формулой
            }
        }
    }
    return all_sheets


def test_build_dependency_graph_simple(test_data):
    """
    Тест для проверки правильности построения графа зависимостей для простого случая.
    Мы проверяем, что для простых зависимостей граф построен правильно.
    """
    # Строим граф зависимостей
    graph, indeg = build_dependency_graph(test_data)

    # Ожидаемый граф зависимостей:
    expected_graph = {
        'Sheet1!A1': [],  # A1 не зависит от других
        'Sheet1!B1': [],  # B1 не зависит от других
        'Sheet1!C1': ['Sheet1!A1', 'Sheet1!B1']  # C1 зависит от A1 и B1
    }

    # Проверяем, что граф соответствует ожиданиям (игнорируем порядок зависимостей)
    for node in expected_graph:
        assert set(graph[node]) == set(expected_graph[node]), f"Expected {expected_graph[node]}, but got {graph[node]}"

    # Проверка на входные степени:
    # C1 зависит от двух ячеек (A1 и B1), у неё степень входа 2
    expected_indegree = {'Sheet1!A1': 0, 'Sheet1!B1': 0, 'Sheet1!C1': 2}
    assert indeg == expected_indegree, f"Expected {expected_indegree}, but got {indeg}"


def test_build_dependency_graph_multiple_independent_components():
    """
    Тест для проверки графа с несколькими независимыми компонентами.
    Мы создаём случай, когда ячейки не зависят друг от друга.
    """
    all_sheets = {
        'Sheet1': {
            'data': {
                'A1': 10,
                'B1': 20,
                'C1': '=A1 + B1',  # Формула в data тоже
                'D1': 40,
                'E1': '=A1 + B1',
                'F1': '=C1 + D1'
            },
            'formulas': {
                'C1': '=A1 + B1',  # Формула для C1
                'E1': '=A1 + B1',
                'F1': '=C1 + D1'
            }
        }
    }

    # Ожидаемый граф зависимостей:
    expected_graph = {
        'Sheet1!A1': [],  # A1 не зависит от других
        'Sheet1!B1': [],  # B1 не зависит от других
        'Sheet1!C1': ['Sheet1!A1', 'Sheet1!B1'],  # C1 зависит от A1 и B1
        'Sheet1!D1': [],  # D1 не зависит от других
        'Sheet1!E1': ['Sheet1!A1', 'Sheet1!B1'],  # E1 зависит от A1 и B1
        'Sheet1!F1': ['Sheet1!C1', 'Sheet1!D1']   # F1 зависит от C1 и D1
    }

    graph, indeg = build_dependency_graph(all_sheets)
    
    # Проверяем, что граф соответствует ожиданиям (игнорируем порядок зависимостей)
    for node in expected_graph:
        assert set(graph[node]) == set(expected_graph[node]), f"Expected {expected_graph[node]}, but got {graph[node]}"

    # Проверка на входные степени:
    expected_indegree = {
        'Sheet1!A1': 0,  # A1 не зависит от других
        'Sheet1!B1': 0,  # B1 не зависит от других
        'Sheet1!C1': 2,  # C1 зависит от A1 и B1
        'Sheet1!D1': 0,  # D1 не зависит от других
        'Sheet1!E1': 2,  # E1 зависит от A1 и B1
        'Sheet1!F1': 2   # F1 зависит от C1 и D1
    }

    assert indeg == expected_indegree, f"Expected {expected_indegree}, but got {indeg}"


def test_build_dependency_graph_multiple_levels_of_dependencies():
    """
    Тест для проверки графа с несколькими уровнями зависимостей.
    Здесь ячейки зависят друг от друга через несколько уровней.
    """
    all_sheets = {
        'Sheet1': {
            'data': {
                'A1': 10,
                'B1': 20,
                'C1': '=A1 + B1',  # Формула в data
                'D1': '=C1 + 5'    # Формула в data
            },
            'formulas': {
                'C1': '=A1 + B1',  # Формула для C1
                'D1': '=C1 + 5'    # Формула для D1
            }
        }
    }

    # Ожидаемый граф зависимостей:
    expected_graph = {
        'Sheet1!A1': [],  # A1 не зависит от других
        'Sheet1!B1': [],  # B1 не зависит от других
        'Sheet1!C1': ['Sheet1!A1', 'Sheet1!B1'],  # C1 зависит от A1 и B1
        'Sheet1!D1': ['Sheet1!C1']  # D1 зависит от C1
    }

    graph, indeg = build_dependency_graph(all_sheets)

    # Проверяем, что граф соответствует ожиданиям (игнорируем порядок зависимостей)
    for node in expected_graph:
        assert set(graph[node]) == set(expected_graph[node]), f"Expected {expected_graph[node]}, but got {graph[node]}"

    # Проверка на входные степени:
    expected_indegree = {
        'Sheet1!A1': 0,  # A1 не зависит от других
        'Sheet1!B1': 0,  # B1 не зависит от других
        'Sheet1!C1': 2,  # C1 зависит от A1 и B1
        'Sheet1!D1': 1   # D1 зависит от C1
    }

    assert indeg == expected_indegree, f"Expected {expected_indegree}, but got {indeg}"


def test_build_dependency_graph__cycle_in_graph():
    """
    Тест на граф с циклической зависимостью.
    В этом тесте мы проверяем, что циклические зависимости правильно обрабатываются.
    """
    all_sheets = {
        'Sheet1': {
            'data': {
                'A1': '=C1',  # Формула с циклической зависимостью
                'B1': 20,      # Числовое значение
                'C1': '=A1 + B1'
            },
            'formulas': {
                'C1': '=A1 + B1',
                'A1': '=C1'  # Циклическая зависимость
            }
        }
    }

    # Ожидаемый граф для теста
    expected_graph = {
        'Sheet1!A1': ['Sheet1!C1'],  # A1 зависит от C1
        'Sheet1!B1': [],              # B1 не зависит от других ячеек
        'Sheet1!C1': ['Sheet1!A1', 'Sheet1!B1']   # C1 зависит от A1
    }

    # Строим граф зависимостей
    graph, indeg = build_dependency_graph(all_sheets)

    # Проверяем, что построенный граф соответствует ожидаемому
    for node in expected_graph:
        assert set(graph[node]) == set(expected_graph[node]), f"Expected {expected_graph[node]}, but got {graph[node]}"

    # Проверка на входные степени:
    expected_indegree = {
        'Sheet1!A1': 1,  # A1 зависит от C1
        'Sheet1!B1': 0,              # B1 не зависит от других ячеек
        'Sheet1!C1': 2   # C1 зависит от A1
    }

    assert indeg == expected_indegree, f"Expected {expected_indegree}, but got {indeg}"


def test_build_dependency_graph_no_dependencies():
    all_sheets = {
        'Sheet1': {
            'data': {
                'A1': 10,
                'B1': 20
            },
            'formulas': {
            }
        }
    }

    expected_graph = {
        'Sheet1!A1': [],
        'Sheet1!B1': []
    }

    graph, indeg = build_dependency_graph(all_sheets)

    for node in expected_graph:
        assert set(graph[node]) == set(expected_graph[node]), f"Expected {expected_graph[node]}, but got {graph[node]}"

    # Проверка на входные степени (если необходимо)
    expected_indegree = {
        'Sheet1!A1': 0,
        'Sheet1!B1': 0
    }

    assert indeg == expected_indegree, f"Expected {expected_indegree}, but got {indeg}"



#ТЕСТИТРУЕМ ФУНКЦИЮ, ОБНАРУЖИВАЮЩУЮ ЦИКЛЫ


def test_has_cycle_no_cycle_simple():
    """
    Тест для проверки графа без цикла.
    Мы проверяем, что функция правильно обрабатывает граф без циклических зависимостей.
    """
    graph = {
        'A': ['B'],
        'B': ['C'],
        'C': []
    }
    assert has_cycle(graph) is False, "Ожидали, что граф не будет содержать цикл"


def test_has_cycle_single():
    """
    Тест для графа с одним циклом.
    Мы проверяем, что функция правильно обрабатывает граф с циклической зависимостью.
    """
    graph = {
        'A': ['B'],
        'B': ['C'],
        'C': ['A']
    }
    assert has_cycle(graph) is True, "Ожидали, что граф будет содержать цикл"


def test_has_cycle_multiple():
    """
    Тест для графа с несколькими циклами.
    Мы проверяем, что функция правильно обрабатывает граф с несколькими циклами.
    """
    graph = {
        'A': ['B'],
        'B': ['C'],
        'C': ['A'],
        'D': ['E'],
        'E': ['D']
    }
    assert has_cycle(graph) is True, "Ожидали, что граф будет содержать цикл"


def test_has_cycle_no_cycle_multiple_components():
    """
    Тест для графа с несколькими независимыми компонентами без цикла.
    Мы проверяем, что функция правильно обрабатывает граф без циклов в независимых компонентах.
    """
    graph = {
        'A': ['B'],
        'B': [],
        'C': ['D'],
        'D': []
    }
    assert has_cycle(graph) is False, "Ожидали, что граф не будет содержать цикл"


def test_has_cycle_single_node_no_edges():
    """
    Тест для графа с одной вершиной без рёбер.
    Мы проверяем, что граф с одной вершиной не содержит цикл.
    """
    graph = {
        'A': []
    }
    assert has_cycle(graph) is False, "Ожидали, что граф не будет содержать цикл"


def test_has_cycle_empty_graph():
    """
    Тест для пустого графа.
    Мы проверяем, что пустой граф не содержит цикл.
    """
    graph = {}
    assert has_cycle(graph) is False, "Ожидали, что пустой граф не будет содержать цикл"


def test_has_cycle_cycle_in_component():
    """
    Тест для графа с циклом в одной компоненте.
    Мы проверяем, что функция правильно обрабатывает цикл в одной из компонент.
    """
    graph = {
        'A': ['B'],
        'B': ['C'],
        'C': ['A'],  # Цикл
        'D': ['E'],
        'E': []      # Без цикла
    }
    assert has_cycle(graph) is True, "Ожидали, что граф будет содержать цикл"


# ДАЛЕЕ ТЕСТИРУЕМ АЛГОРИТМ ТОПОЛОГИЧЕСКОЙ СОРТИРОВКИ

# Фикстура для простого графа A -> B -> C
@pytest.fixture
def simple_graph():
    graph = {'A': ['B'], 'B': ['C'], 'C': []}
    indeg = {'A': 1, 'B': 1, 'C': 0}
    return graph, indeg


# Тест на топологическую сортировку для простого графа
def test_topological_sort_kahn_simple(simple_graph):
    """
    Тест для простой топологической сортировки. Проверяем, что простые зависимости корректно сортируются.
    """
    graph, indeg = simple_graph
    order = topological_sort_kahn(graph, indeg)
    expected_order = ['C', 'B', 'A']
    assert order == ['C', 'B', 'A'], f"Expected {expected_order}, but got {order}"


# Тест на топологическую сортировку для более сложного графа с независимыми компонентами
def test_topological_sort_kahn_multiple_paths():
    """
    Тест для проверки топологической сортировки с несколькими путями. Мы проверяем, что алгоритм корректно сортирует независимые компоненты.
    """
    graph = {'A': ['B'], 'C': ['D'], 'B': [], 'D': []}
    indeg = {'A': 1, 'B': 0, 'C': 1, 'D': 0}
    order = topological_sort_kahn(graph, indeg)
    expected_orders = [
        ['B', 'D', 'A', 'C'],
        ['B', 'D', 'C', 'A'],
        ['D', 'B', 'A', 'C'],
        ['D', 'B', 'C', 'A']
    ]
    assert order in expected_orders, f"Expected {expected_orders}, but got {order}"


# Тест на топологическую сортировку в графе с независимыми компонентами и циклами
def test_topological_sort_kahn_with_cycle():
    """
    Тест на граф с циклической зависимостью. Мы проверяем, что цикл в графе вызывает исключение при попытке сортировать.
    """
    graph = {'A': ['B'], 'B': ['C'], 'C': ['A'], 'D': ['E'], 'E': []}
    indeg = {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 0}
    try:
        topological_sort_kahn(graph, indeg)
        assert False, "Ожидалась ошибка, но топологическая сортировка прошла"
    except ValueError:
        pass  # Ожидаем исключение, так как граф содержит цикл


# Тест на пустой граф
def test_topological_sort_kahn_empty_graph():
    """
    Тест для пустого графа. Мы проверяем, что топологическая сортировка для пустого графа возвращает пустой список.
    """
    graph = {}
    indeg = {}
    order = topological_sort_kahn(graph, indeg)
    assert order == [], "Топологическая сортировка для пустого графа должна вернуть пустой список"


# Тест на граф с одной вершиной и без рёбер
def test_topological_sort_kahn_single_node_graph():
    """
    Тест для графа с одной вершиной. Проверяем, что сортировка для такого графа вернёт правильный порядок.
    """
    graph = {'A': []}
    indeg = {'A': 0}
    order = topological_sort_kahn(graph, indeg)
    assert order == ['A'], "Граф с одной вершиной должен вернуть её в качестве результата"


# Тест на корректную работу с циклом и независимыми компонентами
def test_cycle_with_independent_component():
    """
    Тест на граф с циклом и независимыми компонентами. Мы проверяем, что алгоритм корректно обработает такие случаи.
    """
    graph = {'A': ['B'], 'B': ['C'], 'C': ['A'], 'D': ['E'], 'E': []}
    indeg = {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 0}
    try:
        topological_sort_kahn(graph, indeg)
        assert False, "Ожидалась ошибка, но топологическая сортировка прошла"
    except ValueError:
        pass  # Ожидаем исключение, так как граф содержит цикл


def test_topological_sort_kahn_three_independent_components():
    """
    Тест на граф с тремя независимыми компонентами. Мы проверяем, что сортировка работает правильно для такого графа.
    """
    graph = {
        'A1': ['B1'],   # A1 зависит от B1
        'B1': ['C1'],   # B1 зависит от C1
        'C1': [],       # C1 не зависит от других
        'D1': ['E1'],   # D1 зависит от E1
        'E1': [],       # E1 не зависит от других
        'F1': []        # F1 не зависит от других
    }

    indeg = {
        'A1': 1,  
        'B1': 1,  
        'C1': 0,  
        'D1': 1,  
        'E1': 0,  
        'F1': 0   
    }

    expected_orders = [
        ['C1', 'E1', 'F1', 'B1', 'A1', 'D1'],
        ['C1', 'E1', 'F1', 'D1', 'B1', 'A1'],
        ['C1', 'E1', 'F1', 'B1', 'D1', 'A1'],
        ['C1', 'F1', 'E1', 'B1', 'A1', 'D1'],
        ['C1', 'F1', 'E1', 'D1', 'B1', 'A1'],
        ['C1', 'F1', 'E1', 'B1', 'D1', 'A1'],
        ['F1', 'C1', 'E1', 'B1', 'A1', 'D1'],
        ['F1', 'C1', 'E1', 'D1', 'B1', 'A1'],
        ['F1', 'C1', 'E1', 'B1', 'D1', 'A1'],
        ['E1', 'C1', 'F1', 'B1', 'A1', 'D1'],
        ['E1', 'C1', 'F1', 'D1', 'B1', 'A1'],
        ['E1', 'C1', 'F1', 'B1', 'D1', 'A1']
    ]

    order = topological_sort_kahn(graph, indeg)
    assert order in expected_orders, f"Expected {expected_orders}, but got {order}"
