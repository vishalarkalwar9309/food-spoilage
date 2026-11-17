# STEP-BY-STEP PROJECT DEMONSTRATION GUIDE
## Smart Food Storage Spoilage Predictor - College Evaluation & Viva Walkthrough

**Audience:** Evaluators, Professors, IoT Viva Examiners, Project Review Committee  
**Estimated Demonstration Time:** 10 – 15 minutes  
**Two Available Demonstration Modes:**
1. **Mode 1: Pure Software Simulation** (No physical hardware required; uses the built-in sensor simulator).
2. **Mode 2: Physical ESP32 Hardware Integration** (Using ESP32 node with DHT22, MQ-135, LEDs, and Buzzer).

---

## 1. Executive Summary for Evaluators (The 30-Second Pitch)

> *"The Smart Food Storage Spoilage Predictor is an industrial-grade IoT system designed to eliminate perishable agricultural post-harvest loss. Rather than providing generic single-sensor threshold alarms, our system continuously monitors headspace microclimate kinetics—temperature, relative humidity, and volatile amine/senescence gases—and computes a cumulative, stress-weighted spoilage risk score ($0\text{--}100\%$) tailored to specific crop profiles.
> 
> A critical innovation is our **Exposure Persistence Model**: brief fluctuations produce early warnings, whereas sustained unfavorable conditions compound over time using an accelerated stress multiplier ($\alpha = 1.5$), modeling real biological tissue senescence."*

---

## 2. DEMONSTRATION PART 1: Pure Software Simulation Mode (No Hardware Needed)

This mode demonstrates 100% of application capabilities using the built-in sensor simulator.

### Setup (1 minute)
1. Double-click [`start.bat`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/start.bat) in the project root.
2. Confirm the browser opens to `http://localhost:5173`.
3. Verify the top navbar displays:
   - `Simulation Mode` (highlighted in amber).
   - `Stream: SIMULATOR`.
   - `Target HW: ESP32 + DHT22 + MQ-135`.

---

### Step 1: Baseline Storage Conditions (Optimal Envelope)
1. In the **Commodity Profile Management** section, ensure **Rice** is selected (or click "Select Profile").
2. In the **Hardware Emulation & Sensor Simulator** dock, click **1. Normal Conditions**.
3. Click **Step Once** (or click **Start Auto-Stream (3.5s)**).
4. **Point out to Evaluators:**
   - Temperature is around $13.5^\circ\text{C}$ (within the optimal $12\text{--}15^\circ\text{C}$ green window).
   - Relative Humidity is around $87\%$ (within the optimal $85\text{--}90\%$ window).
   - MQ-135 Gas response is around $190\text{ ADC}$ (near calibrated clean baseline of $180\text{ ADC}$).
   - The **Radial Risk Gauge** shows **LOW RISK ($\approx 10\text{--}14\%$)** with a green badge.
   - Component scores: $T_s = 0\%$, $H_s = 0\%$, $G_s \approx 4\%$.

---

### Step 2: Inducing Thermal Stress (Elevated Temperature)
1. In the simulator dock, click **2. High Temperature**.
2. Click **Step Once** (or observe the live auto-stream).
3. **Point out to Evaluators:**
   - Temperature jumps to $26\text{--}28^\circ\text{C}$ (well above $T_{max} = 15^\circ\text{C}$).
   - The Temperature card immediately changes badge from **OPTIMAL** to **DEVIATED (+12.5°C Above Max)** in red.
   - Temperature component score ($T_s$) surges to $80\text{--}90\%$.
   - The Composite Risk Score increases to **MODERATE ($\approx 40\text{--}52\%$)** with an amber/yellow badge.
   - Recommendation updates automatically: *"Elevated storage temperature detected (+12.5°C above max). Accelerates enzymatic ripening. Cool container immediately."*

---

### Step 3: Inducing Condensation Risk (High Humidity)
1. In the simulator dock, click **3. High Humidity**.
2. Click **Step Once**.
3. **Point out to Evaluators:**
   - Relative Humidity rises to $>96\%$ (exceeding $H_{max} = 90\%$).
   - The Humidity card displays **DEVIATED (+7.5% Saturation Risk)** in amber.
   - Humidity component score ($H_s$) increases, warning against condensation and mold sporulation.

---

### Step 4: Inducing Metabolic Gas Release (Elevated Headspace VOCs)
1. In the simulator dock, click **4. Elevated Gas**.
2. Click **Step Once**.
3. **Point out to Evaluators:**
   - MQ-135 reading spikes to $420\text{--}480\text{ ADC}$ (crossing the senescence threshold of $400\text{ ADC}$).
   - The MQ-135 card switches from **BASELINE** to **ELEVATED** in red.
   - Gas component score ($G_s$) reaches $100\%$.
   - The Composite Risk advances to **HIGH RISK ($65\text{--}75\%$)**.

