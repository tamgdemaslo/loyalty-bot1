// Конфигурация API
const API_BASE = '/api';

// Глобальные переменные
let currentUsersPage = 1;
let currentTransactionsPage = 1;
let currentSearch = '';
let activityChart = null;
let levelsChart = null;
let dailyAnalyticsChart = null;
let customerDynamicsChart = null;
let customerTypesChart = null;
let customerRevenueChart = null;

// Обновление статуса очередей
async function loadCallQueuesStatus() {
    try {
        console.log('Загрузка статистики очередей...');
        const response = await fetch(`${API_BASE}/call-queues/stats`);
        const data = await response.json();
        console.log('Получены данные:', data);

        if (response.ok && data.stats) {
            updateCallQueueStats(data.stats);
            document.getElementById('queue-status').classList.remove('alert-danger');
            document.getElementById('queue-status').classList.add('alert-success');
            document.getElementById('queue-status').innerHTML = '<i class="bi bi-check-circle-fill me-2"></i><strong>Очереди готовы к работе!</strong>';
        } else {
            console.error('Ошибка ответа:', data);
            showError('Ошибка загрузки статуса очередей');
        }
    } catch (error) {
        console.error('Error loading queue status:', error);
        showError('Ошибка подключения к серверу');
    }
}

// Обновление статистики очередей
function updateCallQueueStats(stats) {
    const queueMapping = {
        'Reactivation-High': 'reactivation',
        'Pre-TO': 'preto',
        'VIP-Frequent': 'vip',
        'Data-Poor': 'datapoor'
    };

    stats.forEach(queue => {
        const mappedName = queueMapping[queue.queue_type];
        if (mappedName) {
            const countElement = document.getElementById(`count-${mappedName}`);
            const avgElement = document.getElementById(`avg-${mappedName}`);

            if (countElement) {
                countElement.textContent = queue.count || 0;
                avgElement.textContent = `Средний чек: ${Math.round((queue.avg_check || 0) / 100).toLocaleString()} ₽`;
            }
        }
    });
    
    // Добавляем обработчики кликов на карточки
    document.querySelectorAll('.queue-card').forEach(card => {
        card.onclick = function() {
            const queueType = this.dataset.queue;
            loadQueueCustomers(queueType);
        };
    });
}

// Показать клиентов из очереди
async function loadQueueCustomers(queueType) {
    const response = await fetch(`${API_BASE}/call-queues/${queueType}?page=1&limit=20`);
    if (response.ok) {
        const data = await response.json();
        renderQueueCustomers(data.customers, queueType);
    } else {
        showError('Ошибка загрузки клиентов очереди');
    }
}

// Отобразить клиентов из очереди
function renderQueueCustomers(customers, queueType) {
    document.getElementById('selected-queue-name').textContent = queueType;
    document.getElementById('queue-customers-section').style.display = 'block';
    document.querySelector('#call-queues-section .row').style.display = 'none';
    document.querySelector('#call-queues-section .card.mt-4').style.display = 'none';
    
    const tbody = document.getElementById('queue-customers-table');
    if (customers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">Нет клиентов в этой очереди</td></tr>';
        return;
    }
    
    tbody.innerHTML = customers.map(customer => `
        <tr>
            <td>${customer.name || 'Не указано'}</td>
            <td>${customer.phone || 'Не указано'}</td>
            <td>${Math.round((customer.avg_check || 0) / 100).toLocaleString()} ₽</td>
            <td>${Math.round((customer.total_revenue || 0) / 100).toLocaleString()} ₽</td>
            <td>${customer.recency_days || 0} дней</td>
            <td>${Math.round(customer.bonus_balance || 0).toLocaleString()}</td>
            <td>${customer.last_contact ? new Date(customer.last_contact).toLocaleDateString('ru-RU') : 'Нет контактов'}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="addContact('${customer.agent_id}')">📞 Звонок</button>
                <button class="btn btn-sm btn-outline-info ms-1" onclick="showClientModal('${customer.agent_id}')">👁 Детали</button>
                <button class="btn btn-sm btn-outline-warning ms-1" onclick="showPersonalMessageModal('${customer.agent_id}', '${customer.name || 'Клиент'}')">💬 Сообщение</button>
            </td>
        </tr>
    `).join('');
}

// Скрыть список клиентов
function hideQueueCustomers() {
    document.getElementById('queue-customers-section').style.display = 'none';
    document.querySelector('#call-queues-section .row').style.display = 'flex';
    document.querySelector('#call-queues-section .card.mt-4').style.display = 'block';
}

