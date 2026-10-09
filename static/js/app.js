// CleanCSV - Phase 2 Advanced In-Browser Grid & Profiling Logic

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const fileInfoBadge = document.getElementById("fileInfoBadge");
  const fileNameDisplay = document.getElementById("fileNameDisplay");
  const fileSizeDisplay = document.getElementById("fileSizeDisplay");
  const removeFileBtn = document.getElementById("removeFileBtn");
  const trySampleBtn = document.getElementById("trySampleBtn");

  const columnMappingSection = document.getElementById("columnMappingSection");
  const mappingGrid = document.getElementById("mappingGrid");

  const cleanerForm = document.getElementById("cleanerForm");
  const cleanBtn = document.getElementById("cleanBtn");
  const btnText = document.getElementById("btnText");
  const spinnerIcon = document.getElementById("spinnerIcon");
  const sparkleIcon = document.getElementById("sparkleIcon");

  const resultsSection = document.getElementById("resultsSection");
  const metricOriginalRows = document.getElementById("metricOriginalRows");
  const metricDuplicates = document.getElementById("metricDuplicates");
  const metricImputed = document.getElementById("metricImputed");
  const metricNormalized = document.getElementById("metricNormalized");
  const metricFinalRows = document.getElementById("metricFinalRows");
  const healthBadge = document.getElementById("healthBadge");

  const tabCleaned = document.getElementById("tabCleaned");
  const tabOriginal = document.getElementById("tabOriginal");
  const tableHead = document.getElementById("tableHead");
  const tableBody = document.getElementById("tableBody");
  const previewRowInfo = document.getElementById("previewRowInfo");
  const filterErrorsBtn = document.getElementById("filterErrorsBtn");
  const errorCountBadge = document.getElementById("errorCountBadge");
  const resetEditsBtn = document.getElementById("resetEditsBtn");

  // Export Buttons
  const downloadCsvBtn = document.getElementById("downloadCsvBtn");
  const downloadExcelBtn = document.getElementById("downloadExcelBtn");
  const downloadJsonBtn = document.getElementById("downloadJsonBtn");
  const copyClipboardBtn = document.getElementById("copyClipboardBtn");
  const copyText = document.getElementById("copyText");
  const startOverBtn = document.getElementById("startOverBtn");
  const downloadSubtext = document.getElementById("downloadSubtext");

  // Audit Modal Elements
  const openAuditBtn = document.getElementById("openAuditBtn");
  const auditModal = document.getElementById("auditModal");
  const closeAuditModalBtn = document.getElementById("closeAuditModalBtn");
  const closeAuditModalBtn2 = document.getElementById("closeAuditModalBtn2");
  const modalHealthScore = document.getElementById("modalHealthScore");
  const modalMemoryReduction = document.getElementById("modalMemoryReduction");
  const modalMemoryDetails = document.getElementById("modalMemoryDetails");
  const modalDimensions = document.getElementById("modalDimensions");
  const modalColumnsTable = document.getElementById("modalColumnsTable");

  // State
  let currentFile = null;
  let sampleCsvData = null;
  let inspectedColumns = [];
  let lastResultData = null;
  let originalCleanedBackup = null;
  let activeTab = "cleaned";
  let filterOnlyErrors = false;

  function formatBytes(bytes) {
    if (!bytes || bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  }

  // Set file and trigger inspection
  async function setFile(file) {
    currentFile = file;
    sampleCsvData = null;
    if (file) {
      fileNameDisplay.textContent = file.name;
      fileSizeDisplay.textContent = formatBytes(file.size);
      fileInfoBadge.classList.remove("hidden");
      await inspectCurrentFile();
    } else {
      fileInfoBadge.classList.add("hidden");
      fileInput.value = "";
      columnMappingSection.classList.add("hidden");
      mappingGrid.innerHTML = "";
      inspectedColumns = [];
    }
  }

  // Inspect file to populate Column Mapping
  async function inspectCurrentFile() {
    const formData = new FormData();
    if (currentFile) {
      formData.append("file", currentFile);
    } else if (sampleCsvData) {
      formData.append("raw_csv", sampleCsvData);
      formData.append("filename", "dirty_data.csv");
    } else {
      return;
    }

    try {
      const res = await fetch("/api/inspect", { method: "POST", body: formData });
      const data = await res.json();
      if (data.success && data.columns && data.columns.length > 0) {
        inspectedColumns = data.columns;
        renderColumnMapping(data.columns);
      }
    } catch (err) {
      console.error("Inspection error:", err);
    }
  }

  function renderColumnMapping(columns) {
    mappingGrid.innerHTML = columns.map((col) => {
      return `
        <div class="bg-white border border-slate-200 rounded-xl p-3 shadow-xs flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <span class="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 truncate max-w-[140px]" title="${escapeHtml(col)}">
              ${escapeHtml(col)}
            </span>
            <label class="inline-flex items-center gap-1.5 cursor-pointer text-xs text-slate-500 hover:text-slate-700">
              <input type="checkbox" data-col="${escapeHtml(col)}" class="col-keep-toggle w-3.5 h-3.5 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500" checked>
              <span>Keep</span>
            </label>
          </div>
          <div>
            <input type="text" data-orig="${escapeHtml(col)}" placeholder="Rename (optional)..."
              class="col-rename-input w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-xs text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500">
          </div>
        </div>
      `;
    }).join("");

    columnMappingSection.classList.remove("hidden");
  }

  // Drag & Drop
  ["dragenter", "dragover"].forEach((eventName) => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.add("drag-over");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.remove("drag-over");
    });
  });

  let batchFiles = null;

  dropZone.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 1) {
      batchFiles = Array.from(files);
      currentFile = null;
      fileNameDisplay.textContent = `Batch Mode (${batchFiles.length} files)`;
      fileSizeDisplay.textContent = "Multi-file";
      fileInfoBadge.classList.remove("hidden");
      btnText.textContent = `Clean Batch (${batchFiles.length} Files) & Download ZIP`;
    } else if (files.length === 1) {
      batchFiles = null;
      const ext = files[0].name.toLowerCase();
      if (ext.endsWith(".csv") || ext.endsWith(".xlsx") || ext.endsWith(".xls")) {
        setFile(files[0]);
      } else {
        alert("Please upload a valid CSV or Excel (.xlsx, .xls) file.");
      }
    }
  });

  dropZone.addEventListener("click", (e) => {
    if (e.target.closest("#removeFileBtn") || e.target.closest("#fileInfoBadge")) return;
    fileInput.click();
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 1) {
      batchFiles = Array.from(e.target.files);
      currentFile = null;
      fileNameDisplay.textContent = `Batch Mode (${batchFiles.length} files)`;
      fileSizeDisplay.textContent = "Multi-file";
      fileInfoBadge.classList.remove("hidden");
      btnText.textContent = `Clean Batch (${batchFiles.length} Files) & Download ZIP`;
    } else if (e.target.files.length === 1) {
      batchFiles = null;
      setFile(e.target.files[0]);
    }
  });

  removeFileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    batchFiles = null;
    setFile(null);
    btnText.textContent = "Clean Dataset Now";
  });

  // Try Sample Data
  trySampleBtn.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/sample");
      const data = await res.json();
      if (data.success) {
        batchFiles = null;
        currentFile = null;
        sampleCsvData = data.csv;
        fileNameDisplay.textContent = "dirty_data.csv (Sample)";
        fileSizeDisplay.textContent = `${data.csv.length} bytes`;
        fileInfoBadge.classList.remove("hidden");
        btnText.textContent = "Clean Dataset Now";
        await inspectCurrentFile();
      }
    } catch (err) {
      console.error("Failed to load sample:", err);
    }
  });

  // Submit Cleaning
  cleanerForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    // Check if batch processing mode
    if (batchFiles && batchFiles.length > 1) {
      cleanBtn.disabled = true;
      spinnerIcon.classList.remove("hidden");
      sparkleIcon.classList.add("hidden");
      btnText.textContent = `Processing ${batchFiles.length} files...`;

      const batchFormData = new FormData();
      batchFiles.forEach(f => batchFormData.append("files", f));

      try {
        const response = await fetch("/api/clean-batch", { method: "POST", body: batchFormData });
        if (!response.ok) throw new Error("Batch cleaning failed.");
        const blob = await response.blob();
        triggerDownload(blob, "cleancsv_batch_results.zip");
        alert(`Successfully cleaned ${batchFiles.length} files! Your ZIP archive has downloaded.`);
      } catch (err) {
        alert("Batch error: " + err.message);
      } finally {
        cleanBtn.disabled = false;
        spinnerIcon.classList.add("hidden");
        sparkleIcon.classList.remove("hidden");
        btnText.textContent = `Clean Batch (${batchFiles.length} Files) & Download ZIP`;
      }
      return;
    }

    if (!currentFile && !sampleCsvData) {
      alert("Please choose or drag-and-drop a CSV/Excel file first!");
      fileInput.click();
      return;
    }

    cleanBtn.disabled = true;
    spinnerIcon.classList.remove("hidden");
    sparkleIcon.classList.add("hidden");
    btnText.textContent = "Cleaning & Validating...";

    const formData = new FormData();
    if (currentFile) {
      formData.append("file", currentFile);
    } else if (sampleCsvData) {
      formData.append("raw_csv", sampleCsvData);
      formData.append("filename", "dirty_data.csv");
    }

    const columnMapping = {};
    const dropColumns = [];

    document.querySelectorAll(".col-rename-input").forEach((input) => {
      const orig = input.getAttribute("data-orig");
      const renameVal = input.value.trim();
      if (renameVal && renameVal !== orig) {
        columnMapping[orig] = renameVal;
      }
    });

    document.querySelectorAll(".col-keep-toggle").forEach((toggle) => {
      const col = toggle.getAttribute("data-col");
      if (!toggle.checked) {
        dropColumns.push(col);
      }
    });

    formData.append("column_mapping", JSON.stringify(columnMapping));
    formData.append("drop_columns", JSON.stringify(dropColumns));
    formData.append("numeric_strategy", document.getElementById("numericStrategy").value);
    formData.append("string_strategy", document.getElementById("stringStrategy").value);
    formData.append("standardize_dates", document.getElementById("standardizeDates").checked);
    formData.append("drop_duplicates", document.getElementById("dropDuplicates").checked);
    formData.append("trim_strings", document.getElementById("trimStrings").checked);
    formData.append("handle_outliers", document.getElementById("handleOutliers").checked);
    formData.append("fuzzy_clustering", document.getElementById("fuzzyClustering")?.checked || false);
    formData.append("split_names", document.getElementById("splitNames")?.checked || false);

    try {
      const response = await fetch("/api/clean", { method: "POST", body: formData });
      const result = await response.json();
      if (!result.success) throw new Error(result.error || "Cleaning failed");

      lastResultData = result;
      originalCleanedBackup = JSON.parse(JSON.stringify(result.cleaned.rows));
      renderResults(result);
    } catch (error) {
      alert("Error: " + error.message);
    } finally {
      cleanBtn.disabled = false;
      spinnerIcon.classList.add("hidden");
      sparkleIcon.classList.remove("hidden");
      btnText.textContent = "Clean Dataset Now";
    }
  });

  // Render Table & Metrics
  function renderResults(data) {
    metricOriginalRows.textContent = data.original.total_rows;
    metricDuplicates.textContent = data.report.duplicates_removed;

    let totalImputed = 0;
    for (const key in data.report.imputed_columns) {
      totalImputed += data.report.imputed_columns[key].missing_count;
    }
    metricImputed.textContent = totalImputed;

    const datesCount = (data.report.standardized_dates || []).length;
    let outlierCount = 0;
    for (const key in data.report.outliers_handled || {}) {
      outlierCount += data.report.outliers_handled[key];
    }
    metricNormalized.textContent = datesCount + outlierCount;

    metricFinalRows.textContent = data.cleaned.total_rows;

    // Health Score
    const score = data.profiling?.health_score || 95;
    healthBadge.textContent = `${score}% Health Score`;
    if (score >= 90) {
      healthBadge.className = "px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
    } else {
      healthBadge.className = "px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30";
    }

    // Validation count
    const totalErrors = data.validation?.total_errors || 0;
    errorCountBadge.textContent = totalErrors;

    downloadSubtext.textContent = `Clean file: ${data.cleaned.total_rows} rows, ${data.cleaned.total_cols} columns ready to export.`;

    activeTab = "cleaned";
    filterOnlyErrors = false;
    updateTabsUI();
    renderTable();

    resultsSection.classList.remove("hidden");
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function updateTabsUI() {
    if (activeTab === "cleaned") {
      tabCleaned.className = "tab-btn active px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-semibold bg-white text-indigo-700 shadow-sm border border-slate-200/80 transition";
      tabOriginal.className = "tab-btn px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-medium text-slate-600 hover:text-slate-900 transition";
    } else {
      tabOriginal.className = "tab-btn active px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-semibold bg-white text-indigo-700 shadow-sm border border-slate-200/80 transition";
      tabCleaned.className = "tab-btn px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-medium text-slate-600 hover:text-slate-900 transition";
    }
  }

  // Render Table with in-browser editable cells & validation badges
  function renderTable() {
    if (!lastResultData) return;
    const target = activeTab === "cleaned" ? lastResultData.cleaned : lastResultData.original;
    const cellErrors = (activeTab === "cleaned" && lastResultData.validation?.cell_errors) || {};

    let displayRows = target.rows;
    if (activeTab === "cleaned" && filterOnlyErrors) {
      displayRows = target.rows.filter((_, rIdx) => {
        return target.columns.some((col) => cellErrors[`${rIdx}_${col}`]);
      });
    }

    previewRowInfo.textContent = `Showing ${displayRows.length} of ${target.total_rows} rows`;

    tableHead.innerHTML = `
      <tr>
        <th class="py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider w-12 text-center">#</th>
        ${target.columns.map((col) => `<th class="py-3 px-4 font-semibold text-slate-700 border-l border-slate-200/60">${escapeHtml(col)}</th>`).join("")}
      </tr>
    `;

    if (displayRows.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="${target.columns.length + 1}" class="text-center py-8 text-slate-400">No rows found matching current filter.</td></tr>`;
      return;
    }

    tableBody.innerHTML = displayRows.map((row, idx) => {
      const originalRowIdx = target.rows.indexOf(row);
      return `
        <tr class="transition hover:bg-slate-50/80">
          <td class="py-2.5 px-4 text-xs text-slate-400 text-center font-mono select-none">${originalRowIdx + 1}</td>
          ${target.columns.map((col) => {
            const val = row[col];
            const isMissing = val === null || val === undefined || val === "";
            const errKey = `${originalRowIdx}_${col}`;
            const errorMsg = cellErrors[errKey];

            if (isMissing) {
              return `<td class="py-2.5 px-4 border-l border-slate-100 font-mono text-xs"><span class="cell-missing">NaN</span></td>`;
            }

            const isEditable = activeTab === "cleaned";
            const errorClass = errorMsg ? "cell-error" : "";
            const tooltipAttr = errorMsg ? `title="⚠️ ${escapeHtml(errorMsg)}"` : "";

            return `
              <td class="py-2.5 px-4 border-l border-slate-100 text-slate-800 ${isEditable ? 'cell-editable' : ''} ${errorClass}"
                ${isEditable ? 'contenteditable="true"' : ''}
                data-row="${originalRowIdx}"
                data-col="${escapeHtml(col)}"
                ${tooltipAttr}>
                ${escapeHtml(String(val))}
              </td>
            `;
          }).join("")}
        </tr>
      `;
    }).join("");

    // Attach Cell Edit Event Listeners
    if (activeTab === "cleaned") {
      document.querySelectorAll(".cell-editable").forEach((cell) => {
        cell.addEventListener("blur", handleCellEdit);
        cell.addEventListener("keydown", (e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            cell.blur();
          }
        });
      });
    }
  }

  // Handle cell edit by user
  function handleCellEdit(e) {
    const cell = e.target;
    const rowIdx = parseInt(cell.getAttribute("data-row"), 10);
    const colName = cell.getAttribute("data-col");
    const newVal = cell.innerText.trim();

    if (isNaN(rowIdx) || !colName || !lastResultData) return;

    // Update state
    lastResultData.cleaned.rows[rowIdx][colName] = newVal;
    cell.classList.add("cell-edited");

    // Clear error if resolved
    const errKey = `${rowIdx}_${colName}`;
    if (lastResultData.validation?.cell_errors && lastResultData.validation.cell_errors[errKey]) {
      delete lastResultData.validation.cell_errors[errKey];
      cell.classList.remove("cell-error");
      cell.removeAttribute("title");
      const remaining = Object.keys(lastResultData.validation.cell_errors).length;
      errorCountBadge.textContent = remaining;
    }

    resetEditsBtn.classList.remove("hidden");
    recomputeExportPayloads();
  }

  // Rebuild CSV & JSON in-memory payloads after edits
  function recomputeExportPayloads() {
    if (!lastResultData) return;
    const cols = lastResultData.cleaned.columns;
    const rows = lastResultData.cleaned.rows;

    // Build CSV
    const csvLines = [cols.join(",")];
    for (const r of rows) {
      const line = cols.map((c) => {
        const v = r[c] ?? "";
        return String(v).includes(",") ? `"${String(v).replace(/"/g, '""')}"` : String(v);
      });
      csvLines.push(line.join(","));
    }
    lastResultData.csv_content = csvLines.join("\n");
    lastResultData.json_content = JSON.stringify(rows, null, 2);
  }

  // Reset Edits
  resetEditsBtn.addEventListener("click", () => {
    if (!originalCleanedBackup || !lastResultData) return;
    lastResultData.cleaned.rows = JSON.parse(JSON.stringify(originalCleanedBackup));
    resetEditsBtn.classList.add("hidden");
    recomputeExportPayloads();
    renderTable();
  });

  // Filter Issues Only toggle
  filterErrorsBtn.addEventListener("click", () => {
    if (activeTab !== "cleaned") return;
    filterOnlyErrors = !filterOnlyErrors;
    if (filterOnlyErrors) {
      filterErrorsBtn.className = "px-2.5 py-1 rounded-md border border-amber-300 bg-amber-50 text-amber-800 font-semibold transition flex items-center gap-1";
    } else {
      filterErrorsBtn.className = "px-2.5 py-1 rounded-md border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-medium transition flex items-center gap-1";
    }
    renderTable();
  });

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.innerText = text;
    return div.innerHTML;
  }

  tabCleaned.addEventListener("click", () => {
    activeTab = "cleaned";
    updateTabsUI();
    renderTable();
  });

  tabOriginal.addEventListener("click", () => {
    activeTab = "original";
    filterOnlyErrors = false;
    updateTabsUI();
    renderTable();
  });

  // Download CSV
  downloadCsvBtn.addEventListener("click", () => {
    if (!lastResultData || !lastResultData.csv_content) return;
    const blob = new Blob([lastResultData.csv_content], { type: "text/csv;charset=utf-8;" });
    triggerDownload(blob, lastResultData.download_csv_filename || "cleaned_data.csv");
  });

  // Download Excel (.xlsx)
  downloadExcelBtn.addEventListener("click", () => {
    if (!lastResultData || !lastResultData.excel_b64) return;
    const byteCharacters = atob(lastResultData.excel_b64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
    triggerDownload(blob, lastResultData.download_excel_filename || "cleaned_data.xlsx");
  });

  // Export JSON
  downloadJsonBtn.addEventListener("click", () => {
    if (!lastResultData || !lastResultData.json_content) return;
    const blob = new Blob([lastResultData.json_content], { type: "application/json;charset=utf-8;" });
    triggerDownload(blob, lastResultData.download_json_filename || "cleaned_data.json");
  });

  // Copy CSV to Clipboard
  copyClipboardBtn.addEventListener("click", async () => {
    if (!lastResultData || !lastResultData.csv_content) return;
    try {
      await navigator.clipboard.writeText(lastResultData.csv_content);
      copyText.textContent = "Copied!";
      copyClipboardBtn.classList.add("text-emerald-400", "border-emerald-600");
      setTimeout(() => {
        copyText.textContent = "Copy CSV";
        copyClipboardBtn.classList.remove("text-emerald-400", "border-emerald-600");
      }, 2000);
    } catch (err) {
      alert("Failed to copy to clipboard.");
    }
  });

  function triggerDownload(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  // Audit Report Modal Logic
  openAuditBtn.addEventListener("click", () => {
    if (!lastResultData || !lastResultData.profiling) return;
    const p = lastResultData.profiling;

    modalHealthScore.textContent = `${p.health_score}%`;
    modalMemoryReduction.textContent = `${p.memory_reduction_pct}%`;
    modalMemoryDetails.textContent = `${formatBytes(p.memory_before_bytes - p.memory_after_bytes)} saved`;
    modalDimensions.textContent = `${p.final_rows} × ${p.final_cols}`;

    modalColumnsTable.innerHTML = p.columns_profile.map((col) => {
      const minMax = (col.min !== null && col.max !== null) ? `${col.min} to ${col.max}` : "—";
      return `
        <tr class="hover:bg-slate-50">
          <td class="py-2 px-3 font-semibold text-slate-800 font-mono">${escapeHtml(col.name)}</td>
          <td class="py-2 px-3 text-slate-600"><span class="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[11px]">${escapeHtml(col.type)}</span></td>
          <td class="py-2 px-3 text-slate-600">${col.missing_pct}% (${col.missing_count})</td>
          <td class="py-2 px-3 text-slate-600">${col.unique_count}</td>
          <td class="py-2 px-3 text-slate-600 font-mono text-[11px]">${minMax}</td>
        </tr>
      `;
    }).join("");

    auditModal.classList.remove("hidden");
  });

  function closeAuditModal() {
    auditModal.classList.add("hidden");
  }

  closeAuditModalBtn.addEventListener("click", closeAuditModal);
  closeAuditModalBtn2.addEventListener("click", closeAuditModal);
  auditModal.addEventListener("click", (e) => {
    if (e.target === auditModal) closeAuditModal();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !auditModal.classList.contains("hidden")) {
      closeAuditModal();
    }
  });

  startOverBtn.addEventListener("click", () => {
    setFile(null);
    resultsSection.classList.add("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
});
