from flask import Flask, render_template_string

app = Flask(__name__)

HTML_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Pose Rep Counter • Teachable Machine</title>
    <style>
        :root{
            --bg:#0f1720; --card:#0b1220; --accent:#20c997; --muted:#94a3b8; --glass: rgba(255,255,255,0.04);
            font-family: Inter, system-ui, -apple-system, Roboto, 'Segoe UI', Arial;
        }
        body{margin:0; min-height:100vh; background:linear-gradient(180deg,#071026 0%, #07182a 100%); color:#e6eef6; display:flex; align-items:center; justify-content:center; padding:24px}
        .container{width:100%; max-width:980px;}
        .card{background:var(--card); border-radius:12px; padding:18px; box-shadow: 0 6px 28px rgba(2,6,23,0.6);} 
        header{display:flex; align-items:center; justify-content:space-between; gap:12px}
        h1{font-size:20px; margin:0}
        .controls{display:flex; gap:8px; align-items:center}
        button{background:var(--accent); color:#012; border:none; padding:8px 12px; border-radius:8px; cursor:pointer; font-weight:600}
        button.secondary{background:transparent; border:1px solid rgba(255,255,255,0.06); color:var(--muted)}
        button:disabled{opacity:0.5; cursor:not-allowed}
        .grid{display:grid; grid-template-columns: 1fr 300px; gap:16px; margin-top:14px}
        .video-wrap{background:var(--glass); border-radius:10px; padding:12px; display:flex; flex-direction:column; align-items:center}
        canvas{width:100%; height:auto; border-radius:8px; background:#081022}
        .sidebar{display:flex; flex-direction:column; gap:10px}
        .stat{background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); padding:10px; border-radius:8px}
        .big{font-size:36px; font-weight:700; color:var(--accent)}
        .labels{font-family:monospace; font-size:13px; color:var(--muted); max-height:220px; overflow:auto}
        .footer{margin-top:12px; text-align:center; color:var(--muted); font-size:13px}
        @media (max-width:880px){ .grid{grid-template-columns:1fr; } .sidebar{order:2} }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <header>
                <h1>Teachable Machine • Pose Counter</h1>
                <div class="controls">
                    <button id="startBtn">Start</button>
                    <button id="stopBtn" class="secondary" disabled>Stop</button>
                    <button id="resetBtn" class="secondary">Reset</button>
                </div>
            </header>

            <div class="grid">
                <div class="video-wrap">
                    <div style="width:100%; max-width:720px">
                        <canvas id="canvas"></canvas>
                    </div>
                    <div style="display:flex; gap:12px; width:100%; justify-content:center; margin-top:10px;">
                        <div class="stat" style="flex:1; text-align:center">
                            <div style="font-size:12px; color:var(--muted)">Reps</div>
                            <div id="rep-count" class="big">0</div>
                        </div>
                        <div class="stat" style="width:110px; text-align:center">
                            <div style="font-size:12px; color:var(--muted)">Confidence</div>
                            <div id="conf-val" class="big">0%</div>
                        </div>
                    </div>
                </div>

                <aside class="sidebar">
                    <div class="stat">
                        <div style="font-weight:600">Model: <span id="model-name">—</span></div>
                        <div style="font-size:13px; color:var(--muted); margin-top:6px">Tip: Train "Up" and "Down" (or your own pair) in Teachable Machine. Use a reasonably high confidence threshold.</div>
                    </div>

                    <div class="stat">
                        <div style="font-weight:600; margin-bottom:6px">Realtime Labels</div>
                        <div id="label-container" class="labels">Waiting…</div>
                    </div>

                    <div class="stat">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="font-weight:600">Settings</div>
                        </div>
                        <div style="margin-top:8px; font-size:13px; color:var(--muted)">
                            Confidence threshold: <input id="confThreshold" type="range" min="0" max="100" value="70"> <span id="confText">70%</span>
                        </div>
                    </div>
                </aside>
            </div>

            <div class="footer">Status: <span id="status">Idle</span> • FPS: <span id="fps">0</span></div>
        </div>
    </div>

    <!-- Use versions that are compatible with the teachablemachine pose lib -->
    <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@1.3.1"></script>
    <script src="https://cdn.jsdelivr.net/npm/@teachablemachine/pose@0.8/dist/teachablemachine-pose.min.js"></script>
<script>
    // Ensure tmPose is available
    const tmPose = window.tmPose;
</script>

    <script>
        // ---------- CONFIG ----------
        const URL = "/static/my-pose-model/";  // local model path
        const SIZE = 360; // canvas size

        // ---------- STATE ----------
        let model, webcam, ctx, labelContainer, maxPredictions;
        let repCount = 0;
        let downDetected = false;
        let running = false;
        let lastFrameTime = performance.now();
        let fps = 0;

        // ---------- UI refs ----------
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const resetBtn = document.getElementById('resetBtn');
        const repEl = document.getElementById('rep-count');
        const confEl = document.getElementById('conf-val');
        const labelBox = document.getElementById('label-container');
        const modelNameEl = document.getElementById('model-name');
        const statusEl = document.getElementById('status');
        const fpsEl = document.getElementById('fps');
        const confRange = document.getElementById('confThreshold');
        const confText = document.getElementById('confText');

        confRange.addEventListener('input', ()=>{ confText.innerText = confRange.value + '%'; });

        startBtn.addEventListener('click', start);
        stopBtn.addEventListener('click', stop);
        resetBtn.addEventListener('click', ()=>{ repCount=0; downDetected=false; repEl.innerText=repCount; });

        async function start(){
            if(running) return;
            statusEl.innerText = 'Loading model and camera...';
            startBtn.disabled = true;

            try{
                const modelURL = URL + 'model.json';
                const metadataURL = URL + 'metadata.json';
                model = await tmPose.load(modelURL, metadataURL);
                maxPredictions = model.getTotalClasses();
                modelNameEl.innerText = 'my-pose-model';

                webcam = new tmPose.Webcam(SIZE, SIZE, true);
                await webcam.setup();
                await webcam.play();

                const canvas = document.getElementById('canvas');
                canvas.width = SIZE; canvas.height = SIZE;
                ctx = canvas.getContext('2d');

                labelBox.innerHTML = '';
                for (let i = 0; i < maxPredictions; i++) {
                    const el = document.createElement('div');
                    el.style.padding = '4px 6px';
                    labelBox.appendChild(el);
                }

                running = true;
                stopBtn.disabled = false;
                statusEl.innerText = 'Running';
                window.requestAnimationFrame(loop);
            }catch(err){
                console.error(err);
                statusEl.innerText = 'Error: ' + err.message;
                startBtn.disabled = false;
            }
        }

        function stop(){
            running = false;
            stopBtn.disabled = true;
            startBtn.disabled = false;
            statusEl.innerText = 'Stopped';
            if(webcam) webcam.stop();
        }

        async function loop(timestamp){
            if(!running) return;
            const dt = timestamp - lastFrameTime;
            fps = Math.round(1000 / Math.max(1, dt));
            lastFrameTime = timestamp;
            fpsEl.innerText = fps;

            webcam.update();
            await predict();
            window.requestAnimationFrame(loop);
        }

        async function predict(){
            try{
                const { pose, posenetOutput } = await model.estimatePose(webcam.canvas);
                const prediction = await model.predict(posenetOutput);

                let highestProb = 0;
                let predictedClass = '';

                for(let i=0;i<prediction.length;i++){
                    const name = prediction[i].className;
                    const prob = prediction[i].probability;
                    labelBox.childNodes[i].innerText = name + ': ' + (prob*100).toFixed(1) + '%';
                    if(prob > highestProb){ highestProb = prob; predictedClass = name; }
                }

                confEl.innerText = Math.round(highestProb*100) + '%';

                const threshold = Number(confRange.value)/100;
                if(highestProb >= threshold){
                    handleReps(predictedClass);
                }

                drawPose(pose);
            }catch(err){
                console.error('predict error', err);
            }
        }

        let lastRepTime = 0;
        function handleReps(poseClass){
            const now = Date.now();
            const MIN_REP_INTERVAL = 600;

            if(poseClass === 'Down'){
                downDetected = true;
                statusEl.innerText = 'Detected: Down';
            }else if(poseClass === 'Up'){
                if(downDetected && (now - lastRepTime) > MIN_REP_INTERVAL){
                    repCount += 1;
                    repEl.innerText = repCount;
                    lastRepTime = now;
                    downDetected = false;
                    statusEl.innerText = 'Rep counted!';
                }else{
                    statusEl.innerText = 'Detected: Up';
                }
            }else{
                statusEl.innerText = 'Detected: ' + poseClass;
            }
        }

        function drawPose(pose){
            if(!webcam || !ctx) return;
            ctx.clearRect(0,0,SIZE,SIZE);
            ctx.drawImage(webcam.canvas, 0, 0, SIZE, SIZE);
            if(pose){
                const minPartConfidence = 0.45;
                tmPose.drawKeypoints(pose.keypoints, minPartConfidence, ctx);
                tmPose.drawSkeleton(pose.keypoints, minPartConfidence, ctx);
            }
        }

        window.addEventListener('beforeunload', ()=>{ if(webcam) webcam.stop(); });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

if __name__ == '__main__':
    app.run(debug=True)
