// Telegram Mini App - Система лояльности
class LoyaltyApp {
    constructor() {
        this.tg = window.Telegram.WebApp;
        this.userData = null;
        this.currentPage = 'dashboard';
        this.bookingData = {};
        
        this.init();
    }

    init() {
        // Инициализация Telegram WebApp
        this.tg.ready();
        this.tg.expand();
        
        // Получаем данные пользователя из Telegram
        this.userData = this.tg.initDataUnsafe?.user;
        
        // Загружаем данные приложения
        this.loadUserData();
        
        // Настраиваем обработчики событий
        this.setupEventListeners();
        
        // Применяем тему Telegram
        this.applyTelegramTheme();
        
        // Показываем главный экран
        this.showMainApp();
    }

    applyTelegramTheme() {
        const root = document.documentElement;
        
        // Применяем цвета темы Telegram
        if (this.tg.themeParams) {
            const theme = this.tg.themeParams;
            
            if (theme.bg_color) root.style.setProperty('--tg-theme-bg-color', theme.bg_color);
            if (theme.text_color) root.style.setProperty('--tg-theme-text-color', theme.text_color);
            if (theme.hint_color) root.style.setProperty('--tg-theme-hint-color', theme.hint_color);
            if (theme.link_color) root.style.setProperty('--tg-theme-link-color', theme.link_color);
            if (theme.button_color) root.style.setProperty('--tg-theme-button-color', theme.button_color);
            if (theme.button_text_color) root.style.setProperty('--tg-theme-button-text-color', theme.button_text_color);
            if (theme.secondary_bg_color) root.style.setProperty('--tg-theme-secondary-bg-color', theme.secondary_bg_color);
        }
    }

    async loadUserData() {
        try {
            // Имитация загрузки данных с сервера
            // В реальном приложении здесь будет API вызов
            await this.sleep(1500);
            
            // Демо данные
            this.userLoyaltyData = {
                balance: 2450,
                level: 'Silver',
                totalSpent: 75000,
                totalEarned: 5420,
                totalRedeemed: 2970,
                totalVisits: 12,
                phone: this.userData?.phone_number || '+7 XXX XXX-XX-XX',
                name: this.userData?.first_name || 'Пользователь',
                registeredDate: '2023-05-15'
            };
            
            this.updateUserInterface();
            
        } catch (error) {
            console.error('Error loading user data:', error);
            this.showError('Ошибка загрузки данных');
        }
    }

    updateUserInterface() {
        // Обновляем информацию в заголовке
        document.getElementById('user-name').textContent = this.userLoyaltyData.name;
        document.getElementById('user-status').textContent = `Статус: ${this.userLoyaltyData.level}`;
        document.getElementById('balance-amount').textContent = this.formatMoney(this.userLoyaltyData.balance);
        
        // Обновляем карточку лояльности
        this.updateLoyaltyCard();
        
        // Обновляем профиль
        this.updateProfileData();
        
        // Загружаем последние транзакции
        this.loadRecentTransactions();
        
        // Загружаем историю посещений
        this.loadVisitHistory();
        
        // Загружаем данные ТО
        this.loadMaintenanceData();
    }

    updateLoyaltyCard() {
        const levelBadge = document.getElementById('level-badge');
        const progressFill = document.getElementById('progress-fill');
        const currentSpent = document.getElementById('current-spent');
        const nextLevelReq = document.getElementById('next-level-requirement');
        
        levelBadge.textContent = this.userLoyaltyData.level;
        levelBadge.className = `level-badge ${this.userLoyaltyData.level}`;
        
        currentSpent.textContent = this.formatMoney(this.userLoyaltyData.totalSpent);
        
        const levels = {
            'Bronze': { next: 'Silver', requirement: 50000 },
            'Silver': { next: 'Gold', requirement: 150000 },
            'Gold': { next: 'Platinum', requirement: 300000 },
            'Platinum': { next: 'VIP', requirement: 500000 },
            'VIP': { next: null, requirement: null }
        };
        
        const currentLevel = levels[this.userLoyaltyData.level];
        if (currentLevel.next) {
            const progress = (this.userLoyaltyData.totalSpent / currentLevel.requirement) * 100;
            progressFill.style.width = `${Math.min(progress, 100)}%`;
            
            const remaining = currentLevel.requirement - this.userLoyaltyData.totalSpent;
            nextLevelReq.textContent = `до ${currentLevel.next}: ${this.formatMoney(remaining)}`;
        } else {
            progressFill.style.width = '100%';
            nextLevelReq.textContent = 'Максимальный уровень';
        }
    }

