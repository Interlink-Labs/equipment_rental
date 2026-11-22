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
            const response = await fetch(`/equipment/?${query}`, { signal: request.signal });
            if (!response.ok) {
                throw new Error(`Ошибка загрузки: ${response.status}`);
            }
            const items = await response.json();
            if (request.signal.aborted) return;
            const search = searchInput.value.trim().toLocaleLowerCase('ru');
            const data = items.filter(item =>
                item.name.toLocaleLowerCase('ru').includes(search) ||
                item.inventory_number.toLocaleLowerCase('ru').includes(search)
            );

            loadingEl.style.display = 'none';

            if (data.length === 0) {
                emptyStateEl.style.display = 'block';
                return;
            }

            equipmentTable.style.display = 'table';
            equipmentList.innerHTML = '';

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
                actions.append(changeStatus, ' ', remove);
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
            showMessage(actionMessage, method === 'DELETE' ? 'Инструмент удалён' : 'Статус обновлён', 'success');
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

        const nameInput = document.getElementById('name');
        const invInput = document.getElementById('inv-number');
        const rateInput = document.getElementById('rate');

        const payload = {
            name: nameInput.value.trim(),
            inventory_number: invInput.value.trim(),
            daily_rate: parseFloat(rateInput.value)
        };

        try {
            const response = await fetch('/equipment/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (!response.ok) {
                // Если сервер вернул ошибку (например, 400 при дубликате)
                throw new Error(result.detail || 'Ошибка сохранения');
            }

            // Успех! Очищаем форму и показываем сообщение
            showMessage(formMessage, `✅ Инструмент "${result.name}" успешно добавлен!`, 'success');
            addForm.reset();
            loadEquipment(); // Перезагружаем список
        } catch (error) {
            showMessage(formMessage, `❌ Ошибка: ${error.message}`, 'error');
        }
    });

    // Кнопка обновления
    btnRefresh.addEventListener('click', () => {
        loadEquipment();
    });
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
