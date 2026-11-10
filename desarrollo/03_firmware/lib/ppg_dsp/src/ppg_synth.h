// ppg_synth.h - Generador de señal PPG sintética (modo DEMO_SENSOR y pruebas).
// Produce la tensión que vería el ADC en GPIO1 [mV]: centrada en Vref, con la
// sístole hacia ABAJO (fotodiodo en transmisión), muesca dícrota, deriva de
// línea base, ruido blanco gaussiano, zumbido de 60 Hz y variabilidad del ritmo.
#pragma once
#include <math.h>
#include <stdint.h>

namespace ppg {

class PpgSynth {
 public:
  struct Params {
    float fs = 200.0f;
    float vref_mv = 1320.0f;
    float amp_mv = 400.0f;      // p-p del pulso en el ADC
    float noise_mv = 20.0f;     // sigma del ruido blanco
    float wander_mv = 120.0f;   // amplitud de la deriva (respiración ~0.25 Hz)
    float mains_mv = 15.0f;     // 60 Hz
    float hrv = 0.01f;           // variación relativa del periodo latido a latido
    bool inverted = true;       // sístole hacia abajo (como el hardware real)
  };

  explicit PpgSynth(uint32_t seed = 12345) : rng_(seed ? seed : 1) {}
  void setParams(const Params& p) { p_ = p; }
  const Params& params() const { return p_; }
  void setBpm(float bpm) { bpm_ = bpm; }
  float bpm() const { return bpm_; }

  // Siguiente muestra [mV]. finger=false -> línea plana en Vref + ruido.
  float next(bool finger = true) {
    const float dt = 1.0f / p_.fs;
    t_ += dt;
    float v = p_.vref_mv + p_.mains_mv * sinf(2.0f * 3.14159265f * 60.0f * t_) + p_.noise_mv * 0.25f * gauss();
    if (!finger) return v;
    phase_ += dt / period_;
    if (phase_ >= 1.0f) {
      phase_ -= 1.0f;
      period_ = (60.0f / bpm_) * (1.0f + p_.hrv * gauss());
    }
    const float pulse = shape(phase_);  // 0..1
    const float s = p_.inverted ? -1.0f : 1.0f;
    v += s * p_.amp_mv * (pulse - 0.35f);
    v += p_.wander_mv * sinf(2.0f * 3.14159265f * 0.25f * t_);
    v += p_.noise_mv * gauss();
    return v;
  }

  // Forma de un latido (fase 0..1): onda sistólica + onda dícrota.
  static float shape(float ph) {
    const float a = (ph - 0.15f) / 0.07f;
    const float b = (ph - 0.42f) / 0.09f;
    return expf(-0.5f * a * a) + 0.35f * expf(-0.5f * b * b);
  }

 private:
  uint32_t xorshift() {
    rng_ ^= rng_ << 13;
    rng_ ^= rng_ >> 17;
    rng_ ^= rng_ << 5;
    return rng_;
  }
  float uniform() { return ((xorshift() >> 8) + 0.5f) * (1.0f / 16777216.0f); }
  float gauss() {  // Box-Muller
    const float u1 = uniform(), u2 = uniform();
    return sqrtf(-2.0f * logf(u1)) * cosf(2.0f * 3.14159265f * u2);
  }

  Params p_;
  uint32_t rng_;
  float bpm_ = 72.0f, phase_ = 0.0f, period_ = 60.0f / 72.0f, t_ = 0.0f;
};

}  // namespace ppg
