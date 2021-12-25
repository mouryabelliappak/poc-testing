var overnightAccommodationsOptions = $("#id_overnight_accommodations li");
var registrationTypeInputs = $("input[name='registration_type']");

function hideAccommodationOptions() {
  overnightAccommodationsOptions.hide();
}

function accommodationIsEligible(index, element) {
  var registrantAge = parseInt($("#id_age").val());

  var ageMin = parseInt($(element).attr("data-age-min"));
  var ageMax = parseInt($(element).attr("data-age-max"));

  if (registrantAge) {
    var oldEnough = registrantAge >= ageMin;
    var youngEnough = registrantAge <= ageMax;

    return oldEnough && youngEnough;
  }
}

function showEligibleAccommodations(event) {
  hideAccommodationOptions();

  // TODO: de-select any previously selected value
  // to prevent the selection from being hidden and submitted

  var eligibleAccommodations = overnightAccommodationsOptions.filter(
    accommodationIsEligible
  );

  eligibleAccommodations.show();
}

function hideDaysAttending() {
  $("#days-attending-container").hide();
}

function showDaysAttending() {
  $("#days-attending-container").show();
}

function hideOvernightAccommodations() {
  $("#overnight-accommodations-container").hide();
}

function showOvernightAccommodations() {
  $("#overnight-accommodations-container").show();
}

function showRelevantFormSections() {
  hideDaysAttending();
  hideOvernightAccommodations();

  // Get the selected registration type
  var registrationType = registrationTypeInputs.filter(":checked").val();

  if (registrationType === "overnight_attender") {
    showDaysAttending();
    showOvernightAccommodations();
  } else if (registrationType === "day_attender") {
    showDaysAttending();
  }
}

$(document).ready(function () {
  hideOvernightAccommodations();
  hideDaysAttending();
  showRelevantFormSections();

  // Trigger age input event
  // to filter accommodations options
  $("#id_age").trigger("input");
});

$("#id_age").on("input", showEligibleAccommodations);

registrationTypeInputs.on("change", showRelevantFormSections);
