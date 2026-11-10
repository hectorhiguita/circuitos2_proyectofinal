// alert_logic.h - Lógica de alertas tempranas (código puro, probado en el PC).
// Reglas (SPEC.md):
//   - BPM fuera de [bpm_min, bpm_max] sostenido 10 s  -> "alto" / "bajo"
//   - cambio > 25 lpm dentro de 30 s                  -> "subida_rapida" / "bajada_rapida"
//   - pérdida de señal 10 s tras haber medido          -> "sin_senal"
//   - enfriamiento de 5 min por tipo de alerta
#pragma once
#include <stdint.h>

namespace ppg {

enum AlertType : uint8_t { ALERT_ALTO = 0, ALERT_BAJO, ALERT_SUBIDA, ALERT_BAJADA, ALERT_SIN_SENAL, ALERT_COUNT };

const char* alertName(AlertType t);

struct AlertEvent {
  AlertType type;
  int bpm;
  int umbral;
};

class AlertEngine {
 public:
  static constexpr uint32_t kSustainMs = 10000;
  static constexpr uint32_t kTrendWindowMs = 30000;
  static constexpr int kTrendDelta = 25;
  static constexpr uint32_t kCooldownMs = 300000;
  static constexpr uint32_t kNoSignalMs = 10000;

  void setLimits(int bpm_min, int bpm_max) {
    min_ = bpm_min;
    max_ = bpm_max;
  }
  // Llamar periódicamente (~1 Hz). Devuelve nº de eventos escritos en out.
  int update(uint32_t now_ms, bool valid, int bpm, AlertEvent* out, int max_out);
  void reset();

 private:
  bool fire(AlertType t, uint32_t now);
  static constexpr int kHist = 64;
  int min_ = 50, max_ = 120;
  bool hi_active_ = false, lo_active_ = false;
  uint32_t hi_since_ = 0, lo_since_ = 0;
  bool had_signal_ = false, lost_active_ = false;
  uint32_t lost_since_ = 0;
  uint32_t hist_t_[kHist] = {0};
  int16_t hist_b_[kHist] = {0};
  int hist_n_ = 0, hist_head_ = 0;
  bool fired_[ALERT_COUNT] = {false};
  uint32_t last_fire_[ALERT_COUNT] = {0};
};

}  // namespace ppg
