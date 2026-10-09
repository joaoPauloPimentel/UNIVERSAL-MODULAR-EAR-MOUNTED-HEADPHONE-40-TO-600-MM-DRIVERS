import { LOJAS, PECAS_PADRAO, CONFIG_PADRAO } from "./parts.js";
import { extrairOfertas, lerFrete } from "./extract.js";

const ALARME = "umeh-busca";
const espera = ms => new Promise(r => setTimeout(r, ms));
const get = async k => (await chrome.storage.local.get(k))[k];
const set = o => chrome.storage.local.set(o);

async function pecas() { return (await get("pecas")) || PECAS_PADRAO; }
async function config() { return Object.assign({}, CONFIG_PADRAO, (await get("config")) || {}); }

async function agendar() {
  const c = await config();
  await chrome.alarms.clear(ALARME);
  if (c.ativo) chrome.alarms.create(ALARME, { delayInMinutes: 1, periodInMinutes: Math.max(1, c.horas) * 60 });
}
chrome.runtime.onInstalled.addListener(agendar);
chrome.runtime.onStartup.addListener(agendar);
chrome.alarms.onAlarm.addListener(a => { if (a.name === ALARME) buscar(); });

const normal = s => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
function combina(peca, titulo) {
  const t = normal(titulo);
  const ok = (peca.precisa || []).every(g => g.split("|").some(w => t.includes(normal(w.trim()))));
  const proibido = (peca.proibe || []).some(w => w.trim() && t.includes(normal(w.trim())));
  return ok && !proibido;
}

// Espera a aba terminar de carregar (ou estourar o tempo).
function carregou(tabId, limite = 30000) {
  return new Promise(resolve => {
    const fim = setTimeout(() => { chrome.tabs.onUpdated.removeListener(ouvir); resolve(); }, limite);
    function ouvir(id, info) { if (id === tabId && info.status === "complete") { clearTimeout(fim); chrome.tabs.onUpdated.removeListener(ouvir); resolve(); } }
    chrome.tabs.onUpdated.addListener(ouvir);
  });
}

