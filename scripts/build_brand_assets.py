"""Optional brand-asset regeneration. Requires Pillow; no generated photography."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
FONTS=Path('/usr/share/fonts/truetype/dejavu')
def font(size,bold=False,serif=False):
    name='DejaVuSerif.ttf' if serif else ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')
    try:return ImageFont.truetype(str(FONTS/name),size)
    except OSError:return ImageFont.load_default(size=size)

im=Image.new('RGB',(1600,440),'#f2f5e9');d=ImageDraw.Draw(im)
d.rounded_rectangle((48,48,114,114),radius=18,fill='#244b43')
for x,y,c in [(65,65,'#dcebc7'),(85,65,'#dcebc7'),(65,85,'#dcebc7'),(85,85,'#ffffff')]:d.rectangle((x,y,x+12,y+12),fill=c)
d.text((137,67),'A CLINICAL EVIDENCE WORKSPACE',font=font(18,True),fill='#677a5c')
d.text((48,142),'CareContext.',font=font(77,serif=True),fill='#244b43')
d.text((53,250),'Every statement has a source.',font=font(28),fill='#53694b')
d.text((53,337),'SYNTHETIC RECORDS   /   DATED CITATIONS   /   HUMAN REVIEW',font=font(15,True),fill='#6f7f64')
d.line((955,50,955,390),fill='#d1dcc6',width=2)
for i,(label,detail) in enumerate([('01   ASK THE RECORD','A question, scoped to one case'),('02   FOLLOW THE CITATION','The original words. The original date.'),('03   KEEP THE CONTEXT','Differing entries stay visible')]):
    y=48+i*116
    d.rounded_rectangle((1000,y,1548,y+98),radius=15,fill='#ffffff',outline='#d5dfcb',width=2)
    d.text((1026,y+19),label,font=font(17,True),fill='#244b43')
    d.text((1026,y+53),detail,font=font(17),fill='#74816d')
out=ROOT/'docs/assets/carecontext-banner.png';im.save(out,optimize=True)
print(out)
