import { useState, useEffect } from "react";
import { getPrevious } from "./Call";
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
import HistoryIcon from '@mui/icons-material/History';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

function PreviousSidebar({ onFightSelect }) {
  const [previousFights, setPreviousFights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedIndex, setExpandedIndex] = useState(null);

  useEffect(() => {
    const fetchPrevious = async () => {
      setLoading(true);
      setError(null);
      try {
        const fights = await getPrevious();
        const parseFightDate = (fightId) => {
          if (!fightId) return 0;
          const parts = fightId.split('_');
          if (parts.length < 3) return 0;
          const dateStr = `${parts[0]} ${parts[1]} 20${parts[2]}`;
          const timestamp = Date.parse(dateStr);
          return isNaN(timestamp) ? 0 : timestamp;
        };

        const sortedFights = [...fights].sort((a, b) => {
          const timeA = parseFightDate(a.fight_id);
          const timeB = parseFightDate(b.fight_id);
          if (timeA !== timeB) return timeB - timeA;
          return (a.fight_number || 999) - (b.fight_number || 999);
        });
        setPreviousFights(sortedFights);
      } catch (err) {
        setError(err.message || "Failed to load previous fights");
      } finally {
        setLoading(false);
      }
    };
    fetchPrevious();
  }, []);

  const getTotalWinProb = (fight) => {
    const redTotal = (fight.red_ko || 0) + (fight.red_sub || 0) + (fight.red_dec || 0);
    const blueTotal = (fight.blue_ko || 0) + (fight.blue_sub || 0) + (fight.blue_dec || 0);
    return { redTotal, blueTotal };
  };

  const getResultInfo = (result) => {
    if (!result) return null;
    const r = typeof result === 'number' ? result : parseInt(result);
    if (r === 1) return { winner: 'red', method: 'KO/TKO', resultNum: r };
    if (r === 2) return { winner: 'red', method: 'Sub', resultNum: r };
    if (r === 3) return { winner: 'red', method: 'Dec', resultNum: r };
    if (r === 4) return { winner: 'blue', method: 'KO/TKO', resultNum: r };
    if (r === 5) return { winner: 'blue', method: 'Sub', resultNum: r };
    if (r === 6) return { winner: 'blue', method: 'Dec', resultNum: r };
    return null;
  };

  const getPredictionAccuracy = (fight, resultInfo) => {
    if (!resultInfo) return { winnerCorrect: null, outcomeCorrect: null, predictedMethod: null, predictedFighter: null };
    const { redTotal, blueTotal } = getTotalWinProb(fight);
    const predictedWinner = redTotal > blueTotal ? 'red' : 'blue';
    const winnerCorrect = predictedWinner === resultInfo.winner;
    const outcomes = [
      { value: fight.red_ko || 0, resultNum: 1, method: 'KO/TKO', fighter: 'red' },
      { value: fight.red_sub || 0, resultNum: 2, method: 'Sub', fighter: 'red' },
      { value: fight.red_dec || 0, resultNum: 3, method: 'Dec', fighter: 'red' },
      { value: fight.blue_ko || 0, resultNum: 4, method: 'KO/TKO', fighter: 'blue' },
      { value: fight.blue_sub || 0, resultNum: 5, method: 'Sub', fighter: 'blue' },
      { value: fight.blue_dec || 0, resultNum: 6, method: 'Dec', fighter: 'blue' },
    ];
    const predicted = outcomes.reduce((max, curr) => curr.value > max.value ? curr : max);
    return { winnerCorrect, outcomeCorrect: predicted.resultNum === resultInfo.resultNum, predictedMethod: predicted.method, predictedFighter: predicted.fighter };
  };

  const calculateAccuracyStats = () => {
    if (previousFights.length === 0) return { winnerAccuracy: 0, outcomeAccuracy: 0 };
    let wCorrect = 0, oCorrect = 0, total = 0;
    previousFights.forEach(fight => {
      const ri = getResultInfo(fight.result);
      if (!ri) return;
      total++;
      const { winnerCorrect, outcomeCorrect } = getPredictionAccuracy(fight, ri);
      if (winnerCorrect) wCorrect++;
      if (outcomeCorrect) oCorrect++;
    });
    return {
      winnerAccuracy: total > 0 ? (wCorrect / total) * 100 : 0,
      outcomeAccuracy: total > 0 ? (oCorrect / total) * 100 : 0,
    };
  };

  const handleCardClick = (e, index, fight) => {
    e.stopPropagation();
    setExpandedIndex(expandedIndex === index ? null : index);
  };

  const handleFightSelect = (fight) => {
    if (onFightSelect) onFightSelect(fight.red_fighter, fight.blue_fighter);
  };

  // Compact probability bar for the expanded view
  const ProbBar = ({ value, color = 'primary', isActualResult = false }) => (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.3 }}>
      <Box sx={{ flex: 1 }}>
        <LinearProgress variant="determinate" value={value * 100}
          sx={{
            height: 3, borderRadius: 1.5,
            backgroundColor: isActualResult ? 'rgba(76,175,80,0.2)' : undefined,
            '& .MuiLinearProgress-bar': {
              backgroundColor: isActualResult ? '#4caf50' : undefined,
            },
          }}
          color={isActualResult ? undefined : color}
        />
      </Box>
      <Typography variant="caption" sx={{ minWidth: 28, fontSize: '0.55rem', color: isActualResult ? '#4caf50' : 'text.secondary' }}>
        {`${(value * 100).toFixed(0)}%`}
      </Typography>
    </Box>
  );

  return (
    <Paper elevation={0} sx={{ p: 1, borderRadius: 3, border: 1, borderColor: 'grey.800', bgcolor: 'background.paper', height: 'fit-content', maxHeight: 'calc(100vh - 120px)', overflow: 'auto' }}>
      <Box sx={{ mb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <HistoryIcon sx={{ color: 'secondary.main', mr: 0.75, fontSize: 18 }} />
          <Typography variant="h6" fontWeight="bold" sx={{ fontSize: '0.9rem' }}>Previous Fights</Typography>
        </Box>
        {!loading && !error && previousFights.length > 0 && (() => {
          const stats = calculateAccuracyStats();
          return (
            <Box sx={{ p: 0.75, borderRadius: 1.5, bgcolor: 'background.default', border: 1, borderColor: 'grey.800' }}>
              <Stack spacing={0.5}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>Winner Accuracy:</Typography>
                  <Typography variant="caption" fontWeight="bold" sx={{ fontSize: '0.65rem', color: 'primary.main' }}>{stats.winnerAccuracy.toFixed(0)}%</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>Outcome Accuracy:</Typography>
                  <Typography variant="caption" fontWeight="bold" sx={{ fontSize: '0.65rem', color: 'secondary.main' }}>{stats.outcomeAccuracy.toFixed(0)}%</Typography>
                </Box>
              </Stack>
            </Box>
          );
        })()}
      </Box>

      {loading && <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}><CircularProgress size={32} /></Box>}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {!loading && !error && previousFights.length === 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>No previous fights available</Typography>
      )}

      {!loading && !error && previousFights.length > 0 && (
        <Stack spacing={0.75}>
          {previousFights.map((fight, index) => {
            const { redTotal, blueTotal } = getTotalWinProb(fight);
            const redFighter = fight.red_fighter || "TBD";
            const blueFighter = fight.blue_fighter || "TBD";
            const resultInfo = getResultInfo(fight.result);
            const { winnerCorrect, outcomeCorrect, predictedMethod, predictedFighter } = getPredictionAccuracy(fight, resultInfo);
            const redPct = Math.round(redTotal * 100);
            const bluePct = Math.round(blueTotal * 100);
            const isExpanded = expandedIndex === index;

            const winnerName = resultInfo ? (resultInfo.winner === 'red' ? redFighter : blueFighter) : null;
            const loserName = resultInfo ? (resultInfo.winner === 'red' ? blueFighter : redFighter) : null;
            const resultWinnerLastName = winnerName ? winnerName.split(' ').pop() : '';

            return (
              <Card key={index} elevation={0}
                sx={{
                  borderRadius: 1.5, border: 1,
                  borderColor: winnerCorrect ? 'rgba(76,175,80,0.5)' : resultInfo ? 'rgba(244,67,54,0.4)' : 'grey.800',
                  borderWidth: resultInfo ? 1.5 : 1,
                  cursor: 'pointer',
                  '&:hover': { bgcolor: 'action.hover' },
                  transition: 'all 0.2s',
                }}
                onClick={(e) => handleCardClick(e, index, fight)}
              >
                <CardContent sx={{ p: 0.75, '&:last-child': { pb: 0.75 } }}>
                  <Stack spacing={0.3}>
                    {/* Verdict + Winner line */}
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      {resultInfo && (
                        winnerCorrect
                          ? <CheckCircleIcon sx={{ fontSize: 14, color: '#4caf50' }} />
                          : <CancelIcon sx={{ fontSize: 14, color: '#f44336' }} />
                      )}
                      <Typography variant="body2" fontWeight="bold" noWrap sx={{ fontSize: '0.7rem', flex: 1 }}>
                        {winnerName || redFighter}
                        <Box component="span" sx={{ color: 'text.secondary', fontWeight: 400, mx: 0.5, fontSize: '0.6rem' }}>def.</Box>
                        {loserName || blueFighter}
                      </Typography>
                      {isExpanded
                        ? <ExpandLessIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                        : <ExpandMoreIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                      }
                    </Box>

                    {/* Head-to-head bar */}
                    <Box>
                      <Box sx={{ display: 'flex', height: 5, borderRadius: 2.5, overflow: 'hidden' }}>
                        <Box sx={{ width: `${redPct}%`, bgcolor: winnerCorrect ? '#4caf50' : 'primary.main', borderRadius: '2.5px 0 0 2.5px' }} />
                        <Box sx={{ width: `${bluePct}%`, bgcolor: winnerCorrect ? 'rgba(76,175,80,0.3)' : 'secondary.main', borderRadius: '0 2.5px 2.5px 0' }} />
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.1 }}>
                        <Typography variant="caption" sx={{ fontSize: '0.5rem', color: 'text.secondary' }}>{redPct}%</Typography>
                        <Typography variant="caption" sx={{ fontSize: '0.5rem', color: 'text.secondary' }}>{bluePct}%</Typography>
                      </Box>
                    </Box>

                    {/* Predicted vs Actual with winner name */}
                    {resultInfo && (
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 0.5 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.3 }}>
                          <Typography variant="caption" sx={{ fontSize: '0.5rem', color: 'text.secondary' }}>Pred</Typography>
                          <Box sx={{
                            px: 0.5, py: 0.1, borderRadius: 0.5,
                            bgcolor: outcomeCorrect ? 'rgba(76,175,80,0.15)' : 'rgba(244,67,54,0.1)',
                            border: `1px solid ${outcomeCorrect ? 'rgba(76,175,80,0.4)' : 'rgba(244,67,54,0.3)'}`,
                          }}>
                            <Typography variant="caption" sx={{ fontSize: '0.5rem', fontWeight: 700, color: outcomeCorrect ? '#4caf50' : '#ef5350' }}>
                              {predictedFighter === 'red' ? redFighter.split(' ').pop() : blueFighter.split(' ').pop()} {predictedMethod}
                            </Typography>
                          </Box>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.3 }}>
                          <Typography variant="caption" sx={{ fontSize: '0.5rem', color: 'text.secondary' }}>Result</Typography>
                          <Box sx={{
                            px: 0.5, py: 0.1, borderRadius: 0.5,
                            bgcolor: resultInfo.winner === 'red' ? 'rgba(0,174,239,0.12)' : 'rgba(144,202,249,0.1)',
                            border: `1px solid ${resultInfo.winner === 'red' ? 'rgba(0,174,239,0.3)' : 'rgba(144,202,249,0.25)'}`,
                          }}>
                            <Typography variant="caption" sx={{ fontSize: '0.5rem', fontWeight: 700, color: resultInfo.winner === 'red' ? 'primary.main' : 'secondary.main' }}>
                              {resultWinnerLastName} {resultInfo.method}
                            </Typography>
                          </Box>
                        </Box>
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
                              <ProbBar value={fight.red_ko || 0} color="primary" isActualResult={resultInfo && resultInfo.resultNum === 1} />
                            </Box>
                            <Box>
                              <Typography variant="caption" sx={{ fontSize: '0.5rem', color: 'text.secondary' }}>Sub</Typography>
                              <ProbBar value={fight.red_sub || 0} color="primary" isActualResult={resultInfo && resultInfo.resultNum === 2} />
                            </Box>
                            <Box>
                              <Typography variant="caption" sx={{ fontSize: '0.5rem', color: 'text.secondary' }}>Dec</Typography>
                              <ProbBar value={fight.red_dec || 0} color="primary" isActualResult={resultInfo && resultInfo.resultNum === 3} />
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
                              <ProbBar value={fight.blue_ko || 0} color="secondary" isActualResult={resultInfo && resultInfo.resultNum === 4} />
                            </Box>
                            <Box>
                              <Typography variant="caption" sx={{ fontSize: '0.5rem', color: 'text.secondary' }}>Sub</Typography>
                              <ProbBar value={fight.blue_sub || 0} color="secondary" isActualResult={resultInfo && resultInfo.resultNum === 5} />
                            </Box>
                            <Box>
                              <Typography variant="caption" sx={{ fontSize: '0.5rem', color: 'text.secondary' }}>Dec</Typography>
                              <ProbBar value={fight.blue_dec || 0} color="secondary" isActualResult={resultInfo && resultInfo.resultNum === 6} />
                            </Box>
                          </Stack>
                        </Box>

                        {/* Click to load in center */}
                        {onFightSelect && (
                          <Box
                            onClick={(e) => { e.stopPropagation(); handleFightSelect(fight); }}
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

export default PreviousSidebar;
