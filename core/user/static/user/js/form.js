document.addEventListener('DOMContentLoaded', function () {
    new JustValidate('#frmForm', {
        errorFieldCssClass: 'is-invalid',
        errorLabelCssClass: 'invalid-feedback',
        focusInvalidField: true,
    })
        .addField('[name="username"]', [
            { rule: 'required', errorMessage: 'Ingrese un usuario' },
            { rule: 'minLength', value: 3, errorMessage: 'El usuario debe tener al menos 3 caracteres' },
            {
                validator: (value) => () =>
                    value
                        ? fetch(pathname, {
                              method: 'POST',
                              headers: { 'X-CSRFToken': csrftoken },
                              body: new URLSearchParams({ username: value, pattern: 'username', action: 'validate_data' }),
                          })
                              .then((r) => r.json())
                              .then((d) => Boolean(d.valid))
                        : Promise.resolve(true),
                errorMessage: 'Ya se encuentra registrado',
            },
        ])
        .addField('[name="email"]', [
            { rule: 'required', errorMessage: 'Ingrese un correo' },
            { rule: 'email', errorMessage: 'Ingrese un correo válido' },
            {
                validator: (value) => () =>
                    value
                        ? fetch(pathname, {
                              method: 'POST',
                              headers: { 'X-CSRFToken': csrftoken },
                              body: new URLSearchParams({ email: value, pattern: 'email', action: 'validate_data' }),
                          })
                              .then((r) => r.json())
                              .then((d) => Boolean(d.valid))
                        : Promise.resolve(true),
                errorMessage: 'Ya se encuentra registrado',
            },
        ])
        .addField('[name="dni"]', [
            { rule: 'required', errorMessage: 'Ingrese la cédula' },
            {
                validator: (value) => () =>
                    value
                        ? fetch(pathname, {
                              method: 'POST',
                              headers: { 'X-CSRFToken': csrftoken },
                              body: new URLSearchParams({ dni: value, pattern: 'dni', action: 'validate_data' }),
                          })
                              .then((r) => r.json())
                              .then((d) => Boolean(d.valid))
                        : Promise.resolve(true),
                errorMessage: 'Ya se encuentra registrado',
            },
        ])
        .onSuccess(function (event) {
            submit_formdata_with_ajax_form(event.target);
        });
});
