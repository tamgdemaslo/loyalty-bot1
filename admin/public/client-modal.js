/**
 * Универсальный компонент для показа детальной информации о клиенте
 * Используется во всех разделах админ панели
 */

// HTML шаблон модального окна
const CLIENT_MODAL_HTML = `
<div class="modal fade" id="clientModal" tabindex="-1" aria-labelledby="clientModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header">
                <div class="d-flex align-items-center">
                    <i class="bi bi-person-circle text-primary me-2" style="font-size: 1.5rem;"></i>  
                    <div>
                        <h4 class="modal-title mb-0" id="clientModalLabel">Загрузка...</h4>
                        <small class="text-muted" id="clientModalSubtitle"></small>
                    </div>
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Закрыть"></button>
            </div>
            <div class="modal-body">
                <div id="clientModalLoading" class="text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Загрузка...</span>
                    </div>
                    <div class="mt-2">Загрузка информации о клиенте...</div>
                </div>
                
                <div id="clientModalContent" style="display: none;">
                    <!-- Основная информация о клиенте -->
                    <div class="row mb-4">
                        <div class="col-md-8">
                            <div class="card">
                                <div class="card-header">
                                    <h6 class="mb-0"><i class="bi bi-info-circle me-2"></i>Основная информация</h6>
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-md-6">
                                            <p><strong>Название:</strong> <span id="clientName">-</span></p>
                                            <p><strong>Телефон:</strong> <span id="clientPhone">-</span></p>
                                            <p><strong>Email:</strong> <span id="clientEmail">-</span></p>
                                            <p><strong>Адрес:</strong> <span id="clientAddress">-</span></p>
                                        </div>
                                        <div class="col-md-6">
                                            <p><strong>ID контрагента:</strong> <code id="clientAgentId">-</code></p>
                                            <p><strong>Статус регистрации:</strong> <span id="clientRegistrationStatus">-</span></p>
                                            <p><strong>Имя в боте:</strong> <span id="clientBotName">-</span></p>
                                            <p><strong>Описание:</strong> <span id="clientDescription">-</span></p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-header">
                                    <h6 class="mb-0"><i class="bi bi-award me-2"></i>Статистика и бонусы</h6>
                                </div>
                                <div class="card-body">
                                    <div class="mb-3">
                                        <div class="d-flex justify-content-between">
                                            <span>Баланс бонусов:</span>
                                            <strong class="text-success" id="clientBalance">0 ₽</strong>
                                        </div>
                                    </div>
                                    <div class="mb-3">
                                        <div class="d-flex justify-content-between">
                                            <span>Уровень лояльности:</span>
                                            <span class="badge bg-primary" id="clientLevel">1</span>
                                        </div>
                                    </div>
                                    <div class="mb-3">
                                        <div class="d-flex justify-content-between">
                                            <span>Всего потрачено:</span>
                                            <strong id="clientTotalSpent">0 ₽</strong>
                                        </div>
                                    </div>
                                    <div id="clientSegmentInfo" style="display: none;">
                                        <hr>
                                        <div class="mb-2">
                                            <span class="badge bg-secondary" id="clientSegment">-</span>
                                        </div>
                                        <div class="mb-2">
                                            <small>RFM:</small>
                                            <div id="clientRFMScores"></div>
                                        </div>
                                        <div class="mb-2">
                                            <small>Активность:</small> <span id="clientActivity" class="small">-</span>
                                        </div>
                                        <div>
                                            <small>Потенциал:</small> <span id="clientGrowthPotential" class="small">-</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Табы -->
                    <ul class="nav nav-tabs" id="clientTabs" role="tablist">
                        <li class="nav-item" role="presentation">
                            <button class="nav-link active" id="shipments-tab" data-bs-toggle="tab" data-bs-target="#shipments" type="button" role="tab">
                                <i class="bi bi-truck me-2"></i>Отгрузки (<span id="shipmentsCount">0</span>)
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="transactions-tab" data-bs-toggle="tab" data-bs-target="#transactions" type="button" role="tab">
                                <i class="bi bi-coin me-2"></i>Транзакции (<span id="transactionsCount">0</span>)
                            </button>
                        </li>
                    </ul>

                    <!-- Содержимое табов -->
                    <div class="tab-content mt-3" id="clientTabsContent">
                        <!-- Таб отгрузок -->
                        <div class="tab-pane fade show active" id="shipments" role="tabpanel">
                            <div id="shipmentsTable">
                                <div class="table-responsive">
                                    <table class="table table-sm table-hover">
                                        <thead class="table-light">
                                            <tr>
                                                <th>Номер</th>
                                                <th>Дата</th>
                                                <th>Сумма</th>
                                                <th>Статус</th>
                                                <th>Позиций</th>
                                                <th>Действия</th>
                                            </tr>
                                        </thead>
                                        <tbody id="shipmentsTableBody">
                                            <!-- Данные будут загружены через JS -->
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        <!-- Таб транзакций -->
                        <div class="tab-pane fade" id="transactions" role="tabpanel">
                            <div id="transactionsTable">
                                <div class="table-responsive">
                                    <table class="table table-sm table-hover">
                                        <thead class="table-light">
                                            <tr>
                                                <th>Дата</th>
                                                <th>Тип</th>
                                                <th>Сумма</th>
                                                <th>Описание</th>
                                            </tr>
                                        </thead>
                                        <tbody id="transactionsTableBody">
                                            <!-- Данные будут загружены через JS -->
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div id="clientModalError" class="alert alert-danger" style="display: none;">
                    <h6>Ошибка загрузки</h6>
                    <p class="mb-0">Не удалось загрузить информацию о клиенте. Попробуйте еще раз.</p>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Модальное окно для позиций отгрузки -->
<div class="modal fade" id="shipmentPositionsModal" tabindex="-1" aria-labelledby="shipmentPositionsModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="shipmentPositionsModalLabel">
                    <i class="bi bi-list-ul me-2"></i>Позиции отгрузки
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Закрыть"></button>
            </div>
            <div class="modal-body">
                <div id="positionsLoading" class="text-center py-3">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Загрузка...</span>
                    </div>
                </div>
                
                <div id="positionsContent" style="display: none;">
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead class="table-light">
                                <tr>
                                    <th>Наименование</th>
                                    <th>Кол-во</th>
                                    <th>Цена</th>
                                    <th>Сумма</th>
                                    <th>Авто</th>
                                </tr>
                            </thead>
                            <tbody id="positionsTableBody">
                                <!-- Данные будут загружены через JS -->
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="row mt-3">
                        <div class="col-md-6" id="carInfo">
                            <!-- Информация об автомобиле -->
                        </div>
                        <div class="col-md-6">
                            <div class="text-end">
                                <h6>Итого: <span id="positionsTotal" class="text-success">0 ₽</span></h6>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
`;

