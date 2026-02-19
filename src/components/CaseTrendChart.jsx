import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Box, Typography, Paper } from '@mui/material';
import { useState, useEffect, useRef } from 'react';

export default function CaseTrendChart({ stats }) {
  const [history, setHistory] = useState([]);
  // Use a ref to store the latest stats without triggering a render
  const latestStats = useRef(stats);

  // Keep the ref in sync with the prop
  useEffect(() => {
    latestStats.current = stats;
  }, [stats]);

  useEffect(() => {
    // Update the chart at a steady heartbeat (1 second)
    const interval = setInterval(() => {
      const timestamp = new Date().toLocaleTimeString([], { 
        hour12: false, 
        minute: '2-digit', 
        second: '2-digit' 
      });

      setHistory(prev => {
        const newSnap = {
          time: timestamp,
          total: latestStats.current.total_cases || 0,
          blocked: latestStats.current.auto_blocked || 0,
          approved: latestStats.current.auto_approved || 0,
          manual: latestStats.current.manual_cases || 0,
        };
        return [...prev, newSnap].slice(-20); // Show last 20 data points
      });
    }, 1000); 

    return () => clearInterval(interval);
  }, []); // Only run once on mount

  return (
    <Paper sx={{ 
      p: 2, 
      bgcolor: '#1e293b', 
      borderRadius: 4, 
      border: '1px solid #334155',
      height: 320,
      background: 'linear-gradient(180deg, rgba(30, 41, 59, 1) 0%, rgba(15, 23, 42, 1) 100%)'
    }}>
      <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 'bold', mb: 2, display: 'block', letterSpacing: 1.5 }}>
        ANALYTICS_TIME_SERIES // LIVE_VELOCITY
      </Typography>
      <Box sx={{ height: 240, width: '100%' }}>
        <ResponsiveContainer>
          <LineChart data={history}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis dataKey="time" stroke="#475569" fontSize={10} tickMargin={10} hide={history.length < 5} />
            <YAxis stroke="#475569" fontSize={10} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: 8, fontSize: '10px' }}
            />
            <Legend iconType="rect" wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }} />
            <Line type="monotone" dataKey="total" name="TOTAL" stroke="#f8fafc" strokeWidth={2} dot={false} isAnimationActive={false} />
            <Line type="monotone" dataKey="blocked" name="BLOCKED" stroke="#ef4444" strokeWidth={2} dot={false} isAnimationActive={false} />
            <Line type="monotone" dataKey="approved" name="APPROVED" stroke="#10b981" strokeWidth={2} dot={false} isAnimationActive={false} />
            <Line type="monotone" dataKey="manual" name="MANUAL" stroke="#3b82f6" strokeWidth={2} dot={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </Box>
    </Paper>
  );
}