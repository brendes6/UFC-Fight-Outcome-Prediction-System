import { useState } from "react";
import { getPredictions, getUpcoming } from "./Call";
import Prediction from "./Prediction";
import Paper from '@mui/material/Paper';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';




function Upcoming() {

    const fighters = async () => await getUpcoming();
    const redFighters = fighters.redFighters
    const blueFighters = fighters.blueFighters

    
    
    const result = async () => await getPredictions(fighter1Query, fighter2Query);

    return (
        <Paper>

            <Box sx={{ mt: 6 }}>
            {fighters.map((red) => {
                <Prediction pred={getPredictions(fighter1Query, fighter2Query)} />})}
            </Box>
        </Paper>
    )
}