class ClientModal {
    constructor() {
        this.currentClientId = null;
        this.modal = null;
        this.positionsModal = null;
        this.init();
    }

    init() {
        // Добавляем HTML в конец body, если его еще нет
        if (!document.getElementById('clientModal')) {
            document.body.insertAdjacentHTML('beforeend', CLIENT_MODAL_HTML);
        }
        
        // Инициализируем модальные окна
        this.modal = new bootstrap.Modal(document.getElementById('clientModal'));
        this.positionsModal = new bootstrap.Modal(document.getElementById('shipmentPositionsModal'));
    }

    // Открыть карточку клиента
    async show(agentId) {
        this.currentClientId = agentId;
        this.modal.show();
        
        // Сбрасываем состояние
        this.resetModal();
        
        try {
            // Загружаем данные клиента
            const response = await fetch(`/api/client/${agentId}`);
            if (!response.ok) {
                throw new Error('Ошибка загрузки данных клиента');
            }
            
            const data = await response.json();
            this.displayClientData(data);
            
        } catch (error) {
            console.error('Error loading client data:', error);
            this.showError();
        }
    }

    resetModal() {
        document.getElementById('clientModalLoading').style.display = 'block';
        document.getElementById('clientModalContent').style.display = 'none';
        document.getElementById('clientModalError').style.display = 'none';
        
        document.getElementById('clientModalLabel').textContent = 'Загрузка...';
        document.getElementById('clientModalSubtitle').textContent = '';
    }

