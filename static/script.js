/*
 * script.js
 * Small improvements on top of the HTML pages. The pages and forms still work without it.
 * Each block below runs once the page has loaded and only does something
 * if the elements it needs are on the current page.
 *
 *   1. Sidebar menu, today's date, calorie ring, messages, profile form
 *   2. Hip field on the body-fat calculator (women only)
 *   3. Live food preview while typing the grams
 *   4. Filters that submit on change, and "are you sure?" before deleting
 *   5. "The coach is thinking…" while waiting for an answer
 *   6. Light/dark theme switch
 */


/* ---------- 1. Shared page behaviour ---------- */
document.addEventListener("DOMContentLoaded", function () {

    // Phone menu: the menu button and the dark overlay both open/close the sidebar
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("overlay");
    const menuButton = document.getElementById("menu-button");

    function toggleSidebar() {
        sidebar.classList.toggle("open");
        overlay.classList.toggle("open");
    }
    if (menuButton) {
        menuButton.addEventListener("click", toggleSidebar);
        overlay.addEventListener("click", toggleSidebar);
    }

    // Replace "Today" with the date, e.g. "Monday 26 October"
    const dateLabel = document.getElementById("today-date");
    if (dateLabel) {
        dateLabel.textContent = new Date().toLocaleDateString("en-GB", {
            weekday: "long", day: "numeric", month: "long",
        });
    }

    // Calorie ring: show the eaten percentage of the circle (see "Calorie ring" in style.css)
    document.querySelectorAll(".ring").forEach(function (ring) {
        const fill = ring.querySelector(".ring-fill");
        const circumference = 326.7; // 2 × π × 52, the circle's radius
        const progress = Math.min(Number(ring.dataset.progress) || 0, 100);

        // A short delay so the ring visibly fills up when the page opens
        setTimeout(function () {
            fill.style.strokeDashoffset = circumference * (1 - progress / 100);
        }, 100);
    });

    // Success messages fade out after 3 seconds (error messages stay)
    document.querySelectorAll(".flash-success").forEach(function (message) {
        setTimeout(function () { message.classList.add("fade"); }, 3000);
        setTimeout(function () { message.remove(); }, 3500);
    });

    // Profile form: outline any invalid box in red and stop the form from sending.
    // The server checks everything again anyway.
    const form = document.getElementById("profile-form");
    if (form) {
        form.addEventListener("submit", function (event) {
            let valid = true;
            form.querySelectorAll("input[type=number], input[type=text]").forEach(function (input) {
                const ok = input.checkValidity();
                input.classList.toggle("invalid", !ok);
                if (!ok) valid = false;
            });
            if (!valid) {
                event.preventDefault();
                form.querySelector(".invalid").focus();
            }
        });
    }
});


/* ---------- 2. Fields shown for one sex only ---------- */
// Used by the hip box on the body-fat calculator: <div data-show-for="female">.
// A hidden box is also disabled, so it isn't sent with the form.
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-show-for]").forEach(function (slot) {
        const form = slot.closest("form");
        const input = slot.querySelector("input");

        function update() {
            const checked = form.querySelector("input[name=sex]:checked");
            const show = checked !== null && checked.value === slot.dataset.showFor;
            slot.hidden = !show;
            input.disabled = !show;
        }

        form.querySelectorAll("input[name=sex]").forEach(function (radio) {
            radio.addEventListener("change", update);
        });
        update();
    });
});


/* ---------- 3. Live food preview ---------- */
// Recalculates calories and macros as the grams change: value per 100 g × grams ÷ 100.
// This is only a preview; the saved numbers are calculated again in Python.
document.addEventListener("DOMContentLoaded", function () {
    const preview = document.getElementById("food-preview");
    const gramsInput = document.getElementById("grams");
    if (!preview || !gramsInput) return;

    function updatePreview() {
        const grams = parseFloat(gramsInput.value) || 0;
        preview.querySelectorAll("[data-per100g]").forEach(function (number) {
            const per100g = parseFloat(number.dataset.per100g);
            const amount = per100g * grams / 100;
            const decimals = Number(number.dataset.decimals);

            // toFixed rounds; Number() then drops a pointless ".0"
            number.textContent = Number(amount.toFixed(decimals)).toLocaleString("en-GB");
        });
    }

    gramsInput.addEventListener("input", updatePreview);

    // Ready to type a new amount straight away
    gramsInput.focus();
    gramsInput.select();
});


/* ---------- 4. Filters and delete confirmations ---------- */
document.addEventListener("DOMContentLoaded", function () {

    // <select data-auto-submit> reloads the page as soon as an option is picked
    document.querySelectorAll("select[data-auto-submit]").forEach(function (select) {
        select.addEventListener("change", function () {
            select.form.submit();
        });
    });

    // <form data-confirm="Delete …?"> asks first, and only sends if you press OK
    document.querySelectorAll("form[data-confirm]").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            if (!window.confirm(form.dataset.confirm)) {
                event.preventDefault();
            }
        });
    });
});


/* ---------- 5. AI Coach: waiting message ---------- */
// Claude can take a few seconds, so show "The coach is thinking…" and dim the buttons
document.addEventListener("DOMContentLoaded", function () {
    const coachForm = document.getElementById("coach-form");
    if (!coachForm) return;

    coachForm.addEventListener("submit", function () {
        coachForm.classList.add("is-waiting");
    });
});


/* ---------- 6. Light/dark theme switch ---------- */
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-theme-toggle]").forEach(function (button) {
        button.addEventListener("click", function () {
            const root = document.documentElement;
            const newTheme = root.dataset.theme === "dark" ? "light" : "dark";
            root.dataset.theme = newTheme;

            // Remember the choice for next time
            try {
                localStorage.setItem("theme", newTheme);
            } catch (error) {
                // Some browsers block storage (e.g. private mode); the theme still changes on this page
            }

            // Lets progress.js redraw the charts in the new colours
            document.dispatchEvent(new CustomEvent("themechange"));
        });
    });
});
