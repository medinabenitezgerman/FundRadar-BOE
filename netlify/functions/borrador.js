exports.handler = async function(event, context) {
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
      },
      body: ''
    };
  }

  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method Not Allowed' };
  }

  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Content-Type': 'application/json'
  };

  try {
    const { prompt, url_convocatoria } = JSON.parse(event.body);

    let contexto_convocatoria = '';
    if (url_convocatoria) {
      try {
        const res = await fetch(url_convocatoria);
        const html = await res.text();
        const texto = html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').substring(0, 8000);
        contexto_convocatoria = `\n\nTEXTO COMPLETO DE LA CONVOCATORIA:\n${texto}`;
      } catch(e) {
        console.log('No se pudo leer la convocatoria:', e.message);
      }
    }

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-6',
        max_tokens: 2000,
        messages: [{ role: 'user', content: prompt + contexto_convocatoria }]
      })
    });

    const data = await response.json();
    return { statusCode: 200, headers, body: JSON.stringify(data) };
  } catch (error) {
    return { statusCode: 500, headers, body: JSON.stringify({ error: error.message }) };
  }
};
