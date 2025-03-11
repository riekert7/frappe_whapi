frappe.ui.form.on('Whapi Message', {
	refresh: function(frm) {
		if (frm.doc.type == 'Incoming'){
			frm.add_custom_button(__("Reply"), function(){
				frappe.new_doc("Whapi Message", {"to": frm.doc.from});

			});
		}
	}
});
