const telefoneInput = document.getElementById("telefone");

const telefoneMask = (value) => {
    return value.replace(/\D/g, '').replace(/^(\d{2})(\d)/, '($1) $2').replace(/(\d{5})(\d)/, '$1-$2');
}

telefoneInput.addEventListener("input", (e) => {
    e.target.value = telefoneMask(e.target.value);
});
    