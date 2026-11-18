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

    // ==================== АРЕНДЫ И БРОНИ ====================

// 1. Загружаем оборудование и клиентов для выпадающих списков и для отображения имён
let equipmentMap = {};   // id -> name
let clientMap = {};      // id -> full_name

async function loadEquipmentAndClientsForRentals() {
  try {
    const [eqRes, clRes] = await Promise.all([
      fetch('/equipment/'),
      fetch('/clients/')          // предполагается, что эндпоинт GET /clients/ существует
    ]);

    if (!eqRes.ok) throw new Error('Не удалось загрузить оборудование');
    if (!clRes.ok) throw new Error('Не удалось загрузить клиентов');

    const equipment = await eqRes.json();
    const clients = await clRes.json();

    equipmentMap = Object.fromEntries(equipment.map(e => [e.id, e.name]));
    clientMap = Object.fromEntries(clients.map(c => [c.id, c.full_name]));

    const rentalEqSelect = document.getElementById('rental-equipment');
    const bookingEqSelect = document.getElementById('booking-equipment');
    const rentalClientSelect = document.getElementById('rental-client');
    const bookingClientSelect = document.getElementById('booking-client');

    // очищаем selects
    [rentalEqSelect, bookingEqSelect, rentalClientSelect, bookingClientSelect].forEach(sel => {
      if (sel) sel.innerHTML = '';
    });

    equipment.forEach(e => {
      const label = `${e.name} (ID ${e.id})`;
      if (rentalEqSelect) rentalEqSelect.add(new Option(label, e.id));
      if (bookingEqSelect) bookingEqSelect.add(new Option(label, e.id));
    });

    clients.forEach(c => {
      const label = `${c.full_name} (ID ${c.id})`;
      if (rentalClientSelect) rentalClientSelect.add(new Option(label, c.id));
      if (bookingClientSelect) bookingClientSelect.add(new Option(label, c.id));
    });
  } catch (err) {
    console.warn('Не удалось подготовить списки для аренд:', err.message);
  }
}

// 2. Загрузка и отрисовка таблицы аренд
async function loadRentals() {
  const loadingEl = document.getElementById('rentals-loading');
  const tableEl = document.getElementById('rentals-table');
  const emptyEl = document.getElementById('rentals-empty');
  const tbody = document.getElementById('rentals-list');

  if (!loadingEl || !tableEl || !emptyEl || !tbody) return; // секция аренд не добавлена

  loadingEl.style.display = 'block';
  tableEl.style.display = 'none';
  emptyEl.style.display = 'none';

  try {
    const res = await fetch('/rentals/');
    if (!res.ok) throw new Error(`Ошибка загрузки аренд: ${res.status}`);
    const rentals = await res.json();

    loadingEl.style.display = 'none';

    if (rentals.length === 0) {
      emptyEl.style.display = 'block';
      return;
    }

    tableEl.style.display = 'table';
    tbody.innerHTML = '';

    rentals.forEach(r => {
      const tr = document.createElement('tr');

      // Бонус: показываем название инструмента и ФИО клиента вместо ID
      const equipmentName = equipmentMap[r.equipment_id] ?? `ID ${r.equipment_id}`;
      const clientName = clientMap[r.client_id] ?? `ID ${r.client_id}`;

      const statusText =
        r.status === 'ACTIVE' ? 'Активна' :
        r.status === 'RETURNED' ? 'Возвращена' :
        r.status === 'RESERVED' ? 'Забронирована' : r.status;

      tr.innerHTML = `
        <td>${r.id}</td>
        <td>${escapeHtml(equipmentName)}</td>
        <td>${escapeHtml(clientName)}</td>
        <td>${r.start_date} — ${r.end_date}</td>
        <td>${r.total_cost.toFixed(2)} ₽</td>
        <td>${statusText}</td>
        <td></td>
      `;

      const actionsCell = tr.lastElementChild;

      // Кнопка «Вернуть» только для активных аренд
      if (r.status === 'ACTIVE') {
        const returnBtn = document.createElement('button');
        returnBtn.type = 'button';
        returnBtn.className = 'btn btn-secondary';
        returnBtn.textContent = 'Вернуть';
        returnBtn.addEventListener('click', () => handleReturn(r.id));
        actionsCell.appendChild(returnBtn);
      }

      tbody.appendChild(tr);
    });
  } catch (err) {
    loadingEl.style.display = 'none';
    console.error(err);
    alert(`Не удалось загрузить аренды: ${err.message}`);
  }
}

// 3. Возврат оборудования
async function handleReturn(rentalId) {
  if (!window.confirm('Подтвердить возврат оборудования?')) return;

  try {
    const res = await fetch(`/rentals/${rentalId}/return`, {
      method: 'POST'
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Ошибка возврата: ${res.status}`);
    }

    // Обновляем таблицу аренд и список оборудования (статус изменился)
    await loadRentals();
    await loadEquipment();   // эта функция уже есть в app.js
  } catch (err) {
    alert(err.message);
  }
}

// 4. Общая отправка формы аренды/брони
async function submitRental(url, payload, messageElId) {
  const msgEl = document.getElementById(messageElId);
  if (!msgEl) return;

  msgEl.textContent = '';
  msgEl.className = 'message';

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Ошибка: ${res.status}`);
    }

    msgEl.textContent = '✅ Успешно оформлено!';
    msgEl.classList.add('success');
    msgEl.style.display = 'block';

    // Обновляем таблицу аренд и оборудование (мог измениться статус)
    await loadRentals();
    await loadEquipment();

    // Сбрасываем форму
    const form = msgEl.closest('form');
    if (form) form.reset();
  } catch (err) {
    msgEl.textContent = `❌ ${err.message}`;
    msgEl.classList.add('error');
    msgEl.style.display = 'block';
  }
}

// 5. Обработчики форм
const rentalForm = document.getElementById('rental-form');
if (rentalForm) {
  rentalForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      equipment_id: Number(document.getElementById('rental-equipment').value),
      client_id: Number(document.getElementById('rental-client').value),
      start_date: document.getElementById('rental-start').value,
      end_date: document.getElementById('rental-end').value
    };
    await submitRental('/rentals/', payload, 'rental-message');
  });
}

const bookingForm = document.getElementById('booking-form');
if (bookingForm) {
  bookingForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      equipment_id: Number(document.getElementById('booking-equipment').value),
      client_id: Number(document.getElementById('booking-client').value),
      start_date: document.getElementById('booking-start').value,
      end_date: document.getElementById('booking-end').value
    };
    await submitRental('/rentals/book', payload, 'booking-message');
  });
}

// 6. Первоначальная загрузка данных для аренд
(async () => {
  await loadEquipmentAndClientsForRentals();
  await loadRentals();
})();

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
