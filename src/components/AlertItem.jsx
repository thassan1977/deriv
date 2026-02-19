import { Box, Typography, Stack, Chip } from "@mui/material";
import { useNavigate } from "react-router-dom";

export default function AlertItem({ caseData }) {
  const navigate = useNavigate();
  
  // High-intensity color for critical cases
  const isCritical = caseData.fraudProbability > 0.8;

  return (
    <Box 
      onClick={() => navigate(`/cases/${caseData.caseId}`)}
      sx={{ 
        p: 2, 
        bgcolor: '#1e293b', 
        borderRadius: 2, 
        border: `1px solid ${isCritical ? '#ef4444' : '#334155'}`, 
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        '&:hover': { 
          bgcolor: '#334155',
          transform: 'translateX(5px)',
          borderColor: '#3b82f6'
        },
        // CSS Pulse for critical cases
        animation: isCritical ? 'pulse 2s infinite' : 'none',
        "@keyframes pulse": {
          "0%": { boxShadow: "0 0 0 0 rgba(239, 68, 68, 0.4)" },
          "70%": { boxShadow: "0 0 0 10px rgba(239, 68, 68, 0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(239, 68, 68, 0)" }
        },
        animation: 'pulse 1.5s infinite','@keyframes pulse': {
            '0%': { opacity: 1, transform: 'scale(1)' },
            '50%': { opacity: 0.8, transform: 'scale(0.98)', backgroundColor: 'rgba(239, 68, 68, 0.1)' },
            '100%': { opacity: 1, transform: 'scale(1)' },
        }
      }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="body2" fontWeight="bold" sx={{ color: '#f8fafc' }}>
          {caseData.caseId.split('-').pop()} {/* Short ID */}
        </Typography>
        <Chip 
          label={isCritical ? "CRITICAL" : "HIGH"} 
          size="small" 
          sx={{ 
            fontSize: '10px', 
            bgcolor: isCritical ? '#450a0a' : '#451a03', 
            color: isCritical ? '#fca5a5' : '#fdba74',
            fontWeight: 'bold'
          }} 
        />
      </Stack>
      <Typography variant="caption" sx={{ color: '#94a3b8', display: 'block', mt: 1 }}>
        User: {caseData.userId}
      </Typography>
      <Typography variant="body2" sx={{ color: '#3b82f6', fontWeight: 'bold' }}>
        ${caseData.transactionSummary?.amount || '0.00'} {caseData.transactionSummary?.currency || 'USD'}
      </Typography>
    </Box>
  );
}