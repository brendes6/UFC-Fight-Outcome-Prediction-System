import { useState, useEffect } from "react";
import { getUpcoming } from "./Call";
import Paper from '@mui/material/Paper';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Alert from '@mui/material/Alert';
import LinearProgress from '@mui/material/LinearProgress';
import Collapse from '@mui/material/Collapse';
import Divider from '@mui/material/Divider';
import EventIcon from '@mui/icons-material/Event';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

function UpcomingSidebar({ onFightSelect }) {
  const [upcomingFights, setUpcomingFights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedIndex, setExpandedIndex] = useState(null);

  useEffect(() => {
    const fetchUpcoming = async () => {
      setLoading(true);
      setError(null);
      try {
        const fights = await getUpcoming();
        const sortedFights = [...fights].sort((a, b) => {
          return (a.fight_number || 999) - (b.fight_number || 999);
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

  const handleCardClick = (e, index) => {
    e.stopPropagation();
    setExpandedIndex(expandedIndex === index ? null : index);
  };

  const handleFightSelect = (e, fight) => {
    e.stopPropagation();
    if (onFightSelect) onFightSelect(fight.red_fighter, fight.blue_fighter);
  };

  const ProbBar = ({ value, color = 'primary' }) => (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.3 }}>
      <Box sx={{ flex: 1 }}>
        <LinearProgress variant="determinate" value={value * 100} color={color}
          sx={{ height: 3, borderRadius: 1.5 }} />
      </Box>
      <Typography variant="caption" sx={{ minWidth: 28, fontSize: '0.55rem', color: 'text.secondary' }}>
        {`${(value * 100).toFixed(0)}%`}
      </Typography>
    </Box>
  );

  const hasEvData = (f) => f.best_bet != null && f.best_bet_ev != null && f.best_bet_ev > 0;
  const hasOddsData = (f) => f.red_prob != null && f.blue_prob != null;
  const getBestBetName = (f) => f.best_bet === 'Red' ? f.red_fighter : f.best_bet === 'Blue' ? f.blue_fighter : null;

  const evBetCount = upcomingFights.filter(hasEvData).length;

  return (
    <Paper elevation={0} sx={{ p: 1, borderRadius: 3, border: 1, borderColor: 'grey.800', bgcolor: 'background.paper', height: 'fit-content', maxHeight: 'calc(100vh - 120px)', overflow: 'auto' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <EventIcon sx={{ color: 'primary.main', mr: 0.75, fontSize: 18 }} />
        <Typography variant="h6" fontWeight="bold" sx={{ fontSize: '0.9rem', flex: 1 }}>Upcoming Fights</Typography>
        {!loading && evBetCount > 0 && (
          <Chip icon={<TrendingUpIcon sx={{ fontSize: 12 }} />} label={`${evBetCount} EV`} size="small"
            sx={{ height: 18, fontSize: '0.55rem', fontWeight: 'bold', bgcolor: 'rgba(255,183,77,0.15)', color: '#ffb74d', border: '1px solid rgba(255,183,77,0.3)', '& .MuiChip-icon': { color: '#ffb74d' } }} />
        )}
      </Box>

      {loading && <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}><CircularProgress size={32} /></Box>}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {!loading && !error && upcomingFights.length === 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>No upcoming fights available</Typography>
      )}

      {!loading && !error && upcomingFights.length > 0 && (
        <Stack spacing={0.75}>
          {upcomingFights.map((fight, index) => {
            const { redTotal, blueTotal } = getTotalWinProb(fight);
            const redFighter = fight.red_fighter || "TBD";
            const blueFighter = fight.blue_fighter || "TBD";
            const fightHasEv = hasEvData(fight);
            const fightHasOdds = hasOddsData(fight);
            const redPct = Math.round(redTotal * 100);
            const bluePct = Math.round(blueTotal * 100);
            const isExpanded = expandedIndex === index;

            return (
              <Card key={index} elevation={0}
                sx={{
                  borderRadius: 1.5, border: 1,
                  borderColor: fightHasEv ? 'rgba(255,183,77,0.5)' : 'grey.800',
                  borderWidth: fightHasEv ? 1.5 : 1,
                  cursor: 'pointer',
                  '&:hover': { borderColor: fightHasEv ? '#ffb74d' : 'primary.main', bgcolor: 'action.hover' },
                  transition: 'all 0.2s',
                  ...(fightHasEv && { boxShadow: '0 0 8px rgba(255,183,77,0.1)' }),
                }}
                onClick={(e) => handleCardClick(e, index)}
              >
                <CardContent sx={{ p: 0.75, '&:last-child': { pb: 0.75 } }}>
                  <Stack spacing={0.4}>
                    {/* Fighter names */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" fontWeight="bold" noWrap
                        sx={{ flex: 1, fontSize: '0.7rem', color: redTotal > blueTotal ? 'primary.main' : 'text.primary' }}>
                        {redFighter}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', mx: 0.3 }}>
                        <Typography variant="caption" sx={{ fontSize: '0.55rem', color: 'text.secondary' }}>vs</Typography>
                        {isExpanded
                          ? <ExpandLessIcon sx={{ fontSize: 12, color: 'text.secondary', ml: 0.1 }} />
                          : <ExpandMoreIcon sx={{ fontSize: 12, color: 'text.secondary', ml: 0.1 }} />
                        }
                      </Box>
                      <Typography variant="body2" fontWeight="bold" noWrap
                        sx={{ flex: 1, fontSize: '0.7rem', textAlign: 'right', color: blueTotal > redTotal ? 'secondary.main' : 'text.primary' }}>
                        {blueFighter}
                      </Typography>
                    </Box>

                    {/* Head-to-head bar */}
                    <Box>
                      <Box sx={{ display: 'flex', height: 6, borderRadius: 3, overflow: 'hidden' }}>
                        <Box sx={{ width: `${redPct}%`, bgcolor: 'primary.main', borderRadius: '3px 0 0 3px' }} />
                        <Box sx={{ width: `${bluePct}%`, bgcolor: 'secondary.main', borderRadius: '0 3px 3px 0' }} />
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.15 }}>
                        <Typography variant="caption" sx={{ fontSize: '0.5rem', color: 'primary.main', fontWeight: 600 }}>{redPct}%</Typography>
                        <Typography variant="caption" sx={{ fontSize: '0.5rem', color: 'secondary.main', fontWeight: 600 }}>{bluePct}%</Typography>
                      </Box>
                    </Box>

                    {/* Method breakdown chips */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 0.5 }}>
                      <Box sx={{ display: 'flex', gap: 0.3 }}>
                        {[
                          { label: 'KO', val: Math.round((fight.red_ko||0)*100) },
                          { label: 'Sub', val: Math.round((fight.red_sub||0)*100) },
                          { label: 'Dec', val: Math.round((fight.red_dec||0)*100) },
                        ].map(m => (
                          <Box key={m.label} sx={{
                            px: 0.4, py: 0.05, borderRadius: 0.5,
                            bgcolor: 'rgba(0,174,239,0.12)', border: '1px solid rgba(0,174,239,0.25)',
                            display: 'flex', alignItems: 'center', gap: 0.2,
                          }}>
                            <Typography variant="caption" sx={{ fontSize: '0.45rem', color: 'rgba(0,174,239,0.7)', fontWeight: 600 }}>{m.label}</Typography>
                            <Typography variant="caption" sx={{ fontSize: '0.5rem', color: 'primary.main', fontWeight: 700 }}>{m.val}</Typography>
                          </Box>
                        ))}
                      </Box>
                      <Box sx={{ display: 'flex', gap: 0.3 }}>
                        {[
                          { label: 'KO', val: Math.round((fight.blue_ko||0)*100) },
                          { label: 'Sub', val: Math.round((fight.blue_sub||0)*100) },
                          { label: 'Dec', val: Math.round((fight.blue_dec||0)*100) },
                        ].map(m => (
                          <Box key={m.label} sx={{
                            px: 0.4, py: 0.05, borderRadius: 0.5,
                            bgcolor: 'rgba(144,202,249,0.1)', border: '1px solid rgba(144,202,249,0.2)',
                            display: 'flex', alignItems: 'center', gap: 0.2,
                          }}>
                            <Typography variant="caption" sx={{ fontSize: '0.45rem', color: 'rgba(144,202,249,0.6)', fontWeight: 600 }}>{m.label}</Typography>
                            <Typography variant="caption" sx={{ fontSize: '0.5rem', color: 'secondary.main', fontWeight: 700 }}>{m.val}</Typography>
                          </Box>
                        ))}
                      </Box>
                    </Box>

                    {/* Model vs Market compact */}
                    {fightHasOdds && (
                      <Box sx={{ p: 0.4, borderRadius: 0.75, bgcolor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="caption" sx={{ fontSize: '0.45rem', color: 'text.secondary' }}>Model / Market</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="caption" sx={{ fontSize: '0.55rem' }}>
                            <Box component="span" sx={{ color: 'primary.main', fontWeight: 700 }}>{Math.round((fight.red_win||redTotal)*100)}%</Box>
                            <Box component="span" sx={{ color: 'text.secondary' }}> / {Math.round(fight.red_prob*100)}%</Box>
                          </Typography>
                          <Typography variant="caption" sx={{ fontSize: '0.55rem' }}>
                            <Box component="span" sx={{ color: 'text.secondary' }}>{Math.round(fight.blue_prob*100)}% / </Box>
                            <Box component="span" sx={{ color: 'secondary.main', fontWeight: 700 }}>{Math.round((fight.blue_win||blueTotal)*100)}%</Box>
                          </Typography>
                        </Box>
                      </Box>
                    )}

                    {/* EV Badge */}
                    {fightHasEv && (
                      <Box sx={{ p: 0.4, borderRadius: 0.75, background: 'linear-gradient(135deg, rgba(255,183,77,0.12) 0%, rgba(255,143,0,0.08) 100%)', border: '1px solid rgba(255,183,77,0.25)', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <TrendingUpIcon sx={{ fontSize: 11, color: '#ffb74d' }} />
                        <Typography variant="caption" noWrap sx={{ fontSize: '0.55rem', fontWeight: 700, color: '#ffb74d', flex: 1 }}>
                          {getBestBetName(fight)}
                        </Typography>
                        <Chip label={`+${(fight.best_bet_ev*100).toFixed(1)}% EV`} size="small"
                          sx={{ height: 15, fontSize: '0.5rem', fontWeight: 'bold', bgcolor: 'rgba(255,183,77,0.2)', color: '#ffb74d', border: '1px solid rgba(255,183,77,0.4)' }} />
                      </Box>
                    )}

                    {/* Expandable detailed breakdown */}
                    <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                      <Box sx={{ mt: 0.5 }}>
                        <Divider sx={{ mb: 0.75 }} />

                        {/* Red Fighter breakdown */}
                        <Box sx={{ mb: 0.75 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.25 }}>
                            <Typography variant="body2" fontWeight="bold" noWrap sx={{ fontSize: '0.65rem' }}>{redFighter}</Typography>
                            <Chip label={`${redPct}%`} size="small" color="primary" sx={{ height: 15, fontSize: '0.55rem', fontWeight: 'bold' }} />
                          </Box>
                          <Stack spacing={0.2}>
                            <Box>
                              <Typography variant="caption" sx={{ fontSize: '0.5rem', color: 'text.secondary' }}>KO/TKO</Typography>
                              <ProbBar value={fight.red_ko || 0} color="primary" />
                            </Box>
                            <Box>
                              <Typography variant="caption" sx={{ fontSize: '0.5rem', color: 'text.secondary' }}>Sub</Typography>
                              <ProbBar value={fight.red_sub || 0} color="primary" />
                            </Box>
                            <Box>
                              <Typography variant="caption" sx={{ fontSize: '0.5rem', color: 'text.secondary' }}>Dec</Typography>
                              <ProbBar value={fight.red_dec || 0} color="primary" />
                            </Box>
                          </Stack>
                        </Box>

                        <Divider sx={{ my: 0.5 }} />

                        {/* Blue Fighter breakdown */}
                        <Box>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.25 }}>
                            <Typography variant="body2" fontWeight="bold" noWrap sx={{ fontSize: '0.65rem' }}>{blueFighter}</Typography>
                            <Chip label={`${bluePct}%`} size="small" color="secondary" sx={{ height: 15, fontSize: '0.55rem', fontWeight: 'bold' }} />
                          </Box>
                          <Stack spacing={0.2}>
                            <Box>
                              <Typography variant="caption" sx={{ fontSize: '0.5rem', color: 'text.secondary' }}>KO/TKO</Typography>
                              <ProbBar value={fight.blue_ko || 0} color="secondary" />
                            </Box>
                            <Box>
                              <Typography variant="caption" sx={{ fontSize: '0.5rem', color: 'text.secondary' }}>Sub</Typography>
                              <ProbBar value={fight.blue_sub || 0} color="secondary" />
                            </Box>
                            <Box>
                              <Typography variant="caption" sx={{ fontSize: '0.5rem', color: 'text.secondary' }}>Dec</Typography>
                              <ProbBar value={fight.blue_dec || 0} color="secondary" />
                            </Box>
                          </Stack>
                        </Box>

                        {/* Open in center */}
                        {onFightSelect && (
                          <Box
                            onClick={(e) => handleFightSelect(e, fight)}
                            sx={{
                              mt: 0.75, p: 0.4, borderRadius: 0.75, textAlign: 'center',
                              bgcolor: 'rgba(0,174,239,0.08)', border: '1px solid rgba(0,174,239,0.2)',
                              cursor: 'pointer',
                              '&:hover': { bgcolor: 'rgba(0,174,239,0.15)' },
                              transition: 'all 0.15s',
                            }}
                          >
                            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: 'primary.main', fontWeight: 600 }}>
                              Open in Matchup Analyzer →
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    </Collapse>
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
