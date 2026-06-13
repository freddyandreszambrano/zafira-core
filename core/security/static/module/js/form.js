document.addEventListener('DOMContentLoaded', function () {
    new JustValidate('#frmForm', {
        errorFieldCssClass: 'is-invalid',
        errorLabelCssClass: 'invalid-feedback',
        focusInvalidField: true,
    })
        .addField('[name="name"]', [
            { rule: 'required', errorMessage: 'Ingrese un nombre' },
            { rule: 'minLength', value: 2, errorMessage: 'El nombre debe tener al menos 2 caracteres' },
        ])
        .addField('[name="url"]', [
            { rule: 'required', errorMessage: 'Ingrese la dirección del módulo' },
            {
                validator: (value) => () =>
                    value
                        ? fetch(pathname, {
                              method: 'POST',
                              headers: { 'X-CSRFToken': csrftoken },
                              body: new URLSearchParams({ url: value, pattern: 'url', action: 'validate_data' }),
                          })
                              .then((r) => r.json())
                              .then((d) => Boolean(d.valid))
                        : Promise.resolve(true),
                errorMessage: 'La dirección ya se encuentra registrada',
            },
        ])
        .onSuccess(function (event) {
            submit_formdata_with_ajax_form(event.target);
        });
});
