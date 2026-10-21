// Run where Playwright is installed; CHROME_PATH optionally selects a local browser.
const {createRequire}=require('module'),path=require('path'),fs=require('fs');
const {pathToFileURL}=require('url');
const {chromium}=createRequire(path.join(process.cwd(),'package.json'))('playwright');
(async()=>{
 const target=path.resolve(process.argv[2]), reports=[];
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
 try {for(const width of [375,390]){for(const fontScale of [1,1.2]){
  const page=await browser.newPage({viewport:{width,height:844}});
  await page.goto(pathToFileURL(target).href);
  await page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));});
  if(fontScale!==1)await page.evaluate(scale=>{const root=document.querySelector('[data-article-root],#gzh-content,#js_content');if(!root)return;const nodes=[root,...root.querySelectorAll('*')].map(e=>({e,size:parseFloat(getComputedStyle(e).fontSize),line:parseFloat(getComputedStyle(e).lineHeight)}));for(const {e,size,line} of nodes){e.style.fontSize=`${size*scale}px`;if(Number.isFinite(line))e.style.lineHeight=`${line*scale}px`;}},fontScale);
  const result=await page.evaluate(()=>{
   const root=document.querySelector('[data-article-root],#gzh-content,#js_content');
   if(!root)throw Error('Missing article root; use data-article-root, gzh-content or js_content');
   const visible=e=>e.getBoundingClientRect().height>0&&getComputedStyle(e).visibility!=='hidden';
   const role=e=>e.closest('[data-role]')?.dataset.role;
   const leaf=e=>![...e.children].some(c=>/^(P|DIV|SECTION|LI|H[1-6])$/.test(c.tagName));
   const candidates=[...root.querySelectorAll('p,li,section,div,h1,h2,h3,h4')].filter(e=>visible(e)&&(leaf(e)||e.dataset.role==='title')&&e.textContent.trim()&&!e.parentElement.closest('[data-role="title"]'));
   const histogram={};
   for(const e of candidates){const size=parseFloat(getComputedStyle(e).fontSize);if(size>=12&&size<=20&&!/^H/.test(e.tagName)&&!['caption','metadata','number','title','subtitle','header-bar'].includes(role(e)))histogram[size]=(histogram[size]||0)+e.textContent.length;}
   const inferred=Number(Object.keys(histogram).sort((a,b)=>histogram[b]-histogram[a])[0]);
   const explicit=candidates.filter(e=>role(e)==='body');
   const body=new Set([...explicit,...candidates.filter(e=>parseFloat(getComputedStyle(e).fontSize)===inferred&&!/^H/.test(e.tagName)&&!['caption','metadata','number','title','subtitle','header-bar'].includes(role(e)))]);
   // Text-node rectangles avoid counting padding, margins and nested spans as extra lines.
   function lineWidths(e){const groups=[];const walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);let n;
    while(n=walker.nextNode()){if(!n.textContent.trim())continue;const range=document.createRange();range.selectNodeContents(n);for(const r of range.getClientRects()){if(!r.width||!r.height)continue;let g=groups.find(g=>Math.abs(g.top-r.top)<3);if(!g)groups.push(g={top:r.top,left:r.left,right:r.right});else{g.left=Math.min(g.left,r.left);g.right=Math.max(g.right,r.right);}}}
    return groups.sort((a,b)=>a.top-b.top).map(g=>g.right-g.left);
   }
   const text=e=>e.textContent.trim().slice(0,90),runs=[];let run=[];
   const flush=()=>{if(run.length)runs.push({paragraphs:run.length,lines:run.reduce((a,x)=>a+x.lines,0),start:run[0].text});run=[];};
   const long=[],titles=[],numbers=[],orphans=[],bars=[],hierarchyWarnings=[];
   const ordered=[...candidates,...root.querySelectorAll('img')].sort((a,b)=>a===b?0:a.compareDocumentPosition(b)&Node.DOCUMENT_POSITION_FOLLOWING?-1:1);
   for(const e of ordered){if(e.tagName==='IMG'){flush();continue;}const lines=lineWidths(e),size=parseFloat(getComputedStyle(e).fontSize),item={text:text(e),lines:lines.length};
    if(e.tagName==='H1'&&size<=inferred)hierarchyWarnings.push({text:text(e),titleFontSize:size,bodyFontSize:inferred});
    if(role(e)==='number'){numbers.push(item);flush();}else if(role(e)==='header-bar'){bars.push(item);flush();}else if(body.has(e)){run.push(item);if(lines.length>6)long.push(item);}else if(/^H/.test(e.tagName)||role(e)==='title'||size>inferred+2){flush();if(/^\d{2}$/.test(e.textContent.trim()))numbers.push(item);else titles.push(item);}else if(role(e)==='header-bar'){bars.push(item);}
    if((body.has(e)||titles.at(-1)===item)&&lines.length>1&&lines.at(-1)<size*2.1)orphans.push(item);
   }flush();
   const imgs=[...root.querySelectorAll('img')],bounds=root.getBoundingClientRect();
   return{width:innerWidth,bodyFontSize:inferred,bodyDetection:explicit.length?'explicit-plus-inferred-review-required':'inferred-review-required',bodyParagraphCount:body.size,coverageFailure:body.size===0,overflow:document.documentElement.scrollWidth>innerWidth+1,longParagraphs:long,denseRuns:runs.filter(r=>r.lines>16||r.paragraphs>6),maxRunLines:Math.max(0,...runs.map(r=>r.lines)),titles,hierarchyWarnings,titleWarnings:titles.filter(x=>x.lines>2),orphanWarnings:orphans,numbers,headerBars:bars,brokenImages:imgs.filter(i=>!i.complete||!i.naturalWidth).length,imageOverflow:imgs.filter(i=>i.getBoundingClientRect().right>Math.min(innerWidth,bounds.right)+1).length,rawMarkdown:root.innerText.includes('**'),placeholderWarning:/【待[^】]*】|TODO|lorem ipsum/i.test(root.innerText)};
  });reports.push({...result,fontScale});await page.close();
 }}}finally{await browser.close();}
 const report={file:target,results:reports,note:'Inferred coverage, density, headings and orphan warnings require full-page semantic review. Heading containers must include all title lines; split containers require manual coverage review. Summary faithfulness, caption necessity and emphasis require semantic review. Nonzero exit can include density flags requiring a recorded decision. This does not verify WeChat paste or phone rendering.'};
 if(process.argv[3])fs.writeFileSync(process.argv[3],JSON.stringify(report,null,2));
 console.log(JSON.stringify(report,null,2));
 if(reports.some(r=>r.coverageFailure||r.hierarchyWarnings.length||r.overflow||(r.fontScale===1&&r.longParagraphs.length)||r.brokenImages||r.imageOverflow||r.rawMarkdown||r.placeholderWarning||(r.fontScale===1&&r.titleWarnings.length)||r.headerBars.some(x=>x.lines>1)||r.numbers.some(x=>x.lines!==1)||r.denseRuns.length))process.exitCode=1;
})().catch(e=>{console.error(e.message);process.exitCode=2;});
