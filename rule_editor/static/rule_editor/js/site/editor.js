// Define the CodeMirror editor
let editor;

// Initialize the CodeMirror editor and set up its configuration
function initializeEditor() {
    editor = CodeMirror.fromTextArea(document.getElementById("editor"), {
        lineNumbers: true,
        mode: "yara",
        gutter: true,
        theme: "base16-dark",
        extraKeys: {
            // Add a key binding for Ctrl+S (Cmd+S on Mac)
            "Ctrl-S": saveEditorContent
        }
    });

    // Load YARA rule content from API if available
    loadYaraRuleContent();

    // Add click handler to the "Save" button
    $("#save-button").click(saveEditorContent);
}

// Load YARA rule content from the API
function loadYaraRuleContent() {
    const matches = window.location.href.match(/\/rules\/([^\/]+)/);
    if (!matches) {
        editor.setValue("\n".repeat(25));
        return;
    }

    $.ajax({
        url: `/api/rules/${matches[1]}`,
        method: "GET",
        success: function(response) {
            editor.setValue(response["yara_rule"]["rule"]);
        },
        error: function(xhr, status, error) {
            editor.setValue("\n".repeat(25));
            console.error("API error:", error);
        }
    });
}

// Save the editor's content to the API
function saveEditorContent() {
    const matches = window.location.href.match(/\/rules\/([^\/]+)/);
    if (!matches) {
        return;
    }

    // Get the YARA rule content from the editor
    const yaraRule = editor.getValue();

    // Create a JSON object with the YARA rule
    const dataToSend = {
        "yara_rule": yaraRule
    };

    // Send the AJAX PUT request
    $.ajax({
        type: "PUT",
        url: `/api/rules/${matches[1]}/editor`,
        data: JSON.stringify(dataToSend),
        headers: { "X-CSRFToken": getCookie("csrftoken") },
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function(response) {
            toastr.success('Rule has been validated and saved.', 'Saved Rule.');
        },
        error: function(jqXHR) {
            const errorResponse = JSON.parse(jqXHR.responseText)["error"];
            if (errorResponse) {
                toastr.error(errorResponse, "Parsing Error");
            }
        }
    });
}

// Function to open the debug side panel
function openDebugSidePanel() {
    const matches = window.location.href.match(/\/rules\/([^\/]+)/);
    if (!matches) {
        editor.setValue("\n".repeat(25));
        return;
    }

    // Fetch YARA rule details from the API
    $.ajax({
        url: `/api/rules/${matches[1]}/editor`,
        method: "GET",
        success: function(response) {
            const rule = response["yara_rule"];
            const variableTable = generateVariableTable(rule);
            const importsSection = generateImportsSection(rule);

            // Update the side panel content
            updateSidePanelContent(rule, variableTable, importsSection);
        },
        error: function(xhr, status, error) {
            console.error("API error:", error);
        }
    });
}

// Generate the Variables table HTML
function generateVariableTable(rule) {
    let variableTable = "";
    if (rule["strings"]) {
        variableTable = "<hr><h6>Variables</h6>";
        rule["strings"].forEach(function(string) {
            const modifierListBody = generateModifierList(string);
            const modifierList = `<ul class="list-group">${modifierListBody}</ul>`;
            variableTable += `<tr>
                <td>${escapeHtml(string["name"])}</td>
                <td>${escapeHtml(string["value"])}</td>
                <td>${string["type"]}</td>
                <td>${modifierList}</td>
            </tr>`;
        });
    }
    return `<table class="table info-table">
        <tbody>
            <thead>
                <tr>
                    <th>Variable</th>
                    <th>Value</th>
                    <th>Type</th>
                    <th>Modifiers</th>
                </tr>
            </thead>
            ${variableTable}
        </tbody>
    </table>`;
}

// Generate the Modifiers list for a string
function generateModifierList(string) {
    let modifierListBody = "";
    if (string["modifiers"]) {
        string["modifiers"].forEach(function(modifier) {
            modifierListBody += `<li class="list-group-item">${modifier}</li>`;
        });
    }
    return modifierListBody;
}

// Generate the Imports section HTML
function generateImportsSection(rule) {
    let importsSection = "";
    if (rule["imports"]) {
        importsSection = "<h6>Imports</h6>";
        rule["imports"].forEach(function(_import) {
            importsSection += `<li class="list-group-item"><code>${_import}</code></li>`;
        });
    }
    return importsSection;
}

// Update the content of the side panel
function updateSidePanelContent(rule, variableTable, importsSection) {
    const html = `
        <h6>Condition</h6>
        <code>${rule["condition_terms"].join(" ")}</code>
        <br><br>
        ${importsSection}
        <br><br>
        ${variableTable}
    `;
    $("#side-panel-popout-title").text("Debug Rule");
    $("#side-panel-popout-body").html(html);
}

// Call the openDebugSidePanel function when needed
function callOpenDebugSidePanel() {
    openDebugSidePanel();
}

// Initialize the editor when the page is loaded
$(document).ready(function() {
    initializeEditor();
});
