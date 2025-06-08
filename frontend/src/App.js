import React, { useState } from 'react';
import { 
  Container, 
  TextField, 
  Button, 
  Typography, 
  Box, 
  Paper,
  Grid,
  CircularProgress,
  Alert
} from '@mui/material';
import axios from 'axios';

function App() {
  const [fighter1, setFighter1] = useState('');
  const [fighter2, setFighter2] = useState('');
  const [predictions, setPredictions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [displayFighter1, setDisplayFighter1] = useState('');
  const [displayFighter2, setDisplayFighter2] = useState('');

  const handlePredict = async () => {
    if (!fighter1 || !fighter2) {
      setError('Please enter both fighters\' names');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await axios.get(`http://127.0.0.1:8000/predict?fighter1=${encodeURIComponent(fighter1)}&fighter2=${encodeURIComponent(fighter2)}`);
      if (response.data && response.data.predicted_probs) {
        setPredictions(response.data);
        setDisplayFighter1(fighter1);
        setDisplayFighter2(fighter2);
      } else {
        setError('Invalid response from server');
      }
    } catch (err) {
      console.error('Error details:', err);
      if (err.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        setError(err.response.data.detail || 'Server error occurred');
      } else if (err.request) {
        // The request was made but no response was received
        setError('No response from server. Please make sure the backend is running.');
      } else {
        // Something happened in setting up the request that triggered an Error
        setError('Error setting up the request');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom align="center">
          UFC Fight Predictor
        </Typography>
        
        <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={5}>
              <TextField
                fullWidth
                label="Fighter 1 (Red Corner)"
                value={fighter1}
                onChange={(e) => setFighter1(e.target.value)}
                variant="outlined"
              />
            </Grid>
            <Grid item xs={12} sm={5}>
              <TextField
                fullWidth
                label="Fighter 2 (Blue Corner)"
                value={fighter2}
                onChange={(e) => setFighter2(e.target.value)}
                variant="outlined"
              />
            </Grid>
            <Grid item xs={12} sm={2}>
              <Button
                fullWidth
                variant="contained"
                onClick={handlePredict}
                disabled={loading}
                sx={{ height: '100%' }}
              >
                Predict
              </Button>
            </Grid>
          </Grid>
        </Paper>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {loading && (
          <Box display="flex" justifyContent="center" my={4}>
            <CircularProgress />
          </Box>
        )}

        {predictions && !loading && (
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Predictions
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Win Probabilities
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography>
                    {displayFighter1}: {(predictions.predicted_probs['Red to Win'] * 100).toFixed(1)}%
                  </Typography>
                  <Typography>
                    {displayFighter2}: {(predictions.predicted_probs['Blue to Win'] * 100).toFixed(1)}%
                  </Typography>
                </Box>

                <Typography variant="h6" gutterBottom>
                  Method of Victory
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography>
                    {displayFighter1} by KO: {(predictions.predicted_probs['Red by KO'] * 100).toFixed(1)}%
                  </Typography>
                  <Typography>
                    {displayFighter1} by Submission: {(predictions.predicted_probs['Red by Sub'] * 100).toFixed(1)}%
                  </Typography>
                  <Typography>
                    {displayFighter1} by Decision: {(predictions.predicted_probs['Red by Dec'] * 100).toFixed(1)}%
                  </Typography>
                  <Typography>
                    {displayFighter2} by KO: {(predictions.predicted_probs['Blue by KO'] * 100).toFixed(1)}%
                  </Typography>
                  <Typography>
                    {displayFighter2} by Submission: {(predictions.predicted_probs['Blue by Sub'] * 100).toFixed(1)}%
                  </Typography>
                  <Typography>
                    {displayFighter2} by Decision: {(predictions.predicted_probs['Blue by Dec'] * 100).toFixed(1)}%
                  </Typography>
                </Box>
              </Grid>

              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Value Picks
                </Typography>
                {predictions.value_picks.map((pick, index) => (
                  <Typography key={index} sx={{ mb: 1 }}>
                    {pick}
                  </Typography>
                ))}
              </Grid>
            </Grid>
          </Paper>
        )}
      </Box>
    </Container>
  );
}

export default App;
