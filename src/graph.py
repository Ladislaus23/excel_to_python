#src/graph.py

from collections import defaultdict, deque
from src.parser import extract_cell_references
from collections import deque

def build_dependency_graph(all_sheets: dict):
    """
    Строит граф зависимостей между ячейками:
    - вершины: 'Sheet!A1'
    - ребро из X в Y, если Y зависит от X.
    Возвращает graph и словарь in_degree (входные степени).
    """
    graph = defaultdict(list)  # Словарь, где для каждой ячейки мы храним список её зависимостей
    in_degree = defaultdict(int)  # Словарь для учёта входных степеней каждой ячейки

    # Шаг 1: Инициализация графа для всех ячеек
    # Для каждой ячейки в данных (data) и формулах создаем записи в graph и in_degree
    for sheet, content in all_sheets.items():
        for addr in content['data'].keys():  # Для каждой ячейки с данными
            node = f"{sheet}!{addr}"
            graph[node]    # Гарантируем, что ячейка существует в графе
            in_degree[node]  # Инициализируем входную степень для ячейки (пока 0)

    # Шаг 2: Обработка формул и добавление зависимостей
    # Для каждой формулы находим ячейки, от которых она зависит
    for sheet, content in all_sheets.items():
        for addr, formula in content['formulas'].items():
            node = f"{sheet}!{addr}"
            deps = extract_cell_references(formula, all_sheets)  # Извлекаем зависимости для данной формулы
            for dep in deps:
                if '!' in dep:
                    dep_node = dep  # Межлистовая зависимость
                else:
                    dep_node = f"{sheet}!{dep}"  # Локальная зависимость в текущем листе
                graph[node].append(dep_node)  # Добавляем зависимость dep_node -> node
                in_degree[node] += 1  # Увеличиваем входную степень для node

    # Шаг 3: Обработка ячеек, которые не имеют зависимостей
    # Если ячейка не имеет зависимостей, то её входная степень остаётся равной 0
    for sheet, content in all_sheets.items():
        for addr in content['data'].keys():
            node = f"{sheet}!{addr}"
            if node not in in_degree:
                in_degree[node] = 0  # Если нет зависимостей, входная степень остаётся 0

    return graph, in_degree




def has_cycle(graph: dict) -> bool:
    """
    Проверяет граф на наличие цикла (DFS).
    Возвращает True, если цикл найден.
    """
    visited = {node: 0 for node in graph}  # 0=не посещено, 1=в процессе, 2=завершено

    def dfs(u):
        if visited[u] == 1:
            return True  # Цикл найден, так как мы встретили вершину, которую уже обрабатываем
        if visited[u] == 2:
            return False  # Вершина уже обработана, цикла нет
        visited[u] = 1  # Отметим вершину как "в процессе обработки"
        for v in graph[u]:
            if dfs(v):
                return True  # Если цикл найден, возвращаем True
        visited[u] = 2  # Завершаем обработку вершины
        return False

    # Применяем DFS ко всем вершинам, чтобы проверить наличие цикла
    return any(dfs(node) for node in graph if visited[node] == 0)



def topological_sort_kahn(graph: dict, in_degree: dict) -> list:
    """
    Топологическая сортировка по алгоритму Кана.
    Возвращает упорядоченный список вершин.
    В начале проверяется, есть ли цикл в графе.
    Если цикл найден, выбрасывается исключение.
    """
    # Проверяем наличие цикла перед началом сортировки
    if has_cycle(graph):
        raise ValueError("Граф содержит цикл — топологическая сортировка невозможна")

    # Основной алгоритм Кана для топологической сортировки
    queue = deque([n for n, deg in in_degree.items() if deg == 0]) # Инициализируем очередь с вершинами с нулевой степенью
    topo = [] # Список для хранения топологически отсортированных вершин

    while queue:
        u = queue.popleft() # Извлекаем вершину из очереди
        topo.append(u) # Добавляем вершину в результат
        
        result = []  # Список для хранения ячеек, которые зависят от u
        for key, dependencies in graph.items():
            if u in dependencies:  # Если u есть в списке зависимостей для этой ячейки
                result.append(key)  # Добавляем текущий ключ (ячейку) в результат

        for v in result:
            in_degree[v] -= 1 # Уменьшаем входную степень для вершины v
            if in_degree[v] == 0: # Если входная степень стала 0, добавляем её в очередь
                queue.append(v)

    return topo

