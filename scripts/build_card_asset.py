"""Generate QR code as base64 PNG + create the self-contained card.html asset."""
import qrcode
import base64
import io
import os
import json
from PIL import Image, ImageDraw, ImageFont

# ============== CARD DATA — EDIT THESE FIELDS ==============
CARD = {
    "firstName": "Rahul",
    "lastName": "Sharma",
    "name": "Rahul Sharma",
    "title": "Senior Product Manager",
    "company": "TechFlow Solutions",
    "phone": "+919876543210",
    "phoneDisplay": "+91 98765 43210",
    "whatsapp": "919876543210",
    "website": "https://techflow.example.com",
    "websiteDisplay": "techflow.example.com",
    "linkedin": "https://www.linkedin.com/in/rahulsharma",
    "linkedinDisplay": "in/rahulsharma",
    "email": "rahul.sharma@techflow.example.com",
    "location": "Bengaluru, India",
}
SHARE_URL = "https://rahulsharma.techflow.example.com"
# ===========================================================

ASSETS_DIR = "/home/z/my-project/android-app/assets"
os.makedirs(ASSETS_DIR, exist_ok=True)


def get_initials(name):
    return "".join(n[0] for n in name.split()[:2]).upper()


# ---------- 1. QR code ----------
qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
qr.add_data(SHARE_URL)
qr.make(fit=True)
qr_img = qr.make_image(fill_color="#08070d", back_color="white")
buf = io.BytesIO()
qr_img.save(buf, format="PNG")
qr_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
print(f"QR generated for: {SHARE_URL} ({len(qr_b64)} chars)")

# ---------- 2. Avatar ----------
BG = (8, 7, 13)
GRAD_START = (217, 70, 239)
GRAD_MID = (139, 92, 246)
GRAD_END = (34, 211, 238)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def make_gradient(size):
    img = Image.new("RGB", (size, size), BG)
    px = img.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * (size - 1))
            if t < 0.5:
                c = lerp(GRAD_START, GRAD_MID, t * 2)
            else:
                c = lerp(GRAD_MID, GRAD_END, (t - 0.5) * 2)
            px[x, y] = c
    return img


def find_font(size_px):
    for c in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]:
        if os.path.exists(c):
            return ImageFont.truetype(c, size_px)
    return ImageFont.load_default()


size = 240
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
grad = make_gradient(size)
mask = Image.new("L", (size, size), 0)
d = ImageDraw.Draw(mask)
d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=255)
ring = Image.new("RGBA", (size, size), (0, 0, 0, 0))
ring.paste(grad, (0, 0), mask)
img = Image.alpha_composite(img, ring)
inner_size = int(size * 0.72)
inner_off = (size - inner_size) // 2
inner = Image.new("RGBA", (inner_size, inner_size), (0, 0, 0, 0))
id_ = ImageDraw.Draw(inner)
id_.rounded_rectangle([0, 0, inner_size - 1, inner_size - 1], radius=int(inner_size * 0.20), fill=BG + (255,))
img.paste(inner, (inner_off, inner_off), inner)
d = ImageDraw.Draw(img)
font = find_font(int(size * 0.34))
text = get_initials(CARD["name"])
bbox = d.textbbox((0, 0), text, font=font)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
tx = (size - tw) // 2 - bbox[0]
ty = (size - th) // 2 - bbox[1]
grad_text = make_gradient(size)
alpha = Image.new("L", (size, size), 0)
ad = ImageDraw.Draw(alpha)
ad.text((tx, ty), text, font=font, fill=255)
grad_text.putalpha(alpha)
img = Image.alpha_composite(img, grad_text)

buf = io.BytesIO()
img.save(buf, format="PNG")
avatar_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
print(f"Avatar generated ({len(avatar_b64)} chars)")

