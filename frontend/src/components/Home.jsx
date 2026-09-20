import { useState, useEffect } from "react";
import { getPredictions } from "../api/client";
import Prediction from "./Prediction";
import Paper from '@mui/material/Paper';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import Collapse from '@mui/material/Collapse';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

function Home({ onFightSelectRef }) {
  const [fighter1Query, setFighter1Query] = useState("");
  const [fighter2Query, setFighter2Query] = useState("");
  const [submittedFighters, setSubmittedFighters] = useState({ f1: "", f2: "" });
  const [fightPrediction, setFightPrediction] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFightSelect = (f1, f2) => {
    setFighter1Query(f1);
    setFighter2Query(f2);
  };

  useEffect(() => {
    if (onFightSelectRef) {
      // Store the callback itself. Passing it directly makes React treat it as
      // a state updater and invokes it with the previous state value.
      onFightSelectRef(() => handleFightSelect);
    }
  }, [onFightSelectRef]);

  const handleSearch = async (e) => {
    e.preventDefault();
    setError(null);
    setFightPrediction(null);
    setLoading(true);
    try {
      const result = await getPredictions(fighter1Query, fighter2Query);
      if (!result) throw new Error("Prediction request failed.");
      setFightPrediction(result);
      setSubmittedFighters({ f1: fighter1Query, f2: fighter2Query });
    } catch (err) {
      setError(err.message || "Something went wrong. Please check the fighter names.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper elevation={0} sx={{ p: { xs: 2, sm: 3 }, borderRadius: 1, border: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
      <Typography component="p" variant="caption" sx={{ color: 'text.secondary', fontFamily: 'monospace', letterSpacing: '.08em', textTransform: 'uppercase', mb: .75 }}>
        Matchup analyzer
      </Typography>
      <Typography variant="h5" component="h1" sx={{ mb: .75 }}>
        Predict a Matchup
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3, maxWidth: '40ch' }}>
        Compare the red and blue corners using the current prediction model.
      </Typography>
      <Box component="form" onSubmit={handleSearch}>
        <Box className="matchup-fields">
          <TextField
            label="Red corner"
            variant="outlined"
            value={fighter1Query}
            onChange={(e) => setFighter1Query(e.target.value)}
            required
            disabled={loading}
            fullWidth
            sx={{ '& .MuiInputLabel-root.Mui-focused': { color: 'primary.main' } }}
          />
          <Typography aria-hidden="true" className="matchup-versus">VS</Typography>
          <TextField
            label="Blue corner"
            color="secondary"
            variant="outlined"
            value={fighter2Query}
            onChange={(e) => setFighter2Query(e.target.value)}
            required
            disabled={loading}
            fullWidth
            sx={{ '& .MuiInputLabel-root.Mui-focused': { color: 'secondary.main' } }}
          />
        </Box>
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 5 }}>
          <Button
            type="submit"
            variant="contained"
            size="large"
            sx={{ bgcolor: '#d8d0c3', color: '#1d1a18', py: 1.1, '&:hover': { bgcolor: '#eee8dd' } }}
            disabled={loading}
          >
            {loading ? <CircularProgress size={26} color="inherit" /> : 'Predict Fight'}
          </Button>
        </Box>
      </Box>

      <Box sx={{ mt: 3 }}>
        <Collapse in={!!error}>
          <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
        </Collapse>
        
        <Collapse in={!!fightPrediction}>
          {fightPrediction && (
            <Prediction 
              pred={fightPrediction} 
              fighter1={submittedFighters.f1} 
              fighter2={submittedFighters.f2} 
            />
          )}
        </Collapse>
      </Box>
    </Paper>
  );
}

export default Home;
