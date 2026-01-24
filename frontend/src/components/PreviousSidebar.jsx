import { useState, useEffect } from "react";
import { getPrevious } from "./Call";
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
import HistoryIcon from '@mui/icons-material/History';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

function PreviousSidebar({ onFightSelect }) {
  const [previousFights, setPreviousFights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPrevious = async () => {
      setLoading(true);
      setError(null);
      try {
        const fights = await getPrevious();
        // Sort by fight_number (ascending order)
        const sortedFights = [...fights].sort((a, b) => {
          const aNum = a.fight_number || 999;
          const bNum = b.fight_number || 999;
          return aNum - bNum;
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
    // 1 = red KO, 2 = red sub, 3 = red dec
    // 4 = blue KO, 5 = blue sub, 6 = blue dec
    if (!result) return null;
    const resultNum = typeof result === 'number' ? result : parseInt(result);
    
    if (resultNum === 1) return { winner: 'red', method: 'KO/TKO', color: 'primary', resultNum };
    if (resultNum === 2) return { winner: 'red', method: 'Sub', color: 'primary', resultNum };
    if (resultNum === 3) return { winner: 'red', method: 'Dec', color: 'primary', resultNum };
    if (resultNum === 4) return { winner: 'blue', method: 'KO/TKO', color: 'secondary', resultNum };
    if (resultNum === 5) return { winner: 'blue', method: 'Sub', color: 'secondary', resultNum };
    if (resultNum === 6) return { winner: 'blue', method: 'Dec', color: 'secondary', resultNum };
    return null;
  };

  const getPredictionAccuracy = (fight, resultInfo) => {
    if (!resultInfo) return { winnerCorrect: null, outcomeCorrect: null };
    
    const { redTotal, blueTotal } = getTotalWinProb(fight);
    const predictedWinner = redTotal > blueTotal ? 'red' : 'blue';
    const winnerCorrect = predictedWinner === resultInfo.winner;
    
    // Find the outcome with highest probability
    const outcomes = [
      { value: fight.red_ko || 0, resultNum: 1 },
      { value: fight.red_sub || 0, resultNum: 2 },
      { value: fight.red_dec || 0, resultNum: 3 },
      { value: fight.blue_ko || 0, resultNum: 4 },
      { value: fight.blue_sub || 0, resultNum: 5 },
      { value: fight.blue_dec || 0, resultNum: 6 },
    ];
    const predictedOutcome = outcomes.reduce((max, curr) => curr.value > max.value ? curr : max);
    const outcomeCorrect = predictedOutcome.resultNum === resultInfo.resultNum;
    
    return { winnerCorrect, outcomeCorrect };
  };

  const calculateAccuracyStats = () => {
    if (previousFights.length === 0) return { winnerAccuracy: 0, outcomeAccuracy: 0 };
    
    let winnerCorrect = 0;
    let outcomeCorrect = 0;
    let total = 0;
    
    previousFights.forEach(fight => {
      const resultInfo = getResultInfo(fight.result);
      if (!resultInfo) return;
      
      total++;
      const { winnerCorrect: wc, outcomeCorrect: oc } = getPredictionAccuracy(fight, resultInfo);
      if (wc) winnerCorrect++;
      if (oc) outcomeCorrect++;
    });
    
    return {
      winnerAccuracy: total > 0 ? (winnerCorrect / total) * 100 : 0,
      outcomeAccuracy: total > 0 ? (outcomeCorrect / total) * 100 : 0,
    };
  };

  const handleFightClick = (fight) => {
    if (onFightSelect) {
      onFightSelect(fight.red_fighter, fight.blue_fighter);
    }
  };

  const CompactProbabilityBar = ({ value, color = 'primary', isActualResult = false, isCorrect = false, isIncorrect = false }) => {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.2 }}>
        <Box sx={{ flex: 1, position: 'relative' }}>
          <LinearProgress 
            variant="determinate" 
            value={value * 100} 
            sx={{ 
              height: 2.5, 
              borderRadius: 1.25,
              backgroundColor: isActualResult
                ? 'rgba(76, 175, 80, 0.2)' 
                : isIncorrect 
                  ? 'rgba(244, 67, 54, 0.2)' 
                  : undefined,
              '& .MuiLinearProgress-bar': {
                backgroundColor: isActualResult
                  ? '#4caf50' 
                  : isIncorrect 
                    ? '#f44336' 
                    : undefined,
              }
            }} 
          />
          {isCorrect && (
            <CheckCircleIcon 
              sx={{ 
                position: 'absolute', 
                right: -18, 
                top: -2, 
                fontSize: 12, 
                color: 'success.main' 
              }} 
            />
          )}
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
      <Box sx={{ mb: 1.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <HistoryIcon sx={{ color: 'secondary.main', mr: 0.75, fontSize: 18 }} />
          <Typography variant="h6" fontWeight="bold" sx={{ fontSize: '0.9rem' }}>
            Previous Fights
          </Typography>
        </Box>
        {!loading && !error && previousFights.length > 0 && (() => {
          const stats = calculateAccuracyStats();
          return (
            <Box sx={{ 
              p: 0.75, 
              borderRadius: 1.5, 
              bgcolor: 'background.default',
              border: 1,
              borderColor: 'grey.800'
            }}>
              <Stack spacing={0.5}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
                    Winner Accuracy:
                  </Typography>
                  <Typography variant="caption" fontWeight="bold" sx={{ fontSize: '0.65rem', color: 'primary.main' }}>
                    {stats.winnerAccuracy.toFixed(0)}%
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
                    Outcome Accuracy:
                  </Typography>
                  <Typography variant="caption" fontWeight="bold" sx={{ fontSize: '0.65rem', color: 'secondary.main' }}>
                    {stats.outcomeAccuracy.toFixed(0)}%
                  </Typography>
                </Box>
              </Stack>
            </Box>
          );
        })()}
      </Box>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress size={32} />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
      )}

      {!loading && !error && previousFights.length === 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
          No previous fights available
        </Typography>
      )}

      {!loading && !error && previousFights.length > 0 && (
        <Stack spacing={1.25}>
          {previousFights.map((fight, index) => {
            const { redTotal, blueTotal } = getTotalWinProb(fight);
            const redFighter = fight.red_fighter || "TBD";
            const blueFighter = fight.blue_fighter || "TBD";
            const redKo = fight.red_ko || 0;
            const redSub = fight.red_sub || 0;
            const redDec = fight.red_dec || 0;
            const blueKo = fight.blue_ko || 0;
            const blueSub = fight.blue_sub || 0;
            const blueDec = fight.blue_dec || 0;
            const resultInfo = getResultInfo(fight.result);
            const { winnerCorrect, outcomeCorrect } = getPredictionAccuracy(fight, resultInfo);
            
            // Determine which outcome was predicted (highest probability)
            const outcomes = [
              { value: redKo, resultNum: 1, fighter: 'red', method: 'KO/TKO' },
              { value: redSub, resultNum: 2, fighter: 'red', method: 'Sub' },
              { value: redDec, resultNum: 3, fighter: 'red', method: 'Dec' },
              { value: blueKo, resultNum: 4, fighter: 'blue', method: 'KO/TKO' },
              { value: blueSub, resultNum: 5, fighter: 'blue', method: 'Sub' },
              { value: blueDec, resultNum: 6, fighter: 'blue', method: 'Dec' },
            ];
            const predictedOutcome = outcomes.reduce((max, curr) => curr.value > max.value ? curr : max);
            
            return (
              <Card
                key={index}
                elevation={0}
                sx={{
                  borderRadius: 1.5,
                  border: 1,
                  borderColor: winnerCorrect 
                    ? 'success.main' 
                    : resultInfo 
                      ? (resultInfo.winner === 'red' ? 'primary.main' : 'secondary.main')
                      : 'grey.800',
                  borderWidth: winnerCorrect ? 2 : 1,
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
                          <CompactProbabilityBar 
                            value={redKo} 
                            color="primary" 
                            isActualResult={resultInfo && resultInfo.winner === 'red' && resultInfo.method === 'KO/TKO'}
                            isCorrect={resultInfo && resultInfo.winner === 'red' && resultInfo.method === 'KO/TKO' && outcomeCorrect}
                            isIncorrect={resultInfo && predictedOutcome.resultNum === 1 && !outcomeCorrect}
                          />
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem', lineHeight: 1.2 }}>
                            Sub
                          </Typography>
                          <CompactProbabilityBar 
                            value={redSub} 
                            color="primary" 
                            isActualResult={resultInfo && resultInfo.winner === 'red' && resultInfo.method === 'Sub'}
                            isCorrect={resultInfo && resultInfo.winner === 'red' && resultInfo.method === 'Sub' && outcomeCorrect}
                            isIncorrect={resultInfo && predictedOutcome.resultNum === 2 && !outcomeCorrect}
                          />
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem', lineHeight: 1.2 }}>
                            Dec
                          </Typography>
                          <CompactProbabilityBar 
                            value={redDec} 
                            color="primary" 
                            isActualResult={resultInfo && resultInfo.winner === 'red' && resultInfo.method === 'Dec'}
                            isCorrect={resultInfo && resultInfo.winner === 'red' && resultInfo.method === 'Dec' && outcomeCorrect}
                            isIncorrect={resultInfo && predictedOutcome.resultNum === 3 && !outcomeCorrect}
                          />
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
                          <CompactProbabilityBar 
                            value={blueKo} 
                            color="secondary" 
                            isActualResult={resultInfo && resultInfo.winner === 'blue' && resultInfo.method === 'KO/TKO'}
                            isCorrect={resultInfo && resultInfo.winner === 'blue' && resultInfo.method === 'KO/TKO' && outcomeCorrect}
                            isIncorrect={resultInfo && predictedOutcome.resultNum === 4 && !outcomeCorrect}
                          />
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem', lineHeight: 1.2 }}>
                            Sub
                          </Typography>
                          <CompactProbabilityBar 
                            value={blueSub} 
                            color="secondary" 
                            isActualResult={resultInfo && resultInfo.winner === 'blue' && resultInfo.method === 'Sub'}
                            isCorrect={resultInfo && resultInfo.winner === 'blue' && resultInfo.method === 'Sub' && outcomeCorrect}
                            isIncorrect={resultInfo && predictedOutcome.resultNum === 5 && !outcomeCorrect}
                          />
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem', lineHeight: 1.2 }}>
                            Dec
                          </Typography>
                          <CompactProbabilityBar 
                            value={blueDec} 
                            color="secondary" 
                            isActualResult={resultInfo && resultInfo.winner === 'blue' && resultInfo.method === 'Dec'}
                            isCorrect={resultInfo && resultInfo.winner === 'blue' && resultInfo.method === 'Dec' && outcomeCorrect}
                            isIncorrect={resultInfo && predictedOutcome.resultNum === 6 && !outcomeCorrect}
                          />
                        </Box>
                      </Stack>
                    </Box>

                    {/* Result indicator */}
                    {resultInfo && (
                      <Box sx={{ mt: 0.5, pt: 0.5, borderTop: 1, borderColor: 'grey.800' }}>
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem', fontStyle: 'italic' }}>
                          Result: {resultInfo.winner === 'red' ? redFighter : blueFighter} by {resultInfo.method}
                        </Typography>
                      </Box>
                    )}
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
