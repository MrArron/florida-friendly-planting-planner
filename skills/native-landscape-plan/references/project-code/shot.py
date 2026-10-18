import sys, asyncio
from playwright.async_api import async_playwright
async def main(svg, out, w):
    html=f"<html><head><style>{open('tokens.css').read()} body{{margin:0;background:#fbfaf6}}</style></head><body>{open(svg).read()}</body></html>"
    open('_prev.html','w').write(html)
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':w,'height':800})
        await pg.goto('file://' + __import__('os').path.abspath('_prev.html') + ''); await pg.screenshot(path=out, full_page=True); await b.close()
asyncio.run(main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv)>3 else 1523))
