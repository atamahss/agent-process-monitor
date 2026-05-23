const AUTO_REFRESH_MS = 10000;
const I18N = {
  ru: {
    loading: '\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430...',
    database: '\u0411\u0430\u0437\u0430',
    refresh: '\u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c',
    summaryRunning: '\u0441\u0435\u0439\u0447\u0430\u0441',
    summaryDone: '\u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u043e',
    summaryStopped: '\u043e\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u043e \u0430\u0433\u0435\u043d\u0442\u043e\u043c',
    summaryFailed: '\u0441 \u043e\u0448\u0438\u0431\u043a\u043e\u0439',
    tabRunning: '\u0421\u0435\u0439\u0447\u0430\u0441',
    tabHistory: '\u0418\u0441\u0442\u043e\u0440\u0438\u044f',
    searchPlaceholder: '\u041f\u043e\u0438\u0441\u043a \u043f\u043e \u0446\u0435\u043b\u0438, \u043a\u043e\u043c\u0430\u043d\u0434\u0435, PID \u0438\u043b\u0438 \u043f\u0430\u043f\u043a\u0435',
    allStatuses: '\u0412\u0441\u0435 \u0441\u0442\u0430\u0442\u0443\u0441\u044b',
    empty: '\u0417\u0430\u043f\u0438\u0441\u0435\u0439 \u043f\u043e\u043a\u0430 \u043d\u0435\u0442.',
    details: '\u0414\u0435\u0442\u0430\u043b\u0438',
    detailsButton: '\u0414\u0435\u0442\u0430\u043b\u0438',
    stopButton: '\u0421\u0442\u043e\u043f',
    command: '\u041a\u043e\u043c\u0430\u043d\u0434\u0430',
    folder: '\u041f\u0430\u043f\u043a\u0430',
    start: '\u0421\u0442\u0430\u0440\u0442',
    finish: '\u0424\u0438\u043d\u0438\u0448',
    stopConfirm: '\u041e\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u044c \u043f\u0440\u043e\u0446\u0435\u0441\u0441 \u0434\u043b\u044f \u0446\u0435\u043b\u0438',
    sec: '\u0441\u0435\u043a',
    min: '\u043c\u0438\u043d',
    hour: '\u0447',
    statuses: {
      running: '\u0432 \u0440\u0430\u0431\u043e\u0442\u0435',
      completed: '\u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u043e',
      failed: '\u043e\u0448\u0438\u0431\u043a\u0430',
      recorded: '\u0437\u0430\u043f\u0438\u0441\u0430\u043d\u043e',
      stopped_by_agent: '\u043e\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u043e \u0430\u0433\u0435\u043d\u0442\u043e\u043c',
      ended_external: '\u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u043e \u0438\u0437\u0432\u043d\u0435',
      ended_unknown: '\u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u043e, \u043f\u0440\u0438\u0447\u0438\u043d\u0430 \u043d\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043d\u0430',
    },
  },
  en: {
    loading: 'Loading...',
    database: 'Database',
    refresh: 'Refresh',
    summaryRunning: 'running now',
    summaryDone: 'completed',
    summaryStopped: 'stopped by agent',
    summaryFailed: 'failed',
    tabRunning: 'Running',
    tabHistory: 'History',
    searchPlaceholder: 'Search by goal, command, PID, or folder',
    allStatuses: 'All statuses',
    empty: 'No records yet.',
    details: 'Details',
    detailsButton: 'Details',
    stopButton: 'Stop',
    command: 'Command',
    folder: 'Folder',
    start: 'Started',
    finish: 'Finished',
    stopConfirm: 'Stop process for goal',
    sec: 'sec',
    min: 'min',
    hour: 'h',
    statuses: {
      running: 'running',
      completed: 'completed',
      failed: 'failed',
      recorded: 'recorded',
      stopped_by_agent: 'stopped by agent',
      ended_external: 'ended externally',
      ended_unknown: 'ended, reason unknown',
    },
  },
};

