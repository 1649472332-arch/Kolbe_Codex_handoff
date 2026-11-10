#!/usr/bin/env python3
"""Offline Chrome acceptance: real UI, manifest transforms, pixels, reproducible build."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time
from html.parser import HTMLParser
from PIL import Image, ImageStat
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.loads = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ['src', 'srcset', 'href']:
            if key in attrs and tag in ['script', 'link', 'img', 'iframe', 'video', 'audio', 'source']:
                self.loads.append([tag, key, attrs[key]])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, default=ROOT / 'demo_v2.html')
    parser.add_argument('--manifest',type=Path,default=ROOT/'stack_manifest.json')
    parser.add_argument('--out', type=Path, default=ROOT / 'renders')
    args = parser.parse_args()
    html = args.html.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = {'overall': 'fail', 'checks': {}, 'screenshots': [], 'console_errors': [],
              'page_errors': [], 'warnings': [], 'failed_requests': [], 'requests': [], 'http_requests': []}
    checks = report['checks']

    def check(name, ok, detail=None):
        checks[name] = {'status': 'pass' if ok else 'fail', 'detail': detail}
        if not ok:
            raise AssertionError(f'{name}: {detail}')
        print(f'PASS {name}', flush=True)

    def clean():
        check('runtime_errors', not any(report[k] for k in ['console_errors', 'page_errors', 'failed_requests', 'http_requests']),
              {k: report[k] for k in ['console_errors', 'page_errors', 'failed_requests', 'http_requests']})

    def attach(context):
        context.set_offline(True)
        context.route(re.compile(r'^https?://'), lambda route: route.abort())
        context.on('request', lambda request: (report['requests'].append(request.url),
                   report['http_requests'].append(request.url) if request.url.startswith(('http://', 'https://')) else None))
        context.on('requestfailed', lambda request: report['failed_requests'].append({'url': request.url, 'failure': request.failure}))
        page = context.new_page()
        page.set_default_timeout(30000)
        page.on('pageerror', lambda error: report['page_errors'].append(str(error)))
        page.on('console', lambda msg: report['console_errors'].append(msg.text) if msg.type == 'error' else
                report['warnings'].append(msg.text) if msg.type == 'warning' else None)
        page.goto(html.as_uri(), wait_until='load', timeout=30000)
        page.wait_for_function('window.__demo?.ready===true', timeout=30000)
        return page

    def action(page, code):
        return page.evaluate('async()=>{' + code + ';await Promise.race([__demo.whenIdle(),new Promise((_,r)=>setTimeout(()=>r(Error("idle timeout")),30000))]);}')

    def state(page):
        return page.evaluate('__demo.getState()')

    def snap(page, name, expected):
        path = out / name
        page.screenshot(path=str(path), full_page=False, timeout=30000)
        image = Image.open(path).convert('RGB')
        stat = ImageStat.Stat(image)
        check('pixels_' + name, image.size == expected and max(stat.stddev) > 12,
              {'size': list(image.size), 'stddev': stat.stddev})
        report['screenshots'].append(str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path))
        clean()

    def geometry_state(page, value, manifest):
        action(page, f'__demo.setExplode({value})')
        s = state(page)
        source = {i['id']: i for i in manifest['instances']}
        errors = []
        if abs(s['compressionRatio']-manifest['parameters']['gasket_compression_ratio']*(1-value))>1e-4:
            errors.append(['compression_ratio',s['compressionRatio']])
        for i in s['instances']:
            original = source[i['id']]
            for field, a, b, tolerance in [('position', 'translation', 'exploded_translation', .02), ('scale', 'scale', 'exploded_scale', 1e-4)]:
                expected = [x + value * (y - x) for x, y in zip(original[a], original[b])]
                if max(abs(x-y) for x, y in zip(i[field], expected)) > tolerance:
                    errors.append([i['id'], field, i[field], expected])
            if original['part'] == 'bolt':
                if i['scale'] != [1, 1, 1] or abs(original['local_bbox_mm'][1][2]-60) > .001:
                    errors.append([i['id'], 'bolt length'])
        check(f'transforms_{value}', not errors, errors)
        return s

    def layout(page, width, height):
        page.set_viewport_size({'width': width, 'height': height})
        action(page, '__demo.fitAll()')
        result = page.evaluate('''()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,
          client:document.documentElement.clientWidth,canvas:document.querySelector('canvas').getBoundingClientRect().toJSON(),
          buttons:[...document.querySelectorAll('button,select,input[type=range]')].filter(b=>b.getClientRects().length).map(b=>({id:b.id||b.getAttribute('aria-label'),w:b.getBoundingClientRect().width,h:b.getBoundingClientRect().height}))})''')
        bad = [b for b in result['buttons'] if b['w'] < 43.99 or b['h'] < 43.99]
        s = state(page)
        check(f'layout_{width}x{height}', result['scroll'] <= result['client'] and not bad and
              result['canvas']['height'] >= 160 and abs(s['camera']['aspect']-result['canvas']['width']/result['canvas']['height']) < 1e-5 and
              s['viewport']['dpr'] <= 2, {'overflow': result['scroll']-result['client'], 'small_controls': bad, 'viewport': s['viewport']})

    start = time.time()
    browser = None
    try:
        # Every invocation proves the generator is deterministic; preserve source and geometry.
        before = html.read_bytes()
        custom = args.manifest.resolve()!=ROOT/'stack_manifest.json' or html!=ROOT/'demo_v2.html'
        build_args = [str(args.manifest.resolve()),str(html)] if custom else []
        builds = []
        for _ in range(2):
            result = subprocess.run(['node', 'scripts/build_demo_v2.mjs', *build_args], cwd=ROOT, capture_output=True, text=True, check=True)
            builds.append(sha(html.read_bytes()))
        check('reproducible_build', builds[0] == builds[1] == sha(before), builds)
        data = html.read_bytes()
        report.update(html_bytes=len(data), html_mib=len(data)/1024**2, html_sha256=sha(data))
        check('file_size', len(data) < 8_000_000, len(data))
        text = data.decode()
        resources = Resources()
        resources.feed(text)
        css_urls = re.findall(r'url\(\s*[\'\"]?([^\)\'\"]+)', text)
        source_loads = re.findall(r'(?:import\s*\(|fetch\s*\(|new\s+(?:Worker|XMLHttpRequest)\s*\()\s*[\'\"](https?://[^\'\"]+)', text)
        report['url_hits'] = [{'url': u, 'classification': 'inert library namespace/license/documentation string'}
                              for u in sorted(set(re.findall(r'https?://[^\s<>"\'`\\]+', text)))]
        check('static_offline_resources', not resources.loads and not css_urls and not source_loads,
              {'element_loads': resources.loads, 'css_urls': css_urls, 'literal_network_loads': source_loads, 'url_hits': report['url_hits']})
        manifest = json.loads(args.manifest.read_text())
        build = json.loads((Path(str(html)+'.build.json') if custom else ROOT/'renders/demo_v2_build.json').read_text())
        report['build'] = build
        check('geometry_encoding', all(g['triangles'] == g['retained_triangles'] == manifest['files'][f]['triangles'] and
              g['max_error_mm'] <= .002 and (g['encoding']=='float32' or not (g['quantized_collapsed_triangles'] or g['quantized_flipped_triangles'])) for f, g in build['geometry'].items()), build['geometry'])
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True, args=ARGS)
            report['browser'] = browser.version
            desktop = browser.new_context(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
            page = attach(desktop)
            s = state(page)
            report['three'] = s['three']
            check('instance_and_geometry_identity', len(s['instances']) == 41 and s['sharedGeometry'] and s['geometryCount'] == 12 and
                  all(n == build['geometry'][f]['triangles'] for f, n in s['geometryTriangles'].items()),
                  {'instances': len(s['instances']), 'geometries': s['geometryCount']})
            geometry_state(page, 0, manifest)
            geometry_state(page, .5, manifest)
            geometry_state(page, 1, manifest)
            action(page, '__demo.setExplode(0);__demo.showAll();__demo.fitAll()')
            snap(page, 'demo_v2_assembled.png', (1440, 1000))
            action(page, '__demo.showAll();__demo.setExplode(1);__demo.fitAll()')
            snap(page, 'demo_v2_exploded.png', (1440, 1000))
            # Opaque preview makes the shoulder and rabbet easier to read in the close-up.
            page.locator('#opaque').click()
            action(page, '__demo.select("frame_2");__demo.setIsolation("hide")')
            frame = state(page)
            chosen = next(i for i in frame['instances'] if i['id'] == 'frame_2')
            screen = chosen['screenBBox']
            fraction = max((screen[1][0]-screen[0][0])*frame['viewport']['width']/2,
                           (screen[1][1]-screen[0][1])*frame['viewport']['height']/2)/min(frame['viewport']['width'],frame['viewport']['height'])
            check('frame_close_fit', .65 <= fraction <= .85, fraction)
            check('hide_isolation', [i['id'] for i in frame['instances'] if i['visible']] == ['frame_2'] and chosen['edgeVisible'], None)
            snap(page, 'demo_v2_frame_isolated.png', (1440, 1000))
            action(page, '__demo.flipSelected()')
            reverse = state(page)
            cam, cam2 = frame['camera'], reverse['camera']
            a = [x-y for x, y in zip(cam['position'], cam['target'])]
            b = [x-y for x, y in zip(cam2['position'], cam2['target'])]
            check('flip_camera_only', max(abs(x-y) for x,y in zip(cam['target'],cam2['target'])) < 1e-6 and
                  abs(cam['distance']/cam2['distance']-1) < .01 and a[0]*b[0]+a[2]*b[2] < 0 and
                  [(i['position'],i['scale']) for i in frame['instances']] == [(i['position'],i['scale']) for i in reverse['instances']], None)
            snap(page, 'demo_v2_frame_reverse.png', (1440, 1000))
            action(page, '__demo.flipSelected()')
            restored = state(page)
            check('flip_returns', max(abs(x-y) for x,y in zip(cam['position'],restored['camera']['position'])) < .01, None)
            action(page, '__demo.select("gasket_4");__demo.setIsolation("hide")')
            check('gasket_card', '0.800 mm' in page.locator('#info').inner_text() and 'gasket_4' in page.locator('#info').inner_text(), None)
            snap(page, 'demo_v2_gasket_isolated.png', (1440, 1000))
            action(page, '__demo.select("electrode_2");__demo.setIsolation("hide")')
            electrode = state(page)
            check('electrode_isolation_and_support_notice',
                  [i['id'] for i in electrode['instances'] if i['visible']] == ['electrode_2'] and
                  '一体导电' in page.locator('#info').inner_text() and
                  '旧桥保持留空' in page.locator('#info').inner_text(), None)
            snap(page, 'demo_v2_electrode_isolated.png', (1440, 1000))
            for number,side in [(1,'left'),(2,'right')]:
                page.locator('#tab-'+side).click()
                action(page, '')
                fit=state(page)
                expected=manifest['groups']['tab_fit_'+str(number)]
                check('tab_fit_'+side, sorted(i['id'] for i in fit['instances'] if i['visible'])==sorted(expected) and
                      '0.3 mm' in page.locator('#info').inner_text(), expected)
                snap(page, 'demo_v2_tab_fit_'+side+'.png', (1440, 1000))
            action(page, '__demo.showAll();__demo.setExplode(1)')
            action(page, '__demo.select("gasket_2");__demo.setIsolation("hide")')
            snap(page, 'demo_v2_gasket_left_slot.png', (1440, 1000))
            action(page, '__demo.select("gasket_4");__demo.setIsolation("hide")')
            snap(page, 'demo_v2_gasket_right_slot.png', (1440, 1000))
            for id in ['bolt_8', 'locator_pin_2']:
                action(page, f'__demo.select("{id}")')
                check('selection_'+id, state(page)['selected'] == id and id in page.locator('#info').inner_text(), None)
            action(page, '__demo.select("frame_2");__demo.setIsolation("ghost")')
            s = state(page)
            check('ghost_isolation', all(i['visible'] and i['ghost'] and i['opacity'] == .08 and not i['depthWrite'] for i in s['instances'] if i['id'] != 'frame_2'), None)
            action(page, '__demo.showAll()')
            check('show_all', all(i['visible'] and not i['ghost'] and i['opacity'] > .08 for i in state(page)['instances']), None)
            # Use actual pointer events and a projected, ray-tested frame surface.
            point = state(page)['pickPoint']
            check('frame_surface_available', point and point['id'] == 'frame_2', point)
            page.mouse.click(point['x'], point['y'])
            action(page, '')
            check('pointer_raycast', state(page)['selected'] == 'frame_2', None)
            action(page, '__demo.showAll()')
            point = state(page)['pickPoint']
            page.mouse.move(point['x'], point['y'])
            page.mouse.down()
            page.mouse.move(point['x']+30, point['y']+15, steps=5)
            page.mouse.up()
            action(page, '')
            check('drag_does_not_select', state(page)['selected'] is None, None)
            # Every stable instance, including all seven gaskets and eight washers, via UI navigation.
            traversal = page.evaluate('''()=>{__demo.select('front_endplate');const ids=[];for(let n=0;n<41;n++){ids.push(__demo.getState().selected);document.getElementById('next').click();}return ids;}''')
            check('next_all_41', traversal == state(page)['ids'], traversal)
            previous = page.evaluate('''()=>{const ids=[];for(let n=0;n<41;n++){document.getElementById('prev').click();ids.push(__demo.getState().selected);}return ids;}''')
            check('prev_all_41', previous == list(reversed(traversal)), previous)
            action(page, '')
            page.locator('[data-group="washers"]').click()
            check('group_card', state(page)['group'] == 'washers' and '8 pieces' in page.locator('#info').inner_text() and
                  len(page.locator('.group-pieces [data-piece^="washer_"]').all()) == 8, None)
            page.locator('#next').click()
            check('group_next_first', state(page)['selected'] == 'washer_1', None)
            action(page, '__demo.showAll();__demo.setExplode(0);__demo.setSection(true,71.75/74)')
            section = state(page)
            check('section_planes', section['section'] and abs(section['cutX']-34.75) < 1e-6 and
                  all(i['clipping'] == i['edgeClipping'] == 1 for i in section['instances']) and
                  '0.600 mm' in page.locator('#info').inner_text() and '25.0%' in page.locator('#info').inner_text(), None)
            # Section screenshot starts with the information card in view, independent of prior scroll.
            page.locator('.panel-body').evaluate('(e)=>e.scrollTop=0')
            snap(page, 'demo_v2_section.png', (1440, 1000))
            # Clipped and hidden triangles cannot capture a raycast; point sample is on retained geometry.
            action(page, '__demo.select("frame_2");__demo.setIsolation("hide");__demo.setSection(true,.5)')
            clipped = state(page)
            point = clipped['clippedPickPoint']
            check('clipped_surface_available', point is not None, point)
            page.mouse.click(point['x'],point['y'])
            action(page, '')
            check('clipped_surface_not_pickable', state(page)['selectionEvents'] == clipped['selectionEvents'], None)
            page.locator('#cut').fill('0.75')
            check('section_slider', abs(state(page)['cutX']-18.5) < 1e-6, state(page)['clippingPlane'])
            action(page, '__demo.showAll()')
            check('section_off', not state(page)['section'] and all(i['clipping'] == i['edgeClipping'] == 0 for i in state(page)['instances']), None)
            before_preview = [(i['position'], i['scale']) for i in state(page)['instances']]
            page.locator('#gasket-material').select_option('FKM')
            check('fkm_preview', state(page)['gasket'] == 'FKM' and next(i for i in state(page)['instances'] if i['id'] == 'gasket_4')['color'] == '342820', None)
            page.locator('#gasket-material').select_option('PTFE')
            page.locator('#metal-material').select_option('platinum')
            preview = state(page)
            check('material_preview', preview['gasket'] == 'PTFE' and preview['metal'] == 'platinum' and
                  next(i for i in preview['instances'] if i['id'] == 'gasket_4')['color'] == 'f4f3ec' and
                  next(i for i in preview['instances'] if i['id'] == 'electrode_2')['color'] == 'd9d6cf' and
                  before_preview == [(i['position'], i['scale']) for i in preview['instances']] and
                  '尺寸沿用当前 manifest' in page.locator('.note').inner_text(), None)
            action(page, '__demo.showAll()')
            check('show_all_keeps_preview', state(page)['gasket'] == 'PTFE' and state(page)['opaque'], None)
            page.locator('#reset').click()
            action(page, '')
            reset = state(page)
            check('reset_defaults', reset['target'] == 0 and reset['actual'] == 0 and reset['selected'] is None and
                  reset['gasket'] == 'EPDM' and reset['metal'] == 'titanium' and not reset['opaque'] and not reset['section'] and
                  all(i['visible'] and not i['ghost'] for i in reset['instances']), None)
            # Keyboard tab reaches native controls.
            page.locator('#show-all').focus()
            page.keyboard.press('Tab')
            check('keyboard_navigation', page.evaluate('document.activeElement.id') == 'reset', None)
            report['desktop_performance'] = state(page)['performance']
            clean()
            desktop.close()
            mobile = browser.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True)
            page = attach(mobile)
            action(page, '__demo.setExplode(1)')
            layout(page, 360, 800)
            layout(page, 844, 390)
            layout(page, 390, 844)
            page.locator('#panel-toggle').click()
            action(page, '__demo.fitAll()')
            check('mobile_panel_collapses', not page.locator('.panel-body').is_visible() and page.locator('#explode').is_visible(), None)
            # Two-finger gesture through CDP exercises actual touch events and OrbitControls.
            r = page.locator('canvas').bounding_box()
            x, y = r['x']+r['width']/2, r['y']+r['height']/2
            cdp = mobile.new_cdp_session(page)
            for kind, d in [('touchStart',30),('touchMove',50),('touchEnd',0)]:
                points = [] if kind == 'touchEnd' else [{'x':x-d,'y':y,'id':1},{'x':x+d,'y':y,'id':2}]
                cdp.send('Input.dispatchTouchEvent', {'type':kind, 'touchPoints':points})
            action(page, '')
            check('pinch_does_not_select', state(page)['selected'] is None, None)
            action(page, '__demo.fitAll()')
            check('mobile_exploded_in_frame', all(all(-1.001 <= x <= 1.001 for p in i['screenBBox'] for x in p)
                  for i in state(page)['instances']), None)
            snap(page, 'demo_v2_mobile.png', (780, 1688))
            page.locator('#panel-toggle').tap()
            check('mobile_panel_expands', page.locator('.panel-body').is_visible(), None)
            page.locator('#collapse').tap()
            action(page, '')
            check('mobile_collapse_control', state(page)['target'] == 0 and state(page)['actual'] == 0, None)
            page.locator('#explode-range').fill('0.5')
            action(page, '')
            check('mobile_slider_control', abs(state(page)['actual']-.5) <= 1e-4, None)
            page.locator('#explode').tap()
            action(page, '')
            check('mobile_explode_control', state(page)['target'] == 1 and state(page)['actual'] == 1, None)
            report['mobile_performance'] = state(page)['performance']
            report['performance_note'] = 'Software SwiftShader active-frame intervals and render submission times; not physical phone FPS. Includes shader compilation.'
            stable = state(page)
            action(page, '')
            later = state(page)
            check('stable_camera_and_animation', stable['camera']['position'] == later['camera']['position'] and
                  stable['actual'] == later['actual'] == 1, None)
            clean()
            mobile.close()
            browser.close()
            browser = None
        report['overall'] = 'pass'
    except Exception as error:
        report['failure'] = str(error)
        print(f'FAIL {error}', file=sys.stderr, flush=True)
        raise
    finally:
        report['elapsed_seconds'] = round(time.time()-start, 2)
        (out/'demo_v2_verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(f"Verified {len(checks)} checks; {len(report['screenshots'])} screenshots; {report['html_bytes']} bytes", flush=True)


if __name__ == '__main__':
    main()