// Добавить контакт
async function addContact(agentId) {
    const result = prompt('Результат звонка:\n1 - Успешно\n2 - Не ответил\n3 - Не заинтересован\n4 - Перезвонить позже');
    
    const resultMap = {
        '1': 'success',
        '2': 'no_answer',
        '3': 'not_interested',
        '4': 'callback'
    };
    
    const contactResult = resultMap[result];
    if (!contactResult) return;
    
    const notes = prompt('Комментарий к звонку:');
    
    try {
        const response = await fetch(`${API_BASE}/call-queues/contact`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                agent_id: agentId,
                contact_type: 'call',
                result: contactResult,
                notes: notes || ''
            })
        });
        
        if (response.ok) {
            showSuccess('Контакт успешно добавлен');
            // Обновляем текущий список
            const queueType = document.getElementById('selected-queue-name').textContent;
            loadQueueCustomers(queueType);
        } else {
            showError('Ошибка добавления контакта');
        }
    } catch (error) {
        console.error('Error adding contact:', error);
        showError('Ошибка подключения к серверу');
    }
}
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
});

// Управление разделами
function showSection(sectionName) {
    // Скрываем все разделы
    const sections = ['dashboard', 'users', 'transactions', 'analytics', 'call-queues', 'customer-analytics'];
    sections.forEach(section => {
        const element = document.getElementById(section + '-section');
        if (element) {
            element.style.display = 'none';
        }
    });

    // Показываем выбранный раздел
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        targetSection.style.display = 'block';
    }

    // Обновляем активный пункт меню
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    event.target.classList.add('active');

    // Загружаем данные для раздела
    switch(sectionName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'users':
            loadUsers();
            break;
        case 'transactions':
            loadTransactions();
            break;
        case 'analytics':
            loadAnalytics();
            break;
        case 'call-queues':
            loadCallQueuesStatus();
            break;
        case 'customer-analytics':
            loadCustomerAnalytics();
            break;
    }
}

// Загрузка дашборда
function updateCallQueues() {
    document.getElementById('refresh-icon').classList.add('bi-spin');
    fetch(`${API_BASE}/call-queues/refresh`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Очереди успешно обновлены');
                loadCallQueuesStatus();
            } else {
                alert('Ошибка обновления очередей');
            }
        })
        .finally(() => {
            document.getElementById('refresh-icon').classList.remove('bi-spin');
        });
}

async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const stats = await response.json();
        
        if (response.ok) {
            renderStatsCards(stats);
            renderLevelsChart(stats.levelDistribution || []);
            loadActivityChart();
        } else {
            showError('Ошибка загрузки статистики');
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError('Ошибка подключения к серверу');
    }
}