---

### Step 5: Inducing Combined Critical Stress & Alert Escalation
1. In the simulator dock, click **5. Combined Stress**.
2. Click **Step Once** 2 to 3 times.
3. **Point out to Evaluators:**
   - All three parameters are severely degraded simultaneously: $T \approx 29^\circ\text{C}$, $H \approx 98\%$, $G \approx 490\text{ ADC}$.
   - The **Radial Risk Gauge** escalates to **CRITICAL RISK ($85\text{--}92\%$)** in red.
   - Scroll to the **Alerts & Event Timeline** panel:
     - Notice a new alert was automatically generated:
       `Storage risk elevated to CRITICAL (88.4%). Relocate produce to cold storage immediately.`
     - Click **Acknowledge** on the alert to show operator acknowledgement and audit trail logging in SQLite!

---

### Step 6: Cumulative Duration Acceleration Demonstration
1. In the **Storage Session Management** card, start a new session named `"Stress Test Batch"`.
2. Keep the simulator running in **Combined Stress** mode for 5 to 6 steps.
3. **Point out to Evaluators:**
   - Notice that the **Cumulative Storage Duration** card tracks **Effective Exposure Hours**.
   - Because $T_s$ and $H_s$ are high, the stress multiplier ($\alpha = 1.5$) accelerates the effective duration accumulation:
     $$\text{Effective Hours} = \Delta t \times (1.0 + 1.5 \times 0.9) = \Delta t \times 2.35$$
   - Effective time accumulates **2.35× faster** than wall-clock time, representing physiological stress!

---

### Step 7: Historical Analytics & Temporal Filtering
1. Scroll to the **Historical Analytics** section.
2. Click the time range toggle buttons:
   - **Last Hour (`1h`)**: Shows granular minute-by-minute fluctuations.
   - **Last 24 Hours (`24h`)**: Shows daily diurnal trends.
   - **Last 7 Days (`7d`)**: Shows macro shelf-life progression.
3. Show the **Safe Storage Envelopes**:
   - The green band on the Temperature chart shows the optimal $[12, 15]^\circ\text{C}$ window.
   - The purple dashed line on the Gas chart shows the $400\text{ ADC}$ senescence threshold.

---

### Step 8: Multi-Crop Profile Switching & Session Isolation
1. In **Commodity Profile Management**, select **Oranges** (\text{--}8^\circ\text{C}$).
2. Click **Start New Storage Session** with profile set to Oranges.
3. **Point out to Evaluators:**
   - All charts and target reference envelopes dynamically adjust: the optimal temperature window changes to $[1, 4]^\circ\text{C}$, and shelf life updates to 720 hours (30 days).
   - Past historical data from previous sessions remains preserved in SQLite without corruption.

---

## 3. DEMONSTRATION PART 2: Physical ESP32 Hardware Integration Mode

If you have connected the physical ESP32 breadboard circuit:

### Setup
1. Switch the top navbar mode toggle from **Simulation Mode** to **Physical ESP32**.
2. Flash the ESP32 using the instructions in [`HARDWARE_GUIDE.md`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/HARDWARE_GUIDE.md).
3. Open the Arduino Serial Monitor at **115200 baud**.

---

### Step 1: Boot Sequence & Sensor Stabilization
1. Press the **EN / RESET** button on the ESP32.
2. Watch the LEDs run a quick self-test chase (Green $\to$ Yellow $\to$ Red).
3. The buzzer emits a crisp 50ms startup confirmation chime.
4. Serial Monitor prints:
   ```
   [OK] DHT Environmental Sensor Initialized.
   [*] Connecting to Wi-Fi: MyHomeWiFi......
   [OK] Wi-Fi Connected! IP: 192.168.0.145 (RSSI: -58 dBm)
   [*] Beginning MQ-135 Heater Stabilization (60 seconds)...
   ```
5. Yellow LED pulses at 1Hz during the 60-second stabilization countdown.

---

### Step 2: Live Ingestion & Low Risk State
1. Once stabilization finishes, the ESP32 enters the acquisition loop.
2. Serial Monitor logs:
   ```
   [HTTP] POST -> http://192.168.0.101:5000/api/sensor-data
   [HTTP] Ingestion Successful (201)
   [BACKEND TRUTH] Risk Category: Low | Score: 12.8%
   ```
