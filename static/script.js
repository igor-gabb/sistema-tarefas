// O frontend não fala com o banco direto.
// Ele faz pedidos (fetch) para a API do Flask, e o Flask fala com o banco.

const form = document.getElementById("form");
const campo = document.getElementById("campo");
const lista = document.getElementById("lista");
const vazio = document.getElementById("vazio");
const erro = document.getElementById("erro");
const resumo = document.getElementById("resumo");

function mostrarErro(msg) {
  erro.textContent = msg || "";
}

// Busca todas as tarefas no servidor e desenha a lista
async function carregar() {
  try {
    const resp = await fetch("/api/tarefas");
    if (!resp.ok) throw new Error();
    const tarefas = await resp.json();
    desenhar(tarefas);
  } catch {
    mostrarErro("Não consegui falar com o servidor. Se estiver no Render, ele pode estar acordando — espere uns segundos e recarregue.");
  }
}

function desenhar(tarefas) {
  lista.innerHTML = "";
  vazio.style.display = tarefas.length ? "none" : "block";

  tarefas.forEach((t) => {
    const li = document.createElement("li");
    if (t.concluida) li.classList.add("feita");

    const check = document.createElement("input");
    check.type = "checkbox";
    check.checked = t.concluida;
    check.addEventListener("change", () => alternar(t.id));

    const texto = document.createElement("span");
    texto.textContent = t.titulo; // textContent evita injeção de HTML

    const del = document.createElement("button");
    del.className = "excluir";
    del.textContent = "×";
    del.title = "Excluir";
    del.addEventListener("click", () => excluir(t.id));

    li.append(check, texto, del);
    lista.appendChild(li);
  });

  const feitas = tarefas.filter((t) => t.concluida).length;
  resumo.textContent = tarefas.length ? `${feitas} de ${tarefas.length} concluídas` : "";
}

// Criar (POST)
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const titulo = campo.value.trim();
  if (!titulo) return;

  const botao = form.querySelector("button");
  botao.disabled = true;
  mostrarErro("");

  try {
    const resp = await fetch("/api/tarefas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ titulo }),
    });
    const dados = await resp.json();
    if (!resp.ok) return mostrarErro(dados.erro);
    campo.value = "";
    await carregar();
  } catch {
    mostrarErro("Erro ao salvar. Tente de novo.");
  } finally {
    botao.disabled = false;
    campo.focus();
  }
});

// Marcar/desmarcar (PATCH)
async function alternar(id) {
  await fetch(`/api/tarefas/${id}`, { method: "PATCH" });
  carregar();
}

// Excluir (DELETE)
async function excluir(id) {
  await fetch(`/api/tarefas/${id}`, { method: "DELETE" });
  carregar();
}

carregar();
