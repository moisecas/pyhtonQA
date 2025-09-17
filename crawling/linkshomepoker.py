import asyncio
import csv
import re
import sys
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Set, Tuple, Dict, List, Optional
from urllib.parse import urljoin, urlsplit, urlunsplit, urlparse

from playwright.async_api import async_playwright, Error as PWError

# -------------------- CONFIG POR DEFECTO --------------------
START_URL = "https://pokerenchile.com/"
OUTPUT_CSV = "broken_links_pokerenchile.csv"
MAX_DEPTH = 5                     # Niveles de profundidad a recorrer
MAX_PAGES = 8000                   # Límite de páginas a visitar (seguridad)
REQUEST_TIMEOUT_MS = 20000        # Timeout navegación/requests
CONCURRENT_CHECKS = 20            # Concurrencia para validación de enlaces
IGNORE_HTTPS_ERRORS = True        # Aceptar certificados no válidos
RESPECT_SAME_HOST_FOR_CRAWL = True # Solo navegar dentro del mismo host
CHECK_EXTERNAL_LINKS = True       # Validar enlaces externos aunque no se navegue
TREAT_403_AS_BROKEN = False       # Por defecto 403 NO se reporta como roto
SKIP_BINARY_ASSETS = True         # Opcional: no validar jpg/png/gif/pdf/etc (reduce ruido)
WAIT_UNTIL = "domcontentloaded"   # Estrategia de carga
HEADLESS = True                   # Navegación sin UI

BINARY_EXT = re.compile(r".*\.(?:jpg|jpeg|png|gif|bmp|webp|svg|ico|pdf|zip|rar|7z|gz|tar|mp4|mp3|wav|avi|mov|mkv|woff|woff2|ttf|eot)(\?.*)?$", re.I)
HTTP_SCHEMES = {"http", "https"}

@dataclass
class LinkRecord:
    source_page: str
    link_url: str
    status: Optional[int]
    ok: bool
    reason: str
    final_url: Optional[str]
    tag: str
    attr: str
    depth: int

# -------------------- UTILIDADES --------------------
def normalize_url(base: str, href: str) -> Optional[str]:
    if not href:
        return None
    href = href.strip()
    if href.startswith(("mailto:", "tel:", "javascript:", "#")):
        return None
    try:
        abs_url = urljoin(base, href)
        parts = urlsplit(abs_url)
        if parts.scheme.lower() not in HTTP_SCHEMES:
            return None
        # Normaliza removiendo fragmentos
        normalized = urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query, ""))
        return normalized
    except Exception:
        return None

def same_host(u1: str, u2: str) -> bool:
    try:
        return urlsplit(u1).netloc.lower() == urlsplit(u2).netloc.lower()
    except Exception:
        return False

def canonical_for_seen(u: str) -> str:
    parts = urlsplit(u)
    path = parts.path or "/"
    # Normalizar barra final (evita duplicados /ruta y /ruta/)
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return urlunsplit((parts.scheme, parts.netloc.lower(), path, parts.query, ""))

def should_skip_asset(url: str) -> bool:
    return bool(BINARY_EXT.match(url))

# -------------------- EXTRACCIÓN DE ENLACES --------------------
async def extract_links(page) -> List[Dict[str, str]]:
    # Devuelve [{tag, attr, url}]
    js = """
    () => {
      const out = [];
      const push = (el, attr) => {
        const v = el.getAttribute(attr);
        if (v) out.push({ tag: el.tagName.toLowerCase(), attr, url: v });
      };
      document.querySelectorAll('a[href]').forEach(a => push(a, 'href'));
      document.querySelectorAll('img[src]').forEach(i => push(i, 'src'));
      document.querySelectorAll('link[href]').forEach(l => push(l, 'href'));
      document.querySelectorAll('script[src]').forEach(s => push(s, 'src'));
      return out;
    }
    """
    try:
        links = await page.evaluate(js)
        return links or []
    except Exception:
        return []

# -------------------- VALIDACIÓN HTTP --------------------
async def check_one(request_ctx, url: str) -> Tuple[int, str, str]:
    """
    Intenta HEAD y si falla/405/501, usa GET.
    Devuelve (status, reason, final_url)
    """
    resp = None
    try:
        resp = await request_ctx.head(url)
        # Algunos servidores devuelven 405/501 a HEAD
        if resp.status in (405, 501):
            await resp.dispose()
            resp = await request_ctx.get(url)
    except Exception as e:
        if resp:
            await resp.dispose()
        return (0, f"EXC:{type(e).__name__}", url)

    try:
        status = resp.status
        reason = resp.status_text or ""
        final_url = resp.url
    finally:
        await resp.dispose()
    return (status, reason, final_url)

async def validate_links(request_ctx, links: List[Tuple[str, str, str, int]]) -> List[LinkRecord]:
    """
    links: [(source_page, url, tag, depth)]
    """
    records: List[LinkRecord] = []

    sem = asyncio.Semaphore(CONCURRENT_CHECKS)

    async def worker(source_page, u, tag, attr, depth):
        if SKIP_BINARY_ASSETS and should_skip_asset(u):
            records.append(LinkRecord(source_page, u, None, True, "skipped_binary", None, tag, attr, depth))
            return
        async with sem:
            status, reason, final_url = await check_one(request_ctx, u)
        ok = 200 <= status < 400
        if status == 403 and not TREAT_403_AS_BROKEN:
            # Tratar 403 como "bloqueado" no roto
            records.append(LinkRecord(source_page, u, status, True, "blocked_403", final_url, tag, attr, depth))
        else:
            records.append(LinkRecord(source_page, u, status if status else None, ok, reason or "", final_url, tag, attr, depth))

    tasks = []
    for (src, u, tag, attr, depth) in links:
        tasks.append(asyncio.create_task(worker(src, u, tag, attr, depth)))
    await asyncio.gather(*tasks)
    return records

