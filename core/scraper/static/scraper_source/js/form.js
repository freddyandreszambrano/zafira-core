document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('frmForm');
    const isCreate = (form?.dataset.action || 'add') === 'add';
    const splitUrls = value => (value.match(/https?:\/\/[^\s,;]+/gi) || []);
    const hasOnlyUrls = value => {
        const trimmed = (value || '').trim();
        if (!trimmed) return false;
        const remainder = trimmed.replace(/https?:\/\/[^\s,;]+/gi, '').replace(/[,;]/g, '').trim();
        return !remainder;
    };
    const hasValidUrlValue = value => {
        if (!hasOnlyUrls(value)) return false;
        return isCreate || splitUrls(value).length === 1;
    };

    new JustValidate('#frmForm', {
        errorFieldCssClass: 'is-invalid',
        errorLabelCssClass: 'invalid-feedback',
        focusInvalidField: true,
    })
        .addField('[name="name"]', [
            { rule: 'required', errorMessage: 'Ingrese un nombre' },
            { rule: 'minLength', value: 2, errorMessage: 'El nombre debe tener al menos 2 caracteres' },
            {
                validator: value => () =>
                    value
                        ? fetch(pathname, {
                              method: 'POST',
                              headers: { 'X-CSRFToken': csrftoken },
                              body: new URLSearchParams({ name: value, pattern: 'name', action: 'validate_data' }),
                          })
                              .then(r => r.json())
                              .then(d => Boolean(d.valid))
                        : Promise.resolve(true),
                errorMessage: 'El nombre ya se encuentra registrado',
            },
        ])
        .addField('[name="url"]', [
            { rule: 'required', errorMessage: 'Ingrese una URL' },
            {
                validator: value => hasValidUrlValue(value),
                errorMessage: 'Ingrese una URL valida',
            },
            {
                validator: value => () =>
                    value
                        ? Promise.all(splitUrls(value).map(url =>
                            fetch(pathname, {
                                method: 'POST',
                                headers: { 'X-CSRFToken': csrftoken },
                                body: new URLSearchParams({ url, pattern: 'url', action: 'validate_data' }),
                            })
                                .then(r => r.json())
                                .then(d => Boolean(d.valid))
                        )).then(results => results.every(Boolean))
                        : Promise.resolve(true),
                errorMessage: 'La URL ya se encuentra registrada',
            },
        ])
        .onSuccess(function (event) {
            submit_formdata_with_ajax_form(form || event.target);
        });
});
