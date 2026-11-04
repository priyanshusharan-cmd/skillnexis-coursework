// Occupancy features computed on the ESP32 from a 30-minute ring buffer, identical to ml/occupancy.py
// make_features() (checked sample-by-sample by tests/test_firmware_host.py). Header-only, no allocation.
#pragma once
#include <cmath>
#include <cstdint>

class FeatureExtractor {
 public:
  static constexpr int kN = 13;
  explicit FeatureExtractor(bool bedroom) : bedroom_(bedroom) {}

  // one call per minute: was there PIR motion this minute, mean sound level (dB), temperature (°C)
  void push(int motion, float sound_db, float temp_c, int minute_of_day, bool weekend) {
    head_ = (head_ + 1) % kHist;
    motion_[head_] = motion ? 1 : 0;
    sound_[head_] = sound_db;
    temp_[head_] = temp_c;
    if (count_ < kHist) count_++;
    if (total_ == 0) temp_first_ = temp_c;
    total_++;
    since_ = motion ? 0 : (since_ < 0 ? -1 : since_ + 1);
    minute_ = minute_of_day;
    weekend_ = weekend;
  }

  // order: motion_1, motion_5, motion_15, motion_30, since_motion, sound_mean5, sound_max5, sound_std15,
  //        temp_delta30, hour_sin, hour_cos, weekend, bedroom
  void get(float* f) const {
    f[0] = motion_[head_];
    f[1] = msum(5);
    f[2] = msum(15);
    f[3] = msum(30);
    f[4] = since_ < 0 ? 120.f : (since_ > 120 ? 120.f : static_cast<float>(since_));
    int n5 = count_ < 5 ? count_ : 5;
    float s = 0, mx = -1e9f;
    for (int i = 0; i < n5; i++) {
      float v = sound_[at(i)];
      s += v;
      if (v > mx) mx = v;
    }
    f[5] = s / n5;
    f[6] = mx;
    int n15 = count_ < 15 ? count_ : 15;  // sample standard deviation (ddof = 1), 0 until 2 samples
    if (n15 < 2) {
      f[7] = 0;
    } else {
      double m = 0, ss = 0;
      for (int i = 0; i < n15; i++) m += sound_[at(i)];
      m /= n15;
      for (int i = 0; i < n15; i++) ss += (sound_[at(i)] - m) * (sound_[at(i)] - m);
      f[7] = static_cast<float>(std::sqrt(ss / (n15 - 1)));
    }
    // temperature 30 minutes ago (or the first reading while the buffer fills)
    float t30 = total_ > 30 ? temp_[at(30)] : temp_first_;
    f[8] = temp_[head_] - t30;
    float h = minute_ / 60.f;
    f[9] = std::sin(2.f * static_cast<float>(M_PI) * h / 24.f);
    f[10] = std::cos(2.f * static_cast<float>(M_PI) * h / 24.f);
    f[11] = weekend_ ? 1.f : 0.f;
    f[12] = bedroom_ ? 1.f : 0.f;
  }

 private:
  static constexpr int kHist = 31;  // current minute + 30 minutes back
  int at(int back) const { return (head_ - back + kHist) % kHist; }
  float msum(int w) const {
    int n = count_ < w ? count_ : w, s = 0;
    for (int i = 0; i < n; i++) s += motion_[at(i)];
    return static_cast<float>(s);
  }
  bool bedroom_;
  uint8_t motion_[kHist] = {};
  float sound_[kHist] = {}, temp_[kHist] = {};
  float temp_first_ = 0;
  int head_ = -1, count_ = 0, since_ = -1, minute_ = 0;
  long total_ = 0;
  bool weekend_ = false;
};
