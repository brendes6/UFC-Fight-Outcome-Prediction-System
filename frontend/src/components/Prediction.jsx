import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import LinearProgress from '@mui/material/LinearProgress';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import Divider from '@mui/material/Divider';

function ProbabilityBar({ value, color = 'primary' }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
      <Box sx={{ width: '100%', mr: 1 }}>
        <LinearProgress variant="determinate" value={value * 100} color={color} sx={{ height: 8, borderRadius: 5 }} />
      </Box>
      <Box sx={{ minWidth: 45 }}>
        <Typography variant="body2" color="text.secondary" fontWeight="bold">{`${(value * 100).toFixed(1)}%`}</Typography>
      </Box>
    </Box>
  );
}

function Prediction({ pred, fighter1, fighter2 }) {
  const probs = pred || [0, 0, 0, 0, 0, 0];
  const valuePicks = pred.value_picks || [];

  const fighter1TotalProb = probs.red_ko + probs.red_sub + probs.red_dec;
  const fighter2TotalProb = probs.blue_ko + probs.blue_sub + probs.blue_dec;

  return (
    <Card elevation={0} sx={{ borderRadius: 3, border: 1, borderColor: 'grey.800' }}>
      <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>

          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography variant="h6" fontWeight="bold" noWrap>{fighter1}</Typography>
            <Stack spacing={1.5} sx={{ mt: 2 }}>
              <Typography variant="caption">To win by KO/TKO</Typography>
              <ProbabilityBar value={probs.red_ko} />
              <Typography variant="caption">To win by Submission</Typography>
              <ProbabilityBar value={probs.red_sub} />
              <Typography variant="caption">To win by Decision</Typography>
              <ProbabilityBar value={probs.red_dec} />
            </Stack>
          </Box>

          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h5" fontWeight="900" color="text.secondary">VS</Typography>
            <Box sx={{ my: 1 }}>
              <Typography variant="h6" color="primary.main" fontWeight="bold">{`${(fighter1TotalProb * 100).toFixed(0)}%`}</Typography>
              <Typography variant="h6" color="secondary.main" fontWeight="bold">{`${(fighter2TotalProb * 100).toFixed(0)}%`}</Typography>
            </Box>
          </Box>
          
          <Box sx={{ flex: 1, textAlign: 'right', minWidth: 0 }}>
             <Typography variant="h6" fontWeight="bold" noWrap>{fighter2}</Typography>
             <Stack spacing={1.5} sx={{ mt: 2, alignItems: 'flex-end' }}>
              <Typography variant="caption">To win by KO/TKO</Typography>
              <ProbabilityBar value={probs.blue_ko} color="secondary" />
              <Typography variant="caption">To win by Submission</Typography>
              <ProbabilityBar value={probs.blue_sub} color="secondary" />
              <Typography variant="caption">To win by Decision</Typography>
              <ProbabilityBar value={probs.blue_dec} color="secondary" />

            </Stack>
          </Box>

        </Box>

        {valuePicks.length > 0 && valuePicks[0] !== "No value picks available." && (
          <Box sx={{ mt: 3 }}>
            <Divider sx={{ mb: 2 }} />
            <Typography variant="subtitle1" fontWeight="bold" color="goldenrod" display="flex" alignItems="center" mb={1}>
              <EmojiEventsIcon sx={{ mr: 1 }} /> Value Picks
            </Typography>
            {valuePicks.map((pick, i) => (
              <Typography key={i} variant="body2" sx={{ mb: 0.5 }}>- {pick}</Typography>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

export default Prediction;