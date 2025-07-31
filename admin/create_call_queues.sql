-- Создание таблицы для очередей обзвона
CREATE TABLE IF NOT EXISTS call_queues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    queue_type TEXT NOT NULL, -- 'reactivation_high', 'pre_to', 'vip_frequent', 'data_poor'
    priority INTEGER NOT NULL, -- 1=высший, 4=низкий
    customer_name TEXT,
    phone TEXT,
    email TEXT,
    segment TEXT,
    recency_days INTEGER,
    frequency INTEGER,
    monetary_total INTEGER,
    last_purchase_date TEXT,
    car_model TEXT,
    mileage TEXT,
    last_oil_change_date TEXT,
    days_since_oil_change INTEGER,
    contact_attempts INTEGER DEFAULT 0,
    last_contact_date TEXT,
    status TEXT DEFAULT 'new', -- 'new', 'contacted', 'callback', 'dnc', 'converted'
    notes TEXT,
    offer_text TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES contractors_data(agent_id)
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_call_queues_type_priority ON call_queues(queue_type, priority);
CREATE INDEX IF NOT EXISTS idx_call_queues_status ON call_queues(status);
CREATE INDEX IF NOT EXISTS idx_call_queues_agent ON call_queues(agent_id);

-- Таблица для отслеживания истории контактов
CREATE TABLE IF NOT EXISTS contact_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    queue_id INTEGER NOT NULL,
    contact_date TEXT DEFAULT CURRENT_TIMESTAMP,
    contact_type TEXT, -- 'call', 'sms', 'email'
    result TEXT, -- 'no_answer', 'busy', 'callback', 'interested', 'not_interested', 'dnc'
    notes TEXT,
    next_action TEXT,
    next_contact_date TEXT,
    FOREIGN KEY (agent_id) REFERENCES contractors_data(agent_id),
    FOREIGN KEY (queue_id) REFERENCES call_queues(id)
);

-- Очистка старых данных
DELETE FROM call_queues;

-- 1. REACTIVATION-HIGH (потерянные ценные)
-- Критерии: R > 180 дн, F ≥ 2 или M ≥ 10 000 ₽
INSERT INTO call_queues (
    agent_id, queue_type, priority, customer_name, phone, email, segment,
    recency_days, frequency, monetary_total, last_purchase_date,
    car_model, mileage, offer_text
)
SELECT 
    cs.agent_id,
    'reactivation_high' as queue_type,
    1 as priority,
    cs.customer_name,
    cs.phone,
    cs.email,
    cs.segment,
    cs.recency_days,
    cs.frequency,
    cs.monetary_total,
    cs.last_purchase_date,
    'Не указано' as car_model,
    'Не указано' as mileage,
    'Диагностика ходовой/тормозов 0 ₽ при записи на будни до ' || 
    date('now', '+14 days') || '. Звоните: +7-XXX-XXX-XXXX' as offer_text
FROM customer_segments cs
WHERE cs.recency_days > 180 
  AND (cs.frequency >= 2 OR cs.monetary_total >= 1000000) -- 10 000 ₽ в копейках
  AND cs.phone IS NOT NULL 
  AND cs.phone != ''
ORDER BY cs.monetary_total DESC, cs.frequency DESC;

-- 2. PRE-ТО (по пробегу/сроку)
-- Критерии: 6 мес с последней замены масла/жидкости
-- Используем данные из maintenance_history для определения последней замены масла
INSERT INTO call_queues (
    agent_id, queue_type, priority, customer_name, phone, email, segment,
    recency_days, frequency, monetary_total, last_purchase_date,
    last_oil_change_date, days_since_oil_change, offer_text
)
SELECT 
    cs.agent_id,
    'pre_to' as queue_type,
    2 as priority,
    cs.customer_name,
    cs.phone,
    cs.email,
    cs.segment,
    cs.recency_days,
    cs.frequency,
    cs.monetary_total,
    cs.last_purchase_date,
    COALESCE(last_oil.performed_date, cs.last_purchase_date) as last_oil_change_date,
    CASE 
        WHEN last_oil.performed_date IS NOT NULL THEN
            CAST((julianday('now') - julianday(last_oil.performed_date)) AS INTEGER)
        ELSE cs.recency_days
    END as days_since_oil_change,
    'Пакет ТО: масло + фильтр + долив стеклоомывателя в подарок! ' ||
    'Запись по тел: +7-XXX-XXX-XXXX' as offer_text
