const http = require('http');
const fs = require('fs');

const port = Number(process.env.MOCK_PORT || 18765);
const received = [];

function json(res, status, body) {
  const data = JSON.stringify(body);
  res.writeHead(status, {'content-type': 'application/json', 'content-length': Buffer.byteLength(data)});
  res.end(data);
}

const server = http.createServer((req, res) => {
  let body = '';
  req.on('data', chunk => body += chunk);
  req.on('end', () => {
    const url = new URL(req.url, `http://127.0.0.1:${port}`);
    received.push({method: req.method, path: url.pathname, search: url.search, body});

    if (req.method === 'GET' && url.pathname === '/health') {
      return json(res, 200, {ok: true});
    }

    if (req.method === 'GET' && /\/repos\/[^/]+\/[^/]+\/commits$/.test(url.pathname)) {
      return json(res, 200, [
        {sha: 'abc123456789', commit: {message: 'Add deterministic weekly summary fixture'}},
        {sha: 'def987654321', commit: {message: 'Fix report date window\n\nDetails'}}
      ]);
    }

    if (req.method === 'GET' && url.pathname === '/search/issues') {
      const q = url.searchParams.get('q') || '';
      if (q.includes('is:pr') && q.includes('is:merged')) {
        return json(res, 200, {total_count: 1, items: [
          {number: 42, title: 'Ship weekly reporting workflow'}
        ]});
      }
      return json(res, 200, {total_count: 1, items: [
        {number: 17, title: 'Close stale summary formatting bug'}
      ]});
    }

    if (req.method === 'POST' && url.pathname === '/v1/messages') {
      let parsed;
      try { parsed = JSON.parse(body || '{}'); } catch { return json(res, 400, {error: 'invalid json'}); }
      if (parsed.model !== 'claude-sonnet-4-20250514') {
        return json(res, 400, {error: 'wrong model'});
      }
      return json(res, 200, {
        id: 'msg_mock',
        type: 'message',
        role: 'assistant',
        model: parsed.model,
        content: [{type: 'text', text: 'Weekly update: the team shipped the reporting workflow, fixed summary formatting, and added deterministic coverage.'}],
        stop_reason: 'end_turn'
      });
    }

    if (req.method === 'POST' && url.pathname === '/discord') {
      let parsed;
      try { parsed = JSON.parse(body || '{}'); } catch { return json(res, 400, {error: 'invalid json'}); }
      if (!parsed.content || !parsed.content.includes('Weekly update')) {
        return json(res, 400, {error: 'summary missing'});
      }
      fs.writeFileSync(process.env.MOCK_CAPTURE || '/tmp/discord-payload.json', JSON.stringify(parsed, null, 2));
      res.writeHead(204);
      return res.end();
    }

    return json(res, 404, {error: 'not found', path: url.pathname});
  });
});

server.listen(port, '127.0.0.1', () => {
  console.log(`mock server listening on ${port}`);
});
