import { 
  Box, Typography, Paper, Grid, Divider, Chip, LinearProgress, Stack 
} from "@mui/material";
import HubIcon from '@mui/icons-material/Hub';
import InsightsIcon from '@mui/icons-material/Insights';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import VerifiedIcon from '@mui/icons-material/Verified';

export function AISignalsAnalysis({ aiSignals }) {
  if (!aiSignals) return null;

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h6" sx={{ mb: 2, color: '#f8fafc' }}>Technical AI Layer Analysis</Typography>
      <Grid container spacing={3}>
        
        {/* LAYER 1 & 2: THE ENGINE */}
        <Grid item xs={12} md={6}>
          <SignalCard title="L1: Feature Extraction" icon={<InsightsIcon />}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
              {Object.entries(aiSignals.feature_extraction?.key_features || {}).map(([k, v]) => (
                <Chip key={k} label={`${k}: ${v?.toFixed(2) || v}`} size="small" variant="outlined" sx={{ color: '#94a3b8' }} />
              ))}
            </Box>
          </SignalCard>

          <SignalCard title="L2: ML Ensemble Analysis" icon={<HubIcon />}>
            <ScoreBar 
              label="ML Confidence Score" 
              value={aiSignals.ml_analysis?.score * 100} 
              color={aiSignals.ml_analysis?.decision === 'BLOCKED' ? 'error' : 'success'} 
            />
            <Typography variant="caption" sx={{ color: '#64748b', mt: 1, display: 'block' }}>
              Top Factors: {aiSignals.ml_analysis?.feature_importance?.join(", ")}
            </Typography>
          </SignalCard>
        </Grid>

        {/* LAYER 3 & 4: THE DEEP SCAN */}
        <Grid item xs={12} md={6}>
          {aiSignals.graph_analysis?.executed ? (
            <SignalCard title="L3: Graph Ring Detection" icon={<HubIcon color="warning" />}>
              <ScoreBar label="Ring Probability" value={aiSignals.graph_analysis.ring_probability * 100} color="warning" />
              <Typography variant="body2" sx={{ mt: 1 }}>
                Connected Entities: <strong>{aiSignals.graph_analysis.connected_users_count}</strong>
              </Typography>
            </SignalCard>
          ) : <InactiveLayer title="L3: Graph Analysis" />}

          {aiSignals.anomaly_detection?.executed ? (
            <SignalCard title="L4: Anomaly Detection" icon={<WarningAmberIcon color="error" />}>
              <ScoreBar label="Behavioral Deviation" value={aiSignals.anomaly_detection.anomaly_score * 100} color="error" />
              <Box sx={{ mt: 1 }}>
                {aiSignals.anomaly_detection.detected_patterns?.map(p => (
                  <Chip key={p} label={p} size="small" color="error" sx={{ mr: 0.5, mt: 0.5 }} />
                ))}
              </Box>
            </SignalCard>
          ) : <InactiveLayer title="L4: Anomaly Detection" />}
        </Grid>

        {/* LAYER 5: LLM REASONING FINAL VERDICT */}
        {aiSignals.llm_reasoning?.executed && (
            <Grid item xs={12}>
                <Paper sx={{ p: 2, bgcolor: '#0f172a', border: '1px solid #3b82f6', borderRadius: 2 }}>
                    <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                        <VerifiedIcon sx={{ color: '#3b82f6' }} />
                        <Typography variant="subtitle1" fontWeight="bold">L5: LLM Reasoning Finalized Decision</Typography>
                    </Stack>
                    <Typography variant="body2" sx={{ color: '#cbd5e1', fontStyle: 'italic' }}>
                        {aiSignals.llm_reasoning.recommendation}
                    </Typography>
                </Paper>
            </Grid>
        )}
      </Grid>
    </Box>
  );
}

// Sub-components for cleaner code
function SignalCard({ title, icon, children }) {
  return (
    <Paper sx={{ p: 2, mb: 2, bgcolor: '#1e293b', color: 'white', borderRadius: 2 }}>
      <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1.5 }}>
        <Box sx={{ color: '#3b82f6' }}>{icon}</Box>
        <Typography variant="subtitle2" sx={{ textTransform: 'uppercase', letterSpacing: 1 }}>{title}</Typography>
      </Stack>
      {children}
    </Paper>
  );
}

function ScoreBar({ label, value, color }) {
  return (
    <Box sx={{ mb: 1 }}>
      <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.5 }}>
        <Typography variant="caption" sx={{ color: '#94a3b8' }}>{label}</Typography>
        <Typography variant="caption" fontWeight="bold">{value.toFixed(1)}%</Typography>
      </Stack>
      <LinearProgress variant="determinate" value={value} color={color} sx={{ height: 6, borderRadius: 3, bgcolor: '#334155' }} />
    </Box>
  );
}

function InactiveLayer({ title }) {
  return (
    <Paper sx={{ p: 2, mb: 2, bgcolor: '#0f172a', color: '#475569', borderRadius: 2, border: '1px dashed #334155', display: 'flex', justifyContent: 'space-between' }}>
      <Typography variant="subtitle2">{title}</Typography>
      <Typography variant="caption">BYPASSED (Low Risk)</Typography>
    </Paper>
  );
}