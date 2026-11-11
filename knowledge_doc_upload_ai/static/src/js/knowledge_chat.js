/** @odoo-module **/
/**
 * AI Knowledge — Help Knowledge Chat
 *
 * Zero-dependency approach: uses a plain setTimeout loop to detect when
 * the Knowledge form view is present, then injects a vanilla-JS chat widget
 * directly into the DOM. No OWL, no services, nothing that can break Odoo.
 */

(function () {
    "use strict";

    const ROUTE = "/knowledge/chat/search";
    const CHECK_INTERVAL = 800; // ms between DOM checks

    let widgetMounted = false;
    let widgetEl = null;

    // ── Markdown renderer ─────────────────────────────────────────────────────
    function md(text) {
        if (!text) return "";
        return text
            .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
            .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g,
                '<a href="$2" target="_blank" rel="noopener">$1</a>')
            .replace(/^• (.+)$/gm, "<li>$1</li>")
            .replace(/\*([^*\n]+)\*/g, "<em>$1</em>")
            .replace(/\n/g, "<br>")
            .replace(/(<li>[^<]*<\/li>(<br>)*)+/g,
                (m) => "<ul>" + m.replace(/<br>/g, "") + "</ul>");
    }

    // ── Build the widget HTML ─────────────────────────────────────────────────
    function createWidget() {
        const div = document.createElement("div");
        div.id = "o_ai_kc_root";
        div.innerHTML = `
            <div id="o_ai_kc_panel" style="display:none">
                <div id="o_ai_kc_header">
                    <span><i class="fa fa-search"></i> Help Knowledge</span>
                    <button id="o_ai_kc_close"><i class="fa fa-times"></i></button>
                </div>
                <div id="o_ai_kc_msgs">
                    <div id="o_ai_kc_welcome">
                        <p>Ask a question and I'll search the Knowledge articles for you.</p>
                        <div id="o_ai_kc_chips"></div>
                    </div>
                </div>
                <div id="o_ai_kc_inputrow">
                    <input id="o_ai_kc_input" type="text" placeholder="Type your question…" />
                    <button id="o_ai_kc_send"><i class="fa fa-paper-plane"></i></button>
                </div>
            </div>
            <button id="o_ai_kc_fab">
                <i class="fa fa-comments"></i>
                <span>Help Knowledge</span>
            </button>
        `;

        const suggestions = [
            "How to process an order?",
            "Logical container issues",
            "How to rollback an order",
            "Philippines order process",
        ];
        const chips = div.querySelector("#o_ai_kc_chips");
        suggestions.forEach((s) => {
            const btn = document.createElement("button");
            btn.className = "o_ai_kc_chip";
            btn.textContent = s;
            btn.onclick = () => { doSend(s, div); };
            chips.appendChild(btn);
        });

        // Toggle open/close
        div.querySelector("#o_ai_kc_fab").onclick = () => toggle(div);
        div.querySelector("#o_ai_kc_close").onclick = () => toggle(div);

        // Send on Enter or button click
        const input = div.querySelector("#o_ai_kc_input");
        input.onkeydown = (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                doSend(input.value, div);
            }
        };
        div.querySelector("#o_ai_kc_send").onclick = () => doSend(input.value, div);

        return div;
    }

    function toggle(div) {
        const panel = div.querySelector("#o_ai_kc_panel");
        const fab = div.querySelector("#o_ai_kc_fab");
        const open = panel.style.display !== "none";
        panel.style.display = open ? "none" : "flex";
        fab.classList.toggle("o_ai_kc_fab_open", !open);
        if (!open) {
            setTimeout(() => {
                const inp = div.querySelector("#o_ai_kc_input");
                if (inp) inp.focus();
            }, 60);
        }
    }

    let busy = false;

    async function doSend(query, div) {
        query = (query || "").trim();
        if (!query || busy) return;
        busy = true;

        // Clear input
        const input = div.querySelector("#o_ai_kc_input");
        if (input) input.value = "";

        // Hide welcome
        const welcome = div.querySelector("#o_ai_kc_welcome");
        if (welcome) welcome.style.display = "none";

        const msgs = div.querySelector("#o_ai_kc_msgs");

        // User bubble
        const userBubble = document.createElement("div");
        userBubble.className = "o_ai_kc_msg o_ai_kc_user";
        userBubble.textContent = query;
        msgs.appendChild(userBubble);

        // "AI is thinking..." indicator
        const thinking = document.createElement("div");
        thinking.className = "o_ai_kc_thinking";
        thinking.innerHTML =
            '<div class="o_ai_kc_spinner"></div><span>🤖 AI is thinking...</span>';
        msgs.appendChild(thinking);
        msgs.scrollTop = msgs.scrollHeight;

        // Bot bubble is only added once the answer arrives
        const botBubble = document.createElement("div");
        botBubble.className = "o_ai_kc_msg o_ai_kc_bot";

        try {
            const r = await fetch(ROUTE, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query, limit: 5 }),
            });
            const d = await r.json();
            botBubble.innerHTML = (d.success && d.answer)
                ? md(d.answer)
                : `<em>${d.error || "No results found."}</em>`;
        } catch (e) {
            botBubble.innerHTML = `<em>Error: ${e.message}</em>`;
        } finally {
            thinking.remove();
            msgs.appendChild(botBubble);
            busy = false;
            msgs.scrollTop = msgs.scrollHeight;
        }
    }

    // ── Mount / unmount based on Knowledge presence ───────────────────────────
    function isKnowledge() {
        return !!document.querySelector(".o_knowledge_form_view");
    }

    function mount() {
        if (widgetMounted) return;
        widgetEl = createWidget();
        document.body.appendChild(widgetEl);
        widgetMounted = true;
    }

    function unmount() {
        if (!widgetMounted) return;
        widgetEl.remove();
        widgetEl = null;
        widgetMounted = false;
        busy = false;
    }

    // Poll every CHECK_INTERVAL ms
    setInterval(() => {
        if (isKnowledge()) {
            mount();
        } else {
            unmount();
        }
    }, CHECK_INTERVAL);

})();
