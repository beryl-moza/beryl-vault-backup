// Netlify Identity: Auto-confirm new users (invited only)
// This fires on the identity-signup event
exports.handler = async (event) => {
  const body = JSON.parse(event.body);
  const { user } = body;

  // Only allow users with @antidote.group or pre-approved client emails
  const allowedDomains = ['antidote.group'];
  const allowedEmails = process.env.ALLOWED_CLIENT_EMAILS
    ? process.env.ALLOWED_CLIENT_EMAILS.split(',').map(e => e.trim().toLowerCase())
    : [];

  const email = (user.email || '').toLowerCase();
  const domain = email.split('@')[1] || '';

  if (allowedDomains.includes(domain) || allowedEmails.includes(email)) {
    return {
      statusCode: 200,
      body: JSON.stringify({ app_metadata: { confirmed: true } }),
    };
  }

  // Reject unknown signups
  return {
    statusCode: 403,
    body: JSON.stringify({ error: 'Signup not allowed for this email.' }),
  };
};
