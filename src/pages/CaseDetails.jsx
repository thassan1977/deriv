import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { getCaseById, resolveCase } from "../api/fraudApi";
import { AISignalsAnalysis } from "../components/AISignalsAnalysis";
import { 
  Container, Typography, Button, Stack, Paper, Grid, Box, Divider, Chip, CircularProgress, List, ListItem, ListItemText, ListItemIcon
} from "@mui/material";
import ShieldIcon from '@mui/icons-material/Shield';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import DevicesIcon from '@mui/icons-material/Devices';
import PsychologyIcon from '@mui/icons-material/Psychology';
import AssignmentTurnedInIcon from '@mui/icons-material/AssignmentTurnedIn';
import LayersIcon from '@mui/icons-material/Layers';


export default function CaseDetails() {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const [fraudCase, setFraudCase] = useState(null);

  useEffect(() => {
    getCaseById(caseId).then(res => setFraudCase(res.data));
  }, [caseId]);

  if (!fraudCase) return (
    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}>
        <CircularProgress color="inherit" />
    </Box>
  );

  const handleDecision = (decision) => {
    resolveCase(caseId, decision, "Resolved via Dashboard").then(() => navigate('/'));
  };

  const getRiskColor = (prob) => prob > 0.7 ? '#ef4444' : prob > 0.4 ? '#f59e0b' : '#10b981';

  return (
    <Box sx={{ bgcolor: '#0f172a', minHeight: '100vh', py: 4, color: '#f8fafc' }}>
      <Container maxWidth="xl">
        
        {/* HEADER */}
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
          <Box>
            <Typography variant="h4" fontWeight="bold">Investigation: {fraudCase.caseId}</Typography>
            <Typography variant="body1" sx={{ color: '#94a3b8' }}>
              System Status: <Chip label={fraudCase.status} size="small" color="warning" sx={{ ml: 1 }} />
            </Typography>
          </Box>
          <Stack direction="row" spacing={2}>
            <Button variant="outlined" sx={{ color: '#ef4444', borderColor: '#ef4444' }} onClick={() => handleDecision("BLOCKED")}>Block Account</Button>
            <Button variant="contained" sx={{ bgcolor: '#3b82f6' }} onClick={() => handleDecision("APPROVED")}>Approve</Button>
          </Stack>
        </Stack>

        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Stack spacing={3}>
              
              {/* 1. AI REASONING & RECOMMENDATIONS */}
              <Paper sx={{ p: 3, bgcolor: '#1e293b', color: 'white', borderRadius: 3, borderLeft: '6px solid #3b82f6' }}>
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5, color: '#3b82f6' }}>
                  <PsychologyIcon /> AI Narrative Analysis
                </Typography>
                <Typography variant="body1" sx={{ mb: 3, lineHeight: 1.7, fontStyle: 'italic' }}>
                  "{fraudCase.aiReasoning || "No automated narrative available."}"
                </Typography>
                
                <Divider sx={{ my: 2, bgcolor: '#334155' }} />
                
                <Typography variant="subtitle1" fontWeight="bold" sx={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <AssignmentTurnedInIcon fontSize="small" /> AI Recommendations
                </Typography>
                <Typography variant="body2" sx={{ color: '#cbd5e1' }}>
                  {fraudCase.aiRecommendations || "Proceed with standard verification protocol."}
                </Typography>
              </Paper>

              {/* 2. DYNAMIC FLAGS (Identity, Network, Behavioral) */}
              <Typography variant="h6">Evidence & Flag Analysis</Typography>
              <Grid container spacing={2}>
                <FlagSection title="Identity" data={fraudCase.identityFlags} icon={<ShieldIcon />} color="#3b82f6" />
                <FlagSection title="Network" data={fraudCase.networkFlags} icon={<LocationOnIcon />} color="#10b981" />
                <FlagSection title="Behavioral" data={fraudCase.behavioralFlags} icon={<PsychologyIcon />} color="#f59e0b" />
                <FlagSection title="Device" data={fraudCase.transactionSummary} icon={<DevicesIcon />} color="#a855f7" />
              </Grid>

              {/* 3. AI SIGNALS CLOUD */}
              <AISignalsAnalysis aiSignals={fraudCase.aiSignals} />
            </Stack>
          </Grid>

          {/* RIGHT COLUMN */}
          <Grid item xs={12} md={4}>
            <Stack spacing={3}>
              
              {/* RISK GAUGE */}
              <Paper sx={{ p: 4, bgcolor: '#1e293b', textAlign: 'center', borderRadius: 3, border: `1px solid ${getRiskColor(fraudCase.fraudProbability)}` }}>
                <Box sx={{ position: 'relative', display: 'inline-flex', mb: 2 }}>
                  <CircularProgress variant="determinate" value={fraudCase.fraudProbability * 100} size={140} thickness={5} sx={{ color: getRiskColor(fraudCase.fraudProbability) }} />
                  <Box sx={{ top: 0, left: 0, bottom: 0, right: 0, position: 'absolute', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Typography variant="h3" fontWeight="bold">{(fraudCase.fraudProbability * 100).toFixed(0)}%</Typography>
                  </Box>
                </Box>
                <Typography variant="h6" sx={{ color: '#94a3b8' }}>Risk Probability</Typography>
              </Paper>

              {/* 4. INVESTIGATION LAYERS TIMELINE */}
              <Paper sx={{ p: 3, bgcolor: '#1e293b', color: 'white', borderRadius: 3 }}>
                <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LayersIcon /> Investigation Path
                </Typography>
                <List dense>
                  {fraudCase.investigationLayers?.map((layer, index) => (
                    <ListItem key={index} sx={{ borderLeft: '2px solid #334155', mb: 1 }}>
                      <ListItemIcon sx={{ minWidth: 35 }}>
                        <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: '#3b82f6' }} />
                      </ListItemIcon>
                      <ListItemText 
                        primary={layer.replace(/_/g, ' ')} 
                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace', color: '#cbd5e1' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </Paper>
            </Stack>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

// Helper component for Flag Sections
function FlagSection({ title, data, icon, color }) {
  if (!data) return null;
  return (
    <Grid item xs={12} sm={6}>
      <Paper sx={{ p: 2, bgcolor: '#1e293b', color: 'white', borderRadius: 2, border: '1px solid #334155' }}>
        <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 1 }}>
          <Box sx={{ color }}>{icon}</Box>
          <Typography variant="subtitle2" sx={{ color: '#94a3b8', textTransform: 'uppercase' }}>{title}</Typography>
        </Stack>
        <Box>
          {Object.entries(data).slice(0, 3).map(([key, val]) => (
            <Typography key={key} variant="body2" sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <span style={{ color: '#64748b' }}>{key}:</span>
              <span style={{ fontWeight: 'bold' }}>{String(val)}</span>
            </Typography>
          ))}
        </Box>
      </Paper>
    </Grid>
  );
}