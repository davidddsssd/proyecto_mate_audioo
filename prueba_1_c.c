// --- Definiciones de Pines ---
const int PIN_FREQ_POT = 32;  // ADC1 Channel 4
const int PIN_AMP_POT = 33;   // ADC1 Channel 5
const int PIN_BUTTON = 4;     // Botón para encender/apagar (usará pull-up interno)

// --- Variables de Estado ---
bool audio_state = false;
int last_button_state = HIGH; // Estado inicial del botón (HIGH por pull-up)

// --- Variables para Filtrado y Muestreo ---
// Usamos un simple filtro de promedio móvil para estabilizar la lectura del ADC
const int NUM_READINGS = 5;
int freq_readings[NUM_READINGS];
int amp_readings[NUM_READINGS];
int read_index = 0;

// Variables para evitar enviar datos continuamente (Anti-Chatter)
float last_freq_sent = -1.0;
float last_amp_sent = -1.0;
unsigned long last_send_time = 0;
const long SEND_INTERVAL_MS = 20; // Enviar datos cada 20 ms (50 veces por segundo)
const float FREQ_TOLERANCE = 5.0; // Solo enviar si la Frecuencia cambia más de 5 Hz
const float AMP_TOLERANCE = 0.01; // Solo enviar si la Amplitud cambia más de 0.01 (1%)

// --- SETUP ---
void setup() {
  Serial.begin(115200);
  pinMode(PIN_BUTTON, INPUT_PULLUP); // Activa la resistencia pull-up interna
  
  // Inicializar arrays de promedio
  for (int i = 0; i < NUM_READINGS; i++) {
    freq_readings[i] = analogRead(PIN_FREQ_POT);
    amp_readings[i] = analogRead(PIN_AMP_POT);
  }
}

// --- LOOP ---
void loop() {
  // 1. --- Gestión de Botón ---
  handleButton();

  // 2. --- Lectura y Filtrado de Potenciómetros (ADC) ---
  handleADCReadings();
  
  // 3. --- Mapeo y Envío de Datos por Serial ---
  if (millis() - last_send_time >= SEND_INTERVAL_MS) {
    sendDataToPC();
    last_send_time = millis();
  }
}

// --- FUNCIONES AUXILIARES ---

void handleButton() {
  int current_button_state = digitalRead(PIN_BUTTON);

  // Detectar flanco de bajada (botón presionado)
  if (current_button_state == LOW && last_button_state == HIGH) {
    // Retardo para debounce (antirrebote)
    delay(50); 
    if (digitalRead(PIN_BUTTON) == LOW) {
      audio_state = !audio_state; // Toggle el estado
      
      // Enviar el nuevo estado del audio al PC: T1 (ON) o T0 (OFF)
      Serial.print("T");
      Serial.println(audio_state ? "1" : "0");
    }
  }
  last_button_state = current_button_state;
}

void handleADCReadings() {
  // Leer los nuevos valores
  int new_freq_val = analogRead(PIN_FREQ_POT);
  int new_amp_val = analogRead(PIN_AMP_POT);

  // Reemplazar la lectura más antigua con la nueva
  freq_readings[read_index] = new_freq_val;
  amp_readings[read_index] = new_amp_val;
  
  // Avanzar el índice (buffer circular)
  read_index = (read_index + 1) % NUM_READINGS;
}

void sendDataToPC() {
  long sum_freq = 0;
  long sum_amp = 0;

  // Calcular el promedio (Filtro de Promedio Móvil)
  for (int i = 0; i < NUM_READINGS; i++) {
    sum_freq += freq_readings[i];
    sum_amp += amp_readings[i];
  }
  int avg_freq_adc = sum_freq / NUM_READINGS;
  int avg_amp_adc = sum_amp / NUM_READINGS;

  // 1. Mapeo de Frecuencia (Lineal Logarítmico)
  // Mapeamos el ADC (0-4095) a una escala logarítmica para mejorar la sensibilidad en bajas frecuencias
  // [20 Hz, 20000 Hz] -> (log10(20) a log10(20000))
  // ESP32 ADC Resolution es 12 bits (0-4095)
  float log_min = log10(20.0);
  float log_max = log10(20000.0);
  
  // Mapeamos el valor ADC lineal a un valor logarítmico lineal
  float log_value = log_min + (log_max - log_min) * ((float)avg_freq_adc / 4095.0);
  float mapped_freq = pow(10, log_value); 

  // 2. Mapeo de Amplitud (Lineal Simple)
  // [0.0, 1.0]
  float mapped_amp = (float)avg_amp_adc / 4095.0;

  // --- Enviar Frecuencia ---
  if (abs(mapped_freq - last_freq_sent) >= FREQ_TOLERANCE) {
    // Formato: F<valor> (e.g., F440.00)
    Serial.print("F");
    Serial.println(mapped_freq, 2); // Enviar con 2 decimales
    last_freq_sent = mapped_freq;
  }
  
  // --- Enviar Amplitud ---
  if (abs(mapped_amp - last_amp_sent) >= AMP_TOLERANCE) {
    // Formato: A<valor> (e.g., A0.55)
    Serial.print("A");
    Serial.println(mapped_amp, 2); // Enviar con 2 decimales
    last_amp_sent = mapped_amp;
  }
}