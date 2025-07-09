# tests/test_loader.py

import pytest 
from itertools import islice
import random
from src.loader import read_excel_file, split_into_constants_and_formulas

@pytest.fixture(scope="session")
def raw_sheets():
    """
    Читаем Excel-файл один раз, возвращаем "сырые" данные:
        {sheet_name: {'values': [...], 'formulas': [...]} }
    """
    # Загружаем данные с помощью функции read_excel_file
    raw = read_excel_file('Экономика поставок.xlsx')
    print(f"[test_loader] Загружены сырые листы: {list(raw.keys())}")
    print()
    return raw # Возвращаем загруженные данные для использования в других тестах


# Фикстура для разбивки сырых данных на структуру all_sheets
@pytest.fixture(scope="session")
def sheets(raw_sheets):
    """
    Разбиваем сырые данные на структуру all_sheets:
        { sheet_name: {data, constants, formulas, calculated} }
    """
    # Используем split_into_constants_and_formulas для преобразования сырых данных в нужную структуру
    shts = split_into_constants_and_formulas(raw_sheets)
    print(f"[test_loader] После split: листы в all_sheets: {list(shts.keys())}")
    print()
    return shts # Возвращаем данные в структуре all_sheets для использования в тестах

def test_all_sheets_present(raw_sheets, sheets):
    """
    Убедимся, что после split_into_constants_and_formulas
    у нас в sheets остались ровно те же имена листов, что и в raw_sheets.
    """

    # Сравниваем имена листов из сырых данных с именами листов в all_sheets
    expected = set(raw_sheets.keys())
    actual   = set(sheets.keys())
    print(f"[test_loader] expected sheets: {expected}")
    print(f"[test_loader] actual   sheets: {actual}")
    print()

    missing = expected - actual # Листы, которые отсутствуют
    extra   = actual - expected # Листы, которых не должно быть

    # Проверяем, что все листы из raw_sheets присутствуют в sheets
    assert actual == expected, (
        f"Несовпадение имён листов:\n"
        f"  Отсутствуют: {missing}\n"
        f"  Лишние:     {extra}"
    )

def test_structure_for_each_sheet(sheets):
    """
    Для каждого листа проверяем наличие разделов 'data', 'constants', 'formulas', 'calculated'
    и корректность вложенных ключей:
      - data = константы ∪ формулы
      - calculated ⊆ formulas
    """
    # Проходим по каждому листу в sheets
    for name, content in sheets.items():
        print(f"\n[test_loader] Проверяем лист: {name}")
        # У всех листов должны быть ровно эти четыре раздела
        keys = set(content.keys())
        print(f"[test_loader] Разделы на листе '{name}': {keys}")


        # Проверяем, что все четыре раздела присутствуют на каждом листе
        assert keys == {'data', 'constants', 'formulas', 'calculated'}, (
            f"На листе {name} неверная структура: {keys}"
        )


        # Разбиваем ключи на соответствующие категории
        data_keys  = set(content['data'].keys())
        const_keys = set(content['constants'].keys())
        form_keys  = set(content['formulas'].keys())
        calc_keys  = set(content['calculated'].keys())


        # Логируем количество ячеек в каждом разделе
        print(f"[test_loader]  data      ({len(data_keys)} ячеек)")
        print(f"[test_loader]  constants ({len(const_keys)} ячеек)")
        print(f"[test_loader]  formulas  ({len(form_keys)} ячеек)")
        print(f"[test_loader]  calculated({len(calc_keys)} ячеек)")


        # Проверяем, что data — это объединение констант и формул
        assert data_keys == const_keys | form_keys, (
            f"На листе {name}: data != constants ∪ formulas\n"
            f"  data_keys  = {data_keys}\n"
            f"  const_keys = {const_keys}\n"
            f"  form_keys  = {form_keys}"
        )

        # Проверяем, что calculated — подмножество formulas
        assert calc_keys <= form_keys, (
            f"На листе {name}: calculated встречаются не в формулах:\n"
            f"  calculated_keys = {calc_keys}\n"
            f"  формулы_keys    = {form_keys}"
        )

def test_samples_for_Вход(sheets):
    """
    Выводим несколько примеров по листу 'Вход' для ручной проверки, без подробных ассертов.
    """
    name = 'Вход'
    assert name in sheets, f"Лист {name} отсутствует"
    content = sheets[name]

    # Функция для выборки n случайных ключей с непустыми значениями
    def sample_keys(d, n=3):
        keys = [k for k, v in d.items() if v is not None]
        return random.sample(keys, min(n, len(keys)))

    print(f"\n[test_loader] Случайные примеры данных на листе '{name}':")

    # Выбираем случайные примеры из разделов 'data' и 'constants'
    for section in ('data', 'constants'):
        keys = sample_keys(content[section], 3) # Берём случайные 3 ключа
        print(f"  {section}:")
        for key in keys:
            print(f"    {key}: {content[section][key]!r}") # Выводим ключи и их значения

    # Для formulas и calculated используем один и тот же набор адресов
    formula_keys = sample_keys(content['formulas'], 3) # Берём случайные 3 ключа из формул
    print(f"\n[test_loader] Примеры формул и их вычислений на листе '{name}':")
    for key in formula_keys:
        formula = content['formulas'].get(key) # Получаем формулу
        calc = content['calculated'].get(key) # Получаем вычисленное значение
        print(f"  {key} -> formula: {formula!r}, calculated: {calc!r}") # Выводим формулу и её вычисление