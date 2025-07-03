// Additional functions for WebApp functionality

// Filter transactions function
function filterTransactions(type) {
    const allButtons = document.querySelectorAll('.filter-btn');
    const transactions = document.querySelectorAll('.transaction-item');
    
    // Update active button
    allButtons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Show/hide transactions based on filter
    transactions.forEach(transaction => {
        if (type === 'all') {
            transaction.style.display = 'flex';
        } else {
            const amount = transaction.querySelector('.transaction-amount');
            if (type === 'earned' && amount.classList.contains('positive')) {
                transaction.style.display = 'flex';
            } else if (type === 'spent' && amount.classList.contains('negative')) {
                transaction.style.display = 'flex';
            } else {
                transaction.style.display = 'none';
            }
        }
    });
}

// Show screen function
function showScreen(screenId) {
    // Hide all screens
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    
    // Show requested screen
    const targetScreen = document.getElementById(screenId);
    if (targetScreen) {
        targetScreen.classList.add('active');
        
        // Hide loading modal
        const loadingModal = document.getElementById('loading-modal');
        if (loadingModal) {
            loadingModal.classList.remove('active');
        }
        
        // Load screen-specific data
        if (screenId === 'visits-screen') {
            loadVisitHistory();
        } else if (screenId === 'transactions-screen') {
            loadTransactionHistory();
        } else if (screenId === 'balance-screen') {
            updateBalanceDetails();
        } else if (screenId === 'achievements-screen') {
            updateAchievements();
        }
    }
}

// Logout function
function logout() {
    if (confirm('Вы уверены, что хотите выйти?')) {
        // Clear user data
        localStorage.removeItem('authToken');
        localStorage.removeItem('userData');
        
        // Show auth screen
        showScreen('auth-screen');
    }
}

// Load visit history
async function loadVisitHistory() {
    const visitsList = document.getElementById('visits-list');
    if (!visitsList) return;
    
    try {
        const response = await fetch('/api/visits', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            }
        });
        
        if (response.ok) {
            const visits = await response.json();
            if (visits.length > 0) {
                visitsList.innerHTML = visits.map(visit => `
                    <div class="visit-card">
                        <div class="visit-header">
                            <span class="visit-date">${formatDate(visit.date)}</span>
                            <span class="visit-amount">${formatMoney(visit.amount)}</span>
                        </div>
                        <div class="visit-details">
                            <p>${visit.services.join(', ')}</p>
                            <p>Бонусы: +${visit.bonuses_earned}</p>
                        </div>
                    </div>
                `).join('');
            } else {
                visitsList.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">История посещений пока пуста</p>';
            }
        }
    } catch (error) {
        console.error('Error loading visits:', error);
        visitsList.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">История посещений пока пуста</p>';
    }
}

// Load transaction history
async function loadTransactionHistory() {
    const transactionsList = document.getElementById('transactions-list');
    if (!transactionsList) return;
    
    try {
        const response = await fetch('/api/transactions', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            }
        });
        
        if (response.ok) {
            const transactions = await response.json();
            if (transactions.length > 0) {
                transactionsList.innerHTML = transactions.map(transaction => `
                    <div class="transaction-item">
                        <div class="transaction-header">
                            <span class="transaction-date">${formatDate(transaction.date)}</span>
                            <span class="transaction-amount ${transaction.type === 'earned' ? 'positive' : 'negative'}">
                                ${transaction.amount}
                            </span>
                        </div>
                        <div class="transaction-details">
                            <p>${transaction.description}</p>
                        </div>
                    </div>
                `).join('');
            } else {
                transactionsList.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">История транзакций пока пуста</p>';
            }
        }
    } catch (error) {
        console.error('Error loading transactions:', error);
        transactionsList.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">История транзакций пока пуста</p>';
    }
}

// Update balance details
function updateBalanceDetails() {
    const userData = JSON.parse(localStorage.getItem('userData') || '{}');
    
    // Update balance
    const detailBalance = document.getElementById('detail-balance');
    if (detailBalance) {
        detailBalance.textContent = userData.loyalty_points || 0;
    }
    
    // Update stats
    const totalVisits = document.getElementById('total-visits');
    if (totalVisits) {
        totalVisits.textContent = userData.total_visits || 0;
    }
    
    const avgCheck = document.getElementById('avg-check');
    if (avgCheck) {
        avgCheck.textContent = formatMoney(userData.average_check || 0);
    }
}

