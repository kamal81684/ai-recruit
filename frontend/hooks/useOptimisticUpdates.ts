/**
 * Optimistic UI Updates Hook for AI Recruit
 *
 * Provides optimistic updates for better user experience by updating
 * the UI immediately before API confirmation, rolling back on error.
 *
 * Contributor: shubham21155102 - UX Enhancements
 */

import { useState, useCallback, useRef } from 'react';

export interface OptimisticAction<T> {
  id: string;
  data: T;
  timestamp: number;
}

export interface OptimisticState<T> {
  items: T[];
  pendingActions: Map<string, OptimisticAction<T>>;
}

export interface UseOptimisticUpdatesOptions<T> {
  /**
   * Function to identify items (default: 'id' property)
   */
  getKey?: (item: T) => string;

  /**
   * Function to call when action succeeds
   */
  onSuccess?: (item: T, previousData?: T) => void;

  /**
   * Function to call when action fails
   */
  onError?: (error: Error, item: T, previousData?: T) => void;

  /**
   * Delay before automatic rollback on error (ms)
   */
  rollbackDelay?: number;
}

/**
 * Hook for optimistic updates with automatic rollback
 *
 * @example
 * ```tsx
 * const { data, updateItem, deleteItem, addItem } = useOptimisticUpdates({
 *   getKey: (item) => item.id,
 *   onSuccess: (item) => toast.success('Updated successfully'),
 *   onError: (error) => toast.error('Update failed')
 * });
 * ```
 */
