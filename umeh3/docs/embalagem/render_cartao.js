// Prints cartao.html (2 A5 cards on one A4 landscape sheet) to PDF and a PNG preview.
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const dir = __dirname;
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1123, height: 794 } });
  await pg.goto('file://' + dir + '/cartao.html');
  const h = await pg.evaluate(() => [...document.querySelectorAll('.card')].map(c => c.scrollHeight - c.clientHeight));
  console.log('overflow px', h);
  await pg.pdf({ path: dir + '/cartao.pdf', width: '297mm', height: '210mm', printBackground: true });
  await pg.screenshot({ path: dir + '/cartao.png' });
  await b.close();
})();
