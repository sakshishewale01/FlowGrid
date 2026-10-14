FlowGrid AI - Delay Classification Starter Dataset (India version)

Main file: flowgrid_delay_model_india.csv  (1,451 rows, same columns as the original)

What was changed (localised from the Bangladesh version):
- Warehouses: Pune, Kolkata, Ahmedabad, Delhi NCR, Chennai
- Destinations: Lucknow, Jaipur, Guwahati, Patna, Indore, Mumbai, JNPT Nhava Sheva, Bhopal, Surat, Visakhapatnam, Hyderabad, Bengaluru
- distance_km: recomputed from real city coordinates (great-circle distance x 1.3 road factor), so every route now has one consistent, realistic distance (approximate highway km, not GPS-logged).
- Drivers, suppliers and vehicle types given Indian equivalents (suppliers are fictional names, not real companies).

What was NOT changed:
- shipment_id, date, and the is_delayed label are carried over from the original file.

Important:
- This is still NOT real Indian shipment history. Delay labels come from the original synthetic data, so they do not reflect real Indian carrier performance, and they were not generated from distance/route/mode.
- Do not use the model for real decisions. For real delay data, use sources like NHAI/FASTag toll data, Indian Railways freight data, or company logs.
