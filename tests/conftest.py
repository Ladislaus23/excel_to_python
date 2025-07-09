# tests/conftest.py

import os
import sys

# Вставляем корень проекта (один уровень выше tests/) в начало sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from src.loader import read_excel_file, split_into_constants_and_formulas

@pytest.fixture(scope="session")
def sheets():
    # 1) читаем реально существующие листы
    raw = read_excel_file('Экономика поставок.xlsx')
    shts = split_into_constants_and_formulas(raw)

    # 2) добавляем пустые «тестовые» листы, чтобы парсер видел их префиксы
    for fake in ('Sheet1', 'Лист2'):
        if fake not in shts:
            shts[fake] = {
                'data': {},
                'constants': {},
                'formulas': {},
                'calculated': {},
            }

    return shts
