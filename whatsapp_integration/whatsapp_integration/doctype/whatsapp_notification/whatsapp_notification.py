# Copyright (c) 2022, Raaj Tailor and contributors
# For license information, please see license.txt

from re import template
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate,parse_val
from six import string_types
import json
from whatsapp_integration.whatsapp_integration.doctype.whatsapp_setting.whatsapp_setting import send_to_whatsapp

class WhatsappNotification(Document):

	def validate(self):
		self.check_field_exist_in_dictype()
		self.validate_condition()	


	def check_field_exist_in_dictype(self):
		meta = frappe.get_meta(str(self.doctype_c))
		if not meta.has_field(str(self.mobile_number_field)):
			frappe.throw("No such field exist in <b>{}</b> with name <b>{}</b>".format(self.doctype_c,self.mobile_number_field))

		for item in self.location_table:
			if not meta.has_field(str(item.field_name)) and not item.field_name == "name":
				frappe.throw("No such field exist in <b>{}</b> with name <b>{}</b>".format(self.doctype_c,item.field_name))

	def validate_condition(self):
		temp_doc = frappe.new_doc(self.doctype_c)
		if self.condition:
			try:
				frappe.safe_eval(self.condition, None, get_context(temp_doc))
			except Exception:
				frappe.throw(_("The Condition '{0}' is invalid").format(self.condition))

	def send(self, doc):		
		context = get_context(doc)		
		context = {"doc": doc, "alert": self, "comments": None}
		if doc.get("_comments"):
			context["comments"] = json.loads(doc.get("_comments"))
		self.send_a_whatsapp_message(doc, context)
		if self.set_property_after_alert:
			allow_update = True
			if doc.docstatus == 1 and not doc.meta.get_field(self.set_property_after_alert).allow_on_submit:
				allow_update = False
			if allow_update:
				frappe.db.set_value(doc.doctype, doc.name, self.set_property_after_alert,
					self.property_value, update_modified = False)
				doc.set(self.set_property_after_alert, self.property_value)

	def send_a_whatsapp_message(self, doc, context):
		
		mobile_number = frappe.db.get_value(doc.doctype,doc.name,self.mobile_number_field)
		if not mobile_number:
			frappe.throw("Please enter Mobile Number!")
		dynamic_values = []
		for item in self.location_table:
			dynamic_values.append({
				"type":"text",
				"text":str(frappe.db.get_value(doc.doctype,doc.name,item.field_name))
			})		
		
		# if self.template_type == "Media":
		res = send_to_whatsapp(self.template_type,doc.doctype,doc.name,receiver=mobile_number,template_name=self.whatsapp_template_name,dynamic_values=dynamic_values)
		# else:
			# res = send_to_whatsapp_text(receiver=mobile_number,template_name=self.whatsapp_template_name,dynamic_values=dynamic_values)

		create_whatsapp_log({
			"doctype_name" : doc.doctype,
			"doc_name" : doc.name,			
			"message" :_(res.content),
			"message_template":self.whatsapp_template_name,
			"dynamic_values":dynamic_values,
			"status": "Success" if str(res.status_code) == "200" else "Fail",
			"mobile_number" : mobile_number
		})

def create_whatsapp_log(doc):
		enl_doc = frappe.new_doc('Whatsapp Notification Log')	
		enl_doc.status = doc["status"]	
		enl_doc.doctype_name = doc["doctype_name"]
		enl_doc.doc_name = doc["doc_name"]
		enl_doc.status = doc["status"]
		enl_doc.message_template = doc["message_template"]
		enl_doc.dynamic_values = str(doc["dynamic_values"])
		enl_doc.message =_(doc["message"])
		enl_doc.mobile_number = doc["mobile_number"]
		enl_doc.insert(ignore_permissions=True)


@frappe.whitelist()
def run_whatsapp_notifications(doc, method):
	
	'''Run notifications for this method'''
	if frappe.flags.in_import or frappe.flags.in_patch or frappe.flags.in_install:
		return

	if doc.flags.whatsapp_notifications_executed==None:
		doc.flags.whatsapp_notifications_executed = []

	if doc.flags.whatsapp_notifications == None:
		alerts = frappe.cache().hget('whatsapp_notifications', doc.doctype)
		if alerts==None:
			alerts = frappe.get_all('Whatsapp Notification', fields=['name', 'event'],filters={'enabled': 1, 'doctype_c': doc.doctype})
		doc.flags.whatsapp_notifications = alerts

	if not doc.flags.whatsapp_notifications:
		return

	def _evaluate_alert(alert):
		if not alert.name in doc.flags.whatsapp_notifications_executed:
			evaluate_alert(doc, alert.name, alert.event)
			doc.flags.whatsapp_notifications_executed.append(alert.name)

	event_map = {
		"on_update": "Save",
		"after_insert": "New",
		"on_submit": "Submit",
		"on_cancel": "Cancel"
	}

	if not doc.flags.in_insert:
		
		event_map['validate'] = 'Value Change'
		event_map['before_change'] = 'Value Change'
		event_map['before_update_after_submit'] = 'Value Change'
	
	for alert in doc.flags.whatsapp_notifications:
		event = event_map.get(method, None)
		if event and alert.event == event:
			_evaluate_alert(alert)
		elif alert.event=='Method' and method == alert.method:
			_evaluate_alert(alert)

def evaluate_alert(doc, alert, event):	
	try:		
		if isinstance(alert, string_types):			
			alert = frappe.get_doc("Whatsapp Notification", alert)
		context = get_context(doc)
		if alert.condition:			
			if not frappe.safe_eval(alert.condition, None, context):
				
				return
	

		if event=="Value Change" and not doc.is_new():
			try:
				db_value = frappe.db.get_value(doc.doctype, doc.name, alert.value_changed)
			except Exception as e:
				if frappe.db.is_missing_column(e):
					alert.db_set('enabled', 0)
					frappe.log_error('Notification {0} has been disabled due to missing field'.format(alert.name))
					return
				else:
					raise
			db_value = parse_val(db_value)
			if (doc.get(alert.value_changed) == db_value) or (not db_value and not doc.get(alert.value_changed)):
			
				return # value not changed
			

		if event != "Value Change" and not doc.is_new():
			doc = frappe.get_doc(doc.doctype, doc.name)
		alert.send(doc)
	
	except Exception as e:
		error_log = frappe.log_error(message=frappe.get_traceback(), title=str(e))
		frappe.throw(_("Error in Notification: {}".format(
			frappe.utils.get_link_to_form('Error Log', error_log.name))))


def get_context(doc):
	return {"doc": doc, "nowdate": nowdate, "frappe.utils": frappe.utils}
