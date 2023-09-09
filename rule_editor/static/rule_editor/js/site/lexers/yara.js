
function updateIdentifierCount(identifierCount){
    if(document.getElementById("identifier-count") !== null){
        document.getElementById("identifier-count").innerText = identifierCount;
    }
}

function updateVariableCount(variableCount){
    if(document.getElementById("variable-count") !== null){
        document.getElementById("variable-count").innerText = variableCount;
    }
}

function updateWarningCount(errorCount){
    if(document.getElementById("warning-count") !== null){
        document.getElementById("warning-count").innerText = errorCount;
    }
}

CodeMirror.defineMode("yara", function(config, parserConfig) {
  var keywords = [
    "all", "and", "any", "ascii", "at", "base64", "base64wide", "condition",
    "contains", "endswith", "entrypoint", "false", "filesize", "for", "fullword", "global",
    "import", "icontains", "iendswith", "iequals", "in", "include", "int16", "int16be",
    "int32", "int32be", "int8", "int8be", "istartswith", "matches", "meta", "nocase",
    "none", "not", "of", "or", "private", "rule", "startswith", "strings",
    "them", "true", "uint16", "uint16be", "uint32", "uint32be", "uint8", "uint8be",
    "wide", "xor", "defined"
  ];
  let singleLineComment = RegExp(/\/\/.*/);
  let containsCommentStart = RegExp(/\/\*/);
  let containsCommentEnd = RegExp(/\*\//);
  let identifierRegex = RegExp( /^[^\s=]+(?=\s*=)/);
  let variableRegex = RegExp(/\$\w*/);
  let isNumericRegex = RegExp(/^[0-9]+(?:\.[0-9]*)?$/);
  let isBoolRegex = RegExp(/^(true|false)$/);

  return {
    startState: function() {
      return {
        tokenize: null,
        insideComment: false,
        insideRuleDefinition: false,
        insideMetaSection: false,
        insideStringsSection: false,
        insideStringsByteAssignment: false,
        insideConditionSection: false,
        variableAssignmentLine: false,
        variables: [],
        identifiers: [],
        warnings: [],
      };
    },

    token: function(stream, state) {
      if (stream.sol()) {
        // Handle state changes at the start of a line if needed
        //console.log(state)
        updateIdentifierCount(state.identifiers.length);
        updateVariableCount(state.variables.length);
        updateWarningCount(state.warnings.length);
      }
      // Match keywords found outside rule definitions
      if (!state.insideRuleDefinition && stream.match("import")) {
          return "keyword";
      }

      if (!state.insideRuleDefinition && stream.match("rule")) {
          return "keyword";
      }

      // Match single line comments
      if (stream.match(singleLineComment)) {
        return "comment";
      }
      // Check if we've entered into a multiline comment block
      if (!state.insideComment && stream.match(containsCommentStart)){
        state.insideComment = true;
      }
      // Check if we've reached the end of a multiline comment block
      if (state.insideComment && stream.match(containsCommentEnd)){
        state.insideComment = false;
        stream.next();
        return "comment"
      }
      // Highlight comment lines within multiline comment block
      if (state.insideComment){
        stream.next();
        return "comment"
      }
      // Check if we've entered into a rule definition
      // If we are in a variable assignment state then we will not reset the state here
      if (!state.insideRuleDefinition && !state.variableAssignmentLine && stream.match("{")){
        state.insideRuleDefinition = true;
      }
      // Check if we've reached the end of the rule definition
      // If we are in a variable assignment state then we will not reset the state here
      if (state.insideRuleDefinition && !state.variableAssignmentLine && stream.match("}")){
        stream.next();
        return "oblique-text"
      }

      // Bold text inside of rule block and apply keyword and variable formatting
      if (state.insideRuleDefinition){
        stream.next();
        if (stream.match("meta:", false)){
            stream.match("meta");
            state.insideMetaSection = true;
            state.insideStringsSection = false;
            state.insideStringsByteAssignment = false;
            state.insideConditionSection = false;
            state.variableAssignmentLine = false;
            return "oblique-text keyword"

        }
        // Highlight our strings section
        else if (stream.match("strings:", false)){
            stream.match("strings");
            state.insideMetaSection = false;
            state.insideStringsSection = true;
            state.insideStringsByteAssignment = false;
            state.insideConditionSection = false;
            state.variableAssignmentLine = false;
            return "oblique-text keyword"

        }
        // Highlight our condition section
        else if(stream.match("condition:", false)){
            stream.match("condition");
            state.insideMetaSection = false;
            state.insideStringsSection = false;
            state.insideStringsByteAssignment = false;
            state.insideConditionSection = true;
            state.variableAssignmentLine = false;
            return "oblique-text keyword"
        }
        // Highlight our variables inside the strings section
        if (state.insideStringsSection){
            if (stream.match(variableRegex)){
                var variableName = stream.string.trim().split("=")[0].trim();
                state.variables.push(variableName);
                state.variableAssignmentLine = true;
                return "oblique-text variable-2"
            }
        }
        // Highlight our variables inside the condition section
        if (state.insideConditionSection){
            state.variableAssignmentLine = false;
            if (stream.match(variableRegex)){
                if (state.variables.indexOf(stream.string.slice(stream.start, stream.pos).trim()) != -1) {
                    return "oblique-text variable-2"
                }
                else {
                    state.warnings.push("Undeclared variable.")
                    return "string error"
                }

            }
        }
        // Highlight our identifiers inside the meta section
        if (state.insideMetaSection){
            if (stream.match(identifierRegex)){
                var identifierName = stream.string.trim().split("=")[0].trim();
                state.identifiers.push(identifierName);
                state.variableAssignmentLine = true;
                return "oblique-text variable-3";
            }
        }
        // Highlight the assigned values for either identifier or variable assignment lines
        if (state.variableAssignmentLine){
            var assignedValue = stream.string.trim().split("=")[1];
            var wrapAroundValue = stream.string.trim();
            if (assignedValue){
                assignedValue = assignedValue.trim();
                if (isNumericRegex.test(assignedValue) || isBoolRegex.test(assignedValue)){
                    return "oblique-text number-2";
                }
                else if (assignedValue.startsWith("{")) {
                    return "oblique-text hex-2";
                }
                else if (assignedValue.slice(-1) == '"'){
                    return "oblique-text string";
                }
                else {
                    return "string";
                }
            }
            // Probably wrapped around common in byte declarations (E.G {})
            else if (wrapAroundValue) {
                return "oblique-text hex-2"
            }
        }
        return "oblique-text"
      }
      stream.next()
    }
  };
})