
function deleteCollection() {
    let sourceElement = event.target;
    let collectionId = $(sourceElement).data("collectionId");
    $(sourceElement).prop("disabled", true);
    toastr.warning("Deleting collection...");
    $.ajax({
        url: `/api/collections/${collectionId}/`,
        type: 'DELETE',
        headers: { "X-CSRFToken": getCookie("csrftoken") },
        contentType: "application/json; charset=utf-8",
        success: function (response) {
            window.location.reload();
       }
    });
}

function publishCollection() {
    let sourceElement = event.target;
    let collectionId = $(sourceElement).data("collectionId");
    $(sourceElement).prop("disabled", true);
    toastr.info("Publishing collection...");
    $.ajax({
        url: `/api/collections/${collectionId}/publish/`,
        type: 'PUT',
        headers: { "X-CSRFToken": getCookie("csrftoken") },
        contentType: "application/json; charset=utf-8",
        success: function (response) {
            window.location.reload();
       }
    });
}


function openDeleteCollectionSidePanel() {
    // Set the collection ID in the side panel
    let sourceElement = event.delegateTarget;
    let collectionId = $(sourceElement).data("collectionId");
    $("#side-panel-popout-title").text(`Delete Collection`);
    let warningMessage = `<p>Deleting this collection will remove it from your personal rule index.</p>`
    if ($(sourceElement).data("is-public") === "True") {
        warningMessage = `<p>Deleting this collection will remove it from both your personal rule index and the <b>public</b> rule index</p>`;
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
            <button class="btn btn-danger btn-lg float-end" onclick="deleteCollection()" data-collection-id="${collectionId}">
            <i class="fa-solid fa-trash"></i> Delete</button>
        </div>
    `)
}

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
            <button class="btn btn-danger btn-lg float-end" onclick="publishCollection()" data-collection-id="${collectionId}">
            <i class="fa-solid fa-globe"></i> Publish</button>
        </div>
    `)
}


function initializeCollectionSidePanel() {
    // Set the collection ID in the side panel
    $(".publish-collection-button").click(function () {
        openPublishCollectionSidePanel();
    });
}

function initializeModals(){
    $('.collection-icon').click(function() {
        bootbox.dialog({
            message: `<center><h3>${$("#collection-name").html()}</h3><hr><img style="border-radius:100%" src="${$('.collection-icon').attr('src')}" /></center>`
        })
    });
}

$(document).ready(function () {
    initializeCollectionSidePanel();
    initializeModals();
});