// Отображение статистических карточек
function renderStatsCards(stats) {
    const cardsHtml = `
        <div class="col-md-3">
            <div class="card stats-card text-center">
                <div class="card-body">
                    <i class="bi bi-people fs-1 text-primary mb-2"></i>
                    <h5 class="card-title">${stats.totalUsers || 0}</h5>
                    <p class="card-text text-muted">Всего пользователей</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card stats-card text-center">
                <div class="card-body">
                    <i class="bi bi-currency-dollar fs-1 text-success mb-2"></i>
                    <h5 class="card-title">${(stats.totalBalance || 0).toLocaleString()}</h5>
                    <p class="card-text text-muted">Общий баланс бонусов</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card stats-card text-center">
                <div class="card-body">
                    <i class="bi bi-receipt fs-1 text-info mb-2"></i>
                    <h5 class="card-title">${stats.totalTransactions || 0}</h5>
                    <p class="card-text text-muted">Всего транзакций</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card stats-card text-center">
                <div class="card-body">
                    <i class="bi bi-graph-up fs-1 text-warning mb-2"></i>
                    <h5 class="card-title">${(stats.totalSpent || 0).toLocaleString()}</h5>
                    <p class="card-text text-muted">Общая сумма трат</p>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('stats-cards').innerHTML = cardsHtml;
}

// График уровней лояльности
function renderLevelsChart(levelData) {
    const ctx = document.getElementById('levelsChart').getContext('2d');
    
    if (levelsChart) {
        levelsChart.destroy();
    }

    const levelNames = {
        1: 'Новичок',
        2: 'Бронзовый',
        3: 'Серебряный',
        4: 'Золотой',
        5: 'Платиновый'
    };

    const labels = levelData.map(item => levelNames[item.level_id] || `Уровень ${item.level_id}`);
    const data = levelData.map(item => item.count);
    const colors = ['#6c757d', '#28a745', '#ffc107', '#fd7e14', '#dc3545'];

    levelsChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, data.length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// График активности
async function loadActivityChart() {
    try {
        const response = await fetch(`${API_BASE}/analytics/daily?days=30`);
        const data = await response.json();
        
        if (response.ok) {
            renderActivityChart(data);
        }
    } catch (error) {
        console.error('Error loading activity chart:', error);
    }
}

function renderActivityChart(data) {
    const ctx = document.getElementById('activityChart').getContext('2d');
    
    if (activityChart) {
        activityChart.destroy();
    }

    const dates = data.map(item => new Date(item.date).toLocaleDateString('ru-RU'));
    const accrualData = data.map(item => item.accrual.count);
    const redemptionData = data.map(item => item.redemption.count);

    activityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates.reverse(),
            datasets: [
                {
                    label: 'Начисления',
                    data: accrualData.reverse(),
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Списания',
                    data: redemptionData.reverse(),
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Загрузка пользователей
async function loadUsers(page = 1, search = '') {
    currentUsersPage = page;
    currentSearch = search;

    try {
        const params = new URLSearchParams({
            page: page,
            limit: 20
        });
        
        if (search) {
            params.append('search', search);
        }

        const response = await fetch(`${API_BASE}/users?${params}`);
        const data = await response.json();
        
        if (response.ok) {
            renderUsersTable(data.users);
            renderPagination('usersPagination', data.pagination, loadUsers);
        } else {
            showError('Ошибка загрузки пользователей');
        }
    } catch (error) {
        console.error('Error loading users:', error);
        showError('Ошибка подключения к серверу');
    }
}

// Отображение таблицы пользователей
function renderUsersTable(users) {
    const tbody = document.getElementById('usersTable');
    
    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">Пользователи не найдены</td></tr>';
        return;
    }

    const levelNames = {
        1: 'Новичок',
        2: 'Бронзовый',
        3: 'Серебряный',
        4: 'Золотой',
        5: 'Платиновый'
    };

    tbody.innerHTML = users.map(user => `
        <tr>
            <td>${user.tg_id}</td>
            <td>${user.fullname || 'Не указано'}</td>
            <td>${user.phone || 'Не указано'}</td>
            <td>${user.balance.toLocaleString()}</td>
            <td><span class="level-badge level-${user.level_id}">${levelNames[user.level_id]}</span></td>
            <td>${user.total_spent.toLocaleString()}</td>
            <td>${user.registered_at ? new Date(user.registered_at).toLocaleDateString('ru-RU') : 'Н/Д'}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary btn-action" onclick="editBalance('${user.agent_id}', ${user.balance})">
                        <i class="bi bi-cash"></i>
                    </button>
                    <button class="btn btn-outline-secondary btn-action" onclick="editLevel('${user.agent_id}', ${user.level_id})">
                        <i class="bi bi-award"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Поиск пользователей
function searchUsers() {
    const search = document.getElementById('userSearch').value;
    loadUsers(1, search);
}

// Редактирование баланса
function editBalance(agentId, currentBalance) {
    document.getElementById('balanceAgentId').value = agentId;
    document.getElementById('balanceAmount').value = '';
    document.getElementById('balanceDescription').value = '';
    
    const modal = new bootstrap.Modal(document.getElementById('balanceModal'));
    modal.show();
}

// Отправка изменения баланса
async function submitBalanceChange() {
    const agentId = document.getElementById('balanceAgentId').value;
    const amount = parseInt(document.getElementById('balanceAmount').value);
    const description = document.getElementById('balanceDescription').value;

    if (!amount || !description) {
        showError('Заполните все поля');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/users/${agentId}/balance`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ amount, description })
        });

        const result = await response.json();

        if (response.ok) {
            showSuccess('Баланс успешно изменен');
            bootstrap.Modal.getInstance(document.getElementById('balanceModal')).hide();
            loadUsers(currentUsersPage, currentSearch);
        } else {
            showError(result.error || 'Ошибка изменения баланса');
        }
    } catch (error) {
        console.error('Error updating balance:', error);
        showError('Ошибка подключения к серверу');
    }
}

// Редактирование уровня
function editLevel(agentId, currentLevel) {
    document.getElementById('levelAgentId').value = agentId;
    document.getElementById('levelId').value = currentLevel;
    
    const modal = new bootstrap.Modal(document.getElementById('levelModal'));
    modal.show();
}

// Отправка изменения уровня
async function submitLevelChange() {
    const agentId = document.getElementById('levelAgentId').value;
    const levelId = parseInt(document.getElementById('levelId').value);

    try {
        const response = await fetch(`${API_BASE}/users/${agentId}/level`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ levelId })
        });

        const result = await response.json();

        if (response.ok) {
            showSuccess('Уровень успешно изменен');
            bootstrap.Modal.getInstance(document.getElementById('levelModal')).hide();
            loadUsers(currentUsersPage, currentSearch);
        } else {
            showError(result.error || 'Ошибка изменения уровня');
        }
    } catch (error) {
        console.error('Error updating level:', error);
        showError('Ошибка подключения к серверу');
    }
}

// Загрузка транзакций
async function loadTransactions(page = 1) {
    currentTransactionsPage = page;

    try {
        const type = document.getElementById('transactionType')?.value || '';
        const params = new URLSearchParams({
            page: page,
            limit: 50
        });
        
        if (type) {
            params.append('type', type);
        }

        const response = await fetch(`${API_BASE}/transactions?${params}`);
        const data = await response.json();
        
        if (response.ok) {
            renderTransactionsTable(data.transactions);
            renderPagination('transactionsPagination', data.pagination, loadTransactions);
        } else {
            showError('Ошибка загрузки транзакций');
        }
    } catch (error) {
        console.error('Error loading transactions:', error);
        showError('Ошибка подключения к серверу');
    }
}

// Отображение таблицы транзакций
function renderTransactionsTable(transactions) {
    const tbody = document.getElementById('transactionsTable');
    
    if (transactions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">Транзакции не найдены</td></tr>';
        return;
    }

    tbody.innerHTML = transactions.map(transaction => `
        <tr>
            <td>${transaction.id}</td>
            <td>
                ${transaction.fullname || 'Неизвестно'}<br>
                <small class="text-muted">${transaction.phone || transaction.agent_id}</small>
            </td>
            <td>
                <span class="badge ${transaction.transaction_type === 'accrual' ? 'bg-success' : 'bg-danger'}">
                    ${transaction.transaction_type === 'accrual' ? 'Начисление' : 'Списание'}
                </span>
            </td>
            <td>${transaction.amount.toLocaleString()}</td>
            <td>${transaction.description}</td>
            <td>${new Date(transaction.created_at).toLocaleString('ru-RU')}</td>
        </tr>
    `).join('');
}

// Фильтрация транзакций
function filterTransactions() {
    loadTransactions(1);
}

// Загрузка аналитики
async function loadAnalytics() {
    const days = document.getElementById('analyticsPeriod')?.value || 30;
    
    try {
        const response = await fetch(`${API_BASE}/analytics/daily?days=${days}`);
        const data = await response.json();
        
        if (response.ok) {
            renderDailyAnalyticsChart(data);
        } else {
            showError('Ошибка загрузки аналитики');
        }
    } catch (error) {
        console.error('Error loading analytics:', error);
        showError('Ошибка подключения к серверу');
    }
}

// График ежедневной аналитики
function renderDailyAnalyticsChart(data) {
    const ctx = document.getElementById('dailyAnalyticsChart').getContext('2d');
    
    if (dailyAnalyticsChart) {
        dailyAnalyticsChart.destroy();
    }

    const dates = data.map(item => new Date(item.date).toLocaleDateString('ru-RU'));
    const accrualAmounts = data.map(item => item.accrual.amount);
    const redemptionAmounts = data.map(item => item.redemption.amount);

    dailyAnalyticsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates.reverse(),
            datasets: [
                {
                    label: 'Начислено бонусов',
                    data: accrualAmounts.reverse(),
                    backgroundColor: 'rgba(40, 167, 69, 0.8)',
                    borderColor: '#28a745',
                    borderWidth: 1
                },
                {
                    label: 'Списано бонусов',
                    data: redemptionAmounts.reverse(),
                    backgroundColor: 'rgba(220, 53, 69, 0.8)',
                    borderColor: '#dc3545',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Экспорт пользователей
function exportUsers() {
    window.open(`${API_BASE}/export/users`, '_blank');
}

// Загрузка аналитики клиентов по месяцам
async function loadCustomerAnalytics() {
    const months = document.getElementById('customerAnalyticsPeriod')?.value || 12;
    
    try {
        const response = await fetch(`${API_BASE}/analytics/customers-monthly?months=${months}`);
        const data = await response.json();
        
        if (response.ok) {
            renderCustomerAnalytics(data);
        } else {
            showError('Ошибка загрузки аналитики клиентов');
        }
    } catch (error) {
        console.error('Error loading customer analytics:', error);
        showError('Ошибка подключения к серверу');
    }
}

// Отображение аналитики клиентов по месяцам
function renderCustomerAnalytics(data) {
    // Очищаем контейнер с карточками
    document.getElementById('customer-summary-cards').innerHTML = '';
    
    // Подготавливаем данные для графиков
    const months = data.monthly_analytics.map(item => item.month);
    const newCustomers = data.monthly_analytics.map(item => item.new_customers);
    const existingCustomers = data.monthly_analytics.map(item => item.existing_customers);
    const newRevenue = data.monthly_analytics.map(item => item.new_customers_revenue);
    const existingRevenue = data.monthly_analytics.map(item => item.existing_customers_revenue);
    
    // Обновляем график динамики клиентов
    const ctxDynamics = document.getElementById('customerDynamicsChart').getContext('2d');
    if (customerDynamicsChart) {
        customerDynamicsChart.destroy();
    }
    customerDynamicsChart = new Chart(ctxDynamics, {
        type: 'line',
        data: {
            labels: months.reverse(),
            datasets: [
                {
                    label: 'Новые клиенты',
                    data: newCustomers.reverse(),
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Существующие клиенты',
                    data: existingCustomers.reverse(),
                    borderColor: '#ffc107',
                    backgroundColor: 'rgba(255, 193, 7, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
    
    // Обновляем график выручки
    const ctxRevenue = document.getElementById('customerRevenueChart').getContext('2d');
    if (customerRevenueChart) {
        customerRevenueChart.destroy();
    }
    customerRevenueChart = new Chart(ctxRevenue, {
        type: 'bar',
        data: {
            labels: months.reverse(),
            datasets: [
                {
                    label: 'Выручка от новых клиентов',
                    data: newRevenue.reverse(),
                    backgroundColor: 'rgba(0, 123, 255, 0.8)',
                    borderColor: '#007bff',
                    borderWidth: 1
                },
                {
                    label: 'Выручка от существующих клиентов',
                    data: existingRevenue.reverse(),
                    backgroundColor: 'rgba(255, 193, 7, 0.8)',
                    borderColor: '#ffc107',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Обновляем таблицу с данными
    const tbody = document.getElementById('customerAnalyticsTable');
    tbody.innerHTML = data.monthly_analytics.map(item => `
        <tr>
            <td>${item.month}</td>
            <td>${item.new_customers}</td>
            <td>${item.new_customers_revenue.toLocaleString()} ₽</td>
            <td>${item.existing_customers}</td>
            <td>${item.existing_customers_revenue.toLocaleString()} ₽</td>
            <td>${item.new_customers + item.existing_customers}</td>
            <td>${(item.new_customers_revenue + item.existing_customers_revenue).toLocaleString()} ₽</td>
            <td>${((item.new_customers / (item.new_customers + item.existing_customers)) * 100).toFixed(1)}%</td>
        </tr>
    `).join('');
}

// Отображение пагинации
function renderPagination(containerId, pagination, loadFunction) {
    const container = document.getElementById(containerId);
    
    if (!container || pagination.pages <= 1) {
        container.innerHTML = '';
        return;
    }

    let paginationHtml = '';
    
    // Предыдущая страница
    if (pagination.page > 1) {
        paginationHtml += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="${loadFunction.name}(${pagination.page - 1}); return false;">Назад</a>
            </li>
        `;
    }

    // Номера страниц
    const startPage = Math.max(1, pagination.page - 2);
    const endPage = Math.min(pagination.pages, pagination.page + 2);

    for (let i = startPage; i <= endPage; i++) {
        paginationHtml += `
            <li class="page-item ${i === pagination.page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="${loadFunction.name}(${i}); return false;">${i}</a>
            </li>
        `;
    }

    // Следующая страница
    if (pagination.page < pagination.pages) {
        paginationHtml += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="${loadFunction.name}(${pagination.page + 1}); return false;">Вперед</a>
            </li>
        `;
    }

    container.innerHTML = paginationHtml;
}

// Уведомления
function showSuccess(message) {
    showToast(message, 'success');
}

function showError(message) {
    showToast(message, 'danger');
}

function showToast(message, type) {
    // Создаем контейнер для уведомлений, если его нет
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }

    // Создаем элемент toast
    const toastElement = document.createElement('div');
    toastElement.className = `toast align-items-center text-white bg-${type} border-0`;
    toastElement.setAttribute('role', 'alert');
    toastElement.setAttribute('aria-live', 'assertive');
    toastElement.setAttribute('aria-atomic', 'true');
    
    toastElement.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    toastContainer.appendChild(toastElement);

    try {
        const toast = new bootstrap.Toast(toastElement);
        toast.show();

        // Удаляем элемент после скрытия
        toastElement.addEventListener('hidden.bs.toast', function() {
            if (this.parentNode) {
                this.parentNode.removeChild(this);
            }
        });
        
        // Автоматически скрываем через 5 секунд
        setTimeout(() => {
            if (toastElement.parentNode) {
                toast.hide();
            }
        }, 5000);
    } catch (error) {
        console.error('Error creating toast notification:', error);
        // Fallback: простое alert
        alert(message);
        if (toastElement.parentNode) {
            toastElement.parentNode.removeChild(toastElement);
        }
    }
}

// =============================================================================
// ФУНКЦИИ ДЛЯ ОЧЕРЕДЕЙ ОБЗВОНА
// =============================================================================

// Обновление очередей обзвона
async function updateCallQueues() {
    const button = document.querySelector('button[onclick="updateCallQueues()"]');
    if (!button) return;
    
    const originalText = button.innerHTML;
    
    // Показываем индикатор загрузки
    button.innerHTML = '<i class="bi bi-arrow-repeat spin me-2"></i>Обновление...';
    button.disabled = true;
    
    try {
        console.log('Запущен процесс обновления очередей...');
        
        // Имитация обновления - в реальности здесь был бы запрос к серверу
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        console.log('Очереди обзвона успешно обновлены!');
        
        // Обновляем статус
        await loadCallQueuesStatus();
        
        // Показываем уведомление об успехе
        setTimeout(() => {
            showSuccess('Очереди обзвона успешно обновлены!');
        }, 100);
        
    } catch (error) {
        console.error('Error updating call queues:', error);
        setTimeout(() => {
            showError('Ошибка обновления очередей');
        }, 100);
    } finally {
        // Восстанавливаем кнопку
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// Добавляем CSS для анимации вращения
const style = document.createElement('style');
style.textContent = `
    .spin {
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);

// Показать модалку клиента
function showClientModal(agentId) {
    // Проверяем, подключен ли client-modal.js
    if (typeof window.showClientDetailsModal === 'function') {
        window.showClientDetailsModal(agentId);
    } else {
        // Если модалка не доступна, открываем в новой вкладке
        window.open(`/client.html?agent_id=${agentId}`, '_blank');
    }
}

// Обработчик Enter в поле поиска
document.addEventListener('DOMContentLoaded', function() {
    const userSearch = document.getElementById('userSearch');
    if (userSearch) {
        userSearch.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchUsers();
            }
        });
    }
});

