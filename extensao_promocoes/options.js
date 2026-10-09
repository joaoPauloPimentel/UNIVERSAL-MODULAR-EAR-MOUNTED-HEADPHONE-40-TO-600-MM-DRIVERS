import { LOJAS, PECAS_PADRAO, CONFIG_PADRAO } from "./parts.js";
const $ = id => document.getElementById(id);

function linha(p) {
  const tr = document.createElement("tr");
  const campo = (v, cls, tipo = "text") => { const td = document.createElement("td"); const i = document.createElement("input"); i.type = tipo; i.value = v; i.className = cls; if (tipo === "number") { i.step = "0.01"; i.min = "0"; } td.append(i); return td; };
  tr.dataset.id = p.id;
  tr.append(campo(p.nome, "nome"), campo(p.busca, "busca"), campo((p.precisa || []).join(", "), "precisa"), campo((p.proibe || []).join(", "), "proibe"), campo(p.precoAlvo, "alvo", "number"));
  const td = document.createElement("td"); td.className = "lojas";
  for (const [k, l] of Object.entries(LOJAS)) {
    const lb = document.createElement("label"), c = document.createElement("input");
    c.type = "checkbox"; c.value = k; c.checked = (p.lojas || []).includes(k); lb.append(c, " " + l.nome); td.append(lb);
  }
  const tdx = document.createElement("td"), x = document.createElement("button"); x.textContent = "×"; x.className = "sec"; x.title = "Remover"; x.onclick = () => tr.remove(); tdx.append(x);
  tr.append(td, tdx);
  return tr;
}
function desenhar(lista) { const tb = $("linhas"); tb.textContent = ""; lista.forEach(p => tb.append(linha(p))); }
const lista = () => [...$("linhas").rows].map(tr => {
  const v = c => tr.querySelector("." + c).value;
  const sep = s => s.split(",").map(x => x.trim()).filter(Boolean);
  return { id: tr.dataset.id, nome: v("nome"), busca: v("busca"), precisa: sep(v("precisa")), proibe: sep(v("proibe")),
           precoAlvo: parseFloat(String(v("alvo")).replace(",", ".")) || 0, lojas: [...tr.querySelectorAll(".lojas input:checked")].map(c => c.value) };
}).filter(p => p.nome && p.busca);

(async () => {
  const s = await chrome.storage.local.get(["pecas", "config"]);
  const c = Object.assign({}, CONFIG_PADRAO, s.config || {});
  $("horas").value = c.horas; $("queda").value = c.quedaAviso; $("ativo").checked = c.ativo;
  desenhar(s.pecas || PECAS_PADRAO);
})();
$("nova").onclick = () => $("linhas").append(linha({ id: "p" + Date.now(), nome: "", busca: "", precisa: [], proibe: [], precoAlvo: 0, lojas: ["ml", "shopee"] }));
$("padrao").onclick = () => desenhar(PECAS_PADRAO);
$("salvar").onclick = async () => {
  await chrome.storage.local.set({ pecas: lista(), config: { horas: +$("horas").value || 12, quedaAviso: +$("queda").value || 10, ativo: $("ativo").checked } });
  chrome.runtime.sendMessage("reagendar");
  $("ok").textContent = "Salvo."; setTimeout(() => $("ok").textContent = "", 2500);
};
