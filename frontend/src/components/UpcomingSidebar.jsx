import { useState, useEffect } from "react";
import { getUpcoming } from "./Call";
import Paper from '@mui/material/Paper';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Divider from '@mui/material/Divider';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Alert from '@mui/material/Alert';
import LinearProgress from '@mui/material/LinearProgress';
import EventIcon from '@mui/icons-material/Event';

function UpcomingSidebar({ onFightSelect }) {
  const [upcomingFights, setUpcomingFights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchUpcoming = async () => {
      setLoading(true);
      setError(null);
      try {
        const fights = await getUpcoming();
        // Sort by fight_number (ascending order)
        const sortedFights = [...fights].sort((a, b) => {
          const aNum = a.fight_number || 999;
          const bNum = b.fight_number || 999;
          return aNum - bNum;
        });
        setUpcomingFights(sortedFights);
      } catch (err) {
        setError(err.message || "Failed to load upcoming fights");
      } finally {
        setLoading(false);
      }
    };

    fetchUpcoming();
  }, []);

  const getTotalWinProb = (fight) => {
    const redTotal = (fight.red_ko || 0) + (fight.red_sub || 0) + (fight.red_dec || 0);
    const blueTotal = (fight.blue_ko || 0) + (fight.blue_sub || 0) + (fight.blue_dec || 0);
    return { redTotal, blueTotal };
  };

  const handleFightClick = (fight) => {
    if (onFightSelect) {
      onFightSelect(fight.red_fighter, fight.blue_fighter);
    }
  };

  const CompactProbabilityBar = ({ value, color = 'primary' }) => {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.2 }}>
        <Box sx={{ flex: 1 }}>
          <LinearProgress 
            variant="determinate" 
            value={value * 100} 
            color={color} 
            sx={{ height: 2.5, borderRadius: 1.25 }} 
          />
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ minWidth: 28, fontSize: '0.55rem' }}>
          {`${(value * 100).toFixed(0)}%`}
        </Typography>
      </Box>
    );
  };

  return (
    <Paper 
      elevation={0} 
      sx={{ 
        p: 1, 
        borderRadius: 3, 
        border: 1, 
        borderColor: 'grey.800', 
        bgcolor: 'background.paper',
        height: 'fit-content',
        maxHeight: 'calc(100vh - 120px)',
        overflow: 'auto'
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <EventIcon sx={{ color: 'primary.main', mr: 0.75, fontSize: 18 }} />
        <Typography variant="h6" fontWeight="bold" sx={{ fontSize: '0.9rem' }}>
          Upcoming Fights
        </Typography>
      </Box>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress size={32} />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
      )}

      {!loading && !error && upcomingFights.length === 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
          No upcoming fights available
        </Typography>
      )}

      {!loading && !error && upcomingFights.length > 0 && (
        <Stack spacing={1.25}>
          {upcomingFights.map((fight, index) => {
            const { redTotal, blueTotal } = getTotalWinProb(fight);
            const redFighter = fight.red_fighter || "TBD";
            const blueFighter = fight.blue_fighter || "TBD";
            const redKo = fight.red_ko || 0;
            const redSub = fight.red_sub || 0;
            const redDec = fight.red_dec || 0;
            const blueKo = fight.blue_ko || 0;
            const blueSub = fight.blue_sub || 0;
            const blueDec = fight.blue_dec || 0;
            
            return (
              <Card
                key={index}
                elevation={0}
                sx={{
                  borderRadius: 1.5,
                  border: 1,
                  borderColor: 'grey.800',
                  cursor: onFightSelect ? 'pointer' : 'default',
                  '&:hover': onFightSelect ? {
                    borderColor: 'primary.main',
                    bgcolor: 'action.hover'
                  } : {},
                  transition: 'all 0.2s'
                }}
                onClick={() => handleFightClick(fight)}
              >
                <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
                  <Stack spacing={0.75}>
                    {/* Red Fighter */}
                    <Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.15 }}>
                        <Typography variant="body2" fontWeight="bold" noWrap sx={{ flex: 1, mr: 0.75, fontSize: '0.75rem' }}>
                          {redFighter}
                        </Typography>
                        <Chip 
                          label={`${(redTotal * 100).toFixed(0)}%`}
                          size="small"
                          color="primary"
                          sx={{ height: 16, fontSize: '0.6rem', fontWeight: 'bold', px: 0.4 }}
                        />
                      </Box>
                      <Stack spacing={0.05} sx={{ mt: 0.4 }}>
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem', lineHeight: 1.2 }}>
                            KO/TKO
                          </Typography>
                          <CompactProbabilityBar value={redKo} color="primary" />
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem', lineHeight: 1.2 }}>
                            Sub
                          </Typography>
                          <CompactProbabilityBar value={redSub} color="primary" />
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem', lineHeight: 1.2 }}>
                            Dec
                          </Typography>
                          <CompactProbabilityBar value={redDec} color="primary" />
                        </Box>
                      </Stack>
                    </Box>
                    
                    <Divider sx={{ my: 0.15 }} />
                    
                    {/* Blue Fighter */}
                    <Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.15 }}>
                        <Typography variant="body2" fontWeight="bold" noWrap sx={{ flex: 1, mr: 0.75, fontSize: '0.75rem' }}>
                          {blueFighter}
                        </Typography>
                        <Chip 
                          label={`${(blueTotal * 100).toFixed(0)}%`}
                          size="small"
                          color="secondary"
                          sx={{ height: 16, fontSize: '0.6rem', fontWeight: 'bold', px: 0.4 }}
                        />
                      </Box>
                      <Stack spacing={0.05} sx={{ mt: 0.4 }}>
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem', lineHeight: 1.2 }}>
                            KO/TKO
                          </Typography>
                          <CompactProbabilityBar value={blueKo} color="secondary" />
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem', lineHeight: 1.2 }}>
                            Sub
                          </Typography>
                          <CompactProbabilityBar value={blueSub} color="secondary" />
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem', lineHeight: 1.2 }}>
                            Dec
                          </Typography>
                          <CompactProbabilityBar value={blueDec} color="secondary" />
                        </Box>
                      </Stack>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            );
          })}
        </Stack>
      )}
    </Paper>
  );
}

export default UpcomingSidebar;
