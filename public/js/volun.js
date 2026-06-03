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

    const nome     = document.getElementById("nome").value.trim();
    const email    = document.getElementById("email").value.trim();
    const telefone = document.getElementById("telefone").value.trim();
    const ong      = document.getElementById("ongs").value;
    const mensagem = document.getElementById("mensagem").value.trim();

    const voluntario = { nome, email, telefone, ong, mensagem };

    try {
        const response = await fetch('/api/voluntarios', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(voluntario)
        });

        if (response.ok) {
            mostrarAlerta("✓ Cadastro realizado com sucesso!", "sucesso");
            form.reset();
        } else {
            const erro = await response.json();

            // Cadastro bloqueado pelo ML — mostra os motivos
            if (response.status === 422 && erro.ml?.motivos?.length > 0) {
                const lista = erro.ml.motivos.map(m => `• ${m}`).join('\n');
                mostrarAlerta(`Cadastro bloqueado:\n\n${lista}`, "erro", 8000);
            } else {
                mostrarAlerta("Erro: " + (erro.erro || "Falha ao cadastrar."), "erro");
            }
        }
    } catch (error) {
        mostrarAlerta("Erro de conexão com o servidor. Verifique se o servidor está rodando.", "erro");
    }
});

function mostrarAlerta(texto, tipo = "sucesso", duracao = 4000) {
    // Remove alerta anterior se existir
    const anterior = document.getElementById("alerta-ml");
    if (anterior) anterior.remove();

    const alerta = document.createElement("div");
    alerta.id = "alerta-ml";
    alerta.innerText = texto;

    Object.assign(alerta.style, {
        position:     "fixed",
        top:          "20px",
        right:        "20px",
        maxWidth:     "360px",
        backgroundColor: tipo === "sucesso" ? "#22c55e" : "#ef4444",
        color:        "#fff",
        padding:      "15px 20px",
        borderRadius: "8px",
        boxShadow:    "0 4px 12px rgba(0,0,0,0.2)",
        zIndex:       "9999",
        whiteSpace:   "pre-line",
        lineHeight:   "1.5",
        fontSize:     "14px",
    });

    document.body.appendChild(alerta);
    setTimeout(() => alerta.remove(), duracao);
}