from __future__ import annotations
from typing import List, Dict, Any


class SustainabilityModel:
    def simulate(self, plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        text = " ".join(map(str, plan)).lower()
        energy = (
            0.2 + 0.5 * ("train_large_model" in text) + 0.2 * ("gpu_cluster" in text)
        )
        co2 = 0.1 + 0.2 * ("flight" in text) + 0.2 * ("diesel" in text)
        water = 0.1 + 0.3 * ("cooling" in text)
        biodiversity = (
            0.8
            if any(k in text for k in ["deforest", "mining", "habitat_loss"])
            else 0.0
        )
        score = 1.0 - (0.4 * energy + 0.3 * co2 + 0.2 * water + 0.1 * biodiversity)
        tips = []
        if energy > 0.5:
            tips.append(
                "Pakai quantization, distillation, dan batch scheduling off-peak."
            )
        if co2 > 0.3:
            tips.append("Gunakan energi terbarukan; hindari transport intensif karbon.")
        if water > 0.3:
            tips.append("Optimalkan cooling dan pilih lokasi bersuhu rendah.")
        if biodiversity > 0.0:
            tips.append("Stop aktivitas yang merusak habitat; cari alternatif.")
        return {
            "sustainability_score": round(max(0.0, min(1.0, score)), 3),
            "env_breakdown": {
                "energy": round(energy, 3),
                "co2": round(co2, 3),
                "water": round(water, 3),
                "biodiversity": round(biodiversity, 3),
            },
            "tips": tips,
        }
