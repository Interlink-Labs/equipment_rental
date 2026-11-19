(() => {
    const money = new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' });
    const labels = { ACTIVE: 'Активна', RESERVED: 'Бронь', RETURNED: 'Возвращена', BLOCKED: 'Заблокирован', MANAGER: 'Менеджер', ADMIN: 'Администратор' };

    const columns = {
        rentals: item => [
            '#' + item.equipment_id, '#' + item.client_id,
            item.start_date + ' — ' + item.end_date, money.format(item.total_cost),
            labels[item.status] ?? item.status
        ],
        clients: item => ['#' + item.id, item.full_name],
        employers: item => [item.full_name, labels[item.role] ?? item.role, item.is_active === 'ACTIVE' ? 'Активен' : labels[item.is_active] ?? item.is_active]
    };

    async function loadRegister(section) {
        if (!section.open) return;
        const key = section.dataset.register;
        const message = section.querySelector('[role="status"]');
        const table = section.querySelector('.table-responsive');

        try {
            const response = await fetch('/' + key + '/');
            if (!response.ok) throw new Error('Register unavailable');
            const records = await response.json();
            const rows = records.map(record => {
                const row = document.createElement('tr');
                columns[key](record).forEach(value => { row.insertCell().textContent = value ?? '—'; });
                return row;
            });
            section.querySelector('tbody').replaceChildren(...rows);
            table.hidden = rows.length === 0;
            message.textContent = 'В журнале пока нет записей.';
            message.hidden = rows.length > 0;
        } catch {
            table.hidden = true;
            message.hidden = false;
            message.textContent = 'Не удалось загрузить журнал.';
        }
    }

    document.querySelectorAll('[data-register]').forEach(section => {
        section.addEventListener('toggle', () => loadRegister(section));
        section.addEventListener('rental-updated', () => loadRegister(section));
        loadRegister(section);
    });
})();
