#!/usr/bin/env python3
"""Build a self-contained, progressively enhanced GitHub Pages guide."""
from pathlib import Path
from html import escape
from urllib.parse import urlencode
import json
import re
import shutil

ROOT = Path(__file__).resolve().parent
BASE = 'The Driskill, 604 Brazos St, Austin, TX 78701'

def e(value):
    return escape(str(value), quote=True)

def icon(name):
    return f'<svg aria-hidden="true"><use href="#i-{name}"></use></svg>'

def maps(address, mode='walk', from_hotel=True):
    params = {'destination': address, 'mode': 'walking' if mode == 'walk' else 'driving'}
    if from_hotel:
        params['source'] = BASE
    return 'https://maps.apple.com/directions?' + urlencode(params)

def link(label, url, cls='', icon_name=None):
    return f'<a class="{e(cls)}" href="{e(url)}" target="_blank" rel="noopener noreferrer">{icon(icon_name) if icon_name else ""}{e(label)}</a>'

def load(name):
    return json.loads((ROOT/'content.json').read_text())[name.removesuffix('.json')]

explore_bars = load('explore-bars.json')
food = load('food.json')
events = load('entertainment.json')
festival = load('festival.json')
notes = load('entertainment-notes.json')
all_cards = explore_bars + food + events
ids = [c['id'] for c in all_cards]
assert len(ids) == len(set(ids)), 'Duplicate card ID'
for card in all_cards:
    for key in ('id','name','section','category','description','address','travel','mode','sources','links'):
        assert key in card, (card.get('id'),key)
    assert card['mode'] in ['walk','ride']
    for source in card['sources'] + card['links']:
        assert source['url'].startswith('https://'), source

preferred = {
    'explore':['texas-capitol','waterloo-park','central-library','lady-bird-trail','bullock-museum','driskill-history'],
    'food':['driskill-grill','coopers-bbq','local-foods','roaring-fork','casino-el-camino','1886-cafe'],
    'entertainment':['antones-soul-man-sam','parker-kris-kimura','oob-fallout-six','elephant-tommy-howard','oob-cabaret-eight','esthers-follies']
}

def sorted_cards(section):
    selected = [c for c in all_cards if c['section'] == section]
    order = preferred[section]
    return sorted(selected, key=lambda c: order.index(c['id']) if c['id'] in order else len(order))

def card_html(c):
    facts = []
    if c.get('hours') or c.get('time'):
        facts.append(('Saturday hours' if c.get('hours') else 'Saturday, November 7', c.get('hours') or c['time']))
    for key,label in [('price','Price guide'),('bestFor','Best for'),('address','Where')]:
        if c.get(key): facts.append((label,c[key]))
    fact_html = ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k,v in facts)
    source_html = '<span>·</span>'.join(link(s['label'],s['url']) for s in c['sources'])
    details = ''.join(f'<p class="extra-detail">{e(d)}</p>' for d in c.get('details',[]))
    travel_icon = 'walk' if c['mode'] == 'walk' else 'car'
    time_badge = f'<span class="badge event-time">{icon("clock")}{e(c["time"])}</span>' if c.get('time') else ''
    tags = [t for t in c.get('tags',[]) if t in ['21+','All ages','Lunch','Dinner','Dessert','Free','Seated','Standing']][:2]
    tags_html = ''.join(f'<span class="badge">{e(t)}</span>' for t in tags)
    # Content is fully present in HTML. JS only enhances navigation and filtering.
    searchable = ' '.join([c['name'],c['category'],c.get('kicker',''),c['description'],c.get('bestFor',''),c.get('tip',''),*c.get('tags',[])]).lower()
    primary = c['links'][0]
    extra_links = ''.join(link(s['label'],s['url'],'card-action') for s in c['links'][1:])
    return f'''<article id="{e(c['id'])}" class="place-card" data-name="{e(c['name'])}" data-category="{e(c['category'])}" data-mode="{e(c['mode'])}" data-travel="{e(c['travel'])}" data-tags="{e('|'.join(c.get('tags',[])))}" data-search="{e(searchable)}">
      <div class="card-top"><div><div class="card-category eyebrow">{e(c['category'])}</div><h3>{e(c['name'])}</h3></div><button type="button" class="save-place js-only" data-save="{e(c['id'])}" aria-pressed="false" aria-label="Save {e(c['name'])} to your picks">{icon('bookmark')}</button></div>
      <p class="card-kicker">{e(c.get('kicker',''))}</p>
      <div class="card-meta"><span class="badge">{icon(travel_icon)}{e(c['travel'])}</span>{time_badge}{tags_html}</div>
      <p class="card-description">{e(c['description'])}</p>
      <div class="card-actions">{link('Apple Maps',maps(c['address'],c['mode']),'card-action','pin')}{link(primary['label'],primary['url'],'card-action primary','arrow')}</div>
      <details class="card-details"><summary><span>{'Show details & ticket advice' if c['section']=='entertainment' else 'Hours, prices & local tips'}</span>{icon('chevron')}</summary><div class="details-body"><dl class="facts">{fact_html}</dl><div class="local-tip"><strong>Good to know</strong>{e(c.get('tip',''))}</div>{details}{('<div class="card-actions">'+extra_links+'</div>') if extra_links else ''}<div class="source-links">Sources: {source_html}</div></div></details>
    </article>'''

