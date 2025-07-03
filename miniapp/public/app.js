// Telegram Mini App - Система лояльности
class LoyaltyApp {
    constructor() {
        console.log('📱 Initializing LoyaltyApp...');
        console.log('💭 window.Telegram exists:', !!window.Telegram);
        
        // Защита от отсутствия Telegram объекта (для локальной разработки)
        if (!window.Telegram) {
            console.log('⚠️ Creating stub Telegram WebApp object for development');
            window.Telegram = { 
                WebApp: { 
                    ready() { console.log('📍 Stub ready() called'); }, 
                    expand() { console.log('📍 Stub expand() called'); }, 
                    initData: '', 
                    initDataUnsafe: { user: { id: 12345, first_name: 'DevUser' } },
                    BackButton: { show() {}, hide() {}, onClick(cb) {} },
                    showAlert(text) { alert(text); }
                } 
            };
        }
        
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
        // Проверяем, есть ли авторизация, но по сути сразу показываем форму телефона
        try {
            console.log('Checking authorization status...');
            
            const response = await fetch('/api/user', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    initData: this.tg.initData || '',
                    user: this.tg.initDataUnsafe?.user || null
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                console.log('Server requires phone auth:', errorData);
                
                // Показываем форму авторизации по телефону
                this.showPhoneAuthForm({
                    firstName: errorData?.firstName || this.userData?.first_name || 'пользователь'
                });
                return;
            }
            
            // Если пользователь уже авторизован (маловероятно)
            this.userLoyaltyData = await response.json();
            this.updateUserInterface();
            
        } catch (error) {
            console.error('Error loading user data:', error);
            
            // При любой ошибке показываем форму авторизации
            this.showPhoneAuthForm({
                firstName: this.userData?.first_name || 'пользователь'
            });
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

    async loadRecentTransactions() {
        const container = document.getElementById('recent-transactions');
        
        try {
            const userId = this.userLoyaltyData?.id || this.userData?.id;
            if (!userId) {
                throw new Error('User ID not available');
            }
            
            const response = await fetch(`/api/transactions/${userId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const transactions = await response.json();
            
            container.innerHTML = '';
            
            if (transactions.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: var(--tg-theme-hint-color);">Нет операций</p>';
                return;
            }
            
            // Показываем только последние 3 транзакции на главной
            const recentTransactions = transactions.slice(0, 3);
            
            recentTransactions.forEach(transaction => {
                const item = document.createElement('div');
                item.className = 'transaction-item';
                
                const isPositive = transaction.amount > 0;
                
                item.innerHTML = `
                    <div class="transaction-info">
                        <div class="transaction-type">${transaction.description}</div>
                        <div class="transaction-date">${this.formatDate(transaction.date)}</div>
                    </div>
                    <div class="transaction-amount ${isPositive ? 'positive' : 'negative'}">
                        ${isPositive ? '+' : ''}${this.formatMoney(Math.abs(transaction.amount))}
                    </div>
                `;
                
                container.appendChild(item);
            });
            
        } catch (error) {
            console.error('Error loading transactions:', error);
            
            // Fallback к демо данным
            const transactions = [
                { type: 'Начисление за визит', amount: 450, date: '2024-01-20', positive: true },
                { type: 'Списание бонусов', amount: -320, date: '2024-01-18', positive: false },
                { type: 'Начисление за визит', amount: 680, date: '2024-01-15', positive: true }
            ];
            
            container.innerHTML = '';
            
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
    }

    async loadVisitHistory() {
        const container = document.getElementById('history-list');
        
        try {
            const userId = this.userLoyaltyData?.id || this.userData?.id;
            if (!userId) {
                throw new Error('User ID not available');
            }
            
            const response = await fetch(`/api/visits/${userId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const visits = await response.json();
            
            container.innerHTML = '';
            
            if (visits.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: var(--tg-theme-hint-color);">История пуста</p>';
                return;
            }
            
            visits.forEach(visit => {
                const item = document.createElement('div');
                item.className = 'history-item';
                
                // Формируем список услуг из массива services
                const servicesList = visit.services && visit.services.length > 0 
                    ? visit.services.map(s => s.name || s).join(', ')
                    : 'Услуги не указаны';
                
                item.innerHTML = `
                    <div class="history-header">
                        <div class="history-title">${visit.title}</div>
                        <div class="history-amount">${this.formatMoney(visit.amount)}</div>
                    </div>
                    <div class="history-date">${this.formatDate(visit.date)}</div>
                    <div style="margin-top: 8px; font-size: 14px; color: var(--tg-theme-hint-color);">
                        ${servicesList}
                    </div>
                    ${visit.bonusEarned ? `<div style="margin-top: 4px; font-size: 12px; color: #4CAF50;">+${this.formatMoney(visit.bonusEarned)} бонусов</div>` : ''}
                `;
                
                item.addEventListener('click', () => this.showVisitDetails(visit));
                container.appendChild(item);
            });
            
        } catch (error) {
            console.error('Error loading visit history:', error);
            
            // Fallback к демо данным
            const visits = [
                { id: 1, title: 'Чек №12345', amount: 8500, date: '2024-01-20', services: ['Замена масла', 'Диагностика'] },
                { id: 2, title: 'Чек №12344', amount: 15300, date: '2024-01-15', services: ['ТО-15000', 'Замена фильтров'] },
                { id: 3, title: 'Чек №12343', amount: 3200, date: '2024-01-10', services: ['Развал-схождение'] }
            ];
            
            container.innerHTML = '';
            
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
    }

    async loadMaintenanceData() {
        const container = document.getElementById('maintenance-overview');
        
        try {
            const userId = this.userLoyaltyData?.id || this.userData?.id;
            if (!userId) {
                throw new Error('User ID not available');
            }
            
            const response = await fetch(`/api/maintenance/${userId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const maintenanceItems = await response.json();
            
            container.innerHTML = '';
            
            if (maintenanceItems.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: var(--tg-theme-hint-color);">Нет данных о ТО</p>';
                return;
            }
            
            maintenanceItems.forEach(item => {
                const element = document.createElement('div');
                element.className = 'maintenance-item';
                
                let statusText = '';
                switch (item.status) {
                    case 'ok': statusText = 'В порядке'; break;
                    case 'soon': statusText = 'Скоро'; break;
                    case 'overdue': statusText = 'Просрочено'; break;
                    case 'never': statusText = 'Не делали'; break;
                    default: statusText = item.status;
                }
                
                element.innerHTML = `
                    <div class="maintenance-info">
                        <div class="maintenance-title">${item.title}</div>
                        <div class="maintenance-subtitle">${item.subtitle}</div>
                        ${item.lastPerformed ? `<div style="font-size: 12px; color: var(--tg-theme-hint-color);">Последнее: ${this.formatDate(item.lastPerformed)} (${item.lastMileage} км)</div>` : ''}
                    </div>
                    <div class="maintenance-status ${item.status}">${statusText}</div>
                `;
                
                container.appendChild(element);
            });
            
        } catch (error) {
            console.error('Error loading maintenance data:', error);
            
            // Fallback к демо данным
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
    
    showAuthorizationPrompt() {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('main-app').innerHTML = `
            <div style="padding: 40px 20px; text-align: center;">
                <div style="font-size: 64px; margin-bottom: 24px;">🔐</div>
                <h2 style="margin-bottom: 16px;">Требуется авторизация</h2>
                <p style="color: var(--tg-theme-hint-color); margin-bottom: 32px;">
                    Для доступа к приложению необходимо сначала авторизоваться в боте.
                </p>
                <p style="color: var(--tg-theme-hint-color); margin-bottom: 24px;">
                    Перейдите в чат с ботом @tgmclientbot и выполните команду /start, поделившись номером телефона.
                </p>
                <button class="btn-primary" onclick="window.Telegram.WebApp.close()">
                    Закрыть приложение
                </button>
            </div>
        `;
        document.getElementById('main-app').style.display = 'block';
    }
    
    showPhoneAuthForm(authData) {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('main-app').innerHTML = `
            <div style="padding: 40px 20px; text-align: center;">
                <div style="font-size: 64px; margin-bottom: 24px;">📞</div>
                <h2 style="margin-bottom: 16px;">Авторизация</h2>
                <p style="color: var(--tg-theme-hint-color); margin-bottom: 32px;">
                    Добро пожаловать, ${authData?.firstName || 'пользователь'}!<br>
                    Для доступа к приложению введите номер телефона.
                </p>
                
                <div id="phone-auth-form" style="max-width: 300px; margin: 0 auto;">
                    <div style="margin-bottom: 24px; text-align: left;">
                        <label style="display: block; margin-bottom: 8px; font-weight: 500;">Номер телефона:</label>
                        <div style="display: flex; align-items: center; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
                            <span style="padding: 12px; background: #f0f0f0; border-right: 1px solid #ddd; font-weight: 500;">+7</span>
                            <input type="tel" id="user-phone-input" placeholder="999 255 60 31" 
                                   maxlength="13"
                                   style="flex: 1; padding: 12px; border: none; outline: none;">
                        </div>
                    </div>
                    
                    <button class="btn-primary" onclick="loyaltyApp.authorizeByPhone()" style="width: 100%; margin-bottom: 16px;">
                        Войти
                    </button>
                    
                    <button class="btn-secondary" onclick="window.Telegram.WebApp.close()" style="width: 100%;">
                        Отмена
                    </button>
                </div>
                
                <div id="auth-loading" style="display: none; padding: 20px;">
                    <div style="font-size: 24px; margin-bottom: 16px;">⏳</div>
                    <p>Авторизация...</p>
                </div>
                
                <div style="margin-top: 32px; padding: 16px; background: var(--tg-theme-secondary-bg-color, #f0f0f0); border-radius: 8px; font-size: 14px; color: var(--tg-theme-hint-color);">
                    <strong>Как это работает:</strong><br>
                    • Если вы уже клиент - найдем ваш аккаунт<br>
                    • Если новый клиент - создадим профиль<br>
                    • Получите доступ ко всем бонусам
                </div>
            </div>
        `;
        document.getElementById('main-app').style.display = 'block';
        
        // Добавляем форматирование номера телефона
        setTimeout(() => {
            const phoneInput = document.getElementById('user-phone-input');
            if (phoneInput) {
                phoneInput.addEventListener('input', (e) => {
                    let value = e.target.value.replace(/\D/g, '');
                    
                    // Ограничиваем до 10 цифр
                    if (value.length > 10) value = value.slice(0, 10);
                    
                    // Форматируем как XXX XXX XX XX
                    let formattedValue = '';
                    if (value.length > 0) {
                        formattedValue = value.slice(0, 3);
                        if (value.length > 3) {
                            formattedValue += ' ' + value.slice(3, 6);
                        }
                        if (value.length > 6) {
                            formattedValue += ' ' + value.slice(6, 8);
                        }
                        if (value.length > 8) {
                            formattedValue += ' ' + value.slice(8, 10);
                        }
                    }
                    
                    e.target.value = formattedValue;
                });
            }
        }, 100);
    }
    
    showRegistrationForm() {
        // Эта функция больше не используется, заменена на showPhoneAuthForm
        this.showPhoneAuthForm({ firstName: 'пользователь' });
    }
    
    async authorizeByPhone() {
        const phoneValue = document.getElementById('user-phone-input').value.trim();
        
        if (!phoneValue) {
            this.tg.showAlert('Пожалуйста, введите номер телефона');
            return;
        }
        
        // Убираем все нецифровые символы
        const phoneDigits = phoneValue.replace(/\D/g, '');
        
        // Проверяем длину (должно быть 10 цифр)
        if (phoneDigits.length !== 10) {
            this.tg.showAlert('Введите номер телефона в формате: 999 255 60 31 (10 цифр)');
            return;
        }
        
        // Добавляем префикс +7
        const fullPhone = '+7' + phoneDigits;
        
        try {
            document.getElementById('phone-auth-form').style.display = 'none';
            document.getElementById('auth-loading').style.display = 'block';
            
            const response = await fetch('/api/auth-phone', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    initData: this.tg.initData || '',
                    phone: fullPhone,
                    user: this.tg.initDataUnsafe?.user || null
                })
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                // Сохраняем данные пользователя
                this.userLoyaltyData = result.user;
                // Также сохраняем userData для совместимости
                this.userData = this.tg.initDataUnsafe?.user || { id: result.user.id };
                
                // Показываем уведомление
                const message = result.user.isNewUser 
                    ? `Добро пожаловать!\n\n🎉 Вы зарегистрированы в системе лояльности\n💰 Начислено 100 приветственных бонусов!`
                    : `Добро пожаловать!\n\n✅ Авторизация успешна\n💰 Ваш баланс: ${this.formatMoney(result.user.balance)}`;
                
                this.tg.showAlert(message);
                
                // Переключаемся на главный экран
                // Перестраиваем интерфейс
                document.getElementById('loading').style.display = 'none';
                document.getElementById('main-app').style.display = 'block';
                document.getElementById('main-app').innerHTML = `
                    <div class="navbar">
                        <div class="nav-btn active" data-page="dashboard" onclick="showPage('dashboard')">
                            <i class="fas fa-home"></i>
                            <span>Главная</span>
                        </div>
                        <div class="nav-btn" data-page="history" onclick="showPage('history')">
                            <i class="fas fa-history"></i>
                            <span>История</span>
                        </div>
                        <div class="nav-btn" data-page="maintenance" onclick="showPage('maintenance')">
                            <i class="fas fa-tools"></i>
                            <span>ТО</span>
                        </div>
                        <div class="nav-btn" data-page="profile" onclick="showPage('profile')">
                            <i class="fas fa-user"></i>
                            <span>Профиль</span>
                        </div>
                    </div>
                    
                    <div class="pages">
                        <div id="dashboard-page" class="page active">
                            <div class="header">
                                <div class="user-info">
                                    <div id="user-name">${this.userLoyaltyData.name}</div>
                                    <div id="user-status">Статус: ${this.userLoyaltyData.level}</div>
                                </div>
                                <div class="balance">
                                    <div class="balance-label">Бонусы</div>
                                    <div id="balance-amount">${this.formatMoney(this.userLoyaltyData.balance)}</div>
                                </div>
                            </div>
                            
                            <div class="loyalty-card">
                                <div class="card-header">
                                    <div id="level-badge" class="level-badge ${this.userLoyaltyData.level}">${this.userLoyaltyData.level}</div>
                                    <div class="card-title">Карта лояльности</div>
                                </div>
                                <div class="progress-container">
                                    <div id="progress-fill" class="progress-fill" style="width: 45%"></div>
                                </div>
                                <div class="loyalty-info">
                                    <div>Потрачено: <span id="current-spent">${this.formatMoney(this.userLoyaltyData.totalSpent)}</span></div>
                                    <div>Осталось <span id="next-level-requirement">до Silver: ₽45,000</span></div>
                                </div>
                            </div>
                            
                            <div class="quick-actions">
                                <button class="action-btn" id="redeem-btn">
                                    <i class="fas fa-gift"></i> Использовать бонусы
                                </button>
                                <button class="action-btn" id="analytics-btn">
                                    <i class="fas fa-chart-line"></i> Аналитика
                                </button>
                            </div>
                            
                            <div class="section">
                                <div class="section-header">
                                    <h3>Последние операции</h3>
                                    <a href="#" onclick="showPage('history')">Все</a>
                                </div>
                                <div id="recent-transactions" class="transactions-list">
                                    <div class="loading-spinner">Загрузка...</div>
                                </div>
                            </div>
                        </div>
                        
                        <div id="history-page" class="page">
                            <h2>История визитов</h2>
                            <div id="history-list" class="history-list">
                                <div class="loading-spinner">Загрузка...</div>
                            </div>
                        </div>
                        
                        <div id="maintenance-page" class="page">
                            <h2>Техническое обслуживание</h2>
                            <div id="maintenance-overview" class="maintenance-overview">
                                <div class="loading-spinner">Загрузка...</div>
                            </div>
                            <button class="btn-primary" id="add-maintenance-btn">
                                <i class="fas fa-plus"></i> Добавить запись о ТО
                            </button>
                        </div>
                        
                        <div id="booking-page" class="page">
                            <h2>Онлайн запись</h2>
                            <div id="booking-content">
                                <div class="loading-spinner">Загрузка...</div>
                            </div>
                        </div>
                        
                        <div id="profile-page" class="page">
                            <h2>Профиль</h2>
                            <div class="profile-info">
                                <div class="profile-field">
                                    <label>Имя:</label>
                                    <div id="profile-name">${this.userLoyaltyData.name}</div>
                                </div>
                                <div class="profile-field">
                                    <label>Телефон:</label>
                                    <div id="profile-phone">${this.userLoyaltyData.phone}</div>
                                </div>
                                <div class="profile-field">
                                    <label>Дата регистрации:</label>
                                    <div id="profile-registered">${this.formatDate(this.userLoyaltyData.registeredDate)}</div>
                                </div>
                            </div>
                            
                            <h3>Статистика</h3>
                            <div class="stats-container">
                                <div class="stat-item">
                                    <div class="stat-value" id="total-visits">${this.userLoyaltyData.totalVisits}</div>
                                    <div class="stat-label">Визитов</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value" id="total-spent">${this.formatMoney(this.userLoyaltyData.totalSpent)}</div>
                                    <div class="stat-label">Потрачено</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value" id="total-earned">${this.formatMoney(this.userLoyaltyData.totalEarned)}</div>
                                    <div class="stat-label">Начислено</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value" id="total-redeemed">${this.formatMoney(this.userLoyaltyData.totalRedeemed)}</div>
                                    <div class="stat-label">Списано</div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                // Устанавливаем обработчики событий
                this.setupEventListeners();
                
                // Загружаем данные
                setTimeout(() => {
                    this.updateLoyaltyCard();
                    this.loadRecentTransactions();
                    this.loadVisitHistory();
                    this.loadMaintenanceData();
                }, 500);
            } else {
                throw new Error(result.message || 'Ошибка авторизации');
            }
            
        } catch (error) {
            console.error('Authorization error:', error);
            document.getElementById('phone-auth-form').style.display = 'block';
            document.getElementById('auth-loading').style.display = 'none';
            this.tg.showAlert(`Ошибка авторизации: ${error.message}`);
        }
    }
    
    async registerUser() {
        // Метод оставлен для совместимости, но больше не используется
        this.tg.showAlert('Используйте авторизацию по номеру телефона');
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
            try {
                this.showLoading('Списание бонусов...');
                
                const response = await fetch('/api/redeem', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        userId: this.userLoyaltyData?.id || this.userData?.id,
                        amount: availableAmount,
                        description: `Списание ${availableAmount} бонусов через Mini App`
                    })
                });
                
                const result = await response.json();
                
                if (response.ok && result.success) {
                    // Обновляем баланс из ответа сервера
                    this.userLoyaltyData.balance = result.newBalance;
                    this.userLoyaltyData.totalRedeemed += availableAmount;
                    
                    this.updateUserInterface();
                    this.closeModal();
                    
                    this.tg.showAlert(result.message || `Успешно списано ${this.formatMoney(availableAmount)} бонусов!`);
                } else {
                    throw new Error(result.message || 'Ошибка при списании бонусов');
                }
                
            } catch (error) {
                console.error('Error redeeming bonuses:', error);
                this.tg.showAlert(`Ошибка: ${error.message}`);
            }
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
