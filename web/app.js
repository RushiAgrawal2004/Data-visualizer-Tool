let jwtToken = localStorage.getItem("jwt_token");
let dataToken = null;
let allColumns = [];
let numericColumns = [];

const el = (id) => document.getElementById(id);

// Visual theme for Plotly charts to match a professional dashboard look
const THEME = {
  colorway: ["#3b82f6", "#60a5fa", "#a78bfa", "#22d3ee", "#34d399", "#f59e0b", "#f43f5e", "#94a3b8"],
  paper_bgcolor: "#0f131a",
  plot_bgcolor: "#0f131a",
  grid: "#1f2a37",
  axis: "#cbd5e1",
  muted: "#9ca3af",
  mean: "#94a3b8",
};

function baseLayout() {
  return {
    paper_bgcolor: THEME.paper_bgcolor,
    plot_bgcolor: THEME.plot_bgcolor,
    font: { color: THEME.axis, family: 'Inter, system-ui, sans-serif' },
    colorway: THEME.colorway,
    margin: { t: 48, r: 24, b: 48, l: 56 },
    legend: { bgcolor: 'rgba(0,0,0,0)', orientation: 'h', x: 0, y: 1.08 },
    xaxis: {
      gridcolor: THEME.grid,
      zeroline: false,
      linecolor: THEME.grid,
      tickcolor: THEME.grid,
      automargin: true,
    },
    yaxis: {
      gridcolor: THEME.grid,
      zeroline: false,
      linecolor: THEME.grid,
      tickcolor: THEME.grid,
      automargin: true,
    },
    hoverlabel: { bgcolor: '#111827', bordercolor: '#1f2937', font: { color: THEME.axis } },
  };
}

function setOptions(select, options, includeEmpty = false) {
  select.innerHTML = "";
  if (includeEmpty) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "None";
    select.appendChild(opt);
  }
  for (const v of options) {
    const opt = document.createElement("option");
    opt.value = v;
    opt.textContent = v;
    select.appendChild(opt);
  }
}

function getHeaders() {
  return {
    "Content-Type": "application/json",
    "x-access-token": jwtToken,
  };
}

