document.addEventListener('DOMContentLoaded', function () {
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
            { rule: 'customRegexp', value: /^https?:\/\/.+/i, errorMessage: 'Ingrese una URL valida' },
            {
                validator: value => () =>
                    value
                        ? fetch(pathname, {
                              method: 'POST',
                              headers: { 'X-CSRFToken': csrftoken },
                              body: new URLSearchParams({ url: value, pattern: 'url', action: 'validate_data' }),
                          })
                              .then(r => r.json())
                              .then(d => Boolean(d.valid))
                        : Promise.resolve(true),
                errorMessage: 'La URL ya se encuentra registrada',
            },
        ])
        .onSuccess(function (event) {
            submit_formdata_with_ajax_form(event.target);
        });
});
