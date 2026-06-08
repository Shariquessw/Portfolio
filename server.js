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

// We added 'tokenName' so the Mothership knows which token belongs to which bot
function launchPythonBot(botKey, scriptPath, tokenName) {
    console.log(`[DEPLOYING] Starting Python process for ${botKey}...`);
    
    // Create a custom environment just for this specific bot
    const botEnv = Object.assign({}, process.env);
    
    // MAGIC HACK: Pass the specific token as standard names so your Python code doesn't break
    botEnv['TOKEN'] = process.env[tokenName];
    botEnv['DISCORD_TOKEN'] = process.env[tokenName];

    const botProcess = spawn('python3', [path.basename(scriptPath)], {
        cwd: path.dirname(scriptPath),
        env: botEnv 
    });

    botStatus[botKey] = 'online';

    botProcess.stdout.on('data', (data) => {
        console.log(`[${botKey.toUpperCase()}] ${data.toString().trim()}`);
    });

    botProcess.stderr.on('data', (data) => {
        console.error(`[${botKey} ERROR] ${data.toString().trim()}`);
    });

    botProcess.on('close', (code) => {
        console.log(`[${botKey.toUpperCase()}] Process exited with code ${code}. Restarting...`);
        botStatus[botKey] = 'offline';
        setTimeout(() => launchPythonBot(botKey, scriptPath, tokenName), 5000);
    });
}

// Fire up all three nodes and map their specific tokens!
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
