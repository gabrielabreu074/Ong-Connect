// Máscara de telefone
const telefoneInput = document.getElementById("telefone");

const telefoneMask = (value) => {
    return value
        .replace(/\D/g, '')
        .replace(/^(\d{2})(\d)/, '($1) $2')
        .replace(/(\d{5})(\d)/, '$1-$2');
};

telefoneInput.addEventListener("input", (e) => {
    e.target.value = telefoneMask(e.target.value);
});

// Envio do formulário
const form = document.getElementById("volunteerForm");

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const nome = document.getElementById("nome").value.trim();
    const email = document.getElementById("email").value.trim();
    const telefone = document.getElementById("telefone").value.trim();
    const ong = document.getElementById("ongs").value;
    const mensagem = document.getElementById("mensagem").value.trim();

    const voluntario = {
        nome,
        email,
        telefone,
        ong,
        mensagem
    };

    try {
        const response = await fetch('/api/voluntarios', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(voluntario)
        });

        if (response.ok) {
            mostrarAlerta("Cadastro realizado com sucesso!");
            form.reset();
        } else {
            const erro = await response.json();
            mostrarAlerta("Erro: " + (erro.erro || "Falha ao cadastrar."));
        }
    } catch (error) {
        mostrarAlerta("Erro de conexão com o servidor.");
    }
});

function mostrarAlerta(texto) {
    const alerta = document.createElement("div");
    alerta.innerText = texto;
    alerta.style.position = "fixed";
    alerta.style.top = "20px";
    alerta.style.right = "20px";
    alerta.style.backgroundColor = "#22c55e";
    alerta.style.color = "#fff";
    alerta.style.padding = "15px 20px";
    alerta.style.borderRadius = "8px";
    alerta.style.boxShadow = "0 0 10px rgba(0,0,0,0.2)";
    alerta.style.zIndex = "9999";

    document.body.appendChild(alerta);

    setTimeout(() => {
        alerta.remove();
    }, 3000);
}