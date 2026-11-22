// static/app.js — Логика фронтенда на чистом JavaScript
// Зона ответственности: Пара 4 (ветка feature/frontend)

document.addEventListener('DOMContentLoaded', () => {
    const equipmentList = document.getElementById('equipment-list');
    const equipmentTable = document.getElementById('equipment-table');
    const loadingEl = document.getElementById('loading');
    const emptyStateEl = document.getElementById('empty-state');
    const addForm = document.getElementById('add-equipment-form');
    const formMessage = document.getElementById('form-message');
    const btnRefresh = document.getElementById('btn-refresh');
    const statusFilter = document.getElementById('equipment-status-filter');
    const searchInput = document.getElementById('equipment-search');
    const actionMessage = document.getElementById('equipment-action-message');
    const sortSelect = document.getElementById('equipment-sort');
    const submitButton = document.getElementById('btn-submit');
    const cancelEdit = document.getElementById('equipment-cancel');
    let editingId = null;
    let equipmentRequest;
    let searchTimer;

    // Функция загрузки списка оборудования с бэкенда (GET /equipment/)
    async function loadEquipment() {
        equipmentRequest?.abort();
        const request = new AbortController();
        equipmentRequest = request;
        loadingEl.style.display = 'block';
        equipmentTable.style.display = 'none';
        emptyStateEl.style.display = 'none';

        try {
            const query = new URLSearchParams();
            if (statusFilter.value) {
                query.set('status_filter', statusFilter.value);
            }
            query.set('query', searchInput.value.trim());
            query.set('sort', sortSelect.value);
            const response = await fetch(`/equipment/?${query}`, { signal: request.signal });
            if (!response.ok) {
                throw new Error(`Ошибка загрузки: ${response.status}`);
            }
            const items = await response.json();
            if (request.signal.aborted) return;
            const data = items;

            loadingEl.style.display = 'none';
            equipmentList.replaceChildren();

            if (data.length === 0) {
                emptyStateEl.style.display = 'block';
                return;
            }

            equipmentTable.style.display = 'table';

            data.forEach(item => {
                const tr = document.createElement('tr');

                // Определяем цвет и текст бейджа для статуса
                let badgeClass = 'badge-available';
                let statusText = 'Доступен';

                if (item.status === 'RENTED') {
                    badgeClass = 'badge-rented';
                    statusText = 'В аренде';
                } else if (item.status === 'REPAIR') {
                    badgeClass = 'badge-repair';
                    statusText = 'В ремонте';
                }

                tr.innerHTML = `
                    <td><strong>#${item.id}</strong></td>
                    <td><code>${escapeHtml(item.inventory_number)}</code></td>
                    <td>${escapeHtml(item.name)}</td>
                    <td>${item.daily_rate.toFixed(2)} ₽</td>
                    <td><span class="badge ${badgeClass}">${statusText}</span></td>
                `;
                const actions = tr.insertCell();
                const edit = document.createElement('button');
                edit.type = 'button';
                edit.className = 'btn btn-secondary';
                edit.textContent = 'Изменить';
                edit.addEventListener('click', () => {
                    editingId = item.id;
                    document.getElementById('name').value = item.name;
                    document.getElementById('inv-number').value = item.inventory_number;
                    document.getElementById('inv-number').disabled = true;
                    document.getElementById('rate').value = item.daily_rate;
                    submitButton.textContent = 'Сохранить изменения';
                    addForm.closest('section').querySelector('h2').textContent = 'Редактировать оборудование';
                    cancelEdit.hidden = false;
                    document.getElementById('name').focus();
                });
                const changeStatus = document.createElement('button');
                changeStatus.type = 'button';
                changeStatus.className = 'btn btn-secondary';
                changeStatus.textContent = 'Изменить статус';
                changeStatus.disabled = item.status === 'RENTED';
                changeStatus.addEventListener('click', () => {
                    const nextStatus = item.status === 'REPAIR' ? 'AVAILABLE' : 'REPAIR';
                    updateEquipment(item.id, 'PUT', { status: nextStatus }, actions);
                });

                const remove = document.createElement('button');
                remove.type = 'button';
                remove.className = 'btn btn-secondary';
                remove.textContent = 'Удалить';
                remove.addEventListener('click', () => {
                    if (window.confirm(`Удалить инструмент «${item.name}»?`)) {
                        updateEquipment(item.id, 'DELETE', undefined, actions);
                    }
                });
                actions.append(edit, ' ', changeStatus, ' ', remove);
                equipmentList.appendChild(tr);
            });
        } catch (error) {
            if (request.signal.aborted) return;
            loadingEl.style.display = 'none';
            showMessage(formMessage, `Не удалось загрузить данные: ${error.message}`, 'error');
        }
    }

    async function updateEquipment(id, method, payload, actions) {
        const buttons = Array.from(actions.querySelectorAll('button:not(:disabled)'));
        buttons.forEach(button => { button.disabled = true; });
        try {
            const options = { method };
            if (payload) {
                options.headers = { 'Content-Type': 'application/json' };
                options.body = JSON.stringify(payload);
            }
            const response = await fetch(`/equipment/${id}`, options);
            if (!response.ok) {
                const result = await response.json().catch(() => ({}));
                throw new Error(typeof result.detail === 'string' ? result.detail : `Ошибка ${response.status}`);
            }
            if (method === 'DELETE' && editingId === id) addForm.reset();
            showMessage(actionMessage, method === 'DELETE' ? 'Оборудование удалено' : 'Статус обновлён', 'success');
            await loadEquipment();
        } catch (error) {
            showMessage(actionMessage, error.message, 'error');
        } finally {
            buttons.forEach(button => { button.disabled = false; });
        }
    }

    // Обработка отправки формы добавления (POST /equipment/)
    addForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (submitButton.disabled) return;

        const nameInput = document.getElementById('name');
        const invInput = document.getElementById('inv-number');
        const rateInput = document.getElementById('rate');

        const payload = {
            name: nameInput.value.trim(),
            inventory_number: invInput.value.trim(),
            daily_rate: parseFloat(rateInput.value)
        };

        const updating = editingId !== null;
        if (updating) delete payload.inventory_number;
        submitButton.disabled = true;
        try {
            const response = await fetch(updating ? '/equipment/' + editingId : '/equipment/', {
                method: updating ? 'PUT' : 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (!response.ok) {
                // Если сервер вернул ошибку (например, 400 при дубликате)
                throw new Error(typeof result.detail === 'string' ? result.detail : result.detail?.map(item => item.msg).join('. ') || 'Ошибка сохранения');
            }

            // Успех! Очищаем форму и показываем сообщение
            showMessage(formMessage, updating ? 'Изменения сохранены.' : 'Оборудование добавлено.', 'success');
            addForm.reset();
            loadEquipment(); // Перезагружаем список
        } catch (error) {
            showMessage(formMessage, `❌ Ошибка: ${error.message}`, 'error');
        } finally {
            submitButton.disabled = false;
        }
    });

    // Кнопка обновления
    btnRefresh.addEventListener('click', () => {
        loadEquipment();
    });
    addForm.addEventListener('reset', () => {
        editingId = null;
        document.getElementById('inv-number').disabled = false;
        submitButton.textContent = 'Добавить в каталог';
        addForm.closest('section').querySelector('h2').textContent = 'Добавить оборудование';
        cancelEdit.hidden = true;
    });
    sortSelect.addEventListener('change', loadEquipment);
    statusFilter.addEventListener('change', loadEquipment);
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(loadEquipment, 250);
    });

    // Вспомогательная функция для показа уведомлений
    function showMessage(element, text, type) {
        element.textContent = text;
        element.className = `message ${type}`;
        element.style.display = 'block';
        clearTimeout(element.messageTimer);
        element.messageTimer = setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }

    // Защита от XSS (экранирование спецсимволов)
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Первоначальная загрузка данных
    loadEquipment();
});
