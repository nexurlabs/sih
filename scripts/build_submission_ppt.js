const PptxGenJS = require('/tmp/node_modules/pptxgenjs');
const pptx = new PptxGenJS();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'MailTrace';
pptx.subject = 'SIH 2026 idea presentation';
pptx.title = 'MailTrace - SIH26106';
pptx.company = 'MailTrace';
const slides = [1, 2, 3, 4, 5, 6];
for (const n of slides) {
  const slide = pptx.addSlide();
  slide.background = { color: 'FFFFFF' };
  slide.addImage({ path: `/tmp/mt_submit_pages_final/page00${n}.png`, x: 0, y: 0, w: 13.333, h: 7.5 });
}
pptx.writeFile({ fileName: '/root/sih-mailtrace/docs/MailTrace_SIH26106_SUBMISSION.pptx' })
  .then(() => console.log('wrote pptx'))
  .catch((err) => { console.error(err); process.exit(1); });
