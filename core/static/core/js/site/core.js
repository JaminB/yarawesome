function escapeHtml(html) {
  var element = document.createElement("div");
  element.textContent = html;
  return element.innerHTML;
}