// Update achievements
function updateAchievements() {
    const userData = JSON.parse(localStorage.getItem('userData') || '{}');
    const totalVisits = userData.total_visits || 0;
    
    // Update achievement cards based on visits
    const achievementCards = document.querySelectorAll('.achievement-card');
    achievementCards.forEach(card => {
        const title = card.querySelector('h3').textContent;
        if (title === 'Новичок' && totalVisits >= 1) {
            card.classList.remove('locked');
            card.classList.add('unlocked');
        } else if (title === 'Постоянный клиент' && totalVisits >= 10) {
            card.classList.remove('locked');
            card.classList.add('unlocked');
        } else if (title === 'VIP клиент' && totalVisits >= 50) {
            card.classList.remove('locked');
            card.classList.add('unlocked');
        } else if (title === 'Легенда' && totalVisits >= 100) {
            card.classList.remove('locked');
            card.classList.add('unlocked');
        }
    });
}

// Format money
function formatMoney(amount) {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    });
}

// Initialize phone auth
document.addEventListener('DOMContentLoaded', function() {
    // Handle phone form submission
    const phoneForm = document.getElementById('phone-form');
    if (phoneForm) {
        phoneForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const phoneInput = document.getElementById('phone-input');
            const phone = '+7' + phoneInput.value.replace(/\D/g, '');
            
            if (phone.length !== 12) {
                showError('Введите корректный номер телефона');
                return;
            }
            
            // Show loading
            const loadingModal = document.getElementById('loading-modal');
            if (loadingModal) {
                loadingModal.classList.add('active');
            }
            
            try {
                const response = await fetch('/api/auth/phone', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ phone })
                });
                
                const data = await response.json();
                
                if (response.ok && data.success) {
                    // Save auth data
                    localStorage.setItem('authToken', data.token);
                    localStorage.setItem('userData', JSON.stringify(data.user));
                    
                    // Update UI with user data
                    updateUserInterface(data.user);
                    
                    // Show main screen
                    showScreen('main-screen');
                } else {
                    showError(data.message || 'Ошибка авторизации');
                }
            } catch (error) {
                console.error('Auth error:', error);
                showError('Ошибка подключения к серверу');
            } finally {
                if (loadingModal) {
                    loadingModal.classList.remove('active');
                }
            }
        });
    }
    
    // Format phone input
    const phoneInput = document.getElementById('phone-input');
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            // Replace 8 with 7 at the beginning
            if (value.startsWith('8')) {
                value = '7' + value.slice(1);
            }
            
            // Remove +7 prefix if entered
            if (value.startsWith('7')) {
                value = value.slice(1);
            }
            
            // Limit to 10 digits
            if (value.length > 10) value = value.slice(0, 10);
            
            // Format as XXX XXX XX XX
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
        
        // Handle paste event
        phoneInput.addEventListener('paste', function(e) {
            e.preventDefault();
            let paste = (e.clipboardData || window.clipboardData).getData('text');
            let value = paste.replace(/\D/g, '');
            
            // Handle different formats
            if (value.startsWith('8')) {
                value = '7' + value.slice(1);
            }
            if (value.startsWith('7')) {
                value = value.slice(1);
            }
            
            if (value.length > 10) value = value.slice(0, 10);
            
            // Format and set value
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
        
        // Prevent non-numeric input
        phoneInput.addEventListener('keypress', function(e) {
            if (!/[0-9]/.test(e.key) && e.key !== 'Backspace' && e.key !== 'Delete' && e.key !== 'Tab' && e.key !== 'ArrowLeft' && e.key !== 'ArrowRight' && e.key !== 'Enter') {
                e.preventDefault();
            }
        });
    }
});

// Update user interface
function updateUserInterface(userData) {
    // Update user name
    const userName = document.getElementById('user-name');
    if (userName) {
        userName.textContent = userData.name || 'Пользователь';
    }
    
    // Update balance
    const balanceAmount = document.getElementById('balance-amount');
    if (balanceAmount) {
        balanceAmount.textContent = userData.loyalty_points || 0;
    }
}

// Show error message
function showError(message) {
    const authError = document.getElementById('auth-error');
    if (authError) {
        authError.textContent = message;
        authError.style.display = 'block';
        
        setTimeout(() => {
            authError.style.display = 'none';
        }, 5000);
    }
}

// Make functions available globally
window.filterTransactions = filterTransactions;
window.showScreen = showScreen;
window.logout = logout;
window.loadVisitHistory = loadVisitHistory;
window.loadTransactionHistory = loadTransactionHistory;
window.updateBalanceDetails = updateBalanceDetails;
window.updateAchievements = updateAchievements;