const state = {
  view: 'running',
  runs: [],
  database: '',
  lang: localStorage.getItem('agentProcessMonitorLang') || 'ru',
};

const el = {
  runs: document.querySelector('#runs'),
  empty: document.querySelector('#empty'),
  refresh: document.querySelector('#refreshBtn'),
  search: document.querySelector('#search'),
  status: document.querySelector('#statusFilter'),
  dbPath: document.querySelector('#dbPath'),
  runningCount: document.querySelector('#runningCount'),
  doneCount: document.querySelector('#doneCount'),
  stoppedCount: document.querySelector('#stoppedCount'),
  failedCount: document.querySelector('#failedCount'),
  dialog: document.querySelector('#detailsDialog'),
  closeDialog: document.querySelector('#closeDialog'),
  detailTitle: document.querySelector('#detailTitle'),
  detailMeta: document.querySelector('#detailMeta'),
  detailFields: document.querySelector('#detailFields'),
  stdoutLog: document.querySelector('#stdoutLog'),
  stderrLog: document.querySelector('#stderrLog'),
  langRu: document.querySelector('#langRu'),
  langEn: document.querySelector('#langEn'),
};

function t(key) {
  return I18N[state.lang][key];
}

function statusLabel(status) {
  return I18N[state.lang].statuses[status] || status;
}

function applyLanguage() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll('[data-i18n]').forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  document.querySelectorAll('[data-status-option]').forEach((node) => {
    node.textContent = statusLabel(node.dataset.statusOption);
  });
  el.search.placeholder = t('searchPlaceholder');
  el.refresh.title = t('refresh');
  el.refresh.textContent = t('refresh');
  el.langRu.classList.toggle('active', state.lang === 'ru');
  el.langEn.classList.toggle('active', state.lang === 'en');
  el.dbPath.textContent = state.database ? `${t('database')}: ${state.database}` : t('loading');
  if (!el.dialog.open) {
    el.detailTitle.textContent = t('details');
  }
}

function setLanguage(lang) {
  state.lang = lang;
  localStorage.setItem('agentProcessMonitorLang', lang);
  applyLanguage();
  render();
}

function fmtDate(value) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('ru-RU');
}

