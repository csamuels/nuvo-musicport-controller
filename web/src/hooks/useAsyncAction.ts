import { useState, useCallback } from 'react';
import { useStatus } from '../contexts/StatusContext';

interface UseAsyncActionOptions {
  onSuccess?: (result: any) => void;
  onError?: (error: Error) => void;
  successMessage?: string;
  loadingMessage?: string;
  errorMessage?: string | ((error: Error) => string);
}

export function useAsyncAction<T extends (...args: any[]) => Promise<any>>(
  action: T,
  options: UseAsyncActionOptions = {}
) {
  const [isLoading, setIsLoading] = useState(false);
  const { showStatus, clearStatus } = useStatus();

  const execute = useCallback(
    async (...args: Parameters<T>): Promise<ReturnType<T> | null> => {
      setIsLoading(true);

      // Show loading message if provided
      let loadingId: string | undefined;
      if (options.loadingMessage) {
        loadingId = showStatus(options.loadingMessage, 'loading');
      }

      try {
        const result = await action(...args);

        // Clear loading message
        if (loadingId) {
          clearStatus(loadingId);
        }

        // Show success message
        if (options.successMessage) {
          showStatus(options.successMessage, 'success');
        }

        // Call success callback
        if (options.onSuccess) {
          options.onSuccess(result);
        }

        return result;
      } catch (error) {
        // Clear loading message
        if (loadingId) {
          clearStatus(loadingId);
        }

        const err = error as Error;

        // Determine error message
        let errorMsg = 'An error occurred';
        if (options.errorMessage) {
          errorMsg = typeof options.errorMessage === 'function'
            ? options.errorMessage(err)
            : options.errorMessage;
        } else {
          errorMsg = err.message || 'An error occurred';
        }

        // Show error message
        showStatus(errorMsg, 'error', 10000); // Keep errors longer

        // Call error callback
        if (options.onError) {
          options.onError(err);
        }

        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [action, options, showStatus, clearStatus]
  );

  return { execute, isLoading };
}
