let fv;

document.addEventListener('DOMContentLoaded', function () {
    fv = FormValidation.formValidation(document.getElementById('frmForm'), {
        locale: 'es_ES',
        localization: FormValidation.locales.es_ES,
        plugins: {
            trigger: new FormValidation.plugins.Trigger(),
            submitButton: new FormValidation.plugins.SubmitButton(),
            bootstrap: new FormValidation.plugins.Bootstrap(),
            icon: new FormValidation.plugins.Icon({
                valid: 'fa fa-check',
                invalid: 'fa fa-times',
                validating: 'fa fa-refresh',
            }),
        },
        fields: {
            old_password: {
                validators: {
                    notEmpty: { message: 'Ingrese su contraseña actual' },
                },
            },
            new_password: {
                validators: {
                    notEmpty: { message: 'Ingrese una nueva contraseña' },
                    stringLength: { min: 6, message: 'La contraseña debe tener al menos 6 caracteres' },
                },
            },
            new_password_confirm: {
                validators: {
                    notEmpty: { message: 'Confirme la nueva contraseña' },
                    identical: {
                        compare: function () {
                            return fv.form.querySelector('[name="new_password"]').value;
                        },
                        message: 'Las contraseñas no coinciden',
                    },
                },
            },
        },
    }).on('core.form.valid', function () {
        submit_formdata_with_ajax_form(fv);
    });
});