section_info = {
    'explore':('01 / THE DAYTIME HOURS','A little room to explore.','History, art, green space, and a good walk. Start close to the hotel; take a short ride when you feel like going farther.',['all','History','Outdoors','Museums','Neighborhoods']),
    'food':('02 / SOMETHING FOR EVERY APPETITE','Good food. A proper drink.','Steak and barbecue for the beef enthusiast, lighter lunches, Austin favorites, dessert, and bars with some character.',['all','Lunch','Dinner','Steakhouses','Barbecue','Austin favorites','Lighter meals','Cocktails','Dive bars','Dessert']),
    'entertainment':('03 / SATURDAY, NOVEMBER 7','Make a night of it.','A blues room around the corner, seated jazz, a dancehall, or a festival full of improv. All show times below are Austin time, CST.',['all','Live music','Improv','Comedy & variety'])
}

def festival_html():
    groups = {}
    for event in festival:
        key = event['venue'] + (' · ' + event['room'] if event['room'] != 'Theater' else '')
        groups.setdefault(key,[]).append(event)
    group_html = ''
    for name,items in groups.items():
        rows = ''.join(f'<div class="festival-row" id="{e(x["id"])}" data-mode="{"walk" if x["venue"] == "Fallout Theater" else "ride"}" data-search="{e((x["venue"]+" "+x["room"]+" "+x["lineup"]+" "+x["format"]).lower())}"><div class="time">{e(x["time"])}</div><div><div class="lineup">{e(x["lineup"])}</div><div class="format">{e(x["format"])}</div></div>{link("Tickets",x["url"],icon_name="arrow")}</div>' for x in items)
        group_html += f'<div class="festival-group"><h3>{e(name)}</h3><p class="festival-address">{e(items[0]["address"])}</p>{rows}</div>'
    return f'''<details class="festival-panel"><summary><div><span class="eyebrow" id="festival-label">The full Saturday lineup</span><span class="serif">Out of Bounds, your way.</span></div>{icon('chevron')}</summary><div class="festival-content"><p class="festival-intro">Twelve show blocks across Fallout, ColdTowne’s two rooms, and Dougherty. Each block is <strong>$22.35 including fees</strong>; eligible students, seniors, and active military pay $17.10. For one or two shows, individual tickets are the straightforward choice. A $129 badge still requires show reservations.</p><p class="festival-intro">Several recommended blocks offered tickets during the research check. Use each ticket page for the current status; these listings do not hold seats. The bills mix improv, sketch, clowning, and music, as labeled below.</p>{link('Official festival schedule','https://oobfest.com/out-of-bounds-comedy-festival-schedule/','button secondary','arrow')}{group_html}<p class="theater-note"><strong>The Hideout has moved:</strong> 5555 N Lamar Blvd, Suite B103. No public November 7 show was confirmed on its current calendar. {link('Check its calendar','https://hideouttheatre.com/calendar/')} before making the trip. The old Congress Avenue address is no longer the destination.</p></div></details>'''

