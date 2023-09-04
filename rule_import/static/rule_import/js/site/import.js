function initializeImportForm() {
    let optionSelect = $("#import-option-select");
    optionSelect.val("local")
    $(optionSelect).on("change", function(){
        updateImportForm($(this))
    });
    $("#import-form").on("submit", function(event){
       event.preventDefault();
       addImportFormEventOnSubmitHandler(this)
    })
}

function updateImportForm(formSelectElem) {
    let importInput = formSelectElem.parent().find("input").first();
    if (formSelectElem.val() == "local") {
        $(importInput).attr("type", "file")
        $(importInput).attr("placeholder", "Browse a file or archive on disk.")
    } else if (formSelectElem.val() == "github") {
        $(importInput).attr("type", "url")
        $(importInput).attr("placeholder", "Import from a Github repo containing YARA rules.")
    } else if (formSelectElem.val() == "url") {
        $(importInput).attr("type", "url")
        $(importInput).attr("placeholder", "Import from an archive containing YARA rules.")
    }
}

function addImportFormEventOnSubmitHandler(formElem){
    let formSelectElem = $(formElem).find("select").first();
    let formInputElem = $(formElem).find("input").first();

    let formData = new FormData();

    for (var i = 0; i < formInputElem.prop("files").length; i++) {
        formData.append('file', formInputElem.prop("files")[i]);
    }
    if (formSelectElem.val() == "local") {
          let progressBar = $(".progress");
          let progressBarText = progressBar.find(".progress-bar");

          $.ajax({
            type: "POST",
            url: "/api/import/",
            headers: { "X-CSRFToken": getCookie("csrftoken") },
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
              console.log("Upload completed:", response);
              progressBar.hide(); // Hide the progress bar on success
            },
            error: function (error) {
              // Handle the error response
              console.error("Upload error:", error);
            },
          });

          progressBar.show(); // Show the progress bar when the upload starts
    }
}

$(document).ready(function() {
    initializeImportForm();
});