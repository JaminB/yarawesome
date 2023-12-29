function download(filename, text) {
    let elem = document.createElement('a');
    elem.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
    elem.setAttribute('download', filename);

    elem.style.display = 'none';
    document.body.appendChild(elem);

    elem.click();

    document.body.removeChild(elem);
}

/**
 * Deletes a collection.
 *
 * @param elem - The source element.
 * @param {function} onSuccess - Success callback function.
 * @param {function} onFailure - Failure callback function.
 */
function deleteCollection(elem, onSuccess, onFailure) {
    let sourceElement = $(elem);
    let collectionId = $(sourceElement).data("collectionId");
    console.log(sourceElement);
    $(sourceElement).prop("disabled", true);
    toastr.warning("Deleting collection...");
    $.ajax({
        url: `/api/collections/${collectionId}/`,
        type: 'DELETE',
        headers: {"X-CSRFToken": getCookie("csrftoken")},
        contentType: "application/json; charset=utf-8",
        success: function (response) {
            if (onSuccess !== undefined) {
                onSuccess(response);
            } else {
                window.location.reload();
            }
        },
        error: function (response) {
            if (onFailure !== undefined) {
                onFailure(response);
            } else {
                toastr.error("Failed to delete collection.");
            }
        }
    });
}


function downloadCollection(elem, onSuccess, onFailure) {
    // Get the source element and collection ID from the event target.
    let sourceElement = $(elem);
    let collectionId = $(sourceElement).data("collectionId");
    window.location="/api/collections/" + collectionId + "/raw/";
}

function editCollection(elem, onSuccess, onFailure) {
    // Get the source element and collection ID from the event target.
    let sourceElement = $(elem);
    let collectionId = $(sourceElement).data("collectionId");

    // Get collection information from input fields.
    let collectionName = $("#collection-name-input").val();
    let collectionDescription = $("#collection-description-input").val();
    let collectionIcon = $("#collection-icon").data("icon");

    // Prepare the payload for the PUT request.
    let payload = {
        "name": collectionName,
        "description": collectionDescription,
        "icon": collectionIcon
    };

    // Disable the source element and display an editing message.
    $(sourceElement).prop("disabled", true);
    toastr.info("Editing collection...");

    // Send an AJAX PUT request to edit the collection.
    $.ajax({
        url: `/api/collections/${collectionId}/`,
        type: 'PUT',
        headers: {"X-CSRFToken": getCookie("csrftoken")},
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify(payload),
        success: function (response) {
            if (onSuccess !== undefined) {
                onSuccess(response);
            } else {
                window.location.reload();
            }
        },
        error: function (response) {
            if (onFailure !== undefined) {
                onFailure(response);
            } else {
                toastr.error("Failed to edit collection.");
            }
        }
    });
}

/**
 * Publishes a collection.
 * @param elem - The source element.
 * @param {function} onSuccess - Success callback function.
 * @param {function} onFailure - Failure callback function.
 */
function publishCollection(elem, onSuccess, onFailure) {
    let sourceElement = $(elem);
    let collectionId = $(sourceElement).data("collectionId");
    $(sourceElement).prop("disabled", true);
    toastr.info("Publishing collection...");
    $.ajax({
        url: `/api/collections/${collectionId}/publish/`,
        type: 'PUT',
        headers: {"X-CSRFToken": getCookie("csrftoken")},
        contentType: "application/json; charset=utf-8",
        success: function (response) {
            if (onSuccess !== undefined) {
                onSuccess(response);
            } else {
                window.location.reload();
            }
        },
        error: function (response) {
            if (onFailure !== undefined) {
                onFailure(response);
            } else {
                toastr.error("Failed to publish collection.");
            }
        }
    });
}

/**
 * Opens the delete collection side panel.
 *
 * @param {function} onSuccess - Success callback function.
 * @param {function} onFailure - Failure callback function.
 */
