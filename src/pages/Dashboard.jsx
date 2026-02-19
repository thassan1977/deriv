import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Box, Typography, Stack, Paper, Button, 
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow 
} from "@mui/material";
import { createWebSocketClient } from "../api/websocket";
import { getQueue, getStats } from "../api/fraudApi";

// Components
import StatsCards from "../components/StatsCards";
import FraudDistributionPie from "../components/FraudDistributionPie";
import CaseTrendChart from "../components/CaseTrendChart";

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({ total_cases: 0, auto_approved: 0, auto_blocked: 0, manual_cases: 0, tps: 0 });
  const [cases, setCases] = useState([]);

  useEffect(() => {
    // Initial Data Load
    getStats().then(res => setStats(res.data));
    getQueue().then(res => setCases(res.data || []));

    // WebSocket for Real-time updates
    const client = createWebSocketClient((msg) => {
      if (msg.caseId) {
        setCases(prev => [msg, ...prev].slice(0, 25)); 
      } else {
        setStats(msg);
      }
    });
    client.activate();
    return () => client.deactivate();
  }, []);

  return (
    <Box sx={{ 
      bgcolor: '#020617', 
      height: '100vh', 
      width: '100vw', 
      display: 'flex', 
      overflow: 'hidden', 
      color: '#f8fafc',
      fontFamily: 'Inter, sans-serif'
    }}>
      
      {/* LEFT CONTENT: ANALYTICS HUB */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 2, gap: 2, minWidth: 0 }}>
        
        {/* TOP HUD HEADER */}
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 900, letterSpacing: -1.5, color: '#f8fafc' }}>
              DERIV<span style={{ color: '#3b82f6' }}>HACKATHON</span> COMMAND CENTER
            </Typography>
            <Typography sx={{ color: '#475569', fontSize: '0.65rem', letterSpacing: 2, textTransform: 'uppercase' }}>
              Multilayer Fraud Engine // Live Dashboard
            </Typography>
          </Box>
          <SystemStatusPill />
        </Stack>

        {/* ALIGNED BODY: STATS AND GRAPHS */}
        <Stack spacing={2} sx={{ flex: 1, minHeight: 0, width: '100%' }}>
          
          {/* STATS ROW (Forced alignment) */}
          <Box sx={{ width: '100%' }}>
            <StatsCards stats={stats} />
          </Box>

          {/* ANALYTICS ROW */}
          <Box sx={{ display: 'flex', gap: 2, flex: 1, minHeight: 0, width: '100%' }}>
            
            <Paper sx={{ flex: 1, p: 2, bgcolor: '#0f172a', border: '1px solid #1e293b', display: 'flex', flexDirection: 'column', borderRadius: 1 }}>
              <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 'bold', mb: 2 }}>DECISION_DISTRIBUTION</Typography>
              <Box sx={{ flex: 1, minHeight: 0 }}>
                <FraudDistributionPie stats={stats} />
              </Box>
            </Paper>

            <Paper sx={{ flex: 2, p: 2, bgcolor: '#0f172a', border: '1px solid #1e293b', display: 'flex', flexDirection: 'column', borderRadius: 1 }}>
              <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 'bold', mb: 2 }}>VELOCITY_TIME_SERIES</Typography>
              <Box sx={{ flex: 1, minHeight: 0 }}>
                <CaseTrendChart stats={stats} />
              </Box>
            </Paper>

          </Box>
        </Stack>
      </Box>

      {/* RIGHT SIDEBAR: LIVE_DECISION_STREAM */}
      <Box sx={{ 
        width: '420px', 
        bgcolor: '#070a13', 
        borderLeft: '1px solid #1e293b',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <Box sx={{ p: 2, borderBottom: '1px solid #1e293b', bgcolor: '#0f172a' }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="caption" sx={{ color: '#f8fafc', fontWeight: '900', letterSpacing: 1.5 }}>
              LIVE_STREAM
            </Typography>
            <Typography variant="caption" sx={{ color: '#3b82f6', fontSize: '10px' }}>
              {cases.length} EVENTS_CACHED
            </Typography>
          </Stack>
        </Box>

        <TableContainer sx={{ flex: 1, overflowY: 'auto' }}>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ bgcolor: '#070a13', color: '#475569', fontSize: '10px', py: 1, borderBottom: '1px solid #1e293b' }}>CASE_LOG</TableCell>
                {/* <TableCell align="center" sx={{ bgcolor: '#070a13', color: '#475569', fontSize: '10px', py: 1, borderBottom: '1px solid #1e293b' }}>Amount</TableCell> */}
                <TableCell align="right" sx={{ bgcolor: '#070a13', color: '#475569', fontSize: '10px', py: 1, borderBottom: '1px solid #1e293b' }}>ACTION</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {cases.map((c) => {
                
                const transactionId = c.transactionId || 'none';
                const riskColor = '#10b981';

                return (
                  <TableRow key={c.caseId} sx={{ '&:hover': { bgcolor: '#0f172a' } }}>
                    <TableCell sx={{ py: 1.5, borderBottom: '1px solid #161e31' }}>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Box sx={{ 
                          width: 6, height: 6, borderRadius: '50%', 
                          bgcolor: riskColor,
                          boxShadow: `0 0 6px ${riskColor}`
                        }} />
                        <Box>
                          <Typography sx={{ color: '#f8fafc', fontWeight: 'bold', fontSize: '0.75rem', lineHeight: 1 }}>
                            {c.userId || 'USR-UNK'}
                          </Typography>
                          <Typography sx={{ color: '#475569', fontSize: '0.6rem', mt: 0.2 }}>
                            {c.caseId.slice(-10)}
                          </Typography>
                        </Box>
                      </Stack>
                    </TableCell>

                    {/* <TableCell align="center" sx={{ py: 1.5, borderBottom: '1px solid #161e31' }}>
                      <Typography sx={{ color: riskColor, fontSize: '0.75rem', fontWeight: '900', fontFamily: 'monospace' }}>
                        {transactionId}
                      </Typography>
                    </TableCell> */}

                    <TableCell align="right" sx={{ py: 1.5, borderBottom: '1px solid #161e31' }}>
                      <Button 
                        size="small"
                        variant="outlined"
                        onClick={() => navigate(`/case/${c.caseId}`)}
                        sx={{ 
                          fontSize: '9px', 
                          color: '#3b82f6', 
                          borderColor: 'rgba(59, 130, 246, 0.3)',
                          minWidth: '40px', height: '22px',
                          '&:hover': { borderColor: '#3b82f6', bgcolor: 'rgba(59, 130, 246, 0.1)' }
                        }}
                      >
                        Investigate
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Box>
  );
}

function SystemStatusPill() {
  return (
    <Box sx={{ 
      bgcolor: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.2)',
      px: 1.5, py: 0.4, borderRadius: 1, display: 'flex', alignItems: 'center', gap: 1
    }}>
      <Box sx={{ width: 6, height: 6, bgcolor: '#10b981', borderRadius: '50%' }} />
      <Typography sx={{ color: '#10b981', fontSize: '0.65rem', fontWeight: 'bold' }}>NETWORK_STABLE</Typography>
    </Box>
  );
}