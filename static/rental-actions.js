(() => {
    const section = document.querySelector('[data-register="rentals"]');
    const form = document.getElementById('rental-form');
    const message = document.getElementById('rental-message');
    const buttons = [...form.querySelectorAll('button')];
    const equipment = document.getElementById('rental-equipment');
    const client = document.getElementById('rental-client');

    async function loadOptions(url, select, label, placeholder) {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Не удалось загрузить данные для аренды.');
        const items = await response.json();
        select.replaceChildren(new Option(placeholder, ''), ...items.map(item =>
            new Option(label(item), item.id)
        ));
        return items.length;
    }

    async function sendRental(path, data) {
        const options = { method: 'POST' };
        if (data) {
            options.headers = { 'Content-Type': 'application/json' };
            options.body = JSON.stringify(data);
        }
        const response = await fetch(path, options);
        if (!response.ok) {
            const error = await response.json().catch(() => null);
            throw new Error(typeof error?.detail === 'string' ? error.detail : 'Не удалось выполнить действие.');
        }
    }

    function refreshRentalViews() {
        section.dispatchEvent(new Event('rental-updated'));
        document.getElementById('btn-refresh').click();
    }

    section.addEventListener('click', async event => {
        const button = event.target.closest('button[data-return-rental]');
        if (!button || button.disabled || !window.confirm('Отметить оборудование как возвращённое?')) return;
        button.disabled = true;
        try {
            await sendRental('/rentals/' + button.dataset.returnRental + '/return');
            message.textContent = 'Оборудование возвращено.';
            refreshRentalViews();
        } catch (error) {
            message.textContent = error.message;
            button.disabled = false;
        }
    });

    form.addEventListener('submit', async event => {
        event.preventDefault();
        const submitter = event.submitter;
        if (!submitter || submitter.disabled) return;
        const data = Object.fromEntries(new FormData(form));
        if (data.start_date > data.end_date) {
            message.textContent = 'Дата окончания должна быть не раньше даты начала.';
            return;
        }
        data.equipment_id = Number(data.equipment_id);
        data.client_id = Number(data.client_id);
        const booking = submitter.value === 'book';
        buttons.forEach(button => { button.disabled = true; });
        try {
            await sendRental(booking ? '/rentals/book' : '/rentals/', data);
            form.reset();
            message.textContent = booking ? 'Бронь оформлена.' : 'Аренда оформлена.';
            refreshRentalViews();
        } catch (error) {
            message.textContent = error.message;
        } finally {
            buttons.forEach(button => { button.disabled = false; });
        }
    });

    Promise.all([
        loadOptions('/equipment/', equipment, item => item.name + ' · ' + item.inventory_number, 'Выберите оборудование'),
        loadOptions('/clients/', client, item => item.full_name, 'Выберите клиента')
    ]).then(([equipmentCount, clientCount]) => {
        message.textContent = equipmentCount && clientCount ? '' : 'Для аренды нужны оборудование и клиент.';
        buttons.forEach(button => { button.disabled = !(equipmentCount && clientCount); });
    }).catch(error => { message.textContent = error.message; });
})();
