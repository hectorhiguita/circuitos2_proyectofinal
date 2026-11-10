// alert_logic.cpp - ver alert_logic.h
#include "alert_logic.h"

namespace ppg {

const char* alertName(AlertType t) {
  switch (t) {
    case ALERT_ALTO: return "alto";
    case ALERT_BAJO: return "bajo";
    case ALERT_SUBIDA: return "subida_rapida";
    case ALERT_BAJADA: return "bajada_rapida";
    case ALERT_SIN_SENAL: return "sin_senal";
    default: return "?";
  }
}

void AlertEngine::reset() {
  hi_active_ = lo_active_ = had_signal_ = lost_active_ = false;
  hist_n_ = hist_head_ = 0;
  for (int i = 0; i < ALERT_COUNT; i++) fired_[i] = false;
}

bool AlertEngine::fire(AlertType t, uint32_t now) {
  if (fired_[t] && (uint32_t)(now - last_fire_[t]) < kCooldownMs) return false;
  fired_[t] = true;
  last_fire_[t] = now;
  return true;
}

int AlertEngine::update(uint32_t now, bool valid, int bpm, AlertEvent* out, int max_out) {
  int n = 0;
  auto emit = [&](AlertType t, int b, int u) {
    if (n < max_out && fire(t, now)) out[n++] = AlertEvent{t, b, u};
  };

  if (!valid) {
    hi_active_ = lo_active_ = false;
    hist_n_ = 0;
    if (had_signal_) {
      if (!lost_active_) {
        lost_active_ = true;
        lost_since_ = now;
      } else if ((uint32_t)(now - lost_since_) >= kNoSignalMs) {
        emit(ALERT_SIN_SENAL, 0, 0);
        had_signal_ = false;
        lost_active_ = false;
      }
    }
    return n;
  }

  had_signal_ = true;
  lost_active_ = false;

  // ---- fuera de rango sostenido
  if (bpm > max_) {
    if (!hi_active_) {
      hi_active_ = true;
      hi_since_ = now;
    } else if ((uint32_t)(now - hi_since_) >= kSustainMs) {
      emit(ALERT_ALTO, bpm, max_);
    }
  } else {
    hi_active_ = false;
  }
  if (bpm < min_) {
    if (!lo_active_) {
      lo_active_ = true;
      lo_since_ = now;
    } else if ((uint32_t)(now - lo_since_) >= kSustainMs) {
      emit(ALERT_BAJO, bpm, min_);
    }
  } else {
    lo_active_ = false;
  }

  // ---- tendencia en ventana de 30 s
  int mn = bpm, mx = bpm;
  const int tail = (hist_head_ - hist_n_ + kHist) % kHist;
  int keep_from = hist_n_;
  for (int i = 0; i < hist_n_; i++) {
    const int k = (tail + i) % kHist;
    if ((uint32_t)(now - hist_t_[k]) <= kTrendWindowMs) {
      if (keep_from == hist_n_) keep_from = i;
      if (hist_b_[k] < mn) mn = hist_b_[k];
      if (hist_b_[k] > mx) mx = hist_b_[k];
    }
  }
  hist_n_ -= keep_from;  // descarta lo más viejo que la ventana
  bool trend = false;
  if (bpm - mn > kTrendDelta) {
    emit(ALERT_SUBIDA, bpm, kTrendDelta);
    trend = true;
  } else if (mx - bpm > kTrendDelta) {
    emit(ALERT_BAJADA, bpm, kTrendDelta);
    trend = true;
  }
  if (trend) hist_n_ = 0;  // nueva línea base tras una alerta de tendencia
  hist_t_[hist_head_] = now;
  hist_b_[hist_head_] = (int16_t)bpm;
  hist_head_ = (hist_head_ + 1) % kHist;
  if (hist_n_ < kHist) hist_n_++;
  return n;
}

}  // namespace ppg
