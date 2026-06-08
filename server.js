require('dotenv').config();
const express = require('express');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname, 'public')));

let botStatus = {
    hyperion: 'offline',
    steve: 'offline',
    oracle: 'offline'
};

// --- LAUNCH THE PYTHON STACK ---

function launchPythonBot(botKey, scriptPath, tokenName) {
    console.log(`[DEPLOYING] Attempting to start Python process for ${botKey} at ${scriptPath}...`);
    
    // Check if the file exists to avoid ENOENT errors
    const fs = require('fs');
    if (!fs.existsSync(scriptPath)) {
        console.error(`[CRITICAL] File not found: ${scriptPath}. Check your folder structure!`);
        return;
    }

    const botEnv = Object.assign({}, process.env);
    botEnv['TOKEN'] = process.env[tokenName];
    botEnv['DISCORD_TOKEN'] = process.env[tokenName];

    // Explicitly using 'python3' for Linux/Docker environments
    const botProcess = spawn('python3', [path.basename(scriptPath)], {
        cwd: path.dirname(scriptPath),
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
        setTimeout(() => launchPythonBot(botKey, scriptPath, tokenName), 5000);
    });
}

// Ensure these paths match your actual GitHub structure exactly
// If the bots are in the root, remove 'bots/oracle/' etc.
launchPythonBot('oracle', path.join(__dirname, 'bots', 'oracle', 'Astrobot.py'), 'ORACLE_TOKEN');
launchPythonBot('hyperion', path.join(__dirname, 'bots', 'hyperion', 'chatbot.py'), 'HYPERION_TOKEN');
launchPythonBot('steve', path.join(__dirname, 'bots', 'steve', 'steve.py'), 'STEVE_TOKEN');

// --- REAL-TIME STATUS API ---
app.get('/api/status', (req, res) => {
    res.json(botStatus);
});

app.listen(PORT, () => {
    console.log(`[SYSTEM UPLINK] Portfolio mothership active on port ${PORT}`);
});
