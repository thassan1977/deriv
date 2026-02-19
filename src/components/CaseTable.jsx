import {
  Table, TableHead, TableRow, TableCell, TableBody,
  Button, Box, Typography, Paper, TableContainer
} from "@mui/material";
import { useNavigate } from "react-router-dom";

export default function CaseTable({ cases = [] }) {
  const navigate = useNavigate();

  const getScoreColor = (score) => {
    if (score > 0.8) return '#ef4444'; // Red
    if (score > 0.5) return '#f59e0b'; // Amber
    return '#10b981'; // Green
  };

  if (!cases || cases.length === 0) {
    return (
      <Box sx={{ 
        p: 10, 
        textAlign: 'center', 
        bgcolor: 'rgba(30, 41, 59, 0.5)', 
        borderRadius: 4,
        position: 'relative',
        overflow: 'hidden',
        border: '1px solid #334155'
      }}>
        {/* Scanning Radar Overlay */}
        <Box sx={{
          position: 'absolute',
          top: 0, left: 0, right: 0, height: '2px',
          background: 'linear-gradient(90deg, transparent, #3b82f6, transparent)',
          animation: 'scan 3s linear infinite',
          '@keyframes scan': {
            '0%': { top: '0%' },
            '100%': { top: '100%' }
          }
        }} />
        <Typography sx={{ color: '#64748b', fontFamily: 'JetBrains Mono, monospace', letterSpacing: 2 }}>
          &gt; INITIALIZING_STREAM_LISTENER...
        </Typography>
        <Typography variant="caption" sx={{ color: '#334155' }}>
          AWAITING INBOUND REDIS TRAFFIC
        </Typography>
      </Box>
    );
  }

  return (
    <TableContainer component={Paper} sx={{ 
      bgcolor: 'transparent', 
      boxShadow: 'none',
      border: '1px solid #334155',
      borderRadius: 2,
      '&::-webkit-scrollbar': { width: '4px' },
      '&::-webkit-scrollbar-thumb': { bgcolor: '#334155', borderRadius: '10px' }
    }}>
      <Table size="small" stickyHeader>
        <TableHead>
          <TableRow>
            <TableCell sx={{ bgcolor: '#0f172a', color: '#64748b', fontWeight: 'bold', fontSize: '0.75rem' }}>TIME_STAMP</TableCell>
            <TableCell sx={{ bgcolor: '#0f172a', color: '#64748b', fontWeight: 'bold', fontSize: '0.75rem' }}>IDENTIFIER</TableCell>
            <TableCell sx={{ bgcolor: '#0f172a', color: '#64748b', fontWeight: 'bold', fontSize: '0.75rem' }}>RISK_INDEX</TableCell>
            <TableCell sx={{ bgcolor: '#0f172a', color: '#64748b', fontWeight: 'bold', fontSize: '0.75rem' }} align="right">ACTION</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {cases.map((c) => (
            <TableRow
              key={c.caseId}
              onClick={() => navigate(`/cases/${c.caseId}`)}
              sx={{
                cursor: 'pointer',
                transition: 'all 0.1s',
                '&:hover': {
                  bgcolor: 'rgba(59, 130, 246, 0.08) !important',
                  '& td': { color: '#fff' }
                }
              }}
            >
              <TableCell sx={{ 
                fontFamily: 'JetBrains Mono, monospace', 
                color: '#475569', 
                fontSize: '0.8rem',
                borderBottom: '1px solid #1e293b' 
              }}>
                {new Date(c.createdAt).toLocaleTimeString([], { hour12: false })}
              </TableCell>
              
              <TableCell sx={{ borderBottom: '1px solid #1e293b' }}>
                <Typography sx={{ color: '#94a3b8', fontSize: '0.85rem', fontWeight: 500 }}>
                  {c.userId}
                </Typography>
                <Typography variant="caption" sx={{ color: '#334155', fontFamily: 'JetBrains Mono' }}>
                  {c.caseId.substring(0, 12)}...
                </Typography>
              </TableCell>

              <TableCell sx={{ borderBottom: '1px solid #1e293b' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Box sx={{ 
                    width: '60px', height: '4px', bgcolor: '#1e293b', borderRadius: 1, overflow: 'hidden' 
                  }}>
                    <Box sx={{ 
                      width: `${c.fraudProbability * 100}%`, 
                      height: '100%', 
                      bgcolor: getScoreColor(c.fraudProbability),
                      boxShadow: `0 0 10px ${getScoreColor(c.fraudProbability)}`
                    }} />
                  </Box>
                  <Typography sx={{ 
                    color: getScoreColor(c.fraudProbability), 
                    fontFamily: 'JetBrains Mono', 
                    fontWeight: 'bold',
                    fontSize: '0.8rem'
                  }}>
                    {(c.fraudProbability * 100).toFixed(1)}%
                  </Typography>
                </Box>
              </TableCell>

              <TableCell align="right" sx={{ borderBottom: '1px solid #1e293b' }}>
                <Button 
                  size="small" 
                  variant="text" 
                  sx={{ 
                    color: '#3b82f6', 
                    fontSize: '0.7rem', 
                    '&:hover': { bgcolor: 'rgba(59, 130, 246, 0.2)' } 
                  }}
                >
                  INVESTIGATE //
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}