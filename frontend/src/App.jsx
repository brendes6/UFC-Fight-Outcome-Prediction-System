import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import SportsMmaIcon from '@mui/icons-material/SportsMma';
import Home from './components/Home';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#d32f2f' }, // UFC red
    secondary: { main: '#1976d2' }, // UFC blue
    background: { default: '#181818', paper: '#232323' },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar
        position="static"
        elevation={0}
        sx={{
          background: 'linear-gradient(90deg, #d32f2f 0%, #232323 100%)',
          borderBottom: '4px solid #FFD700',
          boxShadow: '0 2px 12px 0 rgba(0,0,0,0.25)',
        }}
      >
        <Toolbar sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <Typography
            variant="h5"
            component="div"
            sx={{
              fontWeight: 900,
              letterSpacing: 2,
              fontSize: { xs: '1.1rem', sm: '1.5rem' },
              color: 'white',
              textShadow: '1px 1px 8px #000',
            }}
          >
            UFC Fight Outcome Predictor and Betting Value Detector
          </Typography>
        </Toolbar>
      </AppBar>
      <Box
        sx={{
          minHeight: '100vh',
          width: '100vw',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'radial-gradient(circle at 50% 30%, #232323 60%, #181818 100%)',
        }}
      >
        <Box sx={{ width: '100%', maxWidth: 564, px: 2 }}>
          <Home />
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;

