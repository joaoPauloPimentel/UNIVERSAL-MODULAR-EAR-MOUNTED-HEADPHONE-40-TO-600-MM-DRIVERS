// Roda DENTRO da página de busca da loja. Não usa seletores fixos: acha os links de produto da loja,
// sobe até o "cartão" que contém só aquele produto e lê o preço em R$ desse cartão.
export function extrairOfertas(loja) {
  const PADROES = {
    ml: /(MLB-?\d{6,})/i,
    shopee: /-i\.(\d+\.\d+)/,
    ali: /\/item\/(\d{8,})\.html/,
    amazon: /\/(?:dp|gp\/product)\/([A-Z0-9]{10})/
  };
  const re = PADROES[loja];
  const idDe = href => { let h = href || ""; try { h = decodeURIComponent(h); } catch (e) {} const m = h.match(re); return m ? m[1].replace("-", "").toUpperCase() : null; };

  const url = location.href, txt = (document.body && document.body.innerText) || "";
  if (/account-verification|\/login|\/lgz\/|\/jms\/|signin|captcha|verify\/traffic|\/gz\/|registration/i.test(url) || /digite os caracteres|não sou um robô|captcha/i.test(txt.slice(0, 2000)))
    return { status: "login", ofertas: [] };

  const precoDeTexto = s => {
    // "R$ 1.234,56", "R$123,45", "R$ 123 45" (centavos em sobrescrito); ignora parcelas "12x R$ 10,00"
    const out = [];
    const r = /(\d+\s*x\s*(?:de\s*)?)?R\$\s*(\d{1,3}(?:\.\d{3})+|\d+)(?:\s*,\s*(\d{2})|\s+(\d{2})(?!\d))?/g;
    let m;
    while ((m = r.exec(s))) {
      if (m[1]) continue;
      out.push(parseFloat(m[2].replace(/\./g, "") + "." + (m[3] || m[4] || "00")));
    }
    return out;
  };
  const riscado = el => el.closest("s, del, [class*='previous'], [class*='original'], [class*='old-price'], [class*='strike'], [data-a-strike='true'], [class*='a-text-price']");

  const precoDoCartao = card => {
    // 1) aria-label do Mercado Livre: "Agora: 123 reais com 45 centavos"
    for (const el of card.querySelectorAll("[aria-label*='reais']")) {
      if (riscado(el)) continue;
      const a = el.getAttribute("aria-label");
      if (/antes|parcela|x de/i.test(a)) continue;
      const m = a.match(/(\d[\d.]*)\s*reais(?:\s*com\s*(\d+)\s*centavos?)?/i);
      if (m) return parseFloat(m[1].replace(/\./g, "") + "." + String(m[2] || "0").padStart(2, "0"));
    }
    // 2) Amazon: .a-offscreen fora de preço riscado
    for (const el of card.querySelectorAll(".a-price .a-offscreen")) {
      if (riscado(el)) continue;
      const p = precoDeTexto(el.textContent); if (p.length) return p[0];
    }
    // 3) texto do cartão, sem os trechos riscados
    const clone = card.cloneNode(true);
    clone.querySelectorAll("s, del, [class*='previous'], [class*='original'], [class*='old-price'], [class*='strike'], [data-a-strike='true'], [class*='a-text-price'], [class*='installment'], [class*='parcel']").forEach(e => e.remove());
    const t = (clone.innerText || clone.textContent || "").replace(/\s+/g, " ");
    const p = precoDeTexto(t);
    return p.length ? p[0] : null;
  };

  const vistos = new Map();
  for (const a of document.querySelectorAll("a[href]")) {
    const id = idDe(a.getAttribute("href"));
    if (!id || vistos.has(id)) continue;
    // sobe até o maior ancestral que ainda contém só este produto
    let card = a, el = a;
    for (let i = 0; i < 12 && el.parentElement; i++) {
      el = el.parentElement;
      const ids = new Set([...el.querySelectorAll("a[href]")].map(x => idDe(x.getAttribute("href"))).filter(Boolean));
      if (ids.size > 1) break;
      card = el;
    }
    const preco = precoDoCartao(card);
    if (preco == null || preco <= 0) continue;
    const linksDoId = [...card.querySelectorAll("a[href]")].filter(x => idDe(x.getAttribute("href")) === id);
    // título: a linha mais longa do link que não seja preço ou parcela
    const linhaTitulo = t => (t || "").split("\n").map(l => l.trim()).filter(l => l && !/R\$|^\d+\s*x\b|^-?\d+%/i.test(l)).sort((x, y) => y.length - x.length)[0] || "";
    const titulos = linksDoId.map(x => (x.getAttribute("title") || linhaTitulo(x.innerText)).trim())
      .concat([...card.querySelectorAll("img[alt], h2, h3")].map(x => (x.getAttribute("alt") || x.innerText || "").trim()));
    const titulo = titulos.filter(s => s && !/^R\$/.test(s)).sort((x, y) => y.length - x.length)[0] || "";
    const textoCard = (card.innerText || "").toLowerCase();
    vistos.set(id, {
      id, titulo: titulo.slice(0, 200), preco,
      link: linksDoId[0].href,
      freteGratis: /frete gr[áa]tis|free shipping|envio gr[áa]tis/.test(textoCard)
    });
  }
  return { status: "ok", ofertas: [...vistos.values()] };
}

// Roda na página do ANÚNCIO. Lê o frete mostrado para o endereço da conta.
// Devolve { frete: número (0 = grátis) ou null se não achou, texto: trecho lido }.
export function lerFrete(preco) {
  const url = location.href, corpo = (document.body && document.body.innerText) || "";
  if (/account-verification|\/login|\/lgz\/|\/jms\/|signin|captcha|\/gz\//i.test(url)) return { frete: null, texto: "login" };
  const linhas = corpo.split("\n").map(l => l.replace(/\s+/g, " ").trim()).filter(Boolean);
  const valor = s => { const m = s.match(/R\$\s*(\d{1,3}(?:\.\d{3})+|\d+)(?:\s*,\s*(\d{2}))?/); return m ? parseFloat(m[1].replace(/\./g, "") + "." + (m[2] || "00")) : null; };
  const CHAVE = /frete|envio|entrega|shipping|chegar[áa]|receba|delivery/i;
  for (let i = 0; i < linhas.length && i < 2500; i++) {
    if (!CHAVE.test(linhas[i])) continue;
    const trecho = [linhas[i], linhas[i + 1] || "", linhas[i + 2] || ""].join(" ").slice(0, 200);
    if (/devolu|reembolso|garantia|pol[íi]tica|perguntas|full\b|calcular|informe seu cep|digite seu cep/i.test(linhas[i])) continue;
    // "Frete grátis acima de R$ 79": só vale se o produto passa do mínimo
    const cond = trecho.match(/gr[áa]tis[^R]{0,40}(?:acima|a partir|compras? (?:de|acima)|em pedidos)[^R]{0,15}(R\$\s*[\d.,]+)/i);
    if (cond) { const min = valor(cond[1]); if (min != null && preco >= min) return { frete: 0, texto: trecho }; continue; }
    if (/gr[áa]tis|free shipping|frete 0|sem custo/i.test(linhas[i]) || /^(chegar[áa]|receba)[^R]*gr[áa]tis/i.test(trecho)) return { frete: 0, texto: trecho };
    const v = valor(linhas[i]) ?? valor(linhas[i + 1] || "");
    if (v != null && v < 500 && Math.abs(v - preco) > 0.005) return { frete: v, texto: trecho };
  }
  return { frete: null, texto: "" };
}
