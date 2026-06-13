document.addEventListener('DOMContentLoaded', function () {
    new JustValidate('#frmForm', {
        errorFieldCssClass: 'is-invalid',
        errorLabelCssClass: 'invalid-feedback',
        focusInvalidField: true,
    })
        .addField('[name="old_password"]', [
            { rule: 'required', errorMessage: 'Ingrese su contraseña actual' },
        ])
        .addField('[name="new_password"]', [
            { rule: 'required', errorMessage: 'Ingrese una nueva contraseña' },
            { rule: 'minLength', value: 6, errorMessage: 'La contraseña debe tener al menos 6 caracteres' },
        ])
        .addField('[name="new_password_confirm"]', [
            { rule: 'required', errorMessage: 'Confirme la nueva contraseña' },
            {
                validator: (value, fields) => value === fields['[name="new_password"]'].elem.value,
                errorMessage: 'Las contraseñas no coinciden',
            },
        ])
        .onSuccess(function (event) {
            submit_formdata_with_ajax_form(event.target);
        });
});
