import { useState } from "react";
import { getPredictions } from "./Call";
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

const cachedFights = [
  { f1: "Merab Dvalishvili", f2: "Umar Nurmagomedov" },
  { f1: "Alexandre Pantoja", f2: "Joshua Van" },
  { f1: "Alex Pereira", f2: "Carlos Ulberg" },
  { f1: "Khamzat Chimaev", f2: "Anthony Hernandez" },
];


function Home() {
  const [fighter1Query, setFighter1Query] = useState("");
  const [fighter2Query, setFighter2Query] = useState("");
  const [submittedFighters, setSubmittedFighters] = useState({ f1: "", f2: "" });
  const [fightPrediction, setFightPrediction] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleCachedSearch = (f1, f2) => {
    setFighter1Query(f1);
    setFighter2Query(f2);
  };

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
    <Paper elevation={0} sx={{ p: { xs: 2, sm: 4 }, borderRadius: 4, border: 1, borderColor: 'grey.800', bgcolor: 'background.paper' }}>
      <Typography variant="h5" component="h1" sx={{ textAlign: 'center', mb: 3 }}>
        Predict a Matchup
      </Typography>
      <Typography variant="h6" component="h2" sx={{ textAlign: 'center', mb: 2, fontSize: '1rem' }}>
        Update as of Oct 27, 2025:
      </Typography>
      <Typography variant="h6" component="h2" sx={{ textAlign: 'center', mb: 2, fontSize: '1rem' }}>
        Unfortunately, hosting a PyTorch-based fight prediction model as an API in the cloud is a high expense for a college student. I have stored
        a few cached results for you use to see how the app works. If interested, the GitHub repo for this project
        can be found <a href="https://github.com/brendes6/UFC-Fight-Outcome-Prediction-System"> here. </a>
      </Typography>
      <Stack direction="row" spacing={1} justifyContent="center" sx={{ mb: 3, flexWrap: 'wrap' }}>
        {cachedFights.map((fight, index) => (
          <Button
            key={index}
            variant="outlined"
            size="small"
            onClick={() => handleCachedSearch(fight.f1, fight.f2)}
            sx={{ m: 0.5 }}
          >
            Cached Result #{index + 1}
          </Button>
        ))}
      </Stack>

      <Box component="form" onSubmit={handleSearch}>
        <Stack spacing={2}>
          <TextField
            label="Fighter 1"
            variant="outlined"
            value={fighter1Query}
            onChange={(e) => setFighter1Query(e.target.value)}
            required
            disabled={loading}
          />
          <TextField
            label="Fighter 2"
            variant="outlined"
            value={fighter2Query}
            onChange={(e) => setFighter2Query(e.target.value)}
            required
            disabled={loading}
          />
          <Button
            type="submit"
            variant="contained"
            color="primary"
            size="large"
            sx={{ fontWeight: 'bold', letterSpacing: 1, py: 1.5, mt: 1 }}
            disabled={loading}
          >
            {loading ? <CircularProgress size={26} color="inherit" /> : 'Analyze Fight'}
          </Button>
        </Stack>
      </Box>

      <Box sx={{ mt: 4, minHeight: 200 }}>
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