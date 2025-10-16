import React, { useCallback, useEffect, useMemo, useState } from 'react';
import AssignmentDashboard from './components/AssignmentDashboard.jsx';
import FormRenderer from './components/FormRenderer.jsx';
import useAutosaveResponse from './hooks/useAutosaveResponse.js';

const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL ?? 'http://localhost:8000';

const App = () => {
  const [forms, setForms] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [selectedFormId, setSelectedFormId] = useState(null);
  const [currentResponseId, setCurrentResponseId] = useState(null);
  const [responses, setResponses] = useState({});
  const [userId, setUserId] = useState('alice');
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoadingForms, setIsLoadingForms] = useState(false);
  const [isLoadingResponse, setIsLoadingResponse] = useState(false);

  const selectedForm = useMemo(
    () => forms.find((form) => form.id === selectedFormId) ?? null,
    [forms, selectedFormId]
  );
  const activeResponse = currentResponseId ? responses[currentResponseId] : null;

  const fetchForms = useCallback(async () => {
    setIsLoadingForms(true);
    try {
      const response = await fetch(`${API_BASE_URL}/forms`);
      if (!response.ok) {
        throw new Error('Unable to load forms');
      }
      const payload = await response.json();
      setForms(payload);
    } catch (error) {
      console.error(error);
      setErrorMessage(error.message ?? 'Failed to load forms');
    } finally {
      setIsLoadingForms(false);
    }
  }, []);

  const fetchAssignments = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/${userId}/assignments`);
      if (!response.ok) {
        throw new Error('Unable to load assignments');
      }
      const payload = await response.json();
      setAssignments(payload);
      return payload;
    } catch (error) {
      console.error(error);
      setErrorMessage(error.message ?? 'Failed to load assignments');
      return [];
    }
  }, [userId]);

  useEffect(() => {
    fetchForms();
  }, [fetchForms]);

  useEffect(() => {
    fetchAssignments();
  }, [fetchAssignments]);

  const ensureResponseLoaded = useCallback(
    async (responseId) => {
      if (responses[responseId]) {
        return responses[responseId];
      }
      const response = await fetch(`${API_BASE_URL}/form-responses/${responseId}`);
      if (!response.ok) {
        throw new Error('Unable to load form response');
      }
      const payload = await response.json();
      setResponses((prev) => ({
        ...prev,
        [payload.id]: { ...payload, dirty: false },
      }));
      return payload;
    },
    [responses]
  );

  const handleSelectForm = useCallback(
    async (formId) => {
      setSelectedFormId(formId);
      setIsLoadingResponse(true);
      setErrorMessage('');
      try {
        let assignment = assignments.find((item) => item.form_id === formId);
        let currentAssignments = assignments;

        if (!assignment) {
          const response = await fetch(`${API_BASE_URL}/forms/${formId}/assign`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId }),
          });
          if (!response.ok) {
            throw new Error('Failed to assign form');
          }
          currentAssignments = await fetchAssignments();
          assignment = currentAssignments.find((item) => item.form_id === formId) ?? null;
        }

        if (!assignment) {
          throw new Error('Assignment not found after creation');
        }

        setCurrentResponseId(assignment.response_id);
        await ensureResponseLoaded(assignment.response_id);
      } catch (error) {
        console.error(error);
        setErrorMessage(error.message ?? 'Unable to load form response');
      } finally {
        setIsLoadingResponse(false);
      }
    },
    [assignments, userId, fetchAssignments, ensureResponseLoaded]
  );

  const handleFieldChange = useCallback(
    (fieldId, value) => {
      if (!currentResponseId) {
        return;
      }
      setResponses((prev) => {
        const current = prev[currentResponseId] ?? { answers: {}, status: 'Not Started', progress: 0 };
        return {
          ...prev,
          [currentResponseId]: {
            ...current,
            answers: { ...current.answers, [fieldId]: value },
            dirty: true,
          },
        };
      });
    },
    [currentResponseId]
  );

  const handleAutosaveUpdate = useCallback((updatedResponse) => {
    setResponses((prev) => {
      const current = prev[updatedResponse.id] ?? {};
      return {
        ...prev,
        [updatedResponse.id]: {
          ...current,
          ...updatedResponse,
          dirty: false,
        },
      };
    });
    setAssignments((prev) =>
      prev.map((assignment) =>
        assignment.response_id === updatedResponse.id
          ? { ...assignment, status: updatedResponse.status, progress: updatedResponse.progress }
          : assignment
      )
    );
  }, []);

  useAutosaveResponse({
    responseId: currentResponseId,
    answers: activeResponse?.answers ?? {},
    isDirty: activeResponse?.dirty ?? false,
    apiBaseUrl: API_BASE_URL,
    onSaved: handleAutosaveUpdate,
  });

  const handleReassign = useCallback(
    async ({ formId, responseId, userId: newUserId }) => {
      const response = await fetch(`${API_BASE_URL}/forms/${formId}/assign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: newUserId, response_id: responseId }),
      });
      if (!response.ok) {
        throw new Error('Failed to reassign form');
      }
      await fetchAssignments();
    },
    [fetchAssignments]
  );

  const handleUserChange = useCallback((event) => {
    setUserId(event.target.value);
  }, []);

  const handleRefreshAssignments = useCallback(() => {
    fetchAssignments();
  }, [fetchAssignments]);

  return (
    <div className="container">
      <aside className="sidebar">
        <h2>Form Templates</h2>
        {isLoadingForms ? (
          <p>Loading forms...</p>
        ) : (
          <ul className="form-list">
            {forms.map((form) => (
              <li key={form.id}>
                <button
                  type="button"
                  onClick={() => handleSelectForm(form.id)}
                  className={form.id === selectedFormId ? 'active' : ''}
                >
                  <strong>{form.name}</strong>
                  <br />
                  <small>{form.description}</small>
                </button>
              </li>
            ))}
          </ul>
        )}
        <div className="card" style={{ marginTop: '1rem' }}>
          <h3>User Assignments</h3>
          <label htmlFor="user-id-input">User</label>
          <input
            id="user-id-input"
            type="text"
            value={userId}
            onChange={handleUserChange}
            onBlur={handleRefreshAssignments}
          />
          <button type="button" style={{ marginTop: '0.75rem' }} onClick={handleRefreshAssignments}>
            Refresh Assignments
          </button>
        </div>
      </aside>
      <main className="main-panel">
        {errorMessage ? (
          <div className="card" style={{ border: '1px solid #fca5a5', background: '#fef2f2' }}>
            <p>{errorMessage}</p>
          </div>
        ) : null}
        {isLoadingResponse && (
          <div className="card">
            <p>Loading response...</p>
          </div>
        )}
        <FormRenderer form={selectedForm} response={activeResponse} onFieldChange={handleFieldChange} />
        <AssignmentDashboard assignments={assignments} onReassign={handleReassign} />
      </main>
    </div>
  );
};

export default App;
