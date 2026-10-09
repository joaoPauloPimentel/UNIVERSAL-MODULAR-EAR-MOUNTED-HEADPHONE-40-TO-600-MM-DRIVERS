import { LOJAS, PECAS_PADRAO } from "./parts.js";
const $ = id => document.getElementById(id);
const brl = v => "R$ " + v.toFixed(2).replace(".", ",");

async function desenhar() {
  const { pecas, resultados = {}, ultima, progresso } = await chrome.storage.local.get(["pecas", "resultados", "ultima", "progresso"]);
  $("ultima").textContent = ultima ? "última busca " + new Date(ultima).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" }) : "ainda não buscou";
  $("progresso").hidden = !progresso;
  if (progresso) $("progresso").textContent = `Procurando ${progresso.feito + 1}/${progresso.total}: ${progresso.agora}`;
  $("buscar").disabled = !!progresso;
  const tb = $("linhas"); tb.textContent = "";
  for (const p of pecas || PECAS_PADRAO) {
    const r = resultados[p.id], tr = document.createElement("tr");
    const m = r && r.melhor;
    if (r && r.promo) tr.className = "promo";
    const td1 = document.createElement("td"); td1.textContent = p.nome;
    if (r && r.status) {
      const s = document.createElement("small");
      s.textContent = Object.entries(r.status).map(([l, v]) => `${LOJAS[l].nome}: ${v === "login" ? "entre na conta" : v === "erro" ? "erro (" + ((r.erros || {})[l] || "?").slice(0, 120) + ")" : v}`).join(" · ");
      td1.append(s);
    }
    const td2 = document.createElement("td");
    if (m) {
      const a = document.createElement("a"); a.href = m.link; a.target = "_blank"; a.title = m.titulo;
      const total = m.total ?? m.preco;
      a.textContent = brl(total); td2.append(a);
      const frete = m.frete === 0 ? "frete grátis" : m.frete > 0 ? `${brl(m.preco)} + ${brl(m.frete)} frete` : "frete não achado";
      const s = document.createElement("small");
      s.textContent = LOJAS[m.loja].nome + " · " + frete + (r.queda ? ` · ${r.queda > 0 ? "−" : "+"}${Math.abs(r.queda)}%` : "");
      td2.append(s);
    } else td2.textContent = r ? "nada achado" : "—";
    const td3 = document.createElement("td"); td3.textContent = brl(p.precoAlvo);
    tr.append(td1, td2, td3); tb.append(tr);
  }
}
$("buscar").onclick = () => chrome.runtime.sendMessage("buscar");
chrome.storage.onChanged.addListener(desenhar);
desenhar();
