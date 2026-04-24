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

const form = document.getElementById("volunteerForm");

form.addEventListener("submit", (e) => {
    e.preventDefault();

    const nome = document.getElementById("nome").value;
    const email = document.getElementById("email").value;
    const telefone = document.getElementById("telefone").value;
    const ong = document.getElementById("ongs").value;
    const mensagem = document.getElementById("mensagem").value;

    const voluntario = {
        id: Date.now(),
        nome,
        email,
        telefone,
        ong,
        mensagem
    };

    let lista = JSON.parse(localStorage.getItem("voluntarios")) || [];

    lista.push(voluntario);

    localStorage.setItem("voluntarios", JSON.stringify(lista));

    mostrarAlerta("Cadastro realizado com sucesso!");

    form.reset();
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



//admin//
function carregarVoluntarios() {
    const tabela = document.getElementById("tabelaVoluntarios");
    const lista = JSON.parse(localStorage.getItem("voluntarios")) || [];

    tabela.innerHTML = "";

    lista.forEach((v, index) => {
        const tr = document.createElement("tr");

        tr.innerHTML = `
            <td>${index + 1}</td>
            <td>${v.nome}</td>
            <td>${v.telefone}</td>
            <td>${v.ong}</td>
            <td>
                <button onclick="excluir(${v.id})">Excluir</button>
            </td>
        `;

        tabela.appendChild(tr);
    });
}

function excluir(id) {
    let lista = JSON.parse(localStorage.getItem("voluntarios")) || [];

    lista = lista.filter(v => v.id !== id);

    localStorage.setItem("voluntarios", JSON.stringify(lista));

    carregarVoluntarios();
}

carregarVoluntarios();