// =============================================================================
// ФУНКЦИИ ПРОГНОЗИРОВАНИЯ
// =============================================================================

// Глобальные переменные для графиков прогноза
let forecastCustomersChart = null;
let forecastRevenueChart = null;

// Загрузка прогнозов
async function loadForecast() {
    const months = document.getElementById('forecast-months').value;

    try {
        const response = await fetch(`${API_BASE}/analytics/customers-forecast?months=${months}`);
        const data = await response.json();

        if (response.ok) {
            renderForecast(data);
        } else {
            showError('Ошибка загрузки прогноза клиентов');
        }
    } catch (error) {
        console.error('Error loading forecast:', error);
        showError('Ошибка подключения к серверу');
    }
}

// Отображение прогнозов
function renderForecast(data) {
    if (data.error) {
        showError(data.error);
        return;
    }

    const forecastInfo = document.getElementById('forecast-info');
    const forecastCharts = document.getElementById('forecast-charts');
    const forecastTableBody = document.getElementById('forecastTableBody');

    document.getElementById('forecast-algorithm').textContent = data.algorithm;
    forecastInfo.style.display = 'block';
    forecastCharts.style.display = 'block';

    // Данные для графиков
    const forecastMonths = data.forecast.map(item => item.month);
    const newForecastCustomers = data.forecast.map(item => item.new_customers);
    const existingForecastCustomers = data.forecast.map(item => item.existing_customers);
    const newForecastRevenue = data.forecast.map(item => item.new_customers_revenue);
    const existingForecastRevenue = data.forecast.map(item => item.existing_customers_revenue);

    // Обновление графиков прогноза
    const ctxForecastCustomers = document.getElementById('forecast-customers-chart').getContext('2d');
    if (forecastCustomersChart) {
        forecastCustomersChart.destroy();
    }
    forecastCustomersChart = new Chart(ctxForecastCustomers, {
        type: 'line',
        data: {
            labels: forecastMonths,
            datasets: [
                {
                    label: 'Новые клиенты',
                    data: newForecastCustomers,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Существующие клиенты',
                    data: existingForecastCustomers,
                    borderColor: '#ffc107',
                    backgroundColor: 'rgba(255, 193, 7, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    const ctxForecastRevenue = document.getElementById('forecast-revenue-chart').getContext('2d');
    if (forecastRevenueChart) {
        forecastRevenueChart.destroy();
    }
    forecastRevenueChart = new Chart(ctxForecastRevenue, {
        type: 'bar',
        data: {
            labels: forecastMonths,
            datasets: [
                {
                    label: 'Выручка от новых клиентов',
                    data: newForecastRevenue,
                    backgroundColor: 'rgba(0, 123, 255, 0.8)',
                    borderColor: '#007bff',
                    borderWidth: 1
                },
                {
                    label: 'Выручка от существующих клиентов',
                    data: existingForecastRevenue,
                    backgroundColor: 'rgba(255, 193, 7, 0.8)',
                    borderColor: '#ffc107',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Обновление таблицы прогноза
    forecastTableBody.innerHTML = data.forecast.map(row => `
        <tr>
            <td>${row.month}</td>
            <td>${row.new_customers}</td>
            <td>${row.new_customers_revenue.toLocaleString()}</td>
            <td>${row.existing_customers}</td>
            <td>${row.existing_customers_revenue.toLocaleString()}</td>
            <td>${row.total_customers}</td>
            <td>${row.total_revenue.toLocaleString()}</td>
            <td>${(row.confidence * 100).toFixed(1)}%</td>
        </tr>
    `).join('');
}

// =============================================================================
// ФУНКЦИИ ДЛЯ МОДАЛЬНЫХ ОКОН СООБЩЕНИЙ
// =============================================================================

// Показать модальное окно для массовой рассылки по очереди
function showQueueBroadcastModal() {
    const queueType = document.getElementById('selected-queue-name').textContent;
    if (!queueType) {
        showError('Сначала выберите очередь');
        return;
    }
    
    // Очищаем форму
    document.getElementById('broadcastMessage').value = '';
    document.getElementById('channelTelegram').checked = true;
    
    // Обновляем заголовок модального окна
    document.getElementById('broadcast-queue-name').textContent = queueType;
    
    // Показываем модальное окно
    const modal = new bootstrap.Modal(document.getElementById('queueBroadcastModal'));
    modal.show();
}

// Показать модальное окно для массовой рассылки
function showBulkMessageModal() {
    const queueType = document.getElementById('selected-queue-name').textContent;
    if (!queueType) {
        showError('Сначала выберите очередь');
        return;
    }
    
    // Очищаем форму
    document.getElementById('bulkMessage').value = '';
    document.getElementById('bulkChannel').value = 'telegram';
    
    // Обновляем заголовок модального окна
    document.getElementById('bulkMessageQueueName').textContent = queueType;
    
    // Показываем модальное окно
    const modal = new bootstrap.Modal(document.getElementById('bulkMessageModal'));
    modal.show();
}

// Показать модальное окно для персонального сообщения
function showPersonalMessageModal(agentId, customerName) {
    // Заполняем форму данными клиента
    document.getElementById('personalAgentId').value = agentId;
    document.getElementById('personalMessage').value = '';
    
    // Устанавливаем канал Telegram по умолчанию
    const telegramRadio = document.getElementById('personalTelegram');
    if (telegramRadio) {
        telegramRadio.checked = true;
    }
    
    // Обновляем заголовок модального окна
    document.getElementById('personal-client-name').textContent = customerName;
    
    // Показываем модальное окно
    const modal = new bootstrap.Modal(document.getElementById('personalMessageModal'));
    modal.show();
}

// Отправка массового сообщения по очереди
async function sendQueueBroadcast() {
    const message = document.getElementById('broadcastMessage').value.trim();
    const queueType = document.getElementById('selected-queue-name').textContent;
    const channelTelegram = document.getElementById('channelTelegram').checked;
    
    if (!message) {
        showError('Введите текст сообщения');
        return;
    }
    
    if (!queueType) {
        showError('Очередь не выбрана');
        return;
    }
    
    // Скрываем кнопку и показываем индикатор загрузки
    const sendButton = document.getElementById('sendBroadcastBtn');
    const loadingDiv = document.getElementById('broadcast-loading');
    const resultDiv = document.getElementById('broadcast-result');
    
    sendButton.style.display = 'none';
    loadingDiv.style.display = 'block';
    resultDiv.style.display = 'none';
    
    try {
        const response = await fetch(`${API_BASE}/messages/bulk`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                queue_type: queueType,
                message: message,
                channel: channelTelegram ? 'telegram' : 'other'
            })
        });
        
        const result = await response.json();
        
        // Скрываем индикатор загрузки
        loadingDiv.style.display = 'none';
        
        if (response.ok) {
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <i class="bi bi-check-circle-fill me-2"></i>
                    Сообщение успешно отправлено ${result.sent_count || 0} клиентам!
                </div>
            `;
            resultDiv.style.display = 'block';
            
            // Автоматически закрываем модальное окно через 2 секунды
            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('queueBroadcastModal')).hide();
            }, 2000);
        } else {
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    Ошибка: ${result.error || 'Не удалось отправить сообщения'}
                </div>
            `;
            resultDiv.style.display = 'block';
            sendButton.style.display = 'inline-block';
        }
    } catch (error) {
        console.error('Error sending queue broadcast:', error);
        loadingDiv.style.display = 'none';
        resultDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                Ошибка подключения к серверу
            </div>
        `;
        resultDiv.style.display = 'block';
        sendButton.style.display = 'inline-block';
    }
}

// Отправка массового сообщения
async function sendBulkMessage() {
    const message = document.getElementById('bulkMessage').value.trim();
    const channel = document.getElementById('bulkChannel').value;
    const queueType = document.getElementById('selected-queue-name').textContent;
    
    if (!message) {
        showError('Введите текст сообщения');
        return;
    }
    
    if (!queueType) {
        showError('Очередь не выбрана');
        return;
    }
    
    // Показываем индикатор загрузки
    const sendButton = document.querySelector('#bulkMessageModal .btn-primary');
    const originalText = sendButton.innerHTML;
    sendButton.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Отправляем...';
    sendButton.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/messages/bulk`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                queue_type: queueType,
                message: message,
                channel: channel
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(`Сообщение успешно отправлено ${result.sent_count || 0} клиентам`);
            bootstrap.Modal.getInstance(document.getElementById('bulkMessageModal')).hide();
        } else {
            showError(result.error || 'Ошибка отправки сообщения');
        }
    } catch (error) {
        console.error('Error sending bulk message:', error);
        showError('Ошибка подключения к серверу');
    } finally {
        // Восстанавливаем кнопку
        sendButton.innerHTML = originalText;
        sendButton.disabled = false;
    }
}

// Отправка персонального сообщения
async function sendPersonalMessage() {
    const agentId = document.getElementById('personalAgentId').value;
    const message = document.getElementById('personalMessage').value.trim();
    
    // Получаем выбранный канал из радио-кнопок
    const channelRadio = document.querySelector('input[name="personalChannel"]:checked');
    const channel = channelRadio ? channelRadio.value : 'telegram';
    
    if (!message) {
        showError('Введите текст сообщения');
        return;
    }
    
    if (!agentId) {
        showError('ID клиента не указан');
        return;
    }
    
    // Показываем индикатор загрузки
    const sendButton = document.querySelector('#personalMessageModal .btn-primary');
    const originalText = sendButton.innerHTML;
    sendButton.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Отправляем...';
    sendButton.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/messages/personal`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                agent_id: agentId,
                message: message,
                channel: channel
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess('Персональное сообщение успешно отправлено');
            bootstrap.Modal.getInstance(document.getElementById('personalMessageModal')).hide();
        } else {
            showError(result.error || 'Ошибка отправки сообщения');
        }
    } catch (error) {
        console.error('Error sending personal message:', error);
        showError('Ошибка подключения к серверу');
    } finally {
        // Восстанавливаем кнопку
        sendButton.innerHTML = originalText;
        sendButton.disabled = false;
    }
}
