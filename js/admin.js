function carregarVoluntarios() {
    const tabela = document.getElementById("tabelaVoluntarios");
    if (!tabela) return;

    const lista = JSON.parse(localStorage.getItem("voluntarios")) || [];

    tabela.innerHTML = "";

    lista.forEach((v, index) => {
        const tr = document.createElement("tr");

        const tdId = document.createElement("td");
        tdId.textContent = index + 1;

        const tdNome = document.createElement("td");
        tdNome.textContent = v.nome;

        const tdTelefone = document.createElement("td");
        tdTelefone.textContent = v.telefone;

        const tdOng = document.createElement("td");
        tdOng.textContent = v.ong;

        const tdAcoes = document.createElement("td");

        const btnExcluir = document.createElement("button");
        btnExcluir.textContent = "Excluir";
        btnExcluir.classList.add("btn-excluir");

        btnExcluir.addEventListener("click", () => excluir(v.id));

        const btnEditar = document.createElement("button");
        btnEditar.textContent = "Editar";
        btnEditar.classList.add("btn-editar");

        btnEditar.addEventListener("click", () => editar(v.id));

        btnExcluir.addEventListener("click", () => excluir(v.id));

        tdAcoes.appendChild(btnExcluir);
        tdAcoes.appendChild(btnEditar);

        tr.appendChild(tdId);
        tr.appendChild(tdNome);
        tr.appendChild(tdTelefone);
        tr.appendChild(tdOng);
        tr.appendChild(tdAcoes);

        tabela.appendChild(tr);
    });
}

function excluir(id) {
    let lista = JSON.parse(localStorage.getItem("voluntarios")) || [];

    lista = lista.filter(v => v.id !== id);

    localStorage.setItem("voluntarios", JSON.stringify(lista));

    carregarVoluntarios();
}

function editar(id) {
    const lista = JSON.parse(localStorage.getItem("voluntarios")) || [];
    const voluntario = lista.find(v => v.id === id);

    if (voluntario) {
        const nome = prompt("Digite o novo nome:", voluntario.nome);
        const telefone = prompt("Digite o novo telefone:", voluntario.telefone);
        const ong = prompt("Digite a nova ONG:", voluntario.ong);

        if (nome && telefone && ong) {
            voluntario.nome = nome;
            voluntario.telefone = telefone;
            voluntario.ong = ong;

            localStorage.setItem("voluntarios", JSON.stringify(lista));
            carregarVoluntarios();
        }
    }
}

document.addEventListener("DOMContentLoaded", carregarVoluntarios);

const btn = document.querySelector(".menuh");
const menu = document.querySelector(".menu-mobile");

btn.addEventListener("click", (e) => {
  menu.classList.toggle("ativo");
  document.body.classList.toggle("no-scroll");

  e.stopPropagation(); // evita conflito com o clique fora
});

// clique fora
document.addEventListener("click", (e) => {
  const clicouDentroMenu = menu.contains(e.target);
  const clicouNoBotao = btn.contains(e.target);

  if (!clicouDentroMenu && !clicouNoBotao) {
    menu.classList.remove("ativo");
    document.body.classList.remove("no-scroll");
  }
});