#!/usr/bin/env python3
"""
Скрипт для получения нового токена доступа к API МойСклад
"""

import requests
import base64
import json

def get_new_token(username: str, password: str) -> str:
    """
    Получает новый токен доступа к МойСклад API
    
    Args:
        username: логин пользователя
        password: пароль пользователя
    
    Returns:
        str: новый токен доступа
    """
    # Кодируем учетные данные в Base64
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    
    # Заголовки запроса
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Accept-Encoding': 'gzip',
        'Content-Type': 'application/json'
    }
    
    # URL для получения токена
    url = "https://api.moysklad.ru/api/remap/1.2/security/token"
    
    try:
        print("🔑 Получаем новый токен доступа...")
        response = requests.post(url, headers=headers)
        
        if response.status_code in [200, 201]:  # 200 OK или 201 Created
            token_data = response.json()
            access_token = token_data.get('access_token')
            
            if access_token:
                print("✅ Новый токен успешно получен!")
                return access_token
            else:
                print("❌ Токен не найден в ответе")
                print(f"Ответ: {token_data}")
                return None
        else:
            print(f"❌ Ошибка получения токена. Код: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Детали ошибки: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"Текст ошибки: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Исключение при получении токена: {e}")
        return None

def update_env_file(new_token: str):
    """
    Обновляет файл .env с новым токеном
    """
    try:
        # Читаем текущий .env файл
        with open('.env', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Обновляем строку с MS_TOKEN
        updated_lines = []
        token_updated = False
        
        for line in lines:
            if line.startswith('MS_TOKEN='):
                updated_lines.append(f'MS_TOKEN={new_token}\n')
                token_updated = True
            else:
                updated_lines.append(line)
        
        # Если токена не было, добавляем его
        if not token_updated:
            updated_lines.append(f'MS_TOKEN={new_token}\n')
        
        # Записываем обновленный файл
        with open('.env', 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
        
        print("✅ Файл .env успешно обновлен!")
        
    except Exception as e:
        print(f"❌ Ошибка обновления .env файла: {e}")

def main():
    """
    Главная функция
    """
    print("🏪 Получение нового токена доступа МойСклад")
    
    # Учетные данные (замените на свои)
    username = "admin@kuvshinova941"
    password = "559fff8690"
    
    print(f"👤 Пользователь: {username}")
    print(f"🔐 Пароль: {'*' * len(password)}")
    
    # Получаем новый токен
    new_token = get_new_token(username, password)
    
    if new_token:
        print(f"\n🎉 Новый токен получен:")
        print(f"📝 {new_token}")
        
        # Обновляем .env файл
        update_env_file(new_token)
        
        print(f"\n✅ Готово! Теперь можно запускать скрипт начисления бонусов.")
        
    else:
        print("\n❌ Не удалось получить новый токен. Проверьте учетные данные.")

if __name__ == "__main__":
    main()
