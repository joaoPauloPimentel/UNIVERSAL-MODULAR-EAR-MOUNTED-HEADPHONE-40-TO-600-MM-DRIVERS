# UMEH Caça-Promoções (extensão para Brave, Chrome e Edge)

Procura o menor preço de cada peça do fone UMEH-3 no **Mercado Livre, Shopee, AliExpress e Amazon** e avisa
(notificação + número no ícone) quando uma peça fica **igual ou abaixo do seu preço-alvo** ou **cai 10 %** desde a
última busca.

## Instalar no Brave

1. Baixe esta pasta (`extensao_promocoes`) ou o zip e descompacte.
2. Abra `brave://extensions`, ligue o **Modo de desenvolvedor** (canto de cima à direita).
3. Clique em **Carregar sem compactação** e escolha a pasta `extensao_promocoes`.
4. Fixe o ícone roxo na barra (ícone de quebra-cabeça → alfinete).
5. **Entre na sua conta** do Mercado Livre e da Shopee no Brave. Sem login, as duas mostram uma tela de
   verificação no lugar dos resultados, e a extensão marca "entre na conta".

## Como funciona

- A cada 12 horas (ou no botão **Procurar agora**), abre uma janela minimizada, faz a busca de cada peça nas lojas
  marcadas, lê os anúncios da primeira página e fecha a janela. Leva cerca de 8 segundos por busca
  (a lista inicial tem 15 peças e 41 buscas: uns 5 a 6 minutos). Só roda com o Brave aberto.
- Só conta anúncios cujo título tem as palavras de "Precisa ter" e não tem as de "Não pode ter". Assim um
  "tubo PTFE 2x3" não entra na busca do 2 × 4.
- Ignora preço riscado ("De R$ …") e parcelas ("12x R$ …"). O preço é o da busca, **sem frete** (a Shopee e o
  AliExpress às vezes cobram frete à parte). Confira sempre o anúncio antes de comprar.
- Tudo fica no seu navegador: nada é enviado para servidor nenhum.

## Mudar as peças e os preços-alvo

Clique em **Peças e preços-alvo** no popup. Os preços-alvo iniciais são um ponto de partida tirado das faixas da
lista de compras (outubro de 2026); ajuste para o que você considera promoção. Dá para adicionar outras peças
(por exemplo o driver de 40 ou 60 mm) com **+ Peça**.

## Limites

- As lojas mudam o site com frequência. A extensão não depende de nomes de classes (ela acha os links de produto e
  o "R$" perto deles), mas se uma loja passar a mostrar "nada achado" sempre, ela precisa de ajuste.
- Testado em Chromium com páginas montadas no formato das lojas e com a página real do AliExpress. O Mercado Livre,
  a Shopee e a Amazon bloqueiam acesso do servidor onde foi feito o teste, então não foram testados ao vivo.
- Muitas buscas seguidas podem fazer a loja pedir captcha; por isso há uma pausa entre as buscas e o intervalo
  mínimo é de 1 hora.
