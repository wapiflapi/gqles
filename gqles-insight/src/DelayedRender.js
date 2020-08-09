import { useEffect, useState } from 'react';

const useDelayedRender = (delay, skip) => {
    const [delayed, setDelayed] = useState(true);
    useEffect(() => {
        const timeout = setTimeout(() => setDelayed(false), delay || 100);
        return () => clearTimeout(timeout);
    }, [delay]);
    return fn => (!delayed || skip) ? fn() : null;
};

const DelayedRender = ({ skip, delay, children }) =>
      useDelayedRender(skip, delay)(() => children);

export default DelayedRender;
