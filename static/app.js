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

    // Функция загрузки списка оборудования с бэкенда (GET /equipment/)
    async function loadEquipment() {
        loadingEl.style.display = 'block';
        equipmentTable.style.display = 'none';
        emptyStateEl.style.display = 'none';

        try {
            const response = await fetch('/equipment/');
            if (!response.ok) {
                throw new Error(`Ошибка загрузки: ${response.status}`);
            }
            const data = await response.json();

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
                equipmentList.appendChild(tr);
            });
        } catch (error) {
            loadingEl.style.display = 'none';
            showMessage(formMessage, `Не удалось загрузить данные: ${error.message}`, 'error');
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

    // Вспомогательная функция для показа уведомлений
    function showMessage(element, text, type) {
        element.textContent = text;
        element.className = `message ${type}`;
        setTimeout(() => {
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
