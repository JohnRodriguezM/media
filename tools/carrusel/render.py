"""Render a carousel spec (JSON) into 1080x1920 JPEG slides.

Usage: python3 render.py <spec.json> <out_dir>
"""
import asyncio, json, os, sys
from pathlib import Path
from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent


async def main(spec_path, out_dir):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto((HERE / spec.get("template", "template.html")).as_uri())
        await pg.evaluate("document.fonts.ready")
        for i in range(len(spec["slides"])):
            await pg.evaluate("([s,i])=>render(s,i)", [spec, i])
            await pg.evaluate("document.fonts.ready")
            await pg.wait_for_timeout(80)
            await pg.screenshot(path=str(out / f"{i + 1:02d}.jpg"), type="jpeg", quality=92)
        await b.close()
    print("\n".join(sorted(str(f) for f in out.glob("*.jpg"))))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
