import React, { useState, useEffect } from "react";
import { Grid, LinearProgress, Card, CardContent, Typography, Button, TextField } from '@mui/material';
import CheckCircleOutlineRoundedIcon from '@mui/icons-material/CheckCircleOutlineRounded';
import TuneRoundedIcon from '@mui/icons-material/TuneRounded';

export default function Training() {

    return (
        <div className="App" style={{padding:"60px"}}>
            <Typography gutterBottom variant="h3" align="center" >
            Data Auto-Augmentation
            </Typography>
            <Card style={{ maxWidth: 900, padding: "10px 5px", margin: "0 auto" }}>
                <CardContent>
                    <Grid style={{padding:"50px"}}>
                    <Typography gutterBottom variant="subtitle1" align="center" >
                        Our auto-augment agents are working hard to generate your data augmentation policy ...
                    </Typography>
                    <Grid style={{padding:"60px"}}>
                        <LinearProgress color="primary"/>
                        <LinearProgress color="primary" />
                        <LinearProgress color="primary" />
                        <LinearProgress color="primary" />
                    </Grid>
                    </Grid>
                </CardContent>
            </Card>
                
        </div>
    )
}