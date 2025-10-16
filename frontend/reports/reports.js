const state = {
  chart: null,
  report: null,
};

function $(selector) {
  return document.querySelector(selector);
}

function notify(message, isError = false) {
  const notification = $('#notification');
  notification.textContent = message;
  notification.classList.toggle('show', true);
  notification.style.background = isError ? '#dc2626' : '#2563eb';
  setTimeout(() => notification.classList.remove('show'), 3000);
}

async function fetchReport(formId, role) {
  const response = await fetch(`/reports/forms/${formId}`, {
    headers: {
      'X-Role': role,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || 'Unable to load report');
  }
  return response.json();
}

function updateSummary(summary) {
  $('#totalResponses').textContent = summary.total_responses;
  $('#completedResponses').textContent = summary.completed_responses;
  $('#completionRate').textContent = `${(summary.completion_rate * 100).toFixed(1)}%`;

  const chartData = {
    labels: ['Completed', 'Incomplete'],
    datasets: [
      {
        label: 'Responses',
        data: [summary.completed_responses, summary.total_responses - summary.completed_responses],
        backgroundColor: ['#22c55e', '#f97316'],
      },
    ],
  };

  const ctx = document.getElementById('completionChart');
  if (state.chart) {
    state.chart.destroy();
  }
  state.chart = new Chart(ctx, {
    type: 'doughnut',
    data: chartData,
    options: {
      plugins: {
        legend: { position: 'bottom' },
      },
    },
  });
}

function renderFields(fields) {
  const tbody = document.querySelector('#fieldsTable tbody');
  tbody.innerHTML = '';
  const template = document.getElementById('fieldRowTemplate');
  fields.forEach((field) => {
    const row = template.content.cloneNode(true);
    row.querySelector('.field-name').textContent = field.name;
    row.querySelector('.field-type').textContent = field.type;
    row.querySelector('.field-answered').textContent = field.answered_count;
    row.querySelector('.field-rate').textContent = `${(field.response_rate * 100).toFixed(1)}%`;
    row.querySelector('.field-details').textContent = Object.entries(field.statistics)
      .map(([key, value]) => `${key}: ${value}`)
      .join(' | ');
    tbody.appendChild(row);
  });
}

async function exportReport(format) {
  if (!state.report) return;
  const role = $('#role').value;
  const formId = state.report.form_id;
  const response = await fetch(`/reports/forms/${formId}/export?format=${format}`, {
    headers: {
      'X-Role': role,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || 'Unable to export report');
  }
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `form-${formId}-report.${format}`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

function bindEvents() {
  $('#loadReport').addEventListener('click', async () => {
    const formId = $('#formId').value;
    const role = $('#role').value;
    if (!formId) {
      notify('Please provide a form ID', true);
      return;
    }
    try {
      const data = await fetchReport(formId, role);
      state.report = data;
      updateSummary(data.summary);
      renderFields(data.fields);
      $('#exportCsv').disabled = false;
      $('#exportPdf').disabled = false;
      notify('Report loaded');
    } catch (error) {
      notify(error.message, true);
    }
  });

  $('#exportCsv').addEventListener('click', async () => {
    try {
      await exportReport('csv');
      notify('CSV export generated');
    } catch (error) {
      notify(error.message, true);
    }
  });

  $('#exportPdf').addEventListener('click', async () => {
    try {
      await exportReport('pdf');
      notify('PDF export generated');
    } catch (error) {
      notify(error.message, true);
    }
  });
}

window.addEventListener('DOMContentLoaded', bindEvents);
