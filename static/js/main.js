// Bootstrap 5 & AgroDirect Frontend Validation & Back-Button Protection JavaScript

document.addEventListener('DOMContentLoaded', function () {
    // 1. Browser Back-Forward Cache (bfcache) Security Handler
    window.addEventListener('pageshow', function (event) {
        if (event.persisted || (window.performance && window.performance.navigation.type === 2)) {
            // Force page reload to re-verify authentication and cache control
            window.location.reload();
        }
    });

    // 2. Client-Side Form Validation for all forms with novalidate attribute
    const forms = document.querySelectorAll('.needs-validation');

    Array.from(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            let isValid = form.checkValidity();

            // Password confirmation check if present
            const password = form.querySelector('input[name="password"]');
            const confirmPassword = form.querySelector('input[name="confirm_password"]');
            if (password && confirmPassword) {
                if (password.value !== confirmPassword.value) {
                    confirmPassword.setCustomValidity("Passwords do not match.");
                    isValid = false;
                } else {
                    confirmPassword.setCustomValidity("");
                }
            }

            // Phone number regex check if present
            const phoneInput = form.querySelector('input[name="phone_number"]');
            if (phoneInput && phoneInput.value) {
                const cleanPhone = phoneInput.value.replace(/[\s\-\+\(\)]/g, '');
                if (!/^\d{10,15}$/.test(cleanPhone)) {
                    phoneInput.setCustomValidity("Please enter a valid 10-15 digit phone number.");
                    isValid = false;
                } else {
                    phoneInput.setCustomValidity("");
                }
            }

            if (!isValid) {
                event.preventDefault();
                event.stopPropagation();
            }

            form.classList.add('was-validated');
        }, false);

        // Real-time field validation feedback on blur/input
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(function (input) {
            input.addEventListener('input', function () {
                if (input.checkValidity()) {
                    input.classList.remove('is-invalid');
                    input.classList.add('is-valid');
                } else {
                    input.classList.remove('is-valid');
                    input.classList.add('is-invalid');
                }
            });
        });
    });
});
