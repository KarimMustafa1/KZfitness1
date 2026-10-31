/*
 * progress.js
 * Draws the line charts with Chart.js (static/vendor/chart.umd.min.js):
 *   - body weight (Progress page, and the small chart on the Dashboard)
 *   - calories eaten per day, with the daily target as a dashed line
 *   - strength for one exercise: heaviest weight and estimated 1RM

*/
document.addEventListener("DOMContentLoaded", function () {

    // ---------- Read the chart data from the page ----------
    const dataElement = document.getElementById("chart-data");
    if (!dataElement) {
        return; // no charts on this page
    }
    const data = JSON.parse(dataElement.textContent);

    // If Chart.js didn't load, say so instead of leaving empty boxes
    if (typeof Chart === "undefined") {
        document.querySelectorAll(".chart-box").forEach(function (box) {
            box.textContent = "The chart couldn't be loaded.";
        });
        return;
    }

    // ---------- Colours ----------
    // Taken from the CSS variables, so the charts match the light or dark theme
    function readColours() {
        const styles = getComputedStyle(document.documentElement);
        function cssColour(name) {
            return styles.getPropertyValue(name).trim();
        }
        return {
            green: cssColour("--green"),   // weight and calories
            red: cssColour("--red"),       // estimated 1RM
            ink: cssColour("--ink"),       // heaviest weight
            muted: cssColour("--muted"),   // labels and the target line
            grid: cssColour("--line"),     // grid lines
        };
    }

    // ---------- Building blocks ----------

    // One line on a chart. Dashed lines are used for the target and for estimates.
    function makeLine(label, values, colour, dashed) {
        return {
            label: label,
            data: values,
            borderColor: colour,
            backgroundColor: colour,
            borderWidth: dashed ? 2 : 3,
            borderDash: dashed ? [6, 6] : [],   // 6px dash, 6px gap
            pointRadius: 4,
            tension: 0.3,                       // slightly curved line
        };
    }

    // Draws one line chart into the <canvas> with this id.
    // compact = true hides the axes (the small dashboard chart).
    function drawLineChart(canvasId, labels, lines, unit, colours, compact) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            return; // this chart isn't on the page (e.g. not enough data yet)
        }

        // Remove the old chart first when redrawing after a theme change
        const oldChart = Chart.getChart(canvas);
        if (oldChart) {
            oldChart.destroy();
        }

        new Chart(canvas, {
            type: "line",
            data: {
                labels: labels,
                datasets: lines,
            },
            options: {
                maintainAspectRatio: false,   // fill the height set on .chart-box in style.css

                // Hovering anywhere above a date shows every line's value for that date
                interaction: { mode: "index", intersect: false },
                plugins: {
                    // Only show a legend when there is more than one line
                    legend: {
                        display: lines.length > 1,
                        align: "end",
                        labels: { usePointStyle: true, pointStyleWidth: 10, boxHeight: 7, padding: 16 },
                    },
                    // Tooltip text, e.g. "Body weight: 79.6 kg"
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const value = context.parsed.y.toLocaleString("en-GB");
                                return context.dataset.label + ": " + value + " " + unit;
                            },
                        },
                    },
                },
                scales: {
                    x: { display: !compact, grid: { display: false } },
                    y: {
                        display: !compact,
                        grid: { color: colours.grid },
                        ticks: {
                            // Axis labels with the unit, e.g. "2,000 kcal"
                            callback: function (value) {
                                return value.toLocaleString("en-GB") + " " + unit;
                            },
                        },
                    },
                },
            },
        });
    }

    // ---------- Draw every chart that has data ----------
    function drawAllCharts() {
        const colours = readColours();

        // Same font and text colour as the rest of the app
        Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
        Chart.defaults.color = colours.muted;

        // Body weight
        if (data.weight) {
            const weightLine = makeLine("Body weight", data.weight.values, colours.green, false);
            if (data.weight.compact) {
                weightLine.pointRadius = 2;
            }
            drawLineChart("weight-chart", data.weight.labels, [weightLine], "kg", colours, data.weight.compact);
        }

        // Calories eaten, plus the target as a flat dashed line
        if (data.calories) {
            const calorieLines = [makeLine("Calories eaten", data.calories.values, colours.green, false)];
            if (data.calories.target) {
                // The same target value for every date makes a straight line
                const targetValues = data.calories.labels.map(function () {
                    return data.calories.target;
                });
                const targetLine = makeLine("Daily target", targetValues, colours.muted, true);
                targetLine.pointRadius = 0;
                calorieLines.push(targetLine);
            }
            drawLineChart("calorie-chart", data.calories.labels, calorieLines, "kcal", colours, false);
        }

        // Strength: heaviest weight (solid) and estimated 1RM (dashed)
        if (data.strength) {
            drawLineChart(
                "strength-chart",
                data.strength.labels,
                [
                    makeLine("Heaviest weight", data.strength.heaviest, colours.ink, false),
                    makeLine("Estimated 1RM", data.strength.estimated_1rm, colours.red, true),
                ],
                "kg",
                colours,
                false
            );
        }
    }

    drawAllCharts();

    // Redraw in the new colours when the theme switch is pressed (see script.js)
    document.addEventListener("themechange", drawAllCharts);
});
