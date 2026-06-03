// ── Helpers ML ────────────────────────────────────────────────
function renderScore(v) {
    const score = v.score_ml ?? null;

    if (score === null) {
        return '<span style="font-size:12px;color:#888;">sem dados</span>';
    }

    const pct    = Math.round(score * 100);
    const nivel  = score >= 0.55 ? "alto" : score >= 0.35 ? "medio" : "baixo";
    const motivo = v.motivo || "sem descrição";

    return `
        <div class="ml-score-wrap">
            <span class="ml-score-numero">${pct}%</span>
            <div class="ml-score-barra-fundo">
                <div class="ml-score-barra ${nivel}" style="width:${pct}%"></div>
            </div>
            <span class="ml-tooltip">${motivo}</span>
        </div>
    `;
}


function renderAlertas(v) {
    const alertas = v.alertas ?? [];

    if (alertas.length === 0) {
        return '<span class="ml-sem-alerta">✔ nenhum</span>';
    }

    return `
        <div class="ml-alertas">
            ${alertas.map(a => `<span class="ml-alerta-tag">⚠ ${a}</span>`).join("")}
        </div>
    `;
}

function renderMensagem(v) {
    const msg = v.mensagem || "";

    if (!msg.trim()) {
        return '<span class="col-mensagem vazia">sem mensagem</span>';
    }

    // Exibe truncado na célula; texto completo aparece no tooltip nativo (title)
    return `<span class="col-mensagem" title="${msg.replace(/"/g, '&quot;')}">${msg}</span>`;
}

// ── Carrega voluntários ────────────────────────────────────────
async function carregarVoluntarios() {
    const tabela = document.getElementById("tabelaVoluntarios");
    if (!tabela) return;

    try {
        const response = await fetch('/api/voluntarios');
        const lista    = await response.json();

        tabela.innerHTML = "";

lista.forEach((v, index) => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
        <td data-label="ID">${index + 1}</td>
        <td data-label="Nome">${v.nome}</td>
        <td data-label="Telefone">${v.telefone}</td>
        <td data-label="ONG">${v.ong}</td>
        <td data-label="Mensagem">${renderMensagem(v)}</td>
        <td data-label="Qualidade da Mensagem">${renderScore(v)}</td>
        <td data-label="Alertas">${renderAlertas(v)}</td>
        <td data-label="Ações">
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

    } catch (error) {
        console.error('Erro ao carregar voluntários:', error);
    }
}

// ── Excluir ────────────────────────────────────────────────────
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

// ── Editar ─────────────────────────────────────────────────────
async function editar(id) {
    const responseGet = await fetch('/api/voluntarios');
    const lista       = await responseGet.json();
    const voluntario  = lista.find(v => v.id == id);

    if (!voluntario) {
        alert('Voluntário não encontrado.');
        return;
    }

    const nome     = prompt("Digite o novo nome:", voluntario.nome);
    const telefone = prompt("Digite o novo telefone:", voluntario.telefone);

    if (telefone && telefone.length > 11) {
        alert("O telefone deve ter no máximo 11 caracteres.");
        return;
    }

    const ong = prompt("Digite a nova ONG:", voluntario.ong);

    if (nome && telefone && ong) {
        const dadosAtualizados = {
            nome,
            email    : voluntario.email,
            telefone,
            ong,
            mensagem : voluntario.mensagem
        };

        try {
            const response = await fetch(`/api/voluntarios/${id}`, {
                method  : 'PUT',
                headers : { 'Content-Type': 'application/json' },
                body    : JSON.stringify(dadosAtualizados)
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

// ── Init ───────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", carregarVoluntarios);

// ── Menu mobile ────────────────────────────────────────────────
const btn  = document.querySelector(".menuh");
const menu = document.querySelector(".menu-mobile");

btn.addEventListener("click", (e) => {
    menu.classList.toggle("ativo");
    document.body.classList.toggle("no-scroll");
    e.stopPropagation();
});

document.addEventListener("click", (e) => {
    const clicouDentroMenu = menu.contains(e.target);
    const clicouNoBotao    = btn.contains(e.target);

    if (!clicouDentroMenu && !clicouNoBotao) {
        menu.classList.remove("ativo");
        document.body.classList.remove("no-scroll");
    }
});