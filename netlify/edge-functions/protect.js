export default async function handler(request, context) {
  const ALLOWED = [
    'www.sihirlizoka.com',
    'sihirlizoka.com',
  ];

  const referer = request.headers.get('referer') || '';
  const origin  = request.headers.get('origin')  || '';

  function getHost(url) {
    try { return new URL(url).hostname; } catch(e) { return ''; }
  }

  const refHost = getHost(referer) || getHost(origin);
  const allowed = ALLOWED.some(d => refHost === d || refHost.endsWith('.' + d));

  if (!allowed) {
    return new Response(
      `<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><title>Yetkisiz Erişim</title><style>*{margin:0;padding:0;}body{background:#010c16;display:flex;align-items:center;justify-content:center;height:100vh;font-family:monospace;}.box{text-align:center;color:#ff5e2a;padding:30px;}.icon{font-size:52px;margin-bottom:16px;}.title{font-size:20px;font-weight:bold;margin-bottom:10px;}.sub{font-size:13px;color:#7aaac8;}</style></head><body><div class="box"><div class="icon">⛔</div><div class="title">Yetkisiz Erişim</div><div class="sub">Bu içerik yalnızca sihirlizoka.com üzerinde çalışır.</div></div></body></html>`,
      { status: 403, headers: { 'Content-Type': 'text/html; charset=utf-8' } }
    );
  }

  return context.next();
}

export const config = { path: '/balik-radar.html' };
