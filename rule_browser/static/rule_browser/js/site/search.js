function createSearchRuleViewers(){
    var editor = $(".yara-rule").each(function(){
        CodeMirror.fromTextArea(this, {
          lineNumbers: true,
          lineWrapping: true,
          mode:  "yara",
          gutter: true,
          readOnly: true,
          theme: "base16-dark"
        });
    });
    $(".loader").hide();
}
