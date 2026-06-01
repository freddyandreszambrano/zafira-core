let fv;

function uniqueRemote(field) {
    return {
        url: pathname,
        data: () => ({
            [field]: fv.form.querySelector(`[name="${field}"]`).value,
            pattern: field,
            action: 'validate_data',
        }),
        message: 'Ya se encuentra registrado',
        method: 'POST',
        headers: { 'X-CSRFToken': csrftoken },
    };
}

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
            username: {
                validators: {
                    notEmpty: { message: 'Ingrese un usuario' },
                    stringLength: { min: 3 },
                    remote: uniqueRemote('username'),
                },
            },
            email: {
                validators: {
                    notEmpty: { message: 'Ingrese un email' },
                    emailAddress: { message: 'Email inválido' },
                    remote: uniqueRemote('email'),
                },
            },
            dni: {
                validators: {
                    notEmpty: { message: 'Ingrese la cédula' },
                    remote: uniqueRemote('dni'),
                },
            },
        },
    }).on('core.form.valid', function () {
        submit_formdata_with_ajax_form(fv);
    });
});
