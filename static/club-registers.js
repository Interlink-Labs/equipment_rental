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

    const requests = new WeakMap();
    async function loadRegister(section) {
        if (!section.open) return;
        const user = await window.rentalSession;
        if (!user || (section.hasAttribute('data-admin-only') && user.role !== 'ADMIN')) return;
        const key = section.dataset.register;
        const message = section.querySelector(':scope > p[role="status"]');
        const table = section.querySelector('.table-responsive');

        requests.get(section)?.abort();
        const request = new AbortController();
        requests.set(section, request);
        const query = new URLSearchParams();
        if (key === 'rentals') {
            section.querySelectorAll('#rental-filters [name]').forEach(input => {
                if (input.value) query.set(input.name, input.value);
            });
        }
        try {
            const response = await fetch('/' + key + '/?' + query, { signal: request.signal });
            if (!response.ok) throw new Error('Register unavailable');
            const records = await response.json();
            if (request.signal.aborted) return;
            const rows = records.map(record => {
                const row = document.createElement('tr');
                columns[key](record).forEach(value => { row.insertCell().textContent = value ?? '—'; });
                if (key === 'rentals') {
                    const cell = row.insertCell();
                    if (user.role === 'ADMIN' && (record.status === 'ACTIVE' || record.status === 'RESERVED')) {
                        const button = document.createElement('button');
                        button.type = 'button';
                        button.className = 'btn btn-secondary';
                        button.dataset.rentalId = record.id;
                        button.dataset.rentalAction = record.status === 'ACTIVE' ? 'return' : 'issue';
                        button.textContent = record.status === 'ACTIVE' ? 'Вернуть' : 'Выдать';
                        cell.append(button);
                    } else {
                        cell.textContent = '—';
                    }
                }
                return row;
            });
            section.querySelector('tbody').replaceChildren(...rows);
            table.hidden = rows.length === 0;
            message.textContent = 'В журнале пока нет записей.';
            message.hidden = rows.length > 0;
        } catch {
            if (request.signal.aborted) return;
            table.hidden = true;
            message.hidden = false;
            message.textContent = 'Не удалось загрузить журнал.';
        }
    }

    document.querySelectorAll('[data-register]').forEach(section => {
        section.querySelector('#rental-filters')?.addEventListener('change', () => loadRegister(section));
        section.addEventListener('toggle', () => loadRegister(section));
        section.addEventListener('rental-updated', () => loadRegister(section));
        loadRegister(section);
    });
})();
