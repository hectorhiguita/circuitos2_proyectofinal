// ppg_dsp.h - Procesamiento digital de la señal PPG (código puro C++, sin Arduino).
// Se compila igual en el ESP32-C3 y en el PC (pruebas unitarias, entorno "native").
//
// Cadena: raw [mV] -> quitar DC (EMA) -> pasabajas Butterworth 2º orden
//         -> (invertir polaridad) -> detector de picos con umbral adaptativo,
//         histéresis y periodo refractario -> IBI -> BPM = mediana de 5 IBI.
#pragma once
#include <stddef.h>
#include <stdint.h>

namespace ppg {

// ---------------------------------------------------------------- filtros
// Biquad (forma directa II transpuesta).
class Biquad {
 public:
  void lowpass(float fs, float fc, float q);  // diseño por transformada bilineal
  float process(float x);
  void reset() { z1_ = z2_ = 0.0f; }

 private:
  float b0_ = 1, b1_ = 0, b2_ = 0, a1_ = 0, a2_ = 0;
  float z1_ = 0, z2_ = 0;
};

// Quita la componente DC con un promedio móvil exponencial (EMA).
class DcRemover {
 public:
  void init(float fs, float tau_s);
  float process(float x);  // devuelve x - dc
  float dc() const { return dc_; }
  void reset() { primed_ = false; }

 private:
  float alpha_ = 0.01f, dc_ = 0.0f;
  bool primed_ = false;
};

// ---------------------------------------------------------------- detector
struct DetectorEvent {
  bool onset = false;   // cruce ascendente del umbral alto (para pitido/LED inmediato)
  bool beat = false;    // latido confirmado (se emite al bajar del umbral bajo)
  uint32_t beat_t = 0;  // instante [ms] del máximo local del latido confirmado
};

class BeatDetector {
 public:
  void init(float fs, uint16_t refractory_ms, float min_amp, float env_tau_s);
  DetectorEvent process(float y, uint32_t t_ms);
  void reset();
  float hi() const { return hi_; }
  float lo() const { return lo_; }
  float range() const { return pk_ - tr_; }

 private:
  enum State : uint8_t { WAIT_LOW, ARMED, IN_PEAK };
  State st_ = WAIT_LOW;
  float kdec_ = 0.002f, min_amp_ = 20.0f, dt_ms_ = 5.0f;
  uint16_t refr_ = 200;
  float pk_ = 0, tr_ = 0, hi_ = 0, lo_ = 0;
  float peak_v_ = 0, prev_y_ = 0, pre_peak_y_ = 0, post_peak_y_ = 0;
  bool post_set_ = false;
  uint32_t peak_t_ = 0, last_beat_t_ = 0, in_peak_since_ = 0;
  bool have_last_ = false, primed_ = false;
};

// ---------------------------------------------------------------- BPM
class BpmEstimator {
 public:
  static constexpr int kN = 5;
  void init(float bpm_min, float bpm_max, uint32_t timeout_ms);
  // Registra un latido. Devuelve el IBI aceptado [ms] o 0 si no se aceptó.
  uint16_t addBeat(uint32_t t_ms);
  // Actualiza validez por tiempo (sin latidos -> inválido).
  void tick(uint32_t now_ms);
  bool valid() const { return valid_; }
  float bpm() const { return bpm_; }
  uint16_t lastIbi() const { return last_ibi_; }
  int count() const { return n_; }
  void reset();

  static uint16_t median(const uint16_t* v, int n);

 private:
  uint16_t ibi_[kN] = {0};
  int n_ = 0, idx_ = 0;
  uint16_t ibi_min_ = 272, ibi_max_ = 2000, last_ibi_ = 0;
  uint32_t timeout_ = 3500, last_t_ = 0;
  bool have_last_ = false, valid_ = false;
  float bpm_ = 0;
};

// ---------------------------------------------------------------- procesador completo
struct Config {
  float fs = 200.0f;              // Hz
  float dc_tau_s = 0.8f;           // constante de tiempo del quita-DC
  float lp_fc = 5.0f;             // Hz, pasabajas digital (300 lpm = 5 Hz)
  bool invert = true;             // en transmisión, la sístole BAJA la tensión del fotodiodo
  uint16_t refractory_ms = 200;   // 300 lpm
  float env_tau_s = 2.5f;         // relajación de la envolvente del umbral adaptativo
  float min_amp_mv = 20.0f;       // amplitud p-p mínima (señal filtrada) para "dedo presente"
  float dc_min_mv = 700.0f;       // DC fuera de [min,max] -> etapa saturada / sin dedo
  float dc_max_mv = 1950.0f;
  float clip_lo_mv = 40.0f;       // recorte del ADC (0-2.5 V)
  float clip_hi_mv = 2450.0f;
  float bpm_min = 30.0f, bpm_max = 220.0f;
  uint32_t bpm_timeout_ms = 3500;
};

struct Output {
  float raw = 0;     // mV
  float filt = 0;    // mV, AC, picos hacia arriba
  float hi = 0, lo = 0;
  bool onset = false;
  bool beat = false;
  uint32_t beat_t = 0;
  uint16_t ibi = 0;  // ms (si beat y aceptado)
};

class PpgProcessor {
 public:
  void init(const Config& c);
  Output process(float raw_mv, uint32_t t_ms);

  bool finger() const { return finger_; }
  bool clipping() const { return clipping_; }
  bool bpmValid() const { return bpm_.valid() && finger_; }
  bool signalOk() const { return finger_ && !clipping_ && bpm_.valid(); }
  float bpm() const { return bpm_.bpm(); }
  float amplitude() const { return amp_; }  // p-p señal filtrada, ventana 2 s
  float dc() const { return dc_.dc(); }
  const Config& config() const { return cfg_; }

 private:
  static constexpr int kBlocks = 4;  // 4 bloques de 0.5 s = 2 s
  Config cfg_;
  DcRemover dc_;
  Biquad lp_;
  BeatDetector det_;
  BpmEstimator bpm_;
  int blk_len_ = 100, blk_cnt_ = 0, blk_idx_ = 0, blk_filled_ = 0;
  float bmin_f_[kBlocks] = {0}, bmax_f_[kBlocks] = {0};
  float bmin_r_[kBlocks] = {0}, bmax_r_[kBlocks] = {0};
  float cmin_f_ = 0, cmax_f_ = 0, cmin_r_ = 0, cmax_r_ = 0;
  float amp_ = 0;
  bool finger_ = false, clipping_ = false;
  uint32_t settle_until_ = 0;
  bool started_ = false;
};

}  // namespace ppg
