import { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import QueryStatsIcon from '@mui/icons-material/QueryStats';
import Home from './components/Home';
import UpcomingSidebar from './components/UpcomingSidebar';
import PreviousSidebar from './components/PreviousSidebar';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#00AEEF' },
    secondary: { main: '#90CAF9' },
    background: { default: '#121212', paper: '#1E1E1E' },
    text: { primary: '#E0E0E0', secondary: '#BDBDBD' },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h5: { fontWeight: 700 },
    h6: { fontWeight: 600 },
  },
});

function App() {
  const [fightSelectHandler, setFightSelectHandler] = useState(null);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <AppBar position="static" color="transparent" elevation={0} sx={{ borderBottom: 1, borderColor: 'grey.800' }}>
          <Toolbar>
            <QueryStatsIcon sx={{ color: 'primary.main', fontSize: 30, mr: 1.5 }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 700 }}>
              UFC Fight Prediction System
            </Typography>
          </Toolbar>
        </AppBar>
        
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            display: 'flex', 
            p: 3,
            gap: 2,
            maxWidth: '1600px',
            margin: '0 auto',
            width: '100%',
          }}
        >
          <Box sx={{ width: 300, flexShrink: 0, display: { xs: 'none', lg: 'block' } }}>
            <PreviousSidebar onFightSelect={fightSelectHandler} />
          </Box>
          <Box sx={{ flex: 1, maxWidth: 600 }}>
            <Home onFightSelectRef={setFightSelectHandler} />
          </Box>
          <Box sx={{ width: 300, flexShrink: 0, display: { xs: 'none', lg: 'block' } }}>
            <UpcomingSidebar onFightSelect={fightSelectHandler} />
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;