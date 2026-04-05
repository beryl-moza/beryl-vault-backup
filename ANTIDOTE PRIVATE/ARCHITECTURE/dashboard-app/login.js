// Server-side login handler — passwords NEVER sent to the browser
// Passwords stored as Netlify environment variables
const crypto = require('crypto');

// User config (everything EXCEPT passwords — those come from env vars)
const USERS = {
  'beryl@antidote.group': {
    name: 'Beryl', role: 'admin', initial: 'B',
    zones: ['shared', 'private', 'personal'],
    tabs: ['command', 'services', 'agents', 'projects', 'connectors', 'blockers', 'team', 'client'],
    envKey: 'PASS_BERYL'
  },
  'brandon@antidote.group': {
    name: 'Brandon', role: 'partner', initial: 'B',
    zones: ['shared', 'private', 'personal'],
    tabs: ['command', 'services', 'agents', 'projects', 'blockers'],
    envKey: 'PASS_BRANDON'
  },
  'clayton@antidote.group': {
    name: 'Clayton', role: 'partner', initial: 'C',
    zones: ['shared'],
    tabs: ['command', 'services', 'projects', 'blockers'],
    envKey: 'PASS_CLAYTON'
  },
  'eddy@antidote.group': {
    name: 'Eddy', role: 'contributor', initial: 'E',
    zones: ['shared'],
    tabs: ['command', 'projects'],
    envKey: 'PASS_EDDY'
  },
  'demo@client.com': {
    name: 'Demo Client', role: 'client', initial: 'D',
    zones: [],
    tabs: ['client'],
    envKey: 'PASS_DEMO'
  }
};

exports.handler = async (event) => {
  // Only accept POST
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: JSON.stringify({ error: 'Method not allowed' }) };
  }

  // CORS headers
  const headers = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type'
  };

  try {
    const { email, password } = JSON.parse(event.body);

    if (!email || !password) {
      return { statusCode: 400, headers, body: JSON.stringify({ error: 'Email and password required' }) };
    }

    const normalizedEmail = email.trim().toLowerCase();
    const user = USERS[normalizedEmail];

    if (!user) {
      // Don't reveal whether email exists
      return { statusCode: 401, headers, body: JSON.stringify({ error: 'Invalid email or password' }) };
    }

    // Get password from environment variable
    const storedPassword = process.env[user.envKey];
    if (!storedPassword) {
      console.error(`Missing env var: ${user.envKey}`);
      return { statusCode: 500, headers, body: JSON.stringify({ error: 'Server configuration error' }) };
    }

    // Constant-time comparison to prevent timing attacks
    const inputBuf = Buffer.from(password);
    const storedBuf = Buffer.from(storedPassword);

    if (inputBuf.length !== storedBuf.length || !crypto.timingSafeEqual(inputBuf, storedBuf)) {
      return { statusCode: 401, headers, body: JSON.stringify({ error: 'Invalid email or password' }) };
    }

    // Generate a simple session token
    const token = crypto.randomBytes(32).toString('hex');

    // Return user data (no password!) + session token
    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        success: true,
        token: token,
        user: {
          email: normalizedEmail,
          name: user.name,
          role: user.role,
          initial: user.initial,
          zones: user.zones,
          tabs: user.tabs
        }
      })
    };
  } catch (err) {
    return { statusCode: 400, headers, body: JSON.stringify({ error: 'Invalid request' }) };
  }
};