    displayClientData(data) {
        const { client, shipments, transactions } = data;
        
        // Заголовок модального окна
        document.getElementById('clientModalLabel').textContent = client.name || 'Клиент';
        document.getElementById('clientModalSubtitle').textContent = `ID: ${client.agent_id}`;
        
        // Основная информация
        document.getElementById('clientName').textContent = client.name || 'Не указано';
        document.getElementById('clientPhone').textContent = client.phone || 'Не указан';
        document.getElementById('clientEmail').textContent = client.email || 'Не указан';
        document.getElementById('clientAddress').textContent = client.address || 'Не указан';
        document.getElementById('clientAgentId').textContent = client.agent_id;
        document.getElementById('clientDescription').textContent = client.description || 'Нет описания';
        
        // Статус регистрации
        const regStatus = document.getElementById('clientRegistrationStatus');
        if (client.is_registered) {
            regStatus.innerHTML = '<span class="badge bg-success">Зарегистрирован</span>';
            document.getElementById('clientBotName').textContent = client.bot_name || 'Не указано';
        } else {
            regStatus.innerHTML = '<span class="badge bg-secondary">Не зарегистрирован</span>';
            document.getElementById('clientBotName').textContent = 'Не зарегистрирован';
        }
        
        // Бонусы и статистика
        document.getElementById('clientBalance').textContent = this.formatMoney(client.balance);
        document.getElementById('clientLevel').textContent = client.level_id || 1;
        document.getElementById('clientTotalSpent').textContent = this.formatMoney(client.total_spent);
        
        // RFM данные, если есть
        if (client.segment) {
            const segmentInfo = document.getElementById('clientSegmentInfo');
            segmentInfo.style.display = 'block';
            
            document.getElementById('clientSegment').textContent = client.segment;
            
            // RFM скоры
            const rfmContainer = document.getElementById('clientRFMScores');
            rfmContainer.innerHTML = `
                <span class="rfm-score score-${client.R_score || 1}">${client.R_score || '?'}</span>
                <span class="rfm-score score-${client.F_score || 1}">${client.F_score || '?'}</span>
                <span class="rfm-score score-${client.M_score || 1}">${client.M_score || '?'}</span>
            `;
            
            document.getElementById('clientActivity').textContent = client.activity_status || 'Неизвестно';
            document.getElementById('clientGrowthPotential').textContent = client.growth_potential || 'Неизвестно';
        }
        
        // Загружаем отгрузки и транзакции
        this.displayShipments(shipments);
        this.displayTransactions(transactions);
        
        // Показываем контент
        document.getElementById('clientModalLoading').style.display = 'none';
        document.getElementById('clientModalContent').style.display = 'block';
    }

    displayShipments(shipments) {
        const tbody = document.getElementById('shipmentsTableBody');
        const countElement = document.getElementById('shipmentsCount');
        
        countElement.textContent = shipments.length;
        
        if (shipments.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Отгрузки не найдены</td></tr>';
            return;
        }
        
        tbody.innerHTML = shipments.map(shipment => `
            <tr>
                <td><code>${shipment.name || shipment.demand_id}</code></td>
                <td>${this.formatDate(shipment.moment)}</td>
                <td><strong>${this.formatMoney(shipment.sum)}</strong></td>
                <td><span class="badge bg-info">${shipment.state_name || 'Не указан'}</span></td>
                <td>${shipment.positions_count || 0}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="clientModal.showPositions('${shipment.demand_id}', '${shipment.name || shipment.demand_id}')">
                        <i class="bi bi-list-ul"></i> Позиции
                    </button>
                </td>
            </tr>
        `).join('');
    }

    displayTransactions(transactions) {
        const tbody = document.getElementById('transactionsTableBody');
        const countElement = document.getElementById('transactionsCount');
        
        countElement.textContent = transactions.length;
        
        if (transactions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Транзакции не найдены</td></tr>';
            return;
        }
        
        tbody.innerHTML = transactions.map(transaction => `
            <tr>
                <td>${this.formatDate(transaction.created_at)}</td>
                <td>
                    <span class="badge ${transaction.transaction_type === 'accrual' ? 'bg-success' : 'bg-warning'}">
                        ${transaction.transaction_type === 'accrual' ? 'Начисление' : 'Списание'}
                    </span>
                </td>
                <td><strong>${this.formatMoney(transaction.amount * 100)}</strong></td>
                <td>${transaction.description || 'Без описания'}</td>
            </tr>
        `).join('');
    }

