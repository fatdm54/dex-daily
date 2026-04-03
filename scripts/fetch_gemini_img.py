import asyncio
import websockets
import json
import urllib.request
import base64

async def fetch_gemini_image():
    # 1. 获取 CDP 连接
    resp = urllib.request.urlopen("http://localhost:9222/json/list").read().decode()
    pages = json.loads(resp)
    target_page = next((p for p in pages if 'gemini' in p['url'].lower()), None)
    
    if not target_page:
        print("❌ Gemini page not found. Is the browser open?")
        return

    ws_url = target_page['webSocketDebuggerUrl']
    print(f"🔌 Connected to: {target_page['title']}")

    async with websockets.connect(ws_url) as ws:
        # 2. 寻找图片链接
        js_code = """
        (() => {
            // 尝试找 Gemini 生成的图片
            const imgs = document.querySelectorAll('img');
            for (let img of imgs) {
                if (img.src.startsWith('https://lh3.googleusercontent.com') || img.src.startsWith('https://generativelanguage.googleapis.com')) {
                    return img.src;
                }
            }
            return null;
        })()
        """
        
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": js_code, "returnByValue": True}}))
        res = json.loads(await ws.recv())
        img_url = res.get('result', {}).get('result', {}).get('value')
        
        if img_url:
            print(f"🖼️ Found image URL: {img_url[:60]}...")
            # 3. 下载图片
            try:
                data = urllib.request.urlopen(img_url).read()
                with open("/home/dm/.openclaw/workspace/dex-daily/assets/cover-new.png", "wb") as f:
                    f.write(data)
                print("💾 Image saved successfully!")
            except Exception as e:
                print(f"❌ Download failed: {e}")
        else:
            print("⚠️ No generated image found. Taking a screenshot of the whole page just in case...")
            await ws.send(json.dumps({"id": 2, "method": "Page.captureScreenshot", "params": {"format": "png"}}))
            response_data = json.loads(await ws.recv())
            if 'result' in response_data:
                img_b64 = response_data['result']['data']
                with open("/home/dm/.openclaw/workspace/dex-daily/assets/cover-new.png", "wb") as f:
                    f.write(base64.b64decode(img_b64))
                print("💾 Screenshot saved as fallback.")

if __name__ == "__main__":
    asyncio.run(fetch_gemini_image())
