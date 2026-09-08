INSERT INTO material_catalog (
    material_code,
    display_name,
    aggregator_buy_rate,
    collector_margin,
    density_kg_per_m3,
    co2e_factor
) VALUES
    ('pet_plastic', 'PET Plastic', 42.00, 4.00, 35.00, 1.450),
    ('cardboard', 'Cardboard', 18.00, 2.00, 50.00, 0.950),
    ('iron', 'Ferrous Scrap Metal', 32.00, 3.00, 600.00, 8.200),
    ('glass', 'Glass', 12.00, 1.50, 350.00, 0.300)
ON CONFLICT (material_code) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    aggregator_buy_rate = EXCLUDED.aggregator_buy_rate,
    collector_margin = EXCLUDED.collector_margin,
    density_kg_per_m3 = EXCLUDED.density_kg_per_m3,
    co2e_factor = EXCLUDED.co2e_factor;
