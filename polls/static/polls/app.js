(function ($) {
  "use strict";

  function csrfToken() {
    var match = document.cookie.match(/(?:^|; )csrftoken=([^;]*)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function messageFrom(response) {
    if (!response) return "Something went wrong. Please try again.";
    var data = response.responseJSON || response;
    if (typeof data === "string") return data;
    if (data.detail) return data.detail;
    var first = Object.keys(data)[0];
    if (first) {
      var value = data[first];
      return Array.isArray(value) ? value[0] : String(value);
    }
    return "Something went wrong. Please try again.";
  }

  window.ClinDocs = {
    api: function (method, url, data) {
      var isFormData = data instanceof window.FormData;
      return $.ajax({
        url: url,
        method: method,
        data: data === undefined ? undefined : (isFormData ? data : JSON.stringify(data)),
        contentType: isFormData ? false : "application/json",
        processData: !isFormData,
        headers: { "X-CSRFToken": csrfToken() }
      });
    },
    toast: function (message, isError) {
      var toast = $("<div>").addClass("app-toast").toggleClass("error", Boolean(isError)).text(message);
      $("#toast-region").append(toast);
      window.setTimeout(function () { toast.fadeOut(180, function () { toast.remove(); }); }, 4200);
    },
    errorMessage: messageFrom,
    escape: function (value) {
      return String(value == null ? "" : value).replace(/[&<>"']/g, function (char) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char];
      });
    },
    statusBadge: function (status) {
      var value = status || "draft";
      var label = value.replace(/_/g, " ").replace(/\b\w/g, function (letter) { return letter.toUpperCase(); });
      return '<span class="status-badge status-' + this.escape(value) + '">' + this.escape(label) + "</span>";
    }
  };

  $(function () {
    var collapsed = localStorage.getItem("clindocs-sidebar-collapsed") === "true";
    if (collapsed) $("#app-shell").addClass("collapsed");
    $("#sidebar-toggle").on("click", function () {
      $("#app-shell").toggleClass("collapsed");
      localStorage.setItem("clindocs-sidebar-collapsed", $("#app-shell").hasClass("collapsed"));
    });
  });
})(jQuery);