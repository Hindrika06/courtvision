# CourtVision 🎾 — Physical Court Pilot Checklist (Phase 29)

Execute each step below sequentially on the real physical court and record observations and video recordings.

---

## 🟩 Phase 29.1 — Baseline & Calibration

### 1. Interactive 4-Point Court Calibration
- [ ] Open `⚙ CALIBRATE COURT` in active profile (`Court 1`).
- [ ] Click the four actual court corners: Far-Left, Far-Right, Near-Right, Near-Left.
- [ ] Save calibration and verify point order and homography $H$ matrix calculation.
- [ ] Verify virtual baseline ads align perfectly with court baseline lines (`10.97m x 23.77m`).

### 2. Empty Court Baseline Test
- [ ] Enable virtual ads on empty court.
- [ ] Record 1–2 minutes continuous video (`recordings/empty_court_baseline.mp4`).
- [ ] Verify court lines remain visually stable with zero ad flickering, drift, or false player masking.

---

## 🏃 Phase 29.2 — Player Protection Field Tests

### 3. Single Player Scenarios
- [ ] **Stationary (Test 9A)**: Player stands directly over virtual ad $\rightarrow$ player original pixels 100% sharp, zero ad bleed on body.
- [ ] **Walking (Test 9B)**: Player walks through baseline ad $\rightarrow$ smooth pixel protection mask.
- [ ] **Running (Test 9C)**: Player runs across court ad $\rightarrow$ IoU tracker maintains continuous protection.
- [ ] **Lunge (Test 9D)**: Deep court lunge $\rightarrow$ extended limbs remain fully protected.
- [ ] **Fast Movement (Test 9E)**: Rapid gameplay movements $\rightarrow$ no transparency, blur, or bounding box artifacts.

### 4. Multi-Player Scenarios
- [ ] Two players cross court baseline ads simultaneously.
- [ ] Players cross paths over virtual ad region.
- [ ] One player stationary while second player moves past.
- [ ] Record clip (`recordings/multi_player.mp4`).

---

## 🏸 Phase 29.3 — Racket & Fine Object Occlusion Tests

### 5. Racket Scenarios
- [ ] Racket held beside torso over virtual ad $\rightarrow$ racket rim/handle protected.
- [ ] Racket extended away from body over baseline ad $\rightarrow$ fine object detector protects racket.
- [ ] Fast forehand & backhand stroke over ad $\rightarrow$ racket frame protected.
- [ ] Overhead smash $\rightarrow$ racket head protected.
- [ ] **Thin Strings**: Observe string segmentation at far distance $\rightarrow$ record `PARTIAL` if strings fall below 1–2 pixels resolution.

---

## 🎨 Phase 29.4 — Live Operator & Ad Switching Tests

### 6. Live Ad Switching During Gameplay
- [ ] Operator switches active graphic from Ad A to Ad B in Advertisement Manager.
- [ ] Verify ad switches immediately without stopping processing or restarting camera stream.
- [ ] Adjust opacity slider live (0.0 to 1.0) and verify real-time blending change.
- [ ] Record clip (`recordings/live_ad_switching.mp4`).

---

## ⏱️ Phase 29.5 — Long-Run & Recording Integrity

### 7. Continuous 30–60 Minute Session
- [ ] Start recording via Desktop UI (`⏺ RECORD VIDEO`).
- [ ] Execute continuous 30+ minute match recording.
- [ ] Record RAM start, RAM end, RAM delta (verify < 10 MB RAM growth).
- [ ] Record average FPS, min FPS, max FPS, dropped frames, reconnect count.
- [ ] Stop recording cleanly and verify saved file in `output/` directory.

### 8. Post-Session Recording Output Verification
- [ ] Open recorded MP4 video in external media player (VLC / Windows Media Player).
- [ ] Verify beginning, middle, and end of video file play smoothly without corruption.
- [ ] Confirm composited ads and player protection remain intact throughout recorded file.
