# main.py

from src.loader import read_excel_file, split_into_constants_and_formulas

def main():
    # Убедитесь, что test.xlsx лежит в корне проекта или укажите полный путь
    raw = read_excel_file('C:/Users/pc/practicum/marketplace_analytics/Экономика поставок.xlsx')
    sheets = split_into_constants_and_formulas(raw)
    print("Листы:", sheets.keys())
    print("Константы Вход:", sheets['Вход']['constants'])

if __name__ == "__main__":
    main()
