# Copyright (c) 2022, Raaj Tailor and contributors
# For license information, please see license.txt

from mimetypes import init
from re import template
import frappe
from frappe.model.document import Document
import requests
from frappe.utils.data import quoted
import json


class WhatsappSetting(Document):
	pass

@frappe.whitelist()
def send_to_whatsapp(template_type,ref_doctype,ref_docname,receiver,template_name,dynamic_values):
	whatsAppSetting = frappe.get_single("Whatsapp Setting")
	token = whatsAppSetting.get_password('access_token')
	phone_id = whatsAppSetting.get_password('phone_id')	
	send_message_url = "https://graph.facebook.com/v13.0/{phone_id}/messages".format(phone_id=phone_id)
	payload = {
		"messaging_product": "whatsapp",
		"recipient_type": "individual",
		"to": receiver,
		"type": "template",
		"template": {
			"name": template_name,
			"language": {
				"code": "en"
			},
			"components": create_components(template_type,ref_doctype,ref_docname,dynamic_values)
		}
	}
	headers = {
		"Content-Type":"application/json",
		"Authorization": "Bearer {}".format(token)
	}
	r = requests.post(send_message_url, data=json.dumps(payload), headers=headers)
	if str(r.status_code) == "200":
		frappe.msgprint("Whatsapp Alert Has been Sent!")
	else:
		frappe.msgprint("There is some error while sending whatsapp alert, please check whatsapp message log.")
	
	return r

def create_components(template_type,ref_doctype,ref_docname,dynamic_values):
	components = []
	if template_type == "Media":
		components.append({
			
					"type": "header",
					"parameters": [
						{
							"type": "document",
							"document": {
								"link": get_url_for_whatsapp(ref_doctype, ref_docname),
								"filename":str(ref_docname)
							}
							
						}
					]
				
		})
	components.append({
		
		"type": "body",
		"parameters": dynamic_values
		
	})
	return components

def get_url_for_whatsapp(doctype, name):
	doc = frappe.get_doc(doctype, name)
	return "{url}/api/method/whatsapp_integration.get_pdf.pdf?doctype={doctype}&name={name}&key={key}".format(
		url=frappe.utils.get_url(),
		doctype=quoted(doctype),
		name=quoted(name),
		key=doc.get_signature()
	)
