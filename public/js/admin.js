async function carregarVoluntarios() {
    const tabela = document.getElementById("tabelaVoluntarios");
    if (!tabela) return;

    try {
        const response = await fetch('/api/voluntarios');
        const lista = await response.json();

        tabela.innerHTML = "";

        lista.forEach((v, index) => {
            const tr = document.createElement("tr");

            // Mensagem
            const temMensagem = v.mensagem && v.mensagem.trim() !== "";
            const previa = temMensagem
                ? (v.mensagem.length > 40 ? v.mensagem.substring(0, 40) + "…" : v.mensagem)
                : "<span class='sem-mensagem'>—</span>";
            const botaoVerMais = temMensagem && v.mensagem.length > 40
                ? `<button class="btn-ver-mensagem" data-mensagem="${encodeURIComponent(v.mensagem)}">Ver mais</button>`
                : "";

            // Score ML — converte score_ml (prob de ser FALSO) em % de veracidade
            const scoreCell = renderScore(v.score_ml, v.predicao_ml);

            tr.innerHTML = `
                <td>${index + 1}</td>
                <td>${v.nome}</td>
                <td>${v.telefone}</td>
                <td>${v.ong}</td>
                <td class="col-mensagem">${previa} ${botaoVerMais}</td>
                <td class="col-score">${scoreCell}</td>
                <td>
                    <button class="btn-editar" data-id="${v.id}">Editar</button>
                    <button class="btn-excluir" data-id="${v.id}">Excluir</button>
                </td>
            `;

            tabela.appendChild(tr);
        });

        document.querySelectorAll('.btn-excluir').forEach(btn => {
            btn.addEventListener('click', () => excluir(btn.dataset.id));
        });
        document.querySelectorAll('.btn-editar').forEach(btn => {
            btn.addEventListener('click', () => editar(btn.dataset.id));
        });
        document.querySelectorAll('.btn-ver-mensagem').forEach(btn => {
            btn.addEventListener('click', () => {
                abrirModal(decodeURIComponent(btn.dataset.mensagem));
            });
        });

    } catch (error) {
        console.error('Erro ao carregar voluntários:', error);
    }
}

// ── Score de veracidade ───────────────────────────────────────────────────────

function renderScore(scoreMl, predicao) {
    // score_ml é probabilidade de ser FALSO (0 = real, 1 = falso)
    // Veracidade = inverso disso
    if (scoreMl === null || scoreMl === undefined) {
        return `<span class="score-indefinido">—</span>`;
    }

    const veracidade = Math.round((1 - scoreMl) * 100);

    // Cor baseada na veracidade
    let classe, rotulo;
    if (veracidade >= 70) {
        classe = "score-alto";
        rotulo = "Provável real";
    } else if (veracidade >= 40) {
        classe = "score-medio";
        rotulo = "Incerto";
    } else {
        classe = "score-baixo";
        rotulo = "Suspeito";
    }

    return `
        <div class="score-wrap ${classe}">
            <div class="score-barra-bg">
                <div class="score-barra-fill" style="width: ${veracidade}%"></div>
            </div>
            <div class="score-info">
                <span class="score-pct">${veracidade}%</span>
                <span class="score-rotulo">${rotulo}</span>
            </div>
        </div>
    `;
}

// ── Modal de mensagem ─────────────────────────────────────────────────────────

function abrirModal(texto) {
    document.getElementById("modalTexto").textContent = texto;
    document.getElementById("modalMensagem").style.display = "flex";
}

function fecharModal() {
    document.getElementById("modalMensagem").style.display = "none";
}

document.addEventListener("DOMContentLoaded", () => {
    carregarVoluntarios();

    document.getElementById("modalFechar").addEventListener("click", fecharModal);
    document.getElementById("modalMensagem").addEventListener("click", (e) => {
        if (e.target === document.getElementById("modalMensagem")) fecharModal();
    });
});

// ── Excluir ───────────────────────────────────────────────────────────────────

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

// ── Editar ────────────────────────────────────────────────────────────────────

async function editar(id) {
    const responseGet = await fetch('/api/voluntarios');
    const lista = await responseGet.json();
    const voluntario = lista.find(v => v.id == id);

    if (!voluntario) { alert('Voluntário não encontrado.'); return; }

    const nome     = prompt("Digite o novo nome:", voluntario.nome);
    const telefone = prompt("Digite o novo telefone:", voluntario.telefone);

    if (telefone && telefone.length > 11) {
        alert("O telefone deve ter no máximo 11 caracteres.");
        return;
    }

    const ong      = prompt("Digite a nova ONG:", voluntario.ong);
    const mensagem = prompt("Digite a nova mensagem:", voluntario.mensagem);

    if (nome && telefone && ong) {
        const dadosAtualizados = {
            nome,
            email   : voluntario.email,
            telefone,
            ong,
            mensagem: mensagem || voluntario.mensagem,
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

// ── Menu mobile ───────────────────────────────────────────────────────────────

const btn  = document.querySelector(".menuh");
const menu = document.querySelector(".menu-mobile");

btn.addEventListener("click", (e) => {
    menu.classList.toggle("ativo");
    document.body.classList.toggle("no-scroll");
    e.stopPropagation();
});

document.addEventListener("click", (e) => {
    if (!menu.contains(e.target) && !btn.contains(e.target)) {
        menu.classList.remove("ativo");
        document.body.classList.remove("no-scroll");
    }
});