
let statusRefreshCount = 0;

function initializeImportForm() {
    /*
    Initialize the import form and add the event handlers.
     */
    let optionSelect = $("#import-option-select");
    optionSelect.val("local")
    $(optionSelect).on("change", function () {
        updateImportForm($(this))
    });
    $("#import-form").on("submit", function (event) {
        event.preventDefault();
        statusRefreshCount = 0;
        addImportFormEventOnSubmitHandler(this)
    });
    $("#import-input").on("click", function (event) {
        $("#import-status-container").fadeOut();
        $("#import-welcome-container").fadeOut();
        statusRefreshCount = 101;
    });
}


function updateImportedRuleCount(importId) {
    $("#import-status-container").fadeIn();
    return $.ajax({
        url: `/api/rules/import/${importId}`,
        method: "GET",
        success: function (response) {
            $("#rule-import-count").text(response["imported_rule_count"]);
            $("#rule-collection-count").text(response["collections_created"]);
            $("#rule-import-search-link").attr("href", `/rules/mine/?term=import_id: ${importId}`);
        },
        error: function (xhr, status, error) {
            console.error("API error:", error);
        }
    });
}

// Function to run updateImportedRuleCount on a loop every 5 seconds
function refreshImportedRuleCount(importId) {
    updateImportedRuleCount(importId).then(function () {
        setTimeout(function () {
            if (statusRefreshCount < 100) {
                refreshImportedRuleCount(importId);
                statusRefreshCount++;
            }
        }, 5000);
    });
}
function updateImportForm(formSelectElem) {
    /*
    Update the import form based on the selected option.
     */
    let importInput = formSelectElem.parent().find("input").first();
    if (formSelectElem.val() === "local") {
        $(importInput).attr("type", "file")
        $(importInput).attr("placeholder", "Browse a file or archive on disk.")
    } else if (formSelectElem.val() === "github") {
        $(importInput).attr("type", "url")
        $(importInput).attr("placeholder", "Import from a Github repo containing YARA rules.")
    } else if (formSelectElem.val() === "url") {
        $(importInput).attr("type", "url")
        $(importInput).attr("placeholder", "Import from an archive containing YARA rules.")
    }
}

function importFromLocal(formData) {
    let progressBar = $(".progress");
    let progressBarText = progressBar.find(".progress-bar");
    $.ajax({
        type: "POST",
        url: "/api/rules/import/",
        headers: {"X-CSRFToken": getCookie("csrftoken")},
        data: formData,
        processData: false,
        contentType: false,
        xhr: function () {
            let xhr = new XMLHttpRequest();
            xhr.upload.addEventListener("progress", function (e) {
                if (e.lengthComputable) {
                    let percentComplete = (e.loaded / e.total) * 100;
                    progressBarText.css("width", percentComplete + "%").attr("aria-valuenow", percentComplete);
                    progressBarText.text(percentComplete.toFixed(2) + "%");
                }
            });
            return xhr;
        },
        success: function (response) {
            // Handle the success response
            // Run getImportRuleCount on a loop every 5 seconds

            refreshImportedRuleCount(response["import_id"]);

            progressBar.hide(); // Hide the progress bar on success
        },
        error: function (error) {
            // Handle the error response
            console.error("Upload error:", error);
        },
    });
    progressBar.show(); // Show the progress bar when the upload starts
}

function addImportFormEventOnSubmitHandler(formElem) {
    let formSelectElem = $(formElem).find("select").first();
    let formInputElem = $(formElem).find("input").first();

    let formData = new FormData();

    for (let i = 0; i < formInputElem.prop("files").length; i++) {
        formData.append('file', formInputElem.prop("files")[i]);
    }
    if (formSelectElem.val() === "local") {
        importFromLocal(formData);
    }
}

$(document).ready(function () {
    initializeImportForm();
});