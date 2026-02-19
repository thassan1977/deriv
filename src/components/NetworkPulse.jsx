import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts';
import { Box } from '@mui/material';
import { useEffect, useState } from 'react';

export default function NetworkPulse() {
  // Generate initial "static" data
  const [data, setData] = useState(Array.from({ length: 20 }, (_, i) => ({ v: 25 })));

  useEffect(() => {
    const interval = setInterval(() => {
      setData(prev => {
        const newData = [...prev.slice(1), { v: Math.floor(Math.random() * 15) + 20 }];
        return newData;
      });
    }, 200); // Fast update for smooth "pulse"
    return () => clearInterval(interval);
  }, []);

  return (
    <Box sx={{ height: 45, width: '100%', mt: 1, opacity: 0.6, pointerEvents: 'none' }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <YAxis hide domain={[0, 50]} />
          <Line 
            type="monotone" 
            dataKey="v" 
            stroke="#3b82f6" 
            strokeWidth={2} 
            dot={false} 
            isAnimationActive={false} // Important: keep this false for high-frequency updates
          />
        </LineChart>
      </ResponsiveContainer>
    </Box>
  );
}