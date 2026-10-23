import asyncio, sys
from playwright.async_api import async_playwright
async def m(w, out, dark):
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':w,'height':900}, color_scheme='dark' if dark else 'light')
        html="<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'></head><body>"+open('lake-pointe-pool-garden.html').read()+"</body></html>"
        open('_full.html','w').write(html)
        await pg.goto('file://' + __import__('os').path.abspath('_full.html') + ''); await pg.wait_for_timeout(800)
        print('scrollWidth', await pg.evaluate('document.documentElement.scrollWidth'), 'viewport', w)
        await pg.screenshot(path=out, full_page=True); await b.close()
asyncio.run(m(int(sys.argv[1]), sys.argv[2], len(sys.argv)>3))