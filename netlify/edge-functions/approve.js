// Netlify Edge Function — Rapor Onaylama
// Kullanıcı raporu email'den onaylanınca GitHub'a ekler

export default async function handler(request, context) {

  // Sadece GET isteği
  if(request.method !== 'GET'){
    return new Response('Method not allowed', { status: 405 });
  }

  const url   = new URL(request.url);
  const token = url.searchParams.get('token');

  // Güvenlik token kontrolü
  if(token !== Deno.env.get('APPROVE_SECRET')){
    return new Response(html('❌ Geçersiz Token', 'Bu link geçersiz veya süresi dolmuş.'), {
      status: 403,
      headers: { 'Content-Type': 'text/html; charset=utf-8' }
    });
  }

  // Rapor verisini al
  const loc   = url.searchParams.get('loc')  || '';
  const fish  = url.searchParams.get('fish') || '';
  const rod   = url.searchParams.get('rod')  || '';
  const bait  = url.searchParams.get('bait') || '';
  const note  = url.searchParams.get('note') || '';
  const lat   = parseFloat(url.searchParams.get('lat') || '0');
  const lng   = parseFloat(url.searchParams.get('lng') || '0');
  const type  = url.searchParams.get('type') || 'deniz';

  if(!loc || !fish){
    return new Response(html('❌ Eksik Bilgi', 'Lokasyon veya balık bilgisi eksik.'), {
      status: 400,
      headers: { 'Content-Type': 'text/html; charset=utf-8' }
    });
  }

  const GITHUB_TOKEN = Deno.env.get('GITHUB_TOKEN');
  const REPO         = 'hiphopcem/balik-radari';
  const FILE_PATH    = 'data/reports.json';
  const API_BASE     = `https://api.github.com/repos/${REPO}/contents/${FILE_PATH}`;

  try {
    // Mevcut reports.json'u oku
    const getRes = await fetch(API_BASE, {
      headers: {
        'Authorization': `token ${GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'SihirliZokaRadar'
      }
    });

    if(!getRes.ok) throw new Error('GitHub okuma hatası: ' + getRes.status);

    const fileData   = await getRes.json();
    const content    = atob(fileData.content.replace(/\n/g, ''));
    const jsonData   = JSON.parse(content);
    const reports    = jsonData.reports || [];

    // Yeni raporu oluştur
    const newReport = {
      id:        'u' + Date.now(),
      lat:       lat || (39 + Math.random() * 3),
      lng:       lng || (26 + Math.random() * 5),
      loc:       loc,
      fish:      fish.split(',').map(f => f.trim()).filter(Boolean),
      rod:       rod,
      bait:      bait,
      note:      note || 'Kullanıcı raporu (onaylandı).',
      heat:      3,
      type:      type,
      timestamp: new Date().toISOString(),
      source:    'Sihirli Zoka Radar',
      hot:       false
    };

    // Başa ekle
    reports.unshift(newReport);

    // Güncelle ve kaydet
    const updatedJson = JSON.stringify({
      last_updated: new Date().toISOString(),
      total:        reports.length,
      reports:      reports.slice(0, 200) // max 200
    }, null, 2);

    const putRes = await fetch(API_BASE, {
      method: 'PUT',
      headers: {
        'Authorization': `token ${GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'SihirliZokaRadar',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: `✅ Kullanıcı raporu onaylandı: ${loc}`,
        content: btoa(unescape(encodeURIComponent(updatedJson))),
        sha:     fileData.sha,
        branch:  'main'
      })
    });

    if(!putRes.ok){
      const err = await putRes.text();
      throw new Error('GitHub yazma hatası: ' + err);
    }

    // Başarılı
    return new Response(html(
      '✅ Rapor Onaylandı!',
      `<b>${loc}</b> için <b>${fish}</b> raporu haritaya eklendi.<br><br>Netlify otomatik olarak güncellenecek, birkaç dakika içinde haritada görünecek.`
    ), {
      status: 200,
      headers: { 'Content-Type': 'text/html; charset=utf-8' }
    });

  } catch(e) {
    return new Response(html('❌ Hata Oluştu', e.message), {
      status: 500,
      headers: { 'Content-Type': 'text/html; charset=utf-8' }
    });
  }
}

function html(title, message) {
  return `<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${title} — Sihirli Zoka Radar</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box;}
  body{background:#010c16;display:flex;align-items:center;justify-content:center;min-height:100vh;font-family:'Segoe UI',sans-serif;}
  .box{background:#061522;border:1px solid rgba(0,200,248,0.2);border-radius:16px;padding:40px;text-align:center;max-width:420px;width:90%;}
  .icon{font-size:52px;margin-bottom:16px;}
  h1{color:#00c8f8;font-size:20px;margin-bottom:12px;}
  p{color:#7aaac8;font-size:14px;line-height:1.7;}
  .back{display:inline-block;margin-top:20px;padding:10px 24px;background:rgba(0,200,248,0.1);border:1px solid rgba(0,200,248,0.3);color:#00c8f8;border-radius:8px;text-decoration:none;font-size:13px;}
</style>
</head>
<body>
  <div class="box">
    <div class="icon">${title.includes('✅') ? '🎣' : '⛔'}</div>
    <h1>${title}</h1>
    <p>${message}</p>
    <a href="https://www.sihirlizoka.com" class="back">← Siteye Dön</a>
  </div>
</body>
</html>`;
}

export const config = { path: '/approve' };