# -------------------- CRAWL --------------------
async def crawl(start_url: str,
                max_depth: int = MAX_DEPTH,
                max_pages: int = MAX_PAGES) -> List[LinkRecord]:
    visited: Set[str] = set()
    queue = deque([(start_url, 0)])
    start_host = urlsplit(start_url).netloc.lower()
    all_to_check: List[Tuple[str, str, str, str, int]] = []  # (src, url, tag, attr, depth)
    broken_records: List[LinkRecord] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(ignore_https_errors=IGNORE_HTTPS_ERRORS)
        page = await context.new_page()
        request_ctx = await pw.request.new_context(ignore_https_errors=IGNORE_HTTPS_ERRORS, timeout=REQUEST_TIMEOUT_MS)

        pages_visited = 0

        try:
            while queue and pages_visited < max_pages:
                current, depth = queue.popleft()
                canon = canonical_for_seen(current)
                if canon in visited:
                    continue
                visited.add(canon)

                try:
                    await page.goto(current, wait_until=WAIT_UNTIL, timeout=REQUEST_TIMEOUT_MS)
                except PWError as e:
                    # Si la página ni carga, registramos como fallo de navegación
                    broken_records.append(LinkRecord(current, current, 0, False, f"NAV_EXC:{type(e).__name__}", None, "page", "href", depth))
                    continue

                pages_visited += 1
                links = await extract_links(page)
                # Normaliza, clasifica y planifica
                page_links_for_validation: List[Tuple[str, str, str, int]] = []

                for item in links:
                    abs_u = normalize_url(current, item.get("url"))
                    if not abs_u:
                        continue
                    tag = item.get("tag") or "unknown"
                    attr = item.get("attr") or "href"

                    # Guardar para validación (internos y externos)
                    if (not SKIP_BINARY_ASSETS) or (not should_skip_asset(abs_u)):
                        page_links_for_validation.append((current, abs_u, tag, attr, depth))

                    # Encolar para seguir navegando (solo anclas y mismo host)
                    if RESPECT_SAME_HOST_FOR_CRAWL and not same_host(start_url, abs_u):
                        continue
                    # Tiene sentido navegar solo enlaces tipo "a[href]"
                    if tag == "a":
                        # No expandir más allá de la profundidad
                        if depth < max_depth:
                            canon_child = canonical_for_seen(abs_u)
                            if canon_child not in visited:
                                queue.append((abs_u, depth + 1))

                # Validar enlaces de esta página
                validated = await validate_links(request_ctx, page_links_for_validation)
                broken_records.extend([r for r in validated if not r.ok])

                # (Opcional) validar también recursos externos no ancla.
                # Ya lo estamos validando arriba; no navegamos a ellos.

        finally:
            await request_ctx.dispose()
            await context.close()
            await browser.close()

    return broken_records

# -------------------- CSV --------------------
def write_csv(records: List[LinkRecord], path: str) -> None:
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with path_obj.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "source_page", "link_url", "status", "ok", "reason", "final_url", "tag", "attr", "depth"
        ])
        w.writeheader()
        for r in records:
            w.writerow(asdict(r))

# -------------------- CLI --------------------
def parse_args(argv: List[str]) -> Dict:
    import argparse
    p = argparse.ArgumentParser(description="Crawling con Playwright + reporte CSV de enlaces rotos.")
    p.add_argument("--start", default=START_URL, help="URL de inicio")
    p.add_argument("--depth", type=int, default=MAX_DEPTH, help="Profundidad máxima (BFS)")
    p.add_argument("--max-pages", type=int, default=MAX_PAGES, help="Máximo de páginas a visitar")
    p.add_argument("--out", default=OUTPUT_CSV, help="Ruta del CSV de salida")
    p.add_argument("--treat-403-as-broken", action="store_true", help="Contar 403 como roto")
    p.add_argument("--include-binaries", action="store_true", help="Validar assets binarios (jpg,pdf, etc.)")
    p.add_argument("--headful", action="store_true", help="Mostrar navegador (no headless)")
    args = p.parse_args(argv)

    return {
        "start": args.start,
        "depth": args.depth,
        "max_pages": args.max_pages,
        "out": args.out,
        "treat_403_as_broken": args.treat_403_as_broken,
        "skip_binary": not args.include_binaries,
        "headless": not args.headful,
    }

async def main_async(cfg: Dict):
    global TREAT_403_AS_BROKEN, SKIP_BINARY_ASSETS, HEADLESS
    TREAT_403_AS_BROKEN = cfg["treat_403_as_broken"]
    SKIP_BINARY_ASSETS = cfg["skip_binary"]
    HEADLESS = cfg["headless"]

    broken = await crawl(cfg["start"], cfg["depth"], cfg["max_pages"])
    write_csv(broken, cfg["out"])
    print(f"[OK] Páginas rotas/alertas: {len(broken)}")
    print(f"[OK] CSV generado: {cfg['out']}")

def main():
    cfg = parse_args(sys.argv[1:])
    asyncio.run(main_async(cfg))

if __name__ == "__main__":
    main()
