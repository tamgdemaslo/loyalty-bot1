# Loyalty Bot - Система лояльности автосервиса

Этот проект создан для управления программой лояльности автосервиса с функциями обзвона клиентов и RFM-анализа.

## Система очередей обзвона

### 📊 Статистика очередей (последнее обновление)

**1. Reactivation-High (Реактивация ценных клиентов):**
- Количество: 235 клиентов
- Средний чек: ~14,438 ₽
- Общая выручка: 3,392,949 ₽
- Средняя давность: ~319 дней
- Критерии: R > 180 дней, F ≥ 2 или M ≥ 10,000 ₽
- Оффер: диагностика ходовой/тормозов бесплатно при записи на будни

**2. Pre-ТО (Предстоящее ТО):**
- Количество: 4 клиента
- Средний чек: ~20,884 ₽
- Общая выручка: 83,534 ₽
- Средняя давность: 85 дней
- Критерии: 6 месяцев с последней замены масла/жидкости
- Оффер: пакет ТО с подарком

**3. VIP-Frequent (VIP клиенты):**
- Количество: 83 клиента
- Средний чек: ~47,355 ₽
- Общая выручка: 3,930,443 ₽
- Средняя давность: ~40 дней
- Критерии: R ≤ 90 дней, F ≥ 3, M ≥ 15,000 ₽
- Оффер: бесплатная компьютерная диагностика и приоритетный слот

**4. Data-Poor (Недостаточно данных):**
- Количество: 1,600 клиентов
- Средний чек: ~11,402 ₽
- Общая выручка: 18,242,499 ₽
- Средняя давность: ~205 дней
- Критерии: отсутствует пробег/марка или неполные данные
- Цель: обогатить данные и перевести в Telegram-бот

### 🎯 Приоритеты обзвона:
1. **VIP-Frequent** - самые прибыльные и активные клиенты
2. **Reactivation-High** - большой потенциал возврата
3. **Pre-ТО** - небольшая, но важная группа
4. **Data-Poor** - для обогащения базы данных

### 📋 Управление очередями

**Обновление очередей:**
```bash
cd admin
sqlite3 ../loyalty.db < create_call_queues.sql
```

**SQL-скрипт содержит:**
- Создание таблиц `call_queues` и `contact_history`
- Очистку старых данных
- Сегментацию клиентов по RFM-критериям
- Статистику по сформированным очередям

**Политика контактов:**
- Лимит: 1 звонок в 14 дней
- Поддержка тега DNC (Do Not Call)
- Учёт истории контактов

---

# Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
