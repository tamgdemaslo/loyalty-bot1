class LoyaltyApp {
    constructor() {
        this.tg = window.Telegram.WebApp;
        this.appContainer = document.getElementById('app-container');
        this.state = {
            status: 'loading', // loading, auth_required, ready, error
            page: 'dashboard', // dashboard, history, profile
            userData: this.tg.initDataUnsafe?.user || null,
            loyaltyData: null,
            history: null,
            error: null,
        };
        this.init();
    }

    // =================================================================
    // 1. INITIALIZATION & STATE MANAGEMENT
    // =================================================================

    async init() {
        this.tg.ready();
        this.tg.expand();
        this.applyTelegramTheme();
        this.attachEventListeners();

        try {
            const response = await fetch('/api/user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ initData: this.tg.initData, user: this.state.userData })
            });

            if (response.status === 404 || response.status === 403) {
                const errorData = await response.json().catch(() => ({}));
                this.setState({ status: 'auth_required', error: errorData.message });
                return;
            }
            if (!response.ok) throw new Error((await response.json()).message || 'Ошибка сети');

            const loyaltyData = await response.json();
            this.setState({ status: 'ready', loyaltyData });

        } catch (error) {
            console.error("Initialization Error:", error);
            this.setState({ status: 'error', error: 'Не удалось загрузить данные. Попробуйте перезапустить приложение.' });
        }
    }

    setState(newState) {
        Object.assign(this.state, newState);
        this.render();
    }

    // =================================================================
    // 2. RENDERING LOGIC
    // =================================================================

    render() {
this.tg.BackButton.isVisible = this.state.page !== 'dashboard' && this.state.status === 'ready';
        let content = '';
        switch (this.state.status) {
            case 'loading':       content = this.renderScreen('Загрузка...', 'spinner'); break;
            case 'auth_required': content = this.renderAuthForm(); break;
            case 'ready':         content = this.renderMainApp(); break;
            case 'error':         content = this.renderScreen('Ошибка', 'error', this.state.error); break;
        }
        this.appContainer.innerHTML = content;
    }

    renderScreen(title, type, message = '') {
        const icon = type === 'spinner' ? '<div class="spinner"></div>' : (type === 'error' ? '⚠️' : '❓');
        return `
            <div class="screen-container">
                <div class="icon">${icon}</div>
                <h2>${title}</h2>
                ${message ? `<p>${message}</p>` : ''}
            </div>`;
    }

    renderAuthForm() {
        const firstName = this.state.userData?.first_name || 'пользователь';
        return `
            <div class="screen-container" id="auth-container">
                <div class="icon">📞</div>
                <h2>Авторизация</h2>
                <p>Добро пожаловать, ${firstName}!<br>Введите номер телефона для доступа к бонусам.</p>
                <div class="auth-form" style="margin-top: 24px; width: 100%; max-width: 320px;">
                    <div class="phone-input-wrapper">
                        <span>+7</span>
                        <input type="tel" id="user-phone-input" placeholder="999 123-45-67" maxlength="15" data-action="format-phone">
                    </div>
                    <button data-action="auth-by-phone" class="btn-primary">Войти</button>
                </div>
            </div>`;
    }

    renderMainApp() {
        const { loyaltyData, page } = this.state;
        if (!loyaltyData) return this.renderScreen('Ошибка', 'error', 'Не удалось получить данные пользователя.');

        return `
            <div id="main-app">
                <header class="header">
                     <div class="header-content">
                        <div class="user-info">
                            <h2>${loyaltyData.name}</h2>
                            <p>Уровень: ${loyaltyData.level}</p>
                        </div>
                        <div class="balance-badge">
                            <span>${loyaltyData.balance}</span>
                            <small>бонусов</small>
                        </div>
                    </div>
                </header>
                <main id="page-content">${this.renderPageContent()}</main>
                <nav class="bottom-nav">
                    <button data-action="navigate" data-page="dashboard" class="nav-btn ${page === 'dashboard' ? 'active' : ''}"><span class="icon">🏠</span><span>Главная</span></button>
                    <button data-action="navigate" data-page="history" class="nav-btn ${page === 'history' ? 'active' : ''}"><span class="icon">📋</span><span>История</span></button>
                    <button data-action="navigate" data-page="profile" class="nav-btn ${page === 'profile' ? 'active' : ''}"><span class="icon">👤</span><span>Профиль</span></button>
                </nav>
            </div>`;
    }

    renderPageContent() {
        switch (this.state.page) {
            case 'dashboard': return this.renderDashboard();
            case 'history':   return this.renderHistory();
            case 'profile':   return this.renderProfile();
            default: return '';
        }
    }

    renderDashboard() {
        if (this.state.history === null) this.loadHistory();
        const recentHistory = this.state.history?.slice(0, 5) || [];

        return `
            <div class="section">${this.renderLoyaltyCard()}</div>
            <div class="section">
                <div class="quick-actions">
                    <button class="action-btn" data-action="show-placeholder"><span class="icon">🎁</span><span>Списать бонусы</span></button>
                    <button class="action-btn" data-action="show-placeholder"><span class="icon">📅</span><span>Записаться</span></button>
                </div>
            </div>
            <div class="section">
                <div class="section-header">
                    <h3>Последние операции</h3>
                    <button class="view-all-btn" data-action="navigate" data-page="history">Все</button>
                </div>
                ${this.state.history === null ? '<div class="spinner"></div>' : this.renderHistoryList(recentHistory)}
            </div>`;
    }

    renderLoyaltyCard() {
        const { loyaltyData } = this.state;
        const levels = { Bronze: 0, Silver: 50000, Gold: 150000, Platinum: 300000 };
        const nextLevel = Object.keys(levels).find(l => loyaltyData.totalSpent < levels[l]) || 'Diamond';
        const progress = nextLevel !== 'Diamond' ? (loyaltyData.totalSpent / levels[nextLevel]) * 100 : 100;

        return `
        <div class="card loyalty-card">
            <div class="card-header">
                <h3>Карта лояльности</h3>
                <span class="level-badge ${loyaltyData.level}">${loyaltyData.level}</span>
            </div>
            <div class="progress-bar"><div class="progress-fill" style="width: ${progress}%;"></div></div>
            <div class="progress-info">
                <span>${this.formatMoney(loyaltyData.totalSpent)} ₽</span>
                <span>${nextLevel !== 'Diamond' ? `до ${nextLevel}` : 'Макс. уровень'}</span>
            </div>
        </div>`;
    }

    renderHistory() {
        if (this.state.history === null) this.loadHistory();
        return `
            <div class="section">
                <div class="section-header"><h3>История операций</h3></div>
                ${this.state.history === null ? '<div class="spinner"></div>' : this.renderHistoryList(this.state.history)}
            </div>`;
    }

    renderHistoryList(items) {
        if (items.length === 0) {
            return `<div class="empty-list-placeholder"><div class="icon">📂</div><p>Здесь пока пусто</p></div>`;
        }
        return items.map(item => {
            const isPositive = item.type === 'accrual' || item.type === 'visit';
            const icon = item.type === 'accrual' ? '➕' : item.type === 'redemption' ? '➖' : '🛒';
            const amountText = `${isPositive ? '+' : '-'}${this.formatMoney(Math.abs(item.amount))}`;
            return `
            <div class="list-item">
                <div class="item-icon">${icon}</div>
                <div class="item-info">
                    <div class="title">${item.title}</div>
                    <div class="subtitle">${this.formatDate(item.date)}</div>
                </div>
                <div class="item-amount ${isPositive ? 'positive' : 'negative'}">${amountText}</div>
            </div>`;
        }).join('');
    }

    renderProfile() {
        const { loyaltyData } = this.state;
        return `
            <div class="section">
                <div class="section-header"><h3>Статистика</h3></div>
                <div class="profile-stats">
                    <div class="stat-card"><div class="stat-value">${loyaltyData.totalVisits || 0}</div><div class="stat-label">Визитов</div></div>
                    <div class="stat-card"><div class="stat-value">${this.formatMoney(loyaltyData.averageCheck)}</div><div class="stat-label">Средний чек</div></div>
                    <div class="stat-card"><div class="stat-value">${this.formatMoney(loyaltyData.totalSpent)}</div><div class="stat-label">Потрачено</div></div>
                    <div class="stat-card"><div class="stat-value">${this.formatMoney(loyaltyData.totalEarned)}</div><div class="stat-label">Накоплено</div></div>
                </div>
            </div>`;
    }

