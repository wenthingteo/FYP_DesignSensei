import { useState, useEffect } from 'react';

const useSidebarUpdates = () => {
  const [updateTrigger, setUpdateTrigger] = useState(0);
  
  useEffect(() => {
    const handleSidebarUpdate = () => {
      setUpdateTrigger(prev => prev + 1);
    };
    
    window.addEventListener('sidebarUpdate', handleSidebarUpdate);
    return () => window.removeEventListener('sidebarUpdate', handleSidebarUpdate);
  }, []);
  
  const triggerSidebarUpdate = () => {
    window.dispatchEvent(new CustomEvent('sidebarUpdate'));
  };
  
  return { updateTrigger, triggerSidebarUpdate };
};

export default useSidebarUpdates;