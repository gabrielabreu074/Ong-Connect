async function carregarVoluntarios() {
    const tabela = document.getElementById("tabelaVoluntarios");
    if (!tabela) return;

    try {
        const response = await fetch('/api/voluntarios');
        const lista = await response.json();

        tabela.innerHTML = "";

        lista.forEach((v, index) => {
            const tr = document.createElement("tr");

            tr.innerHTML = `
                <td>${index + 1}</td>
                <td>${v.nome}</td>
                <td>${v.telefone}</td>
                <td>${v.ong}</td>
                <td>
                    <button class="btn-editar" data-id="${v.id}">Editar</button>
                    <button class="btn-excluir" data-id="${v.id}">Excluir</button>
                </td>
            `;

            tabela.appendChild(tr);
        });

        // Adiciona os eventos aos botões depois que a tabela é preenchida
        document.querySelectorAll('.btn-excluir').forEach(btn => {
            btn.addEventListener('click', () => excluir(btn.dataset.id));
        });

        document.querySelectorAll('.btn-editar').forEach(btn => {
            btn.addEventListener('click', () => editar(btn.dataset.id));
        });

    } catch (error) {
        console.error('Erro ao carregar voluntários:', error);
    }
}

async function excluir(id) {
    if (!confirm('Tem certeza que deseja excluir este voluntário?')) return;

    try {
        const response = await fetch(`/api/voluntarios/${id}`, { method: 'DELETE' });
        if (response.ok) {
            carregarVoluntarios();
        } else {
            alert('Erro ao excluir voluntário.');
        }
    } catch (error) {
        alert('Erro de conexão.');
    }
}

async function editar(id) {
    // Busca os dados atuais do voluntário
    const responseGet = await fetch('/api/voluntarios');
    const lista = await responseGet.json();
    const voluntario = lista.find(v => v.id == id);

    if (!voluntario) {
        alert('Voluntário não encontrado.');
        return;
    }

    const nome = prompt("Digite o novo nome:", voluntario.nome);
    const telefone = prompt("Digite o novo telefone:", voluntario.telefone);
    const ong = prompt("Digite a nova ONG:", voluntario.ong);

    if (nome && telefone && ong) {
        const dadosAtualizados = {
            nome,
            email: voluntario.email,   // Mantém o email original
            telefone,
            ong,
            mensagem: voluntario.mensagem
        };

        try {
            const response = await fetch(`/api/voluntarios/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dadosAtualizados)
            });

            if (response.ok) {
                carregarVoluntarios();
            } else {
                const erro = await response.json();
                alert('Erro ao atualizar: ' + erro.erro);
            }
        } catch (error) {
            alert('Erro de conexão.');
        }
    }
}

// Carrega a lista ao abrir a página
document.addEventListener("DOMContentLoaded", carregarVoluntarios);

// ----- Mobile menu (mantenha o código existente igual) -----
const btn = document.querySelector(".menuh");
const menu = document.querySelector(".menu-mobile");

btn.addEventListener("click", (e) => {
    menu.classList.toggle("ativo");
    document.body.classList.toggle("no-scroll");
    e.stopPropagation();
});

document.addEventListener("click", (e) => {
    const clicouDentroMenu = menu.contains(e.target);
    const clicouNoBotao = btn.contains(e.target);

    if (!clicouDentroMenu && !clicouNoBotao) {
        menu.classList.remove("ativo");
        document.body.classList.remove("no-scroll");
    }
});