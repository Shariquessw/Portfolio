require('dotenv').config();
const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname, 'public')));

let botStatus = {
    hyperion: 'offline',
    steve: 'offline',
    oracle: 'offline'
};

// --- LAUNCH THE PYTHON STACK ---

function launchPythonBot(botKey, scriptName, tokenName) {
    const scriptPath = path.join(__dirname, scriptName);
    console.log(`[DEPLOYING] Attempting to start Python process for ${botKey} at ${scriptPath}...`);
    
    // Check if the file exists in the root
    if (!fs.existsSync(scriptPath)) {
        console.error(`[CRITICAL] File not found: ${scriptPath}. Ensure it is in the root folder!`);
        return;
    }

    const botEnv = Object.assign({}, process.env);
    botEnv['TOKEN'] = process.env[tokenName];
    botEnv['DISCORD_TOKEN'] = process.env[tokenName];

    // Explicitly using 'python3' for Linux/Docker environments
    const botProcess = spawn('python3', [scriptName], {
        cwd: __dirname,
        env: botEnv 
    });

    // Handle startup errors
    botProcess.on('error', (err) => {
        console.error(`[CRITICAL ERROR] Failed to spawn ${botKey}: ${err.message}`);
        botStatus[botKey] = 'offline';
    });

    botStatus[botKey] = 'online';

    botProcess.stdout.on('data', (data) => {
        console.log(`[${botKey.toUpperCase()}] ${data.toString().trim()}`);
    });

    botProcess.stderr.on('data', (data) => {
        console.error(`[${botKey} ERROR] ${data.toString().trim()}`);
    });

    botProcess.on('close', (code) => {
        console.log(`[${botKey.toUpperCase()}] Process exited with code ${code}. Restarting in 5s...`);
        botStatus[botKey] = 'offline';
        setTimeout(() => launchPythonBot(botKey, scriptName, tokenName), 5000);
    });
}

// Updated to point directly to files in the root folder
launchPythonBot('oracle', 'bots/Oracle/Astrobot.py', 'ORACLE_TOKEN');
launchPythonBot('hyperion', 'bots/Hyperion/chatbot.py', 'HYPERION_TOKEN');
launchPythonBot('steve', 'bots/Steve/steve.py', 'STEVE_TOKEN');

// --- REAL-TIME STATUS API ---
app.get('/api/status', (req, res) => {
    res.json(botStatus);
});

app.listen(PORT, () => {
    console.log(`[SYSTEM UPLINK] Portfolio mothership active on port ${PORT}`);
});