def section_html(name):
    eyebrow,title,intro,filters = section_info[name]
    items = sorted_cards(name)
    chips = ''.join(f'<button type="button" class="chip" data-filter="{e(x)}" aria-pressed="{str(x=="all").lower()}">{e("All choices" if x=="all" else x)}</button>' for x in filters)
    before = ''
    after = ''
    if name == 'entertainment':
        before = '<div class="feature-note"><strong>Out of Bounds is on this weekend.</strong><p>The festival brings special Saturday bills to Fallout, ColdTowne, and Dougherty. Three starting points are below, with the full 12-block schedule after the cards. Reserve the show you want first, then fit dinner around it.</p></div>'
        after = festival_html()
    if name == 'food':
        before = '<div class="feature-note"><strong>A few useful distinctions.</strong><p>1886 is a daytime stop and closes at 3pm. Roaring Fork serves dinner only on Saturday. The three dive picks favor neighborhood character and a mixed crowd; the clientele can still vary by hour and event.</p></div>'
    return f'''<section id="{name}" class="guide-section filterable-section" data-limit="6" aria-labelledby="{name}-title"><div class="section-heading"><div><span class="section-number eyebrow">{e(eyebrow)}</span><h2 id="{name}-title">{e(title)}</h2><p>{e(intro)}</p></div><span class="section-count">{len(items)} choices</span></div><div class="filter-row js-only" aria-label="Filter {name}">{chips}</div>{before}<div class="cards-grid">{''.join(card_html(c) for c in items)}</div><p class="empty-state" hidden>No choices match these filters. Try another category, clear your search, or include short rides.</p><div class="show-more-wrap js-only"><button class="button show-more" type="button" aria-expanded="false">See all {len(items)} choices</button></div>{after}</section>'''

icons = '''<svg xmlns="http://www.w3.org/2000/svg" style="position:absolute;width:0;height:0;overflow:hidden" aria-hidden="true"><defs>
<symbol id="i-pin" viewBox="0 0 24 24"><path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/></symbol>
<symbol id="i-arrow" viewBox="0 0 24 24"><path d="M5 12h14m-5-5 5 5-5 5"/></symbol>
<symbol id="i-chevron" viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"/></symbol>
<symbol id="i-bookmark" viewBox="0 0 24 24"><path d="M6 3h12v18l-6-4-6 4V3Z"/></symbol>
<symbol id="i-close" viewBox="0 0 24 24"><path d="m6 6 12 12M6 18 18 6"/></symbol>
<symbol id="i-search" viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></symbol>
<symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></symbol>
<symbol id="i-walk" viewBox="0 0 24 24"><circle cx="14" cy="4" r="2"/><path d="m8 21 3-7m6 7-2-6-4-3 2-5m-7 6 3-5 4-1 3 4 4 1"/></symbol>
<symbol id="i-car" viewBox="0 0 24 24"><path d="m4 9 2-5h12l2 5M4 9h16l1 4v5H3v-5l1-4ZM5 18v2m14-2v2M6 13h1m10 0h1"/></symbol>
<symbol id="i-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/></symbol>
<symbol id="i-compass" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="m16 8-2 6-6 2 2-6 6-2Z"/></symbol>
<symbol id="i-food" viewBox="0 0 24 24"><path d="M4 3v6c0 3 6 3 6 0V3M7 3v18M19 3c-4 1-4 6-4 9h4m0-9v18"/></symbol>
<symbol id="i-music" viewBox="0 0 24 24"><path d="M9 18V5l11-2v13M9 8l11-2"/><ellipse cx="6" cy="18" rx="3" ry="2"/><ellipse cx="17" cy="16" rx="3" ry="2"/></symbol>
<symbol id="i-info" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.1"/></symbol>
<symbol id="i-ticket" viewBox="0 0 24 24"><path d="M3 5h18v5a2 2 0 0 0 0 4v5H3v-5a2 2 0 0 0 0-4V5Z"/><path d="M15 5v3m0 3v2m0 3v3"/></symbol>
<symbol id="i-phone" viewBox="0 0 24 24"><rect x="6" y="2" width="12" height="20" rx="2"/><path d="M10 5h4m-3 14h2"/></symbol>
</defs></svg>'''

