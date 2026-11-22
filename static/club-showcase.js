const stock = document.getElementById('club-stock');
const stockMessage = document.getElementById('club-stock-message');
const price = new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' });
let stockRequest;

async function loadClubStock() {
    stockRequest?.abort();
    const request = new AbortController();
    stockRequest = request;
    try {
        const response = await fetch('/equipment/?status_filter=AVAILABLE', { signal: request.signal });
        if (!response.ok) throw new Error('Catalog unavailable');
        const items = await response.json();
        if (request.signal.aborted) return;
        stock.replaceChildren(...items.map(item => {
            const card = document.createElement('li');
            const name = document.createElement('strong');
            const rate = document.createElement('span');
            name.textContent = item.name;
            rate.textContent = price.format(item.daily_rate) + ' / сутки';
            card.append(name, rate);
            return card;
        }));
        stock.hidden = items.length === 0;
        stockMessage.hidden = items.length > 0;
        stockMessage.textContent = 'Сейчас свободных позиций нет.';
    } catch {
        if (request.signal.aborted) return;
        stock.hidden = true;
        stockMessage.hidden = false;
        stockMessage.textContent = 'Не удалось загрузить доступное оборудование.';
    }
}

new MutationObserver(loadClubStock).observe(document.getElementById('equipment-list'), { childList: true });
loadClubStock();
