// Lista inicial: peças do UMEH-3 com a almofada oval (lista de compras de outubro de 2026).
// "precoAlvo" é o seu limite: abaixo dele a extensão avisa. Os valores iniciais são só um ponto de partida;
// ajuste na página de opções. "precisa": cada item é uma palavra obrigatória no título (use | para alternativas).
export const LOJAS = {
  ml:     { nome: "Mercado Livre", url: q => `https://lista.mercadolivre.com.br/${encodeURIComponent(q.trim().replace(/\s+/g, "-"))}` },
  shopee: { nome: "Shopee",        url: q => `https://shopee.com.br/search?keyword=${encodeURIComponent(q)}` },
  ali:    { nome: "AliExpress",    url: q => `https://pt.aliexpress.com/w/wholesale-${encodeURIComponent(q.trim().replace(/\s+/g, "-"))}.html` },
  amazon: { nome: "Amazon",        url: q => `https://www.amazon.com.br/s?k=${encodeURIComponent(q)}` }
};

export const PECAS_PADRAO = [
  { id: "pad",     nome: "Almofada oval de veludo 110 × 90 mm (par)", busca: "almofada fone oval veludo 110x90", precisa: ["almofada|earpad|ear pad|espuma", "110", "90"], proibe: ["couro"], precoAlvo: 50, lojas: ["ali", "shopee", "ml"] },
  { id: "fio16",   nome: "Corda de piano / pushrod 1,6 mm (ganchos)", busca: "pushrod aço 1,6mm", precisa: ["1,6|1.6"], proibe: ["inox"], precoAlvo: 17, lojas: ["ml", "shopee"] },
  { id: "fio18",   nome: "Vareta / pushrod 1,8 mm (faixa)", busca: "pushrod aço 1,8mm", precisa: ["1,8|1.8"], proibe: ["inox"], precoAlvo: 34, lojas: ["ml", "shopee"] },
  { id: "ptfe",    nome: "Tubo de PTFE 2 × 4 mm", busca: "tubo ptfe 2x4 impressora 3d", precisa: ["ptfe|teflon", "2x4|2 x 4|2mm|2 mm"], proibe: [], precoAlvo: 12, lojas: ["ml", "shopee", "amazon"] },
  { id: "sil4",    nome: "Mangueira de silicone 4 mm (aquário)", busca: "mangueira silicone aquario 4mm", precisa: ["silicone", "4"], proibe: [], precoAlvo: 12, lojas: ["ml", "shopee", "amazon"] },
  { id: "sil24",   nome: "Mangueira de silicone 2 × 4 mm", busca: "mangueira silicone 2x4mm", precisa: ["silicone", "2x4|2 x 4|2mm x 4mm"], proibe: [], precoAlvo: 12, lojas: ["ml", "shopee", "amazon"] },
  { id: "nasa",    nome: "Travesseiro NASA (espuma viscoelástica)", busca: "travesseiro nasa viscoelastico", precisa: ["nasa|viscoel"], proibe: ["capa avulsa"], precoAlvo: 25, lojas: ["ml", "shopee", "amazon"] },
  { id: "fibra",   nome: "Fibra siliconada", busca: "fibra siliconada", precisa: ["fibra"], proibe: [], precoAlvo: 15, lojas: ["ml", "shopee"] },
  { id: "filtro",  nome: "Esponja filtrante 20 ppi", busca: "esponja filtrante 20 ppi", precisa: ["esponja|espuma", "ppi"], proibe: [], precoAlvo: 40, lojas: ["ml", "shopee"] },
  { id: "soquete", nome: "Soquete fêmea 2 pinos 0,78 mm (par)", busca: "0.78mm 2pin socket female diy", precisa: ["0.78|0,78", "socket|soquete|female|fêmea"], proibe: ["cable", "cabo"], precoAlvo: 10, lojas: ["ali"] },
  { id: "cabo",    nome: "Cabo 2 pinos 0,78 mm", busca: "cabo fone 2 pin 0.78mm", precisa: ["0.78|0,78", "cabo|cable"], proibe: ["mmcx"], precoAlvo: 40, lojas: ["ml", "shopee", "ali"] },
  { id: "jst",     nome: "Conector JST-SH 2 vias com fio (passo 1,0)", busca: "conector jst sh 2 vias 1.0mm com fio", precisa: ["jst|sh", "1.0|1,0|1mm"], proibe: [], precoAlvo: 20, lojas: ["ml", "shopee"] },
  { id: "driver50",nome: "Driver de fone 50 mm (par)", busca: "driver fone de ouvido 50mm", precisa: ["50"], proibe: [], precoAlvo: 40, lojas: ["ml", "shopee", "ali"] },
  { id: "petg",    nome: "Filamento PETG preto 1 kg", busca: "filamento petg preto 1kg 1,75", precisa: ["petg", "1kg|1 kg"], proibe: [], precoAlvo: 80, lojas: ["ml", "shopee", "amazon"] },
  { id: "tpu",     nome: "Filamento TPU 95A", busca: "filamento tpu 95a 1,75", precisa: ["tpu"], proibe: [], precoAlvo: 55, lojas: ["ml", "shopee", "amazon"] }
];

export const CONFIG_PADRAO = { horas: 12, quedaAviso: 10, ativo: true };