FROM customer_segments cs
LEFT JOIN (
    SELECT 
        agent_id,
        MAX(performed_date) as performed_date
    FROM maintenance_history 
    WHERE work_id IN (1, 2) -- предполагаем, что 1,2 - замена масла/фильтра
    GROUP BY agent_id
) last_oil ON cs.agent_id = last_oil.agent_id
WHERE cs.phone IS NOT NULL 
  AND cs.phone != ''
  AND cs.recency_days <= 90 -- активные клиенты
  AND (
    (last_oil.performed_date IS NOT NULL AND 
     CAST((julianday('now') - julianday(last_oil.performed_date)) AS INTEGER) >= 180) -- 6 месяцев
    OR 
    (last_oil.performed_date IS NULL AND cs.recency_days >= 90) -- нет данных о ТО, но покупал 3+ мес назад
  )
ORDER BY days_since_oil_change DESC;

-- 3. VIP-FREQUENT (ядро маржинальности)
-- Критерии: R ≤ 90 дн, F ≥ 3, M ≥ 15 000 ₽
INSERT INTO call_queues (
    agent_id, queue_type, priority, customer_name, phone, email, segment,
    recency_days, frequency, monetary_total, last_purchase_date, offer_text
)
SELECT 
    cs.agent_id,
    'vip_frequent' as queue_type,
    3 as priority,
    cs.customer_name,
    cs.phone,
    cs.email,
    cs.segment,
    cs.recency_days,
    cs.frequency,
    cs.monetary_total,
    cs.last_purchase_date,
    'При ТО — бесплатная компьютерная диагностика + приоритетный слот. ' ||
    'VIP-линия: +7-XXX-XXX-XXXX' as offer_text
FROM customer_segments cs
WHERE cs.recency_days <= 90 
  AND cs.frequency >= 3 
  AND cs.monetary_total >= 1500000 -- 15 000 ₽ в копейках
  AND cs.phone IS NOT NULL 
  AND cs.phone != ''
ORDER BY cs.monetary_total DESC, cs.recency_days ASC;

-- 4. DATA-POOR (досбор данных + подписка)
-- Критерии: нет пробега/марки или неполные поля
INSERT INTO call_queues (
    agent_id, queue_type, priority, customer_name, phone, email, segment,
    recency_days, frequency, monetary_total, last_purchase_date, offer_text
)
SELECT 
    cs.agent_id,
    'data_poor' as queue_type,
    4 as priority,
    cs.customer_name,
    cs.phone,
    cs.email,
    cs.segment,
    cs.recency_days,
    cs.frequency,
    cs.monetary_total,
    cs.last_purchase_date,
    'Обновление данных: получите персональные рекомендации по ТО + ' ||
    'подписка на уведомления в Telegram-боте' as offer_text
FROM customer_segments cs
WHERE cs.phone IS NOT NULL 
  AND cs.phone != ''
  AND cs.frequency > 0 -- есть покупки
  AND (
    cs.email IS NULL OR cs.email = ''
  )
ORDER BY cs.monetary_total DESC;

-- Статистика по очередям
SELECT 
    queue_type,
    COUNT(*) as clients_count,
    AVG(monetary_total)/100 as avg_revenue_rub,
    SUM(monetary_total)/100 as total_revenue_rub,
    AVG(recency_days) as avg_recency_days,
    MIN(recency_days) as min_recency,
    MAX(recency_days) as max_recency
FROM call_queues 
GROUP BY queue_type 
ORDER BY priority;
