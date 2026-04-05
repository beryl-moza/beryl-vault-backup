// Netlify Identity: Assign role based on email domain on login
// This fires on the identity-login event
exports.handler = async (event) => {
  const body = JSON.parse(event.body);
  const { user } = body;
  const email = (user.email || '').toLowerCase();

  // Role mapping
  const adminEmails = ['beryl@antidote.group'];
  const teamDomain = 'antidote.group';

  let role = 'client'; // default

  if (adminEmails.includes(email)) {
    role = 'admin';
  } else if (email.endsWith('@' + teamDomain)) {
    role = 'team';
  }

  return {
    statusCode: 200,
    body: JSON.stringify({
      app_metadata: {
        roles: [role],
        authorization: { roles: [role] },
      },
    }),
  };
};
