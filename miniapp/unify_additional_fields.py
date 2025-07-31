import pandas as pd
import re

# Читаем данные
df = pd.read_excel('/Users/ilaeliseenko/Downloads/товары унифицирировать.xlsx', sheet_name='Sheet0')

# Находим первую строку с данными
first_data_row = 541
data_df = df.iloc[first_data_row:].copy()
data_df.reset_index(drop=True, inplace=True)

print(f"Обрабатываем {len(data_df)} записей")
print(f"Размер данных: {data_df.shape}")

# Определяем столбцы с дополнительными полями
sae_col = 'Доп. поле: SAE'  # столбец 49
acea_col = 'Доп. поле: ACEA (!)'  # столбец 58
brand_col = 'Доп. поле: Brand'  # столбец 55
volume_col = 'Доп. поле: Объем'  # столбец 53

print("\n--- Анализ исходных данных ---")
print(f"SAE - непустых записей: {data_df[sae_col].notna().sum()}")
print(f"ACEA - непустых записей: {data_df[acea_col].notna().sum()}")
print(f"Brand - непустых записей: {data_df[brand_col].notna().sum()}")
print(f"Объем - непустых записей: {data_df[volume_col].notna().sum()}")

# Функции для унификации

def unify_sae(value):
    """Унифицирует значения SAE к формату NW-XX"""
    if pd.isna(value) or value == '':
        return None
    
    value_str = str(value).strip()
    
    # Если значение содержит "Не подлежит", оставляем как есть
    if 'не подлежит' in value_str.lower():
        return value_str
    
    # Приводим к формату NW-XX
    # Ищем паттерны типа 5w-40, 5W40, 5w40
    match = re.search(r'(\d+)[Ww][-\s]?(\d+)', value_str)
    if match:
        return f"{match.group(1)}W-{match.group(2)}"
    
    return value_str

def unify_acea(value):
    """Унифицирует значения ACEA"""
    if pd.isna(value) or value == '':
        return None
    
    value_str = str(value).strip()
    
    # Приводим к верхнему регистру и стандартизируем разделители
    value_str = value_str.upper()
    
    # Заменяем различные разделители на запятую с пробелом
    value_str = re.sub(r'[,;]\s*', ', ', value_str)
    value_str = re.sub(r'\s+', ' ', value_str)
    
    return value_str

def unify_brand(value):
    """Унифицирует названия брендов"""
    if pd.isna(value) or value == '':
        return None
    
    value_str = str(value).strip()
    
    # Приводим первую букву к верхнему регистру
    return value_str.capitalize()

def unify_volume(value):
    """Унифицирует объем к формату N л."""
    if pd.isna(value) or value == '':
        return None
    
    value_str = str(value).strip()
    
    # Ищем числовое значение и приводим к формату "N л."
    match = re.search(r'(\d+(?:\.\d+)?)\s*[лL]', value_str)
    if match:
        number = match.group(1)
        # Убираем .0 если это целое число
        if number.endswith('.0'):
            number = number[:-2]
        return f"{number} л."
    
    return value_str

# Применяем унификацию
print("\n--- Применяем унификацию ---")

# Создаем унифицированные столбцы
data_df['SAE_унифицированное'] = data_df[sae_col].apply(unify_sae)
data_df['ACEA_унифицированное'] = data_df[acea_col].apply(unify_acea)
data_df['Brand_унифицированное'] = data_df[brand_col].apply(unify_brand)
data_df['Объем_унифицированный'] = data_df[volume_col].apply(unify_volume)

# Обновляем оригинальные столбцы
data_df[sae_col] = data_df['SAE_унифицированное']
data_df[acea_col] = data_df['ACEA_унифицированное']
data_df[brand_col] = data_df['Brand_унифицированное']
data_df[volume_col] = data_df['Объем_унифицированный']

# Статистика после унификации
print(f"SAE - записей после унификации: {data_df[sae_col].notna().sum()}")
print(f"ACEA - записей после унификации: {data_df[acea_col].notna().sum()}")
print(f"Brand - записей после унификации: {data_df[brand_col].notna().sum()}")
print(f"Объем - записей после унификации: {data_df[volume_col].notna().sum()}")

# Показываем примеры унифицированных значений
print("\n--- Примеры унифицированных значений ---")

print("SAE:")
sae_values = data_df[sae_col].dropna().unique()
print(f"  Уникальных значений: {len(sae_values)}")
print(f"  Примеры: {list(sae_values)}")

print("\nACEA:")
acea_values = data_df[acea_col].dropna().unique()
print(f"  Уникальных значений: {len(acea_values)}")
print(f"  Примеры: {list(acea_values)}")

print("\nBrand:")
brand_values = data_df[brand_col].dropna().unique()
print(f"  Уникальных значений: {len(brand_values)}")
print(f"  Примеры: {list(brand_values)}")

print("\nОбъем:")
volume_values = data_df[volume_col].dropna().unique()
print(f"  Уникальных значений: {len(volume_values)}")
print(f"  Примеры: {list(volume_values)}")

# Показываем примеры изменений
print("\n--- Примеры изменений ---")
for i in range(min(10, len(data_df))):
    row = data_df.iloc[i]
    if pd.notna(row[sae_col]) or pd.notna(row[acea_col]) or pd.notna(row[brand_col]) or pd.notna(row[volume_col]):
        print(f"\nТовар {i+1}: {row['Наименование']}")
        if pd.notna(row[sae_col]):
            print(f"  SAE: {row[sae_col]}")
        if pd.notna(row[acea_col]):
            print(f"  ACEA: {row[acea_col]}")
        if pd.notna(row[brand_col]):
            print(f"  Brand: {row[brand_col]}")
        if pd.notna(row[volume_col]):
            print(f"  Объем: {row[volume_col]}")

# Сохраняем результат
output_file = '/Users/ilaeliseenko/Downloads/товары_доп_поля_унифицированы.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    data_df.to_excel(writer, sheet_name='Унифицированные_поля', index=False)

print(f"\n✅ Унифицированные данные сохранены в: {output_file}")
print("🔧 Унифицированы поля: SAE, ACEA, Brand, Объем")
print("📊 Все значения приведены к единому формату")