function openDeleteCollectionSidePanel(onSuccess, onFailure) {
    // Set the collection ID in the side panel
    let sourceElement = event.delegateTarget;
    let collectionId = $(sourceElement).data("collectionId");
    $("#side-panel-popout-title").text(`Delete Collection`);
    let warningMessage = `<p>Deleting this collection will remove it from your personal rule index.</p>`;
    if ($(sourceElement).data("is-public") === "True") {
        warningMessage = `<p>Deleting this collection will remove it from both your personal rule index and the <b><u>public</u></b> rule index.</p>`;
    }
    $("#side-panel-popout-body").html(`
        <p class="lead">Are you sure you want to delete this collection?</p>
        <hr>
        ${warningMessage}
        <br>
        <table class="table table-responsive">
            <tbody>
                <tr>
                    <th>Name</th>
                    <td><code>${$(sourceElement).data("name")}</code></td>
                </tr>
                <tr>
                    <th>Description</th>
                    <td>${$(sourceElement).data("description")}</td>
                </tr>
                <tr>
                    <th>Rule Count</th>
                    <th>${$(sourceElement).data("rule-count")}</th>
                </tr>
            </tbody>
        </table>
        <br>
        <div class="align-center">
            <button id="submit-delete-collection-btn" class="btn btn-danger btn-lg float-end" 
            data-collection-id="${collectionId}">
            <i class="fa-solid fa-trash"></i> Delete</button>
        </div>
        <script>
            $("#submit-delete-collection-btn").click(function() {
                deleteCollection(this, ${onSuccess}, ${onFailure});
            });
        </script>
    `);
}

/**
 * Opens the publish collection side panel.
 */
function openPublishCollectionSidePanel() {
    // Set the collection ID in the side panel
    let sourceElement = event.delegateTarget;
    let collectionId = $(sourceElement).data("collectionId");
    $("#side-panel-popout-title").text(`Publish Collection`);
    $("#side-panel-popout-body").html(`
        <p class="lead">Are you sure you want to publish this collection?</p>
        <hr>
        <p>Publishing means that all ${$(sourceElement).data("rule-count")} rule(s) in this collection will be made available <b>publicly</b>.</p>
        <br>
        <table class="table table-responsive">
            <tbody>
                <tr>
                    <th>Name</th>
                    <td><code>${$(sourceElement).data("name")}</code></td>
                </tr>
                <tr>
                    <th>Description</th>
                    <td>${$(sourceElement).data("description")}</td>
                </tr>
                <tr>
                    <th>Rule Count</th>
                    <th>${$(sourceElement).data("rule-count")}</th>
                </tr>
            </tbody>
        </table>
        <br>
        <div class="align-center">
            <button id="submit-publish-collection-btn" class="btn btn-danger btn-lg float-end" data-collection-id="${collectionId}">
            <i class="fa-solid fa-globe"></i> Publish</button>
        </div>
        <script>
            $("#submit-publish-collection-btn").click(function(){
                publishCollection(this, undefined, undefined);
            });
        </script>
    `);
}

/**
 * Handles the icon selection.
 */
function onIconSelect() {
    let collectionIconSelector = $("#collection-icon");
    let selectedIconSrc = $(event.target).parent().find("img").first().attr("src");
    let selectedIconId = $(event.target).parent().find("img").first().data("iconId");
    collectionIconSelector.attr("src", selectedIconSrc);
    collectionIconSelector.data("icon", selectedIconId);
    bootbox.hideAll();
}

/**
 * Displays the icon selector.
 */
function iconSelector() {
    let iconsAvailable = 41;
    let table = `<table class='table table-responsive' style="overflow:auto"><tbody>`;
    let tableRows = "";
    let tableRow = "<tr>";
    for (let i = 1; i < iconsAvailable; i++) {
        tableRow += `<td>
            <div class="collection-icon-container" onClick="onIconSelect()">
                <img src="/static/core/img/icons/collections/${i - 1}.png"  alt="icon-${i - 1}" data-icon-id="${i - 1}">
                <div class="collection-icon-overlay">
                    
                </div>
            </div>
        </td>`;
        if (i % 5 === 0 && i !== 0) {
            tableRow += "</tr>\n";
            tableRows += tableRow;
            tableRow = "<tr>";
        }
    }
    if (iconsAvailable % 5 !== 0) {
        tableRow += "</tr>";
        tableRows += tableRow;
    }
    table = table + tableRows + "</tbody></table>";
    bootbox.dialog({
        title: "Select a Collection Glyph",
        message: table
    });
}

/**
 * Opens the download collection side panel.
 **/