hotel_art = '''<svg class="base-illustration" viewBox="0 0 300 105" aria-hidden="true"><path d="M10 95h280M35 95V45h60v50m-45-50V28h30v17m-25-17V17h20v11M95 95V52h110v43m0 0V45h60v50m-45-50V28h30v17m-25-17V17h20v11M110 52V38h80v14m-70-14 30-24 30 24M140 95V74a10 10 0 0 1 20 0v21M49 62h7v13h-7V62Zm25 0h7v13h-7V62Zm145 0h7v13h-7V62Zm25 0h7v13h-7V62ZM111 65h8v12h-8V65Zm70 0h8v12h-8V65Z"/><path d="M150 14V4m0 0 13 4-13 4M120 88h-12m84 0h-12M20 95V82m260 13V82"/></svg>'''

pick_cards = [
    ('Start with history','The Capitol','Free · 10–15 min walk','texas-capitol'),
    ('An easy barbecue lunch','Cooper’s','11am–10pm · downtown','coopers-bbq'),
    ('A dive with character','Casino El Camino','6–8 min walk','casino-el-camino'),
    ('A seated evening','Parker Jazz Club','7pm or 9:30pm','parker-kris-kimura')
]
quick_html = ''.join(f'<a href="#{id}" class="pick" data-reveal><span class="eyebrow">{e(label)}</span><strong>{e(name)}</strong><small>{e(meta)}{icon("arrow")}</small></a>' for label,name,meta,id in pick_cards)
css = (ROOT/'style.css').read_text()
js = (ROOT/'app.js').read_text()
favicon = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="16" fill="#233b35"/><circle cx="32" cy="32" r="21" fill="none" stroke="#e8c786" stroke-width="2"/><path d="m43 21-6 16-16 6 6-16 16-6Z" fill="#e8c786"/></svg>'
# The favicon is embedded directly in index.html.

