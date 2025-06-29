import { useState } from "react";
import { getPredictions } from "./Call";
import Prediction from "./Prediction";
import Paper from '@mui/material/Paper';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';

function Home() {
  const [fighter1Query, setFighter1Query] = useState("");
  const [fighter2Query, setFighter2Query] = useState("");
  const [fightPrediction, setFightPrediction] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    setError(null);
    setFightPrediction(null);
    setLoading(true);
    try {
      const result = await getPredictions(fighter1Query, fighter2Query);
      if (!result) throw new Error();
      setFightPrediction(result);
    } catch (err) {
      setError("Something went wrong. Please check the fighter names.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper elevation={6} sx={{ p: 4, borderRadius: 3, bgcolor: 'background.paper' }}>
      <Box component="form" onSubmit={handleSearch} sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        <TextField
          label="Red Fighter"
          variant="outlined"
          color="error"
          value={fighter1Query}
          onChange={(e) => setFighter1Query(e.target.value)}
          required
        />
        <TextField
          label="Blue Fighter"
          variant="outlined"
          color="primary"
          value={fighter2Query}
          onChange={(e) => setFighter2Query(e.target.value)}
          required
        />
        <Button
          type="submit"
          variant="contained"
          color="secondary"
          size="large"
          sx={{ fontWeight: 'bold', letterSpacing: 1 }}
          disabled={loading}
        >
          Predict Fight Outcome
        </Button>
      </Box>

      {loading && (
        <>
        <div>
          If loading takes a while, it means the backend is starting up and you will have predictions shortly.  
        </div>
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress color="secondary" />
        </Box>
        </>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 4, textAlign: 'center' }}>{error}</Alert>
      )}

      {fightPrediction && (
        <Box sx={{ mt: 6 }}>
          <Prediction pred={fightPrediction} />
        </Box>
      )}
    </Paper>
  );
}

export default Home;
