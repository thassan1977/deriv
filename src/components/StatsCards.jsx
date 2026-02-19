import { Grid, Paper, Typography, Box } from "@mui/material";
import NetworkPulse from "./NetworkPulse";

export default function StatsCards({ stats }) {
  const getMeta = (key) => {
    switch (key.toLowerCase()) {
      case 'tps': return { label: 'Realtime TPS', color: '#3b82f6', trend: '↑ Stable' };
      case 'manual_cases': return { label: 'Manual Cases', color: '#f59e0b', trend: '⚙ Processing' };
      case 'auto_blocked': return { label: 'Auto Blocked', color: '#ef4444', trend: '⚠ Critical' };
      case 'total_cases': return { label: 'Total Cases', color: '#10b981', trend: '● Active' };
      case 'auto_approved': return { label: 'Auto Approved', color: '#10b981', trend: '● Active' };
      default: return { label: key.replaceAll("_", " "), color: '#94a3b8', trend: '● Active' };
    }
  };

  return (
    <Grid container spacing={2} sx={{ mb: 3 }}>
      {Object.entries(stats).map(([key, value]) => {
        // Only show relevant stats to avoid clutter
        if (['total_cases', 'tps', 'manual_cases', 'auto_blocked', 'auto_approved'].indexOf(key.toLowerCase()) === -1) return null;

        const meta = getMeta(key);
        const isTPS = key.toLowerCase() === 'tps';

        return (
          <Grid item xs={12} md={2.4} key={key}> {/* Adjusted to 2.4 for a 5-card row */}
            <Paper sx={{ 
              p: 2, 
              bgcolor: '#1e293b', 
              color: 'white', 
              borderRadius: 3,
              border: '1px solid #334155',
              borderLeft: `6px solid ${meta.color}`,
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between'
            }}>
              <Box>
                <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: 1 }}>
                  {meta.label}
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: '800', mt: 1, fontFamily: 'JetBrains Mono, monospace' }}>
                  {value.toLocaleString()}
                </Typography>
              </Box>

              {/* DROP NETWORK PULSE HERE IF IT'S TPS */}
              {isTPS && <NetworkPulse />}

              <Typography variant="caption" sx={{ color: meta.color, fontWeight: 'bold', mt: isTPS ? 0 : 2 }}>
                {meta.trend}
              </Typography>
            </Paper>
          </Grid>
        );
      })}
    </Grid>
  );
}