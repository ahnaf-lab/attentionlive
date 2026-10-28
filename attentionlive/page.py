"""The static HTML/SVG/JS page that animates attention weights live.

The page itself never changes; all of its behavior is driven at runtime by
JSON payloads pushed from the server's /events SSE stream (see watch.py).
"""

PAGE_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>attentionlive</title>
<style>
  :root { color-scheme: dark; }
  html, body {
    margin: 0; height: 100%; background: #0b0d12; color: #e7e9ee;
    font-family: system-ui, sans-serif; overflow: hidden;
  }
  #status {
    position: fixed; top: 8px; left: 12px; font-size: 13px; opacity: 0.6;
  }
  #empty {
    position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
    opacity: 0.4; font-size: 15px; text-align: center;
  }
  svg { display: block; width: 100vw; height: 100vh; }
  text.token {
    fill: #e7e9ee; font-size: 20px; text-anchor: middle; dominant-baseline: middle;
    transition: x 0.4s ease, y 0.4s ease;
  }
  line.edge {
    stroke: #6ad7ff;
    transition: x1 0.4s ease, y1 0.4s ease, x2 0.4s ease, y2 0.4s ease,
                stroke-opacity 0.4s ease, stroke-width 0.4s ease;
  }
</style>
</head>
<body>
<div id="status">connecting&hellip;</div>
<div id="empty">type a sentence into the watched scratch file and save it</div>
<svg id="stage" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="glow" x="-200%" y="-200%" width="500%" height="500%">
      <feGaussianBlur stdDeviation="3.2" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <g id="edges"></g>
  <g id="labels"></g>
</svg>
<script>
(function () {
  "use strict";

  var svg = document.getElementById("stage");
  var edgesGroup = document.getElementById("edges");
  var labelsGroup = document.getElementById("labels");
  var statusEl = document.getElementById("status");
  var emptyEl = document.getElementById("empty");
  var NS = "http://www.w3.org/2000/svg";

  var edgeEls = [];
  var labelEls = [];
  var tokenCount = 0;
  var lastPayload = null;

  function stageSize() {
    var rect = svg.getBoundingClientRect();
    return { w: rect.width || window.innerWidth, h: rect.height || window.innerHeight };
  }

  function tokenPosition(i, n, size) {
    var margin = Math.min(size.w * 0.1, 80);
    var usable = Math.max(size.w - margin * 2, 1);
    var x = n <= 1 ? size.w / 2 : margin + (usable * i) / (n - 1);
    return { x: x, y: size.h / 2 };
  }

  function rebuild(n) {
    edgesGroup.textContent = "";
    labelsGroup.textContent = "";
    edgeEls = [];
    labelEls = [];

    for (var i = 0; i < n; i++) {
      for (var j = i + 1; j < n; j++) {
        var line = document.createElementNS(NS, "line");
        line.setAttribute("class", "edge");
        line.setAttribute("filter", "url(#glow)");
        edgesGroup.appendChild(line);
        edgeEls.push({ i: i, j: j, el: line });
      }
    }
    for (var k = 0; k < n; k++) {
      var text = document.createElementNS(NS, "text");
      text.setAttribute("class", "token");
      labelsGroup.appendChild(text);
      labelEls.push(text);
    }
    tokenCount = n;
  }

  function render(payload) {
    var tokens = payload.tokens || [];
    var weights = payload.weights || [];
    var n = tokens.length;

    emptyEl.style.display = n === 0 ? "block" : "none";
    if (n !== tokenCount) rebuild(n);
    if (n === 0) return;

    var size = stageSize();
    var positions = [];
    for (var i = 0; i < n; i++) positions.push(tokenPosition(i, n, size));

    var maxPair = 0.0001;
    var pairWeight = [];
    for (var a = 0; a < edgeEls.length; a++) {
      var pair = edgeEls[a];
      var w = (weights[pair.i][pair.j] + weights[pair.j][pair.i]) / 2;
      pairWeight.push(w);
      if (w > maxPair) maxPair = w;
    }

    for (var b = 0; b < edgeEls.length; b++) {
      var e = edgeEls[b];
      var p1 = positions[e.i];
      var p2 = positions[e.j];
      var rel = pairWeight[b] / maxPair;
      e.el.setAttribute("x1", p1.x);
      e.el.setAttribute("y1", p1.y);
      e.el.setAttribute("x2", p2.x);
      e.el.setAttribute("y2", p2.y);
      e.el.setAttribute("stroke-opacity", (0.05 + 0.9 * rel).toFixed(3));
      e.el.setAttribute("stroke-width", (0.5 + 4.5 * rel).toFixed(2));
    }

    for (var c = 0; c < n; c++) {
      labelEls[c].textContent = tokens[c];
      labelEls[c].setAttribute("x", positions[c].x);
      labelEls[c].setAttribute("y", positions[c].y);
    }
  }

  window.addEventListener("resize", function () {
    if (lastPayload) render(lastPayload);
  });

  var source = new EventSource("/events");
  source.onopen = function () { statusEl.textContent = "connected"; };
  source.onerror = function () { statusEl.textContent = "disconnected, retrying\\u2026"; };
  source.onmessage = function (evt) {
    var payload = JSON.parse(evt.data);
    lastPayload = payload;
    statusEl.textContent = "connected";
    render(payload);
  };
})();
</script>
</body>
</html>
"""

PAGE_HTML_BYTES = PAGE_HTML.encode("utf-8")
