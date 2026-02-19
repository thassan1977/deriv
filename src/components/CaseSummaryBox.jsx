import { Box, Grid, Typography, Paper } from "@mui/material";

function CaseSummaryBox({ stats }) {
  const items = [
    { label: 'TOTAL', value: stats.total_cases, color: '#f8fafc' },
    { label: 'BLOCKED', value: stats.auto_blocked, color: '#ef4444' },
    { label: 'APPROVED', value: stats.auto_approved, color: '#10b981' },
    { label: 'MANUAL', value: stats.manual_cases, color: '#3b82f6' },
  ];

  return (
    <Paper sx={{ 
      p: 2, 
      bgcolor: '#1e293b', 
      borderRadius: 4, 
      border: '1px solid #334155',
      background: 'linear-gradient(145deg, #1e293b 0%, #0f172a 100%)'
    }}>
      <Grid container spacing={2}>
        {items.map((item) => (
          <Grid item xs={6} key={item.label}>
            <Box sx={{ borderLeft: `3px solid ${item.color}`, pl: 2, py: 1 }}>
              <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 'bold', letterSpacing: 1 }}>
                {item.label}
              </Typography>
              <Typography variant="h5" sx={{ color: item.color, fontWeight: '800' }}>
                {item.value?.toLocaleString() || 0}
              </Typography>
            </Box>
          </Grid>
        ))}
      </Grid>
    </Paper>
  );
}

export default CaseSummaryBox; // Move export to the bottom