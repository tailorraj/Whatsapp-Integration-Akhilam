// Copyright (c) 2022, Raaj Tailor and contributors
// For license information, please see license.txt

frappe.notification = {
	setup_fieldname_select: function(frm) {
		// get the doctype to update fields
		if(!frm.doc.doctype_c) {
			return;
		}

		frappe.model.with_doctype(frm.doc.doctype_c, function() {
			let get_select_options = function(df) {
				return {value: df.fieldname, label: df.fieldname + " (" + __(df.label) + ")"};
			}

			let get_date_change_options = function() {
				let date_options = $.map(fields, function(d) {
					return (d.fieldtype=="Date" || d.fieldtype=="Datetime")?
						get_select_options(d) : null;
				});
				// append creation and modified date to Date Change field
				return date_options.concat([
					{ value: "creation", label: `creation (${__('Created On')})` },
					{ value: "modified", label: `modified (${__('Last Modified Date')})` }
				]);
			}

			let fields = frappe.get_doc("DocType", frm.doc.doctype_c).fields;
			let options = $.map(fields,
				function(d) { return in_list(frappe.model.no_value_type, d.fieldtype) ?
					null : get_select_options(d); });

			// set value changed options
			frm.set_df_property("reference_field_for_party", "options", [""].concat(options));
			frm.set_df_property("value_changed", "options", [""].concat(options));
			frm.set_df_property("set_property_after_alert", "options", [""].concat(options));

			// set date changed options
			frm.set_df_property("date_changed", "options", get_date_change_options());

		});
	}
}

frappe.ui.form.on('Whatsapp Notification', {
	refresh: function(frm) {
		frappe.notification.setup_fieldname_select(frm);
	},
	setup_fieldname_select: function(frm) {
		// get the doctype to update fields
		if(!frm.doc.doctype_c) {
			return;
		}

		frappe.model.with_doctype(frm.doc.doctype_c, function() {
			let get_select_options = function(df) {
				return {value: df.fieldname, label: df.fieldname + " (" + __(df.label) + ")"};
			}

			let get_date_change_options = function() {
				let date_options = $.map(fields, function(d) {
					return (d.fieldtype=="Date" || d.fieldtype=="Datetime")?
						get_select_options(d) : null;
				});
				// append creation and modified date to Date Change field
				return date_options.concat([
					{ value: "creation", label: `creation (${__('Created On')})` },
					{ value: "modified", label: `modified (${__('Last Modified Date')})` }
				]);
			}

			let fields = frappe.get_doc("DocType", frm.doc.doctype_c).fields;
			let options = $.map(fields,
				function(d) { return in_list(frappe.model.no_value_type, d.fieldtype) ?
					null : get_select_options(d); });

			// set value changed options
			frm.set_df_property("reference_field_for_party", "options", [""].concat(options));
			frm.set_df_property("value_changed", "options", [""].concat(options));
			frm.set_df_property("set_property_after_alert", "options", [""].concat(options));

			// set date changed options
			frm.set_df_property("date_changed", "options", get_date_change_options());

		});
	},
	doctype_c: function(frm) {
		frappe.notification.setup_fieldname_select(frm);
	},
});
