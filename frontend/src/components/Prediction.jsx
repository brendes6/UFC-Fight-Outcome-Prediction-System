import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import Box from '@mui/material/Box';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import SportsMmaIcon from '@mui/icons-material/SportsMma';

function Prediction({ pred }) {
  const probs = pred.predicted_probs || {};
  const valuePicks = pred.value_picks || [];

  const formatPercent = (value) => (value * 100).toFixed(1) + "%";

  return (
    <Card elevation={4} sx={{ borderRadius: 3, bgcolor: 'background.paper' }}>
      <CardContent>
        <Typography variant="h5" align="center" fontWeight="bold" gutterBottom>
          <SportsMmaIcon sx={{ mr: 1, color: 'primary.main' }} /> Fight Prediction
        </Typography>
        <Grid container spacing={3} sx={{ mb: 2 }}>
          <Grid item xs={12} sm={6}>
            <Box sx={{ bgcolor: 'error.light', p: 2, borderRadius: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold" color="black" display="flex" alignItems="center">
                <span style={{ fontSize: 22, marginRight: 0 }}></span> Red Fighter
              </Typography>
              <Typography sx={{ mt: 1 }}>
                Win Probability: <strong>{formatPercent(probs["Red to Win"] ?? 0)}</strong>
              </Typography>
              <ul style={{ margin: '8px 0 0 18px', fontSize: 14 }}>
                <li>KO/TKO: {formatPercent(probs["Red by KO"] ?? 0)}</li>
                <li>Submission: {formatPercent(probs["Red by Sub"] ?? 0)}</li>
                <li>Decision: {formatPercent(probs["Red by Dec"] ?? 0)}</li>
              </ul>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Box sx={{ bgcolor: 'primary.light', p: 2, borderRadius: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold" color="black" display="flex" alignItems="center">
                <span style={{ fontSize: 22, marginRight: 0 }}></span> Blue Fighter
              </Typography>
              <Typography sx={{ mt: 1 }}>
                Win Probability: <strong>{formatPercent(probs["Blue to Win"] ?? 0)}</strong>
              </Typography>
              <ul style={{ margin: '8px 0 0 18px', fontSize: 14 }}>
                <li>KO/TKO: {formatPercent(probs["Blue by KO"] ?? 0)}</li>
                <li>Submission: {formatPercent(probs["Blue by Sub"] ?? 0)}</li>
                <li>Decision: {formatPercent(probs["Blue by Dec"] ?? 0)}</li>
              </ul>
            </Box>
          </Grid>
        </Grid>
        <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 2 }}>
          <Typography variant="subtitle2" fontWeight="bold" color="black" display="flex" alignItems="center" mb={1}>
            <EmojiEventsIcon sx={{ mr: 1, color: 'goldenrod' }} /> Value Picks:
          </Typography>
          {valuePicks.length === 0 || valuePicks[0] === "No value picks available." ? (
            <Typography color="black">No value picks found for this matchup - Try an upcoming fight for value picks!</Typography>
          ) : (
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 14 }}>
              {valuePicks.map((pick, i) => (
                <Typography color="black">{pick}<br/><br/></Typography>
              ))}
            </ul>
          )}
        </Box>
      </CardContent>
    </Card>
  );
}

export default Prediction;
