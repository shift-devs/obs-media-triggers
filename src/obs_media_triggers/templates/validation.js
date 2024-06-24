window.addEventListener('load', function () {
  'use strict'
  console.debug("Page was loaded! Continuing form validation...")
  var forms = document.querySelectorAll('.needs-validation')
  console.debug("Found " + forms.length + " forms to validate on this page.")

  Array.prototype.slice.call(forms)
    .forEach(function (form) {
      form.addEventListener('submit', function (event) {
        if (!form.checkValidity()) {
          event.preventDefault()
          event.stopPropagation()
        }
        form.classList.add('was-validated')
      }, false)
      console.debug("Event listener added for " + form)
    })
})