function openDownloadCollectionSidePanel(elem, onSuccess, onFailure) {
    // Set the collection ID in the side panel
    let sourceElement = event.delegateTarget;
    let collectionId = $(sourceElement).data("collectionId");
    $("#side-panel-popout-title").text(`Download Collection`);
    $("#side-panel-popout-body").html(`
        <p class="lead">Download this collection?</p>
        <hr>
        <br>
        <table class="table table-responsive">
            <tbody>
                <tr>
                    <th>Name</th>
                    <td><code>${$(sourceElement).data("name")}</code></td>
                </tr>
                <tr>
                    <th>Description</th>
                    <td>${$(sourceElement).data("description")}</td>
                </tr>
                <tr>
                    <th>Rule Count</th>
                    <th>${$(sourceElement).data("rule-count")}</th>
                </tr>
            </tbody>
        </table>
        <br>
        <div class="align-center">
            <a download id="submit-download-collection-btn" href="/api/collections/${collectionId}/raw/"  class="btn btn-danger btn-lg float-end" data-collection-id="${collectionId}">
            <i class="fa-solid fa-download" ></i> Download</a>
        </div>
        <script>
                $("#submit-download-collection-btn").on("click", function(){
                    toastr.info("Downloading collection, it may take a few seconds to start.");
                });
        </script>
    `);
}

/**
 * Opens the edit collection side panel.
 *
 * @param {function} onSuccess - Success callback function.
 * @param {function} onFailure - Failure callback function.
 */
function openEditCollectionSidePanel(onSuccess, onFailure) {
    // Set the collection ID in the side panel
    let sourceElement = event.delegateTarget;
    let collectionId = $(sourceElement).data("collectionId");
    let collectionName = $(sourceElement).data("name");
    let collectionDescription = $(sourceElement).data("description");
    let collectionIcon = $(sourceElement).data("icon");
    $("#side-panel-popout-title").text(`Edit Collection`);
    let warningMessage = `<p>You can make changes to ${collectionName} from here.</p>`;
    if ($(sourceElement).data("is-public") === "True") {
        warningMessage = `<p>${warningMessage} This is a <u><b>public</b></u> collection. Changes to this collection will impact the public instance.</p>`;
    }

    $("#side-panel-popout-body").html(`
        <p class="lead">Edit this collection?</p>
        <hr>
        ${warningMessage}
        <br>
        <form id="collection-edit-form">
            <div class="form-group">
                <!-- Label above the input -->
                <label for="collection-name-input"><b>Name</b></label>
                <div class="input-group">
                    <!-- Add an image holder here -->
                    <div class="input-group-prepend" onClick="iconSelector()">
                        <span class="input-group-text">
                            <img id="collection-icon" class="collection-icon" data-icon="${collectionIcon}" src="/static/core/img/icons/collections/${collectionIcon}.png" alt="Image" width="30" height="30">
                        </span>
                    </div>
        
                    <!-- Name input -->
                    <input type="text" class="form-control collection-name-input" id="collection-name-input"
                           name="collection-name-input"
                           placeholder="Collection Name" value="${collectionName}">
                </div>
            </div>
            <br>
            <div class="form-group">
                <label for="collection-description-input"><b>Description</b></label>
                <textarea rows="5" class="form-control" id="collection-description-input"
                          name="collection-description-input"
                          type="text">${collectionDescription}</textarea>
            </div>
        </form>
        <br>
        <div class="align-center">
            <button id="save-changes-btn" class="btn btn-success btn-lg float-end" 
            data-collection-id="${collectionId}">
            <i class="fa-solid fa-floppy-disk"></i> Save</button>
        </div>
        <script>
            $("#save-changes-btn").click(function(){
                editCollection(this, ${onSuccess}, ${onFailure});
            });
        </script>
    `);
}

/**
 * Initializes the collection side panel.
 */
function initializeCollectionSidePanel() {
    // Set the collection ID in the side panel
    $(".publish-collection-button").click(function () {
        openPublishCollectionSidePanel(function () {
            window.location.href = '/collections/mine';
        });
    });
    $(".edit-collection-btn").click(function () {
        openEditCollectionSidePanel(function () {
            window.location.href = '/collections/mine';
        })
    });
    $("#download-collection-btn").click(function () {
        openDownloadCollectionSidePanel(this, undefined, undefined);
    })

}

/**
 * Initializes the modals.
 */
function initializeModals() {
    $('.collection-icon').click(function () {
        bootbox.dialog({
            message: `<center><h3>${$("#collection-name").html()}</h3><hr><img class="collection-icon-lg" src="${$('.collection-icon').attr('src')}" /></center>`
        });
    });
}

$(document).ready(function () {
    initializeCollectionSidePanel();
    initializeModals();
});


/**
 * Edits a collection using an AJAX PUT request.
 *
 * @param {Function} onSuccess - A callback function to execute on a successful edit.
 * @param {Function} onFailure - A callback function to execute on a failed edit.
 */
