# Copyright (c) 2024, Nishant Bhickta and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class AttendanceRaplItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		attendance: DF.Literal["", "Full", "Half", "Leave"]
		check_in: DF.Time
		check_out: DF.Time
		duration: DF.Duration | None
		employee: DF.Link
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		shift_type: DF.Link | None
	# end: auto-generated types
	pass
