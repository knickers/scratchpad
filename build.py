#!/usr/bin/env python3
import os
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


def build(args) -> None:
	source = args.html.read_text(encoding='utf-8')

	if MARKER not in source:
		raise SystemExit(f'Marker {MARKER!r} not found in {args.html}')

	if args.embed:
		favicon = minify_svg(args.svg.read_text(encoding='utf-8'))

		# First encoding layer: valid SVG data URL.
		favicon = 'data:image/svg+xml,' + quote(favicon, safe='-._~')

		# The SVG URI lives inside an outer HTML data: URL. Escape '%' once more so
		# the outer URL decode leaves the inner SVG URI's percent escapes intact.
		favicon = favicon.replace('%', '%25')
	else:
		# Relative path from `html_path` to `svg_path`
		favicon = Path(os.path.relpath(args.svg, args.html.parent))

	source = source.replace(MARKER, str(favicon), 1)

	if args.embed:
		source = 'data:text/html;charset=utf-8,\n' + source
	else:
		source = '<!doctype html>\n' + source

	args.out.write_text(source, encoding='utf-8')
	print(f'Wrote {len(source)} bytes to {args.out}')


def main() -> None:
	parser = argparse.ArgumentParser(description='Build the minified Pad bookmark HTML.')
	parser.add_argument('--embed', action='store_true')
	parser.add_argument('--html', default='pad.tpl', type=Path)
	parser.add_argument('--svg', default='pad.svg', type=Path)
	parser.add_argument('out', nargs='?', default='pad.html', type=Path)
	args = parser.parse_args()
	build(args)


if __name__ == '__main__':
	main()