async function apiUpload(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch("/api/upload", {
    method: "POST",
    headers: { "x-access-token": jwtToken },
    body: form,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Upload failed");
  return data;
}

async function apiGet(path, params = {}) {
  const usp = new URLSearchParams(params);
  const res = await fetch(`${path}?${usp.toString()}`, {
    headers: { "x-access-token": jwtToken },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || `GET ${path} failed`);
  return data;
}

async function apiPost(path, body = {}) {
  const res = await fetch(path, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || `POST ${path} failed`);
  return data;
}

function renderTable(container, data) {
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const tbody = document.createElement("tbody");

  const headRow = document.createElement("tr");
  for (const c of data.columns) {
    const th = document.createElement("th");
    th.textContent = c;
    headRow.appendChild(th);
  }
  thead.appendChild(headRow);

  for (const row of data.rows) {
    const tr = document.createElement("tr");
    for (const cell of row) {
      const td = document.createElement("td");
      td.textContent = cell;
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }

  table.appendChild(thead);
  table.appendChild(tbody);
  container.innerHTML = "";
  container.appendChild(table);
}

function toggleBarmodeVisibility() {
  const chartType = el("chart-type").value;
  const wrap = el("barmode-wrap");
  wrap.classList.toggle("hidden", chartType !== "Bar graph");
}

function updateControlVisibility() {
  const chartType = el("chart-type").value;
  const xLabel = el("x-select").parentElement;
  const yLabel = el("y-select").parentElement;
  const colorLabel = el("color-select").parentElement;

  // Reset visibility and labels
  xLabel.classList.remove("hidden");
  yLabel.classList.remove("hidden");
  colorLabel.classList.remove("hidden");
  xLabel.querySelector("span").textContent = "X";
  yLabel.querySelector("span").textContent = "Y";

  if (chartType === "Histogram") {
    yLabel.classList.add("hidden");
  } else if (chartType === "Pie Chart") {
    xLabel.querySelector("span").textContent = "Names";
    yLabel.querySelector("span").textContent = "Values";
    colorLabel.classList.add("hidden");
  } else if (chartType === "Line chart") {
    colorLabel.classList.add("hidden");
  }
}

async function refreshPreviewAndDescribe() {
  if (!dataToken) return;
  const [preview, describe] = await Promise.all([
    apiGet("/api/preview", { token: dataToken }),
    apiGet("/api/describe", { token: dataToken }),
  ]);
  renderTable(el("dataframe"), preview);
  renderTable(el("describe"), { columns: ["metric", ...describe.columns], rows: describe.index.map((idx, i) => [idx, ...describe.data[i]]) });
}

function resetSelectors() {
  setOptions(el("x-select"), allColumns);
  setOptions(el("y-select"), numericColumns);
  setOptions(el("color-select"), ["", ...allColumns], true);
  toggleBarmodeVisibility();
  updateControlVisibility();
}

async function handleUploadSubmit(evt) {
  evt.preventDefault();
  const file = el("csv-file").files[0];
  if (!file) {
    el("upload-status").textContent = "Please select a CSV file.";
    return;
  }
  el("upload-status").textContent = "Uploading...";
  try {
    const data = await apiUpload(file);
    dataToken = data.token;
    allColumns = data.columns;
    numericColumns = data.numericColumns;
    el("upload-status").textContent = `Uploaded. ${allColumns.length} columns, ${numericColumns.length} numeric.`;
    resetSelectors();
    await refreshPreviewAndDescribe();
  } catch (err) {
    el("upload-status").textContent = String(err);
  }
}

async function handlePlotClick() {
  if (!dataToken) return;
  const chartType = el("chart-type").value;
  const x = el("x-select").value || null;
  const y = el("y-select").value || null;
  const color = el("color-select").value || null;
  const barmode = el("barmode-select").value || null;

  let payload = { token: dataToken };
  let endpoint = "/api/plot-data";

  switch (chartType) {
    case "Bar graph":
      payload = { ...payload, chart: "bar", x, y, color, barmode };
      break;
    case "Histogram":
      payload = { ...payload, chart: "histogram", x, color };
      break;
    case "Scatter":
      payload = { ...payload, chart: "scatter", x, y, color };
      break;
    case "Pie Chart":
      payload = { ...payload, chart: "pie", values: y, names: x };
      break;
    case "Line chart":
      payload = { ...payload, chart: "line", x, y };
      break;
    case "Box Plot":
      payload = { ...payload, chart: "box", x, y, color };
      break;
    default:
      return;
  }

  try {
    const data = await apiPost(endpoint, payload);
    drawChart(chartType, data);
  } catch (err) {
    alert(String(err));
  }
}

function drawChart(chartType, data) {
  const chartEl = el("chart");
  const layout = baseLayout();

  if (chartType === "Bar graph") {
    const trace = { type: "bar", x: data.x, y: data.y, marker: { line: { color: '#273447', width: 1 } } };
    const traces = [trace];
    if (typeof data.mean === "number") {
      layout.shapes = [{ type: "line", x0: 0, x1: 1, xref: "paper", y0: data.mean, y1: data.mean, line: { dash: "dash", color: THEME.mean } }];
      layout.annotations = [{ xref: "paper", x: 1.0, y: data.mean, xanchor: "right", yanchor: "bottom", text: "mean", showarrow: false }];
    }
    const config = { responsive: true };
    layout.barmode = data.barmode || 'group';
    Plotly.newPlot(chartEl, traces, layout, config);
    return;
  }

  if (chartType === "Line chart") {
    const trace = { type: "scatter", mode: "lines", line: { width: 2 }, x: data.x, y: data.y };
    const traces = [trace];
    if (typeof data.mean === "number") {
      layout.shapes = [{ type: "line", x0: 0, x1: 1, xref: "paper", y0: data.mean, y1: data.mean, line: { dash: "dash", color: THEME.mean } }];
      layout.annotations = [{ xref: "paper", x: 1.0, y: data.mean, xanchor: "right", yanchor: "bottom", text: "mean", showarrow: false }];
    }
    Plotly.newPlot(chartEl, traces, layout, { responsive: true });
    return;
  }

  if (chartType === "Scatter") {
    if (data.series) {
      const traces = data.series.map(s => ({ type: 'scatter', mode: 'markers', name: s.name, x: s.x, y: s.y, marker: { size: 6, line: { width: 1, color: '#273447' } } }));
      Plotly.newPlot(chartEl, traces, layout, { responsive: true });
    } else {
      const trace = { type: "scatter", mode: "markers", x: data.x, y: data.y, marker: { size: 6, line: { width: 1, color: '#273447' } } };
      Plotly.newPlot(chartEl, [trace], layout, { responsive: true });
    }
    return;
  }

  if (chartType === "Histogram") {
    if (data.series) {
      const traces = data.series.map((s) => ({ type: "histogram", name: s.name, x: s.x, opacity: 0.85, marker: { line: { color: '#273447', width: 1 } } }));
      Plotly.newPlot(chartEl, traces, layout, { responsive: true });
    } else {
      Plotly.newPlot(chartEl, [{ type: "histogram", x: data.x, opacity: 0.9, marker: { line: { color: '#273447', width: 1 } } }], layout, { responsive: true });
    }
    return;
  }

  if (chartType === "Pie Chart") {
    const trace = { type: "pie", values: data.values, labels: data.names, textinfo: "label+percent", hole: 0.6, marker: { line: { color: '#0f131a', width: 2 } } };
    Plotly.newPlot(chartEl, [trace], layout, { responsive: true });
    return;
  }

  if (chartType === "Box Plot") {
    if (data.series) {
      const traces = data.series.map(s => ({ type: 'box', name: s.name, x: s.x, y: s.y, boxpoints: false, marker: { color: THEME.colorway[0] } }));
      Plotly.newPlot(chartEl, traces, layout, { responsive: true });
    } else {
      const trace = { type: "box", x: data.x, y: data.y, boxpoints: false };
      Plotly.newPlot(chartEl, [trace], layout, { responsive: true });
    }
    return;
  }
}

// Event bindings
el("upload-form").addEventListener("submit", handleUploadSubmit);
el("plot-btn").addEventListener("click", handlePlotClick);
el("chart-type").addEventListener("change", () => {
  toggleBarmodeVisibility();
  updateControlVisibility();
  // update selectors to reflect numeric-only constraints similar to original app
  const chartType = el("chart-type").value;
  setOptions(el("x-select"), allColumns);
  setOptions(el("y-select"), numericColumns);
  if (chartType === "Histogram") {
    setOptions(el("x-select"), numericColumns);
  }
  if (chartType === "Pie Chart") {
    setOptions(el("y-select"), numericColumns);
  }
});

el("logout-btn").addEventListener("click", () => {
  localStorage.removeItem("jwt_token");
  window.location.href = "/";
});


