import React, { useMemo } from 'react';

const fieldRenderers = {
  text: ({ field, value, onChange }) => (
    <input
      id={field.id}
      type="text"
      value={value}
      onChange={(event) => onChange(field.id, event.target.value)}
    />
  ),
  textarea: ({ field, value, onChange }) => (
    <textarea
      id={field.id}
      rows={4}
      value={value}
      onChange={(event) => onChange(field.id, event.target.value)}
    />
  ),
  date: ({ field, value, onChange }) => (
    <input
      id={field.id}
      type="date"
      value={value}
      onChange={(event) => onChange(field.id, event.target.value)}
    />
  ),
  number: ({ field, value, onChange }) => (
    <input
      id={field.id}
      type="number"
      value={value}
      onChange={(event) => onChange(field.id, event.target.value)}
    />
  ),
  select: ({ field, value, onChange }) => (
    <select
      id={field.id}
      value={value}
      onChange={(event) => onChange(field.id, event.target.value)}
    >
      <option value="">Select an option</option>
      {field.options?.map((option) => (
        <option key={option} value={option}>
          {option}
        </option>
      ))}
    </select>
  ),
};

const statusClass = (status) => {
  switch (status) {
    case 'Complete':
      return 'badge status-complete';
    case 'In Progress':
      return 'badge status-progress';
    default:
      return 'badge status-not-started';
  }
};

const calculateProgress = (form, response) => {
  if (!form) {
    return 0;
  }
  const requiredFields = form.fields.filter((field) => field.required);
  if (!requiredFields.length) {
    return 1;
  }
  const answered = requiredFields.filter((field) => {
    const value = response?.answers?.[field.id];
    return value !== undefined && value !== null && value !== '';
  });
  return answered.length / requiredFields.length;
};

const formatProgress = (value) => Math.round(value * 100);

const FormRenderer = ({ form, response, onFieldChange }) => {
  const progress = useMemo(() => {
    if (response?.progress !== undefined) {
      return response.progress;
    }
    return calculateProgress(form, response);
  }, [form, response]);

  if (!form || !response) {
    return (
      <div className="card">
        <p>Select a form to begin completing a response.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <header>
        <h2>{form.name}</h2>
        <p>{form.description}</p>
      </header>
      <div className="badge-row">
        <span className={statusClass(response.status)}>{response.status}</span>
        <span className="badge">{formatProgress(progress)}% complete</span>
      </div>
      <div className="progress-bar">
        <span style={{ width: `${formatProgress(progress)}%` }} />
      </div>
      {form.fields.map((field) => {
        const Renderer = fieldRenderers[field.type] ?? fieldRenderers.text;
        const value = response.answers?.[field.id] ?? '';
        return (
          <div className="field" key={field.id}>
            <label htmlFor={field.id}>
              {field.label}
              {field.required ? ' *' : ''}
            </label>
            <Renderer field={field} value={value} onChange={onFieldChange} />
          </div>
        );
      })}
    </div>
  );
};

export default FormRenderer;
