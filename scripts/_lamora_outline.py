import re
import urllib.parse
import urllib.request

BASE = "https://wpbingo-lamora.myshopify.com"
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())


def get(url, data=None):
    headers = {"User-Agent": "Mozilla/5.0"}
    if data:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, headers=headers)
    with opener.open(req, timeout=40) as res:
        return res.read().decode("utf-8", "replace")


html = get(BASE + "/password")
token = re.search(r'name="authenticity_token" value="([^"]+)"', html).group(1)
body = urllib.parse.urlencode(
    {"authenticity_token": token, "form_type": "storefront_password", "utf8": "✓", "password": "1"}
).encode()
home = get(BASE + "/password", body)

# Drop scripts/styles for an outline, but keep inline style font-size near headings.
parts = re.split(r"(<section[^>]*>|</section>)", home)
depth = 0
for part in parts:
    if part.startswith("<section"):
        cls = re.search(r'class="([^"]+)"', part)
        name = cls.group(1) if cls else ""
        short = " ".join(name.split()[:4])
        print(f"\nSECTION {short}")
        depth = 1
        continue
    if part == "</section>":
        depth = 0
        continue
    if depth != 1:
        continue
    text = re.sub(r"<script[\s\S]*?</script>", " ", part)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text)
    headings = re.findall(r"<(h[1-4]|p|a|span)[^>]*>([^<]{2,80})</\1>", text)
    seen = []
    for tag, value in headings:
        value = re.sub(r"\s+", " ", value).strip()
        if not value or value in seen or value.startswith("{{"):
            continue
        seen.append(value)
        if len(seen) > 8:
            break
    if seen:
        print(" | ".join(seen[:8]))
