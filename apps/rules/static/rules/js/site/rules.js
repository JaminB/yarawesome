function cloneRule(elem, onSuccess, onFailure) {

    let sourceElement = $(elem);
    let ruleId = $(sourceElement).data("ruleId");
    let ruleName = $(sourceElement).data("name");

    $.ajax({
        url: `/api/rules/${ruleId}/clone/`,
        type: 'PUT',
        headers: {"X-CSRFToken": getCookie("csrftoken")},
        contentType: "application/json; charset=utf-8",
        success: function (response) {
            if (onSuccess !== undefined) {
                onSuccess(response);
            } else {
                toastr.success(`Cloning <b><a href="/rules/${response["rule"]["rule_id"]}" target="_blank">${ruleName}</a></b> to your personal <a href="/collections/${response["collection"]["id"]}"> Cloned Rules collection.</a> `);
            }
        },
        error: function (response) {
            if (onFailure !== undefined) {
                onFailure(response);
            } else {
                toastr.error("Failed to clone rule into personal collection.");
            }
        }
    });
}

/**
 * Initializes the collection side panel.
 */
function initializeRuleActions() {
    $(".clone-rule-btn").click(function () {
        cloneRule(this);
    });
}

$(document).ready(function () {
    initializeRuleActions();
});