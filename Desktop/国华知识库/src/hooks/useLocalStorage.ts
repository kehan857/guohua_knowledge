import { useState, useEffect } from 'react';

// Custom hook for managing localStorage data
function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T) => void] {
  // Get from localStorage or use initial value
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error('Error reading localStorage key:', key, error);
      return initialValue;
    }
  });

  // Update localStorage when the stored value changes
  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(storedValue));
    } catch (error) {
      console.error('Error writing to localStorage key:', key, error);
    }
  }, [key, storedValue]);

  // Return a wrapped version of useState's setter function that persists the new value to localStorage
  const setValue = (value: T) => {
    setStoredValue(value);
  };

  return [storedValue, setValue];
}

export default useLocalStorage;