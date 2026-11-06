# Austin, at your own pace

A mobile-first pocket guide for visitors based at The Driskill in downtown Austin, with entertainment listings for **Saturday, November 7, 2026**.

## What is included

- Eight daytime attractions and walks, with longer outings clearly marked.
- Fourteen restaurants and dessert stops, including steakhouses, barbecue, lighter meals, and Austin favorites.
- Eight bars, including Casino El Camino, The Cloak Room, and Donn’s Depot.
- Twelve main entertainment choices and the complete twelve-block Saturday Out of Bounds festival schedule.
- Google Maps directions, official venue/menu/ticket links, category and meal filters with distinct icons, search, device-local saved picks, dark mode, and a print layout.

The site uses standard HTML, CSS, and JavaScript. It has no external JavaScript libraries, analytics, account system, server, or build dependency installation. All content is present in the HTML, including when JavaScript is disabled. Interactive saved picks are held in this browser’s local storage.

## Map collection data

`map-locations.csv` contains the 38 distinct physical stops represented by the 42 guide cards, with addresses, categories, notes, and links back to the guide. The five entries inside The Driskill share one hotel location. The file is ready for reference while creating the Google Maps collection, or for import into Google My Maps. A shared saved list has not yet been created; the published guide currently provides individual Google Maps directions.

## Publish on GitHub Pages

Publish this **new, dedicated repository** from `main` → `/ (root)` in **Settings → Pages → Deploy from a branch**. The root `index.html` is self-contained, and `.nojekyll` disables Jekyll processing. No custom domain or changes to other repositories are needed.

## Update the content

1. Edit the relevant section of `content.json`.
2. Change the layout in `build.py`, styling in `style.css`, or behavior in `app.js`.
3. Run `python build.py`.
4. Commit the source changes **and the regenerated root `index.html`**.

The ignored `dist/` copy is only for the development preview. The `.openai/` directory is ignored local preview configuration, not a separate hosted project.

## Content and date conventions

All show times refer to Austin, **America/Chicago (CST)**, on November 7, 2026. Dining prices are examples before tax and tip. Ticket fees are included only when explicitly stated. Walking and driving estimates are editorial ranges from The Driskill, not live routing. The Google Maps links use the [documented universal directions URL format](https://developers.google.com/maps/documentation/urls/get-started#directions), including `api=1`, each complete destination address, and `travelmode=walking` or `travelmode=driving`. Place-card links use The Driskill as the origin. The two return-to-hotel links omit the origin so Google Maps can use the visitor’s location or ask for a starting point. On iPhones, the links open in the Google Maps app when installed, or in a browser otherwise.

Every card includes source links. Event availability is not live inventory; ticket links lead to the current vendor pages. A visible notice appears after the event date to prevent the Saturday lineup from being mistaken for a current schedule. Venue information was reviewed November 5–6, 2026.

Do not carry recurring shows forward without confirming the new date, and do not reuse the old Congress Avenue address for The Hideout. The Hideout’s new location is 5555 N Lamar Blvd, Suite B103.

## Scope

This repository is a standalone travel guide. It does not need access to or changes in any other project, repository, custom domain, or account setting.
