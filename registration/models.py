from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect

from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page

from fees.models import AccommodationFee, DayAttenderFee
from event_days.models import EventDay


class Registrant(models.Model):
    """
    Represents a person who will attend the annual session.
    """
    OVERNIGHT_ATTENDER = "overnight_attender"
    DAY_ATTENDER = "day_attender"
    MEMORIALS_ONLY = "memorials_only"
    REGISTRATION_TYPE_CHOICES = [
        (OVERNIGHT_ATTENDER, "Overnight attender"),
        (DAY_ATTENDER, "Day attender"),
        (MEMORIALS_ONLY, "Meeting for Memorials only"),
    ]

    registration_type = models.CharField(
        max_length=255,
        choices=REGISTRATION_TYPE_CHOICES,
        default=OVERNIGHT_ATTENDER,
        help_text="Select 'Overnight attender' if needing overnight accommodations, 'day attender' if commuting to the event daily, or 'Memorials only' if registrant will only attend the Meeting for Memorials.",
    )
    first_name = models.CharField(
        max_length=255,
        help_text="Registrant first name",
    )
    last_name = models.CharField(
        max_length=255,
        help_text="Registrant last name"
    )
    age = models.IntegerField(
        help_text="Age at time of the event.",
        validators=[
            MinValueValidator(0)
        ]
    )
    email = models.EmailField(
        help_text="Personal email for this registrant, if applicable.",
        null=True,
        blank=True,
    )
    needs_ada_accessible_accommodations = models.BooleanField(
        help_text="Will this registrant need accessible accomodations, such as a wheelchair ramp?"
    )
    days_attending = models.ManyToManyField(
        "event_days.EventDay", blank=True, default=True, help_text="On what day(s) will this registrant be attending the event?")
    overnight_accommodations = models.ForeignKey(
        "fees.AccommodationFee", on_delete=models.PROTECT, null=True, blank=True, help_text="What type of overnight accommodations does this registrant need?")
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="registrants",
    )

    def is_full_week_attender(self):
        total_event_days = EventDay.objects.count()

        number_of_days_attending = self.days_attending.count()

        if number_of_days_attending == total_event_days:
            return True

        return False

    def total_partial_day_discount(self):
        partial_day_discounts = [
            day.partial_day_discount for day in self.days_attending.all()
            if day.partial_day_discount is not None
        ]

        return sum(partial_day_discounts)

    def registration_fee(self):
        days_attending = self.days_attending.all()

        number_of_days_attending = len(days_attending)

        if self.registration_type == Registrant.MEMORIALS_ONLY:
            # Memorial-only attendees are free
            return 0
        if self.overnight_accommodations:
            # full week attenders have specific fee
            if self.is_full_week_attender():
                return self.overnight_accommodations.full_week_fee

            # daily attenders have day rate multiplied by days attending
            # they also qualify for daily discount based on partial days
            total_partial_day_discount = self.total_partial_day_discount()

            return self.overnight_accommodations.daily_fee * number_of_days_attending - total_partial_day_discount

        # Default to day attender fee
        relevant_day_attender_fee = DayAttenderFee.objects.get(
            age_min__lte=self.age,
            age_max__gte=self.age
        )

        return relevant_day_attender_fee.daily_fee * number_of_days_attending

    panels = [
        FieldPanel("first_name"),
        FieldPanel("last_name"),
        FieldPanel("registration_type"),
        FieldPanel("age"),
        FieldPanel("email"),
        FieldPanel("needs_ada_accessible_accommodations"),
        FieldPanel("days_attending",
                   widget=forms.CheckboxSelectMultiple),
        FieldPanel("overnight_accommodations"),
        FieldPanel("user"),
    ]

    def full_name(self):
        return f"{ self.first_name } { self.last_name }"

    def __str__(self):
        return self.full_name()


class RegistrationPage(Page):
    intro = RichTextField(null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    max_count = 1

    def __init__(self, *args, **kwargs):
        # Avoid circular dependency
        from registration.forms import RegistrationForm

        super().__init__(*args, **kwargs)

        self.registration_form = RegistrationForm

    def get_context(self, request, *args, **kwargs):

        context = super().get_context(request)

        context["form"] = self.registration_form

        return context

    def serve(self, request, *args, **kwargs):
        # Check if form was submitted
        if request.method == "POST":
            registration_form = self.registration_form(request.POST)

            if registration_form.is_valid():
                registration = registration_form.save()

                # Associate user with registration
                registration.user = request.user
                registration.save()

                messages.success(request, 'Registration added successfully!')

                return redirect("/")
            else:
                self.registration_form = registration_form

        return super().serve(request)


class MyRegistrantsPage(Page):
    intro = RichTextField(null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    max_count = 1

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        context["my_registrants"] = request.user.registrants.all()

        return context


class EditRegistrantPage(Page):
    intro = RichTextField(null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    max_count = 1

    def __init__(self, *args, **kwargs):
        # Avoid circular dependency
        from registration.forms import RegistrationForm

        super().__init__(*args, **kwargs)

        self.registration_form = RegistrationForm

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)
        registrant_id = request.GET["registrant_id"]

        if registrant_id:
            registrant = get_object_or_404(Registrant, pk=registrant_id)

            # prepopulate model form with registrant (dictionary)
            form = self.registration_form(
                instance=registrant,
            )

            context["form"] = form

        return context

    def serve(self, request, *args, **kwargs):
        registrant_id = request.GET["registrant_id"]

        if registrant_id:
            registrant = get_object_or_404(Registrant, pk=registrant_id)

            # Make sure request user is authorized to edit registrant
            # TODO: move this authorization check into the get_context method
            # Throwing an authorization exception from that method should be sufficient
            # also, try to see if the authorization check can be a model method
            if request.user.id is not registrant.user.id:
                # TODO: make this error page a bit more user friendly
                # e.g. by rendering it in the base.html
                return HttpResponse('Unauthorized', status=401)

            # Check if form was submitted
            if request.method == "POST":
                registration_form = self.registration_form(
                    request.POST or None,
                    instance=registrant
                )

                if registration_form.is_valid():
                    registration_form.save()

                    messages.success(
                        request, 'Registration saved successfully!')

                    # Redirect to "My registrants" page on success
                    my_registrants = MyRegistrantsPage.objects.get()

                    return redirect(my_registrants.get_url())
                else:
                    self.registration_form = registration_form

        return super().serve(request)
