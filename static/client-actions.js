(() => {
    const section = document.querySelector('[data-register="clients"]');
    const form = document.getElementById('client-form');
    const message = document.getElementById('client-form-message');
    const submit = form.querySelector('[type="submit"]');
    let busy = false;
    function refresh() {
        section.dispatchEvent(new Event('clients-updated'));
        document.dispatchEvent(new Event('client-options-updated'));
    }
    async function request(path, method, data) {
        const options = { method };
        if (data) {
            options.headers = { 'Content-Type': 'application/json' };
            options.body = JSON.stringify(data);
        }
        const response = await fetch(path, options);
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(typeof error.detail === 'string' ? error.detail :
                error.detail?.map(item => item.msg).join('. ') || 'Не удалось сохранить изменения.');
        }
    }
    form.addEventListener('reset', () => {
        form.elements.client_id.value = '';
        submit.textContent = 'Добавить клиента';
        message.textContent = '';
    });
    form.addEventListener('submit', async event => {
        event.preventDefault();
        if (busy) return;
        const data = Object.fromEntries(new FormData(form));
        const id = data.client_id;
        delete data.client_id;
        busy = true;
        submit.disabled = true;
        try {
            await request('/clients/' + (id || ''), id ? 'PUT' : 'POST', data);
            form.reset();
            message.textContent = id ? 'Данные клиента обновлены.' : 'Клиент добавлен.';
            refresh();
        } catch (error) {
            message.textContent = error.message;
        } finally {
            busy = false;
            submit.disabled = false;
        }
    });
    section.addEventListener('click', async event => {
        const button = event.target.closest('button[data-client-action]');
        if (!button || busy) return;
        const id = button.dataset.clientId;
        if (button.dataset.clientAction === 'edit') {
            form.elements.client_id.value = id;
            form.elements.full_name.value = button.dataset.clientName;
            form.elements.phone.value = button.dataset.clientPhone;
            submit.textContent = 'Сохранить изменения';
            message.textContent = 'Редактирование клиента #' + id;
            form.elements.full_name.focus();
            return;
        }
        if (!window.confirm('Удалить клиента «' + button.dataset.clientName + '»?')) return;
        busy = true;
        button.disabled = true;
        try {
            await request('/clients/' + id, 'DELETE');
            if (form.elements.client_id.value === id) form.reset();
            message.textContent = 'Клиент удалён.';
            refresh();
        } catch (error) {
            message.textContent = error.message;
        } finally {
            busy = false;
            button.disabled = false;
        }
    });
})();
