#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import re
import numpy as np
from typing import Optional

def normalize_volume(volume: str) -> str:
    """
    Нормализует объем в формат 'N л'
    """
    if pd.isna(volume) or volume == '':
        return ''
    
    volume_str = str(volume).strip()
    
    # Удаляем лишние пробелы и заменяем запятые на точки
    volume_str = re.sub(r'\s+', ' ', volume_str).replace(',', '.')
    
    # Извлекаем числовое значение
    match = re.search(r'(\d+(?:\.\d+)?)', volume_str)
    if match:
        num = match.group(1)
        return f"{num} л"
    
    return volume_str

def normalize_viscosity(viscosity: str) -> str:
    """
    Нормализует вязкость в формат 'NW-NN'
    """
    if pd.isna(viscosity) or viscosity == '':
        return ''
    
    viscosity_str = str(viscosity).strip()
    
    # Специальные случаи
    if 'не подлежит классификации' in viscosity_str.lower():
        return 'Не подлежит классификации по SAE'
    
    # Извлекаем числовые значения для вязкости
    # Паттерн для формата типа 0W-20, 5W-30, 10W-40, 75W-90
    pattern = r'(\d+)w[-\s]?(\d+)'
    match = re.search(pattern, viscosity_str, re.IGNORECASE)
    
    if match:
        first_num = match.group(1)
        second_num = match.group(2)
        return f"{first_num}W-{second_num}"
    
    return viscosity_str

def normalize_brand(brand: str) -> str:
    """
    Нормализует название бренда
    """
    if pd.isna(brand) or brand == '':
        return ''
    
    brand_str = str(brand).strip()
    
    # Словарь для нормализации брендов
    brand_mapping = {
        # Liqui Moly
        'liqui moly': 'Liqui Moly',
        'liqyi moly': 'Liqui Moly',
        'liquimoly': 'Liqui Moly',
        
        # Castrol
        'castrol': 'Castrol',
        
        # Mobil
        'mobil': 'Mobil',
        'mobil 1': 'Mobil 1',
        
        # Shell
        'shell': 'Shell',
        
        # Total
        'total': 'Total',
        
        # Elf
        'elf': 'Elf',
        
        # Motul
        'motul': 'Motul',
        
        # Valvoline
        'valvoline': 'Valvoline',
        
        # Fuchs
        'fuchs': 'Fuchs',
        
        # Bardahl
        'bardahl': 'Bardahl',
        
        # Chempioil
        'chempioil': 'Chempioil',
        
        # Felix
        'felix': 'Felix',
        
        # Gazpromneft
        'gazpromneft': 'Gazpromneft',
        
        # Cworks
        'cworks': 'Cworks',
        
        # Aimol
        'aimol': 'Aimol',
        'aimoil': 'Aimol',
        
        # Eurol
        'eurol': 'Eurol',
        
        # BMW
        'bmw': 'BMW',
        
        # Ford
        'ford': 'Ford',
        
        # Honda
        'honda': 'Honda',
        
        # Hyundai Xteer
        'hyundai xteer': 'Hyundai Xteer',
        
        # Denckermann
        'denckermann': 'Denckermann',
        
        # Febi
        'febi': 'Febi',
        
        # Hengst
        'hengst': 'Hengst',
        
        # GM
        'gm': 'GM',
    }
    
    # Приводим к нижнему регистру для поиска
    brand_lower = brand_str.lower()
    
    # Ищем точное совпадение
    if brand_lower in brand_mapping:
        return brand_mapping[brand_lower]
    
    # Если точного совпадения нет, проверяем частичные совпадения
    for key, value in brand_mapping.items():
        if key in brand_lower or brand_lower in key:
            return value
    
    # Если совпадений нет, возвращаем с правильным регистром
    return brand_str.title()

