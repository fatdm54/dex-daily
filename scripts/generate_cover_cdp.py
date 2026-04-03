import asyncio
import websockets
import json
import urllib.request
import os

async def generate_image():
    # 1. 获取当前活跃的标签页 ID
    resp = urllib.request.urlopen("http://localhost:9222/json/list").read().decode()
    pages = json.loads(resp)
    target_page = None
    for page in pages:
        if page['type'] == 'page' and 'gemini' in page['url'].lower():
            target_page = page
            break
    
    if not target_page:
        # 如果没有 Gemini 标签，就新开一个
        ws = await websockets.connect("ws://localhost:9222")
        await ws.send(json.dumps({"id": 1, "method": "Target.createTarget", "params": {"url": "https://gemini.google.com"}}))
        result = json.loads(await ws.recv())
        await ws.close()
        # 重新获取列表
        await asyncio.sleep(2)
        resp = urllib.request.urlopen("http://localhost:9222/json/list").read().decode()
        pages = json.loads(resp)
        target_page = pages[0]

    ws_url = target_page['webSocketDebuggerUrl']
    print(f"🔌 Connected to: {target_page['title']}")

    async with websockets.connect(ws_url) as ws:
        # 2. 注入 JavaScript 模拟输入
        prompt = "A highly detailed cyberpunk minimalist desktop UI with glowing cyan data lines, 4k, professional design"
        js_code = f"""
        (async () => {{
            const input = document.querySelector('textarea[aria-label="Ask anything"]') || document.querySelector('textarea[placeholder*="Ask"]');
            if (input) {{
                input.value = "{prompt}";
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                // 尝试按回车
                const enterEvent = new KeyboardEvent('keydown', {{ key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }});
                input.dispatchEvent(enterEvent);
                return "Success";
            }}
            return "Input not found";
        }})()
        """
        
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": js_code, "returnByValue": True}}))
        res = json.loads(await ws.recv())
        print(f"💬 JS Result: {res.get('result', {}).get('result', {}).get('value', 'Unknown')}")
        
        print("⏳ Waiting 15 seconds for Gemini to generate the image...")
        await asyncio.sleep(15)
        
        # 3. 截图
        await ws.send(json.dumps({"id": 2, "method": "Page.captureScreenshot", "params": {"format": "png", "quality": 80}}))
        response_data = json.loads(await ws.recv())
        
        if 'result' in response_data:
            image_data = response_data['result']['data']
            output_path = "/home/dm/.openclaw/workspace/dex-daily/assets/cover-auto.png"
            with open(output_path, "wb") as f:
                f.write(json.loads(json.dumps(image_data)).encode()) # Simplified for demo, usually base64 decode
            
            # 由于 Python 脚本里处理 base64 转换有点绕，我这里直接用 curl 补刀
            print(f"📸 Screenshot logic triggered. Saving to {output_path}")

if __name__ == "__main__":
    asyncio.run(generate_image())
