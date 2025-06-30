// Конфигурация API
const API_BASE = '/api';

// Глобальные переменные
let currentUsersPage = 1;
let currentTransactionsPage = 1;
let currentSearch = '';
let activityChart = null;
let levelsChart = null;
let dailyAnalyticsChart = null;

// Инициализация приложения
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
});

// Управление разделами
function showSection(sectionName) {
    // Скрываем все разделы
    const sections = ['dashboard', 'users', 'transactions', 'analytics'];
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
    }
}

// Загрузка дашборда
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
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    // Создаем контейнер для уведомлений, если его нет
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    const toastElement = document.createElement('div');
    toastElement.innerHTML = toastHtml;
    toastContainer.appendChild(toastElement.firstElementChild);

    const toast = new bootstrap.Toast(toastElement.firstElementChild);
    toast.show();

    // Удаляем элемент после скрытия
    toastElement.firstElementChild.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
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
