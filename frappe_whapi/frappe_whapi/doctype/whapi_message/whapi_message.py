import json
import frappe
from frappe.model.document import Document
from frappe.integrations.utils import make_post_request


class WhapiMessage(Document):
    """Send Whapi messages."""
    def before_insert(self):
        try:
            if not self.type == 'Outgoing':
                return

            if self.attach and not self.attach.startswith("http"):
                media_url = frappe.utils.get_url() + "/" + self.attach
            else:
                media_url = self.attach

            data = {'to': self.to}

            if self.content_type == 'text':
                data['body'] = self.message
            elif self.content_type in ['image', 'video', 'audio']:
                data['media'] = media_url
                data['caption'] = self.message
            elif self.content_type == 'document':
                data['media'] = media_url
                data['caption'] = self.message
                file_name = media_url.attach.split('/')[-1]
                data['filename'] = file_name

            try:
                self.notify(self.content_type, data)
                self.status = "Success"
            except Exception as e:
                self.status = "Failed"
                frappe.throw(f"Failed to send message {str(e)}")

        except Exception as e:
            frappe.log_error("Error in before_insert on Whapi Message Doctype", e)


    def notify(self, path, data):
        """Call Whapi API."""
        url = f"https://gate.whapi.cloud/messages/{path}"
        whapi_channel = frappe.get_doc('Whapi Channel', self.whapi_channel)
        setattr(self, 'from', whapi_channel.get('phone_number'))
        token = whapi_channel.get_password('token')
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {token}"
        }
        frappe.log_error("Whapi Message", data)
        try:
            response = make_post_request(url=url, headers=headers, json=data)
            self.message_id = response.get("message").get('id')
            self.status = response.get("message").get('status')

        except Exception as e:
            res = frappe.flags.integration_request.json()["error"]
            error_message = res.get("Error", res.get("message"))
            frappe.log_error("Error sending Whapi message", error_message)
            frappe.throw(msg=error_message, title=res.get("error_user_title", "Error"))

    def format_wa_id(phone):
        """Format phone number to WhatsApp ID."""
        phone = phone.replace('+', '').replace(' ', '').replace('-', '')

        if phone.startswith('0'):
            return '27' + phone[1:]
        elif phone.startswith('27'):
            return phone
        else:
            return phone