function duration(run) {
  if (!run.started_at) return '-';
  const start = new Date(run.started_at).getTime();
  const end = run.ended_at ? new Date(run.ended_at).getTime() : Date.now();
  if (Number.isNaN(start) || Number.isNaN(end)) return '-';
  const seconds = Math.max(0, Math.floor((end - start) / 1000));
  if (seconds < 60) return `${seconds} ${t('sec')}`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} ${t('min')} ${seconds % 60} ${t('sec')}`;
  const hours = Math.floor(minutes / 60);
  return `${hours} ${t('hour')} ${minutes % 60} ${t('min')}`;
}

function matches(run) {
  const query = el.search.value.trim().toLowerCase();
  if (el.status.value && run.status !== el.status.value) return false;
  if (!query) return true;
  return [run.goal, run.command_display, run.cwd, run.pid, run.id, run.status]
    .filter(Boolean)
    .some((value) => String(value).toLowerCase().includes(query));
}

function renderCounts(allRuns) {
  el.runningCount.textContent = allRuns.filter((run) => run.status === 'running').length;
  el.doneCount.textContent = allRuns.filter((run) => ['completed', 'recorded'].includes(run.status)).length;
  el.stoppedCount.textContent = allRuns.filter((run) => run.status === 'stopped_by_agent').length;
  el.failedCount.textContent = allRuns.filter((run) => ['failed', 'ended_external', 'ended_unknown'].includes(run.status)).length;
}

function render() {
  const rows = state.runs.filter(matches);
  el.runs.innerHTML = '';
  el.empty.hidden = rows.length > 0;

  for (const run of rows) {
    const item = document.createElement('article');
    item.className = 'run';
    item.innerHTML = `
      <div>
        <div class="goal"></div>
        <div class="meta"></div>
        <div class="cmd"></div>
        <div class="cwd"></div>
      </div>
      <div class="rowActions">
        <span class="badge ${run.status}"></span>
        <button type="button" data-action="details"></button>
        ${run.status === 'running' ? '<button class="danger" type="button" data-action="stop"></button>' : ''}
      </div>
    `;
    item.querySelector('.goal').textContent = run.goal;
    item.querySelector('.meta').textContent = `PID ${run.pid || '-'} - ${fmtDate(run.started_at)} - ${duration(run)} - exit ${run.exit_code ?? '-'}`;
    item.querySelector('.cmd').textContent = run.command_display;
    item.querySelector('.cwd').textContent = run.cwd;
    item.querySelector('.badge').textContent = statusLabel(run.status);
    item.querySelector('[data-action="details"]').textContent = t('detailsButton');
    item.querySelector('[data-action="details"]').addEventListener('click', () => showDetails(run.id));

    const stopBtn = item.querySelector('[data-action="stop"]');
    if (stopBtn) {
      stopBtn.textContent = t('stopButton');
      stopBtn.addEventListener('click', () => stopRun(run));
    }
    el.runs.append(item);
  }
}

async function loadRuns() {
  const response = await fetch('/api/runs?limit=500');
  const data = await response.json();
  const allRuns = data.runs || [];

  state.runs = state.view === 'running'
    ? allRuns.filter((run) => run.status === 'running')
    : allRuns;
  state.database = data.database || '';
  el.dbPath.textContent = state.database ? `${t('database')}: ${state.database}` : '';

  renderCounts(allRuns);
  render();
}

async function showDetails(id) {
  const response = await fetch(`/api/runs/${id}/logs`);
  const data = await response.json();
  const run = data.run;

  el.detailTitle.textContent = run.goal;
  el.detailMeta.textContent = `${statusLabel(run.status)} - PID ${run.pid || '-'} - ${duration(run)}`;
  el.detailFields.innerHTML = '';

  const fields = [
    ['ID', run.id],
    [t('command'), run.command_display],
    [t('folder'), run.cwd],
    [t('start'), fmtDate(run.started_at)],
    [t('finish'), fmtDate(run.ended_at)],
    ['Exit code', run.exit_code ?? '-'],
    ['stdout', run.stdout_log || '-'],
    ['stderr', run.stderr_log || '-'],
  ];

  for (const [name, value] of fields) {
    const dt = document.createElement('dt');
    const dd = document.createElement('dd');
    dt.textContent = name;
    dd.textContent = value;
    el.detailFields.append(dt, dd);
  }

  el.stdoutLog.textContent = data.stdout || '';
  el.stderrLog.textContent = data.stderr || '';
  el.dialog.showModal();
}

async function stopRun(run) {
  const ok = confirm(`${t('stopConfirm')}: ${run.goal}?`);
  if (!ok) return;
  await fetch(`/api/runs/${run.id}/stop`, { method: 'POST' });
  await loadRuns();
}

document.querySelectorAll('.tab').forEach((tab) => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach((node) => node.classList.remove('active'));
    tab.classList.add('active');
    state.view = tab.dataset.view;
    el.status.value = state.view === 'running' ? 'running' : '';
    loadRuns();
  });
});

el.refresh.addEventListener('click', loadRuns);
el.langRu.addEventListener('click', () => setLanguage('ru'));
el.langEn.addEventListener('click', () => setLanguage('en'));
el.search.addEventListener('input', render);
el.status.addEventListener('change', render);
el.closeDialog.addEventListener('click', () => el.dialog.close());

el.status.value = 'running';
applyLanguage();
loadRuns();

setInterval(() => {
  if (!document.hidden && !el.dialog.open) {
    loadRuns();
  }
}, AUTO_REFRESH_MS);
