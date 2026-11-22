(() => {
    const originalFetch = window.fetch.bind(window);
    const state = document.getElementById('auth-state');
    let token = sessionStorage.getItem('rental-token');
    window.rentalUser = null;
    window.fetch = (input, options = {}) => {
        const request = new Request(input, options);
        const url = new URL(request.url);
        if (token && url.origin === location.origin && /^\/(rentals|clients|employers|equipment|auth)(\/|$)/.test(url.pathname)) {
            request.headers.set('Authorization', 'Bearer ' + token);
        }
        return originalFetch(request).then(response => {
            if (response.status === 401 && token && url.origin === location.origin) {
                token = null;
                sessionStorage.removeItem('rental-token');
                document.body.classList.remove('signed-in');
                state.textContent = 'Срок входа истёк. Войдите снова.';
            }
            return response;
        });
    };

    window.rentalSession = (async () => {
        if (!token) return null;
        try {
            const response = await fetch('/auth/me');
            if (!response.ok) throw new Error();
            const user = await response.json();
            window.rentalUser = user;
            document.body.classList.add('signed-in');
            document.getElementById('auth-login').hidden = true;
            document.getElementById('auth-register').closest('details').hidden = true;
            document.getElementById('auth-logout').hidden = false;
            state.textContent = 'Вы вошли как ' + user.username;
            document.getElementById('admin-title').textContent = user.role === 'ADMIN' ? 'Управление арендой' : 'Мои аренды и брони';
            document.getElementById('account-role').textContent = user.role === 'ADMIN' ? 'Администратор' : 'Мои аренды';
            document.querySelectorAll('[data-admin-only]').forEach(element => { element.hidden = user.role !== 'ADMIN'; });
            return user;
        } catch {
            token = null;
            sessionStorage.removeItem('rental-token');
            return null;
        }
    })();

    async function login(username, password) {
        const response = await fetch('/auth/login', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Не удалось войти');
        sessionStorage.setItem('rental-token', data.access_token);
        location.reload();
    }

    ['login', 'register'].forEach(action => {
        const form = document.getElementById('auth-' + action);
        form.addEventListener('submit', async event => {
            event.preventDefault();
            const button = form.querySelector('button');
            button.disabled = true;
            const data = Object.fromEntries(new FormData(form));
            try {
                if (action === 'register') {
                    const response = await fetch('/auth/registration', {
                        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
                    });
                    const result = await response.json();
                    if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Проверьте поля регистрации');
                }
                await login(data.username, data.password);
            } catch (error) {
                state.textContent = error.message;
                button.disabled = false;
            }
        });
    });
    document.getElementById('auth-logout').addEventListener('click', () => {
        sessionStorage.removeItem('rental-token');
        location.reload();
    });
})();