3. **Hardware State:** **Green LED illuminates SOLID ON**. Yellow and Red LEDs are OFF. Buzzer is silent.
4. On the web dashboard, the top navbar pulses: `Node: ESP32 Online (ESP32-FOOD-001)`.

---

### Step 3: Triggering Hardware Moderate Risk
1. Hold a warm mug near the DHT22 or breathe onto it for 10 seconds.
2. Temperature climbs above $16^\circ\text{C}$ and humidity rises.
3. Backend calculates **Moderate Risk**.
4. **Hardware State:** Green LED turns OFF; **Yellow LED turns SOLID ON**.

---

### Step 4: Triggering Hardware High Risk
1. Wave a cotton swab lightly dampened with rubbing alcohol (or an unlit lighter) $5\text{ cm}$ in front of the MQ-135.
2. Analog voltage rises through the voltage divider into GPIO 34.
3. Normalized gas reading exceeds $380\text{ ADC}$.
4. Backend evaluates **High Risk ($65\text{--}78\%$)**.
5. **Hardware State:** **Yellow and Red LEDs both illuminate simultaneously**.

---

### Step 5: Triggering Hardware Critical Alert & Audible Buzzer
1. Continue holding the warm, humid air and gas near the sensors.
2. Risk crosses $80\%$ into **Critical Risk**.
3. **Hardware State:**
   - Green & Yellow turn OFF; **Red LED illuminates SOLID ON**.
   - **Buzzer sounds 3 loud warning beeps** ($120\text{ms}$ on / $80\text{ms}$ off).
   - Buzzer enters a **15-second silence cooldown** to prevent noise fatigue.

---

### Step 6: Safe Fallback Behavior (Network Disconnect Test)
1. Turn off Wi-Fi on the laptop or disconnect the network.
2. When the ESP32 attempts its next HTTP POST:
   - `[HTTP] Request failed, code: -1`
   - `[FALLBACK] Backend link unavailable. Entering safe indication state.`
3. **Hardware State:** Green and Red turn OFF; **Yellow LED blinks rapidly at 1Hz**.
4. **Crucial Viva Talking Point:** The node does NOT assume the food is safe; it honestly signals communication loss to the operator!

---

## 4. Viva Examination Questions & Model Answers

### Q1: "Why does your system output a Spoilage Risk Score instead of stating 'Food is Spoiled'?"
> **Model Answer:**  
> *"Non-destructive external IoT sensors measure ambient headspace environmental kinetics (temperature, humidity, volatile off-gases). While these kinetics strongly correlate with biological senescence and mold development, a definitive claim that food is biologically spoiled requires destructive microbiological assay (colony plate counts) or biochemical titrations. Claiming definitive food safety from ambient sensors would be unscientific and legally hazardous. Our system acts as an environmental decision-support tool."*

### Q2: "How does your Cumulative Duration mathematical model work?"
> **Model Answer:**  
> *"Our equation is $R = 0.30 T_s + 0.25 H_s + 0.25 G_s + 0.20 D_s$. The duration component $D_s$ accumulates effective exposure hours using the formula:  
> $$E_{penalty}(t) = 1.0 + \alpha \cdot \frac{\max(T_s, H_s)}{100}$$  
> If conditions are ideal, produce ages at standard wall-clock rate. If temperature or humidity deviates, the commodity-specific stress factor ($\alpha \ge 1.2\text{--}2.0$) multiplies the aging rate. This prevents a storage manager from ignoring a warm refrigerator simply because the current temperature looks acceptable."*

### Q3: "Why is a voltage divider mandatory between the MQ-135 and the ESP32?"
> **Model Answer:**  
> *"The MQ-135 sensor heater requires 5V to achieve operating temperature, and its analog output swings up to 5.0V under high gas concentrations. However, ESP32 ADC pins are rated for a strict maximum of 3.3V and are not 5V-tolerant. Applying 5V directly to GPIO 34 will destroy the internal ADC silicon. We implemented a $10\,\text{k}\Omega / 20\,\text{k}\Omega$ passive voltage divider that limits the maximum input to $3.33\text{V}$, and compensated for the ratio in firmware."*

### Q4: "How does the system prevent data collisions between the simulator and physical hardware?"
> **Model Answer:**  
> *"The backend maintains an explicit operating mode state machine. Every telemetry row in SQLite records its `source` (`'esp32'` vs `'simulator'`) and `device_id`. When physical telemetry arrives from an ESP32 node, the backend automatically transitions to 'Hardware Mode' and terminates the background simulation thread, ensuring physical and synthetic readings never interleave or corrupt historical analytics."*
