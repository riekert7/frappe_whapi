# Frappe Whapi

Frappe app that integrates with [whapi.cloud](https://whapi.cloud) to send and receive WhatsApp messages from within ERPNext / Frappe — without touching Meta's Cloud API directly.

## What it does

- Provides three doctypes for managing WhatsApp channels, messages, and a delivery log
- Hooks into **every** Frappe doc event across all doctypes and runs matching Server Scripts — so you can trigger WhatsApp messages from any doctype without writing custom Python
- Injects a JS bundle (`frappe_whapi.js`) across all desk pages for client-side helpers

## Doctypes

| Doctype | Purpose |
|---------|---------|
| **Whapi Channel** | Stores whapi.cloud API credentials and channel configuration |
| **Whapi Message** | Log of sent and received messages |
| **Whapi Notification Log** | Audit trail for notification delivery attempts |

## Doc event hooks

The app registers a catch-all `doc_events` hook on `"*"` that fires `run_server_script_for_doc_event` for every lifecycle event:

`before_insert`, `after_insert`, `before_validate`, `validate`, `on_update`, `before_submit`, `on_submit`, `before_cancel`, `on_cancel`, `on_trash`, `after_delete`, `before_update_after_submit`, `on_update_after_submit`

This lets you create Server Scripts (type: Doc Event) on any doctype and call the whapi.cloud API from within them.

## Installation

```bash
bench get-app https://github.com/riekert7/frappe_whapi
bench --site [sitename] install-app frappe_whapi
```

## Usage

1. Add your whapi.cloud API token under **Whapi Channel**
2. Create a **Server Script** (Script Type: Doc Event) targeting any doctype and event
3. Use `requests` in the script to POST to the whapi.cloud REST API

## License

MIT