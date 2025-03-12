# python
"""Webhook."""
import frappe
import json
import requests
import frappe.utils

@frappe.whitelist(allow_guest=True)
def webhook():
    """Handle Whapi webhook."""
    if frappe.request.method == "POST":
        return post()

def get_whapi_channel(channel_id):
    """Get Whapi channel by channel_id."""
    channels = frappe.db.sql("""
        SELECT * FROM `tabWhapi Channel`
        WHERE channel_id = %s
    """, (channel_id,), as_dict=True)
    if channels:  # Whapi Channel ID is unique field
        return channels[0]
    else:
        frappe.log_error("Channel not found", f"Channel {channel_id} not found in frappe")
        return None

def get_whapi_media(whapi_channel, media_id):
    """Fetch Whapi media by media_id."""
    media_url = f"{whapi_channel.api_url}/media/{media_id}"
    headers = {
        'Authorization': f'Bearer {whapi_channel.get_password("token")}'
    }
    try:
        response = requests.get(media_url, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            frappe.log_error(f"Error fetching media: HTTP {response.status_code}", f"Media ID: {media_id}")
            return None
    except Exception as e:
        frappe.log_error("Error downloading media from WhatsApp", str(e))
        return None

def post():
    """Handle POST request for Whapi webhook."""
    data = frappe.local.form_dict
    frappe.get_doc({
        "doctype": "Whapi Notification Log",
        "template": "Webhook",
        "meta_data": json.dumps(data)
    }).insert(ignore_permissions=True)

    whapi_channel = get_whapi_channel(data.get('channel_id'))
    if not whapi_channel:
        return

    process_messages(data.get("messages", []), whapi_channel)
    process_statuses(data.get("statuses", []))

def process_messages(messages, whapi_channel):
    """Process incoming messages."""
    for message in messages:

        if message['from_me']:
            continue

        is_reply = 'context' in message and 'quoted_id' in message.get('context', {})
        reply_to_message_id = message.get('context', {}).get('quoted_id', None) if is_reply else None

        whapi_message = {
            "doctype": "Whapi Message",
            "type": "Incoming",
            "from": message['from'],
            "to": whapi_channel.get('phone_number'),
            "whapi_channel": whapi_channel.get('name'),
            "message_id": message['id'],
            "chat_id": message['chat_id'],
            "reply_to_message_id": reply_to_message_id,
            "is_reply": is_reply,
            "content_type": message['type']
        }

        if message['type'] == 'text':
            whapi_message['message'] = message['text']['body']
            frappe.get_doc(whapi_message).insert(ignore_permissions=True)
        elif message['type'] == 'action' and message['action']['type'] == 'reaction':
            whapi_message['message'] = message['action']['emoji']
            frappe.get_doc(whapi_message).insert(ignore_permissions=True)
        elif message['type'] in ['image', 'video', 'audio', 'sticker', 'document']:
            file_data = get_whapi_media(whapi_channel, message[message['type']]['id'])
            if not file_data:
                continue
            file_extension = message[message['type']]['mime'].split('/')[1]
            file_name = f"{frappe.generate_hash(length=10)}.{file_extension}"
            whapi_message['message'] = message[message['type']].get("caption", f"/files/{file_name}")
            message_doc = frappe.get_doc(whapi_message).insert(ignore_permissions=True)

            file = frappe.get_doc({
                "doctype": "File",
                "file_name": file_name,
                "attached_to_doctype": "Whapi Message",
                "attached_to_name": message_doc.name,
                "content": file_data,
                "attached_to_field": "attach"
            }).save(ignore_permissions=True)

            message_doc.attach = file.file_url
            message_doc.save()
        else:
            whapi_message['message'] = message.get(message['type'])
            frappe.get_doc(whapi_message).insert(ignore_permissions=True)

def process_statuses(statuses):
    """Process message statuses."""
    for status in statuses:
        update_message_status(status)

def update_message_status(data):
    """Update the status of a message."""
    message_id = data['id']
    status = data['status']
    name = frappe.db.get_value("Whapi Message", filters={"message_id": message_id})

    if name:
        doc = frappe.get_doc("Whapi Message", name)
        doc.status = status
        doc.save(ignore_permissions=True)