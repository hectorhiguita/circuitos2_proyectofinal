// Pruebas unitarias del DSP / detector / alertas (se ejecutan en el PC).
//   pio test -e native
#include <math.h>
#include <stdio.h>
#include <unity.h>

#include "alert_logic.h"
#include "ppg_dsp.h"
#include "ppg_synth.h"

using namespace ppg;

void setUp() {}
void tearDown() {}

struct RunResult {
  int checks = 0;        // nº de verificaciones (1 Hz tras el arranque)
  int valid = 0;         // cuántas con BPM válido
  float worst_err = 0;   // peor error absoluto [lpm]
  int beats = 0;
  float last_bpm = 0;
};

// Simula `seconds` s de señal a `bpm` y verifica cada segundo a partir de `warmup_s`.
static RunResult run(float bpm, float seconds, float warmup_s, uint32_t seed, float noise_mv = 20.0f,
                     float amp_mv = 400.0f, float wander_mv = 120.0f) {
  Config cfg;
  PpgProcessor p;
  p.init(cfg);
  PpgSynth syn(seed);
  PpgSynth::Params sp;
  sp.noise_mv = noise_mv;
  sp.amp_mv = amp_mv;
  sp.wander_mv = wander_mv;
  syn.setParams(sp);
  syn.setBpm(bpm);
  RunResult r;
  const int n = (int)(seconds * cfg.fs);
  for (int i = 0; i < n; i++) {
    const uint32_t t = (uint32_t)(i * 5);
    Output o = p.process(syn.next(true), t);
    if (o.beat) r.beats++;
    if (i % 200 == 0 && t >= warmup_s * 1000) {
      r.checks++;
      if (p.bpmValid()) {
        r.valid++;
        const float e = fabsf(p.bpm() - bpm);
        if (e > r.worst_err) r.worst_err = e;
        r.last_bpm = p.bpm();
      }
    }
  }
  printf("  bpm=%.0f -> medido=%.1f, peor error=%.2f lpm, validas=%d/%d, latidos=%d\n", bpm, r.last_bpm,
         r.worst_err, r.valid, r.checks, r.beats);
  return r;
}

static void check_bpm(float bpm) {
  // Varias semillas de ruido para no depender de una sola realización.
  for (uint32_t seed = 1; seed <= 5; seed++) {
    RunResult r = run(bpm, 30.0f, 8.0f, seed * 7919u);
    TEST_ASSERT_EQUAL_INT_MESSAGE(r.checks, r.valid, "BPM no valido en alguna verificacion");
    TEST_ASSERT_TRUE_MESSAGE(r.worst_err <= 3.0f, "error > 3 lpm");
  }
}

void test_bpm_60() { check_bpm(60.0f); }
void test_bpm_120() { check_bpm(120.0f); }
void test_bpm_180() { check_bpm(180.0f); }

void test_bpm_extremes_40_200() {
  RunResult a = run(40.0f, 40.0f, 15.0f, 99);
  TEST_ASSERT_EQUAL_INT(a.checks, a.valid);
  TEST_ASSERT_TRUE(a.worst_err <= 3.0f);
  RunResult b = run(200.0f, 30.0f, 8.0f, 98);
  TEST_ASSERT_EQUAL_INT(b.checks, b.valid);
  TEST_ASSERT_TRUE(b.worst_err <= 4.0f);  // 2 % a 200 lpm (IBI = 300 ms, VFC sintética 1 %)
}

void test_heavy_noise_low_amplitude() {
  // Pulso pequeño (150 mV p-p), ruido fuerte (sigma 25 mV) y deriva de 60 mV
  // (la cadena analógica ya atenúa la respiración con 3 polos pasaaltas de 0.34 Hz).
  RunResult r = run(90.0f, 30.0f, 8.0f, 4242, 25.0f, 150.0f, 60.0f);
  TEST_ASSERT_EQUAL_INT(r.checks, r.valid);
  TEST_ASSERT_TRUE(r.worst_err <= 3.0f);
}

void test_finger_absent() {
  Config cfg;
  PpgProcessor p;
  p.init(cfg);
  PpgSynth syn(7);
  int beats = 0;
  for (int i = 0; i < 200 * 15; i++) {
    Output o = p.process(syn.next(false), (uint32_t)(i * 5));
    if (o.beat) beats++;
  }
  TEST_ASSERT_FALSE(p.finger());
  TEST_ASSERT_FALSE(p.bpmValid());
  TEST_ASSERT_EQUAL_INT(0, beats);
}

void test_finger_removed_then_back() {
  Config cfg;
  PpgProcessor p;
  p.init(cfg);
  PpgSynth syn(11);
  syn.setBpm(75);
  uint32_t t = 0;
  for (int i = 0; i < 200 * 15; i++, t += 5) p.process(syn.next(true), t);
  TEST_ASSERT_TRUE(p.bpmValid());
  for (int i = 0; i < 200 * 6; i++, t += 5) p.process(syn.next(false), t);
  TEST_ASSERT_FALSE(p.finger());
  TEST_ASSERT_FALSE(p.bpmValid());
  for (int i = 0; i < 200 * 15; i++, t += 5) p.process(syn.next(true), t);
  TEST_ASSERT_TRUE(p.bpmValid());
  TEST_ASSERT_FLOAT_WITHIN(3.0f, 75.0f, p.bpm());
}

void test_median() {
  const uint16_t a[5] = {800, 1200, 790, 810, 300};
  TEST_ASSERT_EQUAL_UINT16(800, BpmEstimator::median(a, 5));
  const uint16_t b[3] = {500, 400, 600};
  TEST_ASSERT_EQUAL_UINT16(500, BpmEstimator::median(b, 3));
}

