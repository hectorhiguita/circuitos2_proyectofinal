// ppg_dsp.cpp - ver ppg_dsp.h
#include "ppg_dsp.h"

#include <math.h>

namespace ppg {

static constexpr float kPi = 3.14159265358979f;

// ======================================================================= Biquad
void Biquad::lowpass(float fs, float fc, float q) {
  // RBJ cookbook, pasabajas 2º orden (bilineal con prewarp).
  const float w0 = 2.0f * kPi * fc / fs;
  const float cw = cosf(w0), sw = sinf(w0);
  const float alpha = sw / (2.0f * q);
  const float a0 = 1.0f + alpha;
  b0_ = (1.0f - cw) * 0.5f / a0;
  b1_ = (1.0f - cw) / a0;
  b2_ = b0_;
  a1_ = -2.0f * cw / a0;
  a2_ = (1.0f - alpha) / a0;
  reset();
}

float Biquad::process(float x) {
  const float y = b0_ * x + z1_;
  z1_ = b1_ * x - a1_ * y + z2_;
  z2_ = b2_ * x - a2_ * y;
  return y;
}

// ======================================================================= DC
void DcRemover::init(float fs, float tau_s) {
  alpha_ = 1.0f - expf(-1.0f / (fs * tau_s));
  primed_ = false;
}

float DcRemover::process(float x) {
  if (!primed_) {
    dc_ = x;
    primed_ = true;
  }
  dc_ += alpha_ * (x - dc_);
  return x - dc_;
}

// ======================================================================= detector
void BeatDetector::init(float fs, uint16_t refractory_ms, float min_amp, float env_tau_s) {
  kdec_ = 1.0f / (fs * env_tau_s);
  dt_ms_ = 1000.0f / fs;
  refr_ = refractory_ms;
  min_amp_ = min_amp;
  reset();
}

void BeatDetector::reset() {
  st_ = WAIT_LOW;
  primed_ = false;
  have_last_ = false;
  pk_ = tr_ = hi_ = lo_ = 0;
}

DetectorEvent BeatDetector::process(float y, uint32_t t) {
  DetectorEvent ev;
  if (!primed_) {
    pk_ = tr_ = y;
    primed_ = true;
  }
  // Envolventes: siguen instantáneamente los extremos y se relajan hacia la señal.
  if (y > pk_) pk_ = y; else pk_ += (y - pk_) * kdec_;
  if (y < tr_) tr_ = y; else tr_ += (y - tr_) * kdec_;
  const float range = pk_ - tr_;
  // Umbral adaptativo con histéresis: alto al 60 %, bajo al 35 % del rango.
  hi_ = tr_ + 0.60f * range;
  lo_ = tr_ + 0.35f * range;

  if (range < min_amp_) {  // señal demasiado pequeña: no detectar
    st_ = WAIT_LOW;
    prev_y_ = y;
    return ev;
  }

  switch (st_) {
    case WAIT_LOW:
      if (y < lo_) st_ = ARMED;
      break;
    case ARMED:
      if (y > hi_ && (!have_last_ || (uint32_t)(t - last_beat_t_) >= refr_)) {
        st_ = IN_PEAK;
        peak_v_ = y;
        peak_t_ = t;
        pre_peak_y_ = prev_y_;
        post_set_ = false;
        in_peak_since_ = t;
        ev.onset = true;
      }
      break;
    case IN_PEAK:
      if (y > peak_v_) {
        pre_peak_y_ = prev_y_;
        peak_v_ = y;
        peak_t_ = t;
        post_set_ = false;
      } else if (!post_set_) {
        post_peak_y_ = y;
        post_set_ = true;
      }
      if (y < lo_) {  // bajó del umbral bajo: latido confirmado
        // Interpolación parabólica del máximo (resolución sub-muestra).
        float off = 0.0f;
        const float den = pre_peak_y_ - 2.0f * peak_v_ + post_peak_y_;
        if (post_set_ && den < -1e-6f) {
          off = 0.5f * (pre_peak_y_ - post_peak_y_) / den;
          if (off > 0.5f) off = 0.5f;
          if (off < -0.5f) off = -0.5f;
        }
        const int32_t off_ms = (int32_t)lroundf(off * dt_ms_);
        ev.beat = true;
        ev.beat_t = (uint32_t)((int32_t)peak_t_ + off_ms);
        last_beat_t_ = ev.beat_t;
        have_last_ = true;
        st_ = ARMED;
      } else if ((uint32_t)(t - in_peak_since_) > 2500) {  // atascado (artefacto)
        st_ = WAIT_LOW;
      }
      break;
  }
  prev_y_ = y;
  return ev;
}

// ======================================================================= BPM
void BpmEstimator::init(float bpm_min, float bpm_max, uint32_t timeout_ms) {
  ibi_min_ = (uint16_t)(60000.0f / bpm_max + 0.5f);
  ibi_max_ = (uint16_t)(60000.0f / bpm_min + 0.5f);
  timeout_ = timeout_ms;
  reset();
}

void BpmEstimator::reset() {
  n_ = idx_ = 0;
  have_last_ = valid_ = false;
  bpm_ = 0;
  last_ibi_ = 0;
}

uint16_t BpmEstimator::median(const uint16_t* v, int n) {
  uint16_t s[kN];
  for (int i = 0; i < n; i++) s[i] = v[i];
  for (int i = 1; i < n; i++) {  // inserción
    uint16_t k = s[i];
    int j = i - 1;
    while (j >= 0 && s[j] > k) {
      s[j + 1] = s[j];
      j--;
    }
    s[j + 1] = k;
  }
  if (n == 0) return 0;
  if (n & 1) return s[n / 2];
  return (uint16_t)((s[n / 2 - 1] + s[n / 2]) / 2);
}

uint16_t BpmEstimator::addBeat(uint32_t t) {
  if (!have_last_) {
    last_t_ = t;
    have_last_ = true;
    return 0;
  }
  const uint32_t ibi = t - last_t_;
  if (ibi < ibi_min_) return 0;  // demasiado pronto: se ignora (muesca dícrota / ruido)
  last_t_ = t;
  if (ibi > ibi_max_) return 0;  // pausa larga: reinicia el intervalo
  ibi_[idx_] = (uint16_t)ibi;
  idx_ = (idx_ + 1) % kN;
  if (n_ < kN) n_++;
  last_ibi_ = (uint16_t)ibi;
  if (n_ >= 3) {
    const uint16_t m = median(ibi_, n_);
    bpm_ = 60000.0f / (float)m;
    valid_ = true;
  }
  return (uint16_t)ibi;
}

void BpmEstimator::tick(uint32_t now) {
  if (have_last_ && (uint32_t)(now - last_t_) > timeout_) {
    reset();
  }
}

// ======================================================================= procesador
void PpgProcessor::init(const Config& c) {
  cfg_ = c;
  dc_.init(c.fs, c.dc_tau_s);
  lp_.lowpass(c.fs, c.lp_fc, 0.7071f);
  det_.init(c.fs, c.refractory_ms, c.min_amp_mv * 0.6f, c.env_tau_s);
  bpm_.init(c.bpm_min, c.bpm_max, c.bpm_timeout_ms);
  blk_len_ = (int)(c.fs * 0.5f);
  blk_cnt_ = blk_idx_ = blk_filled_ = 0;
  finger_ = clipping_ = false;
  amp_ = 0;
  started_ = false;
}

Output PpgProcessor::process(float raw, uint32_t t) {
  Output o;
  o.raw = raw;
  if (!started_) {
    started_ = true;
    settle_until_ = t + 1000;  // 1 s para que converjan DC y filtro
  }
  float ac = dc_.process(raw);
  float y = lp_.process(ac);
  if (cfg_.invert) y = -y;
  o.filt = y;

  // ---- estadística por bloques (amplitud, recorte)
  if (blk_cnt_ == 0) {
    cmin_f_ = cmax_f_ = y;
    cmin_r_ = cmax_r_ = raw;
  } else {
    if (y < cmin_f_) cmin_f_ = y;
    if (y > cmax_f_) cmax_f_ = y;
    if (raw < cmin_r_) cmin_r_ = raw;
    if (raw > cmax_r_) cmax_r_ = raw;
  }
  if (++blk_cnt_ >= blk_len_) {
    blk_cnt_ = 0;
    bmin_f_[blk_idx_] = cmin_f_;
    bmax_f_[blk_idx_] = cmax_f_;
    bmin_r_[blk_idx_] = cmin_r_;
    bmax_r_[blk_idx_] = cmax_r_;
    blk_idx_ = (blk_idx_ + 1) % kBlocks;
    if (blk_filled_ < kBlocks) blk_filled_++;
    float mnf = bmin_f_[0], mxf = bmax_f_[0], mnr = bmin_r_[0], mxr = bmax_r_[0];
    for (int i = 1; i < blk_filled_; i++) {
      if (bmin_f_[i] < mnf) mnf = bmin_f_[i];
      if (bmax_f_[i] > mxf) mxf = bmax_f_[i];
      if (bmin_r_[i] < mnr) mnr = bmin_r_[i];
      if (bmax_r_[i] > mxr) mxr = bmax_r_[i];
    }
    amp_ = mxf - mnf;
    clipping_ = (mnr < cfg_.clip_lo_mv) || (mxr > cfg_.clip_hi_mv);
    const float dc = dc_.dc();
    const bool dc_ok = dc >= cfg_.dc_min_mv && dc <= cfg_.dc_max_mv;
    const bool f = (t >= settle_until_) && dc_ok && amp_ >= cfg_.min_amp_mv;
    if (finger_ && !f) {  // se retiró el dedo
      bpm_.reset();
      det_.reset();
    }
    finger_ = f;
  }

  // ---- detección
  DetectorEvent ev = det_.process(y, t);
  o.hi = det_.hi();
  o.lo = det_.lo();
  if (finger_) {
    o.onset = ev.onset;
    if (ev.beat) {
      o.beat = true;
      o.beat_t = ev.beat_t;
      o.ibi = bpm_.addBeat(ev.beat_t);
    }
  }
  bpm_.tick(t);
  return o;
}

}  // namespace ppg