export function useOptimisticUpdates<T extends Record<string, any>>(
  initialData: T[] = [],
  options: UseOptimisticUpdatesOptions<T> = {}
) {
  const {
    getKey = (item: T) => item.id,
    onSuccess,
    onError,
    rollbackDelay = 3000
  } = options;

  const [data, setData] = useState<T[]>(initialData);
  const [optimisticData, setOptimisticData] = useState<T[]>(initialData);
  const pendingActions = useRef(new Map<string, OptimisticAction<T>>());
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Merge optimistic changes with base data
   */
  const getMergedData = useCallback(() => {
    const merged = [...data];

    // Apply pending optimistic updates
    pendingActions.current.forEach((action) => {
      const index = merged.findIndex(item => getKey(item) === action.id);
      if (index !== -1) {
        merged[index] = action.data;
      }
    });

    return merged;
  }, [data, getKey]);

  /**
   * Update an item optimistically
   */
  const updateItem = useCallback(async (
    itemId: string,
    updates: Partial<T>,
    apiCall: () => Promise<T>
  ) => {
    const itemIndex = data.findIndex(item => getKey(item) === itemId);
    if (itemIndex === -1) {
      throw new Error(`Item with id ${itemId} not found`);
    }

    const previousData = data[itemIndex];
    const optimisticItem = { ...previousData, ...updates };

    // Create optimistic action
    const actionId = `update-${itemId}-${Date.now()}`;
    const action: OptimisticAction<T> = {
      id: actionId,
      data: optimisticItem,
      timestamp: Date.now()
    };

    // Apply optimistic update
    pendingActions.current.set(actionId, action);
    setOptimisticData(getMergedData());

    try {
      setIsLoading(true);
      const result = await apiCall();

      // Success: update actual data
      setData(prev => {
        const index = prev.findIndex(item => getKey(item) === itemId);
        if (index !== -1) {
          const newPrev = [...prev];
          newPrev[index] = result;
          return newPrev;
        }
        return prev;
      });

      // Remove pending action
      pendingActions.current.delete(actionId);
      setOptimisticData(getMergedData());

      onSuccess?.(result, previousData);
      return result;

    } catch (error) {
      // Rollback optimistic update
      pendingActions.current.delete(actionId);
      setOptimisticData(getMergedData());

      onError?.(error as Error, optimisticItem, previousData);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [data, getKey, getMergedData, onSuccess, onError]);

  /**
   * Delete an item optimistically
   */
  const deleteItem = useCallback(async (
    itemId: string,
    apiCall: () => Promise<void>
  ) => {
    const itemIndex = data.findIndex(item => getKey(item) === itemId);
    if (itemIndex === -1) {
      throw new Error(`Item with id ${itemId} not found`);
    }

    const previousData = data[itemIndex];

    // Create optimistic action (marked as deleted)
    const actionId = `delete-${itemId}-${Date.now()}`;
    const action: OptimisticAction<T> = {
      id: actionId,
      data: { ...previousData, _deleted: true } as T,
      timestamp: Date.now()
    };

    // Apply optimistic deletion
    pendingActions.current.set(actionId, action);
    setOptimisticData(prev => prev.filter(item => getKey(item) !== itemId));

    try {
      setIsLoading(true);
      await apiCall();

      // Success: remove from actual data
      setData(prev => prev.filter(item => getKey(item) !== itemId));

      // Remove pending action
      pendingActions.current.delete(actionId);

      onSuccess?.(previousData, previousData);

    } catch (error) {
      // Rollback optimistic deletion
      pendingActions.current.delete(actionId);
      setOptimisticData(getMergedData());

      onError?.(error as Error, previousData, previousData);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [data, getKey, getMergedData, onSuccess, onError]);

  /**
   * Add an item optimistically
   */
  const addItem = useCallback(async (
    newItem: Omit<T, 'id'>,
    apiCall: () => Promise<T>
  ) => {
    // Generate temporary ID
    const tempId = `temp-${Date.now()}`;
    const optimisticItem = { ...newItem, id: tempId } as T;

    // Create optimistic action
    const actionId = `add-${tempId}`;
    const action: OptimisticAction<T> = {
      id: actionId,
      data: optimisticItem,
      timestamp: Date.now()
    };

    // Apply optimistic addition
    pendingActions.current.set(actionId, action);
    setOptimisticData(prev => [...prev, optimisticItem]);

    try {
      setIsLoading(true);
      const result = await apiCall();

      // Success: add to actual data
      setData(prev => [...prev, result]);

      // Remove pending action
      pendingActions.current.delete(actionId);
      setOptimisticData(getMergedData());

      onSuccess?.(result, undefined);
      return result;

    } catch (error) {
      // Rollback optimistic addition
      pendingActions.current.delete(actionId);
      setOptimisticData(getMergedData());

      onError?.(error as Error, optimisticItem, undefined);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [getMergedData, onSuccess, onError]);

  /**
   * Refresh data from server
   */
  const refresh = useCallback(async (apiCall: () => Promise<T[]>) => {
    try {
      setIsLoading(true);
      const result = await apiCall();
      setData(result);
      setOptimisticData(result);
      return result;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    data: optimisticData,
    originalData: data,
    isLoading,
    updateItem,
    deleteItem,
    addItem,
    refresh,
    hasPendingChanges: pendingActions.current.size > 0
  };
}

/**
 * Hook for optimistic toggle actions (like starring a candidate)
 */
export function useOptimisticToggle<T extends Record<string, any>>(
  initialData: T[] = [],
  options: UseOptimisticUpdatesOptions<T> = {}
) {
  const { updateItem, ...rest } = useOptimisticUpdates(initialData, options);

  const toggle = useCallback(async (
    itemId: string,
    field: keyof T,
    apiCall: (newValue: boolean) => Promise<T>
  ) => {
    const item = rest.originalData.find(i => options.getKey?.(i) === itemId);
    if (!item) throw new Error('Item not found');

    const currentValue = item[field] as boolean;
    const newValue = !currentValue;

    return updateItem(itemId, { [field]: newValue } as Partial<T>, () => apiCall(newValue));
  }, [updateItem, rest.originalData, options.getKey]);

  return {
    ...rest,
    updateItem,
    toggle
  };
}

/**
 * Hook for batch optimistic updates
 */
export function useOptimisticBatch<T extends Record<string, any>>(
  initialData: T[] = [],
  options: UseOptimisticUpdatesOptions<T> = {}
) {
  const [data, setData] = useState<T[]>(initialData);
  const [pendingBatch, setPendingBatch] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);

  const updateBatch = useCallback(async (
    itemIds: string[],
    updates: Partial<T>,
    apiCall: (ids: string[]) => Promise<T[]>
  ) => {
    // Store previous states
    const previousData = new Map<string, T>();
    data.forEach(item => {
      if (itemIds.includes(options.getKey?.(item) || item.id)) {
        previousData.set(options.getKey?.(item) || item.id, { ...item });
      }
    });

    // Apply optimistic updates
    const batchId = `batch-${Date.now()}`;
    setPendingBatch(prev => new Set([...prev, batchId]));

    setData(prev => prev.map(item => {
      const id = options.getKey?.(item) || item.id;
      if (itemIds.includes(id)) {
        return { ...item, ...updates };
      }
      return item;
    }));

    try {
      setIsLoading(true);
      const result = await apiCall(itemIds);

      // Update with server response
      setData(result);

      setPendingBatch(prev => {
        const newSet = new Set(prev);
        newSet.delete(batchId);
        return newSet;
      });

      return result;

    } catch (error) {
      // Rollback on error
      setData(prev => prev.map(item => {
        const id = options.getKey?.(item) || item.id;
        return previousData.get(id) || item;
      }));

      setPendingBatch(prev => {
        const newSet = new Set(prev);
        newSet.delete(batchId);
        return newSet;
      });

      options.onError?.(error as Error, updates as T, undefined);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [data, options]);

  return {
    data,
    isLoading,
    updateBatch,
    hasPendingBatch: pendingBatch.size > 0
  };
}
