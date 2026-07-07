import os
import numpy as np
import pandas as pd

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "synthetic_broadband_fraud_data.csv")


def generate_broadband_synthetic_data(n_samples: int = 10000, fraud_rate: float = 0.5, seed: int = 42) -> pd.DataFrame:
    """
    Generate realistic synthetic broadband fraud data.
    
    LEGITIMATE: 1-2 GB usage, 3-6 devices (normal home broadband)
    FRAUDSTERS: 8+ GB usage, 8+ devices (account takeover/reselling)
    """
    rng = np.random.default_rng(seed)
    n_fraud = int(n_samples * fraud_rate)
    n_legit = n_samples - n_fraud

    # ========== LEGITIMATE CUSTOMERS ==========
    # Normal home broadband: 1-2 GB/day, 3-6 devices (laptop, phone, tablet, TV, etc)
    legit = pd.DataFrame({
        "customer_id": [f"CUST-L-{i:05d}" for i in range(n_legit)],
        
        # Usage: 1-2.5 GB (1000-2500 MB)
        "usage_mb": rng.normal(1500, 300, n_legit).clip(800, 3000),
        "avg_usage_mb": rng.normal(1500, 300, n_legit).clip(800, 3000),
        
        # Established devices (not new)
        "device_age_days": rng.integers(30, 1200, n_legit),
        
        # NORMAL: 3-6 devices per home (this is NOT fraud!)
        "num_devices_30d": rng.integers(3, 7, n_legit),
        
        # Payments usually successful
        "failed_payments_7d": rng.poisson(0.1, n_legit),
        
        # Established accounts (90+ days old)
        "account_age_days": rng.integers(90, 3000, n_legit),
        
        # Normal login hours (any time of day)
        "login_hour": rng.choice(np.arange(0, 24), size=n_legit, 
                                  p=[0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.04, 0.04, 
                                     0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 
                                     0.05, 0.05, 0.05, 0.04, 0.04, 0.04, 0.04, 0.03]),
        
        # Usual location (within 30 km)
        "distance_from_usual_km": rng.exponential(3, n_legit).clip(0, 50),
        
        # Normal MAC addresses
        "mac_address": [f"AA:BB:CC:{rng.integers(0, 255):02X}:{rng.integers(0, 255):02X}:{rng.integers(0, 255):02X}" 
                        for _ in range(n_legit)],
        "label": 0,
    })

    # ========== FRAUDSTERS ==========
    # Account takeover: 8-20 GB usage, 8+ devices (reselling to many people)
    fraud = pd.DataFrame({
        "customer_id": [f"CUST-F-{i:05d}" for i in range(n_fraud)],
        
        # Usage: 8-20 GB (8000-20000 MB) - massive spike
        "usage_mb": rng.normal(12000, 4000, n_fraud).clip(5000, 30000),
        
        # Their "normal" average is actually normal, but current usage is abnormal
        "avg_usage_mb": rng.normal(1500, 400, n_fraud).clip(500, 3000),
        
        # NEW devices (SIM swap, account takeover)
        "device_age_days": rng.integers(0, 7, n_fraud),
        
        # MANY devices (8+) - selling account to multiple people
        "num_devices_30d": rng.integers(8, 20, n_fraud),
        
        # Multiple failed payments (testing stolen cards)
        "failed_payments_7d": rng.poisson(3, n_fraud) + 1,
        
        # Brand new accounts (subscription fraud)
        "account_age_days": rng.integers(0, 45, n_fraud),
        
        # ODD hours (2-5 AM, late night)
        "login_hour": rng.choice([0, 1, 2, 3, 4, 5, 23], size=n_fraud, 
                                  p=[0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.1]),
        
        # Unusual location (100+ km away)
        "distance_from_usual_km": rng.exponential(150, n_fraud).clip(50, 800),
        
        # Different MAC addresses (attacker's devices)
        "mac_address": [f"FF:FF:FF:{rng.integers(0, 255):02X}:{rng.integers(0, 255):02X}:{rng.integers(0, 255):02X}" 
                        for _ in range(n_fraud)],
        "label": 1,
    })

    df = pd.concat([legit, fraud], ignore_index=True)
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    
    print(f"\n=== Synthetic Data Summary ===")
    print(f"Total samples: {len(df)}")
    print(f"Legitimate: {n_legit} ({100*n_legit/len(df):.1f}%)")
    print(f"Fraud: {n_fraud} ({100*n_fraud/len(df):.1f}%)")
    print(f"\nLegitimate - Devices: {legit['num_devices_30d'].min()}-{legit['num_devices_30d'].max()}, Usage: {legit['usage_mb'].min():.0f}-{legit['usage_mb'].max():.0f} MB")
    print(f"Fraud - Devices: {fraud['num_devices_30d'].min()}-{fraud['num_devices_30d'].max()}, Usage: {fraud['usage_mb'].min():.0f}-{fraud['usage_mb'].max():.0f} MB")
    
    return df


if __name__ == "__main__":
    df = generate_broadband_synthetic_data()
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved {len(df)} synthetic rows to {OUTPUT_PATH}")
