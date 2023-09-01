function setupEditor() {
    var editor = CodeMirror.fromTextArea(document.getElementById("editor"), {
      lineNumbers: true,
      mode:  "yara",
      gutter: true,
      theme: "base16-dark"
    });
    let matches = window.location.href.match(/\/editor\/([^\/]+)/);
    if (matches && matches.length > 1) {
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
    else {
      editor.setValue("\n".repeat(25));
    }
    return editor;
}

function openDebugSidePanel(){
    let matches = window.location.href.match(/\/editor\/([^\/]+)/);
    if (matches && matches.length > 1) {
      $.ajax({
          url: `/api/rules/${matches[1]}/debug`,
          method: "GET",
          success: function(response) {
            var rule = response["yara_rule"];
            let variableTbody = "";
            $("#side-panel-popout-title").text("Debug Rule");
            rule["strings"].forEach(function(string){
                let modifierListBody = "";
                if (string["modifiers"]) {
                    string["modifiers"].forEach(function(modifier){
                        modifierListBody += `<li class="list-group-item">${modifier}</li>`
                    });
                }
                let modifierList = `<ul class="list-group">${modifierListBody}</ul>`;
                variableTbody += `<tr>
                    <td>
                        ${escapeHtml(string["name"])}
                    </td>
                    <td>
                        ${escapeHtml(string["value"])}
                    </td>
                    <td>
                        ${string["type"]}
                    </td>
                    <td>
                        ${modifierList}
                    </td>
                </tr>`
            })
            let variableTable = `<table class="table info-table">
                <tbody>
                    <thead>
                        <tr>
                            <th>Variable</th>
                            <th>Value</th>
                            <th>Type</th>
                            <th>Modifiers</th>
                        </tr>
                    </thead>
                    ${variableTbody}
                </tbody>
            </table>`

            let html = `<h6>Variables</h6>
            <hr>
            ${variableTable}`
            $("#side-panel-popout-body").html(html);
          },
          error: function(xhr, status, error) {
            console.error("API error:", error);
          }
      });
    }
    else {
      editor.setValue("\n".repeat(25));
    }
}