    updateProfileData() {
        document.getElementById('profile-name').textContent = this.userLoyaltyData.name;
        document.getElementById('profile-phone').textContent = this.userLoyaltyData.phone;
        document.getElementById('profile-registered').textContent = this.formatDate(this.userLoyaltyData.registeredDate);
        
        document.getElementById('total-visits').textContent = this.userLoyaltyData.totalVisits;
        document.getElementById('total-spent').textContent = this.formatMoney(this.userLoyaltyData.totalSpent);
        document.getElementById('total-earned').textContent = this.formatMoney(this.userLoyaltyData.totalEarned);
        document.getElementById('total-redeemed').textContent = this.formatMoney(this.userLoyaltyData.totalRedeemed);
    }

    loadRecentTransactions() {
        const container = document.getElementById('recent-transactions');
        
        // Демо данные транзакций
        const transactions = [
            { type: 'Начисление за визит', amount: 450, date: '2024-01-20', positive: true },
            { type: 'Списание бонусов', amount: -320, date: '2024-01-18', positive: false },
            { type: 'Начисление за визит', amount: 680, date: '2024-01-15', positive: true }
        ];
        
        container.innerHTML = '';
        
        if (transactions.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: var(--tg-theme-hint-color);">Нет операций</p>';
            return;
        }
        
        transactions.forEach(transaction => {
            const item = document.createElement('div');
            item.className = 'transaction-item';
            
            item.innerHTML = `
                <div class="transaction-info">
                    <div class="transaction-type">${transaction.type}</div>
                    <div class="transaction-date">${this.formatDate(transaction.date)}</div>
                </div>
                <div class="transaction-amount ${transaction.positive ? 'positive' : 'negative'}">
                    ${transaction.positive ? '+' : ''}${this.formatMoney(Math.abs(transaction.amount))}
                </div>
            `;
            
            container.appendChild(item);
        });
    }

    loadVisitHistory() {
        const container = document.getElementById('history-list');
        
        // Демо данные посещений
        const visits = [
            { id: 1, title: 'Чек №12345', amount: 8500, date: '2024-01-20', services: ['Замена масла', 'Диагностика'] },
            { id: 2, title: 'Чек №12344', amount: 15300, date: '2024-01-15', services: ['ТО-15000', 'Замена фильтров'] },
            { id: 3, title: 'Чек №12343', amount: 3200, date: '2024-01-10', services: ['Развал-схождение'] }
        ];
        
        container.innerHTML = '';
        
        if (visits.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: var(--tg-theme-hint-color);">История пуста</p>';
            return;
        }
        
        visits.forEach(visit => {
            const item = document.createElement('div');
            item.className = 'history-item';
            
            item.innerHTML = `
                <div class="history-header">
                    <div class="history-title">${visit.title}</div>
                    <div class="history-amount">${this.formatMoney(visit.amount)}</div>
                </div>
                <div class="history-date">${this.formatDate(visit.date)}</div>
                <div style="margin-top: 8px; font-size: 14px; color: var(--tg-theme-hint-color);">
                    ${visit.services.join(', ')}
                </div>
            `;
            
            item.addEventListener('click', () => this.showVisitDetails(visit));
            container.appendChild(item);
        });
    }

    loadMaintenanceData() {
        const container = document.getElementById('maintenance-overview');
        
        // Демо данные ТО
        const maintenanceItems = [
            { id: 1, title: '🛢️ Замена масла', subtitle: 'Каждые 10,000 км', status: 'soon', lastKm: 48500, nextKm: 50000 },
            { id: 2, title: '🔧 ТО-15000', subtitle: 'Каждые 15,000 км', status: 'ok', lastKm: 45000, nextKm: 60000 },
            { id: 3, title: '🛞 Замена колодок', subtitle: 'По износу', status: 'overdue', lastKm: 35000, nextKm: 45000 },
            { id: 4, title: '⚙️ Развал-схождение', subtitle: 'Каждые 20,000 км', status: 'never', lastKm: null, nextKm: null }
        ];
        
        container.innerHTML = '';
        
        maintenanceItems.forEach(item => {
            const element = document.createElement('div');
            element.className = 'maintenance-item';
            
            let statusText = '';
            switch (item.status) {
                case 'ok': statusText = 'В порядке'; break;
                case 'soon': statusText = 'Скоро'; break;
                case 'overdue': statusText = 'Просрочено'; break;
                case 'never': statusText = 'Не делали'; break;
            }
            
            element.innerHTML = `
                <div class="maintenance-info">
                    <div class="maintenance-title">${item.title}</div>
                    <div class="maintenance-subtitle">${item.subtitle}</div>
                </div>
                <div class="maintenance-status ${item.status}">${statusText}</div>
            `;
            
            container.appendChild(element);
        });
    }

