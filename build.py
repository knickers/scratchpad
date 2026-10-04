#!/usr/bin/env python3
from pathlib import Path
import argparse
import re
from urllib.parse import quote

MARKER = '{{favicon}}'
DATA_PREFIX = 'data:text/html;charset=utf-8,'


def minify_svg(svg: str) -> str:
	svg = re.sub(r'<!--.*?-->', '', svg, flags=re.S)
	svg = re.sub(r'>\s+<', '><', svg)
	svg = re.sub(r'\s+', ' ', svg).strip()
	svg = re.sub(r'\s*=\s*', '=', svg)
	svg = re.sub(r'\s*;\s*', ';', svg)
	svg = re.sub(r'\s*:\s*', ':', svg)
	return svg


def minify_css(css: str) -> str:
	css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
	css = re.sub(r'\s+', ' ', css)
	css = re.sub(r'\s*([{}:;,])\s*', r'\1', css)
	return css.replace(';}', '}').strip()


def minify_html(html: str) -> str:
	html = re.sub(r'<!--.*?-->', '', html, flags=re.S)
	html = re.sub(
		r'<style\b([^>]*)>(.*?)</style>',
		lambda m: f'<style{m.group(1)}>{minify_css(m.group(2))}</style>',
		html,
		flags=re.S | re.I,
	)
	html = re.sub(r'>\s+<', '><', html)
	html = re.sub(r'[\t\r\n]+', '', html)
	return html.strip()


def build(html_path: Path, svg_path: Path, out_path: Path) -> None:
	source = html_path.read_text(encoding='utf-8')
	svg = minify_svg(svg_path.read_text(encoding='utf-8'))

	if MARKER not in source:
		raise SystemExit(f'Marker {MARKER!r} not found in {html_path}')

	# First encoding layer: valid SVG data URL.
	svg_uri = 'data:image/svg+xml,' + quote(svg, safe='-._~')

	# The SVG URI lives inside an outer HTML data: URL. Escape '%' once more so
	# the outer URL decode leaves the inner SVG URI's percent escapes intact.
	nested_svg_uri = svg_uri.replace('%', '%25')
	favicon = f'<link rel="icon" href="{nested_svg_uri}">'
	source = source.replace(MARKER, favicon, 1)

	if source.startswith(DATA_PREFIX):
		result = DATA_PREFIX + minify_html(source[len(DATA_PREFIX):])
	else:
		result = minify_html(source)

	out_path.write_text(result + '\n', encoding='utf-8')
	print(f'Wrote {len(result)} bytes to {out_path}')


def main() -> None:
	parser = argparse.ArgumentParser(description='Build the minified Pad bookmark HTML.')
	parser.add_argument('html', nargs='?', default='pad.html', type=Path)
	parser.add_argument('svg', nargs='?', default='pad.svg', type=Path)
	parser.add_argument('output', nargs='?', default='pad.min.html', type=Path)
	args = parser.parse_args()
	build(args.html, args.svg, args.output)


if __name__ == '__main__':
	main()