void test_bpm_estimator_rejects_outliers() {
  BpmEstimator e;
  e.init(30, 220, 3500);
  uint32_t t = 0;
  e.addBeat(t);
  const int ibis[] = {1000, 1000, 400, 600, 1000, 1000, 1000};  // un latido extra espurio (400+600)
  for (int ibi : ibis) {
    t += ibi;
    e.addBeat(t);
  }
  TEST_ASSERT_TRUE(e.valid());
  TEST_ASSERT_FLOAT_WITHIN(1.0f, 60.0f, e.bpm());
  e.tick(t + 4000);
  TEST_ASSERT_FALSE(e.valid());
}

// ------------------------------------------------------------------ alertas
static int feed(AlertEngine& a, uint32_t& now, int secs, bool valid, int bpm, AlertEvent* ev, int* types) {
  int total = 0;
  for (int s = 0; s < secs; s++, now += 1000) {
    int n = a.update(now, valid, bpm, ev, 4);
    for (int i = 0; i < n; i++) types[ev[i].type]++;
    total += n;
  }
  return total;
}

void test_alert_high_sustained_and_cooldown() {
  AlertEngine a;
  a.setLimits(50, 120);
  AlertEvent ev[4];
  int types[ALERT_COUNT] = {0};
  uint32_t now = 1000;
  feed(a, now, 20, true, 80, ev, types);
  feed(a, now, 9, true, 130, ev, types);  // 9 s: aún no
  TEST_ASSERT_EQUAL_INT(0, types[ALERT_ALTO]);
  feed(a, now, 60, true, 130, ev, types);  // se dispara 1 vez
  TEST_ASSERT_EQUAL_INT(1, types[ALERT_ALTO]);
  feed(a, now, 200, true, 130, ev, types);  // dentro de 5 min: no repite
  TEST_ASSERT_EQUAL_INT(1, types[ALERT_ALTO]);
  feed(a, now, 60, true, 130, ev, types);  // >5 min: repite
  TEST_ASSERT_EQUAL_INT(2, types[ALERT_ALTO]);
}

void test_alert_low_needs_10s() {
  AlertEngine a;
  a.setLimits(50, 120);
  AlertEvent ev[4];
  int types[ALERT_COUNT] = {0};
  uint32_t now = 0;
  for (int k = 0; k < 10; k++) {  // bajadas intermitentes de 5 s no disparan
    feed(a, now, 5, true, 45, ev, types);
    feed(a, now, 5, true, 60, ev, types);
  }
  TEST_ASSERT_EQUAL_INT(0, types[ALERT_BAJO]);
  feed(a, now, 12, true, 45, ev, types);
  TEST_ASSERT_EQUAL_INT(1, types[ALERT_BAJO]);
}

void test_alert_trend() {
  AlertEngine a;
  a.setLimits(40, 200);
  AlertEvent ev[4];
  int types[ALERT_COUNT] = {0};
  uint32_t now = 0;
  feed(a, now, 30, true, 70, ev, types);
  // sube 1.5 lpm/s durante 20 s (70 -> 100): > 25 en 30 s
  for (int s = 0; s < 20; s++) feed(a, now, 1, true, 70 + (s * 3) / 2, ev, types);
  TEST_ASSERT_EQUAL_INT(1, types[ALERT_SUBIDA]);
  // subida lenta (0.5 lpm/s) no dispara bajada ni nueva subida
  int types2[ALERT_COUNT] = {0};
  AlertEngine b;
  b.setLimits(40, 200);
  now = 0;
  for (int s = 0; s < 120; s++) feed(b, now, 1, true, 70 + s / 2, ev, types2);
  TEST_ASSERT_EQUAL_INT(0, types2[ALERT_SUBIDA]);
  TEST_ASSERT_EQUAL_INT(0, types2[ALERT_BAJADA]);
  // bajada brusca
  feed(b, now, 5, true, 90, ev, types2);
  TEST_ASSERT_EQUAL_INT(1, types2[ALERT_BAJADA]);
}

void test_alert_no_signal() {
  AlertEngine a;
  a.setLimits(50, 120);
  AlertEvent ev[4];
  int types[ALERT_COUNT] = {0};
  uint32_t now = 0;
  feed(a, now, 30, false, 0, ev, types);  // nunca hubo señal: no alerta
  TEST_ASSERT_EQUAL_INT(0, types[ALERT_SIN_SENAL]);
  feed(a, now, 10, true, 70, ev, types);
  feed(a, now, 9, false, 0, ev, types);
  TEST_ASSERT_EQUAL_INT(0, types[ALERT_SIN_SENAL]);
  feed(a, now, 5, false, 0, ev, types);
  TEST_ASSERT_EQUAL_INT(1, types[ALERT_SIN_SENAL]);
}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_median);
  RUN_TEST(test_bpm_estimator_rejects_outliers);
  RUN_TEST(test_bpm_60);
  RUN_TEST(test_bpm_120);
  RUN_TEST(test_bpm_180);
  RUN_TEST(test_bpm_extremes_40_200);
  RUN_TEST(test_heavy_noise_low_amplitude);
  RUN_TEST(test_finger_absent);
  RUN_TEST(test_finger_removed_then_back);
  RUN_TEST(test_alert_high_sustained_and_cooldown);
  RUN_TEST(test_alert_low_needs_10s);
  RUN_TEST(test_alert_trend);
  RUN_TEST(test_alert_no_signal);
  return UNITY_END();
}
