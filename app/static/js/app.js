/**
 * Frontend Application Controller for OrangeHRM RPA Dashboard
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const form = document.getElementById('automationForm');
  const btnSubmit = document.getElementById('btnSubmit');
  const btnSpinner = document.getElementById('btnSpinner');
  const btnText = document.getElementById('btnText');
  const btnGenId = document.getElementById('btnGenId');
  const employeeIdInput = document.getElementById('employeeId');

  const progressSection = document.getElementById('progressSection');
  const runBadge = document.getElementById('runBadge');
  const runIdDisplay = document.getElementById('runIdDisplay');
  const timerDisplay = document.getElementById('timerDisplay');

  const logConsole = document.getElementById('logConsole');
  const autoScroll = document.getElementById('autoScroll');
  const btnClearLogs = document.getElementById('btnClearLogs');

  const resultsSummarySection = document.getElementById('resultsSummarySection');
  const resEmpName = document.getElementById('resEmpName');
  const resEmpId = document.getElementById('resEmpId');
  const resVerifiedAt = document.getElementById('resVerifiedAt');
  const extractedCountBadge = document.getElementById('extractedCountBadge');
  const btnDownloadCsv = document.getElementById('btnDownloadCsv');
  const btnDownloadExcel = document.getElementById('btnDownloadExcel');

  const tableSection = document.getElementById('tableSection');
  const employeeTableBody = document.getElementById('employeeTableBody');
  const tableSearch = document.getElementById('tableSearch');

  const screenshotsSection = document.getElementById('screenshotsSection');
  const screenshotsGrid = document.getElementById('screenshotsGrid');
  const imageModal = document.getElementById('imageModal');
  const modalImg = document.getElementById('modalImg');
  const modalCaption = document.getElementById('modalCaption');
  const modalClose = document.getElementById('modalClose');

  let currentEventSource = null;
  let timerInterval = null;
  let startTime = 0;
  let allExtractedRecords = [];

  // Randomize Employee ID Helper
  btnGenId.addEventListener('click', () => {
    const randomNum = Math.floor(1000 + Math.random() * 9000);
    employeeIdInput.value = `EMP${randomNum}`;
  });

  // Clear Logs
  btnClearLogs.addEventListener('click', () => {
    logConsole.innerHTML = '<div class="text-slate-500">// Console logs cleared.</div>';
  });

  // Lightbox Modal Controls
  modalClose.addEventListener('click', () => {
    imageModal.classList.add('hidden');
    imageModal.classList.remove('flex');
  });
  imageModal.addEventListener('click', (e) => {
    if (e.target === imageModal) {
      imageModal.classList.add('hidden');
      imageModal.classList.remove('flex');
    }
  });

  // Step Node Mapping
  const stepMap = [
    { id: 'step-1', patterns: ['Open Portal', 'Step 1', 'Open Login Page', '01_login'] },
    { id: 'step-2', patterns: ['Authenticate', 'Step 2', 'Login', 'Enter Username', 'Enter Password', 'Submit Login'] },
    { id: 'step-3', patterns: ['Navigate PIM', 'Step 3', 'PIM Navigation', 'Dashboard confirmed'] },
    { id: 'step-4', patterns: ['Add Employee', 'Step 4', 'Open Add Form', 'Click Save Employee'] },
    { id: 'step-5', patterns: ['Verify', 'Step 5', 'Personal Details', 'Toast'] },
    { id: 'step-6', patterns: ['Extract', 'Step 6', 'Employee List', 'Export'] },
    { id: 'step-7', patterns: ['Logout', 'Step 7', 'Clean logout'] },
  ];

  function resetSteps() {
    for (let i = 1; i <= 7; i++) {
      const el = document.getElementById(`step-${i}`);
      if (el) {
        el.className = 'step-card bg-slate-950/80 border border-slate-800/80 rounded-xl p-3 transition-all';
        const icon = el.querySelector('.step-icon');
        if (icon) icon.textContent = '⏳';
      }
    }
  }

  function updateStepProgress(stepName) {
    if (!stepName) return;
    
    let activeIdx = -1;
    for (let i = 0; i < stepMap.length; i++) {
      if (stepMap[i].patterns.some(p => stepName.toLowerCase().includes(p.toLowerCase()))) {
        activeIdx = i;
        break;
      }
    }

    if (activeIdx !== -1) {
      for (let i = 0; i < stepMap.length; i++) {
        const el = document.getElementById(stepMap[i].id);
        if (!el) continue;
        const icon = el.querySelector('.step-icon');
        
        if (i < activeIdx) {
          el.className = 'step-card step-done rounded-xl p-3 transition-all';
          if (icon) icon.textContent = '✓';
        } else if (i === activeIdx) {
          el.className = 'step-card step-active rounded-xl p-3 transition-all';
          if (icon) icon.textContent = '⚡';
        } else {
          el.className = 'step-card bg-slate-950/80 border border-slate-800/80 rounded-xl p-3 transition-all';
          if (icon) icon.textContent = '⏳';
        }
      }
    }
  }

  function markAllStepsComplete() {
    for (let i = 1; i <= 7; i++) {
      const el = document.getElementById(`step-${i}`);
      if (el) {
        el.className = 'step-card step-done rounded-xl p-3 transition-all';
        const icon = el.querySelector('.step-icon');
        if (icon) icon.textContent = '✓';
      }
    }
  }

  function appendLog(entry) {
    const line = document.createElement('div');
    line.className = `log-line ${entry.level || 'INFO'}`;
    
    const timeSpan = `<span class="text-slate-600 mr-2">[${entry.timestamp || new Date().toLocaleTimeString()}]</span>`;
    const stepBadge = entry.step ? `<span class="log-step-badge">${escapeHtml(entry.step)}</span>` : '';
    const msg = `<span>${escapeHtml(entry.message)}</span>`;
    
    line.innerHTML = timeSpan + stepBadge + msg;
    logConsole.appendChild(line);

    if (autoScroll.checked) {
      logConsole.scrollTop = logConsole.scrollHeight;
    }

    if (entry.step) {
      updateStepProgress(entry.step);
    }
  }

  function escapeHtml(text) {
    if (!text) return '';
    return text.toString()
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Handle Form Submission
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Disable button & show spinner
    btnSubmit.disabled = true;
    btnSpinner.classList.remove('hidden');
    btnText.textContent = 'Running Automation...';

    // Reset UI sections
    resetSteps();
    resultsSummarySection.classList.add('hidden');
    tableSection.classList.add('hidden');
    screenshotsSection.classList.add('hidden');
    screenshotsGrid.innerHTML = '';
    progressSection.classList.remove('hidden');

    runBadge.textContent = 'RUNNING';
    runBadge.className = 'text-xs px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium animate-pulse';

    // Start Timer
    startTime = Date.now();
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      timerDisplay.textContent = `${elapsed}s`;
    }, 100);

    const payload = {
      url: document.getElementById('targetUrl').value.trim(),
      username: document.getElementById('username').value.trim(),
      password: document.getElementById('password').value.trim(),
      first_name: document.getElementById('firstName').value.trim(),
      middle_name: document.getElementById('middleName').value.trim(),
      last_name: document.getElementById('lastName').value.trim(),
      employee_id: document.getElementById('employeeId').value.trim() || undefined,
      headless: document.getElementById('headless').checked,
    };

    try {
      appendLog({ level: 'INFO', step: 'Init', message: 'Sending automation request to backend server...' });
      
      const response = await fetch('/api/run-automation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Failed to initiate run`);
      }

      const initData = await response.json();
      const runId = initData.run_id;
      runIdDisplay.textContent = runId;
      appendLog({ level: 'INFO', step: 'Connected', message: `Automation run accepted: ${runId}` });

      // Connect to SSE Log Stream
      if (currentEventSource) {
        currentEventSource.close();
      }

      currentEventSource = new EventSource(`/api/stream-logs/${runId}`);

      currentEventSource.onmessage = (event) => {
        try {
          const logData = JSON.parse(event.data);
          appendLog(logData);
        } catch (err) {
          console.error("Error parsing log line:", err);
        }
      };

      currentEventSource.addEventListener('complete', (event) => {
        try {
          const finalResult = JSON.parse(event.data);
          handleRunComplete(finalResult);
        } catch (err) {
          console.error("Error handling completion payload:", err);
        }
      });

      currentEventSource.onerror = (err) => {
        console.warn("SSE connection closed or errored:", err);
        // Fallback polling check in case SSE severed before final event
        setTimeout(() => checkRunStatusFallback(runId), 2000);
      };

    } catch (err) {
      appendLog({ level: 'ERROR', step: 'Error', message: err.message });
      handleRunFailure(err.message);
    }
  });

  async function checkRunStatusFallback(runId) {
    try {
      const resp = await fetch(`/api/status/${runId}`);
      if (resp.ok) {
        const data = await resp.json();
        if (data.status === 'SUCCESS' || data.status === 'FAILED') {
          handleRunComplete(data);
        }
      }
    } catch (e) {
      console.error("Fallback status check error:", e);
    }
  }

  function handleRunComplete(result) {
    if (currentEventSource) {
      currentEventSource.close();
      currentEventSource = null;
    }
    clearInterval(timerInterval);

    if (result.status === 'SUCCESS') {
      markAllStepsComplete();
      runBadge.textContent = 'COMPLETED';
      runBadge.className = 'text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium';

      // 1. Render Inserted Employee Card
      if (result.inserted_employee) {
        const emp = result.inserted_employee;
        const fullName = [emp.first_name, emp.middle_name, emp.last_name].filter(Boolean).join(' ');
        resEmpName.textContent = fullName;
        resEmpId.textContent = emp.employee_id || 'Auto-Assigned';
        resVerifiedAt.textContent = emp.verified_at || new Date().toLocaleString();
      }
      
      // 2. Set Download Links
      if (result.csv_filename) {
        btnDownloadCsv.href = `/api/download/csv/${encodeURIComponent(result.csv_filename)}`;
        btnDownloadCsv.classList.remove('pointer-events-none', 'opacity-50');
      }
      if (result.excel_filename) {
        btnDownloadExcel.href = `/api/download/excel/${encodeURIComponent(result.excel_filename)}`;
        btnDownloadExcel.classList.remove('pointer-events-none', 'opacity-50');
      }
      extractedCountBadge.textContent = `${result.extracted_count || 0} Records Extracted`;
      resultsSummarySection.classList.remove('hidden');

      // 3. Render Employee Table
      if (result.extracted_data && result.extracted_data.length > 0) {
        allExtractedRecords = result.extracted_data;
        renderTable(allExtractedRecords);
        tableSection.classList.remove('hidden');
      }

      // 4. Render Screenshot Proofs
      if (result.screenshots && result.screenshots.length > 0) {
        renderScreenshots(result.screenshots);
        screenshotsSection.classList.remove('hidden');
      }

      appendLog({
        level: 'INFO',
        step: 'Complete',
        message: `Execution finalized in ${result.duration_seconds}s. Inserted employee verified and ${result.extracted_count} records exported.`,
      });

    } else {
      handleRunFailure(result.error ? result.error.message : 'Automation execution failed.');
    }

    // Reset button
    btnSubmit.disabled = false;
    btnSpinner.classList.add('hidden');
    btnText.textContent = 'Trigger Automation';
  }

  function handleRunFailure(errMsg) {
    if (currentEventSource) {
      currentEventSource.close();
      currentEventSource = null;
    }
    clearInterval(timerInterval);

    runBadge.textContent = 'FAILED';
    runBadge.className = 'text-xs px-2.5 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 font-medium';
    
    appendLog({ level: 'ERROR', step: 'Execution Failed', message: errMsg });

    btnSubmit.disabled = false;
    btnSpinner.classList.add('hidden');
    btnText.textContent = 'Trigger Automation';
  }

  function renderTable(records) {
    employeeTableBody.innerHTML = '';
    if (records.length === 0) {
      employeeTableBody.innerHTML = '<tr><td colspan="7" class="px-4 py-6 text-center text-slate-500">No matching records found.</td></tr>';
      return;
    }

    records.forEach(rec => {
      const tr = document.createElement('tr');
      tr.className = 'hover:bg-slate-800/40 transition';
      tr.innerHTML = `
        <td class="px-4 py-2.5 font-bold text-brand-400">${escapeHtml(rec.employee_id || '-')}</td>
        <td class="px-4 py-2.5 text-white font-sans">${escapeHtml(rec.first_name || '-')}</td>
        <td class="px-4 py-2.5 text-slate-200 font-sans">${escapeHtml(rec.last_name || '-')}</td>
        <td class="px-4 py-2.5 text-slate-400 font-sans">${escapeHtml(rec.job_title || '-')}</td>
        <td class="px-4 py-2.5 text-slate-400 font-sans">${escapeHtml(rec.employment_status || '-')}</td>
        <td class="px-4 py-2.5 text-slate-400 font-sans">${escapeHtml(rec.sub_unit || '-')}</td>
        <td class="px-4 py-2.5 text-slate-400 font-sans">${escapeHtml(rec.supervisor || '-')}</td>
      `;
      employeeTableBody.appendChild(tr);
    });
  }

  // Live Table Search Filter
  tableSearch.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase().trim();
    if (!q) {
      renderTable(allExtractedRecords);
      return;
    }
    const filtered = allExtractedRecords.filter(r => {
      return Object.values(r).some(val => val && val.toLowerCase().includes(q));
    });
    renderTable(filtered);
  });

  // Render Screenshot Thumbnails
  function renderScreenshots(filenames) {
    screenshotsGrid.innerHTML = '';
    filenames.forEach(fname => {
      const div = document.createElement('div');
      div.className = 'screenshot-card bg-slate-950 border border-slate-800 rounded-xl overflow-hidden cursor-pointer group';
      
      const caption = fname.split('_').slice(2).join(' ').replace('.png', '');
      
      div.innerHTML = `
        <div class="h-32 bg-slate-900 overflow-hidden relative">
          <img src="/screenshots/${encodeURIComponent(fname)}" alt="${escapeHtml(fname)}" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
          <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
            <span class="text-xs text-white bg-slate-900/90 px-2 py-1 rounded border border-slate-700">Zoom</span>
          </div>
        </div>
        <div class="p-2.5 border-t border-slate-800">
          <p class="text-[11px] font-mono text-slate-300 truncate">${escapeHtml(caption || fname)}</p>
        </div>
      `;

      div.addEventListener('click', () => {
        modalImg.src = `/screenshots/${encodeURIComponent(fname)}`;
        modalCaption.textContent = fname;
        imageModal.classList.remove('hidden');
        imageModal.classList.add('flex');
      });

      screenshotsGrid.appendChild(div);
    });
  }
});