def main():
    # Читаем Excel файл
    file_path = '/Users/ilaeliseenko/Downloads/товары унифицирировать.xlsx'
    print("Загружаем файл...")
    df = pd.read_excel(file_path)
    
    print(f"Загружено {len(df)} строк")
    
    # Названия столбцов
    volume_col = 'Доп. поле: Объем'
    brand_col = 'Доп. поле: Brand'
    sae_col = 'Доп. поле: SAE'
    
    # Подсчитываем изначальные значения
    print("\n=== СТАТИСТИКА ДО ОБРАБОТКИ ===")
    if volume_col in df.columns:
        print(f"Объем - уникальных значений: {df[volume_col].nunique()}")
        print("Примеры:", df[volume_col].dropna().unique()[:10])
    
    if brand_col in df.columns:
        print(f"Бренд - уникальных значений: {df[brand_col].nunique()}")
        print("Примеры:", df[brand_col].dropna().unique()[:10])
    
    if sae_col in df.columns:
        print(f"Вязкость - уникальных значений: {df[sae_col].nunique()}")
        print("Примеры:", df[sae_col].dropna().unique()[:10])
    
    # Создаем резервную копию
    df_backup = df.copy()
    
    # Нормализуем данные
    print("\n=== ОБРАБОТКА ДАННЫХ ===")
    
    if volume_col in df.columns:
        print("Нормализуем объем...")
        df[volume_col] = df[volume_col].apply(normalize_volume)
    
    if brand_col in df.columns:
        print("Нормализуем бренд...")
        df[brand_col] = df[brand_col].apply(normalize_brand)
    
    if sae_col in df.columns:
        print("Нормализуем вязкость...")
        df[sae_col] = df[sae_col].apply(normalize_viscosity)
    
    # Подсчитываем результаты
    print("\n=== СТАТИСТИКА ПОСЛЕ ОБРАБОТКИ ===")
    if volume_col in df.columns:
        print(f"Объем - уникальных значений: {df[volume_col].nunique()}")
        print("Примеры:", df[volume_col].dropna().unique()[:10])
    
    if brand_col in df.columns:
        print(f"Бренд - уникальных значений: {df[brand_col].nunique()}")
        print("Примеры:", df[brand_col].dropna().unique()[:10])
    
    if sae_col in df.columns:
        print(f"Вязкость - уникальных значений: {df[sae_col].nunique()}")
        print("Примеры:", df[sae_col].dropna().unique()[:10])
    
    # Показываем изменения
    print("\n=== ПРИМЕРЫ ИЗМЕНЕНИЙ ===")
    
    # Объем
    if volume_col in df.columns:
        print("ОБЪЕМ:")
        vol_changes = df_backup[volume_col].fillna('') != df[volume_col].fillna('')
        if vol_changes.any():
            changed_indices = df_backup[vol_changes].index[:5]
            for idx in changed_indices:
                old_val = df_backup.loc[idx, volume_col]
                new_val = df.loc[idx, volume_col]
                print(f"  '{old_val}' -> '{new_val}'")
    
    # Бренд
    if brand_col in df.columns:
        print("БРЕНД:")
        brand_changes = df_backup[brand_col].fillna('') != df[brand_col].fillna('')
        if brand_changes.any():
            changed_indices = df_backup[brand_changes].index[:5]
            for idx in changed_indices:
                old_val = df_backup.loc[idx, brand_col]
                new_val = df.loc[idx, brand_col]
                print(f"  '{old_val}' -> '{new_val}'")
    
    # Вязкость
    if sae_col in df.columns:
        print("ВЯЗКОСТЬ:")
        sae_changes = df_backup[sae_col].fillna('') != df[sae_col].fillna('')
        if sae_changes.any():
            changed_indices = df_backup[sae_changes].index[:5]
            for idx in changed_indices:
                old_val = df_backup.loc[idx, sae_col]
                new_val = df.loc[idx, sae_col]
                print(f"  '{old_val}' -> '{new_val}'")
    
    # Сохраняем обновленный файл
    print("\n=== СОХРАНЕНИЕ ФАЙЛА ===")
    df.to_excel(file_path, index=False)
    print(f"Файл сохранен: {file_path}")
    
    print("\n=== ЗАВЕРШЕНО ===")
    print("Унификация данных завершена успешно!")

if __name__ == "__main__":
    main()
