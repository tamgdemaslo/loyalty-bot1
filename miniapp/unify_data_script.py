import pandas as pd
import re

# Читаем данные
df = pd.read_excel('/Users/ilaeliseenko/Downloads/товары унифицирировать.xlsx', sheet_name='Sheet0')

# Находим первую строку с данными
first_data_row = 541
data_df = df.iloc[first_data_row:].copy()
data_df.reset_index(drop=True, inplace=True)

# Функция для извлечения и унификации вязкости
def extract_viscosity(text):
    if not isinstance(text, str):
        return None
    # Ищем паттерны вязкости
    matches = re.findall(r'(\d+)[Ww][-\s]?(\d+)', text)
    if matches:
        return f"{matches[0][0]}W-{matches[0][1]}"
    return None

# Функция для извлечения и унификации объема
def extract_volume(text):
    if not isinstance(text, str):
        return None
    # Ищем паттерны объема
    matches = re.findall(r'(\d+)\s?[лL]\.?', text)
    if matches:
        return f"{matches[0]} л."
    return None

# Функция для извлечения бренда
def extract_brand(text):
    if not isinstance(text, str):
        return None
    # Ищем бренд после "моторное" или "трансмиссионное"
    brand_match = re.search(r'(?:моторное|трансмиссионное)\s+([А-Яа-яA-Za-z]+)', text)
    if brand_match:
        return brand_match.group(1)
    return None

# Функция для унификации вязкости в тексте
def unify_viscosity_in_text(text):
    if not isinstance(text, str):
        return text
    # Приводим к формату 'NW-XX'
    return re.sub(r'(\d+)[Ww][-\s]?(\d+)', r'\1W-\2', text)

# Функция для унификации объема в тексте
def unify_volume_in_text(text):
    if not isinstance(text, str):
        return text
    # Приводим к формату 'N л.'
    return re.sub(r'(\d+)\s?[лL]\.?', r'\1 л.', text)

# Унификация столбца с названиями
product_col = data_df.columns[4]
print(f"Унифицируем данные в столбце: {product_col}")
print(f"Количество записей: {len(data_df)}")

# Создаем новые столбцы для унифицированных значений
data_df['Унифицированная_вязкость'] = data_df[product_col].apply(extract_viscosity)
data_df['Унифицированный_объем'] = data_df[product_col].apply(extract_volume)
data_df['Бренд'] = data_df[product_col].apply(extract_brand)

# Унифицируем основной столбец с названиями
data_df[product_col] = data_df[product_col].apply(unify_viscosity_in_text)
data_df[product_col] = data_df[product_col].apply(unify_volume_in_text)

# Показываем статистику
print("\n--- Статистика унификации ---")
print(f"Найдено записей с вязкостью: {data_df['Унифицированная_вязкость'].notna().sum()}")
print(f"Найдено записей с объемом: {data_df['Унифицированный_объем'].notna().sum()}")
print(f"Найдено записей с брендом: {data_df['Бренд'].notna().sum()}")

# Показываем примеры унифицированных значений
print("\n--- Примеры унифицированных значений ---")
print("Вязкость:")
print(data_df['Унифицированная_вязкость'].dropna().unique()[:10])
print("\nОбъем:")
print(data_df['Унифицированный_объем'].dropna().unique()[:10])
print("\nБренды:")
print(data_df['Бренд'].dropna().unique()[:10])

# Сохраняем результат
output_file = '/Users/ilaeliseenko/Downloads/товары унифицированы.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    data_df.to_excel(writer, sheet_name='Унифицированные_данные', index=False)

print(f"\nУнифицированные данные сохранены в {output_file}")
print("Добавлены новые столбцы: 'Унифицированная_вязкость', 'Унифицированный_объем', 'Бренд'")