# ---------- 3. card.html ----------
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<meta name="theme-color" content="#08070d">
<title>{CARD["name"]} — Digital Visiting Card</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }}
  html, body {{ background: #08070d; color: #fff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; min-height: 100vh; min-height: 100dvh; -webkit-font-smoothing: antialiased; }}
  body {{ background: radial-gradient(circle at 15% 10%, rgba(217,70,239,0.18), transparent 45%), radial-gradient(circle at 85% 35%, rgba(34,211,238,0.18), transparent 45%), radial-gradient(circle at 50% 90%, rgba(139,92,246,0.18), transparent 50%), #08070d; background-attachment: fixed; padding: 24px 16px 32px; padding-top: max(24px, env(safe-area-inset-top)); padding-bottom: max(32px, env(safe-area-inset-bottom)); }}
  .wrap {{ max-width: 440px; margin: 0 auto; }}
  .badge {{ display: flex; align-items: center; justify-content: center; gap: 6px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 999px; padding: 6px 14px; width: fit-content; margin: 0 auto 20px; backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); font-size: 11px; font-weight: 500; letter-spacing: 0.04em; color: rgba(255,255,255,0.7); }}
  .badge .dot {{ width: 5px; height: 5px; border-radius: 50%; background: #d946ef; }}
  .card {{ background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 24px; padding: 28px 22px; backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); box-shadow: 0 20px 60px rgba(0,0,0,0.5); }}
  .avatar-wrap {{ position: relative; width: 96px; height: 96px; margin: 0 auto 16px; }}
  .avatar-wrap::before {{ content: ''; position: absolute; inset: -3px; border-radius: 50%; background: linear-gradient(135deg, #d946ef, #8b5cf6, #22d3ee); filter: blur(8px); opacity: 0.7; z-index: -1; }}
  .avatar {{ width: 96px; height: 96px; border-radius: 50%; border: 2px solid transparent; background: linear-gradient(135deg, #d946ef, #8b5cf6, #22d3ee) padding-box, linear-gradient(135deg, #d946ef, #8b5cf6, #22d3ee) border-box; display: flex; align-items: center; justify-content: center; background-color: #0d0b14; }}
  .avatar img {{ width: 100%; height: 100%; border-radius: 50%; object-fit: cover; }}
  .status {{ position: absolute; bottom: 4px; right: 4px; width: 16px; height: 16px; border-radius: 50%; background: #34d399; border: 3px solid #08070d; }}
  h1 {{ font-size: 26px; font-weight: 700; text-align: center; letter-spacing: -0.02em; }}
  .title {{ font-size: 14px; color: rgba(255,255,255,0.7); text-align: center; margin-top: 4px; }}
  .company {{ display: inline-flex; align-items: center; gap: 6px; background: rgba(217,70,239,0.1); border: 1px solid rgba(217,70,239,0.3); color: #f5d0fe; font-size: 12px; font-weight: 600; padding: 4px 12px; border-radius: 999px; margin: 10px auto 0; }}
  .company-wrap {{ text-align: center; }}
  .location {{ display: flex; align-items: center; justify-content: center; gap: 4px; font-size: 11px; color: rgba(255,255,255,0.5); margin-top: 8px; }}
  .divider {{ height: 1px; margin: 22px 0; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent); }}
  .qr-panel {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 18px; text-align: center; }}
  .qr-label {{ display: flex; align-items: center; justify-content: center; gap: 6px; font-size: 11px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: rgba(255,255,255,0.6); margin-bottom: 12px; }}
  .qr-box {{ display: inline-block; background: #fff; padding: 12px; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.3); }}
  .qr-box img {{ width: 180px; height: 180px; display: block; }}
  .qr-hint {{ font-size: 10px; color: rgba(255,255,255,0.4); margin-top: 10px; line-height: 1.4; }}
  .actions {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 20px; }}
  .action {{ display: flex; flex-direction: column; align-items: flex-start; gap: 8px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; padding: 14px; text-decoration: none; color: #fff; transition: background 0.15s, transform 0.1s; position: relative; overflow: hidden; }}
  .action:active {{ transform: scale(0.97); }}
  .action:hover {{ background: rgba(255,255,255,0.08); }}
  .action .icon {{ width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #fff; }}
  .action.call .icon {{ background: linear-gradient(135deg, #10b981, #16a34a); }}
  .action.whatsapp .icon {{ background: linear-gradient(135deg, #22c55e, #14b8a6); }}
  .action.website .icon {{ background: linear-gradient(135deg, #06b6d4, #2563eb); }}
  .action.linkedin .icon {{ background: linear-gradient(135deg, #0ea5e9, #4f46e5); }}
  .action .label {{ font-size: 13px; font-weight: 600; }}
  .action .sub {{ font-size: 10px; color: rgba(255,255,255,0.5); max-width: 130px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .secondary {{ display: flex; gap: 10px; margin-top: 10px; }}
  .btn {{ flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); color: rgba(255,255,255,0.9); font-size: 13px; font-weight: 600; padding: 12px; border-radius: 12px; cursor: pointer; transition: background 0.15s, transform 0.1s; }}
  .btn:active {{ transform: scale(0.97); }}
  .btn:hover {{ background: rgba(255,255,255,0.08); }}
  .btn.success {{ color: #34d399; border-color: rgba(52,211,153,0.3); }}
  .footer {{ text-align: center; font-size: 10px; color: rgba(255,255,255,0.3); margin-top: 20px; }}
  svg {{ width: 18px; height: 18px; }}
  .btn svg {{ width: 15px; height: 15px; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="badge"><span class="dot"></span>Digital Visiting Card</div>

  <div class="card">
    <div class="avatar-wrap">
      <div class="avatar"><img src="data:image/png;base64,{avatar_b64}" alt="Avatar"></div>
      <span class="status"></span>
    </div>
    <h1>{CARD["name"]}</h1>
    <div class="title">{CARD["title"]}</div>
    <div class="company-wrap"><span class="company">{CARD["company"]}</span></div>
    <div class="location">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
      {CARD["location"]}
    </div>

    <div class="divider"></div>

    <div class="qr-panel">
      <div class="qr-label">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:13px;height:13px"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><path d="M14 14h7v7h-7z"/></svg>
        Scan to open this card
      </div>
      <div class="qr-box"><img src="data:image/png;base64,{qr_b64}" alt="QR code"></div>
      <div class="qr-hint">Point your phone camera at this QR to instantly open the card on any device.</div>
    </div>

    <div class="actions">
      <a class="action call" href="tel:{CARD["phone"]}">
        <div class="icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg></div>
        <div><div class="label">Call</div><div class="sub">{CARD["phoneDisplay"]}</div></div>
      </a>
      <a class="action whatsapp" href="https://wa.me/{CARD["whatsapp"]}" target="_blank" rel="noopener">
        <div class="icon"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.149-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.149-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51l-.57-.01c-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.247-.694.247-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413z"/></svg></div>
        <div><div class="label">WhatsApp</div><div class="sub">Chat now</div></div>
      </a>
      <a class="action website" href="{CARD["website"]}" target="_blank" rel="noopener">
        <div class="icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg></div>
        <div><div class="label">Website</div><div class="sub">{CARD["websiteDisplay"]}</div></div>
      </a>
      <a class="action linkedin" href="{CARD["linkedin"]}" target="_blank" rel="noopener">
        <div class="icon"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg></div>
        <div><div class="label">LinkedIn</div><div class="sub">{CARD["linkedinDisplay"]}</div></div>
      </a>
    </div>

    <div class="secondary">
      <button class="btn" id="saveBtn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        Save Contact
      </button>
      <button class="btn" id="shareBtn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
        Share
      </button>
    </div>
  </div>

  <div class="footer">Tap a button to connect · Scan the QR to share</div>
</div>

<script>
  var CARD = {json.dumps(CARD, ensure_ascii=False)};
  var SHARE_URL = "{SHARE_URL}";

  document.getElementById('saveBtn').addEventListener('click', function() {{
    var vcard = [
      'BEGIN:VCARD', 'VERSION:3.0',
      'N:' + CARD.lastName + ';' + CARD.firstName + ';;;',
      'FN:' + CARD.name,
      'ORG:' + CARD.company,
      'TITLE:' + CARD.title,
      'TEL;TYPE=CELL:' + CARD.phone,
      'EMAIL;TYPE=WORK:' + CARD.email,
      'URL:' + CARD.website,
      'URL;type=LinkedIn:' + CARD.linkedin,
      'ADR;TYPE=WORK:;;' + CARD.location + ';;;;',
      'END:VCARD'
    ].join('\\r\\n');
    var blob = new Blob([vcard], {{ type: 'text/vcard;charset=utf-8' }});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = CARD.firstName + '_' + CARD.lastName + '.vcf';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }});

  var shareBtn = document.getElementById('shareBtn');
  shareBtn.addEventListener('click', function() {{
    var data = {{
      title: CARD.name + ' — Digital Visiting Card',
      text: 'Connect with ' + CARD.name + ', ' + CARD.title + ' at ' + CARD.company + '.',
      url: SHARE_URL
    }};
    if (navigator.share) {{
      navigator.share(data).catch(function() {{}});
    }} else if (navigator.clipboard) {{
      navigator.clipboard.writeText(SHARE_URL).then(function() {{
        shareBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Copied!';
        shareBtn.classList.add('success');
        setTimeout(function() {{
          shareBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg> Share';
          shareBtn.classList.remove('success');
        }}, 2000);
      }});
    }}
  }});
</script>
</body>
</html>
"""

out_path = os.path.join(ASSETS_DIR, "card.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"card.html written: {len(html)} chars -> {out_path}")
