import 'dotenv/config';
import express, { Request, Response } from 'express';
import http from 'http';
import { spawn, spawnSync, ChildProcessWithoutNullStreams } from 'child_process';
import { WebSocketServer, WebSocket } from 'ws';

const app = express();
const server = http.createServer(app);
const HOST = process.env.HOST || '127.0.0.1';
const PORT = Number(process.env.PORT || 3000);
const BACKEND_HOST = process.env.BACKEND_HOST || '127.0.0.1';
const BACKEND_PORT = Number(process.env.BACKEND_PORT || 8000);
let backendProcess: ChildProcessWithoutNullStreams | null = null;
let backendReady = false;
let backendOwned = false;

app.use(express.json());

function pythonCommand() {
  const venvCandidates = process.platform === 'win32'
    ? ['./.venv/Scripts/python.exe', './.venv/Scripts/python']
    : ['./.venv/bin/python'];
  for (const candidate of venvCandidates) {
    try {
      const r = spawnSync(candidate, ['--version'], { encoding: 'utf8' });
      if (r.status === 0) return candidate;
    } catch {}
  }
  for (const candidate of process.platform === 'win32' ? ['python', 'py', 'python3'] : ['python3', 'python']) {
    try {
      const r = spawnSync(candidate, ['--version'], { encoding: 'utf8' });
      if (r.status === 0) return candidate;
    } catch {}
  }
  return process.platform === 'win32' ? 'python' : 'python3';
}

async function isBackendAlreadyRunning() {
  try {
    const response = await fetch(`http://${BACKEND_HOST}:${BACKEND_PORT}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

async function startFastAPI() {
  if (backendProcess || backendReady) return;
  if (await isBackendAlreadyRunning()) {
    backendReady = true;
    backendOwned = false;
    console.log(`[ResilientEdge] Using existing FastAPI at http://${BACKEND_HOST}:${BACKEND_PORT}`);
    return;
  }
  const py=pythonCommand();
  backendOwned = true;
  backendProcess=spawn(py,['-m','uvicorn','backend.api.fastapi_app:app','--host',BACKEND_HOST,'--port',String(BACKEND_PORT)],{cwd:process.cwd(),env:{...process.env,PYTHONUNBUFFERED:'1'}});
  backendProcess.stdout.on('data',(d)=>console.log(`[FastAPI] ${d.toString().trim()}`));
  backendProcess.stderr.on('data',(d)=>console.log(`[FastAPI] ${d.toString().trim()}`));
  backendProcess.on('exit',()=>{ backendProcess=null; backendReady=false; backendOwned=false; });
}

function proxyToFastAPI(req: Request,res: Response,targetPath=req.originalUrl) {
  const proxy=http.request({hostname:BACKEND_HOST,port:BACKEND_PORT,path:targetPath,method:req.method,headers:{...req.headers,host:`${BACKEND_HOST}:${BACKEND_PORT}`},timeout:5000},(upstream)=>{
    res.writeHead(upstream.statusCode||500,upstream.headers); upstream.pipe(res);
  });
  proxy.on('timeout',()=>{proxy.destroy(); if(!res.headersSent) res.status(504).json({detail:'Backend timeout'});});
  proxy.on('error',(e)=>{if(!res.headersSent) res.status(503).json({detail:'FastAPI unavailable',error:e.message});});
  if(req.body && Object.keys(req.body).length){const body=JSON.stringify(req.body);proxy.setHeader('Content-Type','application/json');proxy.setHeader('Content-Length',Buffer.byteLength(body));proxy.write(body);}
  proxy.end();
}

app.use('/api', (req,res)=>proxyToFastAPI(req,res));
app.use('/health', (req,res)=>proxyToFastAPI(req,res,'/health'));
app.use('/robots', (req,res)=>proxyToFastAPI(req,res));
app.use('/tasks', (req,res)=>proxyToFastAPI(req,res));
app.use('/faults', (req,res)=>proxyToFastAPI(req,res));
app.use('/scenarios', (req,res)=>proxyToFastAPI(req,res));
app.use('/experiments', (req,res)=>proxyToFastAPI(req,res));
app.use('/settings', (req,res)=>proxyToFastAPI(req,res));
app.use('/database', (req,res)=>proxyToFastAPI(req,res));

const wss=new WebSocketServer({server,path:'/ws/telemetry'});
wss.on('connection',(client,request)=>{
  const url=new URL(request.url||'/ws/telemetry',`http://${request.headers.host||HOST}`);
  const token=url.searchParams.get('access_token');
  const demoRole=url.searchParams.get('demo_role');
  const params=new URLSearchParams();
  if(token) params.set('access_token', token);
  if(demoRole) params.set('demo_role', demoRole);
  const query=params.toString();
  const backendUrl=`ws://${BACKEND_HOST}:${BACKEND_PORT}/ws/telemetry${query ? `?${query}` : ''}`;
  const upstream=new WebSocket(backendUrl);
  upstream.on('open',()=>{});
  upstream.on('message',(data,isBinary)=>{if(client.readyState===WebSocket.OPEN) client.send(data,{binary:isBinary});});
  upstream.on('close',()=>{if(client.readyState===WebSocket.OPEN) client.close();});
  upstream.on('error',()=>{if(client.readyState===WebSocket.OPEN) client.close(1011,'Backend websocket unavailable');});
  client.on('message',(data,isBinary)=>{if(upstream.readyState===WebSocket.OPEN) upstream.send(data,{binary:isBinary});});
  client.on('close',()=>upstream.close());
});

async function waitForBackend() {
  await startFastAPI();
  for(let i=0;i<30;i++) {
    await new Promise(r=>setTimeout(r,300));
    try {
      const r=await fetch(`http://${BACKEND_HOST}:${BACKEND_PORT}/health`);
      if(r.ok){backendReady=true; console.log(`[ResilientEdge] FastAPI ready at http://${BACKEND_HOST}:${BACKEND_PORT}`); return;}
    } catch {}
  }
  console.error('[ResilientEdge] FastAPI did not become ready within the startup window.');
}

async function start() {
  await waitForBackend();
  if(process.env.NODE_ENV!=='production') {
    const {createServer}=await import('vite');
    const vite=await createServer({server:{middlewareMode:true},appType:'spa'});
    app.use(vite.middlewares);
  } else {
    app.use(express.static('dist'));
    app.get('*',(_req,res)=>res.sendFile('index.html',{root:'dist'}));
  }
  server.listen(PORT,HOST,()=>console.log(`[ResilientEdge] UI host http://${HOST}:${PORT}`));
}

process.on('SIGINT',()=>{if(backendOwned) backendProcess?.kill();process.exit(0)});
process.on('SIGTERM',()=>{if(backendOwned) backendProcess?.kill();process.exit(0)});
start().catch(err=>{console.error(err);process.exit(1)});
