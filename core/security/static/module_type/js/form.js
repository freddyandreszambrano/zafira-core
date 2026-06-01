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
            name: {
                validators: {
                    notEmpty: { message: 'Ingrese un nombre' },
                    stringLength: { min: 2 },
                    remote: {
                        url: pathname,
                        data: () => ({
                            name: fv.form.querySelector('[name="name"]').value,
                            pattern: 'name',
                            action: 'validate_data',
                        }),
                        message: 'El nombre ya se encuentra registrado',
                        method: 'POST',
                        headers: { 'X-CSRFToken': csrftoken },
                    },
                },
            },
        },
    }).on('core.form.valid', function () {
        submit_formdata_with_ajax_form(fv);
    });
});
