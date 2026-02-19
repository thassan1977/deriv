import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Box } from '@mui/material';

export default function FraudDistributionPie({ stats }) {
  const data = [
    { name: 'Approved', value: stats.auto_approved || 0, color: '#10b981' },
    { name: 'Blocked', value: stats.auto_blocked || 0, color: '#ef4444' },
    { name: 'Manual', value: stats.manual_cases || 0, color: '#3b82f6' },
  ];

  return (
    <Box sx={{ height: 220, width: '100%' }}>
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={data}
            innerRadius={60}
            outerRadius={80}
            paddingAngle={5}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: 8 }}
            itemStyle={{ color: '#fff' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </Box>
  );
}
