function uploadFromLocal(formData) {
    /**
     * Upload a file from the local machine to the server.
     * @type {*|jQuery|HTMLElement}
     */
    let progressBar = $(".progress");
    let progressBarText = progressBar.find(".progress-bar");
    $.ajax({
        type: "POST",
        url: "/api/lab/upload/",
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
            toastr.success("Upload successful! This file will now appear in your lab.", "Upload Success");
            progressBar.hide();
            setTimeout(function () {
                window.location.reload();
            }, 4000);
        },
        error: function (xhr, status, error) {
            // Handle the error response
            toastr.error(`Upload error: ${JSON.parse(xhr.responseText)["error"]}`, "Upload Error");
        },
    });
    progressBar.show();
}

function addUploadFormEventOnSubmitHandler(formElem) {
    /**
     * Add the event handler for the upload form.
     * @type {*|jQuery}
     */
    let formInputElem = $(formElem).find("input").first();

    let formData = new FormData();

    for (let i = 0; i < formInputElem.prop("files").length; i++) {
        formData.append('file', formInputElem.prop("files")[i]);
    }
    uploadFromLocal(formData);
}

function initializeUploadForm() {
    /**
     * Initialize the upload form and add the event handlers.
     * @type {*|jQuery|HTMLElement}
     */
    let optionSelect = $("#upload-option-select");
    $("#upload-form").on("submit", function (event) {
        event.preventDefault();
        addUploadFormEventOnSubmitHandler(this)
    });
    $("#upload-input").on("click", function (event) {
        $("#upload-welcome-container").fadeOut();
    });
}

$(document).ready(function () {
    initializeUploadForm();
});