let rodando = false;
export async function buscar() {
  if (rodando) return;
  rodando = true;
  const lista = await pecas(), c = await config();
  const anterior = (await get("resultados")) || {};
  const resultados = {};
  const tarefas = lista.flatMap(p => (p.lojas || []).filter(l => LOJAS[l]).map(l => [p, l]));
  let janela, tabId;
  try {
    // janela minimizada só para as buscas; é fechada no fim
    janela = await chrome.windows.create({ url: "about:blank", state: "minimized", focused: false });
    tabId = janela.tabs[0].id;
    for (let i = 0; i < tarefas.length; i++) {
      const [p, loja] = tarefas[i];
      await set({ progresso: { feito: i, total: tarefas.length, agora: `${p.nome} · ${LOJAS[loja].nome}` } });
      let r = { status: "erro", ofertas: [] };
      try {
        await chrome.tabs.update(tabId, { url: LOJAS[loja].url(p.busca) });
        await carregou(tabId);
        await espera(3500);
        // rola a página para carregar os cartões preguiçosos (Shopee, AliExpress)
        await chrome.scripting.executeScript({ target: { tabId }, func: () => window.scrollTo(0, document.body.scrollHeight / 2) });
        await espera(2000);
        const [{ result }] = await chrome.scripting.executeScript({ target: { tabId }, func: extrairOfertas, args: [loja] });
        r = result || r;
      } catch (e) {
        let onde = ""; try { onde = new URL((await chrome.tabs.get(tabId)).url).host; } catch (x) {}
        r = { status: "erro", erro: String(e && e.message || e) + (onde ? ` (página: ${onde})` : ""), ofertas: [] };
      }
      const boas = r.ofertas.filter(o => combina(p, o.titulo)).sort((a, b) => a.preco - b.preco).slice(0, 5)
        .map(o => Object.assign(o, { loja }));
      const res = resultados[p.id] || (resultados[p.id] = { ofertas: [], status: {} });
      res.status[loja] = r.status === "ok" ? `${boas.length} de ${r.ofertas.length}` : r.status;
      if (r.erro) (res.erros || (res.erros = {}))[loja] = r.erro;
      res.ofertas.push(...boas);
      await espera(1500 + Math.random() * 2000);   // sem pressa, para não parecer robô
    }
    // frete: abre os 3 anúncios mais baratos de cada peça e lê o frete para o endereço da conta
    const fila = lista.flatMap(p => (resultados[p.id] ? resultados[p.id].ofertas.sort((a, b) => a.preco - b.preco).slice(0, 3) : []).map(o => [p, o]));
    for (let i = 0; i < fila.length; i++) {
      const [p, o] = fila[i];
      await set({ progresso: { feito: tarefas.length + i, total: tarefas.length + fila.length, agora: `frete: ${p.nome} · ${LOJAS[o.loja].nome}` } });
      try {
        await chrome.tabs.update(tabId, { url: o.link });
        await carregou(tabId);
        await espera(4000);
        const [{ result }] = await chrome.scripting.executeScript({ target: { tabId }, func: lerFrete, args: [o.preco] });
        o.frete = result ? result.frete : null;
        o.freteTexto = result ? result.texto : "";
      } catch (e) { o.frete = null; }
      if (o.frete == null && o.freteGratis) o.frete = 0;
      await espera(1000 + Math.random() * 1500);
    }
  } finally {
    if (janela) try { await chrome.windows.remove(janela.id); } catch (e) {}
    rodando = false;
  }

  // compara com a busca anterior e avisa
  const avisos = [];
  for (const p of lista) {
    const res = resultados[p.id]; if (!res) continue;
    // total = preço + frete; frete desconhecido conta só o preço, mas perde o empate e fica marcado com "?"
    for (const o of res.ofertas) o.total = o.preco + (o.frete || 0);
    const chave = o => o.total + (o.frete == null ? 0.001 : 0);
    res.ofertas.sort((a, b) => chave(a) - chave(b));
    const verificadas = res.ofertas.filter(o => o.frete !== undefined);
    const melhor = verificadas[0] || res.ofertas[0], antes = anterior[p.id] && anterior[p.id].melhor;
    res.melhor = melhor || null;
    res.historico = ((anterior[p.id] && anterior[p.id].historico) || []).concat(melhor ? [{ t: Date.now(), total: melhor.total }] : []).slice(-60);
    if (!melhor) continue;
    res.promo = melhor.total <= p.precoAlvo;
    const antesTotal = antes ? (antes.total ?? antes.preco) : 0;
    res.queda = antesTotal > 0 ? Math.round((1 - melhor.total / antesTotal) * 100) : 0;
    if (res.promo || res.queda >= c.quedaAviso)
      avisos.push(`${p.nome}: R$ ${melhor.total.toFixed(2).replace(".", ",")} com frete${melhor.frete == null ? " ?" : ""} (${LOJAS[melhor.loja].nome})${res.queda >= c.quedaAviso ? `, caiu ${res.queda}%` : ""}`);
  }
  await set({ resultados, ultima: Date.now(), progresso: null });
  const n = Object.values(resultados).filter(r => r.promo).length;
  chrome.action.setBadgeText({ text: n ? String(n) : "" });
  chrome.action.setBadgeBackgroundColor({ color: "#7c3aed" });
  if (avisos.length)
    chrome.notifications.create("umeh-" + Date.now(), {
      type: "basic", iconUrl: "icons/128.png", title: `UMEH: ${avisos.length} peça(s) em promoção`,
      message: avisos.slice(0, 4).join("\n"), priority: 1
    });
}

chrome.runtime.onMessage.addListener((m, _s, responder) => {
  if (m === "buscar") { buscar(); responder(true); }
  if (m === "reagendar") { agendar(); responder(true); }
});
chrome.notifications.onClicked.addListener(() => chrome.action.openPopup && chrome.action.openPopup().catch(() => {}));
