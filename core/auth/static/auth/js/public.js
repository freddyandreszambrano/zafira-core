(function () {
    function initPasswordToggles() {
        document.querySelectorAll('[data-password-toggle]').forEach(function (button) {
            var target = document.querySelector(button.getAttribute('data-password-toggle'));
            if (!target) return;

            button.addEventListener('click', function () {
                var visible = target.type === 'text';
                target.type = visible ? 'password' : 'text';
                button.setAttribute('aria-pressed', String(!visible));
                button.innerHTML = visible ? '<i class="fas fa-eye"></i>' : '<i class="fas fa-eye-slash"></i>';
            });
        });
    }

    function passwordScore(value) {
        var score = 0;
        if (value.length >= 8) score += 1;
        if (/[A-Z]/.test(value) && /[a-z]/.test(value)) score += 1;
        if (/\d/.test(value)) score += 1;
        if (/[^A-Za-z0-9]/.test(value)) score += 1;
        return score;
    }

    function initStrengthMeter() {
        var input = document.querySelector('[data-password-strength]');
        var meter = document.querySelector('[data-strength-meter]');
        if (!input || !meter) return;

        input.addEventListener('input', function () {
            meter.setAttribute('data-score', String(passwordScore(input.value)));
        });
    }

    function initPasswordMatch() {
        var message = document.querySelector('[data-password-match]');
        if (!message) return;

        var selectors = message.getAttribute('data-password-match').split(',');
        var password = document.querySelector(selectors[0]);
        var confirmation = document.querySelector(selectors[1]);
        if (!password || !confirmation) return;

        function update() {
            message.classList.remove('is-ok', 'is-bad');
            if (!confirmation.value) {
                message.textContent = '';
                return;
            }
            if (password.value === confirmation.value) {
                message.textContent = 'Las contraseñas coinciden.';
                message.classList.add('is-ok');
                return;
            }
            message.textContent = 'Las contraseñas no coinciden.';
            message.classList.add('is-bad');
        }

        password.addEventListener('input', update);
        confirmation.addEventListener('input', update);
    }

    function initThemeToggle() {
        var button = document.querySelector('[data-theme-toggle]');
        if (!button) return;

        button.addEventListener('click', function () {
            var isDark = document.documentElement.classList.toggle('dark');
            var theme = isDark ? 'dark' : 'light';
            localStorage.setItem('zafira-theme', theme);
            var meta = document.querySelector('meta[name="color-scheme"]');
            if (meta) meta.content = theme;
        });
    }

    function initSubmitState() {
        document.querySelectorAll('.auth-form').forEach(function (form) {
            form.addEventListener('submit', function () {
                var button = form.querySelector('.auth-button');
                if (!button) return;
                button.classList.add('is-loading');
                button.setAttribute('aria-busy', 'true');
            });
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        initThemeToggle();
        initPasswordToggles();
        initStrengthMeter();
        initPasswordMatch();
        initSubmitState();
    });
})();
