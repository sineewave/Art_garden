const {chromium}=require('/opt/node-tools/node_modules/playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:+(process.argv[4]||1)});
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(400);await p.screenshot({path:process.argv[3]});await b.close();})();
