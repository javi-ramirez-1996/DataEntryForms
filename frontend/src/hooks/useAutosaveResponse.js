import { useEffect, useRef } from 'react';

const AUTOSAVE_DELAY = 600;

const useAutosaveResponse = ({ responseId, answers, isDirty, apiBaseUrl, onSaved }) => {
  const controllerRef = useRef();

  useEffect(() => {
    if (!responseId || !isDirty) {
      return undefined;
    }

    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    const timeout = setTimeout(async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/form-responses/${responseId}`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ answers }),
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error('Autosave failed');
        }
        const payload = await response.json();
        onSaved?.(payload);
      } catch (error) {
        if (error.name === 'AbortError') {
          return;
        }
        console.error('Failed to autosave response', error);
      }
    }, AUTOSAVE_DELAY);

    return () => {
      clearTimeout(timeout);
      controller.abort();
    };
  }, [responseId, answers, isDirty, apiBaseUrl, onSaved]);
};

export default useAutosaveResponse;
