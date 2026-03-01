[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

# Canal & River Trust Stoppages for Home Assistant

A custom Home Assistant integration that monitors stoppages (closures, restrictions, and planned works) on Canal & River Trust waterways across England and Wales.

## Overview

This integration connects to the Canal & River Trust API to provide:

- **Per-waterway stoppage sensors** — track the number of active stoppages on each of your chosen waterways
- **Next closure sensor** — shows the soonest upcoming closure across all monitored waterways
- **Total stoppages sensor** — a single count of all active stoppages
- **Map support** — geo_location entities plotted on a Home Assistant map card

## Installation

1. Copy the `custom_components/canal_river_trust/` folder into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. Proceed to [Configuration](#configuration).

## Installation via HACS

1. Open HACS in your Home Assistant instance
2. Click the three dots menu (top right) → **Custom repositories**
3. Add `https://github.com/cawdry-dev/canal-info-hass` with category **Integration**
4. Click **Download** on the Canal & River Trust Stoppages card
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → Add Integration** → search "Canal"

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**.
2. Search for **Canal** and select **Canal & River Trust Stoppages**.
3. Select the waterways you wish to monitor from the list.
4. The integration will create sensors and geo_location entities for your chosen waterways.

## Sensors

### Per-Waterway Stoppage Count

For each waterway you select, a sensor is created (e.g. `sensor.crt_grand_union_canal_stoppages`) showing the number of active stoppages. The sensor state is the count, and the `stoppages` attribute contains a list of stoppage objects with the following fields:

| Field         | Description                              |
|---------------|------------------------------------------|
| `title`       | Name/title of the stoppage               |
| `type`        | Type of stoppage (e.g. closure, restriction) |
| `reason`      | Reason for the stoppage                  |
| `start`       | Start date of the stoppage               |
| `end`         | End date of the stoppage                 |
| `description` | Detailed description (may be empty)      |
| `url`         | Link to the stoppage on the CRT website  |
| `latitude`    | Latitude of the stoppage location        |
| `longitude`   | Longitude of the stoppage location       |

### Next Closure

`sensor.crt_next_closure` shows the title and date of the next upcoming closure across all monitored waterways. Useful for at-a-glance awareness.

### Total Stoppages

`sensor.crt_total_stoppages` provides a single count of all active stoppages across every monitored waterway.

## Map

The integration creates `geo_location` entities for each stoppage that has location data. These entities are automatically available to the Home Assistant map card.

To display stoppages on a map, add a map card with the `canal_river_trust` source:

```yaml
type: map
geo_location_sources:
  - canal_river_trust
default_zoom: 8
```

## Dashboard Examples

### Entities Card — All Sensors

Display all your Canal & River Trust sensors in a single card:

```yaml
type: entities
title: Canal & River Trust Stoppages
entities:
  - entity: sensor.crt_total_stoppages
  - entity: sensor.crt_next_closure
  - entity: sensor.crt_grand_union_canal_stoppages
  - entity: sensor.crt_kennet_avon_canal_stoppages
```

> **Note:** Replace the entity IDs above with your own. Entity IDs are based on the waterway names you selected during configuration.

### Markdown Card — Stoppage Details

Show detailed stoppage information for a specific waterway using a Jinja2 template:

```yaml
type: markdown
title: Grand Union Canal Stoppages
content: >
  {% for s in state_attr('sensor.crt_gu_stoppages', 'stoppages') %}
  ### {{ s.title }}
  **Type:** {{ s.type }} | **Reason:** {{ s.reason }}
  **Dates:** {{ s.start }} to {{ s.end }}
  {{ s.description | default('No details available.') }}
  [View on CRT]({{ s.url }})
  ---
  {% endfor %}
```

### Map Card

Plot all stoppages with location data on an interactive map:

```yaml
type: map
geo_location_sources:
  - canal_river_trust
default_zoom: 8
```

### Conditional Card — Closure Alert

Show an alert card only when there are active closures:

```yaml
type: conditional
conditions:
  - condition: numeric_state
    entity: sensor.crt_total_stoppages
    above: 0
card:
  type: markdown
  title: ⚠️ Active Stoppages
  content: >
    There are currently {{ states('sensor.crt_total_stoppages') }} active
    stoppages on your monitored waterways. Check the details below.
```

## Automations & Notifications

The integration fires custom events when stoppages appear or are resolved, making it easy to build notification automations.

### New Stoppage Alert

Receive a notification whenever a new stoppage is reported on your monitored waterways:

```yaml
automation:
  - alias: "CRT New Stoppage Alert"
    trigger:
      - platform: event
        event_type: crt_new_stoppage
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "New Canal Stoppage"
          message: "{{ trigger.event.data.title }} on {{ trigger.event.data.waterway }} ({{ trigger.event.data.type }}). {{ trigger.event.data.start }} to {{ trigger.event.data.end }}"
          data:
            url: "{{ trigger.event.data.url }}"
```

### Upcoming Closure Warning (Within 7 Days)

Get a warning when a closure is less than 7 days away:

```yaml
automation:
  - alias: "CRT Upcoming Closure Warning"
    trigger:
      - platform: state
        entity_id: sensor.crt_gu_next_closure
    condition:
      - condition: template
        value_template: >
          {{ states('sensor.crt_gu_next_closure') not in ['None', 'unknown', 'unavailable']
             and (as_datetime(states('sensor.crt_gu_next_closure')) - now()).days <= 7 }}
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Canal Closure Warning"
          message: "Closure on Grand Union Canal in {{ (as_datetime(states('sensor.crt_gu_next_closure')) - now()).days }} days: {{ state_attr('sensor.crt_gu_next_closure', 'title') }}"
```

### Stoppage Resolved

Be notified when a previously reported stoppage has been cleared:

```yaml
automation:
  - alias: "CRT Stoppage Resolved"
    trigger:
      - platform: event
        event_type: crt_stoppage_resolved
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Canal Stoppage Cleared"
          message: "{{ trigger.event.data.title }} on {{ trigger.event.data.waterway }} has been resolved."
```

> **Note:** Replace `notify.mobile_app_your_phone` with your actual notification service and `sensor.crt_gu_*` with your actual entity IDs. Entity IDs are based on the waterway names you selected during configuration.

## Troubleshooting

### No sensors appearing after setup

- Ensure you have selected at least one waterway during configuration.
- Check the Home Assistant logs (**Settings** → **System** → **Logs**) for any errors from `canal_river_trust`.
- Verify your Home Assistant instance has internet access to reach the CRT API.

### Stoppages not updating

- The integration polls the CRT API periodically. Allow a few minutes for data to refresh.
- You can force an update via **Developer Tools** → **Services** → `homeassistant.update_entity`.

### Map not showing pins

- Confirm that `geo_location_sources` is set to `canal_river_trust` in your map card configuration.
- Check that the stoppages have valid latitude and longitude data — not all stoppages include location information.

### Integration not found when searching

- Ensure the `custom_components/canal_river_trust/` folder is in the correct location within your Home Assistant config directory.
- Restart Home Assistant after copying the files.

## Brand Assets

The Canal & River Trust logo is included as the integration icon in `custom_components/canal_river_trust/brand/`. HACS will display this icon in the integration card and dashboard.

## Licence

This integration is provided as-is. Stoppage data is sourced from the Canal & River Trust and is subject to their terms of use.