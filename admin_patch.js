// Патч для админ панели - добавляет эндпоинт для показа всех контрагентов с бонусами

// Новый эндпоинт для получения всех контрагентов с бонусами (включая не зарегистрированных)
app.get('/api/all-contractors', (req, res) => {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const offset = (page - 1) * limit;
    const search = req.query.search || '';

    let query = `
        SELECT 
            b.agent_id,
            u.tg_id,
            u.phone,
            u.fullname,
            b.balance,
            l.level_id,
            l.total_spent,
            l.created_at as registered_at,
            CASE WHEN u.agent_id IS NOT NULL THEN 1 ELSE 0 END as is_registered
        FROM bonuses b
        LEFT JOIN user_map u ON b.agent_id = u.agent_id
        LEFT JOIN loyalty_levels l ON b.agent_id = l.agent_id
    `;

    let countQuery = 'SELECT COUNT(*) as total FROM bonuses b';
    let params = [];

    if (search) {
        query += ' WHERE (u.fullname LIKE ? OR u.phone LIKE ? OR b.agent_id LIKE ?)';
        countQuery += ' LEFT JOIN user_map u ON b.agent_id = u.agent_id WHERE (u.fullname LIKE ? OR u.phone LIKE ? OR b.agent_id LIKE ?)';
        const searchParam = `%${search}%`;
        params = [searchParam, searchParam, searchParam];
    }

    query += ' ORDER BY b.balance DESC, l.created_at DESC LIMIT ? OFFSET ?';
    params.push(limit, offset);

    // Получаем общее количество записей
    db.get(countQuery, search ? [params[0], params[1], params[2]] : [], (err, countRow) => {
        if (err) {
            console.error(err);
            res.status(500).json({ error: 'Database error' });
            return;
        }

        // Получаем контрагентов
        db.all(query, params, (err, contractors) => {
            if (err) {
                console.error(err);
                res.status(500).json({ error: 'Database error' });
                return;
            }

            res.json({
                contractors: contractors.map(contractor => ({
                    ...contractor,
                    balance: contractor.balance || 0,
                    level_id: contractor.level_id || 1,
                    total_spent: contractor.total_spent || 0,
                    fullname: contractor.fullname || 'Не зарегистрирован',
                    phone: contractor.phone || 'Не указан',
                    tg_id: contractor.tg_id || null
                })),
                pagination: {
                    page,
                    limit,
                    total: countRow.total,
                    pages: Math.ceil(countRow.total / limit)
                }
            });
        });
    });
});

console.log('✅ Патч применен: добавлен эндпоинт /api/all-contractors');
