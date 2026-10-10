from curl_cffi import requests
import re
for url in ["https://www.perplexity.ai/changelog", "https://x.ai/news", "https://x.ai/news/team-bots"]:
    for imp in ["chrome", "chrome131", "safari18_0", "edge101", "firefox133"]:
        try:
            r = requests.get(url, impersonate=imp, timeout=30)
            print(url, imp, r.status_code, len(r.text), "challenge" if "Just a moment" in r.text else "", len(set(re.findall(r'/news/[a-z0-9-]+', r.text))))
        except Exception as e:
            print(url, imp, "ERR", str(e)[:60])
