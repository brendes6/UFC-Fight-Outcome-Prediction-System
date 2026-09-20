import { useEffect, useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Home from './components/Home';
import UpcomingSidebar from './components/UpcomingSidebar';
import PreviousSidebar from './components/PreviousSidebar';

const colors = {
  background: '#1d1a18', paper: '#25201d', text: '#ebe7de', muted: '#b6afa2',
  red: '#c85a4a', blue: '#5f8fa8', gold: '#cda15a', neutral: '#d8d0c3',
  divider: 'rgba(235, 231, 222, 0.15)',
};

const theme = createTheme({
    palette: {
      mode: 'dark',
      primary: { main: colors.red },
      secondary: { main: colors.blue },
      success: { main: '#5e9a62' },
      error: { main: '#c94b43' },
      warning: { main: colors.gold },
      background: { default: colors.background, paper: colors.paper },
      text: { primary: colors.text, secondary: colors.muted },
      divider: colors.divider,
      action: { hover: 'rgba(235, 231, 222, 0.055)' },
    },
    shape: { borderRadius: 6 },
    typography: {
      fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
      h5: { fontSize: '1.5rem', fontWeight: 600, letterSpacing: '-0.025em' },
      h6: { fontSize: '1rem', fontWeight: 600, letterSpacing: '-0.015em' },
      button: { fontWeight: 600, textTransform: 'none', letterSpacing: '0' },
      caption: { letterSpacing: '0.01em' },
    },
    components: {
      MuiPaper: { styleOverrides: { root: { backgroundImage: 'none' } } },
      MuiCard: { styleOverrides: { root: { backgroundImage: 'none', boxShadow: 'none' } } },
      MuiButton: { styleOverrides: { root: { borderRadius: 4, boxShadow: 'none', '&:hover': { boxShadow: 'none' } } } },
      MuiOutlinedInput: { styleOverrides: { root: { borderRadius: 4 } } },
      MuiLinearProgress: { styleOverrides: { root: { borderRadius: 0 }, bar: { borderRadius: 0 } } },
      MuiChip: { styleOverrides: { root: { borderRadius: 3 } } },
    },
  });

function App({ getRoot }) {
  const [fightSelectHandler, setFightSelectHandler] = useState(null);

  useEffect(() => {
    // Warm up the prediction service so the first real request isn't cold.
    getRoot();
  }, [getRoot]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box component="div" className="site-shell">
        <Box component="header" className="site-header">
          <Box className="site-identity">
            <Typography component="p" className="eyebrow">Brendan Desjardins</Typography>
            <Typography
              component="p"
              className="site-title"
              sx={{ fontSize: { xs: '1.3rem', sm: '1.5rem' }, fontWeight: 600, letterSpacing: '-0.03em' }}
            >
              UFC Fight Prediction System
            </Typography>
          </Box>
        </Box>

        <Box component="main" className="app-grid">
          <Box component="aside" className="fight-column previous-column" aria-label="Previous fights">
            <PreviousSidebar onFightSelect={fightSelectHandler} />
          </Box>
          <Box className="analyzer-column">
            <Home onFightSelectRef={setFightSelectHandler} />
          </Box>
          <Box component="aside" className="fight-column upcoming-column" aria-label="Upcoming fights">
            <UpcomingSidebar onFightSelect={fightSelectHandler} />
          </Box>
        </Box>

        <Box component="footer" className="site-footer">
          <Typography component="span" variant="caption">UFC analytics / Brendan Desjardins</Typography>
          <a href="https://brendandesjardins.fyi">Back to portfolio</a>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;