// =================================================================
    // 3. EVENT HANDLING
    // =================================================================

    attachEventListeners() {
        this.appContainer.addEventListener('click', this.handleAction.bind(this));
        this.appContainer.addEventListener('input', this.handleAction.bind(this));
        this.tg.BackButton.onClick(() => this.navigate('dashboard'));
    }

    handleAction(event) {
        const target = event.target.closest('[data-action]');
        if (!target) return;
        event.preventDefault();
        const { action, page } = target.dataset;
        switch (action) {
            case 'navigate':
                this.navigate(page);
                break;
            case 'auth-by-phone':
                this.authorizeByPhone();
                break;
            case 'format-phone':
                this.formatPhoneNumber(event);
                break;
            case 'show-placeholder':
                this.tg.showAlert('Функция в разработке.');
                break;
        }
    }

    // =================================================================
    // 4. API CALLS & ACTIONS
    // =================================================================

    navigate(page) {
        this.setState({ page });
    }

    async authorizeByPhone() {
        const phoneInput = document.getElementById('user-phone-input');
        const phoneDigits = phoneInput.value.replace(/\D/g, '');
        if (phoneDigits.length !== 10) return this.tg.showAlert('Введите корректный 10-значный номер телефона.');

        this.setState({ status: 'loading' });
        try {
            const result = await this.fetchAPI('/api/auth-phone', {
                method: 'POST',
                body: { phone: '+7' + phoneDigits, user: this.state.userData, initData: this.tg.initData }
            });
            // СНАЧАЛА меняем состояние, ПОТОМ показываем уведомление
            this.setState({ status: 'ready', loyaltyData: result.user });
            this.tg.showAlert(result.message);
        } catch (error) {
            this.setState({ status: 'auth_required', error: error.message });
        }
    }

    async loadHistory() {
        try {
            const [transactions, visits] = await Promise.all([
                this.fetchAPI(`/api/transactions/${this.state.loyaltyData.id}`),
                this.fetchAPI(`/api/visits/${this.state.loyaltyData.id}`)
            ]);
            const history = [
                ...transactions.map(t => ({...t, type: t.type, amount: t.amount, title: t.description})),
                ...visits.map(v => ({...v, type: 'visit', amount: v.bonusEarned, title: v.title}))
            ].sort((a, b) => new Date(b.date) - new Date(a.date));
            this.setState({ history });
        } catch (error) {
            console.error('History loading error:', error);
            this.setState({ history: [] }); // Set to empty array on error to prevent re-fetching
        }
    }

    async fetchAPI(url, options = {}) {
        if (options.body) {
            options.headers = { ...options.headers, 'Content-Type': 'application/json' };
            options.body = JSON.stringify(options.body);
        }
        const response = await fetch(url, options);
        const data = await response.json();
        if (!response.ok) throw new Error(data.message || 'Произошла ошибка');
        return data;
    }

    // =================================================================
    // 5. HELPERS
    // =================================================================

    applyTelegramTheme() {
        Object.entries(this.tg.themeParams).forEach(([key, value]) => {
            document.documentElement.style.setProperty(`--tg-theme-${key.replace(/_/g, '-')}`, value);
        });
    }

    formatMoney(amount, currency = 'RUB') {
        return new Intl.NumberFormat('ru-RU', { style: 'currency', currency, minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(amount || 0);
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' });
    }

    formatPhoneNumber(event) {
        let input = event.target.value.replace(/\D/g, '');
        if (input.length > 10) input = input.substring(0, 10);
        let formatted = '';
        if (input.length > 0) formatted += input.substring(0, 3);
        if (input.length > 3) formatted += ` ${input.substring(3, 6)}`;
        if (input.length > 6) formatted += `-${input.substring(6, 8)}`;
        if (input.length > 8) formatted += `-${input.substring(8, 10)}`;
        event.target.value = formatted;
    }
}

document.addEventListener('DOMContentLoaded', () => new LoyaltyApp());
