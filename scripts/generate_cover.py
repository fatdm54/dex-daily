import asyncio
from playwright.async_api import async_playwright
import os
import time

async def main():
    profile_path = "/home/dm/.config/google-chrome/Profile 1"
    prompt = "A futuristic minimalist desktop UI with glowing blue data lines, symbolizing AI startup, highly detailed, cyberpunk aesthetic, 4k"
    
    print(f"🚀 Starting Chrome with profile: {profile_path}")
    
    async with async_playwright() as p:
        # Launch Chrome attached to the specific user profile
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=False,
            args=[
                '--start-maximized',
                '--no-first-run',
                '--no-default-browser-check'
            ]
        )
        
        # Create a new page
        page = await browser.new_page()
        print("🌐 Navigating to Gemini...")
        
        await page.goto("https://gemini.google.com/")
        
        # Wait for user to be logged in (check for chat input)
        try:
            await page.wait_for_selector('textarea[placeholder*="Ask"]', timeout=15000)
            print("✅ Logged in successfully.")
            
            # Type the prompt
            print("🎨 Generating image prompt...")
            await page.fill('textarea[placeholder*="Ask"]', f"/imagine {prompt}")
            await page.press('textarea[placeholder*="Ask"]', 'Enter')
            
            # Wait for image generation (this might take a while, so we wait for an img tag in the response)
            print("⏳ Waiting for Gemini to generate the image...")
            await page.wait_for_selector('img[src^="https://lh3.googleusercontent.com"]', timeout=60000)
            
            # Get the image source
            img_element = await page.query_selector('img[src^="https://lh3.googleusercontent.com"]')
            img_src = await img_element.get_attribute('src')
            
            print(f"🖼️ Image found: {img_src[:50]}...")
            
            # Download the image
            output_path = "/home/dm/.openclaw/workspace/dex-daily/assets/cover-auto.png"
            async with page.context.request.get(img_src) as response:
                with open(output_path, 'wb') as f:
                    f.write(await response.body())
            
            print(f"💾 Saved to {output_path}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Hint: Make sure you are logged into Gemini in this profile.")
        
        await asyncio.sleep(5) # Keep window open for a moment
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
