from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    modeladmin_register
)

from registration.models import Registrant


class RegistrantModelAdmin(ModelAdmin):
    """Registrant model admin."""

    needs_ada_accessible_accommodations_col_header_text = "ADA accommodations"

    model = Registrant
    menu_label = "Registrants"
    menu_icon = "fa-address-book"
    menu_order = 100
    add_to_settings_menu = False
    exclude_from_explorer = True
    list_display = (
        "full_name",
        "age",
        "needs_ada_accessible_accommodations",
        "is_full_week_attender",
        "total_partial_day_discount",
        "registration_fee",
    )
    list_filter = (
        "registration_type",
        "overnight_accommodations",
        "needs_ada_accessible_accommodations",
        "days_attending",
    )
    search_fields = (
        "first_name",
        "last_name",
        "email",
    )


modeladmin_register(RegistrantModelAdmin)
