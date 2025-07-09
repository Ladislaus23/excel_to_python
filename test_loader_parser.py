# test_loader_parser.py

from src.loader import read_excel_file, split_into_constants_and_formulas
from src.parser import extract_cell_references

def main():
    # 1) Загрузка «сырых» данных
    raw = read_excel_file('Экономика поставок.xlsx')
    print("Загруженные листы:", raw.keys())

    # 2) Разбивка на константы/формулы
    sheets = split_into_constants_and_formulas(raw)
    вход = sheets.get('Вход')
    if not вход:
        raise KeyError("Лист 'Вход' не найден!")

    # 3) Посмотрим, сколько у нас констант и формул
    print(f"На листе 'Вход' найдено {len(вход['constants'])} констант и {len(вход['formulas'])} формул.")

    # 4) Выведем пару примеров
    for addr, formula in list(вход['formulas'].items())[:5]:
        refs = extract_cell_references(formula, sheets)
        print(f"{addr}: {formula} -> ссылки: {refs}")

if __name__ == "__main__":
    main()
