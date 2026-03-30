(function () {
    try {
        var path = String(window.location.pathname || "").toLowerCase();
        var params = new URLSearchParams(window.location.search || "");
        if (path.indexOf("/copilot") === 0 || params.get("embed") === "1") {
            return;
        }

        var style = document.createElement("style");
        style.textContent = "\n" +
            ".copilot-fab{position:fixed;right:18px;bottom:18px;z-index:1200;width:52px;height:52px;border-radius:999px;border:1px solid rgba(91,151,255,.45);background:linear-gradient(135deg,rgba(91,151,255,.2),rgba(0,217,163,.18));color:#dfe9fb;font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:700;cursor:pointer;box-shadow:0 8px 22px rgba(0,0,0,.35)}" +
            ".copilot-modal{position:fixed;inset:0;z-index:1300;background:rgba(3,7,14,.72);display:none;align-items:center;justify-content:center;padding:16px}" +
            ".copilot-shell{width:min(1100px,100%);height:min(760px,92vh);border:1px solid #244073;border-radius:12px;background:#0a101c;overflow:hidden;display:grid;grid-template-rows:44px 1fr}" +
            ".copilot-shell-hd{display:flex;align-items:center;justify-content:space-between;padding:0 10px;border-bottom:1px solid #1f2f51;font-family:'IBM Plex Mono',monospace;font-size:11px;color:#8ca2c8}" +
            ".copilot-shell-hd strong{color:#dce8fb;font-size:12px}" +
            ".copilot-actions{display:flex;gap:6px}" +
            ".copilot-actions button{border:1px solid #284271;background:#101a2d;color:#b7caea;border-radius:6px;padding:5px 9px;font-size:11px;font-family:'IBM Plex Mono',monospace;cursor:pointer}" +
            ".copilot-shell iframe{width:100%;height:100%;border:0;background:#0a101c}";
        document.head.appendChild(style);

        var fab = document.createElement("button");
        fab.className = "copilot-fab";
        fab.id = "copilotFab";
        fab.setAttribute("aria-label", "Open AI Copilot");
        fab.textContent = "AI";

        var modal = document.createElement("div");
        modal.className = "copilot-modal";
        modal.id = "copilotModal";
        modal.setAttribute("aria-hidden", "true");
        modal.innerHTML = "" +
            "<div class='copilot-shell'>" +
            "  <div class='copilot-shell-hd'>" +
            "    <strong>AI Copilot</strong>" +
            "    <div class='copilot-actions'>" +
            "      <button id='copilotFullBtn' type='button'>Full Page</button>" +
            "      <button id='copilotCloseBtn' type='button'>Close</button>" +
            "    </div>" +
            "  </div>" +
            "  <iframe id='copilotFrame' src='/copilot.html?embed=1' title='AI Copilot'></iframe>" +
            "</div>";

        document.body.appendChild(fab);
        document.body.appendChild(modal);

        var closeBtn = document.getElementById("copilotCloseBtn");
        var fullBtn = document.getElementById("copilotFullBtn");

        function openModal() {
            modal.style.display = "flex";
            modal.setAttribute("aria-hidden", "false");
        }

        function closeModal() {
            modal.style.display = "none";
            modal.setAttribute("aria-hidden", "true");
        }

        fab.addEventListener("click", openModal);
        closeBtn.addEventListener("click", closeModal);
        fullBtn.addEventListener("click", function () {
            window.location.href = "/copilot.html";
        });
        modal.addEventListener("click", function (ev) {
            if (ev.target === modal) closeModal();
        });
        document.addEventListener("keydown", function (ev) {
            if (ev.key === "Escape") closeModal();
        });
    } catch (e) {
        // Intentionally silent: widget must never break host page.
    }
})();
