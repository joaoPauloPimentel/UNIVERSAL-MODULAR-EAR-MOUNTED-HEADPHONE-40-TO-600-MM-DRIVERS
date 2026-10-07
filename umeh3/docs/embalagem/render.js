const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs'); const [out, jobs] = [process.argv[2], JSON.parse(process.argv[3])];
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage();
  for (const [n, W, H] of jobs) {
    const svg = fs.readFileSync(`${out}/${n}.svg`, 'utf8');
    await pg.setContent(`<html><head><style>@page{size:${W}mm ${H}mm;margin:0}body{margin:0}svg{display:block}</style></head><body>${svg}</body></html>`);
    await pg.pdf({ path: `${out}/${n}.pdf`, width: `${W}mm`, height: `${H}mm`, printBackground: true });
    await pg.setViewportSize({ width: Math.round(W * 3.78), height: Math.round(H * 3.78) });
    await pg.screenshot({ path: `${out}/${n}.png` });
  }
  await b.close();
})();