html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><meta name="theme-color" content="#f8f4ec"><meta name="description" content="An Austin pocket guide from The Driskill: walkable sights, steak and barbecue, cocktails and dive bars, and Saturday November 7, 2026 music and improv."><meta name="apple-mobile-web-app-title" content="Austin Guide"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="default"><meta property="og:title" content="Austin, at your own pace."><meta property="og:description" content="A pocket guide from The Driskill. Good walks, good food, and a Saturday worth going out for."><meta property="og:type" content="website"><title>Austin, at your own pace · The Driskill Guide</title><link rel="icon" href="data:image/svg+xml,{__import__('urllib.parse',fromlist=['quote']).quote(favicon)}"><script>document.documentElement.classList.add('js');try{{const t=localStorage.getItem('austin-driskill-guide-theme');if(t==='dark'||(!t&&matchMedia('(prefers-color-scheme:dark)').matches))document.documentElement.dataset.theme='dark';}}catch(e){{}}</script><style>{css}</style></head>
<body>{icons}<a class="skip-link" href="#main">Skip to the guide</a>
<div class="wrap"><header class="masthead"><a href="#top" class="brand" aria-label="Austin pocket guide home"><svg class="brand-mark" aria-hidden="true"><use href="#i-compass"></use></svg><div><strong>AUSTIN</strong><span>A pocket guide · The Driskill edition</span></div></a><div class="header-actions js-only"><button id="theme-toggle" type="button" class="icon-button" aria-label="Switch to dark mode" aria-pressed="false">{icon('sun')}</button><button id="open-saved" type="button" class="save-list-button" aria-label="View your saved picks">{icon('bookmark')}<span class="saved-word">My picks</span><span class="count-dot" id="saved-count">0</span></button></div></header>
<div class="hero" id="top"><div><p class="eyebrow">Downtown on foot. A little farther by choice.</p><h1>Austin,<br><em>at your own pace.</em></h1><p class="intro">A good walk, a memorable meal, and somewhere worth staying out for. Your collection of Austin favorites, starting at The Driskill.</p><div class="hero-links"><a class="button" href="#explore">Explore the guide {icon('arrow')}</a><a class="button secondary" href="#entertainment">Saturday’s shows {icon('music')}</a></div></div><aside class="base-card" aria-label="Your starting point">{hotel_art}<div class="base-copy"><p class="eyebrow">Your starting point</p><h2>The Driskill</h2><p class="address">604 Brazos Street<br>Downtown Austin</p>{link('Back to the hotel',maps(BASE,from_hotel=False),'map-link','pin')}</div><p class="base-note">Every travel estimate starts here. Map buttons open a route from the hotel; change the starting point in Maps if you’re already out.</p></aside></div>
<div class="dateline"><span>{icon('sun')} Daytime ideas + Saturday, Nov 7, 2026</span><span>{icon('clock')} All show times are Austin / CST</span><span>{icon('bookmark')} Save a few favorites as you browse</span></div></div>
<nav class="guide-nav" aria-label="Guide sections"><div class="wrap nav-inner"><a href="#explore" class="active" aria-current="location">{icon('compass')}<span>Explore<span class="nav-desktop"> Austin</span></span></a><a href="#food">{icon('food')}<span>Food & drinks</span></a><a href="#entertainment">{icon('music')}<span>Saturday<span class="nav-desktop"> entertainment</span></span></a><a href="#practical">{icon('info')}<span>Good to know</span></a></div></nav>
<main id="main" class="wrap"><div id="archive-note" class="archive-note" hidden>This guide’s show listings are for <strong>Saturday, November 7, 2026</strong>. That date has passed. Use the venue links for current schedules and hours.</div><div class="tools js-only"><div class="search-box"><label class="sr-only" for="guide-search">Search places, food, music, or atmosphere</label>{icon('search')}<input id="guide-search" type="search" placeholder="Try jazz, brisket, a quiet drink…" autocomplete="off"><button type="button" id="clear-search" class="clear-search" aria-label="Clear search" hidden>{icon('close')}</button></div><label class="walk-toggle"><input id="walk-only" type="checkbox"> Walkable choices only</label></div><p id="search-status" class="search-status js-only" aria-live="polite" role="status"></p><noscript><p>The complete guide is below. Enable JavaScript for search, filters, saved picks, and dark mode.</p></noscript>
<section class="quick-picks" id="quick-picks" aria-labelledby="quick-title"><div class="quick-heading"><h2 id="quick-title">A few easy starting points</h2><p>Tap a pick to open its details.</p></div><div class="picks-grid">{quick_html}</div></section>
{section_html('explore')}{section_html('food')}{section_html('entertainment')}
<section id="practical" class="guide-section" aria-labelledby="practical-title"><div class="section-heading"><div><span class="section-number eyebrow">04 / THE USEFUL LITTLE DETAILS</span><h2 id="practical-title">Good to know before you go.</h2><p>A flexible guide for choosing what feels good that day. Book the evening’s anchor, leave room to wander, and keep the hotel easy to find.</p></div></div>
<div class="practical-grid">
<article class="practical-card"><h3>{icon('walk')} Getting around</h3><p>The walk labels are estimates from The Driskill at a relaxed but steady pace. Allow extra time for crossings, stops, and your group’s pace. A “walkable” choice can still be a 25–30 minute walk; each card gives its range.</p><p>Short rides make South Congress, Terry Black’s, ColdTowne, and South Lamar venues easier. Round Rock’s ComedySportz is a separate outing, around 30–45 minutes by car. Traffic can change any ride estimate.</p><p>Apple Maps buttons open walking or driving directions from the hotel. Change the origin to your current location when you are already out.</p></article>
<article class="practical-card"><h3>{icon('ticket')} Reserve the anchor</h3><p>Choose the evening’s show first, then leave enough time for dinner and the walk or ride. A seated steakhouse dinner works best with a reservation and an unhurried buffer.</p><p>Ticket links show current availability. Parker is the clearest seated jazz option; Antone’s is primarily standing. Elephant Room takes no reservations, so an early arrival improves the chance of sitting together.</p><p>Out of Bounds sells tickets by show block. For one or two performances, individual tickets are simpler than a festival badge.</p></article>
<article class="practical-card"><h3>{icon('sun')} Daytime timing</h3><p>Saturday’s Waterloo Park Diwali program runs 9am–noon. The Capitol and museums can fill the middle of the day; the Central Library closes at 5pm.</p><p>1886 Café closes at 3pm, and Roaring Fork is dinner only on Saturday. La Condesa pauses between brunch and dinner. The individual cards have exact service windows.</p><p>For the lake, choose a daylight stroll and dress for the forecast. November is late in the bat season, so a bridge walk is best treated as a view, with no promise of a bat emergence.</p></article>
<article class="practical-card"><h3>{icon('phone')} Keep it handy</h3><p>On an iPhone, open this guide in Safari, tap Share, then choose <strong>Add to Home Screen</strong>. Bookmark it if you prefer. Venue and map links open separately so the guide stays easy to return to.</p><p>The bookmark buttons keep your picks in this browser. They are personal to the device and do not sync to anyone else. Private browsing or clearing website data may remove them.</p><p>Dining prices are examples before tax and tip. Ticket fees are included only where the card says so. Official sources are linked inside every place’s details.</p><button type="button" id="print-guide" class="button secondary js-only">Print or save a PDF {icon('arrow')}</button></article>
</div><div class="back-to-base"><div><h3>Ready to head back?</h3><p>The Driskill · 604 Brazos Street, Austin</p></div>{link('Take me to The Driskill',maps(BASE,from_hotel=False),'button','pin')}</div></section>
</main><footer class="wrap footer"><div><p class="eyebrow">Made for a good Austin weekend.</p><p>Prepared for Saturday, November 7, 2026. Venue information and advertised prices were reviewed November 5–6; hours, menus, lineups, and availability can change. Travel times are estimates. Follow the official links before setting out.</p></div><a href="#top">Back to the top ↑</a></footer>
<dialog class="saved-dialog" id="saved-dialog" aria-labelledby="saved-title"><div class="dialog-inner"><div class="dialog-header"><h2 id="saved-title">Your Austin picks.</h2><button type="button" id="close-saved" class="icon-button" aria-label="Close saved picks">{icon('close')}</button></div><p class="dialog-intro">A little shortlist for the day. Saved on this browser only.</p><div id="saved-items"></div><p class="saved-empty" id="saved-empty">Nothing saved yet. Tap the bookmark on any place to keep it here.</p></div></dialog><div id="toast" class="toast" role="status" aria-live="polite" hidden></div><script>{js}</script></body></html>'''

(ROOT/'index.html').write_text(html)
# A local preview copy; GitHub Pages publishes the repository's root index.html.
(ROOT/'dist').mkdir(exist_ok=True)
(ROOT/'dist'/'index.html').write_text(html)
print(f'Built index.html: {len(all_cards)} cards, {len(festival)} festival blocks, {len(html.encode()):,} bytes')
