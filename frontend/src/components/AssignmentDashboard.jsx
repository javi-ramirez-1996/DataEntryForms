import React, { useState } from 'react';

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

const AssignmentDashboard = ({ assignments, onReassign }) => {
  if (!assignments.length) {
    return (
      <div className="card">
        <h3>Assignments</h3>
        <p>No forms assigned yet. Select a form to get started.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h3>Assignments</h3>
      {assignments.map((assignment) => (
        <AssignmentRow
          key={assignment.response_id}
          assignment={assignment}
          onReassign={onReassign}
        />
      ))}
    </div>
  );
};

const AssignmentRow = ({ assignment, onReassign }) => {
  const [userId, setUserId] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { form_name: formName, status, progress, response_id: responseId, form_id: formId } =
    assignment;

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!userId.trim()) {
      return;
    }
    setIsSubmitting(true);
    try {
      await onReassign({ formId, responseId, userId: userId.trim() });
      setUserId('');
    } catch (error) {
      console.error('Failed to reassign form', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="assignment-card">
      <header>
        <h4>{formName}</h4>
        <span className={statusClass(status)}>{status}</span>
      </header>
      <p>{Math.round(progress * 100)}% complete</p>
      <footer>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem' }}>
          <input
            type="text"
            placeholder="Assign to user"
            value={userId}
            onChange={(event) => setUserId(event.target.value)}
          />
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Saving...' : 'Reassign'}
          </button>
        </form>
      </footer>
    </div>
  );
};

export default AssignmentDashboard;
