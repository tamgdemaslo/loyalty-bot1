-- Удаляем старую таблицу если она существует
DROP TABLE IF EXISTS call_queues;

-- Создаем новую таблицу с правильной структурой
CREATE TABLE call_queues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    queue_type TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 99,
    score REAL DEFAULT 0,
    customer_name TEXT,
    phone TEXT,
    email TEXT,
    segment TEXT,
    recency_days INTEGER DEFAULT 0,
    frequency INTEGER DEFAULT 0,
    monetary_total REAL DEFAULT 0,
    avg_check REAL DEFAULT 0,
    total_revenue REAL DEFAULT 0,
    last_purchase_date TEXT,
    car_model TEXT,
    mileage TEXT,
    last_oil_change_date TEXT,
    days_since_oil_change INTEGER,
    contact_attempts INTEGER DEFAULT 0,
    last_contact_date TEXT,
    is_active INTEGER DEFAULT 1,
    status TEXT DEFAULT 'new',
    notes TEXT,
    offer_text TEXT,
    contact_date TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES contractors_data(agent_id)
);

-- Создаем индексы
CREATE INDEX idx_call_queues_type_priority ON call_queues(queue_type, priority);
CREATE INDEX idx_call_queues_status ON call_queues(status);
CREATE INDEX idx_call_queues_agent ON call_queues(agent_id);
CREATE INDEX idx_call_queues_active ON call_queues(is_active);

-- Таблица contact_history уже существует, не трогаем

-- Заполняем очереди данными
INSERT INTO call_queues (
    agent_id, queue_type, priority, score,
    customer_name, phone, email, segment,
    recency_days, frequency, monetary_total,
    avg_check, total_revenue, last_purchase_date,
    offer_text
)
-- VIP-Frequent (Приоритет 1)
SELECT 
    cs.agent_id,
    'VIP-Frequent' as queue_type,
    1 as priority,
    cs.monetary_total / 1000.0 + cs.frequency * 10 - cs.recency_days / 30.0 as score,
    cd.name,
    cd.phone,
    cd.email,
    cs.segment,
    cs.recency_days,
    cs.frequency,
    cs.monetary_total,
    cs.avg_order_value as avg_check,
    cs.monetary_total as total_revenue,
    cs.last_purchase_date,
    'Бесплатная компьютерная диагностика и приоритетный слот' as offer_text
FROM customer_segments cs
LEFT JOIN contractors_data cd ON cs.agent_id = cd.agent_id
WHERE cs.recency_days <= 90 
    AND cs.frequency >= 3 
    AND cs.monetary_total >= 15000
    AND cs.agent_id NOT IN (
        SELECT agent_id 
        FROM contact_history 
        WHERE contact_date >= datetime('now', '-14 days')
    )

UNION ALL

-- Reactivation-High (Приоритет 2)
SELECT 
    cs.agent_id,
    'Reactivation-High' as queue_type,
    2 as priority,
    cs.monetary_total / 1000.0 + cs.frequency * 5 - cs.recency_days / 60.0 as score,
    cd.name,
    cd.phone,
    cd.email,
    cs.segment,
    cs.recency_days,
    cs.frequency,
    cs.monetary_total,
    cs.avg_order_value as avg_check,
    cs.monetary_total as total_revenue,
    cs.last_purchase_date,
    'Диагностика ходовой/тормозов бесплатно при записи на будни' as offer_text
FROM customer_segments cs
LEFT JOIN contractors_data cd ON cs.agent_id = cd.agent_id
WHERE cs.recency_days > 180 
    AND (cs.frequency >= 2 OR cs.monetary_total >= 10000)
    AND cs.agent_id NOT IN (
        SELECT agent_id 
        FROM contact_history 
        WHERE contact_date >= datetime('now', '-14 days')
    )

UNION ALL

-- Pre-TO (Приоритет 3) - упрощенная версия без demands
SELECT 
    cs.agent_id,
    'Pre-TO' as queue_type,
    3 as priority,
    cs.monetary_total / 1000.0 + 100 - cs.recency_days / 30.0 as score,
    cd.name,
    cd.phone,
    cd.email,
    cs.segment,
    cs.recency_days,
    cs.frequency,
    cs.monetary_total,
    cs.avg_order_value as avg_check,
    cs.monetary_total as total_revenue,
    cs.last_purchase_date,
    'Пакет ТО с подарком' as offer_text
FROM customer_segments cs
LEFT JOIN contractors_data cd ON cs.agent_id = cd.agent_id
WHERE cs.recency_days BETWEEN 150 AND 210  -- Примерно 6 месяцев
    AND cs.frequency >= 2  -- Постоянные клиенты
    AND cs.agent_id NOT IN (
        SELECT agent_id 
        FROM contact_history 
        WHERE contact_date >= datetime('now', '-14 days')
    )

UNION ALL

-- Остальные клиенты - средняя активность (Приоритет 4)
SELECT 
    cs.agent_id,
    'Regular-Maintenance' as queue_type,
    4 as priority,
    cs.monetary_total / 1000.0 + cs.frequency * 2 - cs.recency_days / 60.0 as score,
    cd.name,
    cd.phone,
    cd.email,
    cs.segment,
    cs.recency_days,
    cs.frequency,
    cs.monetary_total,
    cs.avg_order_value as avg_check,
    cs.monetary_total as total_revenue,
    cs.last_purchase_date,
    'Плановое обслуживание и профилактика' as offer_text
FROM customer_segments cs
LEFT JOIN contractors_data cd ON cs.agent_id = cd.agent_id
WHERE cs.monetary_total > 0
    -- Исключаем тех, кто уже попал в другие очереди
    AND cs.agent_id NOT IN (
        -- VIP-Frequent
        SELECT agent_id FROM customer_segments 
        WHERE recency_days <= 90 AND frequency >= 3 AND monetary_total >= 15000
        UNION
        -- Reactivation-High
        SELECT agent_id FROM customer_segments 
        WHERE recency_days > 180 AND (frequency >= 2 OR monetary_total >= 10000)
        UNION
        -- Pre-TO
        SELECT agent_id FROM customer_segments 
        WHERE recency_days BETWEEN 150 AND 210 AND frequency >= 2
    )
    -- Исключаем тех, с кем недавно связывались
    AND cs.agent_id NOT IN (
        SELECT agent_id 
        FROM contact_history 
        WHERE contact_date >= datetime('now', '-14 days')
    );

-- Выводим статистику
SELECT 
    queue_type,
    COUNT(*) as count,
    ROUND(AVG(avg_check), 0) as avg_check,
    ROUND(SUM(total_revenue), 0) as total_revenue,
    ROUND(AVG(recency_days), 0) as avg_recency
FROM call_queues
WHERE is_active = 1
GROUP BY queue_type
ORDER BY priority;
