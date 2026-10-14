#!/usr/bin/env python3
"""Real Chromium integration. Browser <> Python WSS controller; synthetic WebAudio.
Does not test Asterisk or PSTN. Requires playwright+Chromium, websockets, openssl.
"""
import asyncio
import os
import secrets
import socket
import subprocess
import tempfile
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parent.parent

def port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0));return s.getsockname()[1]

async def until_line(proc,text,timeout=8):
    async def read():
        result=[]
        while True:
            line=await proc.stdout.readline()
            if not line:raise RuntimeError('Process exited: '+''.join(result))
            result.append(line.decode(errors='replace'))
            if text in result[-1]:return ''.join(result)
    return await asyncio.wait_for(read(),timeout)

async def main():
    server_port,bot_port=port(),port()
    with tempfile.TemporaryDirectory(prefix='dialtone-browser-') as tmp:
        cert,key=Path(tmp)/'cert.pem',Path(tmp)/'key.pem'
        subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-sha256','-nodes','-days','1',
                        '-keyout',str(key),'-out',str(cert),'-subj','/CN=localhost',
                        '-addext','subjectAltName=DNS:localhost,IP:127.0.0.1'],check=True,capture_output=True)
        token=secrets.token_urlsafe(40)
        server=await asyncio.create_subprocess_exec('node','server.js',cwd=ROOT,env={**os.environ,'PORT':str(server_port)},stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
        bot=await asyncio.create_subprocess_exec('python',str(ROOT/'bot/controller.py'),'--port',str(bot_port),
                 '--token',token,'--cert',str(cert),'--key',str(key),'--noninteractive','--demo-target','1002',
                 stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
        try:
            await until_line(server,'AI Dial-Tone Browser SIP Lab')
            await until_line(bot,'Controller listening')
            async with async_playwright() as p:
                browser=await p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,
                    args=['--no-sandbox','--ignore-certificate-errors','--autoplay-policy=no-user-gesture-required'])
                try:
                    page=await browser.new_page()
                    faults=[]
                    page.on('pageerror',lambda e:faults.append(str(e)))
                    await page.goto(f'http://127.0.0.1:{server_port}',wait_until='domcontentloaded')
                    assert 'Web Lab' in await page.title()
                    assert await page.locator('#agentstate').inner_text()=='OFFLINE'
                    await page.locator('#agenturl').fill(f'wss://localhost:{bot_port}/')
                    await page.locator('#agenttoken').fill(token)
                    await page.locator('#agentconnect').click()
                    await page.wait_for_timeout(100)
                    assert 'APPLY_ALLOWLIST_AND_ARM_FIRST' in await page.locator('#trace').inner_text()
                    await page.locator('#arm').check()
                    await page.locator('#apply').click()
                    await page.locator('#agentconnect').click()
                    await page.wait_for_function("document.querySelector('#agentstate').textContent==='PAIRED'",timeout=8000)
                    await page.wait_for_timeout(500)
                    assert 'call.answered' not in await page.locator('#trace').inner_text()
                    assert not faults, faults
                    print('PASS: Real Chromium UI + WSS bot pairing, pre-arm denial, and no SIP call')

                    # Real AudioWorklet processing with synthetic remote WebRTC audio.
                    result=await page.evaluate('''async () => {
                      const {BotAudio}=await import('/bot-audio.js');
                      const oscCtx=new AudioContext({sampleRate:48000});
                      const osc=oscCtx.createOscillator();osc.frequency.value=440;
                      const remote=oscCtx.createMediaStreamDestination();osc.connect(remote);osc.start();
                      const audio=document.querySelector('#remote');audio.srcObject=remote.stream;
                      const sender={track:remote.stream.getAudioTracks()[0],async replaceTrack(t){this.track=t;}};
                      const original=sender.track;
                      let frames=0;const engine=new BotAudio({onFrame:(buf)=>{if(buf.byteLength===640)frames++;}});
                      engine.peerConnection={connectionState:'connected',getSenders(){return [sender];}};
                      await engine.start(audio);
                      const injectedTrack=sender.track!==original && sender.track.readyState==='live';
                      const samples=new Int16Array(320);for(let i=0;i<320;i++)samples[i]=Math.round(5000*Math.sin(2*Math.PI*440*i/16000));
                      for(let j=0;j<6;j++){const buf=samples.buffer.slice(0);engine.push(buf);await new Promise(r=>setTimeout(r,20));}
                      await new Promise(r=>setTimeout(r,300));
                      await engine.stop();const restored=sender.track===original;
                      osc.stop();await oscCtx.close();audio.srcObject=null;
                      return {frames,injectedTrack,restored};
                    }''')
                    print('Synthetic audio result:',result)
                    assert result['frames']>=8,result
                    assert result['injectedTrack'] and result['restored'],result
                    assert not faults,faults
                    print('PASS: Real AudioWorklet capture, 16-kHz PCM, outgoing track replacement and restoration')
                finally:await browser.close()
        finally:
            for proc in (server,bot):
                if proc.returncode is None:
                    proc.terminate()
                    try:await asyncio.wait_for(proc.wait(),2)
                    except asyncio.TimeoutError:proc.kill();await proc.wait()

if __name__=='__main__':asyncio.run(main())