    async showPositions(demandId, shipmentName) {
        document.getElementById('shipmentPositionsModalLabel').innerHTML = 
            `<i class="bi bi-list-ul me-2"></i>Позиции отгрузки: ${shipmentName}`;
        
        this.positionsModal.show();
        
        // Сброс состояния
        document.getElementById('positionsLoading').style.display = 'block';
        document.getElementById('positionsContent').style.display = 'none';
        
        try {
            const response = await fetch(`/api/shipment/${demandId}/positions`);
            const data = await response.json();
            
            if (data.success) {
                this.displayPositions(data.positions, data.total);
            } else {
                // Используем ошибку от сервера, если есть
                throw new Error(data.message || 'Ошибка загрузки позиций');
            }
            
        } catch (error) {
            console.error('Error loading positions:', error);
            let errorMessage = 'Ошибка загрузки позиций';
            
            // Проверяем, есть ли конкретная ошибка от сервера
            if (error.message) {
                errorMessage = error.message;
            }
            
            document.getElementById('positionsTableBody').innerHTML = 
                `<tr><td colspan="5" class="text-center text-danger">
                    <div><i class="bi bi-exclamation-triangle me-2"></i>${errorMessage}</div>
                    <small class="text-muted d-block mt-2">Проверьте настройки интеграции с МойСклад</small>
                </td></tr>`;
        } finally {
            document.getElementById('positionsLoading').style.display = 'none';
            document.getElementById('positionsContent').style.display = 'block';
        }
    }

    displayPositions(positions, total) {
        const tbody = document.getElementById('positionsTableBody');
        const totalElement = document.getElementById('positionsTotal');
        const carInfoElement = document.getElementById('carInfo');
        
        totalElement.textContent = this.formatMoney(total);
        
        if (positions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Позиции не найдены</td></tr>';
            return;
        }
        
        tbody.innerHTML = positions.map(position => {
            const isService = position.brand === 'Услуга';
            return `
                <tr>
                    <td>
                        <div class="fw-bold">${position.assortment_name}</div>
                        ${position.article ? `<small class="text-muted">Артикул: ${position.article}</small>` : ''}
                        ${position.brand && !isService ? `<br><small class="text-info">Бренд: ${position.brand}</small>` : ''}
                    </td>
                    <td>${position.quantity}</td>
                    <td>${this.formatMoney(position.price)}</td>
                    <td><strong>${this.formatMoney(position.sum)}</strong></td>
                    <td>
                        ${position.car_model ? `<small>${position.car_model} (${position.car_year})</small>` : '-'}
                    </td>
                </tr>
            `;
        }).join('');
        
        // Информация об автомобиле (если есть)
        const carInfo = positions.find(p => p.car_model);
        if (carInfo) {
            carInfoElement.innerHTML = `
                <div class="card bg-light">
                    <div class="card-body p-2">
                        <h6 class="card-title mb-1"><i class="bi bi-car-front me-2"></i>Автомобиль</h6>
                        <p class="mb-1"><strong>${carInfo.car_model}</strong> (${carInfo.car_year})</p>
                        <small class="text-muted">Пробег: ${carInfo.mileage}</small>
                    </div>
                </div>
            `;
        } else {
            carInfoElement.innerHTML = '';
        }
    }

    showError() {
        document.getElementById('clientModalLoading').style.display = 'none';
        document.getElementById('clientModalContent').style.display = 'none';
        document.getElementById('clientModalError').style.display = 'block';
    }

    // Вспомогательные методы
    formatMoney(amount) {
        return new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'RUB',
            minimumFractionDigits: 0
        }).format(amount / 100);
    }

    formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

// Создаем глобальный экземпляр
window.clientModal = new ClientModal();

// Функция для вызова из других модулей
window.showClientDetailsModal = function(agentId) {
    window.clientModal.show(agentId);
};

// CSS стили для RFM скоров
const RFM_STYLES = `
<style>
.rfm-score {
    display: inline-block;
    width: 25px;
    height: 25px;
    border-radius: 50%;
    color: white;
    text-align: center;
    line-height: 25px;
    font-size: 0.8rem;
    font-weight: bold;
    margin: 0 2px;
}
.score-1 { background-color: #dc3545; }
.score-2 { background-color: #fd7e14; }
.score-3 { background-color: #ffc107; color: black; }
.score-4 { background-color: #28a745; }
.score-5 { background-color: #20c997; }
</style>
`;

// Добавляем стили в head
if (!document.querySelector('style[data-client-modal]')) {
    document.head.insertAdjacentHTML('beforeend', RFM_STYLES.replace('<style>', '<style data-client-modal>'));
}