    setupEventListeners() {
        // Навигация
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const page = e.currentTarget.dataset.page;
                this.showPage(page);
            });
        });
        
        // Быстрые действия
        document.getElementById('redeem-btn').addEventListener('click', () => this.showRedeemModal());
        document.getElementById('analytics-btn').addEventListener('click', () => this.showAnalytics());
        
        // Модалы
        document.getElementById('confirm-redeem').addEventListener('click', () => this.confirmRedeem());
        
        // Добавление ТО
        document.getElementById('add-maintenance-btn').addEventListener('click', () => this.showAddMaintenanceForm());
        
        // Закрытие по клику вне модала
        document.getElementById('modal-overlay').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                this.closeModal();
            }
        });
    }

    showPage(pageName) {
        // Скрываем все страницы
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });
        
        // Убираем активный класс с навигации
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Показываем выбранную страницу
        document.getElementById(`${pageName}-page`).classList.add('active');
        document.querySelector(`[data-page="${pageName}"]`).classList.add('active');
        
        this.currentPage = pageName;
        
        // Специальная логика для разных страниц
        if (pageName === 'booking') {
            this.initBookingWizard();
        }
    }

    showMainApp() {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('main-app').style.display = 'block';
    }

    showRedeemModal() {
        // Проверяем возможность списания
        const lastVisitAmount = 8500; // Демо данные
        const maxRedeem = Math.min(this.userLoyaltyData.balance, lastVisitAmount * 0.3);
        
        document.getElementById('available-redeem').textContent = this.formatMoney(maxRedeem);
        document.getElementById('last-check-amount').textContent = this.formatMoney(lastVisitAmount);
        
        document.getElementById('modal-overlay').classList.add('show');
    }

    closeModal() {
        document.getElementById('modal-overlay').classList.remove('show');
    }

    async confirmRedeem() {
        const availableAmount = parseInt(document.getElementById('available-redeem').textContent.replace(/[^\d]/g, ''));
        
        if (availableAmount > 0) {
            // Имитация запроса к серверу
            this.showLoading('Списание бонусов...');
            
            await this.sleep(1000);
            
            // Обновляем баланс
            this.userLoyaltyData.balance -= availableAmount;
            this.userLoyaltyData.totalRedeemed += availableAmount;
            
            this.updateUserInterface();
            this.closeModal();
            
            this.tg.showAlert(`Успешно списано ${this.formatMoney(availableAmount)} бонусов!`);
        }
    }

    showAnalytics() {
        this.tg.showAlert('Аналитика временно недоступна. Эта функция будет добавлена в следующем обновлении.');
    }

    showAddMaintenanceForm() {
        this.tg.showAlert('Функция добавления записей о ТО будет доступна в следующем обновлении.');
    }

    initBookingWizard() {
        // Инициализация мастера бронирования
        document.getElementById('booking-content').innerHTML = `
            <div style="text-align: center; padding: 40px 20px;">
                <div style="font-size: 48px; margin-bottom: 16px;">📅</div>
                <h3 style="margin-bottom: 16px;">Онлайн запись</h3>
                <p style="color: var(--tg-theme-hint-color); margin-bottom: 24px;">
                    Выберите услугу, мастера и удобное время для визита
                </p>
                <button class="btn-primary" onclick="loyaltyApp.startBookingProcess()">
                    Начать запись
                </button>
            </div>
        `;
    }

    startBookingProcess() {
        this.tg.showAlert('Система онлайн записи будет доступна в следующем обновлении.');
    }

    showVisitDetails(visit) {
        this.tg.showAlert(`Детали визита:\n\n${visit.title}\nСумма: ${this.formatMoney(visit.amount)}\nДата: ${this.formatDate(visit.date)}\nУслуги: ${visit.services.join(', ')}`);
    }

    showLoading(message = 'Загрузка...') {
        // Здесь можно показать индикатор загрузки
        console.log(message);
    }

    showError(message) {
        this.tg.showAlert(`Ошибка: ${message}`);
    }

    formatMoney(amount) {
        return new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'RUB',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Глобальные функции для HTML
function showPage(pageName) {
    window.loyaltyApp.showPage(pageName);
}

function closeModal() {
    window.loyaltyApp.closeModal();
}

// Инициализация приложения
window.loyaltyApp = new LoyaltyApp();

// Дополнительные обработчики для Telegram WebApp
window.Telegram.WebApp.onEvent('viewportChanged', () => {
    console.log('Viewport changed');
});

window.Telegram.WebApp.onEvent('themeChanged', () => {
    window.loyaltyApp.applyTelegramTheme();
});

// Обработка кнопки "Назад" в Telegram
window.Telegram.WebApp.BackButton.onClick(() => {
    if (window.loyaltyApp.currentPage !== 'dashboard') {
        window.loyaltyApp.showPage('dashboard');
    } else {
        window.Telegram.WebApp.close();
    }
});

// Показываем кнопку "Назад" когда не на главной странице
document.addEventListener('DOMContentLoaded', () => {
    const observer = new MutationObserver(() => {
        if (window.loyaltyApp && window.loyaltyApp.currentPage !== 'dashboard') {
            window.Telegram.WebApp.BackButton.show();
        } else {
            window.Telegram.WebApp.BackButton.hide();
        }
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
});
